# Project Palantir: Student Integration Backlog

## Scope & Architectural Boundary

**Off-Limits (Core System):** The Java 21 Spring Boot application, Orekit propagator, CCSDS 133.0-B-1 packet encoder, Virtual Thread dispatcher, and UDP transport layer (`CcsdsTelemetrySender`, `UdpCommandReceiver`, `OrbitPropagationService`) are maintained exclusively by the core engineering team. Students **must not** modify any source under `src/main/java/io/github/jakubt4/palantir/`.

**Student Domain:** All work operates on the interfaces exposed by the running system:
- **Yamcs Web API** (HTTP/WebSocket on port 8090)
- **Yamcs Mission Database** (XTCE XML under `yamcs/mdb/`)
- **Yamcs Client Libraries** (`yamcs-client` for Python, Yamcs Web API for JS/TS)

---

## Epic 1: HMI & Spacecraft Operations Display

### PAL-101: Real-Time Orbital Ground Track on CesiumJS Globe

**Objective:** Build a browser-based 3D operator display that subscribes to live Palantir telemetry parameters (`Latitude`, `Longitude`, `Altitude`) via the Yamcs WebSocket API and renders the spacecraft's ground track on a CesiumJS globe in real time.

**Technical Context:**
- Yamcs exposes a WebSocket endpoint at `ws://localhost:8090/api/websocket` for parameter subscriptions. Subscribe to processor `realtime` on instance `palantir`.
- Parameters are defined in the XTCE MDB at paths: `/Palantir/Latitude`, `/Palantir/Longitude`, `/Palantir/Altitude`.
- CesiumJS (`cesium` npm package) provides `Viewer`, `Entity`, and `SampledPositionProperty` for time-dynamic 3D visualization.
- The display must convert geodetic coordinates (lat/lon/alt) to Cartesian via `Cesium.Cartesian3.fromDegrees()`. Altitude from Yamcs is in **kilometers**; CesiumJS expects **meters**.
- Use vanilla JavaScript or TypeScript. No framework requirement. A single `index.html` + bundled JS is acceptable.

**Acceptance Criteria:**
- [ ] WebSocket connection to Yamcs establishes and auto-reconnects on disconnect.
- [ ] Spacecraft icon (point or model) updates position on the CesiumJS globe at 1 Hz matching the propagator cadence.
- [ ] Ground track polyline renders the last 90 minutes (one full LEO orbit) of trajectory history.
- [ ] Altitude is displayed in an overlay panel in km with 2-decimal precision.
- [ ] Application runs with `npm start` or by opening `index.html` in a browser; no backend required.

**Estimate:** 30 man-hours

---

### PAL-102: Telecommand Control Panel with Execution Feedback

**Objective:** Implement a web-based operator panel that issues telecommands (`PING`, `REBOOT_OBC`) to the spacecraft via the Yamcs REST API and displays command history with execution status.

**Technical Context:**
- Yamcs REST API for commanding: `POST /api/processors/palantir/realtime/commands/Palantir/{commandName}` where `{commandName}` matches the XTCE MetaCommand name.
- Command history is queryable via `GET /api/archive/palantir/commands` (returns JSON with `commandId`, `generationTime`, `commandName`, `status`).
- Current MDB defines two commands: `PING` (opcode `0x01`, no arguments) and `REBOOT_OBC` (opcode `0x02`, no arguments).
- The panel should use `fetch()` or `XMLHttpRequest` against the Yamcs HTTP API. CORS is enabled on the Yamcs server (`yamcs.yaml`).
- Command status lifecycle in Yamcs: `QUEUED` -> `RELEASED` -> `SENT`. Without closed-loop verification, terminal state is `SENT`.

**Acceptance Criteria:**
- [ ] Panel displays two buttons: "Send PING" and "Send REBOOT_OBC".
- [ ] Clicking a button issues the corresponding `POST` request to the Yamcs commanding API.
- [ ] A command log table below the buttons shows the last 20 commands with columns: Timestamp, Command Name, Status.
- [ ] Log auto-refreshes every 5 seconds or updates via WebSocket subscription to command history.
- [ ] HTTP errors (4xx/5xx) are displayed inline as user-visible alerts, not swallowed silently.

**Estimate:** 20 man-hours

---

## Epic 2: Flight Dynamics & Payload Analytics

### PAL-201: Orbital Telemetry Export & Trend Analysis Pipeline

**Objective:** Build a Python pipeline that extracts archived telemetry from the Yamcs API, computes orbital statistics, and generates publication-quality plots of the spacecraft's trajectory and altitude profile over a configurable time window.

**Technical Context:**
- Use the `yamcs-client` Python library (`pip install yamcs-client`). Connect via `YamcsClient('localhost:8090')`.
- Retrieve parameter samples: `client.get_processor('palantir', 'realtime')` for live, or `archive = client.get_archive('palantir')` then `archive.list_parameter_values('/Palantir/Latitude', start=..., stop=...)` for historical data.
- Each parameter value object has `.generation_time` (datetime), `.eng_value` (float).
- Use `pandas` for data manipulation and `matplotlib` for plotting.
- Expected outputs: (1) Ground track scatter plot (lon vs lat on a Mercator projection), (2) Altitude vs. time line chart, (3) Summary statistics CSV (min/max/mean for each parameter).

**Acceptance Criteria:**
- [ ] Script accepts `--start` and `--stop` CLI arguments in ISO 8601 format (e.g., `2025-01-01T00:00:00Z`). Defaults to last 2 hours if omitted.
- [ ] Exports a `telemetry_export.csv` with columns: `timestamp`, `latitude_deg`, `longitude_deg`, `altitude_km`.
- [ ] Generates `ground_track.png` (scatter plot of lon/lat with coastline overlay via `cartopy` or `basemap`) and `altitude_profile.png` (altitude vs. time).
- [ ] Prints summary statistics (min, max, mean, std) for all three parameters to stdout.
- [ ] Runs end-to-end with `python orbital_analysis.py` against a live or recently-archived Yamcs instance.

**Estimate:** 25 man-hours

---

### PAL-202: Automated AOS/LOS Pass Prediction Report

**Objective:** Compute Acquisition of Signal (AOS) and Loss of Signal (LOS) windows for a configurable ground station by post-processing archived latitude/longitude telemetry against a station visibility mask.

**Technical Context:**
- A ground station is defined by its geodetic coordinates (lat, lon, alt) and a minimum elevation angle (typically 5-10 degrees).
- Visibility computation: from the spacecraft's geodetic position and the station's position, compute the slant range and elevation angle. AOS occurs when elevation crosses above the threshold; LOS when it drops below.
- Use `numpy` for vectorized great-circle and elevation calculations. The simplified elevation formula: `el = arctan((alt_sc - alt_gs) / d) - arcsin(d / (R_earth + alt_gs))` where `d` is the ground distance. For initial implementation, a line-of-sight geometric model is acceptable.
- Input: archived telemetry from Yamcs (`yamcs-client`), ground station config (JSON or CLI args).
- Output: a Markdown or CSV report listing each pass with AOS time, LOS time, max elevation, and pass duration.

