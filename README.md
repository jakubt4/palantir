# Project Palantir: Orbital Telemetry Digital Twin

> *"They were not made by Sauron... They were made by the Noldor in Eldamar... to see far off, and to converse in thought with one another."* — Gandalf on the Palantiri

## About The Project

Project Palantir is a Proof of Concept (PoC) constructing a "Digital Twin" ground segment environment. It bridges astrodynamics simulation with operational mission control — the system propagates a satellite orbit in real time using SGP4/SDP4, encoding geodetic telemetry into CCSDS Space Packets (CCSDS 133.0-B-1) and streaming them over UDP to a Yamcs mission control instance. Operators can hot-swap Two-Line Element sets via REST at any time with zero propagation downtime.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           DOCKER COMPOSE                                │
│                                                                         │
│  ┌────────────────────────────────┐    ┌─────────────────────────────┐  │
│  │   palantir-core (:8080)        │    │   palantir-yamcs (:8090)    │  │
│  │                                │    │                             │  │
│  │  ┌──────────────────────────┐  │    │  ┌───────────────────────┐  │  │
│  │  │  TleIngestionController  │  │    │  │    Yamcs 5.12.2       │  │  │
│  │  │  POST /api/orbit/tle     │  │    │  │    Instance: palantir │  │  │
│  │  └────────────┬─────────────┘  │    │  │                       │  │  │
│  │               │                │    │  │  UdpTmDataLink :10000 │  │  │
│  │  ┌────────────▼─────────────┐  │    │  │         │             │  │  │
│  │  │ OrbitPropagationService  │  │    │  │  GenericPacket         │  │  │
│  │  │ TLE → SGP4 → WGS84 LLA  │  │    │  │  Preprocessor         │  │  │
│  │  │ @Scheduled(1 Hz)         │  │    │  │         │             │  │  │
│  │  └────────────┬─────────────┘  │    │  │  XTCE MDB Decoder     │  │  │
│  │               │                │    │  │  /Palantir/Latitude    │  │  │
│  │  ┌────────────▼─────────────┐  │    │  │  /Palantir/Longitude  │  │  │
│  │  │  CcsdsTelemetrySender    │──┼────┼──►  /Palantir/Altitude   │  │  │
│  │  │  CCSDS 133.0-B-1        │  │    │  └───────────────────────┘  │  │
│  │  │  UDP Datagram (18B)      │  │    │            │                │  │
│  │  └──────────────────────────┘  │    │       WebSocket + Archive   │  │
│  │                                │    │            ▼                │  │
│  │  Spring Boot 3.2 / Java 21    │    │       Browser UI            │  │
│  │  Orekit 12.2 / Virtual Threads│    │                             │  │
│  └────────────────────────────────┘    │  Yamcs 5.12.2 / XTCE MDB  │  │
│                                        └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
  Operator                  Spring Boot (Physics Engine)                       Yamcs (Mission Control)
     │                                │                                               │
     │                                │  @PostConstruct: load default ISS TLE         │
     │                                │──── Every 1 second ────┐                      │
     │                                │                        │                      │
     │                                │  1. Propagate SGP4     │                      │
     │                                │  2. TEME → ITRF        │                      │
     │                                │  3. Cartesian → LLA    │                      │
     │                                │  4. Encode CCSDS pkt   │                      │
     │                                │                        │                      │
     │                                │◄───────────────────────┘                      │
     │                                │                                               │
     │                                │  CCSDS Space Packet (UDP :10000)              │
     │                                │  [Header 6B | Lat | Lon | Alt] (18B)          │
     │                                │──────────────────────────────────────────────►│
     │                                │                                               │
     │                                │                      GenericPacketPreprocessor│
     │                                │                      (local generation time)  │
     │  POST /api/orbit/tle           │                      XTCE decodes APID=100   │
     │  (hot-swap, zero downtime)     │                                   │           │
     │───────────────────────────────►│                      ParameterRecorder        │
     │                                │                      archives to RocksDB      │
     │                                │                                   │           │
     │                                │                              WebSocket        │
     │                                │                                   ▼           │
     │                                │                              Browser UI       │
