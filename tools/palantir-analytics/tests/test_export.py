"""Unit tests for the export engine.

MagicMock replaces PalantirArchive so tests run without a live Yamcs.
``tmp_path`` is pytest's built-in fixture for a per-test temp directory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from palantir_analytics.export import ParameterStats, run_export
from palantir_analytics.yamcs_client import ParameterSample


def _sample(t: datetime, v: float) -> ParameterSample:
    return ParameterSample(generation_time=t, value=v)


def test_writes_csv_and_returns_stats(tmp_path: Path) -> None:
    """Engine queries archive, writes CSV, returns per-parameter stats."""
    archive = MagicMock()
    t0 = datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 4, 22, 10, 0, 1, tzinfo=timezone.utc)
    archive.list_parameter_values.side_effect = [
        iter([_sample(t0, 10.0), _sample(t1, 20.0)]),     # /Palantir/Latitude
        iter([_sample(t0, 100.0), _sample(t1, 200.0)]),   # /Palantir/Longitude
    ]

    result = run_export(
        archive=archive,
        parameters=["/Palantir/Latitude", "/Palantir/Longitude"],
        start=datetime(2026, 4, 22, 9, tzinfo=timezone.utc),
        stop=datetime(2026, 4, 22, 11, tzinfo=timezone.utc),
        out_dir=tmp_path,
    )

    assert result.sample_count == 2
    assert result.csv_path == tmp_path / "telemetry_export.csv"
    assert result.csv_path.exists()

    assert result.stats["/Palantir/Latitude"] == ParameterStats(
        min=10.0, max=20.0, mean=15.0, std=pytest.approx(7.0710678), count=2
    )
    assert result.stats["/Palantir/Longitude"] == ParameterStats(
        min=100.0, max=200.0, mean=150.0, std=pytest.approx(70.710678), count=2
    )

    csv = result.csv_path.read_text()
    assert "timestamp,Latitude,Longitude" in csv
    assert "10.0" in csv and "100.0" in csv

    # df exposed for downstream plot engines; 2 timestamps × 2 parameters.
    assert result.df.shape == (2, 2)
    assert list(result.df.columns) == ["Latitude", "Longitude"]


def test_empty_window_returns_zero_count_and_header_only_csv(tmp_path: Path) -> None:
    """No samples → sample_count=0 and the CSV still writes header row."""
    archive = MagicMock()
    archive.list_parameter_values.side_effect = [iter([]), iter([])]

    result = run_export(
        archive=archive,
        parameters=["/Palantir/Latitude", "/Palantir/Longitude"],
        start=datetime(2026, 4, 22, 9, tzinfo=timezone.utc),
        stop=datetime(2026, 4, 22, 11, tzinfo=timezone.utc),
        out_dir=tmp_path,
    )

    assert result.sample_count == 0
    assert result.csv_path.exists()
    assert result.stats["/Palantir/Latitude"].count == 0


def test_mismatched_timestamps_outer_join_with_nan(tmp_path: Path) -> None:
    """Parameters sampled at different instants produce outer-joined rows."""
    archive = MagicMock()
    t0 = datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 4, 22, 10, 0, 1, tzinfo=timezone.utc)
    archive.list_parameter_values.side_effect = [
        iter([_sample(t0, 10.0)]),       # Latitude at t0 only
        iter([_sample(t1, 200.0)]),      # Longitude at t1 only
    ]

    result = run_export(
        archive=archive,
        parameters=["/Palantir/Latitude", "/Palantir/Longitude"],
        start=datetime(2026, 4, 22, 9, tzinfo=timezone.utc),
        stop=datetime(2026, 4, 22, 11, tzinfo=timezone.utc),
        out_dir=tmp_path,
    )

    # Two rows (one per unique timestamp); each parameter has 1 non-NaN value.
    assert result.sample_count == 2
    assert result.stats["/Palantir/Latitude"].count == 1
    assert result.stats["/Palantir/Longitude"].count == 1
