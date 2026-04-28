# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Palantir** is a Digital Twin ground segment PoC that bridges astrodynamics simulation with mission control. It simulates a satellite in Low Earth Orbit using Orekit, encoding geodetic telemetry into CCSDS Space Packets (CCSDS 133.0-B-2, with a CCSDS 301.0-B-4 CUC time code in the Secondary Header) and streaming them over UDP to a Yamcs mission control instance.

**Architecture:** Two-pillar design:
- **Physics Engine (port 8080):** Spring Boot 3.2.5 app using Orekit 12.2 for SGP4/SDP4 TLE-based orbit propagation, with Java 21 Virtual Threads for high-throughput telemetry generation. Accepts TLE uploads via REST, propagates at 1 Hz, encodes CCSDS packets over UDP. Listens for telecommands on UDP port 10001.
- **Mission Control (port 8090):** Yamcs 5.12.2 Docker container (instance `palantir`) receiving raw CCSDS telemetry via UdpTmDataLink, decoding via XTCE MDB, sending telecommands via UdpTcDataLink, serving a web UI over WebSocket.

Data flow:
- **Downlink (TM):** `Spring Boot (Orekit SGP4) --CCSDS/UDP:10000--> Yamcs --WebSocket--> Browser`
- **Uplink (TC):** `Yamcs --UDP:10001--> Spring Boot (UdpCommandReceiver)`
- **Operator:** `TLE POST --> Spring Boot REST API`

## Collaboration Style

The user (Jakub) is a senior Java engineer using this project as a learning vehicle for **everything except Java** — Python, Yamcs internals, XTCE, Docker, CCSDS, orbital mechanics, physics, and any new tech introduced later. Work under the following contract.

### 0. Engineering stance

0. **Constructive criticism is the default, not agreement.** When an idea has flaws — the user's, Claude's, or something both missed — name them and explain the cost. Silent agreement is worse than disagreement. This cuts both ways: Claude pushes back on user proposals where warranted; when the user pushes back, Claude takes the critique seriously rather than defending out of habit. Critique lands on substance, not phrasing. No drive-by disagreement to demonstrate rigor — if the idea is sound, agree and move on. No validation padding — skip "great question", "good approach", "interesting point", or similar phatic tokens. Open with substance.

### A. Decision transparency

Calibrate ceremony to stakes. A variable name is a 5-second choice; a third-party library is a week-shaping choice. Rules below scale proportionally — not binary on/off.

1. Every non-trivial technical choice surfaces at least one alternative considered and why it was rejected.
2. When a choice is driven by "Claude knows this pattern works," say so explicitly — don't dress it up as derived logic.
3. No hedging when certainty is available. State concrete claims with version numbers or specific evidence ("Yamcs 5.12.2 rejects duplicate SpaceSystem names" rather than "Yamcs probably doesn't support this"). When uncertain, say "I don't know — need to verify" explicitly. Vague confidence is worse than acknowledged uncertainty.
4. First use of a third-party library: one paragraph on what problem it solves, 1–2 alternatives, why this fits best.

### B. Chunk size & pacing

5. Default commit size ~50–100 lines of meaningful change (adjust as the workflow evolves).
6. One concern per commit. "Scaffold structure" and "add Yamcs client" are two commits, not one.
7. No >150-line diffs without a heads-up and confirmation.
8. Pause after each non-trivial code generation — don't chain multiple implementation steps in one message.

### C. Teaching cadence (full learning mode — applies to everything except Java)

9. **New idioms get a chat explanation when first introduced.** Teaching lives in chat messages, not inline code comments — code stays clean of pedagogical noise. Covers: Python idioms, Yamcs config patterns, XTCE constructs, Docker/docker-compose features, CCSDS packet semantics, orbital mechanics concepts (frames, TLE/SGP4, RTN, etc.), physics/units conventions.
10. When there are multiple idiomatic solutions, pick the one that teaches best for the current level; flag the alternatives.
11. Checkpoint understanding at natural boundaries — focused "does this make sense / any idioms to explain?" at phase transitions.
12. "Why?" questions get trade-off answers, not hedged generalities.

### D. Mistake handling

