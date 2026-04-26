# [RETIRED] Project Palantir: Core Features & Architectural Roadmap

> **This document is retired.** It has been superseded by `FEATURES.md`. The "Killer Features" narrative below (Predictive Orbital Shadowing, Virtual Thread Matrix, Closed-Loop Command Verification) is preserved for the ESA BIC pitch storyline but is **not** the active engineering roadmap. See `FEATURES.md` §6 (Phase F) for the deferred-future treatment of these items, and §8 for technical corrections.

---

# Project Palantir: Core Features & Architectural Roadmap

This document defines the core features and architectural objectives of Project Palantir. The system is engineered as an **Orbital Digital Twin**, enforcing strict High-Availability (HA) standards derived from the Telco/FinTech sectors. It is designed for Ground Segment as a Service (GSaaS) deployment within the commercial NewSpace ecosystem and satellite mega-constellations.

## 1. Current Core Architecture (Baseline)

* **Physics-Telemetry Fusion (Orekit + Yamcs):** Autonomous, real-time integration of the physical propagation engine (Orekit 12+) with the Mission Control and telemetry archive database (Yamcs 5.12+).
* **Real-Time Orbital Propagation:** Asynchronous computation of TLE (Two-Line Elements) data, executing coordinate transformations (SGP4 -> TEME -> ITRF -> Geodetic [Lat/Lon/Alt]) within a deterministic 1Hz execution loop.
* **CCSDS 133.0-B-1 Protocol Bridge:** Custom, byte-buffer level implementation of the Space Packet Protocol. The system generates strictly compliant telemetry packets (APID 100) and streams them via UDP into the Yamcs realtime processor and archive.
* **Asynchronous Uplink (Telecommand):** Ingestion and processing of TC instructions from Yamcs (e.g., `PING`, `REBOOT_OBC`) via a dedicated UDP DataLink, utilizing a Java 21 `VirtualThread` dispatcher for non-blocking I/O operations.
* **Cloud-Native & Containerized:** The entire operational stack (Palantir Core + Yamcs MDB) is fully containerized (`docker-compose`), ensuring immediate deployment readiness for cloud environments such as AWS Ground Station or Azure Space.

---

## 2. "Killer Features" for ESA BIC (Development Roadmap)

The following architectural enhancements define Palantir's strategic advantage over legacy academic and open-source aerospace solutions.

### Feature A: Predictive Orbital Shadowing (The True Digital Twin)
Legacy systems merely visualize received data. Palantir introduces Predictive Maintenance directly into the orbital operations loop.
* **Mechanics:** The Orekit engine continuously simulates the theoretical ideal state of the spacecraft (physics, attitude, position). This model is cross-referenced in real-time against actual telemetry ingested by Yamcs.
* **Anomaly Detection:** If the Δ (deviation) between the simulated and physical state exceeds a pre-defined threshold, the system autonomously triggers a `ParameterAlarm`. Operators receive critical warnings minutes before a catastrophic hardware or trajectory failure occurs.

### Feature B: Massive GSaaS Scaling (Virtual Thread Matrix)
Solving the "Data Deluge" bottleneck for small-satellite mega-constellations.
* **Mechanics:** Transitioning the concurrent execution model from native OS threads to Java 21 Virtual Threads. Instead of blocking CPU resources at each I/O socket, the system allocates thousands of lightweight threads with zero context-switching overhead.
* **Impact:** The capability to concurrently propagate and process high-frequency telemetry for 10,000+ satellites on a single standard commercial off-the-shelf (COTS) server, ensuring extreme network throughput without CPU throttling.

### Feature C: Closed-Loop Command Verification (FinTech-Grade Reliability)
Eliminating the critical vulnerability of "Blind Commanding"—a mandatory requirement for ESA and institutional space agencies.
* **Mechanics:** Implementation of a bidirectional, cryptographic handshake protocol within the `MetaCommandSet`. When Yamcs dispatches a critical command (e.g., `REBOOT_OBC`), the Palantir core processes the instruction and expects an asynchronous confirmation telemetry packet (ACK) from the OBC.
* **Impact:** A command is never marked as `COMPLETED` in the Mission Database until a sequence-verified acknowledgment is received directly from the hardware, ensuring absolute Cyber-Resilience.

---

## 3. Domain Expert Extensions (Payload & HMI Integration)

To establish a comprehensive GSaaS offering, Palantir Core will expose interfaces for the following modules, to be developed by specialized mission integrators (Spaceport_SK team):

* **HMI & Mission Control Dashboard:** Development of zero-latency operator synoptics. Integration of WebSockets, the Yamcs Web API, and CesiumJS for real-time 3D visualization of orbital tracks and subsystem health.
* **Flight Dynamics Analytics:** Python-based data mining (`yamcs-client`, `pandas`) against the Yamcs MDB. Automated generation of Acquisition of Signal / Loss of Signal (AOS/LOS) reports and algorithmic conversion of raw sensor data (e.g., for Earth Observation missions).
* **Payload Dictionary (XTCE Mapping):** Expansion of the current `palantir.xml` Mission Database to include complex telemetry definitions, calibration curves, and critical alarm thresholds for specific environmental, optical, or SAR payloads.