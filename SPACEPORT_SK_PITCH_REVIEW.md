---
title: "Palantir × Spaceport_SK — Senior Review pitch dokumentu"
subtitle: "Štyri perspektívy: Space Systems Architect, System Architect, Java Developer, Mission Control Analyst"
author: "Review assembled 2026-04-11"
date: "2026-04-11"
---

# Palantir × Spaceport_SK — Senior Review pitch dokumentu

> Review dokumentov `SPACEPORT_SK_PITCH.md` a `SPACEPORT_SK_PITCH.en.md` zo štyroch senior perspektív, proti reálnemu stavu kódu na `master` branchi (commit `604a94d`).

## Verdict

Pitch je po obsahu ambiciózny a dobre štruktúrovaný, ale obsahuje niekoľko **technicky nepresných tvrdení, kontradikcií medzi sekciami a marketingových nadsadení**, ktoré senior porotca (Advisory Board má ESA/EUSPA expertov) odhalí do 3 minút. Opraviteľné za ~2 hodiny, ale nutné pred deadline-om. Kritické nálezy sú v tom, že **tri „unique properties" v 3-vetnom exec summary sú z roadmapy, nie z prototypu**, a **CCSDS compliance claim je asymetrický** (downlink áno, uplink nie).

---

## Senior Space Systems Architect

### RED

**R1. „Full CCSDS 133.0-B-1 compliance" je asymetrický claim.**
Downlink (`CcsdsTelemetrySender`) áno — 6 B Primary Header, APID, sequence counter, data length, IEEE 754 big-endian payload, verifikované proti kódu. **Uplink ale NIE.** `UdpCommandReceiver.processTelecommand()` číta len `data[0]` ako 1-byte opcode — ignoruje celú CCSDS TC Packet hlavičku, ktorú Yamcs `UdpTcDataLink` posiela. To je jednosmerná compliance. Pitch tvrdí „bidirekčný CCSDS loop" — ale TC strana kompatibilitu CCSDS hlavičky nevyužíva, len prvý byte payload-u, čo je shortcut (funguje preto, že Yamcs TC Command Container je minimálny uint8 opcode, takže prvý byte za hlavičkou by kolidoval… správne, `data[0]` v skutočnosti vráti prvý byte **primárnej hlavičky** CCSDS TC paketu, nie opcode!). **Toto je podozrenie na skutočný bug** — treba overiť behaviorom: pošli PING z Yamcs a skontroluj, či sa naozaj dekóduje ako 0x01, alebo ako nejaký byte z CCSDS hlavičky TC paketu. Ak to funguje iba „náhodou" kvôli poradiu bitov v hlavičke, to je silná red flag.

> **Fix pre pitch:** „CCSDS 133.0-B-1 downlink (Primary Header verified against spec); uplink uses a simplified opcode dispatcher — a full TC parser with APID/SeqFlags validation is in Phase 3b roadmap."

**R2. „Kryptografický handshake" vo Feature C (Closed-Loop Command Verification) — marketingová inflácia.**
Popis vo `FEATURES_v2.md` je o TC→TM ACK verifikácii — „command nie je COMPLETED, kým nepríde ACK z OBC". To je štandardný CCSDS command verification (CoP-1, `ManualVerifier` v XTCE). **Žiadna kryptografia tam nie je.** HMAC/SDLS je v long-term backlogu. ESA expert v Advisory Board ťa za slovo „kryptografický" chytí okamžite. Buď slovo vypusti, alebo presuň CCSDS SDLS (HMAC-SHA256 autentifikácia TC paketov podľa CCSDS 355.0-B-1) do scope-u Feature C.

**R3. „Jediný skutočný digital twin feature" (Feature A — Predictive Orbital Shadowing) — faktická nesprávnosť.**
Model-vs-telemetry residual detection je štandardná praktika digital twins už od publikácií Digital Twin Consortium (2020), implementovaná v Siemens MindSphere, Tesla battery farms, NASA JPL simulator pipelines (Europa Clipper), Boeing 787 engine twins. **Tvrdenie „jediný" je BS a porota to vie.** Feature A je legitimne opísaná „model-based fault detection for orbit dynamics" — čo je jeden subsystém z mnohých. Priznaj to a získaš kredibilitu: *„Feature A aplikuje štandardný digital twin residual-based fault detection pattern na orbit subsystém — prvý open-source GSaaS, ktorý to má priamo zadrôtované do Yamcs ParameterAlarm pipeline."*

