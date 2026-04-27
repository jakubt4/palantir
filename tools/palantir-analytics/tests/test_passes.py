"""Unit tests for the pass-prediction engine.

MagicMock replaces PalantirArchive so tests run without a live Yamcs.
Synthetic satellite tracks exercise both the geometric model and the
pass-detection state machine (full pass, no pass, incomplete edges,
empty archive, threshold filtering).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

from palantir_analytics.passes import compute_passes
from palantir_analytics.yamcs_client import ParameterSample


def _nav_archive(times, lats, lons, alts):
    """Build a MagicMock archive whose three nav queries return aligned tracks."""
    archive = MagicMock()
    archive.list_parameter_values.side_effect = [
        iter([ParameterSample(t, v) for t, v in zip(times, lats)]),
        iter([ParameterSample(t, v) for t, v in zip(times, lons)]),
        iter([ParameterSample(t, v) for t, v in zip(times, alts)]),
    ]
    return archive


def _track(start_time, n, lat_start, lat_stop, lon=0.0, alt_km=408.0):
    """Linear satellite track sampled at 1 Hz from lat_start to lat_stop."""
    times = [start_time + timedelta(seconds=i) for i in range(n)]
    lats = [lat_start + (lat_stop - lat_start) * i / (n - 1) for i in range(n)]
    return times, lats, [lon] * n, [alt_km] * n


def test_overhead_pass_detected(tmp_path: Path) -> None:
    """Sub-satellite track passing through (0°,0°) at 408 km yields one pass."""
    t0 = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    times, lats, lons, alts = _track(t0, n=51, lat_start=-25.0, lat_stop=25.0)
    archive = _nav_archive(times, lats, lons, alts)

    report = compute_passes(
        archive=archive,
        station_lat_deg=0.0, station_lon_deg=0.0, station_alt_m=0.0,
        start=t0, stop=t0 + timedelta(seconds=60),
        out_dir=tmp_path, min_elevation_deg=5.0,
    )

    assert len(report.passes) == 1
    p = report.passes[0]
    assert p.pass_number == 1
    assert p.max_elevation_deg > 80.0  # near zenith
    assert p.aos_time < p.los_time
    assert p.duration_seconds > 0


def test_no_pass_when_satellite_far(tmp_path: Path) -> None:
    """Same equatorial track is never visible from a polar station."""
    t0 = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    times, lats, lons, alts = _track(t0, n=51, lat_start=-25.0, lat_stop=25.0)
    archive = _nav_archive(times, lats, lons, alts)

    report = compute_passes(
        archive=archive,
        station_lat_deg=80.0, station_lon_deg=0.0, station_alt_m=0.0,
        start=t0, stop=t0 + timedelta(seconds=60),
        out_dir=tmp_path, min_elevation_deg=5.0,
    )

    assert report.passes == []


def test_incomplete_leading_pass_dropped(tmp_path: Path) -> None:
    """Recording starts with satellite already overhead — no AOS, drop the partial pass."""
    t0 = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    times, lats, lons, alts = _track(t0, n=51, lat_start=0.0, lat_stop=30.0)
    archive = _nav_archive(times, lats, lons, alts)

    report = compute_passes(
        archive=archive,
        station_lat_deg=0.0, station_lon_deg=0.0, station_alt_m=0.0,
        start=t0, stop=t0 + timedelta(seconds=60),
        out_dir=tmp_path, min_elevation_deg=5.0,
    )

    assert report.passes == []


def test_incomplete_trailing_pass_dropped(tmp_path: Path) -> None:
    """Recording ends with satellite overhead — no LOS, drop the partial pass."""
    t0 = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    times, lats, lons, alts = _track(t0, n=51, lat_start=30.0, lat_stop=0.0)
    archive = _nav_archive(times, lats, lons, alts)

    report = compute_passes(
        archive=archive,
        station_lat_deg=0.0, station_lon_deg=0.0, station_alt_m=0.0,
        start=t0, stop=t0 + timedelta(seconds=60),
        out_dir=tmp_path, min_elevation_deg=5.0,
    )

    assert report.passes == []


def test_empty_archive_yields_empty_report(tmp_path: Path) -> None:
    """No samples → empty pass list and a header-only CSV."""
    archive = MagicMock()
    archive.list_parameter_values.side_effect = [iter([]), iter([]), iter([])]
    t0 = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)

    report = compute_passes(
        archive=archive,
        station_lat_deg=0.0, station_lon_deg=0.0, station_alt_m=0.0,
        start=t0, stop=t0 + timedelta(seconds=60),
        out_dir=tmp_path, min_elevation_deg=5.0,
    )

    assert report.passes == []
    assert report.csv_path.exists()
    csv = report.csv_path.read_text()
    assert "pass_number,aos_time,los_time,max_elevation_deg,duration_seconds" in csv


def test_high_min_elevation_rejects_pass(tmp_path: Path) -> None:
    """Even an overhead pass is rejected when min_elevation exceeds the peak."""
    t0 = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    times, lats, lons, alts = _track(t0, n=51, lat_start=-25.0, lat_stop=25.0)
    archive = _nav_archive(times, lats, lons, alts)

    report = compute_passes(
        archive=archive,
        station_lat_deg=0.0, station_lon_deg=0.0, station_alt_m=0.0,
        start=t0, stop=t0 + timedelta(seconds=60),
        out_dir=tmp_path, min_elevation_deg=95.0,  # impossible — geometric max is 90°
    )

    assert report.passes == []
