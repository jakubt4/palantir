# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Palantir** is a Digital Twin ground segment PoC that bridges astrodynamics simulation with mission control. It simulates a satellite in Low Earth Orbit using Orekit, streaming real-time telemetry (position, velocity, sensor data) to a Yamcs mission control instance.

**Architecture:** Two-pillar design:
- **Physics Engine (port 8080):** Spring Boot 3.2.5 app using Orekit 12.2 for SGP4/SDP4 TLE-based orbit propagation, with Java 21 Virtual Threads for high-throughput telemetry generation. Accepts TLE uploads via REST, propagates at 1 Hz.
- **Mission Control (port 8090):** Yamcs 5.12.2 Docker container (instance `palantir`) receiving telemetry via REST, serving a web UI over WebSocket.

Data flow: `Operator --TLE POST--> Spring Boot (Orekit SGP4) --JSON/REST--> Yamcs (Docker) --WebSocket--> Browser`

## Build & Run Commands

```bash
# Docker Compose — full stack (builds both Yamcs and Spring Boot)
docker compose up --build

# OR manual setup:
# Build & start Yamcs (Terminal 1)
docker build -t palantir-yamcs yamcs/
docker run --rm --name yamcs -p 8090:8090 palantir-yamcs

# Build & run Spring Boot (Terminal 2)
mvn package
mvn spring-boot:run

# Ingest a TLE to start propagation
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
- **Lombok** for boilerplate reduction (`@Slf4j`, etc.)
- **Spring Retry** with `@Retryable` for resilient telemetry delivery
- **Maven** as build tool, **Jacoco** for code coverage (`target/site/jacoco/index.html`)
- **Yamcs 5.12.2** as mission control (custom Docker image based on `yamcs/example-simulation:5.12.2`)
- **Docker Compose** for full-stack orchestration (Yamcs + Spring Boot)

## Architecture Details

The app is a Spring Boot service that initializes Orekit physics data at startup, then periodically propagates a satellite orbit and pushes telemetry to Yamcs via REST.

- **`config/OrekitConfig`** — `@PostConstruct` loads `orekit-data.zip` from classpath into Orekit's `DataProvidersManager`. Must succeed for any Orekit call to work.
- **`controller/TleIngestionController`** — `@RestController` exposing `POST /api/orbit/tle`. Validates satellite name and TLE lines, delegates to `OrbitPropagationService.updateTle()`, catches Orekit parsing exceptions.
- **`service/OrbitPropagationService`** — `@Service` with `@Scheduled(fixedRate=1000)`. Uses `AtomicReference<TLEPropagator>` for thread-safe dynamic TLE swapping. `@PostConstruct` initializes WGS84 Earth model. `propagateAndSend()` has a WAITING_FOR_TLE guard when no TLE is loaded. Propagates via SGP4, converts TEME→ITRF→geodetic, sends lat/lon/alt to Yamcs.
- **`client/YamcsTelemetryClient`** — `@Service` using Spring's `RestClient` (injected via `RestClient.Builder`) to POST parameter values to the Yamcs REST API at `/api/processors/palantir/realtime/parameters:batchSet`. Uses `@Retryable` (3 attempts, 500ms backoff) with `@Recover` for graceful degradation. Yamcs base URL is configured via `yamcs.base-url` (overridable via `YAMCS_URL` env var).
- **`config/RestClientConfig`** — `RestClientCustomizer` bean that sets 5s connect/read timeouts on the auto-configured `RestClient.Builder`.
- **`dto/`** — Java records: `TleRequest`/`TleResponse` for the ingestion API; `YamcsParameterRequest`, `ParameterValue`, `ValueHolder` for the Yamcs REST API payload.
- **`yamcs/`** — Custom Yamcs Docker image based on `yamcs/example-simulation:5.12.2`. Instance named `palantir` (not `simulator`). Config files:
  - `etc/yamcs.yaml` — Server config (HTTP on 8090, CORS enabled, single `palantir` instance).
  - `etc/yamcs.palantir.yaml` — Instance config (MDB loader, archive services, stream config for events/params/alarms).
  - `etc/processor.yaml` — Custom processor excluding `StreamTmPacketProvider` and `StreamTcCommandReleaser` (we only use LOCAL parameters, no TM/TC streams).
  - `mdb/palantir.xml` — XTCE defining LOCAL float parameters (`/Palantir/Latitude` deg, `/Palantir/Longitude` deg, `/Palantir/Altitude` km).
- **`docker-compose.yaml`** (project root) — Orchestrates `yamcs` and `palantir-core` services. Yamcs has a healthcheck (`GET /api/`), persistent volume, and the Spring Boot service depends on Yamcs health. `YAMCS_URL` env var overrides the default localhost URL for Docker networking.
- **`Dockerfile`** (project root) — Multi-stage build for the Spring Boot app: Maven + JDK 21 build stage, JRE 21 runtime stage.

## Testing

Tests use JUnit 5, Mockito, and AssertJ (all provided by `spring-boot-starter-test`).

- **DTO tests** (`dto/YamcsParameterRequestTest`) — Pure unit tests, no Spring context. Use Jackson `ObjectMapper` to verify JSON serialization matches Yamcs API expectations.
- **Client tests** (`client/YamcsTelemetryClientTest`) — Use `MockRestServiceServer` with a mock-backed `RestClient.Builder` passed via constructor. Verify HTTP method, URI, content type, and JSON body structure without a running Yamcs instance.
- **Service tests** (`service/OrbitPropagationServiceTest`) — `@SpringBootTest` with `@MockBean` for `YamcsTelemetryClient`. Requires full Spring context (Orekit data must load). Uses `ArgumentCaptor` to validate propagated orbital values are physically plausible.
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