**Acceptance Criteria:**
- [ ] Script accepts ground station coordinates and minimum elevation angle as CLI arguments.
- [ ] Default ground station: Kosice, Slovakia (48.7164 N, 21.2611 E, 206 m).
- [ ] Produces a `pass_report.csv` with columns: `pass_number`, `aos_time`, `los_time`, `max_elevation_deg`, `duration_seconds`.
- [ ] Generates a `visibility_timeline.png` showing elevation angle vs. time with AOS/LOS crossings marked.
- [ ] Validated against at least 6 hours of archived telemetry with a minimum of 2 detected passes for a typical LEO orbit.

**Estimate:** 30 man-hours

---

## Epic 3: Mission Database & Systems Integration

### PAL-301: XTCE Payload Telemetry Definition for Environmental Monitoring

**Objective:** Extend the Yamcs Mission Database (`palantir.xml`) with a new telemetry packet definition for a simulated environmental monitoring payload, including parameter calibrations and alarm thresholds.

**Technical Context:**
- The current XTCE MDB (`yamcs/mdb/palantir.xml`) defines a single packet type: `Palantir_Nav_Packet` (APID 100) with three IEEE 754 float parameters.
- New payload packet uses **APID 200** to distinguish it from navigation telemetry. Packet structure: 6-byte CCSDS header + N-byte payload.
- Define the following parameters in XTCE:
  - `Board_Temperature` (float32, degrees Celsius) — calibration: raw float, polynomial identity. Alarm: WARNING at > 60 C, CRITICAL at > 80 C.
  - `Battery_Voltage` (float32, volts) — Alarm: WARNING at < 7.0 V, CRITICAL at < 6.0 V.
  - `Solar_Panel_Current` (float32, amperes) — Alarm: WARNING at < 0.1 A (eclipse expected), CRITICAL at < 0.0 A (panel failure).
  - `Radiation_Dose` (uint16, raw counts) — calibration: polynomial `dose_mrad = counts * 0.0472 + 0.5`.
- Use XTCE `<SequenceContainer>` inheritance from the existing `CCSDS_Packet_Base`, restricted by APID.
- Alarms are defined via `<DefaultAlarm>` with `<StaticAlarmRanges>` in the XTCE parameter type definitions.

**Acceptance Criteria:**
- [ ] `palantir.xml` validates against the XTCE 1.2 schema without errors.
- [ ] New `Env_Payload_Packet` container is defined with APID 200 restriction, inheriting from `CCSDS_Packet_Base`.
- [ ] All four parameters are browsable in the Yamcs web UI under the parameter list after Yamcs restart.
- [ ] Alarm definitions are visible in the Yamcs parameter detail view (warning/critical ranges displayed).
- [ ] Polynomial calibration for `Radiation_Dose` is correctly defined and verified by manual computation.

**Estimate:** 20 man-hours

---

### PAL-302: Multi-Packet Stream Configuration & Archive Validation

**Objective:** Configure the Yamcs instance to ingest, process, and archive the new environmental payload packet (APID 200) alongside the existing navigation telemetry, and validate end-to-end data flow from UDP ingestion through archive retrieval.

**Technical Context:**
- The existing `UdpTmDataLink` on port 10000 already receives all CCSDS packets. The `GenericPacketPreprocessor` routes packets to `tm_realtime` regardless of APID. No link-level changes are needed.
- Yamcs demultiplexes packets by APID using the XTCE container hierarchy. Once `PAL-301` defines the APID 200 container, Yamcs will automatically decode matching packets.
- Validation requires a **test packet sender** — a standalone Python script using `socket` to craft a raw CCSDS packet (6-byte header with APID 200 + payload bytes) and send it via UDP to port 10000.
- Archive validation: use `yamcs-client` to query `archive.list_parameter_values('/Palantir/Board_Temperature')` and confirm values are stored and retrievable.
- Yamcs configuration files involved: `yamcs.palantir.yaml` (verify stream routing), `processor.yaml` (verify `StreamTmPacketProvider` subscription).

**Acceptance Criteria:**
- [ ] Python test sender script (`send_env_packet.py`) transmits a valid CCSDS packet with APID 200 and known payload values to Yamcs UDP port 10000.
- [ ] Yamcs decodes the packet and displays all four environmental parameters with correct engineering values in the web UI.
- [ ] Alarm indicators trigger in the Yamcs UI when test packets contain out-of-range values (e.g., `Board_Temperature = 85.0`).
- [ ] Archived parameter values are retrievable via `yamcs-client` Python API with correct timestamps and values.
- [ ] A `validation_report.md` documents the test procedure, screenshots of Yamcs UI showing decoded parameters, and archive query results.

**Estimate:** 25 man-hours

---

## Epic 4: Enterprise Java Integration & Validation (Air-Gapped)

> **Architectural Constraint:** The Palantir Core codebase (`src/main/java/io/github/jakubt4/palantir/`) is **read-only** for the Java Integrator. All Java deliverables in this Epic are developed in **separate, independent projects** that interact with the Palantir stack exclusively through network interfaces (UDP, HTTP) and shared Docker infrastructure. No modifications to the core `pom.xml`, core source tree, or core Dockerfile are permitted.

### PAL-401: Yamcs Custom Algorithm Plugin — Quaternion-to-Euler Attitude Processor

**Objective:** Develop a custom Yamcs Algorithm/Derived Value plugin that subscribes to raw attitude quaternion telemetry parameters (q0, q1, q2, q3) within the Yamcs processing pipeline and outputs derived Euler angle parameters (Roll, Pitch, Yaw) in real time — enabling operators to monitor spacecraft orientation in human-readable form without modifying the core flight software.

**Technical Context:**
- Yamcs supports user-defined algorithms via two mechanisms: (1) JavaScript algorithms defined inline in XTCE `<MathAlgorithm>`, and (2) Java-based `AlgorithmExecutor` plugins packaged as JARs and loaded into the Yamcs classpath.
- For this ticket, implement a **Java-based algorithm** to demonstrate enterprise plugin development. The plugin JAR is built in an independent Maven project (e.g., `yamcs-plugins/attitude-processor/`) and mounted into the Yamcs Docker image at `/opt/yamcs/lib/ext/`.
- Quaternion-to-Euler conversion (ZYX convention, aerospace standard):
  - Roll (phi) = `atan2(2*(q0*q1 + q2*q3), 1 - 2*(q1^2 + q2^2))`
  - Pitch (theta) = `asin(2*(q0*q2 - q3*q1))`
  - Yaw (psi) = `atan2(2*(q0*q3 + q1*q2), 1 - 2*(q2^2 + q3^2))`
