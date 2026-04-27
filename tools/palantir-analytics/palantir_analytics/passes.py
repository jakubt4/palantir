"""Pass-prediction engine — historical AOS/LOS detection (PAL-202).

Pure engine: queries archived `(latitude, longitude, altitude)` from
PalantirArchive, applies a spherical-Earth visibility model, and writes
``pass_report.csv`` with detected pass windows.

Geometric model (FEATURES.md §1.4):
  - Haversine central angle ``γ`` between station and sub-satellite point
  - Elevation ``el = atan2(cos γ − R_E/(R_E + h_sat), sin γ)``
  - AOS = ``el`` rises through ``el_min``; LOS = falls back through it.

Spherical Earth (``R_E ≈ 6371 km``) is fit-for-purpose for PoC.
Operational schedulers eventually swap to ellipsoidal Earth + atmospheric
refraction correction — see §6 Phase F item 1.

Engine free of CLI output per the engine/wrapper separation directive
(FEATURES.md §0): a future GSaaS REST wrapper reuses this as-is.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from palantir_analytics.yamcs_client import PalantirArchive

R_EARTH_KM = 6371.0  # Mean Earth radius (FEATURES.md §1.4).


@dataclass(frozen=True)
class PassWindow:
    """One AOS/LOS pass over the ground station."""

    pass_number: int
    aos_time: datetime
    los_time: datetime
    max_elevation_deg: float
    duration_seconds: float


@dataclass(frozen=True)
class PassReport:
    """Result envelope from :func:`compute_passes`.

    ``elevation_series`` is exposed (excluded from __eq__/__repr__) so the
    follow-up visibility-timeline plot can render without re-querying.
    """

    csv_path: Path
    passes: list[PassWindow]
    elevation_series: pd.Series = field(compare=False, repr=False)


def compute_passes(
    archive: PalantirArchive,
    station_lat_deg: float,
    station_lon_deg: float,
    station_alt_m: float,
    start: datetime,
    stop: datetime,
    out_dir: Path,
    min_elevation_deg: float = 5.0,
) -> PassReport:
    """Detect AOS/LOS pass windows for the station over ``[start, stop)``.

    :param archive:           PalantirArchive connected to the target Yamcs.
    :param station_lat_deg:   Station latitude (WGS-84 degrees north).
    :param station_lon_deg:   Station longitude (WGS-84 degrees east).
    :param station_alt_m:     Station altitude in metres (currently unused —
                              spherical model assumes h_gs ≪ h_sat; reserved
                              for the future ellipsoidal upgrade).
    :param start:             Window start, timezone-aware.
    :param stop:              Window stop, timezone-aware.
    :param out_dir:           Directory for ``pass_report.csv``; created if missing.
    :param min_elevation_deg: AOS/LOS threshold (default 5° — see FEATURES.md §1.4).
    :return:                  :class:`PassReport` with CSV path, pass list, elevation series.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    df = _join_nav(archive, start, stop)
    elevation_series = _elevation_series(df, station_lat_deg, station_lon_deg)
    passes = _detect_passes(elevation_series, min_elevation_deg)

    csv_path = out_dir / "pass_report.csv"
    _write_pass_report(csv_path, passes)

    return PassReport(csv_path=csv_path, passes=passes, elevation_series=elevation_series)


def _join_nav(
    archive: PalantirArchive,
    start: datetime,
    stop: datetime,
) -> pd.DataFrame:
    """Query the three nav parameters and outer-join into a UTC-indexed frame.

    Drops rows where any of (Latitude, Longitude, Altitude) is NaN — pass
    detection needs all three. In practice they share generation_time
    because they ride in the same Palantir_Nav_Packet (APID 100), so NaN
    rows only appear under packet loss.
    """
    series_by_column: dict[str, pd.Series] = {}
    for parameter in ("/Palantir/Latitude", "/Palantir/Longitude", "/Palantir/Altitude"):
        samples = list(archive.list_parameter_values(parameter, start, stop))
        column = parameter.rsplit("/", 1)[-1]
        series_by_column[column] = pd.Series(
            data=[s.value for s in samples],
            index=pd.DatetimeIndex(
                [s.generation_time for s in samples], name="timestamp"
            ),
            name=column,
        )

    df = pd.concat(series_by_column.values(), axis=1).sort_index().dropna()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def _elevation_series(
    df: pd.DataFrame,
    station_lat_deg: float,
    station_lon_deg: float,
) -> pd.Series:
    """Vectorised Haversine + elevation formula. Returns degrees."""
    if df.empty:
        return pd.Series([], index=df.index, name="elevation_deg", dtype=float)

    phi_gs = math.radians(station_lat_deg)
    lambda_gs = math.radians(station_lon_deg)
    phi_ss = np.radians(df["Latitude"].to_numpy())
    lambda_ss = np.radians(df["Longitude"].to_numpy())
    h_sat_km = df["Altitude"].to_numpy()

    dphi = phi_ss - phi_gs
    dlambda = lambda_ss - lambda_gs
    a = np.sin(dphi / 2) ** 2 + math.cos(phi_gs) * np.cos(phi_ss) * np.sin(dlambda / 2) ** 2
    gamma = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    el_rad = np.arctan2(
        np.cos(gamma) - R_EARTH_KM / (R_EARTH_KM + h_sat_km),
        np.sin(gamma),
    )
    return pd.Series(np.degrees(el_rad), index=df.index, name="elevation_deg")


def _detect_passes(
    elevation_series: pd.Series,
    min_elevation_deg: float,
) -> list[PassWindow]:
    """Find runs where elevation > threshold; emit one PassWindow per run.

    Incomplete passes at window edges (recording starts or ends in-pass)
    are dropped — only fully bounded AOS→LOS pairs are emitted.
    """
    if elevation_series.empty:
        return []

    above = elevation_series > min_elevation_deg
    transitions = above.astype(int).diff()
    aos_idx = elevation_series.index[transitions == 1].tolist()
    los_idx = elevation_series.index[transitions == -1].tolist()

    # If recording starts in pass: leading LOS has no matching AOS — drop.
    if los_idx and aos_idx and los_idx[0] < aos_idx[0]:
        los_idx = los_idx[1:]
    # Truncate to matched pairs — handles both incomplete-trailing (extra AOS)
    # and the lone-LOS-without-AOS case where the recording began in-pass and
    # never had a fresh AOS afterwards.
    paired = min(len(aos_idx), len(los_idx))
    aos_idx = aos_idx[:paired]
    los_idx = los_idx[:paired]

    passes: list[PassWindow] = []
    for n, (aos, los) in enumerate(zip(aos_idx, los_idx, strict=True), start=1):
        window = elevation_series.loc[aos:los]
        passes.append(
            PassWindow(
                pass_number=n,
                aos_time=aos.to_pydatetime(),
                los_time=los.to_pydatetime(),
                max_elevation_deg=float(window.max()),
                duration_seconds=(los - aos).total_seconds(),
            )
        )
    return passes


def _write_pass_report(csv_path: Path, passes: list[PassWindow]) -> None:
    """Write pass_report.csv with the FEATURES.md §1.4 column order."""
    rows = [
        {
            "pass_number": p.pass_number,
            "aos_time": p.aos_time.isoformat(),
            "los_time": p.los_time.isoformat(),
            "max_elevation_deg": round(p.max_elevation_deg, 3),
            "duration_seconds": round(p.duration_seconds, 1),
        }
        for p in passes
    ]
    columns = ["pass_number", "aos_time", "los_time", "max_elevation_deg", "duration_seconds"]
    pd.DataFrame(rows, columns=columns).to_csv(csv_path, index=False)
