# Project Palantir — Architectural Dump

## 1. Project Directory Tree

```
palantir/
├── .claude/
│   └── settings.local.json
├── .dockerignore
├── .gitignore
├── CLAUDE.md
├── Dockerfile
├── FEATURES.md
├── FLOW.md
├── LICENSE
├── README.md
├── docker-compose.yaml
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/io/github/jakubt4/palantir/
│   │   │   ├── PalantirApplication.java
│   │   │   ├── config/
│   │   │   │   └── OrekitConfig.java
│   │   │   ├── controller/
│   │   │   │   └── TleIngestionController.java
│   │   │   ├── dto/
│   │   │   │   ├── TleRequest.java
│   │   │   │   └── TleResponse.java
│   │   │   └── service/
│   │   │       ├── CcsdsTelemetrySender.java
│   │   │       ├── OrbitPropagationService.java
│   │   │       └── uplink/
│   │   │           └── UdpCommandReceiver.java
│   │   └── resources/
│   │       ├── application.yaml
│   │       └── orekit-data.zip
│   └── test/
│       ├── java/io/github/jakubt4/palantir/
│       │   ├── PalantirApplicationTests.java
│       │   ├── controller/
│       │   │   └── TleIngestionControllerTest.java
│       │   └── service/
│       │       └── OrbitPropagationServiceTest.java
│       └── resources/
│           └── application.yaml
└── yamcs/
    ├── Dockerfile
    ├── etc/
    │   ├── processor.yaml
    │   ├── yamcs.palantir.yaml
    │   └── yamcs.yaml
    └── mdb/
        └── palantir.xml
```

---

## 2. Build Manifest — `pom.xml`

**Verified:** Java 21, Orekit 12.2, Spring Boot 3.2.5, JaCoCo 0.8.12

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.5</version>
        <relativePath/>
    </parent>

    <groupId>io.github.jakubt4</groupId>
    <artifactId>palantir</artifactId>
    <version>0.1.0-SNAPSHOT</version>
    <name>palantir</name>
    <description>Orbital Telemetry Digital Twin</description>

    <properties>
        <java.version>21</java.version>
        <orekit.version>12.2</orekit.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <dependency>
            <groupId>org.orekit</groupId>
            <artifactId>orekit</artifactId>
            <version>${orekit.version}</version>
        </dependency>

        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.12</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

**Dependency matrix:**

| Dependency | Version | Purpose |
|---|---|---|
| Spring Boot Starter Web | 3.2.5 | REST API + embedded Tomcat |
| Orekit | 12.2 | SGP4/SDP4 orbit propagation |
| Lombok | (managed) | `@Slf4j`, `@RequiredArgsConstructor` |
| JaCoCo | 0.8.12 | Code coverage reporting |

> Note: Yamcs 5.12.2 is not a Maven dependency — it runs as a separate Docker container.

---

## 3. Container Orchestration

### `Dockerfile` (Spring Boot — Physics Engine)

```dockerfile
# Project Palantir - Physics Engine
FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -q
COPY src ./src
RUN mvn package -DskipTests -q

FROM eclipse-temurin:21-jre

WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

### `yamcs/Dockerfile` (Yamcs — Mission Control)

```dockerfile
# Project Palantir - Ground Segment
FROM yamcs/example-simulation:5.12.2

# Inject strict server and instance configurations
COPY etc/yamcs.yaml /opt/yamcs/etc/yamcs.yaml
COPY etc/yamcs.palantir.yaml /opt/yamcs/etc/yamcs.palantir.yaml
COPY etc/processor.yaml /opt/yamcs/etc/processor.yaml

# Inject the XTCE Mission Database
COPY mdb/palantir.xml /opt/yamcs/mdb/palantir.xml

EXPOSE 8090
EXPOSE 10000/udp
```

### `docker-compose.yaml`

```yaml
services:
  yamcs:
    build:
      context: ./yamcs
      dockerfile: Dockerfile
    container_name: palantir-yamcs
    ports:
      - "8090:8090"
      - "10000:10000/udp"
    volumes:
      - yamcs-data:/opt/yamcs/yamcs-data
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O /dev/null http://localhost:8090/api/ || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 15s

  palantir-core:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: palantir-core
    ports:
      - "8080:8080"
      - "10001:10001/udp"
    environment:
      - YAMCS_UDP_HOST=yamcs
    depends_on:
      yamcs:
        condition: service_started

