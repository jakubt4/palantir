# Project Palantir: Student Integration Backlog

## Executive Summary & Pedagogical ROI

This document defines a 6-month, two-student integration programme that transforms the Palantir Digital Twin from a single-service satellite simulator into a multi-subsystem mission control platform — complete with 3D operator displays, multi-payload telemetry ingestion, collision avoidance automation, and AI-driven anomaly detection. The programme is not a sandbox exercise. It is a structured engineering onboarding that mirrors the first six months of a junior systems engineer's career at a SARIO Spaceport_SK incubatee, a satellite operator, or a defence-sector ground segment integrator. Every ticket produces a deployable artefact that integrates with a live CCSDS/Yamcs stack — the same protocol and mission control ecosystem used by ESA, EUMETSAT, and commercial operators across Europe.

The programme takes two university students and transitions them from the world of standard academic computer science assignments and basic academic projects into mission-critical, real-time space operations. One learning path focuses on real-time operator display development — where WebSocket latency, coordinate system conversions, and safety-critical UX patterns replace typical web application concerns. The other path bridges Java application development with aerospace-grade binary protocols, XTCE mission database engineering, and high-performance simulation — skill sets that are scarce in the European space workforce and command premium placement in SSA, flight dynamics, and ground segment roles. These paths are not rigid silos: both students will encounter the full vertical stack of a modern space mission — from byte-level CCSDS packet encoding through Yamcs server-side processing to publication-quality flight dynamics analysis and ML-based health monitoring — and are encouraged to cross-train across domains as capacity and interest allow.

Upon completion, each student leaves with a portfolio of deployable artefacts spanning the full tech stack: CesiumJS real-time 3D displays with WebSocket integration, Yamcs server-side Java plugins, CCSDS binary protocol encoders, Python flight dynamics pipelines (pandas, matplotlib, cartopy), ONNX-exported PyTorch anomaly detection models, Testcontainers-based integration test suites, and Docker Compose multi-service orchestration. Beyond the technical artefacts, the programme develops engineering cognition that university coursework rarely exercises: reasoning about byte-level binary protocols under real-time constraints, designing safety-critical operator interfaces where a wrong button press has consequences, debugging distributed systems across network boundaries, and making architectural trade-offs in a live integration environment where upstream changes are outside your control. These are the cognitive patterns that separate a graduate who can write code from one who can ship systems — and they are directly demonstrable in technical interviews across the European space, defence, and systems engineering sectors.

---

## Optimal Execution Path (The Master Sequence)

The following is the strictly ordered build sequence for all tickets across all Epics. This sequence eliminates dependency hell by ensuring that every ticket's prerequisites are satisfied before work begins. Tickets listed at the same level may be executed in parallel by different team members.

1. **PAL-101** (Epic 1) — *Real-Time Orbital Ground Track on CesiumJS Globe*
   First contact with the Yamcs WebSocket API. Establishes the foundational HMI layer and proves bidirectional data flow from mission control to operator display. No upstream dependencies beyond the running Palantir Core stack.

2. **PAL-201** (Epic 2) — *Orbital Telemetry Export & Trend Analysis Pipeline* *(parallel with PAL-101)*
   First contact with the Yamcs Archive API via `yamcs-client` Python library. Establishes the offline analytics pattern. Can execute simultaneously with PAL-101 as they share no code or interface dependencies.

3. **PAL-102** (Epic 1) — *Telecommand Control Panel with Execution Feedback*
   Introduces the Yamcs REST commanding API. Can begin as soon as the team is comfortable with the Yamcs HTTP interface. Naturally follows PAL-101 as the second HMI deliverable.

4. **PAL-202** (Epic 2) — *Automated AOS/LOS Pass Prediction Report* *(parallel with PAL-102)*
   Builds on the Yamcs archive querying pattern established in PAL-201. Adds orbital geometry computation. Can execute simultaneously with PAL-102.

5. **PAL-301** (Epic 3) — *XTCE Payload Telemetry Definition for Environmental Monitoring*
   The architectural gatekeeper for all multi-payload work. Defines the XTCE extension pattern (APID 200) that every subsequent payload ticket replicates. Must be completed and validated before PAL-302, and its pattern informs PAL-401, PAL-402, and PAL-503.

6. **PAL-302** (Epic 3) — *Multi-Packet Stream Configuration & Archive Validation*
   **Hard dependency on PAL-301.** Validates that the XTCE definitions from PAL-301 function end-to-end. Establishes the byte-level CCSDS test injection methodology reused by PAL-401, PAL-402, and PAL-403.

7. **PAL-401** (Epic 4) — *Yamcs Custom Algorithm Plugin — Quaternion-to-Euler Attitude Processor*
   Introduces Yamcs Java plugin development and a new XTCE container (APID 300). The math and plugin work are independent of prior tickets, but the XTCE authoring benefits from the pattern established in PAL-301.

8. **PAL-402** (Epic 4) — *Independent Payload Simulator Microservice — Earth Observation Sensor* *(parallel with PAL-401)*
   Independent Spring Boot project with a new APID (400). Follows the CCSDS encoding pattern from PAL-302's test sender and the XTCE pattern from PAL-301. Can run in parallel with PAL-401.

9. **PAL-501** (Epic 5) — *HPC Conjunction Assessment & Monte Carlo Simulation* *(parallel with PAL-402)*
   Standalone Orekit batch application with no Yamcs pipeline dependency. Can begin as soon as a student is available. Outputs conjunction events to Yamcs, which PAL-502 consumes.

10. **PAL-403** (Epic 4) — *Enterprise QA & Integration Testing — Testcontainers Stress Validation*
    Benefits from having PAL-301's XTCE MDB available for the multi-APID demux test case. Best scheduled after PAL-301/302 are merged but can proceed with APID-100-only tests independently.

11. **PAL-502** (Epic 5) — *Automated Collision Avoidance Telecommanding*
    **Hard dependency on PAL-501.** Requires conjunction events in the Yamcs event log to trigger the COLA loop. Also extends the XTCE with `FIRE_THRUSTER` telecommand.

12. **PAL-503** (Epic 5) — *Synthetic Telemetry Generator with Anomaly Injection* *(parallel with PAL-502)*
    Independent synthetic data generator. No upstream dependency beyond XTCE authoring knowledge from PAL-301. Produces the labeled dataset that PAL-504 consumes.

13. **PAL-504** (Epic 5) — *Autoencoder Model Training & ONNX Export*
    **Hard dependency on PAL-503.** Requires the `synth_telemetry.csv` dataset with labeled anomaly windows. Terminal node in the dependency graph — the final deliverable.

---

## Scope & Architectural Boundary

**Off-Limits (Core System):** The Java 21 Spring Boot application, Orekit propagator, CCSDS 133.0-B-1 packet encoder, Virtual Thread dispatcher, and UDP transport layer (`CcsdsTelemetrySender`, `UdpCommandReceiver`, `OrbitPropagationService`) are maintained exclusively by the core engineering team. Students **must not** modify any source under `src/main/java/io/github/jakubt4/palantir/`.

**Student Domain:** All work operates on the interfaces exposed by the running system:
- **Yamcs Web API** (HTTP/WebSocket on port 8090)
- **Yamcs Mission Database** (XTCE XML under `yamcs/mdb/`)
- **Yamcs Client Libraries** (`yamcs-client` for Python, Yamcs Web API for JS/TS)

---

<div style="page-break-before: always;"></div>

## Epic 1: HMI & Spacecraft Operations Display

This Epic establishes the real-time Human-Machine Interface layer of the Palantir Digital Twin — the operator-facing presentation tier that transforms raw CCSDS telemetry into actionable situational awareness for mission controllers. It delivers two foundational capabilities: a CesiumJS-based 3D orbital visualization providing continuous, real-time spacecraft ground track rendering via WebSocket-driven parameter subscription, and a telecommand control panel enabling bidirectional operator interaction with the spacecraft through the Yamcs REST commanding API. Together, these components form the minimum viable operator workstation — the entry point through which all subsequent mission monitoring, commanding, and anomaly response workflows will be accessed, and the primary interface that ESA BIC evaluators and Spaceport_SK mentors will use to assess the platform's operational readiness.

Within the Palantir architecture, Epic 1 operates exclusively at the presentation boundary: it consumes processed telemetry parameters published by the Yamcs realtime processor via WebSocket and issues telecommands through the Yamcs HTTP commanding interface. No direct interaction with the CCSDS transport layer, the Orekit propagation engine, or the UDP data links is required. This isolation ensures that HMI development proceeds independently of core system evolution, while the WebSocket and REST API contracts provide a stable, well-documented integration surface that mirrors the interface patterns used in operational ESA and commercial ground segments worldwide.

