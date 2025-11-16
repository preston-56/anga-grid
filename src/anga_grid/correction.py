from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest

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
        _validate_pair(source, reference)
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
        _stamp_correction(out, source, "linear_scaling")
        return out


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
        _validate_pair(source, reference)
        source_mean = source.mean(dim="time", skipna=True)
        reference_mean = reference.mean(dim="time", skipna=True)
        deltas = reference_mean - source_mean
        deltas.attrs["correction"] = "delta_change"
        return cls(deltas=deltas)

    def apply(self, source: xr.DataArray) -> xr.DataArray:
        if "time" not in source.dims:
            raise AngaGridError("source must have a 'time' dimension")
        out = source + self.deltas
        _stamp_correction(out, source, "delta_change")
        return out


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
        _validate_pair(source, reference)
        source_monthly = source.groupby(source["time"].dt.month).mean(skipna=True)
        reference_monthly = reference.groupby(reference["time"].dt.month).mean(skipna=True)
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
        _stamp_correction(out, source, "monthly_linear_scaling")
        return out


def _validate_pair(source: xr.DataArray, reference: xr.DataArray) -> None:
    if "time" not in source.dims or "time" not in reference.dims:
        raise AngaGridError("both source and reference must have a 'time' dimension")
    if source.shape[1:] != reference.shape[1:]:
        raise AngaGridError(
            f"spatial shapes differ: {source.shape[1:]} vs {reference.shape[1:]}"
        )


def _stamp_correction(
    result: xr.DataArray, source: xr.DataArray, method: str
) -> None:
    result.attrs.update(source.attrs)
    result.attrs["bias_corrected"] = method
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record("bias_correction", method=method)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
