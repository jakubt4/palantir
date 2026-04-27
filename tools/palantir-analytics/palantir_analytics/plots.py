"""Visualization engines for telemetry DataFrames (PAL-201, PAL-202).

Pure engine functions: consume a time-indexed pandas Series/DataFrame
plus optional metadata (pass list, station coordinates, units), write a
PNG to disk, return the path. Kept free of CLI output per the
engine/wrapper separation directive (FEATURES.md §0) so a future GSaaS
REST frontend can reuse them to render dashboards server-side.
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

from palantir_analytics.passes import PassWindow  # noqa: E402


def plot_altitude(
    df: pd.DataFrame,
    out_dir: Path,
    column: str = "Altitude",
    unit: str | None = None,
) -> Path:
    """Render altitude vs. time to ``out_dir/altitude.png``.

    :param df:      Time-indexed DataFrame (DatetimeIndex) with an altitude column.
    :param out_dir: Directory for the PNG; created if missing.
    :param column:  Altitude column name; defaults to 'Altitude'.
    :param unit:    Unit string from the XTCE MDB (e.g. 'km'); appended to the
                    Y-axis label as 'Altitude (km)'. None → no unit suffix.
    :return:        Path to the written PNG.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / "altitude.png"

    ylabel = f"Altitude ({unit})" if unit else "Altitude"

    fig, ax = plt.subplots(figsize=(10, 4))
    try:
        ax.plot(df.index, df[column], linewidth=1.0)
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel(ylabel)
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


def plot_visibility_timeline(
    elevation_series: pd.Series,
    passes: list[PassWindow],
    out_dir: Path,
    min_elevation_deg: float = 5.0,
) -> Path:
    """Render elevation vs. time with AOS/LOS markers (PAL-202).

    Y-axis clipped to ``[-10°, 90°]`` so passes are readable; satellites
    on the far side of Earth give elevations down to ~-90° which would
    flatten the visible region.

    :param elevation_series:  tz-aware UTC index, elevation in degrees.
    :param passes:            Detected pass windows; AOS/LOS marked as
                              vertical lines, in-pass elevation drawn
                              in colour over the grey full-trace.
    :param out_dir:           Directory for the PNG; created if missing.
    :param min_elevation_deg: Threshold drawn as a horizontal dotted line.
    :return:                  Path to the written PNG.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / "visibility_timeline.png"

    fig, ax = plt.subplots(figsize=(14, 5))
    try:
        ax.plot(elevation_series.index, elevation_series.values,
                linewidth=0.5, color="lightgray", label="elevation")

        for p in passes:
            mask = (elevation_series.index >= p.aos_time) & (elevation_series.index <= p.los_time)
            ax.plot(elevation_series.index[mask], elevation_series.values[mask],
                    linewidth=1.5, color="C0")
            ax.axvline(p.aos_time, color="green", linestyle="--", alpha=0.6, linewidth=0.6)
            ax.axvline(p.los_time, color="red", linestyle="--", alpha=0.6, linewidth=0.6)

        ax.axhline(min_elevation_deg, color="orange", linestyle=":",
                   alpha=0.7, label=f"min elevation ({min_elevation_deg}°)")
        ax.set_ylim(-10, 90)
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel("Elevation (degrees)")
        ax.set_title(f"Visibility timeline — {len(passes)} pass(es) detected")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right")
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(png_path, dpi=120)
    finally:
        plt.close(fig)

    return png_path