* **PAL-101:** Real-Time Orbital Ground Track on CesiumJS Globe
* **PAL-102:** Telecommand Control Panel with Execution Feedback

---

<div style="page-break-before: always;"></div>

### PAL-101: Real-Time Orbital Ground Track on CesiumJS Globe

**Objective:** Build a browser-based 3D operator display that subscribes to live Palantir telemetry parameters (`Latitude`, `Longitude`, `Altitude`) via the Yamcs WebSocket API and renders the spacecraft's ground track on a CesiumJS globe in real time.

**Tech Stack:** JavaScript/TypeScript, CesiumJS, Yamcs WebSocket API, HTML5/CSS3, npm

**The 'Plain English' Goal:** Build a live 3D globe that shows exactly where the satellite is right now — like Google Earth for mission control operators tracking an asset in orbit.

**What You Will Learn (Value Add):**
- Real-time WebSocket integration for live telemetry streaming from a mission control system
- 3D geospatial visualization with CesiumJS (the same engine used by AGI/Cesium for satellite tracking)
- Coordinate system conversions (geodetic lat/lon/alt to Cartesian) — a fundamental skill in any space or GIS domain

**Business Value / Real-World Impact:** Replaces expensive proprietary COTS operator displays (AGI STK, Airbus GeoSuite) with a zero-license-cost, browser-native alternative — reducing per-operator-seat HMI costs by 80%+ and enabling instant cloud deployment. This is a key differentiator for GSaaS customers who refuse capital expenditure on desktop software, and demonstrates the "thin-client mission control" capability that Spaceport_SK mentors and future ESA BIC evaluators expect from a scalable Digital Twin proposal.

**Technical Context:**
- Yamcs exposes a WebSocket endpoint at `ws://localhost:8090/api/websocket` for parameter subscriptions. Subscribe to processor `realtime` on instance `palantir`.
- Parameters are defined in the XTCE MDB at paths: `/Palantir/Latitude`, `/Palantir/Longitude`, `/Palantir/Altitude`.
- CesiumJS (`cesium` npm package) provides `Viewer`, `Entity`, and `SampledPositionProperty` for time-dynamic 3D visualization.
- The display must convert geodetic coordinates (lat/lon/alt) to Cartesian via `Cesium.Cartesian3.fromDegrees()`. Altitude from Yamcs is in **kilometers**; CesiumJS expects **meters**.
- Use vanilla JavaScript or TypeScript. No framework requirement. A single `index.html` + bundled JS is acceptable.

**Acceptance Criteria:**
- [ ] WebSocket connection to Yamcs establishes and auto-reconnects on disconnect.
- [ ] Spacecraft icon (point or model) updates position on the CesiumJS globe at 1 Hz matching the propagator cadence.
- [ ] Ground track polyline renders the last ~93 minutes (one full LEO orbit at ISS altitude) of trajectory history.
- [ ] Altitude is displayed in an overlay panel in km with 2-decimal precision.
- [ ] Application runs with `npm start` or by opening `index.html` in a browser; no backend required.

**Estimate:** 30 man-hours

**Dependencies:** None / Palantir Core System

**Execution Mode:** Individual Focus (Solo) — WebSocket integration and CesiumJS 3D rendering require deep, uninterrupted focus on coordinate system conversions and real-time visualization debugging.

---

<div style="page-break-before: always;"></div>

### PAL-102: Telecommand Control Panel with Execution Feedback

**Objective:** Implement a web-based operator panel that issues telecommands (`PING`, `REBOOT_OBC`) to the spacecraft via the Yamcs REST API and displays command history with execution status.

**Tech Stack:** JavaScript/TypeScript, HTML5/CSS3, Yamcs REST API, Yamcs WebSocket API

**The 'Plain English' Goal:** Build the buttons that mission controllers use to talk to the satellite — and the command log that proves the satellite received the instruction.

**What You Will Learn (Value Add):**
- REST API integration for spacecraft commanding — the standard interface pattern used in operational ground segments
- Command lifecycle management (QUEUED → RELEASED → SENT) — understanding how telecommand verification works in real missions
- Error handling and operator feedback design for safety-critical user interfaces

**Business Value / Real-World Impact:** Provides a white-label commanding interface customizable per customer mission profile, eliminating dependency on Yamcs's built-in UI for operator-facing workflows. Enables the platform to monetize telecommand orchestration as a premium GSaaS tier while reducing operator cognitive load during time-critical anomaly response — directly preventing costly command errors that in operational missions risk multi-million-dollar asset loss.

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

**Dependencies:** None / Palantir Core System

**Execution Mode:** Individual Focus (Solo) — Straightforward REST API integration with a focused UI deliverable; low cognitive complexity suits solo development.

---

<div style="page-break-before: always;"></div>

## Epic 2: Flight Dynamics & Payload Analytics

This Epic delivers the post-processing and analytical intelligence layer of the Palantir ground segment — converting archived telemetry from raw parameter time-series into the flight dynamics products that mission analysts use to assess orbit health, schedule ground station contacts, and brief mission directors. It introduces Python-based scientific computing pipelines that query the Yamcs archive API, perform orbital geometry calculations, and produce publication-quality visualizations and structured data exports. The deliverables directly replicate the post-pass analysis workflow performed after every satellite contact in operational LEO missions — the same reports and plots that flight dynamics teams at ESA ESOC, EUMETSAT, and commercial operators produce daily as part of routine constellation management.

Architecturally, both tickets in this Epic operate as offline consumers of the Yamcs telemetry archive — they read historical parameter values via the `yamcs-client` Python library and produce static output artifacts (CSV exports, matplotlib plots, pass prediction reports). This read-only, archive-driven pattern ensures zero interference with the real-time telemetry processing chain and enables execution at any time after data collection, making these tools suitable for both live operations support and historical mission review. The flight dynamics competencies exercised here — ground track visualization with cartographic overlays, orbital statistics computation, and AOS/LOS pass prediction using great-circle geometry and elevation angle analysis — are directly transferable to SSA, mission planning, and ground station scheduling roles across the European space sector, and form the analytical foundation upon which the advanced SSA capabilities in Epic 5 are built.

* **PAL-201:** Orbital Telemetry Export & Trend Analysis Pipeline
* **PAL-202:** Automated AOS/LOS Pass Prediction Report

---

<div style="page-break-before: always;"></div>

### PAL-201: Orbital Telemetry Export & Trend Analysis Pipeline

**Objective:** Build a Python pipeline that extracts archived telemetry from the Yamcs API, computes orbital statistics, and generates publication-quality plots of the spacecraft's trajectory and altitude profile over a configurable time window.

**Tech Stack:** Python 3, yamcs-client, pandas, matplotlib, cartopy, argparse

**The 'Plain English' Goal:** Extract satellite position data from mission control's archive and turn it into the plots and statistics that flight dynamics engineers use to assess orbit health — the same deliverables produced after every real satellite pass.

**What You Will Learn (Value Add):**
- Scientific data pipeline development with pandas — a transferable skill across aerospace, finance, and data engineering
- Publication-quality geospatial visualization with matplotlib and cartopy
- Mission control archive API integration using the yamcs-client library

**Business Value / Real-World Impact:** Automates post-pass flight dynamics reporting that currently requires 2–4 hours of manual analyst effort per satellite per day, enabling a single operator to manage a constellation of 50+ assets. This directly enables the GSaaS unit economics that SARIO Spaceport_SK evaluators expect from a commercially viable space startup — monetizing raw telemetry archives into actionable flight dynamics products at zero marginal cost per additional spacecraft.

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

**Dependencies:** None / Palantir Core System (requires at least 2 hours of archived telemetry in Yamcs)

**Execution Mode:** Individual Focus (Solo) — Python data pipeline with pandas/matplotlib is a well-scoped linear development task requiring systematic, uninterrupted concentration.

---

<div style="page-break-before: always;"></div>

### PAL-202: Automated AOS/LOS Pass Prediction Report

**Objective:** Compute Acquisition of Signal (AOS) and Loss of Signal (LOS) windows for a configurable ground station by post-processing archived latitude/longitude telemetry against a station visibility mask.

**Tech Stack:** Python 3, yamcs-client, numpy, matplotlib, argparse

**The 'Plain English' Goal:** Compute when our satellite can "see" a ground station — the exact seconds it rises above the horizon and disappears again — which is how real missions schedule their communication windows.

