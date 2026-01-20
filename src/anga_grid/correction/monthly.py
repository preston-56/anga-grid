from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from anga_grid.correction.base import stamp_correction, validate_pair
from anga_grid.exceptions import AngaGridError

if TYPE_CHECKING:
    import xarray as xr


@dataclass(frozen=True, slots=True)
class MonthlyLinearScaling:
    factors_by_month: xr.DataArray
    method: str = "monthly_linear_scaling"

    @classmethod
    def fit(
        cls,
        source: xr.DataArray,
        reference: xr.DataArray,
        *,
        min_source_mean: float = 1e-6,
    ) -> MonthlyLinearScaling:
        validate_pair(source, reference)
        source_monthly = source.groupby(source["time"].dt.month).mean(skipna=True)
        reference_monthly = reference.groupby(reference["time"].dt.month).mean(
            skipna=True
        )
        safe_source = source_monthly.where(source_monthly > min_source_mean)
        factors = reference_monthly / safe_source
        factors = factors.where(np.isfinite(factors), other=1.0)
        factors.attrs["correction"] = "monthly_linear_scaling"
        return cls(factors_by_month=factors)

    def apply(self, source: xr.DataArray) -> xr.DataArray:
        import xarray as xr

        if "time" not in source.dims:
            raise AngaGridError("source must have a 'time' dimension")
        month = source["time"].dt.month
        month_factors = self.factors_by_month.sel(month=month, method="nearest").drop_vars(
            "month", errors="ignore"
        )
        if "month" in month_factors.dims:
            month_factors = month_factors.rename({"month": "time"})
        month_factors = month_factors.assign_coords(time=source["time"])
        out = source * month_factors
        out = xr.where(out >= 0, out, 0.0)
        stamp_correction(out, source, "monthly_linear_scaling")
        return out
