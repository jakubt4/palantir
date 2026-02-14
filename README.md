# Project Palantir: Orbital Telemetry Digital Twin

> *"They were not made by Sauron... They were made by the Noldor in Eldamar... to see far off, and to converse in thought with one another."* — Gandalf on the Palantiri

## About The Project

Project Palantir is a Proof of Concept (PoC) constructing a "Digital Twin" ground segment environment.

It bridges astrodynamics simulation with operational mission control software. Operators ingest real Two-Line Element sets (TLEs) via a REST API, and the system propagates the satellite orbit in real time using SGP4, streaming geodetic telemetry (latitude, longitude, altitude) to a Yamcs mission control instance.

## Architecture

The system is composed of two pillars operating in tandem:

- **Physics Engine (port 8080):** A Spring Boot 3.2 application using Orekit 12.2 for SGP4/SDP4 orbit propagation. Accepts TLE uploads via REST, propagates at 1 Hz, and pushes telemetry to Yamcs. Runs on Java 21 with Virtual Threads enabled.

- **Mission Control (port 8090):** A Yamcs 5.12.2 Docker container with a dedicated `palantir` instance. Receives telemetry via REST, serves a web UI over WebSocket. Defines LOCAL float parameters (`/Palantir/Latitude`, `/Palantir/Longitude`, `/Palantir/Altitude`) via an XTCE Mission Database.

### Data Flow

```
                  POST /api/orbit/tle
  Operator ──────────────────────────────► Spring Boot (Orekit SGP4)
                                                │
                                          @Scheduled(1s)
                                          propagate → geodetic
                                                │
                                          JSON / REST (batchSet)
                                                │
                                                ▼
                                          Yamcs (Docker :8090)
                                                │
                                            WebSocket
                                                │
                                                ▼
                                          Browser UI
```

## Tech Stack

| Technology | Purpose |
|---|---|
| **Java 21** (LTS) | Core language, Virtual Threads for high-throughput telemetry |
| **Spring Boot 3.2.5** | Application framework, scheduling, REST API |
| **Spring Retry** | Resilient Yamcs communication with automatic retries |
| **Orekit 12.2** | Astrodynamics library — TLE parsing, SGP4/SDP4 propagation |
| **Yamcs 5.12.2** | Mission control for spacecraft telemetry & commanding |
| **Yamcs Client 5.12.4** | Java client library for Yamcs API interaction |
| **Docker / Compose** | Containerization and orchestration of the full stack |
| **Maven** | Build tool and dependency management |
| **JaCoCo** | Code coverage reporting |

## Getting Started

### Prerequisites

- Java 21 SDK
- Docker (with Compose)
- Maven

### Option A: Docker Compose (Full Stack)

The easiest way to run the entire system:

```bash
docker compose up --build
```

This builds and starts both the Yamcs mission control and the Spring Boot physics engine. The `palantir-core` service waits for Yamcs to be healthy before starting. Yamcs data is persisted in a named volume (`palantir_yamcs_data`).

### Option B: Manual Setup

#### 1. Build & Start Mission Control (Yamcs)

```bash
docker build -t palantir-yamcs yamcs/
docker run --rm --name yamcs -p 8090:8090 palantir-yamcs
```

Verify by visiting http://localhost:8090 in your browser.

#### 2. Configure Physics Data

Orekit requires physical data (leap seconds, Earth orientation parameters, planetary ephemerides). The file `src/main/resources/orekit-data.zip` must be present.

If missing, download from https://gitlab.orekit.org/orekit/orekit-data/-/archive/main/orekit-data-main.zip and place it there. The application auto-loads this data at startup via `OrekitConfig`.

#### 3. Build and Run

```bash
mvn package
mvn spring-boot:run
```

On startup, the application initializes the WGS84 Earth model and waits for a TLE:

```
Earth model initialized — WGS84 ellipsoid, ITRF/IERS-2010
WAITING_FOR_TLE — No active propagator, awaiting TLE ingestion
```

### 4. Ingest a TLE

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

You can update the TLE at any time by posting again — the propagator swaps atomically.

## Usage

Once a TLE is ingested, the logs show real-time position updates every second:

```
AOS — Acquired signal for [ISS (ZARYA)], TLE epoch: 2024-01-01T12:00:00Z, propagator: SGP4
[ISS (ZARYA)] Position — lat=12.34 °, lon=-45.67 °, alt=407.32 km
```