volumes:
  yamcs-data:
    name: palantir_yamcs_data
```

**Key design decision:** `depends_on: service_started` (not `service_healthy`) — `palantir-core` must join the Docker network early so Yamcs can resolve `palantir-core` via Docker DNS when initializing `UdpTcDataLink`. Using `service_healthy` would cause a permanent DNS resolution failure.

---

## 4. Yamcs Configuration

### `yamcs/etc/yamcs.yaml` — Server Config

```yaml
services:
  - class: org.yamcs.http.HttpServer
    args:
      port: 8090
      cors:
        allowOrigin: "*"
        allowCredentials: false

instances:
  - palantir
```

### `yamcs/etc/yamcs.palantir.yaml` — Instance Config (Data Links, MDB, Streams)

```yaml
services:
  - class: org.yamcs.ProcessorCreatorService
    args:
      name: "realtime"
      type: "realtime"
  - class: org.yamcs.archive.XtceTmRecorder
  - class: org.yamcs.archive.ParameterRecorder
  - class: org.yamcs.archive.AlarmRecorder
  - class: org.yamcs.archive.CommandHistoryRecorder
  - class: org.yamcs.archive.ReplayServer

dataLinks:
  - name: udp-tm
    class: org.yamcs.tctm.UdpTmDataLink
    stream: tm_realtime
    port: 10000
    packetPreprocessorClassName: org.yamcs.tctm.GenericPacketPreprocessor
    packetPreprocessorArgs:
      timestampOffset: 0
      useLocalGenerationTime: true
      seqCountOffset: 2
      errorDetection:
        type: NONE
  - name: udp-tc
    class: org.yamcs.tctm.UdpTcDataLink
    stream: tc_realtime
    host: palantir-core
    port: 10001

mdb:
  - type: "xtce"
    spec: "mdb/palantir.xml"

streamConfig:
  tm:
    - name: "tm_realtime"
      processor: "realtime"
  tc:
    - name: "tc_realtime"
      processor: "realtime"
  cmdHist: ["cmdhist_realtime", "cmdhist_dump"]
  event: ["events_realtime"]
  param: ["pp_realtime", "sys_param", "proc_param"]
  parameterAlarm: ["alarms_realtime"]
  eventAlarm: ["event_alarms_realtime"]
```

### `yamcs/etc/processor.yaml` — Processor Definitions

```yaml
realtime:
  services:
    - class: org.yamcs.StreamTmPacketProvider
    - class: org.yamcs.tctm.StreamParameterProvider
    - class: org.yamcs.StreamTcCommandReleaser
  config:
    subscribeAll: true
    alarm:
      parameterCheck: true
      parameterServer: enabled
      eventServer: enabled

Archive:
  services:
    - class: org.yamcs.tctm.ReplayService

ParameterArchive:
  services:
    - class: org.yamcs.tctm.ReplayService

ArchiveRetrieval:
  services:
    - class: org.yamcs.tctm.ReplayService