13. When something generated didn't work, surface it explicitly — no silent-fix-and-move-on. The XTCE SpaceSystem collision (Phase 0) is the canonical teaching-moment pattern: name the error, explain what was wrong, state the lesson.
14. No retroactive rewriting to pretend the bad path didn't happen.

### E. User control

15. **Never commit without an explicit ask.** Default question after a green chunk: "Commit this?" Response options: **yes** / **no** / **"ask X first"** (trigger clarifying questions before deciding).
16. Never run `git push`, `git reset --hard`, `git rebase`, or other destructive operations (Docker volumes, archive data, dependency downgrade) without explicit authorization.
17. Before touching more than one file, state the plan briefly. Single-file edits: just do it.

### F. Verification & hygiene

18. Run relevant tests after non-trivial changes. End-to-end verification for anything touching contracts (API paths, wire formats, XTCE, Docker networking).
19. Reporting "done" = reporting what was actually verified. No conflation of "intended to work" with "validated working."
20. Docs (this file, README.md, FEATURES.md, ARCHITECTURE.md, etc.) stay in sync with code changes in the same commit.

### G. Domain anchoring (part of learning mode)

21. Spacecraft / physics / protocol concepts get anchored in authoritative standards on first use — CCSDS 133.0-B-2, XTCE 1.2, ECSS-Q-ST-80C Rev.2, IERS-2010, WGS-84, IEEE 754, etc. One-line reference, not a lecture.
22. Units called out at every boundary: km↔m, deg↔rad, UTC↔epoch-seconds, big-endian↔little-endian. Single most bug-prone area in ground segment code.
23. When a change touches commanding, archive write paths, external network inputs, or authentication boundaries, flag the safety/security implication explicitly before coding. Name the concrete failure mode — e.g., "opcode collision could send unintended command", "malformed packet could poison archive queries", "open port exposes untrusted input surface". "I flagged it" without a named failure mode doesn't count.

### H. When rules relax

24. **Only Java-language-level concerns relax.** The user is fluent in Java; Java idioms don't need inline teaching annotations. But rules 0–8 and 13–23 still apply to Java code — constructive criticism, pros/cons on choices, commit sizing, mistake handling, verification, domain anchoring.
25. Everything else — Python, Yamcs internals, XTCE, Docker, orbital mechanics, physics, CCSDS protocol, future tech like ML or Kubernetes — stays in full learning mode.

### I. Space Operations Strict Protocols (First Principles)

26. **Time Domain Determinism:** Never use `System.currentTimeMillis()`, `Instant.now()`, or `new Date()` for physics, scheduling, or orbital logic. Time must strictly flow through Orekit's `AbsoluteDate` using the configured TimeScale (usually UTC via `TimeScalesFactory.getUTC()`). Ground Segment reception time must NEVER be used as spacecraft generation time — flight TM packets must carry an embedded time code (e.g. CCSDS 301.0-B-4 CUC), and ground preprocessors must decode it from the packet bytes (PAL-105 closed this for the digital twin via Yamcs `CfsPacketPreprocessor` reading the Secondary Header CUC).
   **Exception — digital twin sim mode:** the propagation scheduler in `OrbitPropagationService` may seed `AbsoluteDate` from `Instant.now()` (in UTC TimeScale) because the Spring Boot service IS the spacecraft and the JVM clock literally is the spacecraft clock. This exception does NOT extend to: (i) ground-segment code that consumes real or replayed telemetry — that code reads time off the packet, never off the local clock; (ii) test fixtures, which should accept an injected `Clock` for deterministic time control; (iii) any future real-flight code path.
