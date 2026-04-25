# palantir-analytics

Python CLI for Palantir ground-segment analytics — telemetry export, pass prediction, trend analysis against the Yamcs archive.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/) and a running Palantir stack (see project root README — `docker compose up --build`).

```bash
cd tools/palantir-analytics
uv sync                              # install deps into .venv (Python 3.12)
uv run palantir-analytics --help     # list subcommands
```

## Commands

### `export` — PAL-201 (implemented)

Dump a time window from the Yamcs parameter archive to CSV, plus altitude and ground-track PNGs.

```bash
uv run palantir-analytics export \
  --start "2026-04-23T20:35:00+00:00" \
  --stop  "2026-04-23T20:50:00+00:00" \
  --out   ./out
```

**Outputs** (written into `--out`):

| File | Content |
|---|---|
| `telemetry_export.csv` | Outer-joined by timestamp (UTC ISO 8601), one column per parameter |
| `altitude.png` | Altitude vs. time; Y-axis unit sourced from the XTCE UnitSet |
| `ground_track.png` | PlateCarrée map with coastlines; antimeridian-aware |

**Key flags:**

| Flag | Default | Notes |
|---|---|---|
| `--start` / `--stop` | required | ISO 8601 **with timezone offset** (naive rejected — use `Z` or `+00:00`) |
| `--parameter` / `-p` | `/Palantir/{Latitude,Longitude,Altitude}` | Repeatable; fully-qualified XTCE path |
| `--yamcs-address` | `localhost:8090` | Host:port of the Yamcs server |
| `--yamcs-instance` | `palantir` | Yamcs instance name |
| `--out` | `./export` | Output directory (created if missing) |
| `--plots` / `--no-plots` | `--plots` | Skip PNG rendering for CSV-only pipelines |

Run `uv run palantir-analytics export --help` for the full list.

### `passes` — PAL-202 (not yet implemented)

AOS/LOS pass predictions for a ground station. Stub today.

## Limitations

- **Not real-time.** This is a window query against the parameter archive. For a live feed, subscribe to Yamcs over WebSocket directly.
- **Memory-bound.** All samples are joined into a single in-memory DataFrame. Fine for hours of 1 Hz telemetry; won't scale to days × hundreds of parameters without chunked streaming.
- **Single-tenant.** Assumes one unauthenticated Yamcs instance — appropriate for the PoC, not for multi-tenant deployment.

## Development

```bash
uv sync --group dev              # install dev deps (pytest)
uv run pytest                    # run the test suite
```

## Architecture

Engine / wrapper separation (see project-root `FEATURES.md` §0). Pure-function engines live in `palantir_analytics/`:

- `yamcs_client.py` — `PalantirArchive` wraps yamcs-client's archive + MDB APIs, returning domain types (`ParameterSample`, unit strings).
- `export.py` — `run_export()` returns `ExportResult` (CSV path, stats, joined DataFrame, units from XTCE).
- `plots.py` — `plot_altitude()` / `plot_ground_track()` consume a DataFrame, return a PNG path.
- `cli.py` — thin Typer layer over the engines; no business logic.

The engines stay reusable for a future GSaaS REST frontend: the same functions that back the CLI will back the server.