**What You Will Learn (Value Add):**
- Orbital geometry and great-circle distance computation — a core flight dynamics competency
- AOS/LOS pass prediction — the same calculation that drives every ground station scheduling system in the industry
- Automated engineering report generation from telemetry archives

**Business Value / Real-World Impact:** Eliminates manual ground station scheduling — the single largest operational bottleneck for multi-satellite LEO operators — and enables dynamic pass allocation across a federated ground station network. Directly reduces per-pass communication costs and unlocks constellation-scale operations without linear headcount growth, which is the scalability proof point commercial investors and SARIO Spaceport_SK evaluators require for incubation acceptance.

**Technical Context:**
- A ground station is defined by its geodetic coordinates (lat, lon, alt) and a minimum elevation angle (typically 5-10 degrees).
- Visibility computation: from the spacecraft's geodetic position and the station's position, compute the Earth central angle and elevation angle. AOS occurs when elevation crosses above the threshold; LOS when it drops below.
- Use `numpy` for vectorized great-circle and elevation calculations. First compute the Earth central angle `γ` between the sub-satellite point and the ground station using the Haversine formula, then apply the elevation formula: `el = arctan((cos(γ) - R_earth / (R_earth + h_sat)) / sin(γ))` where `h_sat` is the satellite altitude above the surface and `R_earth ≈ 6371 km`. For initial implementation, this spherical geometric model is acceptable.
- Input: archived telemetry from Yamcs (`yamcs-client`), ground station config (JSON or CLI args).
- Output: a Markdown or CSV report listing each pass with AOS time, LOS time, max elevation, and pass duration.

**Acceptance Criteria:**
- [ ] Script accepts ground station coordinates and minimum elevation angle as CLI arguments.
- [ ] Default ground station: Kosice, Slovakia (48.7164 N, 21.2611 E, 206 m).
- [ ] Produces a `pass_report.csv` with columns: `pass_number`, `aos_time`, `los_time`, `max_elevation_deg`, `duration_seconds`.
- [ ] Generates a `visibility_timeline.png` showing elevation angle vs. time with AOS/LOS crossings marked.
- [ ] Validated against at least 6 hours of archived telemetry with a minimum of 2 detected passes for a typical LEO orbit.

> **Risk Mitigation & Architect's Advice:** The elevation angle formula looks intimidating but is just trigonometry on a sphere. Start by computing the great-circle distance between the ground station and the sub-satellite point using the Haversine formula — `numpy` has everything you need, and LLMs can generate a correct Haversine implementation in seconds. Get that single function working and unit-tested first, then layer on the elevation calculation. Do not attempt to implement a full SGP4 propagator or use Orekit from Python — you are post-processing positions that Yamcs already has. If your pass count is wrong, plot the raw elevation angle vs. time first; the AOS/LOS crossings should be visually obvious and will tell you whether your geometry is correct before you write the threshold-crossing detection logic.

**Estimate:** 30 man-hours

**Dependencies:** None / Palantir Core System (requires at least 6 hours of archived telemetry in Yamcs)

**Execution Mode:** Individual Focus (Solo) — Orbital geometry math (Haversine, elevation angle computation) requires deep concentration; the sequential trigonometric derivation benefits from uninterrupted focus.

---

<div style="page-break-before: always;"></div>

## Epic 3: Mission Database & Systems Integration

This Epic addresses the foundational data modelling and systems integration challenge of scaling the Palantir platform from a single-instrument telemetry decoder to a multi-payload mission control system. It delivers the XTCE Mission Database extensions required to define, decode, and validate telemetry from a new environmental monitoring payload (APID 200), and establishes the end-to-end validation methodology that proves the entire ingestion-decode-archive pipeline functions correctly for the new packet type. This Epic is the architectural gatekeeper for all subsequent payload integrations — every new APID, parameter set, and alarm configuration that enters the Palantir MDB in Epics 4 and 5 will follow the pattern established here, making it the most leveraged investment in the entire backlog relative to its modest effort estimate.

Within the Yamcs processing architecture, XTCE container definitions drive the entire telemetry demultiplexing and parameter extraction pipeline. The `GenericPacketPreprocessor` routes all incoming CCSDS packets to the `tm_realtime` stream, where the `StreamTmPacketProvider` matches each packet's APID against the XTCE container hierarchy to determine the correct decoding schema. By extending this hierarchy with a new `Env_Payload_Packet` container restricted to APID 200, this Epic proves that the existing data link infrastructure supports multi-payload ingestion without any transport-layer modifications — a critical architectural property for a platform targeting heterogeneous satellite constellations. The validation ticket (PAL-302) then establishes the repeatable acceptance test pattern — byte-level CCSDS packet injection via raw UDP sockets, real-time decoding verification, alarm triggering confirmation, and archive retrieval validation — that becomes the standard onboarding procedure for every future payload integration across the programme.

* **PAL-301:** XTCE Payload Telemetry Definition for Environmental Monitoring
* **PAL-302:** Multi-Packet Stream Configuration & Archive Validation

---

<div style="page-break-before: always;"></div>

### PAL-301: XTCE Payload Telemetry Definition for Environmental Monitoring

**Objective:** Extend the Yamcs Mission Database (`palantir.xml`) with a new telemetry packet definition for a simulated environmental monitoring payload, including parameter calibrations and alarm thresholds.

**Tech Stack:** XTCE 1.2 XML, Yamcs 5.12 MDB, Docker

**The 'Plain English' Goal:** Define what a new sensor's data looks like in the mission database so Yamcs can decode, display, and raise alarms on environmental monitoring telemetry — exactly how payload engineers onboard new instruments onto a spacecraft.

**What You Will Learn (Value Add):**
- XTCE (XML Telemetric and Command Exchange) schema authoring — the CCSDS-standard format used across ESA, NASA, and commercial missions
- Telemetry calibration (polynomial curves) and alarm threshold configuration
- Mission database engineering for multi-payload spacecraft

**Business Value / Real-World Impact:** Demonstrates multi-payload MDB extensibility — the architectural proof that the platform can onboard a new customer instrument in days rather than months. Directly enables the "instrument-agnostic GSaaS" value proposition that differentiates Palantir from vertically-integrated competitors locked to single-mission configurations, and is the #1 technical capability that Spaceport_SK mentors and downstream ESA BIC evaluators assess when evaluating a multi-mission ground segment proposal.

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

> **Risk Mitigation & Architect's Advice:** XTCE is a verbose XML schema with poor discoverability. Do not start from the XTCE 1.2 specification document — it is 200+ pages and will bury you. Instead, start by reading the existing `palantir.xml` line by line; it already contains a working `CCSDS_Packet_Base` → `Palantir_Nav_Packet` inheritance chain that is your exact template. Copy that pattern for APID 200, change the APID restriction value and parameter names, then incrementally add alarm ranges and the polynomial calibrator. Use an LLM to generate the `<PolynomialCalibrator>` XML for `Radiation_Dose` — the syntax is non-obvious but entirely mechanical. Validate each change by restarting Yamcs (`docker compose restart yamcs`) and checking the parameter list in the web UI. Do not try to write the entire XTCE extension in one pass; iterate one parameter at a time.

**Estimate:** 20 man-hours

**Dependencies:** None / Palantir Core System

**Execution Mode:** Pair-Programming (Team) — The XTCE 1.2 schema is verbose, poorly documented, and errors cause silent packet drops with no useful diagnostics; two sets of eyes significantly reduce the risk of subtle XML mistakes.

---

<div style="page-break-before: always;"></div>

### PAL-302: Multi-Packet Stream Configuration & Archive Validation

**Objective:** Configure the Yamcs instance to ingest, process, and archive the new environmental payload packet (APID 200) alongside the existing navigation telemetry, and validate end-to-end data flow from UDP ingestion through archive retrieval.

**Tech Stack:** Python 3, yamcs-client, socket (UDP), Docker, Yamcs 5.12

**The 'Plain English' Goal:** Prove the new sensor definition actually works end-to-end — by injecting test packets, watching Yamcs decode them, and verifying they are stored correctly in the archive. This is the validation step that separates a paper design from a flight-ready configuration.

**What You Will Learn (Value Add):**
- End-to-end integration validation methodology — the systematic approach used in spacecraft AIT (Assembly, Integration, Testing)
- CCSDS Space Packet crafting at the byte level using raw UDP sockets
- Yamcs archive query and verification workflows