### YELLOW

**Y1. „SDP4 propagation"** — Orekit `TLEPropagator.selectExtrapolator()` to auto-routuje na základe orbit period (cut-off 225 min). Kód to technicky podporuje, ale **nikdy si to netestoval na deep-space TLE** — repo má len ISS (LEO, SGP4). Claim „SDP4" je teoreticky true, prakticky neoverený. Buď pridaj jeden deep-space test (napr. GOES-18 TLE), alebo downgraduj claim na „SGP4 (SDP4 auto-supported cez Orekit)".

**Y2. Feature A „minutes before catastrophic failure"** — orbit prediction residuals sú dominované drag + J2 modeling chybami, nie HW faults. V LEO vidíš delta z drag modeling error dlho pred tým, než ti TLE delta naznačí failure. Reálne „minutes before" fault detection je attitude/power/thermal subsystem telemetria, nie orbit. Feature A pomôže pri detekcii manévrov, residual thrust, alebo katastrofálneho orbit decay — nie pri „catastrophic failure" generally. Upresni.

**Y3. XTCE payload bohatosť** — MDB má 3 parametre (lat/lon/alt). Reálny satelit má stovky až tisíce. Porotca-MC-analyst sa spýta: „Kde je attitude quaternion, battery voltage, thermal sensors?". Odpoveď je v Epic 3/4 backlogu — ale pitch to nespomína. Ref. do sekcie 4: *„Aktuálna MDB je minimal nav-only set pre PoC, rozšírenie o environmental/attitude/power parametre (APID 200/300/400) je pokryté v Epic 3-4."*

### GREEN

- TEME → ITRF → WGS84 cez `IERSConventions.IERS_2010` je správne. Použitie `OneAxisEllipsoid` + `WGS84_EARTH_EQUATORIAL_RADIUS` + `WGS84_EARTH_FLATTENING` je idiomatické Orekit. Senior astrodynamika engineer si povie „OK, vie o čom hovorí".
- Správna terminológia: AOS/LOS, TCA, Pc, COLA, RTN frame (implicitne v PAL-502 delta-V argumentoch), CelesTrak GP, SGP4/SDP4. Žiadne terminologické wannabe-isms.
- `AtomicReference<TLEPropagator>` hot-swap je elegantné a je to presne ten pattern, ktorý by senior navrhol pre lock-free TLE update.
- Yamcs 5.12.2 + XTCE 1.2 (schema `20180204`) je aktuálne.

---

## Senior System Architect

### RED

**R4. „10 000+ satelitov na jednom COTS serveri cez Java 21 Virtual Threads"** — **kategoricky zlé prepojenie conceptov.**

Virtual Threads riešia blokujúce I/O (per-socket blocking reads). **SGP4 propagation je CPU-bound** — 10k propagátorových tickov/sec na modernom 8-16 core CPU znamená paralelizmus cez platform threads (ForkJoinPool), nie cez Virtual Threads. VT ti v CPU-bound úlohách nepomôžu vôbec — naopak, môžu byť mierne horšie kvôli scheduler overhead.

Honest claim znie:

> *„Java 21 enables two independent scaling axes: Virtual Threads for thousands of concurrent per-satellite blocking I/O operations (per-sat UDP downlinks, per-sat REST listeners), and platform-thread CPU parallelism for SGP4/SDP4 propagation on multi-core COTS hardware. Combined, both support projected scaling to ~10k satellites on a single 16-core server — subject to empirical benchmarking."*

Dve vety, technicky správne, senior porotca prikývne. Aktuálna jedna veta = red flag.

**R5. „Production-grade PoC" je oxymorón.**
PoC z definície nie je production-grade. Navyše aktuálny stav neprechádza basic production checklist:

- `POST /api/orbit/tle` **nemá žiadnu autentifikáciu** — ktokoľvek na sieti môže swapnúť propagátor. Pre ground segment systém je to nonstarter.
- Žiadny rate limiting.
- Žiadny Micrometer/Prometheus, žiadny `/actuator/health` endpoint (v pom.xml chýba `spring-boot-starter-actuator`).
- Žiadne CI/CD (žiadny `.github/workflows/`), žiadny test coverage badge.
- Žiadne TLS / mTLS.
- Žiadny audit log pre TC operácie.