```

### `yamcs/mdb/palantir.xml` — XTCE Mission Database

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SpaceSystem name="Palantir"
             xmlns="http://www.omg.org/spec/XTCE/20180204"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://www.omg.org/spec/XTCE/20180204 https://www.omg.org/spec/XTCE/20180204/SpaceSystem.xsd">

    <TelemetryMetaData>
        <ParameterTypeSet>
            <IntegerParameterType name="uint16_t" signed="false" sizeInBits="16">
                <IntegerDataEncoding sizeInBits="16" encoding="unsigned" byteOrder="mostSignificantByteFirst"/>
            </IntegerParameterType>

            <FloatParameterType name="float32_t" sizeInBits="32">
                <UnitSet><Unit>deg</Unit></UnitSet>
                <FloatDataEncoding sizeInBits="32" encoding="IEEE754_1985" byteOrder="mostSignificantByteFirst"/>
            </FloatParameterType>

            <FloatParameterType name="distance_t" sizeInBits="32">
                <UnitSet><Unit>km</Unit></UnitSet>
                <FloatDataEncoding sizeInBits="32" encoding="IEEE754_1985" byteOrder="mostSignificantByteFirst"/>
            </FloatParameterType>
        </ParameterTypeSet>

        <ParameterSet>
            <Parameter name="ccsds_packet_id" parameterTypeRef="uint16_t"/>
            <Parameter name="ccsds_seq_count" parameterTypeRef="uint16_t"/>
            <Parameter name="ccsds_length" parameterTypeRef="uint16_t"/>

            <Parameter name="Latitude" parameterTypeRef="float32_t">
                <ShortDescription>Satellite Geodetic Latitude</ShortDescription>
            </Parameter>
            <Parameter name="Longitude" parameterTypeRef="float32_t">
                <ShortDescription>Satellite Geodetic Longitude</ShortDescription>
            </Parameter>
            <Parameter name="Altitude" parameterTypeRef="distance_t">
                <ShortDescription>Satellite Altitude above Ellipsoid</ShortDescription>
            </Parameter>
        </ParameterSet>

        <ContainerSet>
            <SequenceContainer name="CCSDS_Packet_Base" abstract="true">
                <EntryList>
                    <ParameterRefEntry parameterRef="ccsds_packet_id"/>
                    <ParameterRefEntry parameterRef="ccsds_seq_count"/>
                    <ParameterRefEntry parameterRef="ccsds_length"/>
                </EntryList>
            </SequenceContainer>

            <SequenceContainer name="Palantir_Nav_Packet">
                <BaseContainer containerRef="CCSDS_Packet_Base">
                    <RestrictionCriteria>
                        <Comparison parameterRef="ccsds_packet_id" value="100" useCalibratedValue="false"/>
                    </RestrictionCriteria>
                </BaseContainer>

                <EntryList>
                    <ParameterRefEntry parameterRef="Latitude"/>
                    <ParameterRefEntry parameterRef="Longitude"/>
                    <ParameterRefEntry parameterRef="Altitude"/>
                </EntryList>
            </SequenceContainer>
        </ContainerSet>
    </TelemetryMetaData>

    <CommandMetaData>
        <ArgumentTypeSet>
            <IntegerArgumentType name="uint8_arg_t" signed="false" sizeInBits="8">
                <IntegerDataEncoding sizeInBits="8" encoding="unsigned"/>
            </IntegerArgumentType>
        </ArgumentTypeSet>

        <MetaCommandSet>
            <MetaCommand name="PING">
                <ArgumentList>
                    <Argument name="OpCode" argumentTypeRef="uint8_arg_t" initialValue="1"/>
                </ArgumentList>
                <CommandContainer name="PING_Container">
                    <EntryList>
                        <ArgumentRefEntry argumentRef="OpCode"/>
                    </EntryList>
                </CommandContainer>
            </MetaCommand>

            <MetaCommand name="REBOOT_OBC">
                <ArgumentList>
                    <Argument name="OpCode" argumentTypeRef="uint8_arg_t" initialValue="2"/>
                </ArgumentList>
                <CommandContainer name="REBOOT_OBC_Container">
                    <EntryList>
                        <ArgumentRefEntry argumentRef="OpCode"/>
                    </EntryList>
                </CommandContainer>
            </MetaCommand>
        </MetaCommandSet>
    </CommandMetaData>
</SpaceSystem>
```

---

## 5. Core Java Sources

### `PalantirApplication.java` — Entry Point

```java
package io.github.jakubt4.palantir;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class PalantirApplication {

    public static void main(String[] args) {
        SpringApplication.run(PalantirApplication.class, args);
    }
}
```

### `OrekitConfig.java` — Orekit Physics Data Bootstrap

This is where Orekit data (Earth orientation parameters, leap seconds, etc.) is injected into the runtime. All downstream Orekit calls depend on this initialization.

```java
package io.github.jakubt4.palantir.config;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.orekit.data.DataContext;
import org.orekit.data.ZipJarCrawler;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class OrekitConfig {

    @PostConstruct
    public void init() {
        final var orekitData = OrekitConfig.class.getClassLoader().getResource("orekit-data.zip");
        if (orekitData == null) {
            throw new IllegalStateException("orekit-data.zip not found on classpath");
        }
        final var crawler = new ZipJarCrawler(orekitData);
        DataContext.getDefault().getDataProvidersManager().addProvider(crawler);
        log.info("Orekit data loaded from classpath:orekit-data.zip");
    }
}
```

### `OrbitPropagationService.java` — SGP4 Propagation Engine / Yamcs Telemetry Bridge

This is the core class that bridges Orekit physics into the Yamcs telemetry stream. It propagates TLE at 1 Hz, converts TEME to ITRF to geodetic, and hands off to `CcsdsTelemetrySender`.

