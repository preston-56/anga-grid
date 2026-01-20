from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from anga_grid.correction.base import stamp_correction, validate_pair
from anga_grid.exceptions import AngaGridError

if TYPE_CHECKING:
    import xarray as xr


@dataclass(frozen=True, slots=True)
class DeltaChange:
    deltas: xr.DataArray
    method: str = "delta_change"

    @classmethod
    def fit(
        cls,
        source: xr.DataArray,
        reference: xr.DataArray,
    ) -> DeltaChange:
        validate_pair(source, reference)
        source_mean = source.mean(dim="time", skipna=True)
        reference_mean = reference.mean(dim="time", skipna=True)
        deltas = reference_mean - source_mean
        deltas.attrs["correction"] = "delta_change"
        return cls(deltas=deltas)

    def apply(self, source: xr.DataArray) -> xr.DataArray:
        if "time" not in source.dims:
            raise AngaGridError("source must have a 'time' dimension")
        out = source + self.deltas
        stamp_correction(out, source, "delta_change")
        return out
