<!--
  Palantir — Spaceport_SK 2026 Application Deck
  
  8-slide application deck for the 5th cohort of the Spaceport_SK
  incubation programme, operated by the Slovak Space Office (SARIO)
  in cooperation with the Slovak Ministry of Education. Submitted by
  e-mail to spaceoffice@sario.sk together with project topic and team
  composition in the e-mail body. This deck stands alone as the project
  introduction and contains no team or topic metadata.
-->

# PALANTIR

**An open-source digital twin bridging astrodynamics and mission control.**

April 2026

<div style="page-break-before: always;"></div>

# Where this comes from

**12 years mission-critical Java systems engineering**
Telco SDN  ·  FinTech transactional systems

**Currently shipping:** distributed booking platform with protocol translation
and a spatial data normalisation engine  *(Coderama, 2022 – current)*

**MSc thesis** (UMB, 2017): C++/OpenMP implementation of a peer-reviewed heavy-ion event-classification method — translating published science into working code

---

*I stopped reading about space and started building.*

<div style="page-break-before: always;"></div>

# Why the ground segment

| TELCO SDN  *(where I ship)*                | SPACE GROUND SEGMENT                     |
|--------------------------------------------|------------------------------------------|
| **YANG**  (RFC 7950)                       | **XTCE**  (CCSDS 660.0-B-2)              |
| **NETCONF / RESTCONF**  (RFC 6241 / 8040)  | **CCSDS Space Packet**  (CCSDS 133.0-B-1)|
| **OpenDaylight**  (Apache Karaf)           | **Yamcs**  (OSGi-style services)         |
| Shipped to 99.999% Telco SLAs              | Mission-critical TM/TC loops             |

*Seven of those twelve years in the left column made the right column look familiar.*

<div style="page-break-before: always;"></div>

# What it is

**Three components, one Docker Compose command. Fully open-source stack.**

![Palantir architecture — bidirectional CCSDS/UDP between palantir-core and Yamcs](architecture-diagram.png)

<div style="page-break-before: always;"></div>

# Where it is today

**Not a slide deck. A working system you can run today.**

```
$ docker compose up --build
```

**Within a minute of a warm start:**

- Default ISS TLE loads automatically
- Yamcs Web UI on `http://localhost:8090`
- Three parameters streaming at 1 Hz: `/Palantir/Latitude`  ·  `/Palantir/Longitude`  ·  `/Palantir/Altitude`
- Persistent archive on Docker volume — survives restart

**Engineering quality:**

- JUnit 5 / Mockito / AssertJ — tests verifying TLE ingestion, orbital propagation plausibility, and Spring context integrity
- JaCoCo coverage report
- Javadoc on every main class

---

*Active development since February 2026  ·  MIT license*

<div style="page-break-before: always;"></div>

# What you'll see

| ![Yamcs Web UI — live Palantir parameters](yamcs-live-params.png) | ![palantir-core CCSDS DEBUG log](ccsds-debug-log.png) |
|:---:|:---:|
| **Live parameters at 21:24:31 UTC** | **Raw CCSDS Space Packets, 1 Hz cadence** |

Standards-compliant CCSDS Space Packets — the same binary protocol used by ESA missions — decoded in real time by Yamcs at 1 Hz cadence. Three orbital parameters (latitude, longitude, altitude) streamed live from SGP4 propagation.

<div style="page-break-before: always;"></div>

# What I want to build

**The Demo Day target:**
one end-to-end Automated Collision Avoidance flow,
live on stage from a clean `$ docker compose up --build`.
Sequential build: screening first, commanding second, physics reaction last — each layer testable independently.

**1.  CONJUNCTION SCREENING**

- Standalone Orekit batch job  ·  CelesTrak GP catalog (OMM XML)
- 7-day propagation window  ·  Monte Carlo Probability of Collision
- Top events posted to the Yamcs event log

**2.  OPERATOR-APPROVED COMMANDING**

- `FireThruster` XTCE telecommand
- Critical-significance command queue
- No autonomous burn ever flies

**3.  VISIBLE PHYSICS REACTION**

- Operator clicks APPROVE  →  impulsive Δv applied to the orbit
- Ground track visibly shifts within one orbital period
- *A closed loop, made visible.*

**If time allows beyond the September critical path:** synthetic telemetry generation for anomaly detection experimentation.

<div style="page-break-before: always;"></div>

# What I do not know yet

I built Palantir to test whether twelve years of mission-critical systems engineering can translate into the space sector. **That is precisely why I am applying.**

**Two paths I would be happy with, either or both:**

- **Path A — own project trajectory.** If Palantir proves viable during the programme, continue it as an independent initiative beyond September. If the traction is real, explore ESA BIC Slovakia or similar incubation as a longer-term step.
- **Path B — sector transition.** Use the six months as a structured entry into the European space industry. Build the network, understand how operators and integrators hire, and position myself for a role in mission-critical space software.

**Open questions either path would help me answer:**

- What are the real bottlenecks in European ground segment operations today? Where does the current toolchain break or force manual workarounds?
- Where does the open-source stack (Yamcs, Orekit, OpenC3) stop short of production needs — and where is institutional modernisation blocked by budget, qualification, or risk aversion?

**What I want to learn from the programme:**

I have not done market research yet. I built a working system — whether it has real commercial value as an open-source ground segment product is an open question I want to answer during the programme, with mentor guidance and Advisory Board feedback. If the answer is yes, ESA BIC Slovakia is the natural next step.

**My commitments in return:**

- **Working prototype available from day one.** Live demo at every Advisory Board checkpoint, on the reviewer's laptop.
- **All artefacts open-sourced under MIT** — no IP friction, no surprises.
- **Genuinely open to mentor guidance.** The Automated Collision Avoidance flow is my current plan for Demo Day, but I will adapt direction if Advisory Board feedback points to something stronger.