A napriek tomu Feature C claim-uje „FinTech-grade cyber-resilience". **Interná kontradikcia.** Použite „production-ready prototype" alebo „reference implementation" — a v risks sekcii úprimne priznaj, čo chýba do production-grade.

### YELLOW

**Y4. Differentiator tabuľka v sekcii 6** je subjektívna a na viacerých miestach diskutabilná:

- „Cloud-native: SCOS-2000 ❌" — SCOS-2000 má ESA OPS-SAT container cloud deploy (2021+). Nie je to cloud-native-first, ale nie úplne ❌.
- „CCSDS 133.0-B-1: Palantir ✅" — ok pre downlink, viď R1.
- „XTCE MDB: AWS Ground Station ⚠️" — AWS GS nerieši MDB vôbec (je to iba RF/antenna service), takže to ani ⚠️ nie je, iba N/A.

Odporúčam pridať pod tabuľku vetu: *„Comparison is qualitative — exact capability matrix TBD during Phase 1 competitive analysis."* (už tam máš „Tabuľka je hrubá" — len to zdôrazni explicitne).

**Y5. `depends_on: service_started` riešenie pre DNS race** — to je reálne premyslené, ale je to **workaround, nie fix**. Správne riešenie je nastaviť Yamcs `UdpTcDataLink` s retry/DNS re-resolve loop, alebo použiť Docker service discovery s health check, ktorý čaká na Spring Boot. Aktuálny stav znamená, že ak sa `palantir-core` reštartuje (bez Yamcs reštartu), Yamcs stratí DNS resolution. Senior architekt sa spýta: *„A čo sa stane, keď palantir-core padne a reštartuje sa?"*

**Y6. Chýba SBOM, security scan, dependency vulnerability tracking.** Pre „ESA BIC pipeline" ready claim potrebuješ aspoň `dependabot.yml` alebo OWASP Dependency-Check. 30 minút práce, veľký credibility boost.

### GREEN

- Docker Compose je čistý, multi-stage Dockerfile správny (build → JRE runtime).
- Perzistentný named volume pre Yamcs (`palantir_yamcs_data`) je správny operational choice.
- Spring Boot 3.2.5 + Java 21 je aktuálne (aj keď Spring Boot 3.4 je už vonku — nice-to-have upgrade pred pitchom).
- Docker `YAMCS_UDP_HOST` env override cez Spring `@Value` je čistá 12-factor praktika.

---

## Senior Java Developer

### RED

**R6. Dual `AtomicReference<TLEPropagator>` + `AtomicReference<String>` v `OrbitPropagationService`** — **porušuje atomicitu cross-field reads.**

```java
private final AtomicReference<TLEPropagator> activePropagator = new AtomicReference<>();
private final AtomicReference<String> activeSatelliteName = new AtomicReference<>("NONE");
```

Scenár: scheduler thread číta `activePropagator.get()` → dostane NEW propagator (po swap-e). Potom číta `activeSatelliteName.get()` → dostane OLD name (swap ešte neprebehol pre druhú atomic). Výsledok: **log "ISS (ZARYA) Position" pre NOAA-18 orbit**. Nie crash, ale corrupted observability.

**Fix:** jeden `AtomicReference<TleState>` kde `TleState` je record:

```java
private record TleState(TLEPropagator propagator, String satelliteName) {}
private final AtomicReference<TleState> active = new AtomicReference<>();
```

Jeden atomic read = konzistentný stav.

