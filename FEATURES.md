# 🚀 Project Palantir: Features & Roadmap

This document serves as the high-level tracking log for the **Palantir Digital Twin** platform. It outlines the simulation capabilities, implemented standards, and the active development roadmap.

## ✅ Implemented (Done)

### 🛰️ Phase 1: Orbital Physics Core
* **Orekit Integration:** Full integration of the Orekit astrodynamics library (Java 21) for high-precision physics.
* **SGP4/SDP4 Propagation:** Real-time orbit propagation based on standard Two-Line Element (TLE) sets.
* **Coordinate Transformation:** Real-time conversion from Inertial Frames (ECI/J2000) to Geodetic Coordinates (WGS84 Latitude/Longitude/Altitude).

### 📡 Phase 2: CCSDS Telemetry Downlink
* **CCSDS Space Packet Encoding:** Binary serialization of telemetry data adhering to **CCSDS 133.0-B-1** (Space Packet Protocol).
    * *Structure:* 6-byte Primary Header + 12-byte Payload (IEEE 754 Big Endian Floats).
* **UDP Transport Layer:** High-speed packet streaming on port `10000` (Simulating S-Band Downlink).
* **Yamcs Ground Segment Integration:**
    * Configuration of `UdpTmDataLink` for packet ingestion.
    * **XTCE (MDB) Definition:** XML-based mapping of binary streams to engineering values.
    * Real-time parameter visualization (Orbit Track & Altitude profiles).

---

## ✅ Implemented (Done)

### 🎮 Phase 3: Telecommanding (Uplink)
**Objective:** Bidirectional simulation loop — operators control the satellite from Yamcs via binary commands over UDP.

#### 1. Ground Segment Configuration (Yamcs)
* [x] Configure `UdpTcDataLink` in `yamcs.palantir.yaml` targeting `palantir-core:10001`.
* [x] Configure `StreamTcCommandReleaser` in `processor.yaml` to release commands to `tc_realtime` stream.
* [x] Define **MetaCommands** and **CommandContainers** in the XTCE database (`palantir.xml`):
    * `PING` (OpCode: `0x01`) — No-op heartbeat
    * `REBOOT_OBC` (OpCode: `0x02`) — Simulated OBC reboot

#### 2. Flight Software Simulation (`palantir-core`)
* [x] Implement `UdpCommandReceiver` listening on UDP port `10001` (Virtual Thread executor).
* [x] Parse 1-byte opcode from incoming datagrams and dispatch commands (0x01=PING, 0x02=REBOOT_OBC, 0x03=SET_TRANSMIT_POWER).
* [x] Docker Compose exposes UDP 10001 and uses `service_started` dependency to ensure DNS resolution works for `UdpTcDataLink`.

---

## 🛠️ TODO / Roadmap (In Progress)

### 🎮 Phase 3b: Advanced Telecommanding
**Objective:** Extend the telecommand subsystem with richer command handling and simulation feedback.

#### 1. Command Handling Enhancements
* [ ] Implement a **CCSDS Telecommand Parser** with full header validation (APID, Sequence Flags).
* [ ] Create a `CommandExecutorService` to decouple opcode dispatch from `UdpCommandReceiver`.
* [ ] Define additional XTCE commands (SET_TRANSMIT_POWER is handled in code but not yet in XTCE MDB).

#### 2. Simulation Feedback Loop (Physics Reaction)
* [ ] **Thrust Maneuver:** executing a delta-V command must dynamically modify the propagator state (altering the orbit in real-time).
* [ ] **Fault Injection:** Implement a "Chaos Monkey" command to simulate component failure (e.g., Battery Voltage drop to 0V).

---

## 🔮 Future Concepts (Backlog)

### 🌍 Ground Station Visibility & Pass Prediction
* Calculation of AOS (Acquisition of Signal) and LOS (Loss of Signal) events relative to specific ground stations (e.g., ESTEC/Noordwijk).
* Simulation of signal loss when the satellite is below the horizon.

### 🔐 Security (CCSDS SDLS)
* Implementation of **Space Data Link Security (SDLS)** protocol.
* HMAC authentication for Telecommand packets to prevent unauthorized control.

### ☁️ Cloud Native Deployment
* Helm Chart for deploying the full stack (Core + Yamcs) to Kubernetes.
* Horizontal scaling of the Telemetry Processor for multi-satellite constellations.