- The plugin requires a corresponding XTCE extension: define a new `Attitude_Packet` (APID 300) with four float32 quaternion input parameters, and three derived float32 Euler output parameters linked via `<Algorithm>` definitions.
- Input quaternions must be normalized (`|q| = 1.0`). The algorithm should log a WARNING-level event to Yamcs if `|q|` deviates from 1.0 by more than 1e-4, indicating corrupted attitude data.
- A Python test harness (`send_attitude_packet.py`) must craft CCSDS packets with APID 300 containing known quaternion values and transmit them to Yamcs UDP port 10000 for validation.

**Acceptance Criteria:**
- [ ] Independent Maven project (`yamcs-plugins/attitude-processor/`) builds a self-contained JAR with `mvn package`. No dependency on the Palantir Core `pom.xml`.
- [ ] Yamcs Dockerfile updated to copy the plugin JAR into `/opt/yamcs/lib/ext/`. Yamcs starts without errors with the plugin loaded.
- [ ] XTCE MDB extended with `Attitude_Packet` (APID 300): four float32 quaternion inputs (q0, q1, q2, q3) and three derived Euler outputs (Roll_deg, Pitch_deg, Yaw_deg).
- [ ] Derived Euler parameters appear in the Yamcs web UI with correct values when test quaternions are injected. Validated against at least 5 known quaternion-to-Euler reference pairs (including gimbal lock edge case at pitch = +/-90 degrees).
- [ ] Quaternion norm violation triggers a Yamcs event visible in the Event log when `|q|` deviates beyond tolerance.
- [ ] Unit tests (JUnit 5) in the plugin project validate the conversion math independently of Yamcs, with coverage > 90% on the algorithm class.

**Estimate:** 60 man-hours

---

### PAL-402: Independent Payload Simulator Microservice — Earth Observation Sensor

**Objective:** Build a standalone Spring Boot 3.x microservice that simulates an Earth Observation (EO) payload sensor suite, generating synthetic telemetry (multispectral band intensities, CCD temperature, shutter state) as CCSDS Space Packets and streaming them via UDP to the Palantir Yamcs instance — proving the system's ability to ingest telemetry from multiple independent spacecraft subsystems.

**Technical Context:**
- The microservice is a fully independent Spring Boot project (e.g., `simulators/eo-payload-sim/`) with its own `pom.xml`, `Dockerfile`, and `application.yaml`. It joins the Palantir Docker Compose network as a new service (`eo-payload-sim`) but has zero compile-time dependency on the Palantir Core.
- Packet format: CCSDS Space Packet (CCSDS 133.0-B-1) with **APID 400**. Payload structure (20 bytes):
  - `Band_Red` (float32) — simulated reflectance intensity [0.0, 1.0]
  - `Band_Green` (float32) — simulated reflectance intensity [0.0, 1.0]
  - `Band_NIR` (float32) — Near-Infrared reflectance intensity [0.0, 1.0]
  - `CCD_Temperature` (float32) — sensor temperature in Celsius [-40.0, +60.0]
  - `Shutter_State` (uint16) — 0 = CLOSED, 1 = OPEN, 2 = CALIBRATING
  - Padding (2 bytes) — reserved for future use
- The simulator must generate physically plausible data: band intensities follow a sinusoidal model tied to sun illumination angle (approximated as a function of simulated orbital position or elapsed time), CCD temperature drifts between eclipse/sunlit phases, and shutter cycles between OPEN (sunlit) and CLOSED (eclipse).
- Transmission rate: configurable via `application.yaml`, default 1 Hz to match the core telemetry cadence.
- A corresponding XTCE extension in `palantir.xml` must define the `EO_Payload_Packet` (APID 400) container and all parameters with appropriate types, units, and alarm ranges (e.g., CCD_Temperature CRITICAL at > 55 C).
- The CCSDS packet encoding must follow the same byte-level conventions as the core system: big-endian, 6-byte primary header, 14-bit sequence counter.

**Acceptance Criteria:**
- [ ] Independent Spring Boot project builds and runs with `mvn spring-boot:run` or `docker compose up eo-payload-sim`. No imports from the `io.github.jakubt4.palantir` package.
- [ ] Microservice generates CCSDS packets at 1 Hz with APID 400 and transmits them via UDP to Yamcs port 10000.
- [ ] XTCE MDB defines `EO_Payload_Packet` with all five parameters. All parameters are visible and updating in the Yamcs web UI.
- [ ] Band intensity values follow a deterministic sinusoidal model. CCD temperature transitions between eclipse (-20 C) and sunlit (+45 C) phases over a ~90-minute simulated orbit period.
- [ ] Shutter state transitions are logged by Yamcs as parameter updates: OPEN during sunlit, CLOSED during eclipse.
- [ ] Docker Compose integration: `eo-payload-sim` service defined in `docker-compose.yaml` (or a separate `docker-compose.override.yaml`), starts alongside Yamcs and Palantir Core without port conflicts.
- [ ] README in the simulator project documents the packet format, simulation model, and configuration options.

**Estimate:** 70 man-hours

---

### PAL-403: Enterprise QA & Integration Testing — Testcontainers Stress Validation

**Objective:** Implement an automated integration test suite using JUnit 5 and Testcontainers that programmatically spins up the full Palantir stack (Yamcs + Palantir Core Docker images), injects 10,000 CCSDS telemetry packets, and validates end-to-end data integrity from UDP ingestion through Yamcs archive retrieval — establishing a repeatable, CI-ready quality gate for the entire system.

**Technical Context:**
- The test suite lives in an independent Maven project (e.g., `integration-tests/`) with its own `pom.xml`. Dependencies: `org.testcontainers:testcontainers`, `org.testcontainers:junit-jupiter`, `org.yamcs:yamcs-client` (Java client), JUnit 5, AssertJ.
- Testcontainers orchestration: use `DockerComposeContainer` (or `ComposeContainer` in Testcontainers 2.x) pointing at the project's `docker-compose.yaml`. Wait strategies: HTTP health check on Yamcs (`GET /api/` returns 200), TCP port check on 10000/udp for telemetry ingestion.
- Test scenario — **10,000 Packet Stress Test:**
  1. Start the full stack via Testcontainers.
  2. Wait for Yamcs health check to pass and the realtime processor to initialize.
  3. Inject 10,000 CCSDS packets (APID 100, sequential sequence counters, known lat/lon/alt payload values) via `DatagramSocket` to Yamcs UDP port 10000 at maximum throughput (no artificial delay).
  4. Wait for ingestion to settle (poll archive count until stable for 5 seconds).
  5. Query the Yamcs archive via `yamcs-client` Java API: retrieve all `Latitude` parameter values.
  6. Assert: (a) total archived parameter count >= 9,950 (allowing < 0.5% UDP loss), (b) no sequence counter gaps larger than 5, (c) parameter engineering values match the injected payload within float32 precision.
