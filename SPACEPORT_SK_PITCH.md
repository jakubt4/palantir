# Palantir × Spaceport_SK — Research a Pitch Plán

> Pracovný dokument k prihláške do 5. ročníka inkubačného programu **Spaceport_SK** (2026), spravovaného Slovenskou vesmírnou kanceláriou (SARIO) v spolupráci s MŠVVaM SR.

---

## 1. Executive Summary

**Palantir** je open-source **Ground Segment as a Service (GSaaS) Digital Twin** — most medzi astrodynamickou simuláciou (Orekit/SGP4) a operačným mission control systémom (Yamcs) cez štandardný protokol CCSDS 133.0-B-1. V čase podania prihlášky mám **funkčný prototyp s obojsmerným TM/TC linkom, Docker Compose stackom a plnou XTCE decoding pipeline** — teda presne to, čo Spaceport_SK od účastníka očakáva („dobrý nápad stačí, ale prototyp je plus").

Pre 6-mesačný program mám pripravený **pedagogicky štruktúrovaný backlog (`FEATURE-v2-ext.md`)** 13 ticketov (PAL-101 až PAL-504) pokrývajúcich HMI, flight dynamics, multi-payload XTCE, Yamcs Java pluginy, HPC conjunction assessment a ML anomaly detection — čo dokazuje schopnosť škálovať projekt cez integráciu študentských tímov (kandidáti sú z technických vysokých škôl, čo program explicitne podporuje).

**Cieľ účasti:** Validácia produktu, prepojenie na slovenský space ekosystém, príprava na **ESA BIC Slovakia** (program to explicitne menuje ako validačnú cestu pred BIC vstupom), prístup k Advisory Boardu (ESA, EUSPA, YESS, Satlantis) a finančná cena z Demo Day (29. 9. 2026).

---

## 2. Spaceport_SK — čo potrebujeme vedieť pre prihlášku

### Program v kocke
| Atribút | Hodnota |
|---|---|
| Gestor | Slovak Space Office @ SARIO + MŠVVaM SR |
| Formát | Hybridný inkubátor (mentoring + online workshopy) |
| Dĺžka | Apríl – september 2026 (6 mesiacov, 3 fázy) |
| Cieľová skupina | Early-stage startupy, **študentské tímy** (technické/vedecké/biznis odbory), jednotlivci s nápadom alebo prototypom |
| Výstup | Demo Day s pitchami pred expertnou porotou, finančné ceny, pipeline do ESA BIC |

### Kľúčové dátumy
| Dátum | Míľnik |
|---|---|
| **20. 4. 2026** | **Deadline prihlášok** (spaceoffice@sario.sk) |
| 28. 4. 2026 | Kick-off |
| Apríl – máj | Fáza 1: Validácia (Business Canvas, technology validation, go-to-market) |
| Jún | Fáza 2: Investment Readiness (pitch deck, VC Q&A, ESA BIC overview) |
| September | Fáza 3: Finalizácia + Final Advisory Board review |
| **29. 9. 2026** | **Demo Day** (súťaž o ceny pred porotou) |

### Prihláška vyžaduje
1. **Téma projektu**
2. **Zloženie tímu**
3. **Stručný popis projektu**

### Čo program dáva účastníkom
- Mentoring od skúsených profesionálov zo space sektora
- Prístup do slovenského space ekosystému (firmy, výskum, investori)
- Medzinárodný feedback cez Advisory Board (ESA, EUSPA, YESS, Satlantis)
- **Príprava na ESA BIC Slovakia** (oficiálna „validácia pred vstupom")
- Finančná cena pre víťazov Demo Day

### Focus areas programu (kde sa Palantir hodí)
Program explicitne menuje nasledovné priority — **tučne** sú tie, kde Palantir priamo sedí:
- **Satelitné operácie a diaľkový prieskum Zeme** ← **direct fit**
- Earth observation a environmentálny monitoring
- AI a machine vision aplikácie ← *adjacent (roadmap)*
- **Využitie satelitných dát a downstream služby** ← **direct fit (GSaaS)**
- Heat shield technológie
- **Monitorovanie a mitigácia vesmírneho odpadu** ← **adjacent (PAL-501/502 collision avoidance)**
- Propulzné systémy pre small-sate
- **Autonómne systémy** ← **adjacent (automated COLA loop)**
- Geoinformačné riešenia

### Bývalí víťazi — signál toho, čo porota oceňuje
| Ročník | Víťaz | Téma |
|---|---|---|
| 2026 (R4) | **Aerostacks** | Predikcia lavín cez remote sensing + AI |
| 2024 (R3) | **Datafrost Space** | Marketplace pre satellite data users ↔ providers |
| 2023 (R2) | **Straton** | Autonómny glider pre recovery stratosférických prób |
| 2022 (R1) | **SpaceScavengers** | Multi-agent systémy pre správu space debris |

**Vzor:** porota oceňuje riešenia, ktoré (a) majú zrozumiteľný commercial use case, (b) využívajú moderný stack (AI, data platformy), (c) riešia reálny problém viditeľný z vesmíru alebo smerom k vesmíru. **Palantir sa do tejto trajektórie elegantne zaraďuje ako „open-source ground segment pre NewSpace mega-konstelácie".**

---

## 3. Prečo Palantir patrí do Spaceport_SK

### Strategic fit
1. **Má prototyp, nie iba slide deck.** Program to neočakáva ako podmienku — ale je to diferenciátor. Demo s reálnym telemetry streamom za 60 sekúnd je silnejšie ako akýkoľvek pitch.
2. **Adresuje reálnu komerčnú medzeru.** Legacy ground segment (SCOS-2000, EPOCH) je proprietárny a drahý; Yamcs sám o sebe je len core — Palantir pridáva physics-driven digital twin vrstvu a GSaaS-ready deployment model.
3. **Mega-konstelácie = data deluge problem.** Spring Boot 3.2 + Java 21 Virtual Threads umožňujú konkurentne propagovať telemetry pre 10 000+ satelitov na jednom COTS serveri. To je priamo „killer feature C" z `FEATURES_v2.md`.
4. **Cesta k ESA BIC je explicitná.** Program sa sám označuje ako „validácia pred ESA BIC". Palantir je presne profil projektu pre BIC (technický base + komercializačný potenciál v GSaaS).
5. **Student-ready scale-up plán.** 13-ticket backlog v `FEATURE-v2-ext.md` dokazuje, že projekt vie absorbovať študentské/juniorské zdroje a generovať deployable artefakty — to je presne typ škálovania, na ktoré Spaceport_SK pozerá.

### Odlíšenie od predchádzajúcich víťazov
- Datafrost Space rieši **marketplace** pre satellite dáta → Palantir rieši **infraštruktúru**, ktorá tie dáta spracuje a distribuuje do mission control.
- SpaceScavengers rieši **debris management** na úrovni agentov → Palantir poskytuje **ground segment**, kde takéto agenty bežia, vrátane XTCE command definície pre `FIRE_THRUSTER` (PAL-502).
- Palantir nekonkuruje — **komplementuje** existujúce víťazné projekty ako ground infrastructure layer.

---

## 4. Čo už mám ako prototyp (DEMO-ready stav)

Všetko beží v jednom `docker compose up --build`. To je **kľúčová vec pre pitch** — audit mentorov musí vedieť spustiť demo lokálne do 5 minút.

### Implementované (verifikované na master branche)

#### Physics & Orbital Mechanics
- **Orekit 12.2 SGP4/SDP4 propagátor** s real-time loadingom `orekit-data.zip` (leap seconds, EOP, planetárne efemeridy).
- **Transformácia súradníc** TEME → ITRF → WGS84 geodetic cez `OneAxisEllipsoid` a IERS-2010 konvencie.
- **Hot-swap TLE cez REST API** (`POST /api/orbit/tle`) s `AtomicReference<TLEPropagator>` — zero-downtime výmena propagátora.
- Default ISS TLE sa načíta pri štarte → telemetry tečie okamžite po boote, žiadne manuálne kroky.

#### CCSDS Downlink (TM)
- **Plná CCSDS 133.0-B-1 Space Packet implementácia** na úrovni `ByteBuffer` (6 B primary header + 12 B payload).
- APID 100, 14-bit sequence counter s `AtomicInteger`, standalone grouping flags.
- **IEEE 754 big-endian float encoding** pre lat/lon/alt (3 × 4 B).
- **UDP transport** na port 10000 (simuluje S-Band downlink).
- **DEBUG-level hex dump logging** vysielaných paketov (recent commit c5729b1).

#### Yamcs Mission Control (Docker)
- Custom Yamcs 5.12.2 image (`yamcs/example-simulation` base) s inštanciou `palantir`.
- **`UdpTmDataLink`** na port 10000 s `GenericPacketPreprocessor` (local generation time, no CRC).
- **XTCE Mission Database** (`mdb/palantir.xml`):
  - Abstraktný `CCSDS_Packet_Base` container (6 B header).
  - `Palantir_Nav_Packet` (APID=100 restriction, 3 × IEEE 754 float).
  - `CommandMetaData` s PING (0x01) a REBOOT_OBC (0x02) ako uint8 opcode.
- **Realtime processor** s `StreamTmPacketProvider` + `StreamTcCommandReleaser` + `StreamParameterProvider`.
- **Archive services** (`XtceTmRecorder`, `ParameterRecorder`, `CommandHistoryRecorder`) s perzistentným Docker volume (`palantir_yamcs_data`).
- Web UI na porte 8090, CORS enabled.

#### Telecommand Uplink (TC) — bidirekčný loop
- **`UdpTcDataLink`** v Yamcs posiela TC pakety na `palantir-core:10001` cez Docker DNS.
- **`UdpCommandReceiver`** v Spring Boot počúva na UDP 10001 v Java 21 Virtual Thread executori.
- **Opcode dispatch:** 0x01=PING, 0x02=REBOOT_OBC, 0x03=SET_TRANSMIT_POWER (posledný zatiaľ iba v kóde, nie v XTCE).
- Operátor klikne tlačidlo vo Yamcs web UI → paket doletí do Spring Boot cez 2 hop-y za <10 ms.

#### Engineering Quality
- **Java 21** s `spring.threads.virtual.enabled=true` (Project Loom).
- **Dockerfile multi-stage** (Maven + JDK build → JRE runtime).
- **`depends_on: service_started`** (nie `service_healthy`) — premyslené riešenie DNS race condition medzi Yamcs UdpTcDataLink initom a palantir-core join do Docker siete.
- **JUnit 5 + Mockito test suite** (6 testov: `@WebMvcTest` pre controller, `@SpringBootTest` pre propagation service, plus integration test pre full context load).
- **JaCoCo coverage reporting** (`target/site/jacoco/index.html`).
- **Kompletná dokumentácia**: README.md, ARCHITECTURE.md, FEATURES.md, FLOW.md (byte-by-byte walkthrough CCSDS encodingu), FEATURES_v2.md (killer features), FEATURE-v2-ext.md (student backlog).
- **Javadoc naprieč hlavnými triedami** (recent commit 4f9d189).

### Čo to všetko znamená pre pitch
Prototyp je **production-grade PoC**, nie akademický skript. Compiluje sa, behá, má testy, je dokumentovaný, má real-world protokol (CCSDS) a real-world mission control systém (Yamcs — používa ho ESA, EUMETSAT, DLR). To je presne to, čo porota potrebuje vidieť v prvých 60 sekundách.

---

## 5. Plány a roadmap (to, čo by mal program zafinancovať/zmentorovať)

### Phase 3b — Advanced Telecommanding (už v `FEATURES.md`)
- **CCSDS Telecommand Parser** s plnou validáciou hlavičky (APID, Sequence Flags).
- **`CommandExecutorService`** — decoupling opcode dispatchu od UDP receiveru.
- **Doplnenie XTCE commandov** (SET_TRANSMIT_POWER, nové operation commandy).
- **Fyzikálna reakcia na TC:**
  - `THRUST_MANEUVER` → dynamicky modifikuje propagátor (delta-V aplikované na SpacecraftState).
  - `CHAOS_MONKEY` fault injection → simulovaný výpadok subsystému (battery voltage → 0 V).

### Killer Features z `FEATURES_v2.md`
1. **Feature A — Predictive Orbital Shadowing (The True Digital Twin).** Orekit engine beží paralelne s ideálnym modelom, Yamcs porovnáva Δ s live TM, `ParameterAlarm` sa spustí pred katastrofálnym zlyhaním. To je **jediný skutočný digital twin feature** — ostatné systémy iba vizualizujú.
2. **Feature B — Virtual Thread Matrix.** Transition z native OS threadov na Java 21 Virtual Threads → 10 000+ súbežných TLE propagátorov na jednom COTS serveri. Priama odpoveď na data deluge mega-konstelácií.
3. **Feature C — Closed-Loop Command Verification (FinTech-grade).** Kryptografický handshake: command NIE JE `COMPLETED`, kým neprílde ACK z OBC. Povinné pre ESA inštitucionálny provoz. To je ten „cyber-resilience" uhol, ktorý porotu zaujíma.

### Študentský scale-up (z `FEATURE-v2-ext.md`)
6-mesačný programme, 2 študenti, 13 ticketov, výsledkom portfólio deployable artefaktov:

| Epic | Tickety | Doména |
|---|---|---|
| 1 — HMI | PAL-101, PAL-102 | CesiumJS 3D globe, WebSocket telemetry, TC control panel |
| 2 — Flight Dynamics | PAL-201, PAL-202 | Python pandas/matplotlib pipeline, AOS/LOS pass predictions |
| 3 — Multi-Payload XTCE | PAL-301, PAL-302 | APID 200 extension pattern, multi-stream archive validation |
| 4 — Yamcs Plugins | PAL-401, PAL-402, PAL-403 | Java custom algorithms (quaternion→Euler), payload simulator microservice, Testcontainers stress test |
| 5 — HPC + AI | PAL-501, PAL-502, PAL-503, PAL-504 | Orekit Monte Carlo conjunction assessment, automated collision avoidance TC loop, synthetic anomaly dataset, PyTorch autoencoder + ONNX export |

**Prečo to je pre Spaceport_SK dôležité:** program cieli aj na **študentské tímy** — a ja mám pripravený backlog, do ktorého viem okamžite zapojiť 2 študentov. Projekt som prezentoval začiatkom apríla 2026 na **Univerzite Mateja Bela (UMB) v Banskej Bystrici** a aktuálne čakám na odpoveď, či sa do integrácie študenti zapoja. To je unikátny škálovací plán, ktorý iní účastníci pravdepodobne nemajú.

### Dlhodobé (Backlog)
- Ground station visibility (AOS/LOS pre ESTEC, Kiruna, alebo hypoteticky slovenská GS).
- CCSDS SDLS — HMAC autentifikácia TC paketov (bezpečnosť pre inštitucionálny operation).
- Kubernetes Helm chart pre horizontálne škálovanie telemetry processora.
- Cloud-native deployment na AWS Ground Station alebo Azure Space.

### Konkrétny cieľ pre Demo Day 2026: Automated Collision Avoidance Bundle

> *Doplnené 2026-04-11 po scope diskusii pre solo vs. team execution.*

**Target deliverable:** kompletný, end-to-end Automated Collision Avoidance (COLA) flow bežiaci lokálne na vlastnom PC cez `docker compose up`, pripravený pre live demo na Demo Day (29. 9. 2026). To je moment, ktorý má porotu zapamätať — a zároveň priama odpoveď na programový focus area *„Monitorovanie a mitigácia vesmírneho odpadu"*.

**Čo do balíka patrí (tri kusy bundle-nuté ako JEDEN demo package, nie tri nezávislé features):**

1. **PAL-501 — HPC Conjunction Assessment & Monte Carlo Pc** (backlog estimate 100 h)
   Standalone Maven projekt s Orekit 12.2, ingestuje CelesTrak GP catalog (~500 objektov v local validation móde), screeninguje minimum distance cez 7-dňové propagation window, Monte Carlo Pc estimation, output JSON report + top-10 conjunctions posted do Yamcs event logu cez REST API.

2. **PAL-502 — Automated Collision Avoidance Telecommanding** (backlog estimate 80 h)
   `FIRE_THRUSTER` XTCE MetaCommand s `TransmissionConstraint` + `ManualVerifier` (command čaká na operator APPROVE), Python script polluje Yamcs events, detekuje Pc > 10⁻⁴, queue-uje thruster command s vypočítaným delta-V. Safety gate: operator musí ručne approvnúť cez Yamcs UI, inak sa command nikdy nereleasne.

3. **Phase 3b `THRUST_MANEUVER` physics reaction** (odhad ~15–25 h navyše nad backlog)
   *Tento kus v backlogu `FEATURE-v2-ext.md` explicitne chýba, ale je kritický pre demo narrative.* V `OrbitPropagationService` je nutné zareagovať na opcode 0x04 (FIRE_THRUSTER): aplikovať delta-V na aktuálny `SpacecraftState`, vytvoriť nový `TLEPropagator`, atomicky ho swapnúť cez existujúci `AtomicReference<TLEPropagator>` pattern. Výsledok: v Yamcs UI vidno, ako sa orbita **viditeľne mení v reálnom čase** po kliknutí APPROVE.

**Prečo ten tretí kus je nevynechateľný:**
PAL-501 + PAL-502 v originálnom znení končia pri „command reaches `SENT` status" — teda Spring Boot paket dostane, zaloguje opcode, a nič ďalšie sa nestane. To je technicky správny closed-loop, ale vizuálne je to len riadok v logu. Pridanie physics reaction transformuje demo z „impressive plumbing" na **„operator práve zachránil satelit pred zrážkou s debris"** — a to je ten emocionálny moment, ktorý porota Demo Day zapamätá a spája si ho s konkrétnym menom projektu.

**Effort budget:**

| Komponent | Backlog estimate | Solo realistic | Poznámka |
|---|---|---|---|
| PAL-501 | 100 h | 60–80 h | Backlog predpokladá študenta; senior solo je rýchlejší |
| PAL-502 | 80 h | 40–60 h | Backlog predpokladá študenta |
| Phase 3b physics wiring | — | 15–25 h | Nie je v backlogu; kritické pre demo narrative |
| Polish + integration + rehearsal | — | 20–30 h | Demo video, dokumentácia, dry runs |
| **Total (solo)** | **180 h** | **135–195 h** | |

**Timeline reality check (2026-04-11 → 2026-09-29 ≈ 24 týždňov):**

| Týždenný budget | Zhodnotenie |
|---|---|
| > 15 h/týždeň solo | Bezpečná rezerva, zvládne aj plný rigor (N=10 000 Monte Carlo, full test coverage) |
| ~10 h/týždeň solo | Na hrane, nutné descope rigoru (viď nižšie) |
| 5–8 h/týždeň solo | **UMB študenti nie sú nice-to-have, sú blocker**; bez nich sa demo nestíha |
| S 2 UMB študentmi v pair-programming režime na PAL-501 | Pohodový timeline; ja sa sústredím na PAL-502 + Phase 3b wiring + polish |

**Team status (k 2026-04-11):** prezentácia projektu na UMB v Banskej Bystrici prebehla začiatkom apríla 2026. Čaká sa na odpoveď od študentov o potenciálnom zapojení. **Demo target platí bez ohľadu na výsledok** — ak UMB nevyjde, realizácia pokračuje solo s agresívnym descopom.

**Descope stratégia pre solo scenár (ak UMB nevyjde):**

Kľúčový princíp — **descopovať rigor, nie features**. Demo narrative musí zostať intaktný.

- Monte Carlo `N = 1 000` samples miesto `10 000` (ušetrí ~15–20 h výpočtu aj debug času; presnosť Pc stačí pre demo, nie pre papers)
- `--catalog-limit=500` natrvalo, nie ako CLI flag. Skip HPC/Slurm deployment úplne (ušetrí ~25–30 h infra práce)
- 80 % test coverage ako aspirácia, nie acceptance gate (ušetrí ~10 h)
- Skip PAL-502 HMI integrácie (PAL-102 extension) — použiť built-in Yamcs commanding UI na APPROVE/REJECT tlačidlá (ušetrí ~5 h)
- **NESKIPOVAŤ za žiadnu cenu:** Phase 3b physics reaction. To je nonnegotiable pre demo narrative — bez nej padá celý emocionálny payoff.

**Risk-ordered sprint plán (solo scenár):**

| Sprint | Obdobie | Ciele |
|---|---|---|
| 1 | apríl – máj | PAL-501 Maven scaffold, CelesTrak GP CSV parser, `--catalog-limit=10` first run validuje data flow |
| 2 | máj – jún | PAL-501 screening pass (TLE → TLE distance cez 7-day window), Monte Carlo (N=1000), local `--catalog-limit=500` completes < 10 min |
| 3 | jún – júl | PAL-501 Yamcs event posting cez REST, `conjunction_report.json` kompletný, PAL-502 XTCE `FIRE_THRUSTER` + `ManualVerifier` |
| 4 | júl – august | PAL-502 Python COLA script, E2E test so syntetickým conjunction eventom, operator approval flow cez Yamcs UI |
| 5 | august | **Phase 3b `THRUST_MANEUVER` wiring** v `OrbitPropagationService`, delta-V applied to `SpacecraftState`, atomic propagator swap, verification že orbita sa viditeľne mení v Yamcs UI po APPROVE |
| 6 | september | Polish, integration testing, backup 60 s demo video, Demo Day rehearsal, final Advisory Board feedback |

**Critical gate po Sprinte 5:** pred začiatkom septembra musí end-to-end demo fungovať na čistom `docker compose up` z `master` brancha. Žiadne „len u mňa to ide" shortcuts, žiadne manuálne kroky mimo `docker compose up` + curl. Ak gate padne, celý september je buffer na fix + rehearsal.

---

## 6. Komercializačný potenciál (pre Fázu 1 a 2 programu)

### Problem Statement
Legacy ground segment (SCOS-2000, EPOCH, open-source OpenC3) buď stojí státisíce € za seat, alebo neriešia mega-konstelácie (10 000+ satov) ani predictive maintenance. NewSpace operátori potrebujú lacný, cloud-native, škálovateľný GSaaS — a akademické riešenia im ho nedávajú.

### Target Customers
1. **NewSpace operátori small-sat konstelácií** — potrebujú rýchly, škálovateľný ground segment bez CapEx na SCOS-2000.
2. **ESA BIC inkubátorové firmy** — potrebujú reference platform pre ich payload projekty (napr. SatelliteVu, ICEYE scale-up).
3. **Národné vesmírne agentúry malých krajín** — Slovensko, Česko, Maďarsko, Chorvátsko: potrebujú ground segment, ale nemajú rozpočet na ESA-tier systémy.
4. **Defence primes / SSA operátori** — COLA loop, conjunction assessment, fault injection sú priamo defence-relevant.

### Revenue Model Scenariá
- **Open-core SaaS:** core je open-source, plugins a enterprise podpora sú komerčné (model Red Hat / Grafana Labs).
- **GSaaS per-satellite licencovanie** ($/sat/mesiac) cez cloud hosting.
- **Consulting + integrácia** pre inštitucionálnych zákazníkov (SARIO/MOD/Ministerstvo obrany).
- **ESA BIC startup runway** — 50 000 € business support + 200 000 € na validáciu (overiť presné čísla ESA BIC Slovakia v Fáze 2).

### Differentiators vs. konkurencia
| Vlastnosť | Palantir | SCOS-2000 | OpenC3 | AWS Ground Station |
|---|---|---|---|---|
| Open source | ✅ | ❌ | ✅ | ❌ |
| Cloud-native | ✅ | ❌ | ⚠️ | ✅ |
| Physics digital twin | ✅ | ❌ | ❌ | ❌ |
| CCSDS 133.0-B-1 | ✅ | ✅ | ✅ | ✅ |
| XTCE MDB | ✅ | ✅ | ❌ | ⚠️ |
| Virtual Thread scaling | ✅ | ❌ | ❌ | ❌ |
| ESA ground segment lineage (Yamcs) | ✅ | ✅ | ❌ | ❌ |

*(Tabuľka je hrubá — v prípravnej fáze treba overiť presné capabilities konkurencie.)*

---

## 7. Štruktúra krátkej prezentácie (Demo Day + Advisory Board feedback)

Program má dve prezentačné príležitosti:
1. **Kick-off/Advisory Board feedback** (apríl-máj) — 3–5 minútový pitch, technicky detailný.
2. **Demo Day** (29. 9. 2026) — typicky 5–7 minút pre porotu, pitch + live demo.

### Návrh 7-slide pitch decku (adaptovateľný na obe situácie)

| # | Slide | Čo tam ide | Čas |
|---|---|---|---|
| 1 | **Hook — problém** | „NewSpace operátori potrebujú ground segment pre 10 000+ satelitov. Legacy systémy stoja milióny. Open-source systémy tam nie sú." Jeden graf rastu mega-konstelácií (Starlink, Kuiper, OneWeb, Guowang). | 30s |
| 2 | **Riešenie** | „Palantir = open-source GSaaS Digital Twin. Orekit physics + Yamcs mission control + CCSDS 133.0-B-1 cez Virtual Threads." Schéma z `ARCHITECTURE.md` (zjednodušená). | 45s |
| 3 | **LIVE DEMO** | `docker compose up` → ISS telemetry v Yamcs web UI za 60 s. Swap TLE cez curl → orbita sa mení za sekundu. Klik na PING v Yamcs → paket doletí do Spring Boot logov. **Toto je najsilnejší moment.** | 90s |
| 4 | **Technická hĺbka** | Tri bullet pointy: (a) CCSDS 133.0-B-1 na úrovni ByteBuffer, (b) TEME→ITRF→WGS84 cez IERS-2010, (c) hot-swap TLE cez `AtomicReference` zero-downtime. Môj cieľ: ukázať, že nie som AI wrapper — viem fyziku aj protokoly. | 45s |
| 5 | **Differentiators / killer features** | Feature A (Predictive Orbital Shadowing) — jediné true digital twin na trhu; Feature B (Virtual Thread scaling) — 10 000+ satov na jednom serveri; Feature C (Closed-loop command verification) — FinTech-grade reliability. | 45s |
| 6 | **Komercializácia + tím** | Target customers (NewSpace, ESA BIC, malé agentúry, defence). Revenue model (open-core SaaS, per-sat licensing, ESA BIC runway). Škálovateľnosť cez študentský tím (13 ticketov, 2 juniori, 6 mesiacov). | 45s |
| 7 | **Ask / Next steps** | Čo chcem z programu: mentoring na go-to-market, prístup k ESA BIC pipeline, Advisory Board feedback na killer features, validácia revenue modelu, náborové kontakty na juniorské tímy. | 30s |

**Celkom:** ~5,5 minúty pitch + ~2 minúty live demo = bezpečne v 7-minútovom window.

### Čo vyzdvihnúť v 3-vetnej formulácii (pre prihlášku „stručný popis projektu")

> Palantir je open-source Ground Segment as a Service Digital Twin, ktorý spája Orekit astrodynamickú simuláciu s Yamcs mission control cez CCSDS 133.0-B-1 protokol a Java 21 Virtual Threads — funkčný prototyp so obojsmerným TM/TC linkom je dostupný na [github.com/jakubt4/palantir] a spúšťa sa jedným `docker compose up`. Cieľom je vytvoriť škálovateľnú, cloud-native alternatívu k drahým legacy systémom (SCOS-2000, EPOCH) pre NewSpace operátorov small-sat mega-konstelácií, s tromi unikátnymi vlastnosťami: predictive orbital shadowing (true digital twin), 10 000+ satellite propagation na jednom COTS serveri, a closed-loop cryptographic command verification. V rámci Spaceport_SK plánujem validovať go-to-market stratégiu, prejsť cez ESA BIC pipeline, a škálovať vývoj cez 6-mesačný 13-ticket integračný programme pre 2 junior študentov.

### Čo do „zloženie tímu"
- **Core engineer + zakladateľ**: ja (Jakub Toth). Skúsenosť s Java 21, Spring Boot, distributed systems, CCSDS, Orekit.
- **Plánovaný expansion**: 2 študenti z **UMB Banská Bystrica**. Projekt tam bol prezentovaný začiatkom apríla 2026; aktuálne (stav 2026-04-11) sa čaká na odpoveď o commitmente. Zapojenie plánované primárne do `FEATURE-v2-ext.md` Epic 5 work (PAL-501 pair-programming odporúčaný backlogom).
- **Advisory**: hľadám cez program mentorov so space sektora backgroundom (ideálne niekto s Yamcs operation experience alebo ESA BIC).

---

## 8. Riziká a otvorené otázky (na vyriešenie PRED prihláškou)

### Riziká
1. **Môžu porotu prekážať „iba" open-source ground segment bez hardware/ payload komponentu?** Predchádzajúci víťazi mali hmatateľné produkty (glider, AI model). Mitigation: silný live demo + číselný commercial angle (GSaaS market size).
2. **Komercializačná dráha nie je celkom jasná.** Open-core SaaS je validný model, ale treba ho oveľa konkrétnejšie rozpracovať pre Fázu 1 (Business Canvas workshop). Potrebujem early validation od 2–3 potenciálnych customerov PRED programom.
3. **Študentský scale-up plán je ambiciózny.** Reálne viem získať 2 študentov za týchto podmienok? Prezentácia na UMB v Banskej Bystrici prebehla začiatkom apríla 2026 — čaká sa na odpoveď od študentov. Solo fallback plán musí zostať viable (viď sekcia 5, podsekcia *Konkrétny cieľ pre Demo Day 2026*).
4. **Tím = solo founder.** Program to neblokuje, ale mentori často pushujú k „co-founder search". Pripraviť odpoveď prečo solo je OK pre tento fázu projektu.

### Otvorené otázky (na doriešenie)
- [ ] Overiť presné ESA BIC Slovakia podmienky a sumy (financial support, equity, deadline).
- [ ] Overiť, či sa programu dá zúčastniť ako individuálny founder s plánom scale-upu (alebo potrebujem co-founder už pri prihláške).
- [ ] Získať 2–3 discovery calls s potenciálnymi zákazníkmi (slovenský satellite startup? Needronix? SpaceScavengers? Datafrost?). Vytvorí to validáciu pre Fázu 1.
- [ ] Založiť public GitHub repository (ak ešte nie je) — bez toho nebude možné v demo ukázať open-source trust factor.
- [ ] Pripraviť 60-sekundové demo video (backup pre prípad, že live demo zlyhá pri sieťových problémoch na Demo Day).
- [ ] Overiť, či formulácia v prihláške má byť v slovenčine alebo angličtine (program má medzinárodných mentorov — pravdepodobne SK prvky + EN pitch deck).
- [ ] Sledovať spätnú väzbu z UMB ohľadom zapojenia študentov do `FEATURE-v2-ext.md` ticketov (prioritne PAL-501 pair-programming).

---

## 9. Action Items — čo urobiť pred 20. aprílom 2026

### Must-have (pred deadline)
1. **Finalizovať pitch draft** — jeden odsek (prihláška) + 7-slide deck (Demo Day ready-ish).
2. **Definovať tému projektu** — navrhovaná formulácia: *„Palantir: Open-Source GSaaS Digital Twin pre NewSpace Mega-Konstelácie"*.
3. **Stručný popis projektu** — použiť 3-vetnú formuláciu z sekcie 7.
4. **Zloženie tímu** — pravdepodobne solo founder + plán expansion.
5. **Poslať prihlášku** na spaceoffice@sario.sk s predmetom napr. *„Spaceport_SK Application 2026 — Palantir Digital Twin"*.

### Nice-to-have (zvýši šance, ale nie blocker)
6. **Public GitHub repo** — open source rhetoric je dôveryhodnejší s viditeľným kódom.
7. **README.md polish** — sekcie „Live Demo" s GIF-om alebo screenshotom Yamcs UI.
8. **2–3 discovery calls** s reálnymi operátormi (dá materiál pre Fázu 1 Business Canvas).
9. **CesiumJS proof of concept** (PAL-101 aspoň na úrovni „Hello World" 3D globe s dummy polohou) — vizuálny hook pre Demo Day je obrovský.
10. **Follow-up z UMB prezentácie** — sledovať odpoveď o zapojení študentov; ak nevyjde, aktivovať solo descope stratégiu zo sekcie 5.

### Po kick-off (28. apríl a ďalej)
- Fáza 1 (apríl-máj): Business Canvas workshopy, technology validation → pripraviť data pre GTM pitch v júni.
- Fáza 2 (jún): Pitch deck polish, VC Q&A, ESA BIC rozhovor → získať commitment na validation funding.
- Jún-september: Implementovať aspoň jeden z „killer features" (Feature A = Predictive Orbital Shadowing je najlepší kandidát, lebo je najvýraznejšie diferenciácia a technicky najreálnejšie v 3 mesiacoch).
- September: Demo Day rehearsal, final Advisory Board feedback, submission.

---

## 10. Referencie

- **Spaceport_SK**: https://spaceoffice.sk/spaceport-sk/
- **Prihlášky**: spaceoffice@sario.sk
- **Interné dokumenty Palantir**:
  - `README.md` — project overview, build commands, REST API
  - `ARCHITECTURE.md` — full source dump, container config, XTCE MDB
  - `FLOW.md` — byte-level walkthrough CCSDS encodingu
  - `FEATURES.md` — implementation status, Phase 1–3 roadmap
  - `FEATURES_v2.md` — killer features A/B/C pre ESA BIC pitch
  - `FEATURE-v2-ext.md` — 13-ticket študentský integration backlog
- **Externé standardy**:
  - CCSDS 133.0-B-1 (Space Packet Protocol) — https://public.ccsds.org/Pubs/133x0b2e1.pdf
  - Orekit — https://www.orekit.org/
  - Yamcs — https://yamcs.org/