In the Yamcs Web Interface (http://localhost:8090), navigate to the **Parameters** view and search for `Palantir`. Watch `/Palantir/Latitude`, `/Palantir/Longitude`, and `/Palantir/Altitude` update live.

## REST API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orbit/tle` | Ingest a TLE and start/update propagation |

### POST /api/orbit/tle

**Request body:**

```json
{
  "satelliteName": "ISS (ZARYA)",
  "line1": "1 25544U ...",
  "line2": "2 25544 ..."
}
```

**Responses:**

| Status | Condition |
|---|---|
| `200 OK` | TLE parsed and propagation started (`"status": "ACTIVE"`) |
| `400 Bad Request` | Missing/blank satellite name, missing TLE lines, or invalid TLE format (`"status": "REJECTED"`) |

## Project Structure

```
palantir/
├── src/main/java/io/github/jakubt4/palantir/
│   ├── PalantirApplication.java              # Entry point (@EnableScheduling, @EnableRetry)
│   ├── config/
│   │   ├── OrekitConfig.java                 # Loads orekit-data.zip at startup
│   │   └── RestClientConfig.java             # RestClient timeouts (5s connect/read)
│   ├── controller/
│   │   └── TleIngestionController.java       # POST /api/orbit/tle endpoint
│   ├── service/
│   │   └── OrbitPropagationService.java      # SGP4 propagation, @Scheduled telemetry push
│   ├── client/
│   │   └── YamcsTelemetryClient.java         # REST client with @Retryable to Yamcs
│   └── dto/                                  # Java records (TLE request/response, Yamcs API)
├── src/test/java/io/github/jakubt4/palantir/
│   ├── PalantirApplicationTests.java         # Full context load integration test
│   ├── controller/TleIngestionControllerTest.java  # @WebMvcTest — 3 tests
│   ├── service/OrbitPropagationServiceTest.java    # @SpringBootTest — 3 tests
│   ├── client/YamcsTelemetryClientTest.java        # MockRestServiceServer — 2 tests
│   └── dto/YamcsParameterRequestTest.java          # Pure unit — 2 tests
├── src/main/resources/
│   ├── application.yaml                      # Spring Boot config (Virtual Threads, Yamcs URL)
│   └── orekit-data.zip                       # Orekit physics data
├── Dockerfile                                # Multi-stage Spring Boot build (Maven + JRE 21)
├── docker-compose.yaml                       # Full-stack orchestration (Yamcs + Spring Boot)
├── yamcs/                                    # Custom Yamcs Docker image
│   ├── Dockerfile                            # Based on yamcs/example-simulation:5.12.2
│   ├── mdb/palantir.xml                      # XTCE defining LOCAL parameters with units
│   └── etc/
│       ├── yamcs.yaml                        # Yamcs server config (HTTP, CORS, instance)
│       ├── yamcs.palantir.yaml               # Palantir instance config (MDB, archiving)
│       └── processor.yaml                    # Processor config (no TM/TC, LOCAL params only)
└── pom.xml
```

## Testing

```bash
mvn test                                      # Run all 11 tests + JaCoCo coverage
mvn test -Dtest=TleIngestionControllerTest    # Run a single test class
```

The test suite covers:
- **Controller** — TLE ingestion validation (valid, blank name, invalid TLE)
- **Service** — Earth model initialization, no-TLE guard, SGP4 propagation with physical bounds checking
- **Client** — REST payload structure, connection failure handling
- **DTO** — JSON serialization shape for Yamcs API
- **Integration** — Full Spring context load

## Configuration

| Property | Default | Description |
|---|---|---|
| `yamcs.base-url` | `http://localhost:8090` | Yamcs server URL (overridable via `YAMCS_URL` env var) |
| `server.port` | `8080` | Spring Boot server port |
| `spring.threads.virtual.enabled` | `true` | Java 21 Virtual Threads |

In Docker Compose, the `YAMCS_URL` environment variable is set to `http://yamcs:8090` so the Spring Boot container resolves the Yamcs container by its Docker DNS name.

## Future Improvements

- [ ] Implementation of CCSDS packet standards instead of raw JSON
- [ ] Bidirectional communication (Telecommanding) to alter the satellite orbit
- [ ] Multi-satellite tracking with concurrent TLE management
- [ ] Deploying into a Kubernetes cluster alongside Yamcs

## Development Methodology

This project was built using an **AI-augmented workflow** (Claude Code).
AI tools were leveraged for:
- Generating Orekit configuration boilerplate
- Accelerating Java 21 record definitions and Spring Boot wiring
- Writing and iterating on the test suite
- **Core logic and architecture were design-reviewed and integrated by the human author.**

## Author

**Jakub Toth**
Senior Systems Engineer aiming for the stars.
