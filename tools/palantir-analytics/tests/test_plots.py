"""Unit tests for the plotting engines.

Uses matplotlib's Agg backend (set in plots.py on import) so tests run
headless in CI without a display server.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from palantir_analytics.passes import PassWindow
from palantir_analytics.plots import (
    plot_altitude,
    plot_ground_track,
    plot_visibility_timeline,
)


def _tz_utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_plot_altitude_writes_png(tmp_path: Path) -> None:
    """Engine writes a non-empty PNG to out_dir and returns its path."""
    df = pd.DataFrame(
        {"Altitude": [408000.0, 408100.0, 408050.0]},
        index=pd.DatetimeIndex(
            [_tz_utc(2026, 4, 22, 10, 0, 0),
             _tz_utc(2026, 4, 22, 10, 0, 1),
             _tz_utc(2026, 4, 22, 10, 0, 2)],
            name="timestamp",
        ),
    )

    png_path = plot_altitude(df, tmp_path)

    assert png_path == tmp_path / "altitude.png"
    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_plot_altitude_custom_column(tmp_path: Path) -> None:
    """Caller can override the altitude column name."""
    df = pd.DataFrame(
        {"Alt_m": [408000.0, 408100.0]},
        index=pd.DatetimeIndex(
            [_tz_utc(2026, 4, 22, 10, 0, 0),
             _tz_utc(2026, 4, 22, 10, 0, 1)],
            name="timestamp",
        ),
    )

    png_path = plot_altitude(df, tmp_path, column="Alt_m")

    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_plot_ground_track_writes_png(tmp_path: Path) -> None:
    """Engine writes a non-empty PNG and returns its path."""
    df = pd.DataFrame(
        {"Latitude": [48.7, 48.8, 48.9], "Longitude": [19.1, 19.2, 19.3]},
        index=pd.DatetimeIndex(
            [_tz_utc(2026, 4, 22, 10, 0, 0),
             _tz_utc(2026, 4, 22, 10, 0, 1),
             _tz_utc(2026, 4, 22, 10, 0, 2)],
            name="timestamp",
        ),
    )

    png_path = plot_ground_track(df, tmp_path)

    assert png_path == tmp_path / "ground_track.png"
    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_plot_ground_track_handles_antimeridian(tmp_path: Path) -> None:
    """Dateline crossing (|Δlon| > 180°) renders without crashing."""
    df = pd.DataFrame(
        {
            "Latitude": [0.0, 0.0, 0.0, 0.0],
            "Longitude": [170.0, 179.0, -179.0, -170.0],
        },
        index=pd.DatetimeIndex(
            [_tz_utc(2026, 4, 22, h, 0, 0) for h in (10, 11, 12, 13)],
            name="timestamp",
        ),
    )

    png_path = plot_ground_track(df, tmp_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_plot_visibility_timeline_with_passes(tmp_path: Path) -> None:
    """Engine renders elevation series + AOS/LOS markers as a PNG."""
    times = pd.DatetimeIndex(
        [_tz_utc(2026, 4, 27, 12, 0, i) for i in range(60)],
        name="timestamp",
    )
    # Synthetic elevation: sub-horizon → peak ~70° → sub-horizon.
    values = [-30 + abs(30 - i) * (-1) + (40 if 20 <= i <= 40 else 0) for i in range(60)]
    elevation = pd.Series(values, index=times, name="elevation_deg", dtype=float)
    passes = [
        PassWindow(
            pass_number=1,
            aos_time=times[20].to_pydatetime(),
            los_time=times[40].to_pydatetime(),
            max_elevation_deg=40.0,
            duration_seconds=20.0,
        )
    ]

    png_path = plot_visibility_timeline(elevation, passes, tmp_path, min_elevation_deg=5.0)

    assert png_path == tmp_path / "visibility_timeline.png"
    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_plot_visibility_timeline_no_passes(tmp_path: Path) -> None:
    """Empty passes list still produces a valid plot of the elevation trace."""
    times = pd.DatetimeIndex(
        [_tz_utc(2026, 4, 27, 12, 0, i) for i in range(30)],
        name="timestamp",
    )
    elevation = pd.Series([-30.0] * 30, index=times, name="elevation_deg")

    png_path = plot_visibility_timeline(elevation, [], tmp_path, min_elevation_deg=5.0)

    assert png_path.exists()
    assert png_path.stat().st_size > 0
