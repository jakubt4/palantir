# palantir-analytics

Python CLI for Palantir ground-segment analytics — telemetry export, pass prediction, trend analysis against the Yamcs archive.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
cd tools/palantir-analytics
uv sync                              # install deps into .venv (Python 3.12)
uv run palantir-analytics --help     # list subcommands
```

## Subcommands

| Command | Ticket | Status |
|---|---|---|
| `export` | PAL-201 | stub |
| `passes` | PAL-202 | stub |

## Development

```bash
uv sync --group dev              # install dev deps (pytest, responses)
uv run pytest                    # run the test suite
```

## Target Yamcs

Defaults: `http://localhost:8090`, instance `palantir`. Override with `--yamcs-url` / `--yamcs-instance` on any subcommand once implemented.
