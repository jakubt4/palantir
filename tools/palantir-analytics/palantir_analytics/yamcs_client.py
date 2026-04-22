"""Thin wrapper around yamcs-client's archive API.

Exposes just the operations needed by PAL-201 / PAL-202 in terms of
domain-flavored types (ParameterSample dataclass) instead of the SDK's
protobuf-backed objects. Keeps the SDK version upgrade surface small
and makes unit testing trivial (mock our wrapper rather than the SDK).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from yamcs.client import YamcsClient


@dataclass(frozen=True)
class ParameterSample:
    """One archived parameter value at a point in time.

    Mirrors the two fields of yamcs-client's ``ParameterValue`` we care
    about: the engineering (calibrated) value and its generation time.
    """

    generation_time: datetime
    value: float


class PalantirArchive:
    """Queries the palantir Yamcs instance's parameter archive.

    Opens a connection lazily at construction time and exposes a single
    streaming query method. Callers get ``ParameterSample`` records
    instead of the SDK's protobuf objects.
    """

    def __init__(
        self,
        address: str = "localhost:8090",
        instance: str = "palantir",
    ) -> None:
        self._address = address
        self._instance = instance
        self._client = YamcsClient(address=address)
        self._archive = self._client.get_archive(instance)

    def list_parameter_values(
        self,
        parameter: str,
        start: datetime,
        stop: datetime,
    ) -> Iterator[ParameterSample]:
        """Stream archived values for ``parameter`` over ``[start, stop)``.

        :param parameter: Fully-qualified XTCE name, e.g. ``/Palantir/Latitude``.
        :param start:     Lower bound (inclusive), timezone-aware datetime.
        :param stop:      Upper bound (exclusive), timezone-aware datetime.
        :return:          Iterator of ``ParameterSample`` in ascending time order.
        """
        for value in self._archive.list_parameter_values(
            parameter=parameter, start=start, stop=stop
        ):
            yield ParameterSample(
                generation_time=value.generation_time,
                value=value.eng_value,
            )
