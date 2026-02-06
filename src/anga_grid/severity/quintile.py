from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


TERCILE_LABELS: tuple[str, str, str] = ("below-normal", "near-normal", "above-normal")
QUINTILE_LABELS: tuple[str, str, str, str, str] = (
    "very-dry",
    "dry",
    "near-normal",
    "wet",
    "very-wet",
)


def tercile_classification(
    da: xr.DataArray,
    baseline: tuple[int, int] | None = None,
    *,
    lower_pct: float = 33.33,
    upper_pct: float = 66.67,
) -> xr.DataArray:
    import xarray as xr

    if "time" not in da.dims:
        raise AngaGridError("input DataArray must have a 'time' dimension")

    ref = _select_baseline(da, baseline)
    lower = ref.quantile(lower_pct / 100.0, dim="time")
    upper = ref.quantile(upper_pct / 100.0, dim="time")

    out = xr.full_like(da, fill_value="near-normal", dtype=object)
    out = xr.where(da < lower, "below-normal", out)
    out = xr.where(da > upper, "above-normal", out)

    out.attrs.update(da.attrs)
    out.attrs["classification"] = "tercile"
    out.attrs["lower_pct"] = lower_pct
    out.attrs["upper_pct"] = upper_pct
    if baseline is not None:
        out.attrs["baseline"] = f"{baseline[0]}-{baseline[1]}"

    _record_history(out, "tercile_classification", lower_pct=lower_pct, upper_pct=upper_pct)
    return out


def quintile_classification(
    da: xr.DataArray,
    baseline: tuple[int, int] | None = None,
) -> xr.DataArray:
    import xarray as xr

    if "time" not in da.dims:
        raise AngaGridError("input DataArray must have a 'time' dimension")

    ref = _select_baseline(da, baseline)
    breaks = [ref.quantile(p / 100.0, dim="time") for p in (20, 40, 60, 80)]

    out = xr.full_like(da, fill_value="near-normal", dtype=object)
    out = xr.where(da < breaks[0], "very-dry", out)
    out = xr.where((da >= breaks[0]) & (da < breaks[1]), "dry", out)
    out = xr.where((da >= breaks[1]) & (da < breaks[2]), "near-normal", out)
    out = xr.where((da >= breaks[2]) & (da < breaks[3]), "wet", out)
    out = xr.where(da >= breaks[3], "very-wet", out)

    out.attrs.update(da.attrs)
    out.attrs["classification"] = "quintile"
    out.attrs["quintile_breaks"] = "20,40,60,80"
    if baseline is not None:
        out.attrs["baseline"] = f"{baseline[0]}-{baseline[1]}"

    _record_history(out, "quintile_classification")
    return out


def _select_baseline(
    da: xr.DataArray, baseline: tuple[int, int] | None
) -> xr.DataArray:
    if baseline is None:
        return da
    years = da["time"].dt.year
    return da.where((years >= baseline[0]) & (years <= baseline[1]), drop=True)


def tercile_summary(classified: xr.DataArray) -> dict[str, float]:
    if classified.attrs.get("classification") != "tercile":
        raise AngaGridError("summary expects a tercile classification")
    total = int(classified.size)
    if total == 0:
        return {label: 0.0 for label in TERCILE_LABELS}
    values = classified.values
    return {
        label: int(np.sum(values == label)) / total for label in TERCILE_LABELS
    }


def _record_history(result: xr.DataArray, operation: str, **params: object) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record(operation, **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