**R7. Zero testov pre `CcsdsTelemetrySender`** — to je **najrizikovejšia trieda v projekte** (byte-level binary encoding) a má 0% coverage. JaCoCo badge je pritom hlavný sales argument v pitch sekcii 4 („Engineering Quality").

Chýbajú golden byte tests:

```java
@Test void palantirNavPacket_matchesCcsdsSpec() {
    // Given: lat=51.6318, lon=180.4216, alt=407.32
    // Expect: 0x00 0x64, 0xC0 0x00, 0x00 0x0B, 0x42 0x4E 0x8F 0x5C, ...
}
@Test void sequenceCounter_wrapsAt14Bits() { ... }
@Test void apid_maskedTo11Bits() { ... }
```

Bez týchto testov môže jeden zle umiestnený `putFloat()` potichu zničiť celú Yamcs pipeline a CI to nezachytí.

### YELLOW

**Y7. `CcsdsTelemetrySender` má field `@Value` injection** namiesto constructor injection cez `@RequiredArgsConstructor` — inconzistentné s `OrbitPropagationService` a `TleIngestionController`, ktoré constructor injection majú. Drobnosť, ale viditeľná v code review.

**Y8. `ByteBuffer.allocate(18)` pri každom volaní** — na 1 Hz je to triviálne, ale pri „10 000+ sats" claime by to bolo 10k allocation/sec. Better: reusable per-thread `ThreadLocal<ByteBuffer>` alebo direct buffer. Cosmetic na PoC úrovni.

**Y9. `@SuppressWarnings("unused")` na `OrekitConfig` injection** je inteligentný trik pre ordering, ale nestandardný. Cleaner pattern: `@DependsOn("orekitConfig")` na `OrbitPropagationService`. Senior Java dev ihneď vidí „ah, tak sa vynucuje init order" — ale výslovný `@DependsOn` je expresívnejší.

**Y10. `propagateAndSend()` catch `Exception e`** — swallowing generic exception len do `log.error()`. V real ops tam potrebuješ Micrometer counter increment (`propagation.errors.total`) + prípadne alert. Inak timeline pôjde ďalej a observability ti povie „žiadny paket za posledných 10 minút" — ale nezistíš prečo.

**Y11. `UdpCommandReceiver.triggerRebootSequence()` je prázdny stub** — ok pre PoC, ale sekcia 4 hovorí „Telecommand Uplink (TC) — bidirekčný loop" ako implementovaný. Reálne iba logline. Buď uveď ako mock („REBOOT_OBC je acknowledge-only stub"), alebo nemienať toto ako feature.

**Y12. Tests: 6 total** (1 integration + 3 controller + 2 service). Pitch claim „JUnit 5 + Mockito test suite" je technicky true, ale 6 testov nie je „test suite" v očakávaní senior dev. Buď rozšíriť (priority: CCSDS encoder), alebo downgrade jazyk na „baseline smoke test suite".

### GREEN

- `var` + `final` konzistentne naprieč codebase (CLAUDE.md convention je dodržaná, verifikované).
- Java records pre DTOs.
- `@RequiredArgsConstructor` kde sa hodí — správne použitie Lombok.
- `AtomicInteger` pre sequence counter s `getAndIncrement() & 0x3FFF` — idiomatické a race-free.
- `Executors.newVirtualThreadPerTaskExecutor()` v `UdpCommandReceiver` — správne použitie Virtual Threads pre blocking socket receive loop.
- `HexFormat.ofDelimiter(" ")` pre DEBUG logging — moderný Java 17+ API, ukazuje že autor pozná nový stdlib.

---

## Senior Mission Control Analyst

### RED

**R8. ESA BIC finančné čísla sú pravdepodobne zle.**
Pitch sekcia 6 Revenue Model: *„ESA BIC startup runway — 50 000 € business support + 200 000 € na validáciu"*. Reálna ESA BIC ponuka (podľa official ESA BIC Terms 2024-2025):

- **€50k cash incentive** (zero-interest loan alebo grant — záleží od konkrétneho BIC)
- **Technical support + facility access + IPR advice + mentoring** v odhadovanej hodnote **až €200k in-kind services, NIE cash**

Pitch číta „€50k + €200k = €250k cash", čo je **factually wrong**. Advisory Board má ESA zástupcov, ktorí ťa za toto chytia. **Buď opraviť pred pitchom, alebo počkať do Fázy 2, kde dostaneš real ESA BIC Slovakia T&Cs.** Zatiaľ uveď: *„~€50k direct + significant in-kind support (exact figures TBD per ESA BIC Slovakia)."*

**R9. „ESA, EUMETSAT, DLR používajú Yamcs"** — **polopravda**.

- **ESA:** áno pre SmallGEO a niektoré menšie programy, ale primary platforma je SCOS-2000/EGS-CC.
- **EUMETSAT:** používajú vlastné CGMS-aligned systémy, Yamcs nie je ich primárna platforma.
- **DLR GSOC:** používajú GECCOS (vlastný), nie Yamcs ako primárny systém.