```java
package io.github.jakubt4.palantir.service;

import io.github.jakubt4.palantir.config.OrekitConfig;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.orekit.bodies.OneAxisEllipsoid;
import org.orekit.frames.FramesFactory;
import org.orekit.propagation.analytical.tle.TLE;
import org.orekit.propagation.analytical.tle.TLEPropagator;
import org.orekit.time.AbsoluteDate;
import org.orekit.time.TimeScalesFactory;
import org.orekit.utils.Constants;
import org.orekit.utils.IERSConventions;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Date;
import java.util.concurrent.atomic.AtomicReference;

@Slf4j
@Service
@RequiredArgsConstructor
public class OrbitPropagationService {

    private static final String DEFAULT_SAT_NAME = "ISS (ZARYA)";
    private static final String DEFAULT_TLE_LINE1 =
            "1 25544U 98067A   26046.82773376  .00012360  00000+0  23475-3 0  9996";
    private static final String DEFAULT_TLE_LINE2 =
            "2 25544  51.6318 180.4216 0010986 102.2508 257.9711 15.48632468552944";

    @SuppressWarnings("unused")
    private final OrekitConfig orekitConfig;
    private final CcsdsTelemetrySender ccsdsTelemetrySender;

    private final AtomicReference<TLEPropagator> activePropagator = new AtomicReference<>();
    private final AtomicReference<String> activeSatelliteName = new AtomicReference<>("NONE");

    private OneAxisEllipsoid earth;

    @PostConstruct
    void init() {
        final var itrf = FramesFactory.getITRF(IERSConventions.IERS_2010, true);
        earth = new OneAxisEllipsoid(
                Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                Constants.WGS84_EARTH_FLATTENING,
                itrf
        );
        log.info("Earth model initialized — WGS84 ellipsoid, ITRF/IERS-2010");
        loadDefaultTle();
    }

    private void loadDefaultTle() {
        try {
            updateTle(DEFAULT_SAT_NAME, DEFAULT_TLE_LINE1, DEFAULT_TLE_LINE2);
            log.info("Default TLE loaded — propagation active for [{}]", DEFAULT_SAT_NAME);
        } catch (final Exception e) {
            log.warn("Failed to load default TLE, awaiting manual ingestion: {}", e.getMessage());
        }
    }

    public void updateTle(final String satelliteName, final String line1, final String line2) {
        final var tle = new TLE(line1, line2);
        final var propagator = TLEPropagator.selectExtrapolator(tle);
        activePropagator.set(propagator);
        activeSatelliteName.set(satelliteName);
        log.info("AOS — Acquired signal for [{}], TLE epoch: {}, propagator: {}",
                satelliteName, tle.getDate(), propagator.getClass().getSimpleName());
    }

    @Scheduled(fixedRate = 1000)
    public void propagateAndSend() {
        final var propagator = activePropagator.get();
        if (propagator == null) {
            log.debug("WAITING_FOR_TLE — No active propagator, awaiting TLE ingestion");
            return;
        }

        try {
            final var now = new AbsoluteDate(Date.from(Instant.now()), TimeScalesFactory.getUTC());
            final var state = propagator.propagate(now);
            final var position = state.getPVCoordinates(earth.getBodyFrame()).getPosition();
            final var geo = earth.transform(position, earth.getBodyFrame(), now);

            final var latDeg = Math.toDegrees(geo.getLatitude());
            final var lonDeg = Math.toDegrees(geo.getLongitude());
            final var altKm = geo.getAltitude() / 1000.0;

            log.info("[{}] Position — lat={} deg, lon={} deg, alt={} km",
                    activeSatelliteName.get(),
                    String.format("%.2f", latDeg),
                    String.format("%.2f", lonDeg),
                    String.format("%.2f", altKm));

            ccsdsTelemetrySender.sendPacket((float) latDeg, (float) lonDeg, (float) altKm);
        } catch (final Exception e) {
            log.error("[{}] Propagation error: {}", activeSatelliteName.get(), e.getMessage());
        }
    }
}
```

### `CcsdsTelemetrySender.java` — CCSDS Packet Encoder + UDP Transport

