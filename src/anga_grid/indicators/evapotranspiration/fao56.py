from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.evapotranspiration.constants import (
    ALBEDO_REFERENCE_GRASS,
    LATENT_HEAT_VAPORIZATION,
    PSYCHROMETRIC_CONSTANT,
    SOIL_HEAT_FLUX_DAILY,
)
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


def saturation_vapour_pressure(t_celsius: xr.DataArray) -> xr.DataArray:
    import xarray as xr

    return cast(
        xr.DataArray,
        0.6108 * np.exp((17.27 * t_celsius) / (t_celsius + 237.3)),
    )


def slope_saturation_vapour_pressure(t_celsius: xr.DataArray) -> xr.DataArray:
    es = saturation_vapour_pressure(t_celsius)
    return (4098.0 * es) / np.power(t_celsius + 237.3, 2.0)


def _psychrometric_constant(elevation_m: float) -> float:
    pressure = 101.3 * np.power((293.0 - 0.0065 * elevation_m) / 293.0, 5.26)
    return PSYCHROMETRIC_CONSTANT * pressure


def reference_et(
    t_min: xr.DataArray,
    t_max: xr.DataArray,
    solar_radiation_mj: xr.DataArray,
    wind_speed: xr.DataArray,
    relative_humidity_pct: xr.DataArray,
    elevation_m: float = 2000.0,
) -> xr.DataArray:
    for name, da in (
        ("t_min", t_min),
        ("t_max", t_max),
        ("solar_radiation_mj", solar_radiation_mj),
        ("wind_speed", wind_speed),
        ("relative_humidity_pct", relative_humidity_pct),
    ):
        if "time" not in da.dims:
            raise IndicatorError(f"{name} missing 'time' dimension")

    t_mean = (t_max + t_min) / 2.0

    es_tmax = saturation_vapour_pressure(t_max)
    es_tmin = saturation_vapour_pressure(t_min)
    es = (es_tmax + es_tmin) / 2.0
    ea = es * (relative_humidity_pct / 100.0)
    vpd = es - ea
    vpd = vpd.where(vpd > 0, 0.0)

    slope = slope_saturation_vapour_pressure(t_mean)
    gamma = _psychrometric_constant(elevation_m)

    net_radiation = (1.0 - ALBEDO_REFERENCE_GRASS) * solar_radiation_mj

    numerator = (
        0.408 * slope * (net_radiation - SOIL_HEAT_FLUX_DAILY)
        + gamma * (900.0 / (t_mean + 273.0)) * wind_speed * vpd
    )
    denominator = slope + gamma * (1.0 + 0.34 * wind_speed)
    et = numerator / denominator
    et = et.where(et >= 0, 0.0)

    et.attrs.update(t_min.attrs)
    et.attrs["indicator"] = "reference_et"
    et.attrs["units"] = "mm/day"
    et.attrs["method"] = "FAO-56 Penman-Monteith"
    et.attrs["elevation_m"] = elevation_m
    et.attrs["psychrometric_constant"] = float(gamma)
    et.attrs["albedo"] = ALBEDO_REFERENCE_GRASS
    et.attrs["latent_heat_of_vaporization"] = LATENT_HEAT_VAPORIZATION

    _record_history(et, elevation_m)
    return et


def _record_history(result: xr.DataArray, elevation_m: float) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record(
        "reference_et", method="FAO-56", elevation_m=elevation_m
    )
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
