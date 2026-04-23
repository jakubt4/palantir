"""Visualization engines for telemetry DataFrames (PAL-201).

Pure engine functions: consume a time-indexed pandas DataFrame produced
by :mod:`palantir_analytics.export`, write a PNG to disk, return the
path. Kept free of CLI output per the engine/wrapper separation
directive (FEATURES.md §0) so a future GSaaS REST frontend can reuse
them to render dashboards server-side.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Headless backend — safe for tests, CI, and servers.

import matplotlib.pyplot as plt  # noqa: E402 — backend must be set first
import pandas as pd  # noqa: E402


def plot_altitude(
    df: pd.DataFrame,
    out_dir: Path,
    column: str = "Altitude",
) -> Path:
    """Render altitude vs. time to ``out_dir/altitude.png``.

    :param df:      Time-indexed DataFrame (DatetimeIndex) with an altitude column.
    :param out_dir: Directory for the PNG; created if missing.
    :param column:  Altitude column name; defaults to 'Altitude'.
    :return:        Path to the written PNG.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / "altitude.png"

    fig, ax = plt.subplots(figsize=(10, 4))
    try:
        ax.plot(df.index, df[column], linewidth=1.0)
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel("Altitude (m)")
        ax.set_title("Satellite altitude")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(png_path, dpi=120)
    finally:
        plt.close(fig)

    return png_path