- Additional test cases:
  - **Packet Rejection Test:** Send a malformed packet (truncated to 4 bytes). Assert Yamcs does not crash and continues processing subsequent valid packets.
  - **Multi-APID Demux Test:** Interleave packets with APID 100 and APID 200 (if PAL-301 MDB is available). Assert both parameter sets are correctly decoded and archived independently.
- Performance metrics: the test must log total injection time, packets/second throughput, and archive query latency. These metrics are written to a `stress_test_report.json` artifact.
- The test suite must be executable with a single `mvn verify` command and produce a standard Surefire/Failsafe XML report compatible with CI systems (Jenkins, GitHub Actions).

**Acceptance Criteria:**
- [ ] Independent Maven project (`integration-tests/`) builds and executes with `mvn verify`. No dependency on Palantir Core source code — only on the published Docker images.
- [ ] Testcontainers starts the full Palantir stack (Yamcs + Core) from `docker-compose.yaml` and tears it down after each test class.
- [ ] 10,000-packet stress test passes: >= 9,950 packets archived, no sequence gap > 5, payload values match injected data.
- [ ] Malformed packet test passes: Yamcs survives a truncated packet and processes the next valid packet without error.
- [ ] `stress_test_report.json` is generated with fields: `total_packets_sent`, `total_packets_archived`, `loss_percentage`, `injection_duration_ms`, `packets_per_second`, `archive_query_latency_ms`.
- [ ] Test execution completes within 5 minutes (excluding Docker image pull time). Timeout is enforced via JUnit `@Timeout` annotation.
- [ ] CI-compatible: produces `target/failsafe-reports/*.xml` parseable by standard CI report plugins.

**Estimate:** 80 man-hours

---

## Epic 5: Advanced Analytics & HPC Integration (Bonus Track)

> **Scope:** This Epic addresses two mission-critical capabilities absent from the current Palantir stack: (1) Space Situational Awareness (SSA) through conjunction assessment and automated collision avoidance, and (2) AI-driven anomaly detection via unsupervised learning on synthetic telemetry. All deliverables are standalone applications or scripts that interact with the Palantir stack through established interfaces (UDP, Yamcs API, XTCE MDB). The core system remains strictly read-only.

### PAL-501: HPC Conjunction Assessment & Monte Carlo Simulation

**Objective:** Build a standalone Java batch application that ingests the Palantir spacecraft's propagated state and cross-references it against 30,000 catalogued debris objects from CelesTrak, computing Time of Closest Approach (TCA) and Probability of Collision (Pc) via Monte Carlo sampling — providing the foundational SSA capability required for any operational LEO mission.

**Technical Context:**
- The batch application is an independent Maven project (e.g., `hpc/conjunction-assessment/`) using Orekit 12.2 for orbital mechanics. It does **not** depend on or import any Palantir Core classes.
- **Debris catalog ingestion:** Download the CelesTrak GP (General Perturbations) catalog in OMM/CSV format from the CelesTrak public API (`https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv`). Parse each entry into an Orekit `TLE` object. The full active catalog contains ~10,000-30,000 objects depending on the group selected.
- **Screening pass:** For each debris object, propagate both the Palantir spacecraft and the debris object over a 7-day prediction window using SGP4. Compute the minimum distance at discrete time steps (60-second intervals). Flag any conjunction where minimum distance < 10 km as a "close approach" requiring detailed analysis.
- **Monte Carlo Pc estimation:** For each flagged close approach, perform N=10,000 Monte Carlo samples. Perturb the initial state vectors of both objects using covariance matrices (simplified: diagonal covariance with 100m position uncertainty, 0.01 m/s velocity uncertainty). Propagate each sample pair to TCA. Pc = (number of samples where miss distance < combined hard-body radius [10m default]) / N.
- **Local validation mode:** A CLI flag `--catalog-limit=500` filters the catalog to the first 500 objects for rapid local testing before HPC deployment. Full 30,000-object runs target a Slurm-based HPC cluster with Java batch partitioning.
- **Output:** A JSON report (`conjunction_report.json`) listing each flagged conjunction with fields: `debris_norad_id`, `debris_name`, `tca_utc`, `miss_distance_m`, `probability_of_collision`, `relative_velocity_m_s`. Additionally, a summary line to stdout: total objects screened, conjunctions flagged, highest Pc encountered.
- **Yamcs integration:** After computation, the batch app pushes the top-10 highest-Pc conjunctions to Yamcs as events via the Yamcs REST API (`POST /api/archive/palantir/events`), enabling operator visibility in the Yamcs Event log.

**Acceptance Criteria:**
- [ ] Independent Maven project builds with `mvn package`. Produces an executable JAR (`java -jar conjunction-assessment.jar`). No dependency on Palantir Core source.
- [ ] Ingests the CelesTrak active debris catalog (CSV format). Parses at least 10,000 TLE entries without error.
- [ ] `--catalog-limit=500` mode completes screening + Monte Carlo in under 10 minutes on a standard developer workstation (4 cores, 16 GB RAM).
- [ ] `conjunction_report.json` is generated with all required fields. At least one conjunction with Pc > 0 is expected against the ISS default TLE (LEO is a congested regime).
- [ ] Monte Carlo Pc values are reproducible (seeded RNG) and validated against a manually computed reference case with known geometry.
- [ ] Top-10 conjunctions are posted to the Yamcs Event log via REST API and visible in the Yamcs web UI.
- [ ] Unit tests (JUnit 5) cover TLE parsing, screening logic, and Monte Carlo sampling with > 80% coverage on core algorithm classes.

**Estimate:** 100 man-hours

---

### PAL-502: Automated Collision Avoidance Telecommanding

**Objective:** Extend the Yamcs Mission Database with a `FIRE_THRUSTER` telecommand and implement a closed-loop collision avoidance script that monitors conjunction assessment results, automatically queues a thruster firing command when Probability of Collision exceeds the 10^-4 threshold, and enforces mandatory human operator approval before command release — ensuring no autonomous maneuver is executed without explicit HMI confirmation.

**Technical Context:**
- **XTCE Command Definition:** Add a new `FIRE_THRUSTER` MetaCommand to `palantir.xml` with the following arguments:
  - `opcode` (uint8) = `0x04` (fixed value, identifies the command type)
  - `delta_v_x` (float32) — velocity change in m/s along the radial axis
  - `delta_v_y` (float32) — velocity change in m/s along the along-track axis
  - `delta_v_z` (float32) — velocity change in m/s along the cross-track axis
  - `burn_duration_s` (uint16) — thruster burn duration in seconds