```

### CCSDS Space Packet Layout (18 bytes)

The telemetry packet follows CCSDS 133.0-B-1. Yamcs `GenericPacketPreprocessor` extracts the sequence count from offset 2 and assigns generation time from the local clock.

```
Offset  Size   Field               Encoding                            Hex (example)
──────  ────   ─────               ────────                            ─────────────
[0-1]   2B     Packet ID           Version=000|Type=0(TM)|Sec=0|APID  0x0064
[2-3]   2B     Sequence Control    Flags=11(standalone)|Count(14-bit)  0xC000+
[4-5]   2B     Data Length         payload_bytes - 1 = 11              0x000B
─── CCSDS Primary Header (6 bytes) ──────────────────────────────────────────────
[6-9]   4B     Latitude            IEEE 754 float, big-endian (deg)
[10-13] 4B     Longitude           IEEE 754 float, big-endian (deg)
[14-17] 4B     Altitude            IEEE 754 float, big-endian (km)
─── Payload (12 bytes) ─────────────────────────────────────────────────────────
```

### Coordinate Transformation Pipeline

```
TLE (NORAD)  ──►  SGP4/SDP4  ──►  TEME Frame  ──►  ITRF (Earth-Fixed)  ──►  Geodetic (LLA)
  epoch +           Orekit         Cartesian         Cartesian               lat (deg)
  mean elements     TLEPropagator  x, y, z           x, y, z                lon (deg)
                                                     WGS84 ellipsoid        alt (km)
```

### Threading Model

```
Java 21 Virtual Thread Pool (spring.threads.virtual.enabled=true)
│
├── HTTP Request Threads (one per request, virtual)
│   └── TleIngestionController.ingestTle()
│       └── OrbitPropagationService.updateTle()
│           └── AtomicReference<TLEPropagator>.set()    ← atomic write
│
└── Scheduler Thread (Spring @Scheduled, virtual)
    └── OrbitPropagationService.propagateAndSend() @ 1 Hz
        ├── AtomicReference<TLEPropagator>.get()        ← atomic read
        ├── TLEPropagator.propagate(now) → SpacecraftState
        ├── TEME → ITRF → WGS84 geodetic
        └── CcsdsTelemetrySender.sendPacket(lat, lon, alt)
            └── DatagramSocket.send() → UDP :10000
```

`AtomicReference<TLEPropagator>` provides lock-free thread safety between the HTTP thread (writing new TLEs) and the scheduler thread (reading for propagation). TLE updates take effect on the next 1-second tick with zero downtime.

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Language** | Java (LTS) | 21 | Virtual Threads for concurrent telemetry |
| **Framework** | Spring Boot | 3.2.5 | REST API, scheduling, dependency injection |
| **Astrodynamics** | Orekit | 12.2 | TLE parsing, SGP4/SDP4 propagation, reference frames |
| **Telemetry** | CCSDS Space Packet | 133.0-B-1 | Binary packet encoding over UDP |
| **Mission Control** | Yamcs | 5.12.2 | TM decoding, parameter archiving, web UI |
| **Build** | Maven + JaCoCo | 0.8.12 | Dependency management, code coverage |
| **Containers** | Docker Compose | — | Multi-stage builds, full-stack orchestration |

## Getting Started

### Prerequisites

- Java 21 SDK
- Docker (with Compose)
- Maven 3.9+

### Option A: Docker Compose (Full Stack)

```bash
docker compose up --build
```

This builds and starts both services. The `palantir-core` container waits for Yamcs to pass its healthcheck before starting. Telemetry flows immediately using a built-in default ISS TLE. Yamcs archive data is persisted in a named Docker volume (`palantir_yamcs_data`).

### Option B: Manual Setup

**Terminal 1 — Mission Control (Yamcs):**

```bash
docker build -t palantir-yamcs yamcs/
docker run --rm --name yamcs -p 8090:8090 -p 10000:10000/udp palantir-yamcs
```

Verify at http://localhost:8090.

**Terminal 2 — Physics Engine (Spring Boot):**

```bash
mvn package
mvn spring-boot:run
```

On startup you'll see:

```
CCSDS Telemetry Link initialized — target=localhost:10000
Earth model initialized — WGS84 ellipsoid, ITRF/IERS-2010
AOS — Acquired signal for [ISS (ZARYA)], TLE epoch: ..., propagator: SGP4
Default TLE loaded — propagation active for [ISS (ZARYA)]
```

Telemetry starts flowing immediately — no manual TLE ingestion required.

### Update TLE (Optional)

POST a fresh Two-Line Element set to switch satellites or update the orbit:

```bash
curl -X POST http://localhost:8080/api/orbit/tle \
  -H "Content-Type: application/json" \
  -d '{
    "satelliteName": "ISS (ZARYA)",
    "line1": "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9002",
    "line2": "2 25544  51.6400 208.9163 0006703 130.5360 325.0288 15.49560532999999"
  }'
