"""Unit tests for the plotting engines.

Uses matplotlib's Agg backend (set in plots.py on import) so tests run
headless in CI without a display server.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from palantir_analytics.plots import plot_altitude


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
