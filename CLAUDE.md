# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Palantir** is a Digital Twin ground segment PoC that bridges astrodynamics simulation with mission control. It simulates a satellite in Low Earth Orbit using Orekit, encoding geodetic telemetry into CCSDS Space Packets (CCSDS 133.0-B-1) and streaming them over UDP to a Yamcs mission control instance.

**Architecture:** Two-pillar design:
- **Physics Engine (port 8080):** Spring Boot 3.2.5 app using Orekit 12.2 for SGP4/SDP4 TLE-based orbit propagation, with Java 21 Virtual Threads for high-throughput telemetry generation. Accepts TLE uploads via REST, propagates at 1 Hz, encodes CCSDS packets over UDP.
- **Mission Control (port 8090):** Yamcs 5.12.2 Docker container (instance `palantir`) receiving raw CCSDS telemetry via UdpTmDataLink, decoding via XTCE MDB, serving a web UI over WebSocket.

Data flow: `Operator --TLE POST--> Spring Boot (Orekit SGP4) --CCSDS/UDP--> Yamcs (Docker) --WebSocket--> Browser`

## Build & Run Commands

```bash
# Docker Compose — full stack (builds both Yamcs and Spring Boot)
docker compose up --build

# OR manual setup:
# Build & start Yamcs (Terminal 1)
docker build -t palantir-yamcs yamcs/
docker run --rm --name yamcs -p 8090:8090 -p 10000:10000/udp palantir-yamcs

# Build & run Spring Boot (Terminal 2)
mvn package
mvn spring-boot:run

# Ingest a TLE to start propagation (optional — default ISS TLE loads at startup)
curl -X POST http://localhost:8080/api/orbit/tle \
  -H "Content-Type: application/json" \
  -d '{"satelliteName":"ISS","line1":"1 25544U ...","line2":"2 25544 ..."}'

# Run all tests
mvn test

# Run a single test class
mvn test -Dtest=TleIngestionControllerTest

# Clean build artifacts
mvn clean
```

## Tech Stack

- **Java 21** (required — Virtual Threads enabled via `application.yaml`)
- **Spring Boot 3.2.5** with `@EnableScheduling` for periodic telemetry
- **Orekit 12.2** for orbital mechanics (requires `orekit-data.zip` in `src/main/resources/`)
- **Lombok** for boilerplate reduction (`@Slf4j`, `@RequiredArgsConstructor`)
- **Maven** as build tool, **JaCoCo** for code coverage (`target/site/jacoco/index.html`)
- **Yamcs 5.12.2** as mission control (custom Docker image based on `yamcs/example-simulation:5.12.2`)
- **Docker Compose** for full-stack orchestration (Yamcs + Spring Boot)

## Architecture Details

The app is a Spring Boot service that initializes Orekit physics data at startup, loads a default ISS TLE, then periodically propagates a satellite orbit and pushes CCSDS-encoded telemetry to Yamcs over UDP.