```

Response:

```json
{
  "satelliteName": "ISS (ZARYA)",
  "status": "ACTIVE",
  "message": "TLE loaded, propagation started"
}
```

The propagator swaps atomically via `AtomicReference` — zero downtime during TLE updates.

## Usage

On startup the application loads a default ISS TLE and begins propagating immediately:

```
[ISS (ZARYA)] Position — lat=12.34 deg, lon=-45.67 deg, alt=407.32 km
```

In the Yamcs Web Interface (http://localhost:8090), navigate to **Parameters** and search for `Palantir`. Watch `/Palantir/Latitude`, `/Palantir/Longitude`, and `/Palantir/Altitude` update live.

## REST API

### POST /api/orbit/tle

Ingest a TLE and start (or update) orbit propagation.

**Request:**

```json
{
  "satelliteName": "ISS (ZARYA)",
  "line1": "1 25544U ...",
  "line2": "2 25544 ..."
}
```

**Responses:**

| Status | Body | Condition |
|---|---|---|
| `200 OK` | `{"status": "ACTIVE", "message": "TLE loaded, propagation started"}` | Valid TLE parsed successfully |
| `400 Bad Request` | `{"status": "REJECTED", "message": "..."}` | Missing name, missing lines, or invalid TLE format |

## Project Structure

```
palantir/
├── docker-compose.yaml                       # Full-stack orchestration (HTTP + UDP ports)
├── Dockerfile                                # Multi-stage Spring Boot build (Maven → JRE 21)
├── pom.xml                                   # Maven build with JaCoCo coverage
│
├── src/main/java/io/github/jakubt4/palantir/
│   ├── PalantirApplication.java              # @SpringBootApplication + @EnableScheduling
│   ├── config/
│   │   └── OrekitConfig.java                 # @PostConstruct — loads orekit-data.zip into Orekit
│   ├── controller/
│   │   └── TleIngestionController.java       # POST /api/orbit/tle — validates & delegates
│   ├── service/
│   │   ├── OrbitPropagationService.java      # SGP4 propagation @1Hz, atomic TLE hot-swap
│   │   └── CcsdsTelemetrySender.java         # CCSDS 133.0-B-1 encoding, UDP transport
│   └── dto/
│       ├── TleRequest.java                   # Inbound record: satelliteName, line1, line2
│       └── TleResponse.java                  # Outbound record: satelliteName, status, message
│
├── src/test/java/io/github/jakubt4/palantir/
│   ├── PalantirApplicationTests.java         # Integration — full context load
│   ├── controller/
│   │   └── TleIngestionControllerTest.java   # @WebMvcTest — 3 tests (valid, blank, bad TLE)
│   └── service/
│       └── OrbitPropagationServiceTest.java  # @SpringBootTest — 2 tests (init, propagation)
│
├── src/main/resources/
│   ├── application.yaml                      # Virtual Threads, UDP target, logging config
│   └── orekit-data.zip                       # Orekit physics data (leap seconds, EOPs)
│
└── yamcs/                                    # Custom Yamcs Docker image
    ├── Dockerfile                            # FROM yamcs/example-simulation:5.12.2
    ├── etc/
    │   ├── yamcs.yaml                        # Server — HTTP :8090, CORS, instance list
    │   ├── yamcs.palantir.yaml               # Instance — UdpTmDataLink, GenericPacketPreprocessor
    │   └── processor.yaml                    # Processor — StreamParameterProvider, archives
    └── mdb/
        └── palantir.xml                      # XTCE — CCSDS containers, APID=100, float params
