# Palantir — Application Flow (Annotated)

A detailed walkthrough of how data moves through the system, what every
data type means, and why the code looks the way it does.

---

## 1. Startup Sequence

When you run `docker compose up --build` (or `mvn spring-boot:run`), Spring Boot
creates beans in dependency order. Here is what happens, step by step:

### 1.1 OrekitConfig.init()

**File:** `config/OrekitConfig.java`

Orekit is a Java astrodynamics library. Before you can call *any* Orekit API
(propagate an orbit, convert coordinate frames, etc.) it needs reference data:
Earth orientation parameters, leap second tables, planetary ephemerides.

This method loads `orekit-data.zip` from the classpath and registers it with
Orekit's global `DataProvidersManager`. If the zip is missing, the app crashes
immediately — there is no point continuing without physics data.

**Why a `@Configuration` bean?** Other beans (like `OrbitPropagationService`)
inject `OrekitConfig` as a constructor dependency. This forces Spring to
initialize Orekit data *before* anything tries to use it. It is a deliberate
ordering trick — the field itself is never read, but the injection guarantees
the `@PostConstruct` ran first.

### 1.2 OrbitPropagationService.init()

**File:** `service/OrbitPropagationService.java`

Two things happen here:

1. **Build the Earth model** — `OneAxisEllipsoid` is Orekit's representation of
   the Earth as an oblate spheroid (WGS-84 standard). It needs:
   - Equatorial radius: 6,378,137 m
   - Flattening: 1/298.257223563
   - Reference frame: ITRF (International Terrestrial Reference Frame) —
     a frame that rotates with the Earth, so positions on its surface are fixed.

2. **Load the default ISS TLE** — so telemetry starts flowing the moment the app
   boots, with no manual curl required.

**Key types:**
- `OneAxisEllipsoid` — mathematical model of Earth's shape. Used later to convert
  a 3D position in space into latitude/longitude/altitude.
- `AtomicReference<TLEPropagator>` — a thread-safe wrapper. The scheduler reads
  the propagator every second on one thread, while a REST call might swap it on
  another thread. `AtomicReference` guarantees the swap is visible immediately
  without locks.
- `AtomicReference<String>` — same idea, for the satellite name used in logs.

### 1.3 CcsdsTelemetrySender.init()

**File:** `service/CcsdsTelemetrySender.java`

Opens a UDP `DatagramSocket` (unbound — it picks a random local port) and resolves
the Yamcs hostname. The socket stays open for the lifetime of the app.
`@PreDestroy` closes it on shutdown.

**Why UDP, not TCP?** Telemetry in real spacecraft ground systems is almost always
UDP. Packets are fire-and-forget — if one is lost, the next one arrives in a
second anyway. TCP's retransmission and ordering guarantees would add latency
for no benefit.

### 1.4 UdpCommandReceiver.startListening()

**File:** `service/uplink/UdpCommandReceiver.java`

Spawns a Virtual Thread (Java 21 feature — lightweight, OS-thread-cheap) that
blocks on `socket.receive()` forever, waiting for telecommand packets from Yamcs.

---

## 2. Telemetry Downlink — The 1 Hz Loop

This is the core heartbeat. Every second, Spring's `@Scheduled` calls
`OrbitPropagationService.propagateAndSend()`.

### Step-by-step:

```
@Scheduled(fixedRate = 1000)
propagateAndSend()
```

#### 2.1 Get the current propagator

```java
final var propagator = activePropagator.get();
```

`AtomicReference.get()` reads the current `TLEPropagator`. If no TLE has been
loaded yet, this is `null` and the method returns early (no telemetry sent).

#### 2.2 Build an Orekit timestamp

```java
final var now = new AbsoluteDate(Date.from(Instant.now()), TimeScalesFactory.getUTC());
```

- `Instant.now()` — wall-clock time from the JVM.
- `AbsoluteDate` — Orekit's high-precision time representation. It accounts for
  leap seconds and can convert between time scales (UTC, TAI, GPS, etc.).
- We use UTC because TLEs are referenced to UTC.