Yamcs je skutočne respektovaný open-source MC, používaný commercial operátormi (napr. Northrop Grumman, niektoré startupy) a vybranými ESA misiami, ale claim ho pozdvihuje na úroveň ESA-standard, ktorou nie je. **Safer formulácia:** *„Yamcs is a mature open-source mission control system used by selected ESA small-sat programmes and commercial NewSpace operators."*

**R10. „No onboard timestamp" + „errorDetection: NONE" + žiadny secondary header** — legitímne PoC shortcuts, ale senior MC analyst sa spýta: *„Ako riešite timing drift a packet loss diagnostics?"*

V reálnej telemetrii má každý paket:

1. Secondary header s onboard time (typicky CUC/CDS format) — na timing reconstruction počas downlink gaps
2. Packet Error Control (CRC-16) trailer — na bit-flip detection

Ani jedno tu nie je. GenericPacketPreprocessor s `useLocalGenerationTime: true` je demo shortcut — real ops to takto nikdy nerobí, lebo ground-side timestamp stráca onboard event ordering. Pitch by mal úprimne povedať: *„PoC simplifies by using ground-side timestamps; full secondary header with CUC onboard time is a roadmap item for institutional deployments."*

### YELLOW

**Y13. FIRE_THRUSTER delta-V frame nie je v pitch-i uvedený** — v PAL-502 ticket má argumenty `delta_v_x`, `delta_v_y`, `delta_v_z`. Každý flight dynamics analyst sa spýta **v akom frame**: RSW/RTN (radial/tangential/normal), LVLH, ECI? Ticket text hovorí „radial axis / along-track axis / cross-track axis" = RTN/RSW. **Pitch by mal explicitne uviesť „delta-V in RSW frame"** — iba to dve slová robí rozdiel medzi „niekto, kto vie čo robí" a „niekto, kto copy-pasted z ChatGPT".

**Y14. Monte Carlo covariance zjednodušenie** — „diagonal covariance with 100m position uncertainty, 0.01 m/s velocity uncertainty". Real SSA používa full 6×6 Cartesian covariance z orbital determination process (napr. z CDMs — Conjunction Data Messages). Diagonal je demo simplifikácia. PAL-501 ticket to explicitne priznáva („simplified: diagonal covariance"), ale pitch to nespomína. Ak sa na Demo Day spýta SSA expert „aká presnosť Pc", odpoveď „diagonal 100m" bude oceniteľná úprimnosťou, ale tiež treba zdôvodniť *prečo* je to OK pre demo scope.

**Y15. Pc threshold 10⁻⁴** — pitch používa tento prahov v popise PAL-502. Pre kontext: NASA používa 10⁻⁴ pre manned missions (ISS), ESA štandardne 10⁻⁵ pre unmanned LEO (per Space Debris Mitigation Handbook). 10⁻⁴ je konzervatívny a defenzívny, ale mieša normy. Pridaj poznámku: *„Pc > 10⁻⁴ threshold matches NASA COLA practice; ESA unmanned LEO typically uses 10⁻⁵ — configurable per mission profile."*

**Y16. Event posting do Yamcs cez REST API** — PAL-501 description tvrdí „`POST /api/archive/palantir/events`". Yamcs Events API endpoint je `POST /api/instances/{instance}/events` (nie `/archive/...`). Treba overiť exact endpoint proti Yamcs 5.12 docs. Drobnosť, ale pri implementácii zahnije o 2 hodiny.

### GREEN

- APID 100 pre nav, plánované 200+ pre environmental, 300 pre attitude, 400 pre payload — to je čistá APID namespace segregation, ktorú by aj real mission profile použil.
- `ManualVerifier` + `TransmissionConstraint` v XTCE pre FIRE_THRUSTER safety gate — to je THE správny pattern pre safety-critical commanding. Senior MC analyst si povie „OK, autor fakt vie, čo robí COLA procedure."
- Bidirekčný TM/TC loop v PoC (aj keď s R1 caveat) — mnohé akademické projekty majú iba downlink. Uplink integrácia je reálny plus.
- RSW frame pre delta-V v PAL-502 backlogu je správne (aj keď to treba explicitne v pitch uviesť, viď Y13).

---

## Cross-cutting issues (naprieč perspektívami)

**X1. 3-vetný exec summary mieša CURRENT prototype s FUTURE roadmap ako keby to boli už implementované features.**