**Business Value / Real-World Impact:** Establishes a repeatable, documented validation procedure for onboarding new telemetry sources — reducing customer integration risk from weeks of ad-hoc debugging to a standardized acceptance test. This is the operational maturity signal that SARIO Spaceport_SK evaluators and early-adopter satellite operators require before committing to a GSaaS contract, and directly prevents revenue-blocking integration delays during customer onboarding.

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

> **Risk Mitigation & Architect's Advice:** The hardest part of this ticket is getting the CCSDS packet bytes exactly right — a single off-by-one in the header will cause Yamcs to silently drop the packet with no useful error message. Use the existing `CcsdsTelemetrySender.java` in the core codebase as your byte-layout reference (read-only). Build your Python sender to emit a single hardcoded packet first, verify it appears in Yamcs, then parameterize it. If Yamcs receives the UDP datagram but does not decode the parameters, the APID or byte offsets in your XTCE do not match the packet — compare the hex dump of your sent bytes against the XTCE container definition field by field. Use `struct.pack('>HHH3f', ...)` in Python for big-endian encoding. An LLM can generate the `struct.pack` format string from the CCSDS header specification in seconds.

**Estimate:** 25 man-hours

**Dependencies:** PAL-301 (requires XTCE `Env_Payload_Packet` APID 200 container definition merged into `palantir.xml`)

**Execution Mode:** Pair-Programming (Team) — Byte-level CCSDS packet crafting is error-prone and benefits from pair debugging; one person encodes bytes in Python while the other verifies byte offsets against the XTCE container definition.

---

<div style="page-break-before: always;"></div>

## Epic 4: Enterprise Java Integration & Validation (Air-Gapped)

> **Architectural Constraint:** The Palantir Core codebase (`src/main/java/io/github/jakubt4/palantir/`) is **read-only** for the Java Integrator. All Java deliverables in this Epic are developed in **separate, independent projects** that interact with the Palantir stack exclusively through network interfaces (UDP, HTTP) and shared Docker infrastructure. No modifications to the core `pom.xml`, core source tree, or core Dockerfile are permitted.

This Epic exercises the full enterprise Java development lifecycle within the Yamcs ecosystem — from custom server-side algorithm plugins and independent microservice simulators to automated, CI-ready integration test suites. All deliverables are developed in strictly independent Maven projects with zero compile-time dependency on the Palantir Core codebase, interacting with the platform exclusively through UDP transport, HTTP APIs, and Docker Compose network interfaces. This air-gapped constraint is not merely an academic exercise: it validates the platform's extensibility architecture by proving that third-party developers, payload vendors, and integration partners can build, deploy, and test custom components against the Palantir stack without access to or modification of the core flight software — the exact integration model required for a commercially viable multi-tenant GSaaS offering.

The three tickets in this Epic span the critical extension points of a Yamcs-based ground segment: PAL-401 demonstrates server-side derived parameter computation via a custom Java algorithm plugin (quaternion-to-Euler attitude processing), proving the platform supports programmable in-pipeline data transformations that execute within the Yamcs processing chain. PAL-402 validates multi-subsystem telemetry ingestion by deploying an independent Spring Boot microservice that simulates an Earth Observation payload, streaming CCSDS packets with a distinct APID into the shared Yamcs instance alongside the core navigation telemetry. PAL-403 closes the quality assurance loop with a Testcontainers-based stress test suite that programmatically orchestrates the entire Docker Compose stack, injects 10,000 packets at maximum throughput, and validates end-to-end data integrity from UDP ingestion through Yamcs archive retrieval — establishing the automated, CI/CD-ready quality gate required for ECSS-Q-ST-80C software assurance compliance and institutional customer acceptance.

* **PAL-401:** Yamcs Custom Algorithm Plugin — Quaternion-to-Euler Attitude Processor
* **PAL-402:** Independent Payload Simulator Microservice — Earth Observation Sensor
* **PAL-403:** Enterprise QA & Integration Testing — Testcontainers Stress Validation

---

<div style="page-break-before: always;"></div>

### PAL-401: Yamcs Custom Algorithm Plugin — Quaternion-to-Euler Attitude Processor

**Objective:** Develop a custom Yamcs Algorithm/Derived Value plugin that subscribes to raw attitude quaternion telemetry parameters (q0, q1, q2, q3) within the Yamcs processing pipeline and outputs derived Euler angle parameters (Roll, Pitch, Yaw) in real time — enabling operators to monitor spacecraft orientation in human-readable form without modifying the core flight software.

**Tech Stack:** Java 21, Maven, Yamcs 5.12 Plugin API, JUnit 5, XTCE 1.2, Python 3 (test harness), Docker

**The 'Plain English' Goal:** Build a Yamcs plugin that automatically converts raw quaternion attitude data into human-readable roll/pitch/yaw angles — so operators see "the satellite is tilted 15 degrees" instead of four abstract numbers.

**What You Will Learn (Value Add):**
- Yamcs Java plugin development and deployment lifecycle — a rare and highly marketable skill in the European space sector
- Quaternion-to-Euler aerospace attitude mathematics (ZYX convention) including gimbal lock handling
- Server-side derived parameter computation inside a mission control processing pipeline

**Business Value / Real-World Impact:** Proves the platform supports custom server-side data processing plugins — enabling per-customer derived parameter computation without modifying the core system. This transforms the product from a static telemetry display into a programmable mission control platform capable of commanding premium pricing for value-added analytics services, and establishes the plugin ecosystem architecture that drives long-term platform stickiness and recurring revenue.

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

> **Risk Mitigation & Architect's Advice:** This ticket has two independent hard problems — do not try to solve them simultaneously. **Phase 1: The math.** Implement and unit-test the quaternion-to-Euler conversion as a plain Java class with zero Yamcs dependencies. Use the 5 reference pairs from the acceptance criteria as your test vectors (find canonical values on Wikipedia's "Conversion between quaternions and Euler angles" page, or ask an LLM to generate them). Get the gimbal lock edge case right here — not while debugging a Yamcs classloader issue. **Phase 2: The plugin.** Use the Yamcs 5.12 documentation's "Custom Algorithm" example as your starting scaffold. The Yamcs plugin API surface is small (`AbstractAlgorithmExecutor`) but poorly documented — feed the Yamcs source JAR's class listing into an LLM to find the exact interface signatures. The most common failure mode is a classpath/version mismatch between your plugin JAR and the Yamcs server runtime: pin your `yamcs-api` Maven dependency to exactly `5.12.2` and verify the plugin loads by checking the Yamcs startup log for your algorithm name before writing any processing logic.

**Estimate:** 60 man-hours

**Dependencies:** None / Palantir Core System (XTCE authoring benefits from the pattern established in PAL-301, but is not a hard blocker)

**Execution Mode:** Pair-Programming (Team) — Combines aerospace attitude mathematics, a poorly-documented Yamcs plugin API, and XTCE schema authoring; the highest cognitive load ticket in the backlog benefits from two perspectives tackling math and integration in parallel.

---

<div style="page-break-before: always;"></div>

### PAL-402: Independent Payload Simulator Microservice — Earth Observation Sensor

**Objective:** Build a standalone Spring Boot 3.x microservice that simulates an Earth Observation (EO) payload sensor suite, generating synthetic telemetry (multispectral band intensities, CCD temperature, shutter state) as CCSDS Space Packets and streaming them via UDP to the Palantir Yamcs instance — proving the system's ability to ingest telemetry from multiple independent spacecraft subsystems.

**Tech Stack:** Java 21, Spring Boot 3.x, Maven, CCSDS 133.0-B-1, Docker, Docker Compose, XTCE 1.2

**The 'Plain English' Goal:** Build a standalone microservice that pretends to be an Earth Observation camera on the satellite — generating realistic sensor data and streaming it to mission control, proving the system can handle multiple independent instrument feeds simultaneously.

**What You Will Learn (Value Add):**
- Spring Boot microservice development with binary CCSDS protocol encoding — bridging enterprise Java with space standards
- Multi-subsystem telemetry simulation with physics-based models (illumination, thermal, eclipse cycles)
- Docker Compose multi-service orchestration for distributed spacecraft ground systems

**Business Value / Real-World Impact:** Validates the platform's multi-instrument ingestion architecture with an independent subsystem — proving that third-party payload vendors can stream telemetry into the system without core modifications. This is the architectural prerequisite for operating as a multi-tenant GSaaS provider serving heterogeneous satellite constellations, and enables a "bring your own payload" integration model that eliminates vendor lock-in for customers.

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