#### 2.3 Propagate the orbit (SGP4)

```java
final var state = propagator.propagate(now);
```

`TLEPropagator` uses the SGP4/SDP4 analytical model (the standard algorithm for
TLE-based orbit prediction, used by NORAD since the 1960s). Given a TLE epoch
and the current time, it computes the satellite's position and velocity.

The result is a `SpacecraftState` — position + velocity in the **TEME frame**
(True Equator, Mean Equinox). TEME is the native output frame of SGP4. It is an
Earth-centered inertial-ish frame (it drifts slightly because "mean equinox" is
an approximation).

#### 2.4 Convert TEME to geodetic coordinates

```java
final var position = state.getPVCoordinates(earth.getBodyFrame()).getPosition();
final var geo = earth.transform(position, earth.getBodyFrame(), now);
```

Two frame conversions happen here:

1. **TEME -> ITRF**: `getPVCoordinates(earth.getBodyFrame())` rotates the
   position from the inertial TEME frame into ITRF (the Earth-fixed frame).
   ITRF rotates with the Earth, so a point on the ground has constant ITRF
   coordinates.

2. **Cartesian ITRF -> Geodetic**: `earth.transform()` takes the XYZ Cartesian
   position (in meters, Earth-centered) and projects it onto the WGS-84
   ellipsoid to get:
   - **Latitude** — angle from the equatorial plane (-90 to +90 degrees)
   - **Longitude** — angle from the prime meridian (-180 to +180 degrees)
   - **Altitude** — height above the ellipsoid surface (in meters)

```java
final var latDeg = Math.toDegrees(geo.getLatitude());   // radians -> degrees
final var lonDeg = Math.toDegrees(geo.getLongitude());
final var altKm  = geo.getAltitude() / 1000.0;          // meters -> kilometers
```

Orekit returns radians and meters internally. We convert for human readability
and because the XTCE MDB on the Yamcs side defines the units as degrees and km.

#### 2.5 Encode and send CCSDS packet

```java
ccsdsTelemetrySender.sendPacket((float) latDeg, (float) lonDeg, (float) altKm);
```

The `(float)` cast narrows from `double` (64-bit) to `float` (32-bit). This is
intentional — the CCSDS packet format uses IEEE 754 single-precision floats to
keep the packet small (12 bytes of payload instead of 24). For satellite position
telemetry, 32-bit float precision (~7 decimal digits) is more than sufficient.

---

## 3. CCSDS Packet Encoding — Byte by Byte

**File:** `service/CcsdsTelemetrySender.java`

CCSDS 133.0-B-1 ("Space Packet Protocol") is the standard used by virtually
every space agency for telemetry. A Space Packet has a fixed 6-byte header
followed by a variable-length data field.

Our packet is 18 bytes total: 6-byte header + 12-byte payload.

### The ByteBuffer

```java
final var buffer = ByteBuffer.allocate(TOTAL_LENGTH);  // 18 bytes
```

`ByteBuffer` is Java's way to build raw binary data. It defaults to **big-endian**
byte order (most significant byte first), which is exactly what CCSDS requires
(network byte order).

### Byte [0-1]: Packet Identification (a `short`)

```java
final var packetId = (short) (APID & 0x07FF);
buffer.putShort(packetId);
```

These 2 bytes (16 bits) are packed as:

```
Bit:  15 14 13  12       11        10  9  8  7  6  5  4  3  2  1  0
      |------| |------|  |--------|  |--------------------------------|
      Version  Type      SecHeader   APID (Application Process ID)
      000      0=TM      0=absent    100 (decimal) = 0x0064
```

- **Version** (3 bits) = `000` — always zero for CCSDS v1.
- **Type** (1 bit) = `0` — telemetry (1 would be telecommand).
- **Secondary Header Flag** (1 bit) = `0` — we have no secondary header.
- **APID** (11 bits) = `100` — our application identifier. Yamcs uses this to
  route the packet to the correct XTCE container definition.