- **Yamcs Command Verification:** Configure the `FIRE_THRUSTER` command with a `TransmissionConstraint` in XTCE requiring a `ManualVerifier` stage. This ensures the command enters `QUEUED` state but is **not released** to the `tc_realtime` stream until an operator explicitly approves it via the Yamcs web UI commanding interface.
- **Collision Avoidance Script:** A Python script (`collision_avoidance.py`) that:
  1. Polls the Yamcs Event log via REST API (`GET /api/archive/palantir/events`) for conjunction events posted by PAL-501.
  2. Filters events where `Pc > 1e-4` (the COLA red threshold per ESA Space Debris Mitigation standards).
  3. Computes a simplified avoidance maneuver: along-track delta-v = `0.01 m/s * (Pc / 1e-4)` (proportional to threat level), radial and cross-track components = 0, burn duration = 10 seconds.
  4. Issues `POST /api/processors/palantir/realtime/commands/Palantir/FIRE_THRUSTER` with the computed arguments.
  5. Logs the queued command and waits for operator approval (polls command status until `SENT` or `REJECTED`).
- **HMI Integration (PAL-102 extension):** Student A's command panel (PAL-102) should display the queued `FIRE_THRUSTER` command with an "APPROVE" / "REJECT" button. This is a stretch integration — if PAL-102 is already complete, the Yamcs built-in web UI commanding page serves as the approval interface.
- **Safety constraint:** The script must **never** bypass the manual verification stage. If the Yamcs API allows direct command release without verification, the XTCE definition must enforce the constraint server-side.

**Acceptance Criteria:**
- [ ] `FIRE_THRUSTER` command defined in `palantir.xml` with all five arguments (opcode, delta_v_x/y/z, burn_duration_s). Visible in Yamcs commanding interface.
- [ ] `TransmissionConstraint` with `ManualVerifier` is configured. Command enters `QUEUED` state and does **not** auto-release. Verified by sending the command and confirming it waits for operator action.
- [ ] `collision_avoidance.py` polls Yamcs events, detects Pc > 10^-4 conjunctions, and issues a `FIRE_THRUSTER` command with computed delta-v values.
- [ ] The script logs all actions to stdout with timestamps: conjunction detected, command queued, awaiting approval, command approved/rejected.
- [ ] End-to-end test: inject a synthetic conjunction event with Pc = 5e-4 into Yamcs, observe the script queue a thruster command, manually approve it in the Yamcs UI, and verify the command reaches `SENT` status.
- [ ] The script never issues a command without the ManualVerifier constraint active. Attempting to disable the verifier in XTCE causes the script to abort with an error.
- [ ] Documentation (`COLA_PROCEDURE.md`) describes the full collision avoidance workflow: detection, maneuver computation, command queuing, operator approval, and execution verification.

**Estimate:** 80 man-hours

---

### PAL-503: Synthetic Telemetry Generator with Anomaly Injection

**Objective:** Build a standalone Java application that generates continuous synthetic telemetry streams representing a nominal 90-minute LEO orbit (sinusoidal latitude, longitude, and altitude profiles) via CCSDS/UDP, with runtime-configurable CLI triggers to inject realistic thermal runaway and voltage drop anomalies — providing a controlled, repeatable dataset for training and validating anomaly detection models.

**Technical Context:**
- The generator is an independent Maven project (e.g., `simulators/synth-telemetry-gen/`) producing an executable JAR. It transmits CCSDS Space Packets with **APID 500** to the Yamcs UDP port 10000.
- **Nominal telemetry model (APID 500 payload, 24 bytes):**
  - `Latitude` (float32) — sinusoidal: `A * sin(2*pi*t / T_orbit)` where A=51.6 deg (ISS inclination), T_orbit=5400s (90 min)
  - `Longitude` (float32) — sawtooth: `-180 + (360 * (t mod T_orbit) / T_orbit)` with nodal regression offset
  - `Altitude` (float32) — sinusoidal perturbation: `408.0 + 2.0 * sin(2*pi*t / T_orbit + pi/4)` km
  - `Board_Temp` (float32) — eclipse-driven: 20 C (sunlit) / -5 C (eclipse), sinusoidal transitions
  - `Bus_Voltage` (float32) — nominal: 28.0 V with +/- 0.3 V ripple
  - `Gyro_Rate_Z` (float32) — nominal: 0.0 deg/s with +/- 0.01 deg/s noise
- **Anomaly injection via CLI commands** (read from stdin while the generator runs):
  - `THERMAL_RUNAWAY` — `Board_Temp` ramps linearly from current value to +95 C over 120 seconds, then holds.
  - `VOLTAGE_DROP` — `Bus_Voltage` drops exponentially from 28.0 V to 18.0 V with tau=60s, simulating battery cell failure.
  - `TUMBLE` — `Gyro_Rate_Z` ramps from 0.0 to 15.0 deg/s over 30 seconds, simulating loss of attitude control.
  - `NOMINAL` — resets all parameters to nominal profiles.
- **XTCE extension:** Define `Synth_Telemetry_Packet` (APID 500) in `palantir.xml` with all six parameters, appropriate units, and alarm ranges matching the anomaly thresholds (e.g., Board_Temp WARNING > 60 C, CRITICAL > 80 C).
- **Output cadence:** 1 Hz (configurable via `--rate` CLI argument). The generator runs indefinitely until terminated.
- **Dataset export:** A `--record` CLI flag writes all generated samples to a CSV file (`synth_telemetry.csv`) with columns: `timestamp_ms`, `latitude`, `longitude`, `altitude`, `board_temp`, `bus_voltage`, `gyro_rate_z`, `anomaly_label` (NOMINAL, THERMAL_RUNAWAY, VOLTAGE_DROP, or TUMBLE).

**Acceptance Criteria:**
- [ ] Independent Maven project builds an executable JAR with `mvn package`. Runs with `java -jar synth-telemetry-gen.jar`. No Palantir Core dependency.
- [ ] Generates CCSDS packets (APID 500) at 1 Hz with physically plausible nominal orbital and subsystem profiles. All six parameters visible and updating in Yamcs web UI.
- [ ] CLI anomaly injection: typing `THERMAL_RUNAWAY` into stdin triggers a temperature ramp visible in Yamcs within 5 seconds. `NOMINAL` resets all parameters. All four anomaly types functional.
- [ ] `--record` flag produces a CSV with correctly labeled anomaly windows. A 1-hour recording with 2 injected anomalies contains at least 3,600 rows with correct labels.
- [ ] XTCE `Synth_Telemetry_Packet` (APID 500) defines all six parameters with alarms. Yamcs triggers alarm indicators during anomaly injection.
- [ ] Unit tests validate the sinusoidal orbital model (period, amplitude, phase) and each anomaly profile (ramp rate, exponential decay constant, final value).

**Estimate:** 60 man-hours

---

### PAL-504: Autoencoder Model Training & ONNX Export