Sekcia 7, riadok 294:

> *„...s tromi unikátnymi vlastnosťami: predictive orbital shadowing (true digital twin), 10 000+ satellite propagation na jednom COTS serveri, a closed-loop cryptographic command verification."*

**Všetky tri sú FUTURE Killer Features (`FEATURES_v2.md`), NIE sú v prototype.** Aktuálny prototype má: SGP4 propagáciu, CCSDS downlink, Yamcs XTCE decoding, primitive TC uplink. Žiadne shadowing, žiadnych 10k sats, žiadna cryptographic verification.

**Senior porotca to zastaví pri prvom čítaní** ak si potom pozrie GitHub repo a nenájde ani jeden z tých troch features.

**Fix:**

> *„Palantir je open-source GSaaS Digital Twin — funkčný prototype so SGP4 orbital propagation (Orekit 12.2), CCSDS 133.0-B-1 telemetry downlink, Yamcs mission control s XTCE decoding, a bidirekčným TM/TC loop-om cez Docker Compose. Roadmap pre 6-mesačný Spaceport_SK programme zahŕňa tri killer features: predictive orbital fault detection, horizontal scaling pre mega-konstelácie cez Java 21, a closed-loop command ACK verification. Demo Day deliverable je end-to-end Automated Collision Avoidance flow s physics-reactive operator confirmation."*

Jasne oddelené: TERAZ vs. ROADMAP vs. DEMO DAY TARGET.

**X2. Labeling mismatch medzi Feature B a Feature C.**
Sekcia 3 riadok 79: *„priamo 'killer feature C' z FEATURES_v2.md"* — ale kontext je Virtual Threads scaling, čo je **Feature B** v sekcii 5 riadok 152. Jeden z dvoch je zle. Oprav: je to **Feature B**.

**X3. Aerostacks = „R4 (2026)"** — ale ak aktuálny ročník (2026) je 5., tak R4 bol v **2025**, nie 2026. Oprav tabuľku víťazov.

**X4. GitHub repo contradiction.**
Sekcia 7 line 294: pitch 3-vetná formulácia cituje `github.com/jakubt4/palantir`.
Sekcia 8 line 315: open question: „Založiť public GitHub repository (ak ešte nie je)".
**Pitch už cituje URL, ktorú možno nemá verejnú.** Buď repo zverejni PRED poslaním prihlášky, alebo z 3-vetnej formulácie URL vymaž.

**X5. „Solo founder" v sekcii 7 tím + „pending students" v sekcii 5 + „solo mitigation" v sekcii 8** — troje rôznych framings tej istej reality. Pre prihlášku treba ONE consistent narrative. Odporúčam:

> *„Jakub Toth — solo founder and core engineer; actively recruiting student contributors from UMB Banská Bystrica (project presented April 2026, awaiting commitment) to join as Epic 5 pair-programmers. Sprint plan is viable solo; student involvement accelerates timeline and deepens scope."*

Takto čitateľ vidí: (1) kto je za projektom dnes, (2) kto má prísť, (3) že to nie je blocker pre pitch.

**X6. August ako Sprint 5 vrchol** — v SR/EÚ je to dovolenkový mesiac. Ak UMB študenti prídu, časť Sprint 5 bude mrtvá. Aspoň na to upozorni v risks.

**X7. Sprint 6 = september bez buffer marginy.** Demo Day 29. 9., Advisory Board feedback tiež v septembri. Ak Sprint 5 mieska, september nie je „buffer", je to jediná integration window. Reálna buffer marginа nie je. Zvažuj pull-in Sprint 5 do júla.

---

## Prioritizovaný fix list — čo urobiť PRED 20. 4. 2026

### Must-fix (pred odoslaním prihlášky)

1. **Prepísať 3-vetný exec summary (sekcia 7, line 294)** tak, aby jasne oddeľoval current prototype od roadmap. Toto je najväčší credibility risk. [15 min]

2. **Opraviť Feature B/C label mismatch v sekcii 3 line 79.** [2 min]

3. **Opraviť „R4 Aerostacks 2026" → „R4 Aerostacks 2025"** v tabuľke víťazov. Verifikuj rok, ak si neistý. [5 min]