**What is a `short`?** A Java `short` is a 16-bit signed integer (-32768 to
32767). We use it here because `ByteBuffer.putShort()` writes exactly 2 bytes.
The `(short)` cast is needed because `APID & 0x07FF` produces an `int` in Java
(all bitwise operations promote to `int`).

**What does `& 0x07FF` do?** It is a bitmask. `0x07FF` in binary is
`0000 0111 1111 1111` — it keeps only the lowest 11 bits, zeroing out the top 5.
Since APID=100 fits in 11 bits and we want Version=0, Type=0, SecHeader=0, the
top 5 bits are all zero anyway. The mask is defensive — it guarantees that even
if someone set APID > 2047, the header stays well-formed.

### Byte [2-3]: Packet Sequence Control (a `short`)

```java
final var seqCount = sequenceCounter.getAndIncrement() & 0x3FFF;
final var seqControl = (short) (0xC000 | seqCount);
buffer.putShort(seqControl);
```

Another 16-bit field:

```
Bit:  15 14  13 12 11 10  9  8  7  6  5  4  3  2  1  0
      |----|  |--------------------------------------------------|
      Flags   Sequence Count (14 bits, 0..16383, wraps around)
      11
```

- **Grouping Flags** (2 bits) = `11` — "standalone packet" (not part of a
  multi-packet group). `0xC000` = `1100 0000 0000 0000` sets these two bits.

- **Sequence Count** (14 bits) — monotonically increasing counter, wraps at
  16383 back to 0. Yamcs uses this to detect packet loss (gaps in the count).
  `& 0x3FFF` masks to 14 bits (`0011 1111 1111 1111`).

- **`0xC000 | seqCount`** — bitwise OR merges the two fields into one 16-bit
  value. The flags go in the top 2 bits, the count goes in the bottom 14.

- **`AtomicInteger`** — the counter is an `AtomicInteger` for thread safety.
  `getAndIncrement()` atomically returns the current value and bumps it by one,
  so even if two threads called this concurrently, they would never get the same
  sequence number.

### Byte [4-5]: Packet Data Length (a `short`)

```java
final var dataLength = (short) (PAYLOAD_LENGTH - 1);  // 12 - 1 = 11
buffer.putShort(dataLength);
```

CCSDS defines this field as: *"number of octets in the Packet Data Field minus
one."* Our payload is 12 bytes, so this field = 11. The "minus one" is a quirk
of the CCSDS standard (it allows a data length of 0 to mean 1 byte, so the
minimum packet has 1 byte of data, not 0).

### Byte [6-17]: Payload (three `float` values)

```java
buffer.putFloat(lat);   // bytes 6-9
buffer.putFloat(lon);   // bytes 10-13
buffer.putFloat(alt);   // bytes 14-17
```

Each `putFloat()` writes 4 bytes in IEEE 754 single-precision format, big-endian.

**IEEE 754 float (32 bits):**
```
Bit:  31       30..23          22..0
      sign     exponent (8b)   mantissa (23b)
```

For example, latitude 51.64 degrees is stored as `0x424E8F5C` (4 bytes).

**Why `float` and not `double`?** To match the XTCE definition in
`yamcs/mdb/palantir.xml`, which declares `FloatDataEncoding sizeInBits="32"`.
Both sides must agree on the encoding.

### Sending the packet

```java
final var data = buffer.array();                                    // raw byte[]
final var packet = new DatagramPacket(data, data.length, address, port);
socket.send(packet);                                                // fire-and-forget UDP
```

The 18 raw bytes go into a UDP datagram aimed at Yamcs port 10000. No framing,
no length prefix — each UDP datagram is exactly one CCSDS packet.

---

## 4. Yamcs Receives and Decodes the Packet

### 4.1 UdpTmDataLink (port 10000)

Configured in `yamcs/etc/yamcs.palantir.yaml`. Yamcs binds UDP port 10000 and
receives raw datagrams. Each datagram is treated as one CCSDS packet.

### 4.2 GenericPacketPreprocessor

Yamcs runs the packet through `GenericPacketPreprocessor` which:
- Reads the **sequence count** from bytes [2-3] (for gap detection).
- Stamps a **generation time** using the local clock (`useLocalGenerationTime: true`)
  since our packets have no onboard timestamp.
