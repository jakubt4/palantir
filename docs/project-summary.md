# Project Palantir — Plan Summary

*Generated 2026-05-02. Source-of-truth references: `FEATURES.md`, `CLAUDE.md`, `pom.xml`, `pyproject.toml`, `package.json`, git history. Every numeric claim below has been verified against one of these.*

## What it is

Palantir is a Digital Twin ground segment proof-of-concept that bridges astrodynamics simulation with operational mission control. A Spring Boot service (Orekit SGP4 propagator) generates real-time spacecraft state at 1 Hz, encodes it into CCSDS 133.0-B-2 Space Packets with CCSDS 301.0-B-4 CUC time codes in the Secondary Header[^cuc-revision], ships them over UDP to a Yamcs 5.12.2 mission-control instance, and exposes a browser-based operator HMI (CesiumJS globe + telecommand panel) plus a Python analytics tier (telemetry export, AOS/LOS pass prediction). Built solo as a learning vehicle for the space sector, with a long-term direction toward **Ground Segment as a Service (GSaaS)** — a multi-tenant cloud platform where smallsat operators rent mission-control capabilities instead of building their own ops room.

[^cuc-revision]: CCSDS 301.0-B-4 *Time Code Formats* is the revision I cite based on prior knowledge (Nov 2010 publication, no -B-5 known to me). If a more recent revision exists, the project's standards anchor should be re-checked at PAL-105 maintenance time.

Brand backronym (per `memory/project_brand_acronym.md`, my own choice): **PALANTIR** = *Predictive Astrodynamics · Live Awareness · Networked Telemetry · Intelligent Response*.

## Why I'm building it

Three reasons in priority order:

