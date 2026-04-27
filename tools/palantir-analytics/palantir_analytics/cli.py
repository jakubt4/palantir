"""Palantir analytics CLI — Typer app with subcommand routing."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer

from palantir_analytics.export import run_export
from palantir_analytics.passes import compute_passes
from palantir_analytics.plots import plot_altitude, plot_ground_track
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
    plots: bool = typer.Option(
        True,
        "--plots/--no-plots",
        help="Also render altitude.png and ground_track.png alongside the CSV.",
    ),
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

    if plots and result.sample_count > 0:
        altitude_param = next(
            (p for p in parameter if p.rsplit("/", 1)[-1] == "Altitude"),
            None,
        )
        altitude_unit = result.units.get(altitude_param) if altitude_param else None
        altitude_png = plot_altitude(result.df, out, unit=altitude_unit)
        ground_track_png = plot_ground_track(result.df, out)
        typer.echo(f"Wrote {altitude_png}")
        typer.echo(f"Wrote {ground_track_png}")


@app.command()
def passes(
    start: str = typer.Option(..., "--start", help="Window start, ISO 8601 with tz."),
    stop: str = typer.Option(..., "--stop", help="Window stop, ISO 8601 with tz."),
    station_lat: float = typer.Option(
        48.7363, "--station-lat", help="Station latitude °N (default Banská Bystrica)."
    ),
    station_lon: float = typer.Option(
        19.1462, "--station-lon", help="Station longitude °E (default Banská Bystrica)."
    ),
    station_alt: float = typer.Option(
        346.0, "--station-alt", help="Station altitude in metres (default Banská Bystrica)."
    ),
    min_elevation: float = typer.Option(
        5.0, "--min-elevation", help="AOS/LOS elevation threshold in degrees."
    ),
    yamcs_address: str = typer.Option("localhost:8090", "--yamcs-address"),
    yamcs_instance: str = typer.Option("palantir", "--yamcs-instance"),
    out: Path = typer.Option(Path("./out"), "--out", help="Output directory."),
) -> None:
    """Predict ground-station visibility passes from archived telemetry (PAL-202)."""
    start_dt = _parse_iso_utc(start)
    stop_dt = _parse_iso_utc(stop)

    archive = PalantirArchive(address=yamcs_address, instance=yamcs_instance)
    report = compute_passes(
        archive=archive,
        station_lat_deg=station_lat,
        station_lon_deg=station_lon,
        station_alt_m=station_alt,
        start=start_dt,
        stop=stop_dt,
        out_dir=out,
        min_elevation_deg=min_elevation,
    )

    if not report.passes:
        typer.secho(
            f"Warning: no passes >= {min_elevation}° in the requested window.",
            fg=typer.colors.YELLOW,
            err=True,
        )

    typer.echo(f"Wrote {len(report.passes)} passes to {report.csv_path}")
    for p in report.passes:
        typer.echo(
            f"  Pass {p.pass_number}: AOS {p.aos_time.isoformat()} -> "
            f"LOS {p.los_time.isoformat()}, "
            f"max el {p.max_elevation_deg:.1f}°, "
            f"duration {p.duration_seconds:.0f} s"
        )


if __name__ == "__main__":
    app()