27. **Deterministic Randomness (Monte Carlo):** Any random number generation (e.g., for collision assessment, Pc computation, or synthetic telemetry noise) MUST use a seeded PRNG from a known-stable library — Java: `org.hipparchus.random.Well19937a`; Python: `numpy.random.default_rng(seed)` plus framework seeders (`torch.manual_seed`, `tf.random.set_seed`, `random.seed`) when ML is involved. Never use `Math.random()`, bare `new java.util.Random()`, `numpy.random.seed()` (legacy global API), or any unseeded instance. The seed used for a run MUST be logged (or otherwise persisted) so the run is byte-for-byte reproducible for regulatory audits.
28. **Sequence Integrity over Async (downlink path):** In TM **encoding and transmission**, strict chronological ordering and sequence-counter monotonicity are more important than asynchronous I/O isolation. The path from sequence-counter increment through socket write MUST be single-threaded — do not introduce concurrency (Virtual Threads, `CompletableFuture`, `@Async`, executor submits) into packet serialization or transmission. This rule applies per APID — different APIDs maintain independent monotonic counters and may run on independent threads. Async patterns ARE permitted on the **uplink path** and on **non-CCSDS background work** (e.g., the long-lived `socket.receive()` loop in `UdpCommandReceiver`, the `@Scheduled` HTTP fetch in `TleRefreshService`); the rule's concern is downlink wire ordering, not async per se.
29. **Frozen Toolchain:** Do NOT suggest or execute upgrades to **toolchain components** — JDK, Maven plugins, Spring Boot, Orekit, Hipparchus, Yamcs (server + client), Python, `uv`, NumPy, pandas, matplotlib, cartopy, Cesium, vite, Docker base images — unless explicitly instructed. Lockfile refreshes (`uv lock --upgrade`, `mvn versions:use-latest-releases`, `npm update`) count as toolchain changes and require the same authorization. Space systems rely on validated baselines; any minor version bump risks floating-point drift in the physics engine, XTCE loader behaviour change, protobuf wire incompatibility between Yamcs server and client, or virtual-thread scheduler regressions. **Exception — security advisories:** named CVEs MUST be surfaced (CVE-ID, severity score, affected component, brief description) so you can decide whether to authorize the upgrade; do not silently patch and do not silently sit on the advisory.
30. **Astrodynamic Covariance:** When simulating position uncertainty, never inject isotropic (spherical) noise. Orbital uncertainty must be modeled in the Local Orbital Frame (e.g., RTN or QSW) where the In-Track error is orders of magnitude larger than Cross-Track or Radial errors.

### Meta