- Skips error detection (`errorDetection: type: NONE`) — our packets have no
  CRC/checksum.

### 4.3 XTCE Mission Database (palantir.xml)

The packet enters the MDB (Mission Database) pipeline. Yamcs matches it against
XTCE container definitions:

1. **`CCSDS_Packet_Base`** (abstract) — reads 3 x `uint16` (the 6-byte header):
   `ccsds_packet_id`, `ccsds_seq_count`, `ccsds_length`.

2. **`Palantir_Nav_Packet`** — extends the base container with a **restriction**:
   `ccsds_packet_id == 100` (raw value, matching APID=100). If the APID matches,
   Yamcs continues decoding the payload as:
   - `Latitude` — 32-bit IEEE 754 float, unit: degrees
   - `Longitude` — 32-bit IEEE 754 float, unit: degrees
   - `Altitude` — 32-bit IEEE 754 float, unit: km

These become live Yamcs **parameters** visible in the web UI, plottable, and
archivable.

### 4.4 WebSocket to Browser

The `StreamTmPacketProvider` in the realtime processor pushes decoded parameters
to any connected WebSocket client (the Yamcs web UI). You see live lat/lon/alt
values updating every second.

---

## 5. TLE Ingestion (Operator REST Call)

**File:** `controller/TleIngestionController.java`

```
POST /api/orbit/tle
{
  "satelliteName": "ISS (ZARYA)",
  "line1": "1 25544U 98067A ...",
  "line2": "2 25544 51.6318 ..."
}
```

### Flow:

1. **Validate** — satellite name must not be blank, both TLE lines must be present.
   Returns `400 Bad Request` with a `TleResponse(status="REJECTED")` on failure.

2. **Parse** — `OrbitPropagationService.updateTle()` passes the lines to Orekit's
   `new TLE(line1, line2)` constructor, which validates checksum, format, and
   extracts orbital elements. If the TLE is malformed, Orekit throws
   `OrekitException`, caught and returned as 400.

3. **Hot-swap** — `TLEPropagator.selectExtrapolator(tle)` creates a new SGP4 or
   SDP4 propagator (SDP4 for deep-space orbits with period > 225 minutes).
   `activePropagator.set(propagator)` atomically replaces the old propagator.
   The very next 1 Hz tick will use the new TLE — no restart needed.

**DTOs (Data Transfer Objects):**
- `TleRequest` — a Java `record` (immutable data carrier). Fields: `satelliteName`,
  `line1`, `line2`. Spring Boot's Jackson automatically deserializes JSON into this.
- `TleResponse` — returned as JSON. `status` is either `"ACTIVE"` or `"REJECTED"`.

---

## 6. Telecommand Uplink (Yamcs -> Spring Boot)

**File:** `service/uplink/UdpCommandReceiver.java`

### Flow:

1. Operator clicks "Send Command" in Yamcs web UI (e.g., PING or REBOOT_OBC).

2. Yamcs `StreamTcCommandReleaser` puts the command on the `tc_realtime` stream.

3. `UdpTcDataLink` picks it up and sends a UDP datagram to `palantir-core:10001`.

4. `UdpCommandReceiver` (blocked on `socket.receive()`) wakes up, reads the packet.

5. **Opcode dispatch:**
   ```java
   final var opCode = data[0];  // first byte of the UDP payload
   ```
   The XTCE command definition (`palantir.xml`) encodes each command as a single
   `uint8` argument called `OpCode`:
   - `0x01` = PING / NOOP — do nothing, just acknowledge receipt
   - `0x02` = REBOOT_OBC — triggers `triggerRebootSequence()` (currently just a log)
   - `0x03` = SET_TRANSMIT_POWER — recognized but not yet implemented
   - Anything else = logged as UNKNOWN_OPCODE

### Why Virtual Threads?

```java
private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
```

`socket.receive()` is a **blocking** call — the thread sits idle waiting for data.
With traditional (platform) threads, this would tie up an OS thread. Virtual
Threads (Java 21, Project Loom) are extremely cheap — thousands can block
simultaneously with negligible overhead. This is the idiomatic Java 21 way to
handle blocking I/O.

