"""Unit tests for the PalantirArchive wrapper.

Patches yamcs-client's YamcsClient so tests run without a live Yamcs
instance. Asserts the wrapper correctly transforms SDK ParameterValue
objects into domain ParameterSample records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from palantir_analytics.yamcs_client import PalantirArchive, ParameterSample


@pytest.fixture
def archive():
    """Construct PalantirArchive with yamcs_client.YamcsClient patched out."""
    with patch("palantir_analytics.yamcs_client.YamcsClient"):
        yield PalantirArchive(address="localhost:8090", instance="palantir")


def test_list_parameter_values_transforms_records(archive: PalantirArchive) -> None:
    """Each yamcs-client ParameterValue maps to our ParameterSample."""
    fake_value = MagicMock(
        generation_time=datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc),
        eng_value=51.64,
    )
    archive._archive.list_parameter_values.return_value = iter([fake_value])

    start = datetime(2026, 4, 22, 9, tzinfo=timezone.utc)
    stop = datetime(2026, 4, 22, 11, tzinfo=timezone.utc)
    samples = list(archive.list_parameter_values("/Palantir/Latitude", start, stop))

    assert samples == [
        ParameterSample(
            generation_time=datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc),
            value=51.64,
        )
    ]


def test_list_parameter_values_empty_window(archive: PalantirArchive) -> None:
    """No archived data in the window returns an empty iterator."""
    archive._archive.list_parameter_values.return_value = iter([])

    start = datetime(2026, 4, 22, 9, tzinfo=timezone.utc)
    stop = datetime(2026, 4, 22, 11, tzinfo=timezone.utc)
    samples = list(archive.list_parameter_values("/Palantir/Latitude", start, stop))

    assert samples == []


def test_list_parameter_values_forwards_parameters(archive: PalantirArchive) -> None:
    """Wrapper passes through parameter name and time bounds to the SDK."""
    archive._archive.list_parameter_values.return_value = iter([])

    start = datetime(2026, 4, 22, 9, tzinfo=timezone.utc)
    stop = datetime(2026, 4, 22, 11, tzinfo=timezone.utc)
    list(archive.list_parameter_values("/Palantir/Altitude", start, stop))

    archive._archive.list_parameter_values.assert_called_once_with(
        parameter="/Palantir/Altitude", start=start, stop=stop
    )


def test_get_parameter_unit_returns_primary(archive: PalantirArchive) -> None:
    """Primary unit from XTCE UnitSet is returned as a string."""
    archive._mdb.get_parameter.return_value = MagicMock(units=["km"])
    assert archive.get_parameter_unit("/Palantir/Altitude") == "km"


def test_get_parameter_unit_returns_none_when_missing(archive: PalantirArchive) -> None:
    """Parameter with no UnitSet resolves to None."""
    archive._mdb.get_parameter.return_value = MagicMock(units=[])
    assert archive.get_parameter_unit("/Palantir/ccsds_packet_id") is None