- List is editable; revise rules that don't serve the work.
- Stale rules get removed.
- This file is canonical. Chat contradiction loses to file.
- **Rules change only on the user's explicit request.** Claude does not modify them on its own initiative. If Claude notices a rule creating friction, flag it in chat ("Rule N feels like it's costing more than it saves — worth revisiting?") but wait for the user's decision before editing.

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
- **`service/CcsdsTelemetrySender`** — `@Service` that encodes geodetic telemetry as 24-byte CCSDS Space Packets (6B Primary Header + 6B Secondary Header CUC time + 12B payload) and transmits via `DatagramSocket` over UDP. Uses `AtomicInteger` for the 14-bit CCSDS sequence counter. Caller passes the `AbsoluteDate generationTime` so the packet's CUC time bytes (4-byte uint32 coarse + 2-byte uint16 fine, TAI seconds since 1958-01-01) reflect the propagator tick that produced the coordinates, not a separate sender-side clock. Target host/port configurable via `@Value` with env var overrides. `@PostConstruct` creates the socket and the TAI-1958 reference epoch (after `OrekitConfig` has loaded data), `@PreDestroy` closes the socket.
- **`service/uplink/UdpCommandReceiver`** — `@Service` that listens for telecommand packets from Yamcs via UDP. Uses a Virtual Thread executor for non-blocking receive. Parses a 1-byte opcode from each datagram and dispatches commands (0x01=PING, 0x02=REBOOT_OBC, 0x03=SET_TRANSMIT_POWER). Port configurable via `palantir.uplink.port` (default 10001, set to 0 in test profile).
- **`dto/`** — Java records: `TleRequest` (satelliteName, line1, line2) and `TleResponse` (satelliteName, status, message) for the TLE ingestion API.
- **`yamcs/`** — Custom Yamcs Docker image based on `yamcs/example-simulation:5.12.2`. Instance named `palantir`. Config files:
  - `etc/yamcs.yaml` — Server config (HTTP on 8090, CORS enabled, single `palantir` instance).
  - `etc/yamcs.palantir.yaml` — Instance config (UdpTmDataLink on port 10000, UdpTcDataLink sending to `palantir-core:10001`, `org.yamcs.tctm.cfs.CfsPacketPreprocessor` with `timeEncoding.epoch: TAI` reading the CUC time at byte 6 from the Secondary Header, no error detection, XTCE MDB loader, archive services, stream config with `tm_realtime` and `tc_realtime` mapped to `realtime` processor).
  - `etc/processor.yaml` — Realtime processor with `StreamTmPacketProvider` (subscribes to `tm_realtime`, drives XTCE packet decoding into live parameters), `StreamParameterProvider` (routes processed parameters), and `StreamTcCommandReleaser` (releases commands to `tc_realtime` stream). Archive/replay processors with `ReplayService`.
  - `mdb/baseline.xml` — root `<SpaceSystem name="Palantir">`: CCSDS Primary Header bit-fields split per the canonical XTCE pattern (`ccsds_version` 3-bit, `ccsds_type` 1-bit, `ccsds_sec_hdr_flag` 1-bit, `ccsds_apid` 11-bit, `ccsds_grouping_flags` 2-bit, `ccsds_seq_count` 14-bit, `ccsds_length` uint16; abstract `CCSDS_Packet_Base` container) + Secondary Header CUC time (`cuc_coarse_t` uint32, `cuc_fine_t` uint16; abstract `CCSDS_Tm_Packet_Base` container inheriting from `CCSDS_Packet_Base`) + nav telemetry (`Palantir_Nav_Packet` inheriting from `CCSDS_Tm_Packet_Base` with `RestrictionCriteria` matching `ccsds_apid == 100`, Latitude/Longitude/Altitude as IEEE 754 float32). Yamcs paths: `/Palantir/Latitude`, `/Palantir/Longitude`, `/Palantir/Altitude`, `/Palantir/ccsds_time_coarse`, `/Palantir/ccsds_time_fine`.
  - `mdb/features/commands.xml` — `<SpaceSystem name="TC">` nested under `/Palantir` via `subLoaders`: PING (opcode 0x01) and REBOOT_OBC (opcode 0x02). Yamcs paths: `/Palantir/TC/PING`, `/Palantir/TC/REBOOT_OBC`. Yamcs requires unique SpaceSystem names across files — sharing a name raises `IllegalArgumentException: there is already a subsystem with name X`.
  - `mdb/README.md` — pattern for adding new features (new XTCE file under `features/` with its own SpaceSystem name + `subLoaders` entry in `yamcs.palantir.yaml`).
- **`docker-compose.yaml`** (project root) — Orchestrates `yamcs` and `palantir-core` services. Yamcs has a healthcheck (`GET /api/`), persistent volume (`palantir_yamcs_data`), and the Spring Boot service depends on Yamcs start (uses `service_started`, not `service_healthy`, so `palantir-core` joins the Docker network before Yamcs initializes its `UdpTcDataLink` — `service_healthy` would cause a permanent DNS resolution failure). `YAMCS_UDP_HOST=yamcs` env var enables Docker DNS resolution. Exposes UDP 10001 for telecommand uplink.
- **`Dockerfile`** (project root) — Multi-stage build for the Spring Boot app: Maven + JDK 21 build stage, JRE 21 runtime stage.

## Testing

Tests use JUnit 5, Mockito, and AssertJ (all provided by `spring-boot-starter-test`).

- **Controller tests** (`controller/TleIngestionControllerTest`) — `@WebMvcTest` with mocked `OrbitPropagationService`. Tests valid TLE ingestion, blank satellite name rejection, and invalid TLE format rejection.
- **Service tests** (`service/OrbitPropagationServiceTest`) — `@SpringBootTest` with `@MockBean` for `CcsdsTelemetrySender`. Requires full Spring context (Orekit data must load). Uses `ArgumentCaptor<Float>` to validate propagated orbital values are physically plausible (lat ±90, lon ±180, alt > 0).
- **Integration test** (`PalantirApplicationTests`) — Validates full context loads.

Note: `@SpringBootTest` tests start the scheduler, so `OrbitPropagationServiceTest` uses `Mockito.clearInvocations()` in `@BeforeEach` and `atLeastOnce()` verification to handle concurrent scheduler calls. A test-specific `application.yaml` (`src/test/resources/`) sets `palantir.uplink.port=0` so `UdpCommandReceiver` binds to an ephemeral port and avoids conflicts.

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
