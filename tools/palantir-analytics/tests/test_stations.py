"""Unit tests for the ground-station registry (PAL-203).

Covers YAML loading + validation, plus the precedence chain
(individual flags > --station name > default_station > built-in).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from palantir_analytics.stations import (
    BUILTIN_DEFAULT,
    Station,
    StationConfig,
    load_station_config,
    resolve_station,
)


def _write(path: Path, body: str) -> Path:
    path.write_text(body)
    return path


# --- load_station_config -------------------------------------------------


def test_load_valid_config(tmp_path: Path) -> None:
    """Well-formed YAML loads into a StationConfig with all fields parsed."""
    cfg_path = _write(tmp_path / "stations.yaml", """
stations:
  banska-bystrica:
    lat_deg: 48.7363
    lon_deg: 19.1462
    alt_m: 346
  kosice:
    lat_deg: 48.7164
    lon_deg: 21.2611
    alt_m: 206
default_station: banska-bystrica
""")
    config = load_station_config(cfg_path)

    assert set(config.stations.keys()) == {"banska-bystrica", "kosice"}
    assert config.default_station == "banska-bystrica"
    assert config.stations["kosice"] == Station(
        name="kosice", lat_deg=48.7164, lon_deg=21.2611, alt_m=206.0
    )


def test_load_without_default_station(tmp_path: Path) -> None:
    """Missing default_station key parses to None (legal, triggers fallback later)."""
    cfg_path = _write(tmp_path / "stations.yaml", """
stations:
  bratislava:
    lat_deg: 48.1486
    lon_deg: 17.1077
    alt_m: 152
""")
    config = load_station_config(cfg_path)

    assert config.default_station is None
    assert "bratislava" in config.stations


def test_load_rejects_unknown_default_station(tmp_path: Path) -> None:
    """default_station that doesn't appear in stations: hard error."""
    cfg_path = _write(tmp_path / "stations.yaml", """
stations:
  bratislava: {lat_deg: 48.1486, lon_deg: 17.1077, alt_m: 152}
default_station: prague
""")
    with pytest.raises(typer.BadParameter, match="default_station 'prague'"):
        load_station_config(cfg_path)


def test_load_rejects_out_of_range_lat(tmp_path: Path) -> None:
    """Latitude outside [-90, 90] is rejected at load time."""
    cfg_path = _write(tmp_path / "stations.yaml", """
stations:
  bad: {lat_deg: 95.0, lon_deg: 0.0, alt_m: 0}
""")
    with pytest.raises(typer.BadParameter, match="lat_deg=95"):
        load_station_config(cfg_path)


def test_load_rejects_missing_field(tmp_path: Path) -> None:
    """Station entry missing alt_m raises BadParameter with the station name."""
    cfg_path = _write(tmp_path / "stations.yaml", """
stations:
  incomplete: {lat_deg: 0.0, lon_deg: 0.0}
""")
    with pytest.raises(typer.BadParameter, match="incomplete"):
        load_station_config(cfg_path)


def test_load_rejects_malformed_yaml(tmp_path: Path) -> None:
    """Genuinely broken YAML surfaces as a typer.BadParameter, not a YAMLError."""
    cfg_path = _write(tmp_path / "stations.yaml", "stations: [unclosed\n  - foo:")
    with pytest.raises(typer.BadParameter):
        load_station_config(cfg_path)


# --- resolve_station precedence -----------------------------------------


def _config(default: str | None = None) -> StationConfig:
    return StationConfig(
        stations={
            "banska-bystrica": Station("banska-bystrica", 48.7363, 19.1462, 346.0),
            "kosice": Station("kosice", 48.7164, 21.2611, 206.0),
        },
        default_station=default,
    )


def test_resolve_no_config_falls_back_to_builtin() -> None:
    """No config + no overrides → built-in Banská Bystrica default."""
    result = resolve_station(None, None, None, None, None)
    assert result == BUILTIN_DEFAULT


def test_resolve_named_station_from_config() -> None:
    """--station <name> picks that station from the config."""
    result = resolve_station(_config("banska-bystrica"), "kosice", None, None, None)
    assert result.name == "kosice"
    assert result.lat_deg == 48.7164


def test_resolve_default_station_from_config() -> None:
    """No --station + config has default_station → that default is used."""
    result = resolve_station(_config("kosice"), None, None, None, None)
    assert result.name == "kosice"


def test_resolve_no_default_falls_back_to_builtin(capsys: pytest.CaptureFixture[str]) -> None:
    """Config without default_station + no --station → builtin + stderr warning."""
    result = resolve_station(_config(default=None), None, None, None, None)
    assert result == BUILTIN_DEFAULT
    captured = capsys.readouterr()
    assert "Warning" in captured.err
    assert "default_station" in captured.err


def test_resolve_individual_overrides_win() -> None:
    """--station-lat replaces only lat; lon/alt come from base station."""
    result = resolve_station(_config("kosice"), None, lat_override=50.0,
                             lon_override=None, alt_override=None)
    assert result.name == "kosice"
    assert result.lat_deg == 50.0
    assert result.lon_deg == 21.2611  # from kosice
    assert result.alt_m == 206.0


def test_resolve_unknown_station_name_rejected() -> None:
    """--station <name> not in config raises BadParameter listing available names."""
    with pytest.raises(typer.BadParameter, match="not in config"):
        resolve_station(_config("kosice"), "prague", None, None, None)


def test_resolve_named_station_without_config_rejected() -> None:
    """--station with no --config is a usage error."""
    with pytest.raises(typer.BadParameter, match="requires --config"):
        resolve_station(None, "kosice", None, None, None)


def test_resolve_override_validates_range() -> None:
    """--station-lat 95° is rejected (out of [-90, 90])."""
    with pytest.raises(typer.BadParameter, match="lat_deg=95"):
        resolve_station(_config("kosice"), None, lat_override=95.0,
                        lon_override=None, alt_override=None)