```java
package io.github.jakubt4.palantir.service;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.util.HexFormat;
import java.util.concurrent.atomic.AtomicInteger;

@Slf4j
@Service
public class CcsdsTelemetrySender {

    private static final int APID = 100;
    private static final int CCSDS_HEADER_LENGTH = 6;
    private static final int PAYLOAD_LENGTH = 12; // 3 floats x 4 bytes
    private static final int TOTAL_LENGTH = CCSDS_HEADER_LENGTH + PAYLOAD_LENGTH;

    private final AtomicInteger sequenceCounter = new AtomicInteger(0);

    @Value("${yamcs.udp.host:localhost}")
    private String host;

    @Value("${yamcs.udp.port:10000}")
    private int port;

    private DatagramSocket socket;
    private InetAddress address;

    @PostConstruct
    void init() throws SocketException, UnknownHostException {
        socket = new DatagramSocket();
        address = InetAddress.getByName(host);
        log.info("CCSDS Telemetry Link initialized — target={}:{}", host, port);
    }

    @PreDestroy
    void destroy() {
        if (socket != null && !socket.isClosed()) {
            socket.close();
            log.info("CCSDS Telemetry Link closed");
        }
    }

    public void sendPacket(final float lat, final float lon, final float alt) {
        final var buffer = ByteBuffer.allocate(TOTAL_LENGTH);

        // Packet ID: Version(000) | Type(0) | SecHeader(0) | APID(11 bits)
        final var packetId = (short) (APID & 0x07FF);
        buffer.putShort(packetId);

        // Sequence Control: Grouping Flags(11 = standalone) | Sequence Count(14 bits)
        final var seqCount = sequenceCounter.getAndIncrement() & 0x3FFF;
        final var seqControl = (short) (0xC000 | seqCount);
        buffer.putShort(seqControl);

        // Data Length: octets in Packet Data Field minus 1
        final var dataLength = (short) (PAYLOAD_LENGTH - 1);
        buffer.putShort(dataLength);

        // Payload: 3 x IEEE 754 float, big-endian (ByteBuffer default)
        buffer.putFloat(lat);
        buffer.putFloat(lon);
        buffer.putFloat(alt);

        try {
            final var data = buffer.array();
            final var packet = new DatagramPacket(data, data.length, address, port);
            socket.send(packet);
            final var hexFmt = HexFormat.ofDelimiter(" ");
            final var hdrHex = hexFmt.formatHex(data, 0, CCSDS_HEADER_LENGTH);
            final var payloadHex = hexFmt.formatHex(data, CCSDS_HEADER_LENGTH, TOTAL_LENGTH);
            log.debug("TX CCSDS [APID={}, SEQ={}, {} bytes] -> {}:{} | lat={}, lon={}, alt={} km\n"
                            + "         HDR: [{}]  DATA: [{}]",
                    APID, seqCount, data.length, host, port, lat, lon, alt,
                    hdrHex, payloadHex);
        } catch (final IOException e) {
            log.error("Failed to transmit CCSDS packet: {}", e.getMessage());
        }
    }
}
```

### `UdpCommandReceiver.java` — Telecommand Uplink Listener

```java
package io.github.jakubt4.palantir.service.uplink;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Slf4j
@Service
public class UdpCommandReceiver {

    private final int port;
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
    private DatagramSocket socket;
    private volatile boolean running = true;

    public UdpCommandReceiver(@Value("${palantir.uplink.port:10001}") final int port) {
        this.port = port;
    }

    @PostConstruct
    void startListening() {
        executor.submit(() -> {
            try {
                socket = new DatagramSocket(port);
                log.info("[UPLINK] SYSTEM ONLINE | Listening on UDP port {}", socket.getLocalPort());

                final var buffer = new byte[1024];
                while (running) {
                    final var packet = new DatagramPacket(buffer, buffer.length);
                    socket.receive(packet);
                    processTelecommand(packet);
                }
            } catch (final IOException e) {
                if (running) {
                    log.error("[UPLINK] CRITICAL FAILURE: {}", e.getMessage());
                }
            }
        });
    }

    private void processTelecommand(final DatagramPacket packet) {
        final var data = packet.getData();
        final var opCode = data[0];

        final var commandName = switch (opCode) {
            case 0x01 -> "PING / NOOP";
            case 0x02 -> "REBOOT_OBC";
            case 0x03 -> "SET_TRANSMIT_POWER";
            default -> "UNKNOWN_OPCODE (0x" + String.format("%02X", opCode) + ")";
        };

        log.warn("[COMMAND RECEIVED] Source: {}:{} | OpCode: 0x{} | Executing: {}",
                packet.getAddress().getHostAddress(),
                packet.getPort(),
                String.format("%02X", opCode),
                commandName);

        if (opCode == 0x02) {
            triggerRebootSequence();
        }
    }

    private void triggerRebootSequence() {
        log.info("[UPLINK] INITIATING SYSTEM REBOOT SEQUENCE");
    }

    @PreDestroy
    void stop() {
        running = false;
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }
        executor.shutdown();
        log.info("[UPLINK] SYSTEM OFFLINE");
    }
}
```

