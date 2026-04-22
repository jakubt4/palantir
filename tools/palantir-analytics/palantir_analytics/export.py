"""Telemetry export engine (PAL-201).

Pure engine function: queries archived parameter values from a
PalantirArchive, joins them into a time-indexed DataFrame, writes a CSV
to disk, and returns summary stats + metadata.

Kept free of CLI output per the engine/wrapper separation directive
(FEATURES.md §0). The CLI command in cli.py is the thin argparse layer;
a REST wrapper in a future GSaaS frontend reuses this engine as-is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

import pandas as pd

from palantir_analytics.yamcs_client import PalantirArchive


@dataclass(frozen=True)
class ParameterStats:
    """Summary of one parameter's values over the export window.

    NaN-safe — count reflects the number of non-NaN samples, so after an
    outer join on timestamps a parameter with gaps still reports honest
    statistics only over the timestamps where it has data.
    """

    min: float
    max: float
    mean: float
    std: float
    count: int


@dataclass(frozen=True)
class ExportResult:
    """Metadata returned by :func:`run_export`.

    ``sample_count`` is the number of rows in the joined DataFrame
    (i.e. unique timestamps across all parameters). ``stats`` is keyed
    by the parameter's fully-qualified input path.
    """

    csv_path: Path
    sample_count: int
    stats: dict[str, ParameterStats]


def run_export(
    archive: PalantirArchive,
    parameters: Sequence[str],
    start: datetime,
    stop: datetime,
    out_dir: Path,
) -> ExportResult:
    """Export archived telemetry for ``parameters`` over ``[start, stop)``.

    :param archive:    PalantirArchive connected to the target Yamcs.
    :param parameters: Fully-qualified XTCE paths, e.g. ``/Palantir/Latitude``.
    :param start:      Window start (inclusive, timezone-aware UTC).
    :param stop:       Window stop (exclusive, timezone-aware UTC).
    :param out_dir:    Directory for ``telemetry_export.csv``; created if missing.
    :return:           :class:`ExportResult` — csv path, sample count, per-parameter stats.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # One pandas Series per parameter, indexed by generation_time.
    series_by_column: dict[str, pd.Series] = {}
    for parameter in parameters:
        samples = list(archive.list_parameter_values(parameter, start, stop))
        column = parameter.rsplit("/", 1)[-1]  # last path segment, e.g. "Latitude"
        series_by_column[column] = pd.Series(
            data=[s.value for s in samples],
            index=pd.DatetimeIndex(
                [s.generation_time for s in samples], name="timestamp"
            ),
            name=column,
        )

    # Outer join on timestamp — NaN for parameters missing at a given instant.
    df = pd.concat(series_by_column.values(), axis=1).sort_index()

    csv_path = out_dir / "telemetry_export.csv"
    df.to_csv(csv_path, date_format="%Y-%m-%dT%H:%M:%S%z")

    stats = {
        parameter: _compute_stats(df[column])
        for parameter, column in zip(parameters, series_by_column.keys(), strict=True)
    }

    return ExportResult(csv_path=csv_path, sample_count=len(df), stats=stats)


def _compute_stats(series: pd.Series) -> ParameterStats:
    """NaN-safe summary stats for one parameter column."""
    cleaned = series.dropna()
    return ParameterStats(
        min=float(cleaned.min()),
        max=float(cleaned.max()),
        mean=float(cleaned.mean()),
        std=float(cleaned.std()),
        count=int(cleaned.count()),
    )