**Objective:** Develop a Python/PyTorch training pipeline that ingests the synthetic telemetry dataset produced by PAL-503, trains an unsupervised autoencoder to learn the nominal operational envelope, exports the trained model to ONNX format for portable inference, and validates that the model reliably flags all injected anomaly types with a reconstruction error exceeding a calibrated threshold — establishing the foundation for real-time ML-based anomaly detection within the Yamcs processing pipeline.

**Technical Context:**
- **Dataset preparation:** Read `synth_telemetry.csv` (from PAL-503) using `pandas`. Split into training set (NOMINAL-only rows, 80%) and validation set (all rows including anomalies, 20%). Normalize features to [0, 1] range using min-max scaling. Store scaler parameters for inference-time denormalization.
- **Model architecture — LSTM Autoencoder:**
  - Input: sliding window of 60 samples (60 seconds at 1 Hz) x 6 features
  - Encoder: LSTM(input_size=6, hidden_size=32, num_layers=2, batch_first=True) → take final hidden state
  - Bottleneck: Linear(32, 8) → ReLU → Linear(8, 32)
  - Decoder: LSTM(input_size=32, hidden_size=32, num_layers=2, batch_first=True) → Linear(32, 6)
  - Loss: MSE between input window and reconstructed window
- **Training:** Adam optimizer, lr=1e-3, batch_size=64, max 100 epochs with early stopping (patience=10) on validation reconstruction error of NOMINAL samples only. Training should complete in under 30 minutes on a machine with a CUDA GPU, or under 2 hours on CPU.
- **Anomaly threshold calibration:** Compute the 99th percentile of per-window reconstruction error on the NOMINAL validation set. This becomes the anomaly threshold T. Any window with reconstruction error > T is flagged as anomalous.
- **ONNX export:** Use `torch.onnx.export()` to serialize the trained encoder+decoder to `anomaly_detector.onnx` with dynamic batch dimension. Validate the ONNX model using `onnxruntime` inference on 10 test windows (5 nominal, 5 anomalous) and assert outputs match PyTorch within 1e-5 tolerance.
- **Evaluation metrics:** On the validation set containing injected anomalies:
  - Per-anomaly-type detection rate (true positive rate): fraction of anomaly windows correctly flagged
  - False positive rate on NOMINAL windows
  - Target: > 95% detection rate for each anomaly type, < 2% false positive rate on nominal
- **Output artifacts:**
  - `anomaly_detector.onnx` — portable model file
  - `scaler_params.json` — min/max values for each feature
  - `training_report.json` — epochs trained, final train/val loss, threshold T, per-anomaly detection rates, false positive rate
  - `reconstruction_error.png` — time-series plot of reconstruction error with threshold line and anomaly windows highlighted

**Acceptance Criteria:**
- [ ] Training script (`train_autoencoder.py`) runs end-to-end with `python train_autoencoder.py --data synth_telemetry.csv`. Requires only `torch`, `pandas`, `numpy`, `onnx`, `onnxruntime`, `matplotlib`.
- [ ] Model trains on NOMINAL-only data and converges (validation loss decreases for at least 20 epochs before early stopping or reaching 100 epochs).
- [ ] `anomaly_detector.onnx` is exported and passes `onnx.checker.check_model()` validation. File size < 10 MB.
- [ ] ONNX inference via `onnxruntime` produces outputs matching PyTorch within 1e-5 tolerance on 10 test windows.
- [ ] Detection rate > 95% for each anomaly type (THERMAL_RUNAWAY, VOLTAGE_DROP, TUMBLE). False positive rate < 2% on NOMINAL validation windows.
- [ ] `training_report.json` contains all required metrics. `reconstruction_error.png` clearly shows anomaly windows exceeding the threshold.
- [ ] All dependencies installable via `pip install -r requirements.txt`. No proprietary or licensed dependencies.

**Estimate:** 70 man-hours

---

## Integration Plan (12 Sprints x 2 Weeks — 6 Months)

### Team Structure

| Role | Owner | Scope |
|------|-------|-------|
| **Student A** — HMI & Web | Frontend / Operator UX | Epic 1 (PAL-101, PAL-102) |
| **Student B** — Java Integrator & Data | Backend / Systems / QA | Epic 2 (PAL-201, PAL-202), Epic 3 (PAL-301, PAL-302), Epic 4 (PAL-401, PAL-402, PAL-403), Epic 5 (PAL-501, PAL-502, PAL-503, PAL-504) |

### Team Structure

| Role | Owner | Scope |
|------|-------|-------|
| **Student A** — HMI & Web | Frontend / Operator UX | Epic 1 (PAL-101, PAL-102) |
| **Student B** — Java Integrator & Data | Backend / Systems / QA | Epic 2 (PAL-201, PAL-202), Epic 3 (PAL-301, PAL-302), Epic 4 (PAL-401, PAL-402, PAL-403) |

---

### Phase 1: Foundation (Sprints 1-3, Weeks 1-6)

#### Sprint 1 — Environment Bootstrap & First Contact (Weeks 1-2)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | Dev environment operational: `docker compose up` runs the full stack. Yamcs Web UI accessible. CesiumJS project scaffolded (`npm init`, Cesium viewer renders empty globe). First successful WebSocket connection to Yamcs parameter subscription endpoint. | Core team provides Docker images |
| **B** | Dev environment operational. Python virtualenv with `yamcs-client`, `pandas`, `matplotlib` installed. First successful `archive.list_parameter_values()` call returns live data. Familiarization with XTCE schema structure by reading existing `palantir.xml`. | Core team provides Docker images, minimum 1 hour of archived telemetry |

**Sprint 1 Gate:** Both students demonstrate bidirectional data flow — A shows a WebSocket message logged to browser console, B shows a pandas DataFrame printed from Yamcs archive.

#### Sprint 2 — Core Ticket Development Begins (Weeks 3-4)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **PAL-101 (In Progress):** Spacecraft position renders on CesiumJS globe updating at 1 Hz. Basic point entity tracking live lat/lon/alt. Ground track polyline prototype (last 10 minutes). | WebSocket subscription from Sprint 1 |
| **B** | **PAL-201 (In Progress):** CSV export functional with correct columns. `ground_track.png` renders with coastline overlay. CLI argument parsing (`--start`, `--stop`) implemented. | Yamcs archive access from Sprint 1 |

**Sprint 2 Gate:** A shows a moving dot on the globe. B shows a generated ground track plot.

#### Sprint 3 — First Tickets Code-Complete (Weeks 5-6)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **PAL-101 (Complete):** Full 90-minute ground track history, altitude overlay panel, auto-reconnect logic. Code review and merge. | None |
| **B** | **PAL-201 (Complete):** All plots, statistics, and CSV export finalized. **PAL-301 (Started):** XTCE schema draft for `Env_Payload_Packet` (APID 200) with initial parameter definitions. | Core team review of XTCE draft |

**Sprint 3 Gate:** PAL-101 and PAL-201 are code-complete and demonstrated. PAL-301 XTCE draft submitted for architectural review.