4. **Odstrániť slovo „kryptografický" z Feature C** opisov (sekcia 5, tiež sekcia 7 exec summary). Nahraď „closed-loop command ACK verification". [5 min]

5. **Odstrániť slovo „jediný" z Feature A** popisu (sekcia 5 line 151). Nahraď „first open-source GSaaS to wire model residual fault detection directly into Yamcs ParameterAlarm". [5 min]

6. **Reformulovať Virtual Thread scaling claim** (sekcia 3 line 79 + sekcia 5 Feature B) aby oddelil Virtual Threads (I/O scaling) od platform thread CPU parallelism (SGP4 scaling). [10 min]

7. **Overiť behavior UdpCommandReceiver voči reálnemu Yamcs TC paketu** — spusti Yamcs, pošli PING z Yamcs UI, skontroluj či Spring Boot naozaj loguje `0x01`. Ak neloguje, máš **skutočný bug**, nie len dokumentačné nepresnosti. [30 min — najdôležitejšia položka celého review]

8. **Downgrade „Production-grade PoC"** na „Production-ready prototype" alebo „Reference implementation". Sekcia 4 line 136. [5 min]

9. **Opraviť ESA BIC finančné čísla** v sekcii 6 — nespomínať „€200k na validáciu" ako cash. Zmeniť na „€50k direct + in-kind support (exact figures TBD)". [5 min]

10. **Downgrade „ESA, EUMETSAT, DLR používajú Yamcs"** (sekcia 4 line 136) na „Yamcs is used by selected ESA small-sat programmes and commercial NewSpace operators". [5 min]

11. **GitHub repo decision** — buď zverejni repo a nechaj link v 3-vetnom summary, alebo vymaž link a uveď „repository ready for public release on request" (sekcia 7 line 294). [záleží od decision]

### Should-fix (zvýši kredibilitu, ale nie blocker)

12. **Fix dual `AtomicReference` race** v `OrbitPropagationService` — refactor na single `AtomicReference<TleState>`. [30 min + test update]

13. **Pridaj CCSDS golden byte test** pre `CcsdsTelemetrySender` — overí, že encoder produkuje bit-for-bit správny paket. Posilnená „Engineering Quality" sekcia. [45 min]

14. **Pridaj `spring-boot-starter-actuator`** + základný `/actuator/health` + `/actuator/metrics`. [15 min, massive credibility boost]

15. **Pridaj `@DependsOn("orekitConfig")`** miesto `@SuppressWarnings("unused")`. [5 min cleanup]

16. **Pridaj `.github/workflows/ci.yml`** s `mvn test`. [20 min, umožní zobraziť CI badge v README]

17. **Deklaruj explicitne RSW frame** pre FIRE_THRUSTER delta-V v pitch aj v XTCE MDB comments. [5 min]

18. **Doplň sekciu 8 risks o August holiday gap** a Sprint 6 buffer absence. [5 min]

### Nice-to-have (pre Fázu 1-2)

19. Upgrade Spring Boot 3.2.5 → 3.4.x.
20. Pridaj Dependabot config.
21. Rewrite PAL-501 event posting endpoint po overení voči Yamcs 5.12 docs.
22. Overiť Advisory Board composition 2026 (nemenovať ESA/EUSPA/YESS/Satlantis ak sa zloženie zmenilo).

---

## Kľúčové posolstvo

Pitch je **obsahovo ambiciózny a správne adresovaný** na Spaceport_SK focus areas, ale **trpí typickou „PoC promoted to production" inflation**, kde roadmap features znejú ako hotové. To je riziko u každej porotcovskej panelu so silnými domain expertmi — a Advisory Board Spaceport_SK je presne taký. **Rozdiel medzi „zaujímavý projekt" a „winning pitch" je tých 10 malých fixov vyššie, ktoré oddeľujú overselling od confident honest claim.** Hlavný sales argument (funkčný CCSDS/Orekit/Yamcs PoC s bidirekčným loopom + credible Demo Day target v COLA doméne) je sám o sebe silný — netreba ho vylepšovať marketingovými nadsadzeniami. Nech kód hovorí sám za seba.

**Najurgentnejšia položka mimo textových úprav: overiť UdpCommandReceiver behavior voči reálnemu Yamcs TC paketu (fix list #7).** Ak tam je skutočný bug v parsovaní, všetky ostatné úpravy sú kozmetika.
