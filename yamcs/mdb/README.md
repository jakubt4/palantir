# Palantir XTCE Mission Database

## Structure

```
yamcs/mdb/
├── baseline.xml           # SpaceSystem "Palantir" — bus TM + CCSDS primitives (FROZEN)
└── features/
    ├── commands.xml       # SpaceSystem "TC" — nested at /Palantir/TC (bus telecommands)
    └── <new-feature>.xml  # SpaceSystem "<Name>" — nested at /Palantir/<Name> (Phase B+ subsystems)
```

## How it loads

Yamcs instantiates each XTCE file as a `SpaceSystem` in the MDB tree. Under `mdb.subLoaders` in `yamcs/etc/yamcs.palantir.yaml`, sub-files are **nested inside the parent's SpaceSystem** — so `features/commands.xml` (root `<SpaceSystem name="TC">`) ends up at `/Palantir/TC/`.

Two hard rules Yamcs enforces:
1. **No two files may share a SpaceSystem name.** Attempting to load a second `<SpaceSystem name="Palantir">` raises `IllegalArgumentException: there is already a subsystem with name Palantir` at startup.
2. **Nested SpaceSystems resolve parent types by simple name** through the XTCE scope chain — so `features/commands.xml` can reference `uint16_t` or `CCSDS_Packet_Base` without qualified paths; the resolver walks up to `/Palantir` and finds them.

## Parameter & command paths in Yamcs

| Item | Path |
|---|---|
| Primary header parameters | `/Palantir/ccsds_packet_id`, `/Palantir/ccsds_seq_count`, `/Palantir/ccsds_length` |
| Nav telemetry | `/Palantir/Latitude`, `/Palantir/Longitude`, `/Palantir/Altitude` |
| Bus commands | `/Palantir/TC/PING`, `/Palantir/TC/REBOOT_OBC` |

REST command invocation URL mirrors the qualified path:
```
POST /api/processors/palantir/realtime/commands/Palantir/TC/PING
```

## Adding a new feature

1. **Pick a unique APID and SpaceSystem name.** APID 100 is reserved for nav; reserve new APIDs in `FEATURES.md`. The SpaceSystem name must be unique across all loaded files.
2. **Create `features/<feature>.xml`** with:
   - Root `<SpaceSystem name="<FeatureName>">` — unique, and it will become a child of `/Palantir`.
   - `<TelemetryMetaData>` for packets, `<CommandMetaData>` for commands, or both.
   - Reference baseline types and containers by **simple name** — e.g., `parameterTypeRef="uint16_t"`, `containerRef="CCSDS_Packet_Base"`. The XTCE scope resolver walks up to `/Palantir` and finds them.
   - Copy the XTCE schema declaration and root element pattern from `commands.xml`.
3. **Register the file** in `yamcs/etc/yamcs.palantir.yaml` under `mdb.subLoaders`:
   ```yaml
   mdb:
     - type: xtce
       spec: mdb/baseline.xml
       subLoaders:
         - {type: xtce, spec: mdb/features/commands.xml}
         - {type: xtce, spec: mdb/features/<feature>.xml}   # <-- new
   ```
4. **The Dockerfile already copies `mdb/features/` wholesale** — new files ship without a Dockerfile edit.
5. **Rebuild and verify**:
   ```bash
   docker compose up --build yamcs
   ```
   Each file produces one startup log line:
   ```
   XtceStaxReader  XTCE file parsing finished, loaded: N parameters, N tm containers, N commands
   ```
   New parameters/commands appear under **Parameters** / **Commanding** in the Yamcs Web UI at http://localhost:8090 under `/Palantir/<FeatureName>/...`.

## Example: Phase B env payload (PAL-301)

```xml
<!-- features/env-payload.xml -->
<SpaceSystem name="EnvPayload" ...>
  <TelemetryMetaData>
    <ParameterTypeSet>
      <!-- feature-specific types (e.g., °C, V, A units) -->
    </ParameterTypeSet>
    <ParameterSet>
      <Parameter name="Board_Temperature" parameterTypeRef="temperature_t"/>
      <!-- ... -->
    </ParameterSet>
    <ContainerSet>
      <SequenceContainer name="Env_Payload_Packet">
        <BaseContainer containerRef="CCSDS_Packet_Base">
          <RestrictionCriteria>
            <Comparison parameterRef="ccsds_packet_id" value="200" useCalibratedValue="false"/>
          </RestrictionCriteria>
        </BaseContainer>
        <EntryList>
          <ParameterRefEntry parameterRef="Board_Temperature"/>
          <!-- ... -->
        </EntryList>
      </SequenceContainer>
    </ContainerSet>
  </TelemetryMetaData>
</SpaceSystem>
```

Resulting paths: `/Palantir/EnvPayload/Board_Temperature`, `/Palantir/EnvPayload/Env_Payload_Packet`.

## When to extend `baseline.xml` instead

Almost never. Only if the addition is a true CCSDS-level protocol invariant (e.g., a new header encoding defined by a Blue Book revision) or is used by multiple feature files and cannot live in any single one. Payload parameters, command opcodes, alarm ranges — always under `features/`.

## References

- CCSDS 133.0-B-2, *Space Packet Protocol* (June 2020) — primary header wire format
- OMG XTCE 1.2 (2018-02-04) — MDB schema: https://www.omg.org/spec/XTCE/1.2/
- Yamcs MDB loaders: https://docs.yamcs.org/yamcs-server-manual/mdb/
