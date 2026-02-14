# Project Palantir: Orbital Telemetry Digital Twin

> *"They were not made by Sauron... They were made by the Noldor in Eldamar... to see far off, and to converse in thought with one another."* — Gandalf on the Palantiri

## About The Project

Project Palantir is a Proof of Concept (PoC) constructing a "Digital Twin" ground segment environment. It bridges astrodynamics simulation with operational mission control software — operators ingest real Two-Line Element sets (TLEs) via a REST API, and the system propagates the satellite orbit in real time using SGP4/SDP4, streaming geodetic telemetry to a Yamcs mission control instance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                               │
│                                                                     │
│  ┌──────────────────────────────┐   ┌────────────────────────────┐  │
│  │   palantir-core (:8080)      │   │   palantir-yamcs (:8090)   │  │
│  │                              │   │                            │  │
│  │  ┌────────────────────────┐  │   │  ┌──────────────────────┐  │  │
│  │  │  TleIngestionController│  │   │  │   Yamcs Server       │  │  │
│  │  │  POST /api/orbit/tle   │  │   │  │   Instance: palantir │  │  │
│  │  └──────────┬─────────────┘  │   │  │                      │  │  │
│  │             │                │   │  │  Parameters (LOCAL):  │  │  │
│  │  ┌──────────▼─────────────┐  │   │  │  /Palantir/Latitude  │  │  │
│  │  │ OrbitPropagationService│  │   │  │  /Palantir/Longitude │  │  │
│  │  │ TLE → SGP4 → Geodetic  │  │   │  │  /Palantir/Altitude  │  │  │
│  │  │ @Scheduled(1s)         │  │   │  └──────────────────────┘  │  │
│  │  └──────────┬─────────────┘  │   │             │              │  │
│  │             │                │   │         WebSocket           │  │
│  │  ┌──────────▼─────────────┐  │   │             │              │  │
│  │  │ YamcsTelemetryClient   │──┼───┼──► REST     ▼              │  │
│  │  │ @Retryable (3x, 500ms)│  │   │     batchSet    Browser UI │  │
│  │  └────────────────────────┘  │   │                            │  │
│  │                              │   │                            │  │
│  │  Spring Boot 3.2 / Java 21  │   │  Yamcs 5.12.2 / XTCE MDB  │  │
│  └──────────────────────────────┘   └────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
  Operator                  Spring Boot (Physics Engine)                     Yamcs (Mission Control)
     │                              │                                               │
     │  POST /api/orbit/tle         │                                               │
     │  {satelliteName, line1, line2}                                               │
     │─────────────────────────────►│                                               │
     │                              │                                               │
     │  200 OK {status: ACTIVE}     │                                               │
     │◄─────────────────────────────│                                               │
     │                              │                                               │
     │                              │──── Every 1 second ────┐                      │
     │                              │                        │                      │
     │                              │  1. Parse TLE (SGP4)   │                      │
     │                              │  2. Propagate to now   │                      │
     │                              │  3. TEME → ITRF        │                      │
     │                              │  4. Cartesian → LLA    │                      │
     │                              │                        │                      │
     │                              │◄───────────────────────┘                      │
     │                              │                                               │
     │                              │  POST /api/processors/palantir/realtime/      │
     │                              │        parameters:batchSet                    │
     │                              │  {Latitude, Longitude, Altitude}              │
     │                              │──────────────────────────────────────────────►│
     │                              │                                               │
     │                              │                                   WebSocket   │
     │                              │                                       │       │
     │                              │                                       ▼       │
     │                              │                                   Browser UI  │
```

### Coordinate Transformation Pipeline

```
TLE (NORAD)  ──►  SGP4/SDP4  ──►  TEME Frame  ──►  ITRF (Earth-Fixed)  ──►  Geodetic (LLA)
  epoch +           Orekit         Cartesian         Cartesian               lat (deg)
  mean elements     TLEPropagator  x, y, z           x, y, z                lon (deg)
                                                     WGS84 ellipsoid        alt (km)
