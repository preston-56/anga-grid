from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.wrsi.crops import MAIZE, CropProfile
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


def water_requirement_satisfaction_index(
    rainfall: xr.DataArray,
    reference_et: xr.DataArray,
    crop: CropProfile = MAIZE,
    planting_doy: int | None = None,
) -> xr.DataArray:
    import xarray as xr

    if "time" not in rainfall.dims:
        raise IndicatorError("rainfall missing 'time' dimension")
    if "time" not in reference_et.dims:
        raise IndicatorError("reference_et missing 'time' dimension")
    if rainfall.sizes["time"] != reference_et.sizes["time"]:
        raise IndicatorError(
            f"time-dim mismatch: rainfall {rainfall.sizes['time']} "
            f"vs reference_et {reference_et.sizes['time']}"
        )

    times = rainfall["time"]
    n_time = times.size
    doys = times.dt.dayofyear.values

    if planting_doy is not None:
        start_idx = int(np.argmin(np.abs(doys - planting_doy)))
    else:
        start_idx = 0

    end_idx = start_idx + crop.total_days
    if end_idx > n_time:
        raise IndicatorError(
            f"insufficient time samples after planting_doy={planting_doy}: "
            f"need {crop.total_days} got {n_time - start_idx}"
        )

    rainfall_window = rainfall.isel(time=slice(start_idx, end_idx))
    et_window = reference_et.isel(time=slice(start_idx, end_idx))

    kc_curve = _build_kc_curve(crop)
    expanded = _broadcast_to_grid(kc_curve, et_window)
    water_required = et_window * expanded

    total_required = water_required.sum(dim="time", skipna=True)
    total_satisfied = xr.ufuncs.minimum(rainfall_window, water_required).sum(
        dim="time", skipna=True
    )

    safe_required = total_required.where(total_required > 0)
    wrsi = (100.0 * total_satisfied / safe_required).where(safe_required > 0, 100.0)
    wrsi = wrsi.clip(min=0.0, max=100.0)

    wrsi.attrs.update(rainfall.attrs)
    wrsi.attrs["indicator"] = "wrsi"
    wrsi.attrs["crop"] = crop.name
    wrsi.attrs["crop_total_days"] = crop.total_days
    wrsi.attrs["units"] = "%"
    if planting_doy is not None:
        wrsi.attrs["planting_doy"] = planting_doy

    _record_history(wrsi, crop, planting_doy)
    return wrsi


def _build_kc_curve(crop: CropProfile) -> np.ndarray:
    n = crop.total_days
    kc = np.zeros(n, dtype="float64")

    end_init = crop.init_days
    end_devt = end_init + crop.devt_days
    end_mid = end_devt + crop.mid_days

    kc[0:end_init] = crop.kc_init

    if crop.devt_days > 0:
        ramp = np.linspace(
            crop.kc_init, crop.kc_mid, crop.devt_days + 1
        )[1:]
        kc[end_init:end_devt] = ramp

    kc[end_devt:end_mid] = crop.kc_mid

    if crop.late_days > 0:
        descent = np.linspace(
            crop.kc_mid, crop.kc_end, crop.late_days + 1
        )[1:]
        kc[end_mid:n] = descent

    return kc


def _broadcast_to_grid(kc_curve: np.ndarray, et_window: xr.DataArray) -> xr.DataArray:
    import xarray as xr

    kc_da = xr.DataArray(kc_curve, dims=["time"], coords={"time": et_window["time"]})
    if et_window.ndim == 1:
        return kc_da
    return kc_da.broadcast_like(et_window)


def _record_history(
    result: xr.DataArray, crop: CropProfile, planting_doy: int | None
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    params: dict[str, object] = {
        "crop": crop.name,
        "total_days": crop.total_days,
    }
    if planting_doy is not None:
        params["planting_doy"] = planting_doy
    manifest.record("wrsi", **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