> **Risk Mitigation & Architect's Advice:** Do not start with the physics model — start with the packet. Your first milestone is a Spring Boot app that sends a single hardcoded 26-byte CCSDS packet (6B header + 20B payload) to Yamcs and sees it decoded in the web UI. Read the core system's `CcsdsTelemetrySender.java` (read-only reference) to understand the exact CCSDS header byte layout and `DatagramSocket` usage pattern — then replicate it. Use an LLM to scaffold the Spring Boot project, the `@Scheduled` sender method, and the `ByteBuffer` encoding. The physics model (sinusoidal illumination, eclipse thermal transitions) is the easy part once the packet pipeline works — it is just `Math.sin()` with a 5400-second period. The Docker Compose integration is also straightforward: copy the `palantir-core` service block, change the image name and remove the port 10001 mapping. The most common failure mode is byte-order bugs: always use `ByteBuffer.allocate(26).order(ByteOrder.BIG_ENDIAN)`.

**Estimate:** 70 man-hours

**Dependencies:** None / Palantir Core System (XTCE authoring pattern from PAL-301 and CCSDS encoding pattern from PAL-302 are recommended prerequisites but not hard blockers)

**Execution Mode:** Individual Focus (Solo) — Spring Boot microservice development follows a well-established pattern with the core system's `CcsdsTelemetrySender.java` as a read-only reference; the CCSDS encoding and sinusoidal physics model are systematic solo work.

---

<div style="page-break-before: always;"></div>

### PAL-403: Enterprise QA & Integration Testing — Testcontainers Stress Validation

**Objective:** Implement an automated integration test suite using JUnit 5 and Testcontainers that programmatically spins up the full Palantir stack (Yamcs + Palantir Core Docker images), injects 10,000 CCSDS telemetry packets, and validates end-to-end data integrity from UDP ingestion through Yamcs archive retrieval — establishing a repeatable, CI-ready quality gate for the entire system.

**Tech Stack:** Java 21, Maven, JUnit 5, Testcontainers 2.x, AssertJ, yamcs-client (Java), Docker Compose

**The 'Plain English' Goal:** Build an automated test that spins up the entire Palantir system in Docker, fires 10,000 packets at it, and verifies nothing was lost or corrupted — the kind of quality gate that aerospace companies run before every software release.

**What You Will Learn (Value Add):**
- Testcontainers-based integration testing for containerized distributed systems — a high-demand enterprise Java skill
- UDP stress testing and packet loss analysis with quantified SLA metrics
- CI/CD quality gate implementation producing standard Surefire/Failsafe reports for Jenkins/GitHub Actions

**Business Value / Real-World Impact:** Delivers a CI-ready, automated quality gate that catches regression failures before deployment — the minimum viable QA infrastructure required for ESA software assurance (ECSS-Q-ST-80C) compliance. This is a non-negotiable prerequisite for any customer operating under institutional or regulatory software process standards, and directly reduces the cost of defect remediation by catching issues pre-release rather than in operational environments.

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

> **Risk Mitigation & Architect's Advice:** Testcontainers with Docker Compose is powerful but has sharp edges on startup timing. The #1 failure mode is the test sending packets before Yamcs has fully initialized its realtime processor — the health check (`GET /api/` returns 200) passes before the processor is ready to ingest. Add a secondary readiness check: poll `GET /api/processors/palantir/realtime` until it returns a 200 with `"state": "RUNNING"` before injecting any packets. For the stress test, do not try to validate all 10,000 packets individually — inject packets with known, sequential payload values (e.g., `latitude = packetIndex * 0.001f`) so you can validate completeness by checking the count and spot-checking a sample. Use the `maven-failsafe-plugin` (not `maven-surefire-plugin`) for integration tests — this is the standard convention and what CI systems expect. An LLM can generate the full `pom.xml` with Testcontainers dependencies and the `DockerComposeContainer` setup in one shot; start from that scaffold.

**Estimate:** 80 man-hours

