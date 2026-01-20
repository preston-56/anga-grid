from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from anga_grid.correction.base import stamp_correction, validate_pair
from anga_grid.exceptions import AngaGridError

if TYPE_CHECKING:
    import xarray as xr


@dataclass(frozen=True, slots=True)
class LinearScaling:
    factors: xr.DataArray
    method: str = "linear_scaling"

    @classmethod
    def fit(
        cls,
        source: xr.DataArray,
        reference: xr.DataArray,
        *,
        min_source_mean: float = 1e-6,
    ) -> LinearScaling:
        validate_pair(source, reference)
        source_mean = source.mean(dim="time", skipna=True)
        reference_mean = reference.mean(dim="time", skipna=True)
        safe_source = source_mean.where(source_mean > min_source_mean)
        factors = reference_mean / safe_source
        factors = factors.where(np.isfinite(factors), other=1.0)
        factors.attrs["correction"] = "linear_scaling"
        factors.attrs["min_source_mean"] = min_source_mean
        return cls(factors=factors)

    def apply(self, source: xr.DataArray) -> xr.DataArray:
        if "time" not in source.dims:
            raise AngaGridError("source must have a 'time' dimension")
        out = source * self.factors
        out = out.where(out >= 0, 0.0)
        stamp_correction(out, source, "linear_scaling")
        return out