1. **Personal space-sector entry.** I'm a senior Java engineer with deep enterprise experience (self-reported: prior MD-SAL v2 work on OpenDaylight as solo implementer). Palantir is my route into space domain knowledge — orbital mechanics, CCSDS, XTCE, Yamcs internals, flight dynamics, conjunction screening, the ECSS standards stack. Built solo, on my own time, with no external pressure or commercial deadline.
2. **GSaaS product trajectory (untested hypothesis, partially-researched market analysis — May 2026).**
   Market reality I checked via web research (sources at end of file): the GSaaS market is fragmented and growing. Analysts cite GSaaS specifically at $3.8B (2025) trending to $14.2B (2034) at 15.8% CAGR; the broader ground-segment market is $106B per Novaspace. **No single player dominates** — L3Harris led the broader ground-station market in 2024 with only 5% global share; recent entrants (AWS Ground Station 2019, Azure Orbital 2021, Viasat RTE 2026, Contec from Korea, ATLAS Australia 2026) confirm the category is fluid, not consolidated.

   The market splits into layers I had collapsed in my earlier framing:

   - **Antenna-tier self-serve IS well-served.** ATLAS Space Operations' *Freedom GSaaS* markets explicit "self-service scheduling via API or console" with a "bring your satellite, first-come-first-served" model. AWS Ground Station and Azure Orbital cover the same layer with global hyperscaler coverage. Leaf Space, KSAT, RBC Signals, Contec are antenna-network-focused with growing ops-adjacent services.
   - **MCS-tier (full mission control software) is enterprise-sales-dominated.** Real players exist: **Spaceit** (Tallinn, Estonia — markets *MCSAAS* for smallsats <500 kg), **D-Orbit Aurora** (Italy — Mission Control as a Service via Aurora platform), **Bright Ascension HELIX Ops** (Scotland — operations software with scheduling + open APIs), **Kratos OpenSpace** (US — deployed by SSC Space Go for LEO). All use *"Book a demo"* / consultative sales; none surface credit-card-sign-up SaaS pricing publicly; none explicitly market multi-tenant architecture or EU sovereign data residency as a primary differentiator.
   - **EU sovereign cloud is well-served at the infrastructure layer** (AWS European Sovereign Cloud in Brandenburg, Oracle EU Sovereign Cloud, Microsoft / Google equivalents) but I found no satellite-specific MCS that markets EU data residency as a feature.

   The narrower hypothesis worth validating before any commercial commitment: **"There is room for an MCS-tier self-serve SaaS (sign up, configure, run — not 'Book a demo, six-month integration') with explicit EU sovereign deployment, targeted at small operators who don't have ops staff to run their own Yamcs but need more than antenna-only scheduling."** Whether enough such operators exist, what they'd pay, and whether *AWS Ground Station + a self-hosted Yamcs* already covers their actual needs is unknown to me; customer interviews are the only way to find out. None of this would happen before Demo Day. Designing the PoC *as if* it might one day ship is a forcing function for clean architecture regardless of whether the commercial bet is on or off.

   **Orbit regimes supported.** Palantir is architecturally orbit-agnostic — Orekit, CCSDS Space Packet, XTCE, and Yamcs all work the same for LEO, MEO, GEO, HEO, and (Orekit can do) deep-space and lunar trajectories. Operational defaults today (default ISS TLE, PAL-202's `min_elevation_deg = 5°`, Rule 30's `R : C : T = 1 : 10 : 100` covariance ratio) are LEO-tuned because LEO is where the demo runs and where most live debris sits, but switching the digital twin to a GEO comm satellite, a Molniya HEO, or a lunar transfer orbit is a config change, not a code change. The covariance ratio specifically would need re-tuning for non-LEO regimes (Rule 30's ratio is from LEO Space Surveillance Network practice).
3. **Demo Day target — 2026-09-29.** Concrete deliverable presentable at the Spaceport_SK incubator and (aspirationally) ESA BIC: an end-to-end **automated collision-avoidance loop with manual operator approval** (FEATURES.md §4 bundle = PAL-501 + PAL-502 + Phase 3b). Conjunction screening flags an upcoming close approach → system computes evasion manoeuvre → operator approves → THRUST_MANEUVER command propagates and the simulated spacecraft visibly avoids collision.

## What's done — Phase 0 baseline + Phase A complete

### Phase 0 — Baseline (operational, in `master`)

| Capability | Implementation |
|---|---|
| SGP4/SDP4 orbit propagation @ 1 Hz | `OrbitPropagationService` — Orekit 12.2 `TLEPropagator` under `@Scheduled(fixedRate=1000)` |
| Hot-swappable TLE ingestion | `TleIngestionController` + `AtomicReference<TLEPropagator>` lock-free swap |
| TEME → ITRF → Geodetic (WGS-84) | Orekit `OneAxisEllipsoid` + `IERSConventions.IERS_2010` |
| CCSDS 133.0-B-2 Space Packet encoding (24 B w/ CUC time) | `CcsdsTelemetrySender` — Primary Header (6 B) + Secondary Header CUC (6 B) + payload (12 B, three IEEE 754 float32) |
| UDP downlink + uplink | `palantir-yamcs:10000` TM, `palantir-core:10001` TC |
| Yamcs instance `palantir` | UdpTm/Tc data links, `CfsPacketPreprocessor` (TAI epoch), XTCE MDB split across `baseline.xml` + `features/commands.xml` |
| Containerised stack | Docker Compose (Yamcs + palantir-core, persistent named volume, healthcheck) |

### Phase A — Operator HMI & Analytics Foundation (7/7 ✅ done)

| Ticket | Done | Capability |
|---|---|---|
| PAL-201 | 2026-04-23 | Python CLI: archive query → CSV + altitude PNG + ground-track PNG (cartopy, **antimeridian-aware**); units sourced from XTCE MDB |
| PAL-202 | 2026-04-27 | AOS/LOS pass prediction (Haversine γ + atan2 elevation); validated on 35-hour archive producing 10 passes over Banská Bystrica |
| PAL-203 | 2026-04-27 | YAML ground-station registry with override precedence (flag > config-name > config-default > built-in) |
| PAL-101 | 2026-04-27 | CesiumJS browser HMI: live ground track via Yamcs WebSocket, `SampledPositionProperty`, 93-min trail, status pills |
| PAL-102 | 2026-04-27 | Telecommand panel: PING / REBOOT_OBC, command history table, 5 s polling, color-coded status pills |
| PAL-104 | 2026-04-27 | Automated TLE refresh from CelesTrak GP catalog (6 h cadence); reduced TLE drift from 71 days to ~13.5 hours measured live |
| PAL-105 | 2026-04-28 | CCSDS Secondary Header with CUC time code (4 B coarse + 2 B fine, TAI 1958-01-01 epoch); `generation_time` matches propagator tick within ±1 ms (display precision; underlying CUC fine resolution is ~15 µs) |

Project also restructured (2026-04-29) — Java Maven module relocated under `palantir-core/` so each tier opens cleanly in its own IDE: Eclipse for `palantir-core/`, Theia for `tools/`, plain editor for `yamcs/`. Five sibling modules will sit alongside as Phase 0.1 lands.

## What's underway — Phase 0.1 Mission Orchestration Platform (6 tickets queued)

Platform tier built parallel to Phase A — designed to host multiple spacecraft, multiple missions, multiple tenants. Decision to build now (vs defer to Phase G) informed by my prior MD-SAL v2 / OpenDaylight orchestrator experience; the schema-design risk that would normally argue "wait for the rule of three" doesn't apply when the engineer has already shipped a comparable orchestrator.

| Ticket | Scope |
|---|---|
| PAL-001 | Mission model schema — YAML + JSON Schema validating `Mission`, `Spacecraft`, `Constellation`, `GroundStation`, debris-source references, security keys |
| PAL-003 | `palantir-core` parameterisation — APID, NORAD ID, Spacecraft ID, Mission ID, HMAC key all env-var driven |
| PAL-004 | Secured TC envelope — Spacecraft ID byte + 14-bit sequence counter + HMAC-SHA256 trailer (CCSDS 232.0 *TC Space Data Link Protocol* + CCSDS 355.0-B-2 *SDLS*, simplified) |
| PAL-005 | Debris simulator — CelesTrak debris catalogue ingest (tens of thousands of objects; ~25 000+ per ticket DoD) + lazy SGP4 + REST query API |
| PAL-006 | CDM ingestion — Space-Track CDM API (primary, free non-commercial registration) + CelesTrak SOCRATES JSON (fallback) → 6×6 RTN covariance per CCSDS 508.0-B-1 for Pc computation |
| PAL-002 | Orchestrator skeleton — Spring Boot service spawns per-mission Yamcs containers + per-spacecraft simulator containers via Docker API; REST + WebSocket events |

Design philosophy: borrow MD-SAL's *philosophy* (declarative model = source of truth, runtime reconciles, REST API parallel to model) but **not** its primitives (no NETCONF, no datastore abstraction, no two-phase commit, no OSGi/Karaf, no YANG). Spring Boot REST + YAML model + JSON Schema validation. Satellite-domain nouns first-class.

## What's ahead

| Phase | Scope | Status |
|---|---|---|
| **B** — Mission Database Expansion | PAL-301 (XTCE env-payload, APID 200, alarm thresholds), PAL-302 (multi-packet stream validation). Architectural gatekeeper for Phases C–E. | backlog |
| **C** — Java/Yamcs Extensions | PAL-401 (Yamcs algorithm plugin: quaternion → Euler), PAL-402 (independent EO payload simulator), PAL-403 (Testcontainers stress validation against ECSS-Q-ST-80C Rev.2 §6.2.4) | backlog |
| **D** — Collision Avoidance | **PAL-501** (Conjunction screening with Monte Carlo Pc — uses PAL-005 ephemeris + PAL-006 CDMs, Rule-30-conformant RTN covariance), **PAL-502** (closed-loop COLA with manual operator gate via Yamcs command queue significance + minLevel), **Phase 3b** (THRUST_MANEUVER physics wiring — propagator switches from SGP4 to NumericalPropagator post-burn). **Demo Day bundle.** | backlog |
| **E** — ML Telemetry Anomaly Detection | PAL-503 (synthetic generator + anomaly injection state machine, seeded RNG per Rule 27), PAL-504 (LSTM autoencoder training, ONNX export) | backlog |
| **F** — Deferred concepts | Predictive Orbital Shadowing, Virtual Thread matrix scaling, Yamcs 5.13 upgrade, ESA BIC technical readiness package | unscheduled |
| **G** — Productization | Auth, multi-tenancy, billing, tenant onboarding, customer API gateway, frontend, key management (HashiCorp Vault upgrade path from PAL-004's env-var PoC) | unscheduled (post-Demo-Day) |

## Architecture in three layers (current)

1. **Physics engine** (`palantir-core/`, port 8080) — Spring Boot 3.2.5, Java 21 + Virtual Threads (enabled in `application.yaml`), Orekit 12.2. SGP4/SDP4 propagation, CCSDS encoding, telecommand reception. Will become parameterisable + spawnable as N replicas under Phase 0.1.
2. **Mission control** (`yamcs/`, port 8090) — Yamcs 5.12.2 Docker container based on `yamcs/example-simulation:5.12.2`. UdpTm/Tc data links, `CfsPacketPreprocessor` with TAI epoch, XTCE MDB, REST + WebSocket APIs, persistent archive. Will be one-instance-per-mission under Phase 0.1.
3. **Tools** (`tools/`) — Python CLI for analytics (`palantir-analytics`, Python 3.12+, pandas + matplotlib + cartopy), CesiumJS browser HMI (`palantir-hmi`, CesiumJS 1.123 + Vite 5.4). Stays single-instance; queries the right Yamcs URL per mission via `--yamcs-instance` and qualified path.

Phase 0.1 will add three new sibling modules: `palantir-orchestrator/` (Spring Boot), `palantir-debris-sim/` (Spring Boot, Orekit), `palantir-cdm-ingest/` (Spring Boot).

## Standards anchored

CCSDS 133.0-B-2 (Space Packet, June 2020) · CCSDS 301.0-B-4 (Time Code Formats[^cuc-revision]) · CCSDS 232.0 (TC Space Data Link Protocol[^tc-revision]) · CCSDS 355.0-B-2 (SDLS) · CCSDS 508.0-B-1 (CDM, June 2013) · XTCE 1.2 (OMG SpaceSystemV1.2.xsd, 2018-02-04) · IERS-2010 conventions · WGS-84 (`a = 6378137.0 m`, `1/f = 298.257223563`) · IEEE 754-1985 · ECSS-Q-ST-80C Rev.2 (30 April 2025).

[^tc-revision]: CCSDS 232.0 *TC Space Data Link Protocol* — I am citing the standard but not its revision letter, because I'm not confident which revision is current as of writing. The specific revision should be verified at PAL-004 implementation time before the security envelope is wired.

## Engineering ground rules (CLAUDE.md §I — Space Operations Strict Protocols)

- **Time Domain Determinism (Rule 26)** — `AbsoluteDate` + explicit TimeScale; flight TM packets carry embedded time code; ground reads from packet bytes, not local clock. PAL-105 closed this for the digital twin via Yamcs `CfsPacketPreprocessor`. Sim-mode exception explicitly carved out for the propagation scheduler in `OrbitPropagationService` (Spring Boot IS the spacecraft, JVM clock IS the spacecraft clock).
- **Deterministic Randomness (Rule 27)** — seeded PRNG from a known-stable library (Java: `org.hipparchus.random.Well19937a`; Python: `numpy.random.default_rng(seed)` plus framework seeders). Never `Math.random()`, bare `new java.util.Random()`, `numpy.random.seed()`. The seed used for a run MUST be logged for byte-for-byte audit reproducibility.
- **Sequence Integrity over Async (Rule 28)** — TM downlink path single-threaded per APID; no Virtual Threads / `CompletableFuture` / `@Async` / executor submits in the sequence-counter→socket section. Async permitted on uplink path and non-CCSDS background work.
- **Frozen Toolchain (Rule 29)** — no library version bumps without explicit authorisation; CVEs surfaced for decision (CVE-ID + severity + affected component + brief description), never silently patched.
- **Astrodynamic Covariance (Rule 30)** — RTN frame, canonical `R : C : T ≈ 1 : 10 : 100` for tracked LEO objects, frame-bound (`Σ_ECI = R · Σ_RTN · Rᵀ`).

## Notes on this summary

- "Done" status and dates pulled from the ✅ badges in `FEATURES.md` and cross-checked against git commit history. Every PAL-1xx ticket date matches both sources.
- "What's underway" reflects FEATURES.md §0.1 as committed in `259cabf` and updated in `bfc977a`. No tickets there have been started yet — they are queued, not in progress.
- Live verification numbers (10 passes / 35 h, ±1 ms generation gap, 71 → 13.5 day TLE drift reduction) are from smoke-test commit messages (`67fe089`, `5dde4ad`, `f012ca1` respectively) — verifiable from git log + linked logs preserved in those commits.
- Future tickets PAL-301, 401–403, 501–504, Phase 3b are scoped in FEATURES.md but no implementation work has started; treat their descriptions in this document as roadmap intent, not as features that exist.
- This summary itself is **not** committed to the repository by default — it lives at `docs/project-summary.md` like `docs/spaceport-kickoff-intro.md` (untracked, regenerable). If you want it tracked, it's a one-line `git add` away.

## Sources for the GSaaS market analysis (Reason 2)

Web-research-validated 2026-05-02. URLs included so the claim is re-verifiable later (note: live web pages drift; capture via Wayback Machine if you want a frozen snapshot).

- ATLAS Space Operations — *The State Of The Ground Segment And Ground Software As A Service*: https://atlasspace.com/the-state-of-the-ground-segment-and-ground-software-as-a-service/
- Spaceit MCS service page: https://spaceit.eu/services/mcs/
- Spaceit MCS on Orbital Transports SmallSat Catalog: https://catalog.orbitaltransports.com/spaceit-mission-control-as-a-service/
- D-Orbit Aurora Mission Control Software: https://www.dorbit.space/aurora
- Bright Ascension HELIX Ops: https://brightascension.com/products/helix-ops/
- Kratos OpenSpace platform: https://www.kratosspace.com/virtual-ground/platform
- SpaceNews — *$106B Ground Segment Market Enters Service-Driven Era*: https://spacenews.com/106b-ground-segment-market-enters-service-driven-era/
- Novaspace — *$106B Ground Segment Market Enters Service-Driven Era*: https://nova.space/press-release/106b-ground-segment-market-enters-service-driven-era/
- dataintelo — *Ground Segment as a Service Market Research Report 2034*: https://dataintelo.com/report/ground-segment-as-a-service-market
- AWS European Sovereign Cloud: https://aws.amazon.com/compliance/europe-digital-sovereignty/
- Oracle EU Sovereign Cloud: https://www.oracle.com/cloud/eu-sovereign-cloud/
- New Space Economy — *The Ground Segment Revolution: How As-a-Service Models are Connecting Space to Earth* (2025-11-06): https://newspaceeconomy.ca/2025/11/06/the-ground-segment-revolution-how-as-a-service-models-are-connecting-space-to-earth/
- Viasat — *How Ground-Segment-as-a-Service supports next-generation satellite communication*: https://www.viasat.com/perspectives/government/2024/how-ground-segment-as-a-service-supports-next-generation-satellite-communication/