### `TleIngestionController.java` — REST API

```java
package io.github.jakubt4.palantir.controller;

import io.github.jakubt4.palantir.dto.TleRequest;
import io.github.jakubt4.palantir.dto.TleResponse;
import io.github.jakubt4.palantir.service.OrbitPropagationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/orbit")
@RequiredArgsConstructor
public class TleIngestionController {

    private final OrbitPropagationService orbitPropagationService;

    @PostMapping("/tle")
    public ResponseEntity<TleResponse> ingestTle(@RequestBody final TleRequest request) {
        if (request.satelliteName() == null || request.satelliteName().isBlank()) {
            return ResponseEntity.badRequest()
                    .body(new TleResponse(null, "REJECTED", "Satellite name is required"));
        }
        if (request.line1() == null || request.line2() == null) {
            return ResponseEntity.badRequest()
                    .body(new TleResponse(request.satelliteName(), "REJECTED",
                            "TLE line1 and line2 are required"));
        }

        try {
            orbitPropagationService.updateTle(
                    request.satelliteName(), request.line1(), request.line2());
            log.info("TLE ingested for satellite [{}]", request.satelliteName());
            return ResponseEntity.ok(
                    new TleResponse(request.satelliteName(), "ACTIVE",
                            "TLE loaded, propagation started"));
        } catch (final Exception e) {
            log.error("Failed to parse TLE for [{}]: {}", request.satelliteName(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(new TleResponse(request.satelliteName(), "REJECTED",
                            "Invalid TLE: " + e.getMessage()));
        }
    }
}
```

### DTOs — `TleRequest.java` & `TleResponse.java`

```java
public record TleRequest(String satelliteName, String line1, String line2) {}

public record TleResponse(String satelliteName, String status, String message) {}
```

### `application.yaml` — Spring Boot Configuration

```yaml
spring:
  application:
    name: palantir
  threads:
    virtual:
      enabled: true

server:
  port: 8080

logging:
  level:
    io.github.jakubt4.palantir: DEBUG

yamcs:
  udp:
    host: ${YAMCS_UDP_HOST:localhost}
    port: ${YAMCS_UDP_PORT:10000}
```

---

## 6. End-to-End Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOWNLINK (TM)                                │
│                                                                     │
│  OrekitConfig          OrbitPropagationService    CcsdsTelemetrySender
│  ┌──────────┐          ┌───────────────────┐     ┌──────────────────┐
│  │orekit-   │ init()   │ TLEPropagator     │     │ CCSDS 133.0-B-1 │
│  │data.zip  │────────→ │ @Scheduled(1Hz)   │────→│ 18B packets     │
│  │(WGS84,   │          │ SGP4→TEME→ITRF→   │     │ APID=100        │
│  │ EOP)     │          │ geodetic(lat/lon/  │     │ UDP :10000      │
│  └──────────┘          │ alt)               │     └────────┬─────────┘
│                        └───────────────────┘              │
│                                                           ▼
│  ┌────────────────────────────────────────────────────────────────┐
│  │ Yamcs 5.12.2 (Docker)                                         │
│  │  UdpTmDataLink(:10000) → GenericPacketPreprocessor            │
│  │  → tm_realtime stream → StreamTmPacketProvider                │
│  │  → XTCE MDB (palantir.xml) → Latitude/Longitude/Altitude     │
│  │  → HttpServer(:8090) → WebSocket → Browser                   │
│  └────────────────────────────────────────────────────────────────┘
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        UPLINK (TC)                                  │
│                                                                     │
│  Yamcs UdpTcDataLink ──UDP:10001──→ UdpCommandReceiver             │
│  (PING/REBOOT_OBC)                  (opcode dispatch, VirtualThread)│
└─────────────────────────────────────────────────────────────────────┘
```
