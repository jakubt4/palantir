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

## 🛠️ TODO / Roadmap (In Progress)

### 🎮 Phase 3: Telecommanding (Uplink) [PRIORITY: HIGH]
**Objective:** Implement a bidirectional simulation loop, allowing operators to control the satellite state from the Yamcs Ground Station via binary commands.

#### 1. Ground Segment Configuration (Yamcs)
* [ ] Configure `UdpTcDataLink` in `yamcs.yaml` targeting `palantir-core:10001`.
* [ ] Define **MetaCommands** and **CommandContainers** in the XTCE database (`palantir.xml`).
* [ ] Define operational commands:
    * `CMD_REBOOT_OBC` (OpCode: `0x01`)
    * `CMD_ADJUST_ORBIT` (OpCode: `0x02`, Arg: `DeltaV_m_s`)
    * `CMD_SET_TM_RATE` (OpCode: `0x03`, Arg: `RateEnum`)

#### 2. Flight Software Simulation (`palantir-core`)
* [ ] Implement `UdpCommandReceiver` listening on port `10001`.
* [ ] Implement a **CCSDS Telecommand Parser** (Validation of APID: 200 & Sequence Flags).
* [ ] Create a `CommandExecutorService` to map OpCodes to Java logic.

#### 3. Simulation Feedback Loop (Physics Reaction)
* [ ] **Thrust Maneuver:** executing `CMD_ADJUST_ORBIT` must dynamically modify the `TLEPropagator` state (altering the orbit in real-time).
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