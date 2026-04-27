"""Ground-station registry — YAML config with CLI override resolution (PAL-203).

Schema::

    stations:
      <name>:
        lat_deg: float
        lon_deg: float
        alt_m:   float
    default_station: <name>   # optional

First consumer is PAL-202 (passes); PAL-101 ground track HMI and PAL-501
conjunction screening will adopt this same registry as they land. The
goal is to avoid each tool growing its own hardcoded station coordinates
before the pattern can be standardised.

Precedence order (high → low) applied by :func:`resolve_station`:

  1. Individual --station-{lat,lon,alt} override flags
  2. Named station picked via --station <name> from --config
  3. ``default_station`` declared in --config
  4. Built-in default (Banská Bystrica, FEATURES.md §1.4)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
import yaml


@dataclass(frozen=True)
class Station:
    """A ground station identified by name with WGS-84 coordinates."""

    name: str
    lat_deg: float
    lon_deg: float
    alt_m: float


@dataclass(frozen=True)
class StationConfig:
    """Parsed and validated stations.yaml contents."""

    stations: dict[str, Station]
    default_station: str | None


# Built-in fallback per FEATURES.md §1.4.
BUILTIN_DEFAULT = Station(
    name="banska-bystrica",
    lat_deg=48.7363,
    lon_deg=19.1462,
    alt_m=346.0,
)


def load_station_config(path: Path) -> StationConfig:
    """Load and validate a stations.yaml file.

    Raises :class:`typer.BadParameter` on malformed YAML, missing fields,
    out-of-range coordinates, or a ``default_station`` that does not
    appear in the ``stations`` mapping.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except (FileNotFoundError, yaml.YAMLError) as exc:
        raise typer.BadParameter(f"Cannot read {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise typer.BadParameter(f"{path}: top-level YAML must be a mapping")

    stations_raw = raw.get("stations", {})
    if not isinstance(stations_raw, dict):
        raise typer.BadParameter(f"{path}: 'stations' must be a mapping")

    stations: dict[str, Station] = {}
    for name, fields in stations_raw.items():
        if not isinstance(fields, dict):
            raise typer.BadParameter(f"{path}: station '{name}' must be a mapping")
        try:
            lat = float(fields["lat_deg"])
            lon = float(fields["lon_deg"])
            alt = float(fields["alt_m"])
        except (KeyError, TypeError, ValueError) as exc:
            raise typer.BadParameter(
                f"{path}: station '{name}' missing/invalid lat_deg/lon_deg/alt_m: {exc}"
            ) from exc
        _validate_coords(name, lat, lon, alt)
        stations[name] = Station(name=name, lat_deg=lat, lon_deg=lon, alt_m=alt)

    default_station = raw.get("default_station")
    if default_station is not None and default_station not in stations:
        raise typer.BadParameter(
            f"{path}: default_station '{default_station}' not in stations list"
        )

    return StationConfig(stations=stations, default_station=default_station)


def resolve_station(
    config: StationConfig | None,
    station_name: str | None,
    lat_override: float | None,
    lon_override: float | None,
    alt_override: float | None,
) -> Station:
    """Pick the active station, applying override precedence.

    Returns a :class:`Station` whose ``name`` reflects the base station
    chosen by name/default/built-in; per-axis overrides replace fields
    in place but do not invent a new name.
    """
    base = _select_base_station(config, station_name)

    final_lat = lat_override if lat_override is not None else base.lat_deg
    final_lon = lon_override if lon_override is not None else base.lon_deg
    final_alt = alt_override if alt_override is not None else base.alt_m
    _validate_coords(base.name, final_lat, final_lon, final_alt)

    return Station(name=base.name, lat_deg=final_lat, lon_deg=final_lon, alt_m=final_alt)


def _select_base_station(
    config: StationConfig | None,
    station_name: str | None,
) -> Station:
    """Apply the base-station precedence (name → default → built-in)."""
    if station_name is not None:
        if config is None:
            raise typer.BadParameter(f"--station '{station_name}' requires --config")
        if station_name not in config.stations:
            raise typer.BadParameter(
                f"Station '{station_name}' not in config; "
                f"available: {sorted(config.stations)}"
            )
        return config.stations[station_name]

    if config is not None:
        if config.default_station is not None:
            return config.stations[config.default_station]
        # Config provided but no default_station and no --station — warn and fall back.
        typer.secho(
            f"Warning: config has no default_station and --station not given; "
            f"falling back to built-in '{BUILTIN_DEFAULT.name}'.",
            fg=typer.colors.YELLOW,
            err=True,
        )

    return BUILTIN_DEFAULT


def _validate_coords(name: str, lat: float, lon: float, alt: float) -> None:
    """Validate coordinate ranges per FEATURES.md §1.5."""
    if not -90.0 <= lat <= 90.0:
        raise typer.BadParameter(f"Station '{name}': lat_deg={lat} out of [-90, 90]")
    if not -180.0 <= lon <= 180.0:
        raise typer.BadParameter(f"Station '{name}': lon_deg={lon} out of [-180, 180]")
    if not -500.0 <= alt <= 50_000.0:
        raise typer.BadParameter(
            f"Station '{name}': alt_m={alt} out of [-500, 50000]"
        )