**Dependencies:** None / Palantir Core System (the multi-APID demux test case benefits from PAL-301's XTCE MDB, but the primary 10,000-packet APID-100 stress test is independent)

**Execution Mode:** Pair-Programming (Team) — Testcontainers orchestration with Docker Compose has sharp timing edges around container startup races and processor readiness; pair debugging prevents hours of solo troubleshooting non-deterministic initialization failures.

---

<div style="page-break-before: always;"></div>

## Epic 5: Advanced Analytics & HPC Integration (Bonus Track)

> **Scope:** This Epic addresses two mission-critical capabilities absent from the current Palantir stack: (1) Space Situational Awareness (SSA) through conjunction assessment and automated collision avoidance, and (2) AI-driven anomaly detection via unsupervised learning on synthetic telemetry. All deliverables are standalone applications or scripts that interact with the Palantir stack through established interfaces (UDP, Yamcs API, XTCE MDB). The core system remains strictly read-only.

This Epic pushes the Palantir Digital Twin beyond passive telemetry monitoring into the domain of active Space Situational Awareness and AI-driven predictive health management — two capabilities that represent the highest-value, highest-margin services in the modern ground segment market. It delivers four tightly coupled components: a large-scale conjunction assessment engine screening the Palantir spacecraft's orbit against 30,000 catalogued debris objects from CelesTrak with Monte Carlo probability-of-collision estimation (PAL-501), a closed-loop collision avoidance commanding workflow with mandatory human-in-the-loop safety gates enforced at the XTCE level (PAL-502), a configurable synthetic telemetry generator with runtime anomaly injection for ML training data production (PAL-503), and an LSTM autoencoder anomaly detection pipeline exported to ONNX for portable, vendor-neutral inference deployment across any Yamcs-based ground segment (PAL-504).

Architecturally, this Epic demonstrates the platform's capacity to host compute-intensive, safety-critical automation workflows while maintaining strict separation between autonomous decision-making and human operator authority. The conjunction assessment batch application operates as an offline analytical service that posts threat assessments to the Yamcs event log, where the collision avoidance script monitors for actionable threats and queues maneuver commands — but the XTCE `TransmissionConstraint` with `ManualVerifier` ensures no thruster firing is released without explicit operator approval in the Yamcs commanding interface. This detect-recommend-approve-execute pattern is the industry-standard COLA workflow used by ESA's Space Safety Programme and commercial operators managing assets in congested LEO regimes. On the ML side, PAL-503 and PAL-504 establish a complete synthetic-first model development pipeline: deterministic telemetry generation with labeled anomaly injection, followed by unsupervised autoencoder training and ONNX export — enabling anomaly detection model iteration without dependency on proprietary customer flight data, and positioning the platform for a "Telemetry Intelligence" product tier that generates recurring SaaS revenue from predictive health insights.

* **PAL-501:** HPC Conjunction Assessment & Monte Carlo Simulation
* **PAL-502:** Automated Collision Avoidance Telecommanding
* **PAL-503:** Synthetic Telemetry Generator with Anomaly Injection
* **PAL-504:** Autoencoder Model Training & ONNX Export

---

<div style="page-break-before: always;"></div>

### PAL-501: HPC Conjunction Assessment & Monte Carlo Simulation

**Objective:** Build a standalone Java batch application that ingests the Palantir spacecraft's propagated state and cross-references it against 30,000 catalogued debris objects from CelesTrak, computing Time of Closest Approach (TCA) and Probability of Collision (Pc) via Monte Carlo sampling — providing the foundational SSA capability required for any operational LEO mission.

**Tech Stack:** Java 21, Maven, Orekit 12.2, yamcs-client (Java/REST API), CelesTrak GP API, JUnit 5

**The 'Plain English' Goal:** Screen our satellite's orbit against 30,000 pieces of tracked space debris to find potential collisions and compute the probability of each — the foundational capability behind every Space Situational Awareness program from ESA's Space Safety to the US 18th Space Defense Squadron.

**What You Will Learn (Value Add):**
- Orekit-based orbital propagation (SGP4) and conjunction geometry analysis — directly applicable to SSA roles at ESA, EUMETSAT, and commercial operators
- Monte Carlo probability estimation for collision risk assessment — the industry-standard Pc computation method
- CelesTrak debris catalog ingestion and large-scale batch processing with Java

**Business Value / Real-World Impact:** Provides the foundational Space Situational Awareness capability that transforms the platform from a passive telemetry display into an active safety system — directly addressing the #1 risk concern of every LEO operator and unlocking the high-margin SSA analytics market that ESA's Space Safety Programme is actively funding. A credible conjunction assessment capability is the single most compelling feature for Spaceport_SK Demo Day judges — and a strong differentiator for a future ESA BIC application.

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

> **Risk Mitigation & Architect's Advice:** This ticket is computationally heavy but architecturally simple — it is a batch pipeline with three stages (ingest → screen → monte carlo). Build and validate each stage independently before wiring them together. **Stage 1 (Ingest):** Parse the CelesTrak CSV into `TLE` objects using Orekit's `TLE` constructor. This is a one-liner per entry, but the CSV has formatting quirks — use an LLM to generate the CSV parser and handle the two-line TLE extraction from OMM/CSV format. Test with `--catalog-limit=10` first. **Stage 2 (Screen):** Propagate pairs using `TLEPropagator.selectExtrapolator(tle)` and compute Cartesian distance at each timestep. The 60-second step over 7 days is 10,080 steps per pair — at 500 objects this is ~5M propagation calls, which will take minutes, not hours. Use Java 21 Virtual Threads (`Executors.newVirtualThreadPerTaskExecutor()`) to parallelize across objects. **Stage 3 (Monte Carlo):** This is the most CPU-intensive part. Start with N=100 samples to validate the math, then scale to N=10,000 only after you trust the geometry. Seed the `Random` with a fixed value for reproducibility. Do not attempt HPC/Slurm deployment until the local `--catalog-limit=500` run produces a valid report.

**Estimate:** 100 man-hours

**Dependencies:** None / Palantir Core System (standalone Orekit batch application; Yamcs event posting is a final integration step)

**Execution Mode:** Pair-Programming (Team) — Large-scale orbital mechanics with Monte Carlo sampling demands both computational rigor and algorithmic correctness; pairing prevents subtle physics bugs in conjunction geometry from propagating silently through 10,000 simulation runs.

---

<div style="page-break-before: always;"></div>

### PAL-502: Automated Collision Avoidance Telecommanding

**Objective:** Extend the Yamcs Mission Database with a `FIRE_THRUSTER` telecommand and implement a closed-loop collision avoidance script that monitors conjunction assessment results, automatically queues a thruster firing command when Probability of Collision exceeds the 10^-4 threshold, and enforces mandatory human operator approval before command release — ensuring no autonomous maneuver is executed without explicit HMI confirmation.

**Tech Stack:** Python 3, yamcs-client, XTCE 1.2 XML, Yamcs REST API, Docker

**The 'Plain English' Goal:** Build the automated collision avoidance loop — when a dangerous conjunction is detected, the system queues a thruster firing command but absolutely refuses to execute it until a human operator clicks "APPROVE," ensuring no autonomous maneuver happens without explicit human oversight.

**What You Will Learn (Value Add):**
- Closed-loop autonomous commanding with mandatory human-in-the-loop safety gates — the design pattern behind every real COLA (Collision Avoidance) system
- XTCE telecommand definition with TransmissionConstraints and ManualVerifier stages
- Collision avoidance maneuver computation (delta-v budgeting) per ESA Space Debris Mitigation standards

**Business Value / Real-World Impact:** Implements the closed-loop collision avoidance workflow with mandatory human approval — the safety-critical automation pattern that prevents multi-million-dollar asset loss from orbital collisions while maintaining the operator-in-the-loop accountability required by ESA's Space Debris Mitigation guidelines and emerging EU space traffic management regulations. This capability alone can justify an operator's investment in the platform by demonstrating compliance with institutional safety mandates.

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
- **HMI Integration (PAL-102 extension):** The command panel from PAL-102 should display the queued `FIRE_THRUSTER` command with an "APPROVE" / "REJECT" button. This is a stretch integration — if PAL-102 is already complete, the Yamcs built-in web UI commanding page serves as the approval interface.
- **Safety constraint:** The script must **never** bypass the manual verification stage. If the Yamcs API allows direct command release without verification, the XTCE definition must enforce the constraint server-side.

**Acceptance Criteria:**
- [ ] `FIRE_THRUSTER` command defined in `palantir.xml` with all five arguments (opcode, delta_v_x/y/z, burn_duration_s). Visible in Yamcs commanding interface.
- [ ] `TransmissionConstraint` with `ManualVerifier` is configured. Command enters `QUEUED` state and does **not** auto-release. Verified by sending the command and confirming it waits for operator action.
- [ ] `collision_avoidance.py` polls Yamcs events, detects Pc > 10^-4 conjunctions, and issues a `FIRE_THRUSTER` command with computed delta-v values.
- [ ] The script logs all actions to stdout with timestamps: conjunction detected, command queued, awaiting approval, command approved/rejected.
- [ ] End-to-end test: inject a synthetic conjunction event with Pc = 5e-4 into Yamcs, observe the script queue a thruster command, manually approve it in the Yamcs UI, and verify the command reaches `SENT` status.
- [ ] The script never issues a command without the ManualVerifier constraint active. Attempting to disable the verifier in XTCE causes the script to abort with an error.
- [ ] Documentation (`COLA_PROCEDURE.md`) describes the full collision avoidance workflow: detection, maneuver computation, command queuing, operator approval, and execution verification.

> **Risk Mitigation & Architect's Advice:** This ticket has two distinct deliverables — treat them as sequential, not parallel. **Deliverable 1: XTCE command definition.** Get the `FIRE_THRUSTER` command working in the Yamcs web UI before writing a single line of Python. Define the MetaCommand in `palantir.xml`, restart Yamcs, and manually send the command from the Yamcs built-in commanding page. If the ManualVerifier does not gate the command as expected, the XTCE is wrong — fix it before proceeding. The `<TransmissionConstraint>` and `<ManualVerifier>` XTCE syntax is obscure; use an LLM with the Yamcs XTCE examples to generate the XML. **Deliverable 2: Python COLA script.** The script is straightforward REST API polling + POST commanding. Start with a hardcoded test: inject a fake event via the Yamcs REST API, then have the script detect it and queue a command. The delta-v formula is intentionally simplified — do not over-engineer the maneuver computation. The critical design requirement is the safety gate: verify the command stays in `QUEUED` until manual approval both in your script test and by inspecting the Yamcs UI.

**Estimate:** 80 man-hours

**Dependencies:** PAL-501 (requires conjunction events posted to the Yamcs event log to trigger the COLA detection loop)

**Execution Mode:** Individual Focus (Solo) — Python scripting with REST API polling and commanding is a focused, sequential task; the safety-critical ManualVerifier constraint is enforced server-side by XTCE, so the script logic is straightforward.

---

<div style="page-break-before: always;"></div>

### PAL-503: Synthetic Telemetry Generator with Anomaly Injection

**Objective:** Build a standalone Java application that generates continuous synthetic telemetry streams representing a nominal 90-minute LEO orbit (sinusoidal latitude, longitude, and altitude profiles) via CCSDS/UDP, with runtime-configurable CLI triggers to inject realistic thermal runaway and voltage drop anomalies — providing a controlled, repeatable dataset for training and validating anomaly detection models.

**Tech Stack:** Java 21, Maven, CCSDS 133.0-B-1, XTCE 1.2 XML, Docker

**The 'Plain English' Goal:** Build a synthetic satellite that generates realistic telemetry and lets you inject failures on demand — thermal runaway, voltage drops, tumbling — creating the labeled training data that an AI model needs to learn the difference between "healthy" and "failing."

**What You Will Learn (Value Add):**
- Deterministic physical simulation modeling (orbital mechanics, thermal environment, power subsystem, ADCS)
- CCSDS Space Packet encoding from scratch — building the binary protocol layer that flies on real missions
- Anomaly injection and labeled dataset generation — the critical first step in any ML-for-space pipeline

**Business Value / Real-World Impact:** Eliminates the dependency on live spacecraft data for ML model development and operator training — enabling the platform to train anomaly detection models and onboard new operators at zero marginal cost. This is a prerequisite for scaling AI-driven monitoring services across a growing customer base without requiring access to each customer's proprietary flight data, and directly enables a "synthetic-first" development workflow that compresses model iteration cycles from months to days.

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

> **Risk Mitigation & Architect's Advice:** This is architecturally the simplest ticket in Epic 5 — it is a loop that computes `Math.sin()`, packs bytes, and sends UDP. The complexity is in doing it cleanly. **Start with the nominal model only.** Get all six parameters generating at 1 Hz with correct CCSDS encoding and visible in Yamcs before touching anomaly injection. The CCSDS encoding is identical to PAL-402's pattern; reuse or adapt that code. **Anomaly injection is a state machine.** Define an enum `AnomalyState { NOMINAL, THERMAL_RUNAWAY, VOLTAGE_DROP, TUMBLE }` and a `Scanner` thread reading stdin. Each anomaly type modifies one parameter's generation function. Do not try to support simultaneous anomalies in the first pass — the `NOMINAL` reset makes this a single-active-anomaly model, which is simpler and sufficient for the ML training data. The `--record` CSV writer is just a `BufferedWriter` appending one line per tick — implement it last, after the Yamcs integration works. Use an LLM to generate the sinusoidal and exponential decay formulas if the math is unfamiliar.

**Estimate:** 60 man-hours

**Dependencies:** None / Palantir Core System (XTCE authoring pattern from PAL-301 is a recommended prerequisite; CCSDS encoding follows the same byte-level conventions as the core system)

**Execution Mode:** Individual Focus (Solo) — Deterministic signal generation with a state-machine anomaly injection model is a well-scoped task with clear, testable outputs at each stage (nominal model → anomaly injection → CSV recording).

---

<div style="page-break-before: always;"></div>

### PAL-504: Autoencoder Model Training & ONNX Export

**Objective:** Develop a Python/PyTorch training pipeline that ingests the synthetic telemetry dataset produced by PAL-503, trains an unsupervised autoencoder to learn the nominal operational envelope, exports the trained model to ONNX format for portable inference, and validates that the model reliably flags all injected anomaly types with a reconstruction error exceeding a calibrated threshold — establishing the foundation for real-time ML-based anomaly detection within the Yamcs processing pipeline.

**Tech Stack:** Python 3, PyTorch, ONNX, ONNXRuntime, pandas, numpy, matplotlib

**The 'Plain English' Goal:** Train a neural network to learn what healthy satellite telemetry looks like, then export it to a portable format (ONNX) so it can flag anomalies the moment they occur — the same approach satellite operators use to catch failures before they become emergencies.

**What You Will Learn (Value Add):**
- LSTM Autoencoder architecture design for time-series anomaly detection — directly applicable to predictive maintenance in aerospace and industrial IoT
- ONNX model export for cross-platform portable inference — the industry standard for deploying ML models outside Python
- Unsupervised learning threshold calibration, evaluation metrics (TPR, FPR), and reproducible ML experiment reporting

**Business Value / Real-World Impact:** Delivers a portable, vendor-neutral anomaly detection model (ONNX) embeddable into any Yamcs instance — monetizing raw telemetry streams as predictive health insights. Enables a "Telemetry Intelligence" product tier that generates recurring SaaS revenue from AI-driven failure prediction, the highest-margin service in the ground segment value chain, and positions the platform as a data-driven operations provider rather than a commodity telemetry relay.

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

> **Risk Mitigation & Architect's Advice:** Do not start with the LSTM. **Step 1: Data pipeline.** Write the dataset loader, sliding window generator, and train/val split first. Verify the windowed tensors have the correct shape (`[batch, 60, 6]`) using a simple print statement. This plumbing is 40% of the work. **Step 2: Baseline model.** Train a simple dense autoencoder (Linear layers only, no LSTM) first. If this can separate NOMINAL from THERMAL_RUNAWAY on the reconstruction error plot, your data pipeline is correct and the task is feasible. Then upgrade to the LSTM architecture for temporal sensitivity. Use an LLM to generate the PyTorch `nn.Module` class — the LSTM autoencoder architecture is well-known and LLMs produce correct implementations reliably. **Step 3: ONNX export.** This is the most common failure point. PyTorch's `torch.onnx.export()` requires a dummy input tensor with the correct shape and `dynamic_axes` configuration for the batch dimension. If the ONNX export fails on the LSTM (hidden state handling is tricky), simplify by exporting only the forward pass without exposing internal LSTM states. The `onnxruntime` validation is a 5-line script — do not skip it, as silent numerical drift between PyTorch and ONNX is common. Focus on the ONNX export correctness, not the math — the autoencoder will learn if the data pipeline is right.

**Estimate:** 70 man-hours

**Dependencies:** PAL-503 (requires the `synth_telemetry.csv` dataset with labeled anomaly windows for training and validation)

**Execution Mode:** Pair-Programming (Team) — LSTM autoencoder architecture design, PyTorch-to-ONNX export edge cases (hidden state handling), and threshold calibration span multiple domains; pairing accelerates debugging of numerical drift between PyTorch and ONNXRuntime inference.

---

<div style="page-break-before: always;"></div>

## Integration Plan (12 Sprints x 2 Weeks — 6 Months)

### Team Structure — Agile Pull-Based Model

The team consists of two cross-functional students (**Student 1** and **Student 2**) operating under an Agile/Kanban pull-based assignment model. Tickets are not pre-assigned to a specific student. Instead, work is pulled dynamically from the prioritized backlog based on current team capacity, individual learning goals, and dependency readiness. Either student may pick up any ticket from any Epic, subject to prerequisite completion and core team guidance during sprint planning.

**Pair programming** is encouraged for high-complexity tickets (PAL-401, PAL-501, PAL-503) and for cross-domain knowledge transfer — e.g., a student with stronger frontend skills pairs with one focusing on backend/systems work to share context during XTCE or Yamcs plugin development. The sprint tables below suggest a default task routing based on typical skill affinities, but these are recommendations, not mandates. The project lead adjusts assignments at each sprint planning session based on velocity, blockers, and growth objectives.

| Domain | Typical Affinity | Scope |
|--------|-----------------|-------|
| HMI & Operator UX | Frontend-leaning student | Epic 1 (PAL-101, PAL-102) |
| Flight Dynamics & Analytics | Python / data-leaning student | Epic 2 (PAL-201, PAL-202) |
| Mission Database & Systems Integration | Either student | Epic 3 (PAL-301, PAL-302) |
| Enterprise Java & Validation | Java-leaning student | Epic 4 (PAL-401, PAL-402, PAL-403) |
| Advanced Analytics & HPC | Either student (pair recommended) | Epic 5 (PAL-501, PAL-502, PAL-503, PAL-504) |

---

### Phase 1: Foundation (Sprints 1-3, Weeks 1-6)

#### Sprint 1 — Environment Bootstrap & First Contact (Weeks 1-2)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | Dev environment operational for both students: `docker compose up` runs the full stack. Yamcs Web UI accessible. | Core team provides Docker images |
| P0 | CesiumJS project scaffolded (`npm init`, Cesium viewer renders empty globe). First successful WebSocket connection to Yamcs parameter subscription endpoint. | Docker stack running |
| P0 | Python virtualenv with `yamcs-client`, `pandas`, `matplotlib` installed. First successful `archive.list_parameter_values()` call returns live data. Familiarization with XTCE schema structure by reading existing `palantir.xml`. | Docker stack running, minimum 1 hour of archived telemetry |

**Sprint 1 Gate:** Both students demonstrate bidirectional data flow — one shows a WebSocket message logged to browser console, the other shows a pandas DataFrame printed from Yamcs archive. Students may pair-programme on environment setup.

#### Sprint 2 — Core Ticket Development Begins (Weeks 3-4)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P1 | **PAL-101 (In Progress):** Spacecraft position renders on CesiumJS globe updating at 1 Hz. Basic point entity tracking live lat/lon/alt. Ground track polyline prototype (last 10 minutes). | WebSocket subscription from Sprint 1 |
| P1 | **PAL-201 (In Progress):** CSV export functional with correct columns. `ground_track.png` renders with coastline overlay. CLI argument parsing (`--start`, `--stop`) implemented. | Yamcs archive access from Sprint 1 |

**Sprint 2 Gate:** Team shows a moving dot on the globe and a generated ground track plot. Either student may own either deliverable — pull based on interest and capacity.

#### Sprint 3 — First Tickets Code-Complete (Weeks 5-6)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-101 (Complete):** Full ~93-minute ground track history, altitude overlay panel, auto-reconnect logic. Code review and merge. | None |
| P0 | **PAL-201 (Complete):** All plots, statistics, and CSV export finalized. | None |
| P1 | **PAL-301 (Started):** XTCE schema draft for `Env_Payload_Packet` (APID 200) with initial parameter definitions. | Core team review of XTCE draft |

**Sprint 3 Gate:** PAL-101 and PAL-201 are code-complete and demonstrated. PAL-301 XTCE draft submitted for architectural review.

---

### Phase 2: Feature Expansion (Sprints 4-6, Weeks 7-12)

#### Sprint 4 — Second Wave Tickets (Weeks 7-8)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P1 | **PAL-102 (In Progress):** Command panel UI scaffolded. "Send PING" and "Send REBOOT_OBC" buttons issue REST API calls. Basic response handling. | Yamcs commanding API |
| P1 | **PAL-301 (Complete):** XTCE with all four environmental parameters, alarms, and `Radiation_Dose` polynomial calibration validated. Parameters visible in Yamcs UI. | None |
| P2 | **PAL-302 (Started):** `send_env_packet.py` test sender script development begins. | PAL-301 merged to MDB |

**Sprint 4 Gate:** Team demonstrates a command sent from browser and visible in Yamcs command history, and APID 200 parameters decoded in Yamcs UI.

#### Sprint 5 — Feature Completion & Cross-Integration (Weeks 9-10)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-102 (Complete):** Command history log table with auto-refresh, error handling, full acceptance criteria met. | None |
| P0 | **PAL-302 (Complete):** End-to-end validation, alarm triggering, archive retrieval confirmed. `validation_report.md` written. | PAL-301 deployed in Yamcs |
| P1 | **PAL-202 (Started):** AOS/LOS geometric model implementation begins. | Archived telemetry available |

**Sprint 5 Gate:** Epic 1 complete (PAL-101 + PAL-102). Epic 3 complete (PAL-301 + PAL-302). Cross-integration test: HMI displays environmental parameters defined by the XTCE work.

#### Sprint 6 — Analytics Completion & Epic 4 Kickoff (Weeks 11-12)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-202 (Complete):** Pass prediction validated against 6+ hours of telemetry, report and visibility timeline generated. | Archived telemetry from Sprint 5 |
| P1 | **PAL-401 (Started):** Yamcs plugin Maven project scaffolded, quaternion math implemented and unit-tested in isolation. | None |
| P2 | **Buffer / Polish:** Refine PAL-101/102 based on user feedback. Research CesiumJS 3D model loading and satellite FOV cone visualization (stretch goal). | None |

**Sprint 6 Gate:** Epic 2 complete (PAL-201 + PAL-202). Standalone quaternion-to-Euler unit tests passing. Mid-project review with core team.

---

### Phase 3: Enterprise Java & SSA (Sprints 7-9, Weeks 13-18)

#### Sprint 7 — Yamcs Plugin & Conjunction Assessment Kickoff (Weeks 13-14)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-401 (In Progress):** Plugin JAR builds and loads into Yamcs without errors. XTCE `Attitude_Packet` (APID 300) defined. `send_attitude_packet.py` test harness transmits known quaternions. First derived Euler values appear in Yamcs UI. | Yamcs Docker image modification |
| P1 | **PAL-501 (Started):** Conjunction assessment Maven project scaffolded. CelesTrak catalog parser ingests 500-object test subset. | None |
| P2 | **Stretch / Integration:** Integrate PAL-202 AOS/LOS data into HMI — display next pass countdown on CesiumJS overlay. Support XTCE extensions for APID 300. | PAL-202 output data |

**Sprint 7 Gate:** Derived Euler parameters visible in Yamcs UI. CelesTrak parser produces 500 valid TLE objects.

#### Sprint 8 — Plugin Hardening & Screening Pass (Weeks 15-16)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-401 (Complete):** All 5 reference quaternion pairs validated including gimbal lock edge case. Norm violation event logging confirmed. Unit test coverage > 90%. | None |
| P1 | **PAL-501 (In Progress):** Screening pass functional against 500-object subset. Close approaches (< 10 km) flagged. Monte Carlo Pc estimation prototype running for a single conjunction. | None |
| P2 | **Stretch / Integration:** Add APID 300 attitude parameters to HMI display (Roll/Pitch/Yaw gauges or numerical readout). Begin research on conjunction visualization overlay for CesiumJS. | PAL-401 Euler parameters available in Yamcs |

**Sprint 8 Gate:** PAL-401 code-complete. Screening pass identifies at least one close approach with a preliminary Pc value.

#### Sprint 9 — Conjunction Assessment Complete & Simulator Kickoff (Weeks 17-18)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-501 (Complete):** Full 500-object local validation passes. Monte Carlo Pc reproducible with seeded RNG. `conjunction_report.json` generated. Top-10 events posted to Yamcs. Unit tests > 80% coverage. | None |
| P1 | **PAL-402 (Started):** EO Payload Simulator Spring Boot project scaffolded. CCSDS encoder for APID 400 implemented. | None |
| P2 | **Stretch / Integration:** HMI consolidated view — single dashboard showing orbital track (APID 100), environmental health (APID 200), attitude (APID 300). Add conjunction alert panel reading Yamcs events from PAL-501. | XTCE for APID 300, PAL-501 events |

**Sprint 9 Gate:** PAL-501 code-complete (local mode). Conjunction events visible in Yamcs Event log. EO simulator generates a raw CCSDS packet in a unit test.

---

### Phase 4: Simulators & Collision Avoidance (Sprints 10-11, Weeks 19-22)

#### Sprint 10 — EO Simulator & COLA Command Definition (Weeks 19-20)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-402 (Complete):** Simulator generates physically plausible EO telemetry at 1 Hz. Sinusoidal band model and eclipse thermal model operational. Docker Compose integration complete. XTCE for APID 400 merged. README documented. | None |
| P1 | **PAL-502 (Started):** `FIRE_THRUSTER` command defined in XTCE with `ManualVerifier` constraint. `collision_avoidance.py` script scaffolded. | PAL-501 conjunction events in Yamcs |
| P2 | **Stretch / Integration:** Add EO payload status panel to HMI (APID 400 parameters). Add `FIRE_THRUSTER` button to command panel (PAL-102 extension) with APPROVE/REJECT workflow. | XTCE for APID 400 and FIRE_THRUSTER |

**Sprint 10 Gate:** PAL-402 code-complete. Five telemetry sources streaming into Yamcs (APID 100, 200, 300, 400, 500). `FIRE_THRUSTER` command visible in Yamcs commanding interface with manual approval gate.

#### Sprint 11 — Collision Avoidance Complete & Synth Generator (Weeks 21-22)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-502 (Complete):** Closed-loop script detects Pc > 10^-4, queues FIRE_THRUSTER, waits for operator approval. End-to-end test with synthetic conjunction event passes. `COLA_PROCEDURE.md` documented. | PAL-501 events, FIRE_THRUSTER in XTCE |
| P1 | **PAL-503 (Started):** Synth telemetry generator scaffolded. Nominal sinusoidal orbital model transmitting APID 500 packets. | None |
| P2 | **Cross-integration testing:** Execute full operator scenarios — orbit visualization, commanding (including FIRE_THRUSTER approval flow), alarm monitoring across all APIDs. File bug reports for integration issues. | PAL-502 command workflow |

**Sprint 11 Gate:** PAL-502 code-complete. Full COLA loop demonstrated: conjunction detected → command queued → operator approves in UI → command released. Synth generator streaming nominal telemetry.

---

### Phase 5: AI/ML & QA (Sprint 12, Weeks 23-24)

#### Sprint 12 — Anomaly Detection, Integration Testing & Delivery (Weeks 23-24)

| Priority | Backlog Item | Dependencies |
|----------|-------------|--------------|
| P0 | **PAL-503 (Complete):** All four anomaly injection types functional. `--record` produces labeled CSV. XTCE for APID 500 with alarms merged. | None |
| P0 | **PAL-504 (Complete):** Autoencoder trained on NOMINAL data, ONNX exported, detection rate > 95% per anomaly type, FPR < 2%. All artifacts generated. | PAL-503 dataset |
| P0 | **PAL-403 (Complete):** Testcontainers stress test (10,000 packets) passes. Malformed packet resilience and multi-APID demux validated. `stress_test_report.json` generated. CI-compatible reports produced. | Docker images |
| P1 | Final HMI polish across all panels. Screen-capture demo of full operator workflow recorded. | All HMI features stable |
| P0 | Unified `INTEGRATION_REPORT.md` delivered. Joint live demo: end-to-end Palantir Digital Twin with all subsystems — orbital visualization, telecommanding, COLA workflow, environmental/attitude/EO monitoring, conjunction assessment, anomaly detection pipeline, and automated QA. Project handoff to core team. | All tickets closed |

**Sprint 12 Gate:** End-to-end demonstration of the complete Palantir Digital Twin: orbital visualization, commanding, environmental monitoring, attitude processing, EO payload simulation, conjunction assessment, collision avoidance, synthetic telemetry, ML anomaly detection, and automated QA validation. All 13 tickets closed. Project deliverables archived and handed off.

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

> **Note on ticket assignment:** Tickets are pulled from the prioritized backlog by either student based on capacity, interest, and learning goals. The sprint plan above suggests a default priority ordering and natural grouping, but any ticket may be claimed by either student or pair-programmed. The project lead adjusts priorities at each sprint planning session based on velocity, blockers, and growth objectives.

---

<div style="page-break-before: always;"></div>

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