- **`PalantirApplication`** — `@SpringBootApplication` + `@EnableScheduling`. Entry point.
- **`config/OrekitConfig`** — `@PostConstruct` loads `orekit-data.zip` from classpath into Orekit's `DataProvidersManager`. Must succeed for any Orekit call to work.
- **`controller/TleIngestionController`** — `@RestController` exposing `POST /api/orbit/tle`. Validates satellite name and TLE lines, delegates to `OrbitPropagationService.updateTle()`, catches Orekit parsing exceptions.
- **`service/OrbitPropagationService`** — `@Service` with `@Scheduled(fixedRate=1000)`. Uses `AtomicReference<TLEPropagator>` for thread-safe dynamic TLE swapping. `@PostConstruct` initializes WGS84 Earth model and loads a default ISS TLE. `propagateAndSend()` has a null guard when no TLE is loaded. Propagates via SGP4, converts TEME→ITRF→geodetic, sends lat/lon/alt as floats to `CcsdsTelemetrySender`.
- **`service/CcsdsTelemetrySender`** — `@Service` that encodes geodetic telemetry as 20-byte CCSDS Space Packets (6B header + 12B payload + 2B CFS checksum) and transmits via `DatagramSocket` over UDP. Uses `AtomicInteger` for 14-bit CCSDS sequence counter. Target host/port configurable via `@Value` with env var overrides. `@PostConstruct` creates the socket, `@PreDestroy` closes it.
- **`dto/`** — Java records: `TleRequest` (satelliteName, line1, line2) and `TleResponse` (satelliteName, status, message) for the TLE ingestion API.
- **`yamcs/`** — Custom Yamcs Docker image based on `yamcs/example-simulation:5.12.2`. Instance named `palantir`. Config files:
  - `etc/yamcs.yaml` — Server config (HTTP on 8090, CORS enabled, single `palantir` instance).
  - `etc/yamcs.palantir.yaml` — Instance config (UdpTmDataLink on port 10000, GenericPacketPreprocessor with local generation time and no error detection, XTCE MDB loader, archive services, stream config).
  - `etc/processor.yaml` — Realtime processor with `StreamParameterProvider` (routes decoded TM params) and `LocalParameterManager`. Archive/replay processors with `ReplayService`.
  - `mdb/palantir.xml` — XTCE defining CCSDS binary containers: abstract `CCSDS_Packet_Base` (6B header) with `Palantir_Nav_Packet` (APID=100 restriction, 3 IEEE 754 float parameters: Latitude deg, Longitude deg, Altitude km).
- **`docker-compose.yaml`** (project root) — Orchestrates `yamcs` and `palantir-core` services. Yamcs has a healthcheck (`GET /api/`), persistent volume (`palantir_yamcs_data`), and the Spring Boot service depends on Yamcs health. `YAMCS_UDP_HOST=yamcs` env var enables Docker DNS resolution.
- **`Dockerfile`** (project root) — Multi-stage build for the Spring Boot app: Maven + JDK 21 build stage, JRE 21 runtime stage.

## Testing

Tests use JUnit 5, Mockito, and AssertJ (all provided by `spring-boot-starter-test`).

- **Controller tests** (`controller/TleIngestionControllerTest`) — `@WebMvcTest` with mocked `OrbitPropagationService`. Tests valid TLE ingestion, blank satellite name rejection, and invalid TLE format rejection.
- **Service tests** (`service/OrbitPropagationServiceTest`) — `@SpringBootTest` with `@MockBean` for `CcsdsTelemetrySender`. Requires full Spring context (Orekit data must load). Uses `ArgumentCaptor<Float>` to validate propagated orbital values are physically plausible (lat ±90, lon ±180, alt > 0).
- **Integration test** (`PalantirApplicationTests`) — Validates full context loads.

Note: `@SpringBootTest` tests start the scheduler, so `OrbitPropagationServiceTest` uses `Mockito.clearInvocations()` in `@BeforeEach` and `atLeastOnce()` verification to handle concurrent scheduler calls.

## Key Paths

- Entry point: `src/main/java/io/github/jakubt4/palantir/PalantirApplication.java`
- Config: `src/main/resources/application.yaml`
- Orekit physics data: `src/main/resources/orekit-data.zip` (must be present; download from Orekit GitLab if missing)
- Yamcs Docker config: `yamcs/` (Dockerfile, XTCE MDB, instance/server/processor config)
- Docker Compose: `docker-compose.yaml` (project root)
- Package namespace: `io.github.jakubt4.palantir`

## Code Style

- **Always use `var`** for local variable declarations. Never spell out the type when it can be inferred.
- **Use `final`** on local variables that are not reassigned, method parameters, and fields that are set once (constructor / `@PostConstruct`). If a value doesn't change after assignment, it must be `final`.
- Act as a **senior architect**: favor clean, minimal APIs; push complexity down into well-named methods; challenge unnecessary abstraction; prefer composition over inheritance; keep classes small and focused on a single responsibility.
