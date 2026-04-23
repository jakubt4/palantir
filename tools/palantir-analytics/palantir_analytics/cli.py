"""Palantir analytics CLI — Typer app with subcommand routing."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer

from palantir_analytics.export import run_export
from palantir_analytics.yamcs_client import PalantirArchive

app = typer.Typer(
    name="palantir-analytics",
    help="Palantir ground-segment analytics — export, passes, trends.",
    no_args_is_help=True,
)

DEFAULT_NAV_PARAMETERS = [
    "/Palantir/Latitude",
    "/Palantir/Longitude",
    "/Palantir/Altitude",
]


def _parse_iso_utc(value: str) -> datetime:
    """Parse ISO 8601 timestamp; reject naive (timezone-less) values."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise typer.BadParameter(
            f"{value!r} is missing a timezone offset (e.g. '2026-04-22T10:00:00+00:00')"
        )
    return parsed


@app.command()
def export(
    start: str = typer.Option(..., "--start", help="Window start, ISO 8601 with tz."),
    stop: str = typer.Option(..., "--stop", help="Window stop, ISO 8601 with tz."),
    parameter: list[str] = typer.Option(
        DEFAULT_NAV_PARAMETERS,
        "--parameter",
        "-p",
        help="Fully-qualified XTCE parameter path (repeatable).",
    ),
    yamcs_address: str = typer.Option("localhost:8090", "--yamcs-address"),
    yamcs_instance: str = typer.Option("palantir", "--yamcs-instance"),
    out: Path = typer.Option(Path("./export"), "--out", help="Output directory."),
) -> None:
    """Dump archived telemetry to CSV + plots (PAL-201)."""
    start_dt = _parse_iso_utc(start)
    stop_dt = _parse_iso_utc(stop)

    archive = PalantirArchive(address=yamcs_address, instance=yamcs_instance)
    result = run_export(
        archive=archive,
        parameters=parameter,
        start=start_dt,
        stop=stop_dt,
        out_dir=out,
    )

    if result.sample_count == 0:
        typer.secho(
            "Warning: no samples in the requested window.",
            fg=typer.colors.YELLOW,
            err=True,
        )

    typer.echo(f"Wrote {result.sample_count} rows to {result.csv_path}")
    for param, stats in result.stats.items():
        typer.echo(
            f"  {param}: n={stats.count}, "
            f"min={stats.min:.3f}, max={stats.max:.3f}, "
            f"mean={stats.mean:.3f}, std={stats.std:.3f}"
        )


@app.command()
def passes() -> None:
    """Predict ground-station visibility passes (PAL-202)."""
    typer.echo("passes: not implemented yet")


if __name__ == "__main__":
    app()
