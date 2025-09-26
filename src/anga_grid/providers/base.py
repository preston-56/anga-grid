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