---

### Phase 2: Feature Expansion (Sprints 4-6, Weeks 7-12)

#### Sprint 4 — Second Wave Tickets (Weeks 7-8)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **PAL-102 (In Progress):** Command panel UI scaffolded. "Send PING" and "Send REBOOT_OBC" buttons issue REST API calls. Basic response handling. | Yamcs commanding API |
| **B** | **PAL-301 (Complete):** XTCE with all four environmental parameters, alarms, and `Radiation_Dose` polynomial calibration validated. Parameters visible in Yamcs UI. **PAL-302 (Started):** `send_env_packet.py` test sender script development begins. | PAL-301 merged to MDB |

**Sprint 4 Gate:** A demonstrates a command sent from browser and visible in Yamcs command history. B demonstrates APID 200 parameters decoded in Yamcs UI.

#### Sprint 5 — Feature Completion & Cross-Integration (Weeks 9-10)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **PAL-102 (Complete):** Command history log table with auto-refresh, error handling, full acceptance criteria met. | None |
| **B** | **PAL-302 (Complete):** End-to-end validation, alarm triggering, archive retrieval confirmed. `validation_report.md` written. **PAL-202 (Started):** AOS/LOS geometric model implementation begins. | PAL-301 deployed in Yamcs |

**Sprint 5 Gate:** Epic 1 complete (PAL-101 + PAL-102). Epic 3 complete (PAL-301 + PAL-302). First cross-integration test: A's HMI displays environmental parameters defined by B's XTCE work.

#### Sprint 6 — Analytics Completion & Epic 4 Kickoff (Weeks 11-12)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **Buffer sprint:** Polish PAL-101/102 based on user feedback. Begin research on CesiumJS 3D model loading and satellite FOV cone visualization (stretch goal, not ticketed). Assist B with PAL-202 plot review. | None |
| **B** | **PAL-202 (Complete):** Pass prediction validated against 6+ hours of telemetry, report and visibility timeline generated. **PAL-401 (Started):** Yamcs plugin Maven project scaffolded, quaternion math implemented and unit-tested in isolation. | Archived telemetry from Sprint 5 |

**Sprint 6 Gate:** Epic 2 complete (PAL-201 + PAL-202). B demonstrates standalone quaternion-to-Euler unit tests passing. Mid-project review with core team.

---

### Phase 3: Enterprise Java & SSA (Sprints 7-9, Weeks 13-18)

#### Sprint 7 — Yamcs Plugin & Conjunction Assessment Kickoff (Weeks 13-14)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **Stretch / Support:** Integrate PAL-202 AOS/LOS data into HMI — display next pass countdown on CesiumJS overlay. Support B with XTCE extensions for APID 300. | PAL-202 output data |
| **B** | **PAL-401 (In Progress):** Plugin JAR builds and loads into Yamcs without errors. XTCE `Attitude_Packet` (APID 300) defined. `send_attitude_packet.py` test harness transmits known quaternions. First derived Euler values appear in Yamcs UI. **PAL-501 (Started):** Conjunction assessment Maven project scaffolded. CelesTrak catalog parser ingests 500-object test subset. | Yamcs Docker image modification |

**Sprint 7 Gate:** B demonstrates derived Euler parameters in Yamcs UI. CelesTrak parser produces 500 valid TLE objects.

#### Sprint 8 — Plugin Hardening & Screening Pass (Weeks 15-16)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **Stretch / Support:** Add APID 300 attitude parameters to HMI display (Roll/Pitch/Yaw gauges or numerical readout). Begin research on conjunction visualization overlay for CesiumJS (threat corridors). | PAL-401 Euler parameters available in Yamcs |
| **B** | **PAL-401 (Complete):** All 5 reference quaternion pairs validated including gimbal lock edge case. Norm violation event logging confirmed. Unit test coverage > 90%. **PAL-501 (In Progress):** Screening pass functional against 500-object subset. Close approaches (< 10 km) flagged. Monte Carlo Pc estimation prototype running for a single conjunction. | None |

**Sprint 8 Gate:** PAL-401 code-complete. B demonstrates a screening pass identifying at least one close approach and a preliminary Pc value.

#### Sprint 9 — Conjunction Assessment Complete & Simulator Kickoff (Weeks 17-18)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **Stretch / Support:** HMI consolidated view — single dashboard showing orbital track (APID 100), environmental health (APID 200), attitude (APID 300). Begin adding conjunction alert panel (reading Yamcs events from PAL-501). | XTCE for APID 300 from B, PAL-501 events |
| **B** | **PAL-501 (Complete):** Full 500-object local validation passes. Monte Carlo Pc reproducible with seeded RNG. `conjunction_report.json` generated. Top-10 events posted to Yamcs. Unit tests > 80% coverage. **PAL-402 (Started):** EO Payload Simulator Spring Boot project scaffolded. CCSDS encoder for APID 400 implemented. | None |

**Sprint 9 Gate:** PAL-501 code-complete (local mode). Conjunction events visible in Yamcs Event log. EO simulator generates a raw CCSDS packet in a unit test.

---

### Phase 4: Simulators & Collision Avoidance (Sprints 10-11, Weeks 19-22)

#### Sprint 10 — EO Simulator & COLA Command Definition (Weeks 19-20)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **Stretch / Support:** Add EO payload status panel to HMI (APID 400 parameters). Add `FIRE_THRUSTER` button to command panel (PAL-102 extension) with APPROVE/REJECT workflow. | XTCE for APID 400 and FIRE_THRUSTER from B |
| **B** | **PAL-402 (Complete):** Simulator generates physically plausible EO telemetry at 1 Hz. Sinusoidal band model and eclipse thermal model operational. Docker Compose integration complete. XTCE for APID 400 merged. README documented. **PAL-502 (Started):** `FIRE_THRUSTER` command defined in XTCE with `ManualVerifier` constraint. `collision_avoidance.py` script scaffolded. | PAL-501 conjunction events in Yamcs |

**Sprint 10 Gate:** PAL-402 code-complete. Five telemetry sources streaming into Yamcs (APID 100, 200, 300, 400, 500). `FIRE_THRUSTER` command visible in Yamcs commanding interface with manual approval gate.

#### Sprint 11 — Collision Avoidance Complete & Synth Generator (Weeks 21-22)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | **Cross-integration testing:** Execute full operator scenarios — orbit visualization, commanding (including FIRE_THRUSTER approval flow), alarm monitoring across all APIDs. File bug reports for integration issues. | PAL-502 command workflow |
| **B** | **PAL-502 (Complete):** Closed-loop script detects Pc > 10^-4, queues FIRE_THRUSTER, waits for operator approval. End-to-end test with synthetic conjunction event passes. `COLA_PROCEDURE.md` documented. **PAL-503 (Started):** Synth telemetry generator scaffolded. Nominal sinusoidal orbital model transmitting APID 500 packets. | PAL-501 events, FIRE_THRUSTER in XTCE |

