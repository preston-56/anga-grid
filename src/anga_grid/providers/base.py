"""The Provider Protocol every dataset reader implements.

A custom provider integrates with the rest of the library (CLI,
indicators, rollups, classification) by satisfying this Protocol -
no inheritance required. The runtime-checkable form means
isinstance(p, Provider) tells you whether p will work end-to-end.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr


@runtime_checkable
class Provider(Protocol):
    name: str

    def fetch(self, bbox: BoundingBox, time_range: TimeRange) -> xr.Dataset:
        ...