```

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Language** | Java (LTS) | 21 | Virtual Threads for concurrent telemetry |
| **Framework** | Spring Boot | 3.2.5 | REST API, scheduling, dependency injection |
| **Astrodynamics** | Orekit | 12.2 | TLE parsing, SGP4/SDP4 propagation, reference frames |
| **Resilience** | Spring Retry | — | `@Retryable` (3 attempts, 500ms backoff) for Yamcs comms |
| **Mission Control** | Yamcs | 5.12.2 | Telemetry archiving, parameter display, web UI |
| **Build** | Maven + JaCoCo | — | Dependency management, code coverage |
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

This builds and starts both services. The `palantir-core` container waits for Yamcs to pass its healthcheck before starting. Yamcs telemetry data is persisted in a named Docker volume (`palantir_yamcs_data`).

### Option B: Manual Setup

**Terminal 1 — Mission Control (Yamcs):**

```bash
docker build -t palantir-yamcs yamcs/
docker run --rm --name yamcs -p 8090:8090 palantir-yamcs
```

Verify at http://localhost:8090.

**Terminal 2 — Physics Engine (Spring Boot):**

```bash
mvn package
mvn spring-boot:run
```

On startup you'll see:

```
Earth model initialized — WGS84 ellipsoid, ITRF/IERS-2010
WAITING_FOR_TLE — No active propagator, awaiting TLE ingestion
```

### Ingest a TLE

POST a Two-Line Element set to start propagation:

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

You can update the TLE at any time — the propagator swaps atomically via `AtomicReference`.

## Usage

Once a TLE is ingested, the application logs real-time position every second:

```
AOS — Acquired signal for [ISS (ZARYA)], TLE epoch: 2024-01-01T12:00:00Z, propagator: SGP4
[ISS (ZARYA)] Position — lat=12.34 °, lon=-45.67 °, alt=407.32 km
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
├── docker-compose.yaml                       # Full-stack orchestration
├── Dockerfile                                # Multi-stage Spring Boot build (Maven → JRE 21)
├── pom.xml                                   # Maven build with JaCoCo coverage
│
├── src/main/java/io/github/jakubt4/palantir/
│   ├── PalantirApplication.java              # @SpringBootApplication + @EnableScheduling + @EnableRetry
│   ├── config/
│   │   ├── OrekitConfig.java                 # @PostConstruct — loads orekit-data.zip into Orekit
│   │   └── RestClientConfig.java             # RestClientCustomizer — 5s connect/read timeouts
│   ├── controller/
│   │   └── TleIngestionController.java       # POST /api/orbit/tle — validates & delegates
│   ├── service/
│   │   └── OrbitPropagationService.java      # SGP4 propagation, @Scheduled(1s), AtomicReference swap
│   ├── client/
│   │   └── YamcsTelemetryClient.java         # RestClient + @Retryable → Yamcs batchSet
│   └── dto/
│       ├── TleRequest.java                   # Inbound: satelliteName, line1, line2
│       ├── TleResponse.java                  # Outbound: satelliteName, status, message
│       ├── YamcsParameterRequest.java        # Yamcs API: request wrapper
│       ├── ParameterValue.java               # Yamcs API: {id: {name}, value: {type, floatValue}}
│       └── ValueHolder.java                  # Yamcs API: {type: "FLOAT", floatValue: ...}
│
├── src/test/java/io/github/jakubt4/palantir/
│   ├── PalantirApplicationTests.java         # Integration — full context load
│   ├── controller/
│   │   └── TleIngestionControllerTest.java   # @WebMvcTest — 3 tests (valid, blank name, bad TLE)
│   ├── service/
│   │   └── OrbitPropagationServiceTest.java  # @SpringBootTest — 3 tests (init, guard, propagation)
│   ├── client/
│   │   └── YamcsTelemetryClientTest.java     # MockRestServiceServer — 2 tests (payload, failure)
│   └── dto/
│       └── YamcsParameterRequestTest.java    # Pure unit — 2 tests (JSON shape, factory method)
│
├── src/main/resources/
│   ├── application.yaml                      # Spring config (Virtual Threads, Yamcs URL, logging)
│   └── orekit-data.zip                       # Orekit physics data (leap seconds, EOPs, ephemerides)
│
└── yamcs/                                    # Custom Yamcs Docker image
    ├── Dockerfile                            # FROM yamcs/example-simulation:5.12.2
    ├── etc/
    │   ├── yamcs.yaml                        # Server — HTTP :8090, CORS, instance list
    │   ├── yamcs.palantir.yaml               # Instance — MDB, archive services, stream config
    │   └── processor.yaml                    # Processor — LOCAL params only (no TM/TC streams)
    └── mdb/
        └── palantir.xml                      # XTCE — Latitude (deg), Longitude (deg), Altitude (km)
```

## Testing

```bash
mvn test                                   # Run all 11 tests + JaCoCo coverage
mvn test -Dtest=TleIngestionControllerTest # Run a single test class
```

Coverage report: `target/site/jacoco/index.html`

| Test Class | Type | Tests | What It Verifies |
|---|---|---|---|
| `PalantirApplicationTests` | Integration | 1 | Full Spring context loads successfully |
| `TleIngestionControllerTest` | `@WebMvcTest` | 3 | TLE validation: valid input, blank name, invalid TLE |
| `OrbitPropagationServiceTest` | `@SpringBootTest` | 3 | Earth model init, no-TLE guard, SGP4 lat/lon/alt bounds |
| `YamcsTelemetryClientTest` | `MockRestServiceServer` | 2 | REST payload correctness, connection failure resilience |
| `YamcsParameterRequestTest` | Pure unit | 2 | JSON serialization shape, `ValueHolder.ofFloat` factory |

## Configuration

| Property | Default | Env Override | Description |
|---|---|---|---|
| `yamcs.base-url` | `http://localhost:8090` | `YAMCS_URL` | Yamcs server URL |
| `server.port` | `8080` | `SERVER_PORT` | Spring Boot HTTP port |
| `spring.threads.virtual.enabled` | `true` | — | Java 21 Virtual Threads |

In Docker Compose, `YAMCS_URL` is set to `http://yamcs:8090` so the Spring Boot container resolves the Yamcs container via Docker DNS.

## Orekit Physics Data

Orekit requires reference data (leap seconds, Earth orientation parameters, planetary ephemerides) to perform frame transformations and time conversions. The file `src/main/resources/orekit-data.zip` must be present on the classpath.

If missing, download from the [Orekit Data repository](https://gitlab.orekit.org/orekit/orekit-data) and place it in `src/main/resources/`.

## Future Improvements

- [ ] CCSDS packet standards instead of raw JSON telemetry
- [ ] Telecommanding — bidirectional communication to alter satellite orbit
- [ ] Multi-satellite tracking with concurrent TLE management
- [ ] Kubernetes deployment alongside Yamcs
- [ ] Ground station visibility windows and pass prediction

## Development Methodology

This project was built using an **AI-augmented workflow** (Claude Code). AI tools were leveraged for generating Orekit configuration boilerplate, accelerating Java 21 record definitions and Spring Boot wiring, and writing the test suite. **Core logic and architecture were design-reviewed and integrated by the human author.**

## Author

**Jakub Toth**