---

## 7. Data Type Glossary

| Java Type | Size | Range | Used For |
|-----------|------|-------|----------|
| `byte` | 8 bits | -128 to 127 | Opcode in telecommands (`data[0]`) |
| `short` | 16 bits | -32768 to 32767 | CCSDS header fields (2 bytes each) |
| `int` | 32 bits | ~-2.1B to ~2.1B | Sequence counter, APID constant |
| `float` | 32 bits | ~7 decimal digits | Lat/lon/alt in CCSDS payload |
| `double` | 64 bits | ~15 decimal digits | Orekit internal precision, `Math.toDegrees()` output |
| `AtomicInteger` | thread-safe int | same as int | CCSDS sequence counter (concurrent access) |
| `AtomicReference<T>` | thread-safe pointer | — | Hot-swappable propagator and satellite name |

### Why `short` for CCSDS header fields?

CCSDS header fields are exactly 16 bits each. Java's `short` is 16 bits.
`ByteBuffer.putShort()` writes exactly 2 bytes to the buffer — a perfect match.

Java `short` is signed, but we never interpret the value as a signed number. We
use bitwise operations (`&`, `|`, shifts) which work on the raw bit pattern
regardless of sign. The signedness only matters if you print or compare the value
as a number — we never do.

### Bitmask cheat sheet

| Mask | Binary | Purpose |
|------|--------|---------|
| `0x07FF` | `0000 0111 1111 1111` | Keep lowest 11 bits (APID field) |
| `0x3FFF` | `0011 1111 1111 1111` | Keep lowest 14 bits (sequence count) |
| `0xC000` | `1100 0000 0000 0000` | Set top 2 bits (standalone grouping flags) |

---

## 8. Full Data Flow Diagram

```
                        +--------------------------+
                        |   Operator (curl/REST)   |
                        +------------+-------------+
                                     | POST /api/orbit/tle
                                     v
+------------------------------------------------------------------+
|                     Spring Boot (palantir-core)                  |
|                                                                  |
|  TleIngestionController                                          |
|    -> validates TleRequest                                       |
|    -> OrbitPropagationService.updateTle()                        |
|       -> TLE parse + TLEPropagator (SGP4/SDP4)                  |
|       -> AtomicReference.set() [hot swap]                        |
|                                                                  |
|  @Scheduled(1 Hz)                                                |
|  OrbitPropagationService.propagateAndSend()                      |
|    -> propagator.propagate(now)           [TEME frame]           |
|    -> earth.transform(position)           [TEME -> ITRF -> geo]  |
|    -> lat(deg), lon(deg), alt(km)                                |
|    -> CcsdsTelemetrySender.sendPacket()                          |
|       -> ByteBuffer: 6B CCSDS header + 3x float32               |
|       -> UDP datagram                                            |
|                         |                                        |
|  UdpCommandReceiver     |                                        |
|    <- UDP:10001 --------+--+                                     |
|    -> opcode dispatch   |  |                                     |
+-------------------------|--+-------------------------------------+
                          |  ^
             UDP:10000    |  |  UDP:10001
                          v  |
+------------------------------------------------------------------+
|                     Yamcs (mission control)                       |
|                                                                  |
|  UdpTmDataLink (port 10000)                                      |
|    -> GenericPacketPreprocessor (seq count + local timestamp)     |
|    -> XTCE MDB: CCSDS_Packet_Base -> Palantir_Nav_Packet         |
|       -> Latitude (float32, deg)                                 |
|       -> Longitude (float32, deg)                                |
|       -> Altitude (float32, km)                                  |
|    -> StreamTmPacketProvider -> realtime processor                |
|    -> WebSocket -> Browser UI                                    |
|                                                                  |
|  UdpTcDataLink (port 10001 target)                               |
|    <- StreamTcCommandReleaser <- operator command                 |
|    -> sends opcode byte via UDP                                  |
+------------------------------------------------------------------+
```