```

## Yamcs Configuration

The Yamcs instance `palantir` is configured as follows:

| Component | Class | Purpose |
|---|---|---|
| **Data Link** | `UdpTmDataLink` (:10000) | Receives raw CCSDS packets over UDP |
| **Preprocessor** | `GenericPacketPreprocessor` | Extracts sequence count, assigns local generation time |
| **MDB** | XTCE `palantir.xml` | Decodes CCSDS containers by APID, extracts IEEE 754 floats |
| **Archive** | `XtceTmRecorder` + `ParameterRecorder` | Persists raw TM frames and decoded parameter values |
| **Processor** | `StreamParameterProvider` | Routes decoded TM parameters to the realtime processor |

**XTCE Container Hierarchy:**

```
CCSDS_Packet_Base (abstract)          ← 6-byte primary header
  └── Palantir_Nav_Packet             ← APID=100 restriction
        ├── Latitude   (float32, deg)
        ├── Longitude  (float32, deg)
        └── Altitude   (float32, km)
```

## Testing

```bash
mvn test                                   # Run all 6 tests + JaCoCo coverage
mvn test -Dtest=TleIngestionControllerTest # Run a single test class
mvn clean                                  # Clean build artifacts
```

Coverage report: `target/site/jacoco/index.html`

| Test Class | Type | Tests | What It Verifies |
|---|---|---|---|
| `PalantirApplicationTests` | Integration | 1 | Full Spring context loads (Orekit, services, scheduler) |
| `TleIngestionControllerTest` | `@WebMvcTest` | 3 | HTTP layer: valid TLE, blank name, invalid TLE |
| `OrbitPropagationServiceTest` | `@SpringBootTest` | 2 | Earth model init, propagated lat/lon/alt physical bounds |

## Configuration

| Property | Default | Env Override | Description |
|---|---|---|---|
| `yamcs.udp.host` | `localhost` | `YAMCS_UDP_HOST` | Yamcs UDP TM data link host |
| `yamcs.udp.port` | `10000` | `YAMCS_UDP_PORT` | Yamcs UDP TM data link port |
| `server.port` | `8080` | `SERVER_PORT` | Spring Boot HTTP port |
| `spring.threads.virtual.enabled` | `true` | — | Java 21 Virtual Threads |

In Docker Compose, `YAMCS_UDP_HOST` is set to `yamcs` so the Spring Boot container resolves the Yamcs container via Docker DNS.

## Orekit Physics Data

Orekit requires reference data (leap seconds, Earth orientation parameters, planetary ephemerides) to perform frame transformations and time conversions. The file `src/main/resources/orekit-data.zip` must be present on the classpath.

If missing, download from the [Orekit Data repository](https://gitlab.orekit.org/orekit/orekit-data) and place it in `src/main/resources/`.

## Future Improvements

- [x] CCSDS binary packet telemetry over UDP (replaced REST-based transport)
- [x] GenericPacketPreprocessor with local generation time
- [ ] Telecommanding — bidirectional TC/TM communication
- [ ] Multi-satellite tracking with concurrent TLE management
- [ ] Ground station visibility windows and pass prediction
- [ ] Kubernetes deployment with Yamcs

## Development Methodology

This project was built using an **AI-augmented workflow** (Claude Code). AI tools were leveraged for generating Orekit configuration boilerplate, accelerating Java 21 record definitions and Spring Boot wiring, and writing the test suite. **Core logic and architecture were design-reviewed and integrated by the human author.**

## Author

**Jakub Toth**
