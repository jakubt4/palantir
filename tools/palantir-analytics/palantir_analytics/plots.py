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
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import cartopy.crs as ccrs  # noqa: E402
import cartopy.feature as cfeature  # noqa: E402


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


def plot_ground_track(
    df: pd.DataFrame,
    out_dir: Path,
    lat_column: str = "Latitude",
    lon_column: str = "Longitude",
) -> Path:
    """Render satellite ground track to ``out_dir/ground_track.png``.

    Projection: Plate Carrée (equirectangular). Antimeridian crossings
    (|Δlon| > 180°) are broken with NaN so the track doesn't stroke a
    spurious horizontal line across the whole map.

    :param df:         Time-indexed DataFrame with lat/lon columns in degrees.
    :param out_dir:    Directory for the PNG; created if missing.
    :param lat_column: Latitude column name (WGS-84, degrees north).
    :param lon_column: Longitude column name (WGS-84, degrees east).
    :return:           Path to the written PNG.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / "ground_track.png"

    lat = df[lat_column].to_numpy(dtype=float)
    lon = df[lon_column].to_numpy(dtype=float)

    # Split at dateline crossings so cartopy doesn't draw +180° → -180°.
    jumps = np.where(np.abs(np.diff(lon)) > 180)[0] + 1
    lat_plot = np.insert(lat, jumps, np.nan)
    lon_plot = np.insert(lon, jumps, np.nan)

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    try:
        ax.set_global()
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.5)
        ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)
        ax.plot(lon_plot, lat_plot, linewidth=1.0, transform=ccrs.PlateCarree())
        ax.set_title("Satellite ground track")
        fig.tight_layout()
        fig.savefig(png_path, dpi=120)
    finally:
        plt.close(fig)

    return png_path