**Sprint 11 Gate:** PAL-502 code-complete. Full COLA loop demonstrated: conjunction detected → command queued → operator approves in UI → command released. Synth generator streaming nominal telemetry.

---

### Phase 5: AI/ML & QA (Sprint 12, Weeks 23-24)

#### Sprint 12 — Anomaly Detection, Integration Testing & Delivery (Weeks 23-24)

| Student | Deliverable | Dependencies |
|---------|-------------|--------------|
| **A** | Final HMI polish across all panels. Contribute Epic 1 section to `INTEGRATION_REPORT.md`. Record screen-capture demo of full operator workflow. Prepare live demo segment. | All HMI features stable |
| **B** | **PAL-503 (Complete):** All four anomaly injection types functional. `--record` produces labeled CSV. XTCE for APID 500 with alarms merged. **PAL-504 (Complete):** Autoencoder trained on NOMINAL data, ONNX exported, detection rate > 95% per anomaly type, FPR < 2%. All artifacts generated. **PAL-403 (Complete):** Testcontainers stress test (10,000 packets) passes. Malformed packet resilience and multi-APID demux validated. `stress_test_report.json` generated. CI-compatible reports produced. | PAL-503 dataset, Docker images |
| **Both** | Unified `INTEGRATION_REPORT.md` delivered. Joint live demo: end-to-end Palantir Digital Twin with all subsystems — orbital visualization, telecommanding, COLA workflow, environmental/attitude/EO monitoring, conjunction assessment, anomaly detection pipeline, and automated QA. Project handoff to core team. | All tickets closed |

**Sprint 12 Gate:** End-to-end demonstration of the complete Palantir Digital Twin: orbital visualization + commanding (A), environmental monitoring + attitude processing (B), EO payload simulation (B), conjunction assessment + collision avoidance (B), synthetic telemetry + ML anomaly detection (B), and automated QA validation (B). All 13 tickets closed. Project deliverables archived and handed off.

---

## Effort Summary

| Epic | Tickets | Estimated Effort |
|------|---------|-----------------|
| Epic 1: HMI & Spacecraft Operations Display | PAL-101 (30h), PAL-102 (20h) | 50 man-hours |
| Epic 2: Flight Dynamics & Payload Analytics | PAL-201 (25h), PAL-202 (30h) | 55 man-hours |
| Epic 3: Mission Database & Systems Integration | PAL-301 (20h), PAL-302 (25h) | 45 man-hours |
| Epic 4: Enterprise Java Integration & Validation | PAL-401 (60h), PAL-402 (70h), PAL-403 (80h) | 210 man-hours |
| Epic 5: Advanced Analytics & HPC Integration | PAL-501 (100h), PAL-502 (80h), PAL-503 (60h), PAL-504 (70h) | 310 man-hours |
| | | **670 man-hours** |

> **Note on ticket assignment:** Tickets are assigned dynamically by the project lead or claimed by students based on availability and skill development goals. The sprint plan above suggests a default routing, but any ticket may be reassigned between students or picked up by the core team as needed.

---

## Strategic Execution Guidelines (6-Month Plan)

*From the desk of the Lead System Engineer — directives for the student integration team.*

### Directive 1: Absolute Core Isolation

The Palantir Core codebase (`src/main/java/io/github/jakubt4/palantir/`) is **strictly read-only** for all student contributors. No pull requests modifying the core source tree, core `pom.xml`, core `Dockerfile`, or core `application.yaml` will be accepted. All student deliverables — Yamcs plugins, simulators, test suites, analytics scripts, ML pipelines — must be developed in **independent projects** that interact with the Palantir stack exclusively through documented network interfaces: UDP (ports 10000, 10001), Yamcs REST API (port 8090), Yamcs WebSocket API, and the shared XTCE Mission Database. This constraint is non-negotiable. It ensures the flight-heritage core remains stable and certifiable while enabling parallel development at full velocity. If a student discovers a bug or limitation in the core, they must file a report to the core team — never patch it directly.

### Directive 2: AI-Accelerated Onboarding

Students are **required** to leverage Large Language Models (Claude Code, ChatGPT, Copilot) as their primary onboarding accelerator. The Yamcs 5.12 ecosystem has limited community documentation and a steep learning curve. Rather than spending weeks reading source code, students must feed the provided project documentation (`CLAUDE.md`, `ARCHITECTURE.md`, `FEATURES_v2.md`, this backlog, and the Yamcs configuration files) into an LLM and use it to:
- Generate XTCE schema fragments and validate them against the specification.
- Scaffold Maven projects for Yamcs plugins with correct dependency declarations.
- Debug Yamcs processor configuration errors by analyzing log output.
- Prototype CCSDS packet encoders/decoders with correct byte-level layout.

The expectation is that a student who effectively uses LLM-assisted development will compress the typical 4-week Yamcs learning curve into 1 week. Students who refuse to adopt this tooling will fall behind the sprint cadence and jeopardize integration milestones.

### Directive 3: Local Verification Before HPC

All distributed and computationally intensive algorithms — specifically the conjunction assessment (PAL-501) and Monte Carlo Pc estimation — **must be fully validated locally** on a filtered, reduced dataset before any Slurm cluster deployment is attempted. The mandatory local validation profile is:
- **Catalog subset:** `--catalog-limit=500` (first 500 objects from CelesTrak catalog)
- **Prediction window:** 24 hours (not the full 7-day production window)
- **Monte Carlo samples:** N=1,000 (not the production N=10,000)

This local run must complete in under 10 minutes on a standard developer workstation (4 cores, 16 GB RAM) and produce a valid `conjunction_report.json` with reproducible Pc values (seeded RNG). Only after this local validation passes — with unit tests confirming mathematical correctness — may the student request HPC cluster access. Deploying untested code to shared HPC resources wastes compute allocation and delays other research groups. The core team will gate HPC access behind a mandatory local validation report review.

### Directive 4: Incremental Integration

Every bi-weekly Sprint Review (Fridays, end of each sprint) requires a **live, end-to-end demonstration** of data flowing through the student's deliverable — from source (simulator, script, or external input) through the Palantir stack (UDP ingestion, Yamcs processing, archive storage) to a visible output (Yamcs web UI parameter display, generated plot, JSON report, or HMI visualization). Isolated code fragments, unit tests without integration, or "it works on my machine" screenshots are **not acceptable** as sprint deliverables. The demonstration must run against the shared `docker compose up` stack with the student's component deployed alongside the core system. This forces continuous integration discipline and surfaces interface mismatches (byte order, APID conflicts, XTCE schema errors) within days rather than months. A sprint where a student cannot demonstrate end-to-end data flow is a failed sprint — the retrospective must identify the root cause and the recovery plan before the next sprint begins.
