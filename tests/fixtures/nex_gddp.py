from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import xarray as xr


def synthetic_nex_gddp(
    *,
    start: date | str = "2030-01-01",
    end: date | str = "2030-06-30",
    lat_min: float = -1.5,
    lat_max: float = 0.5,
    lon_min: float = 35.5,
    lon_max: float = 36.5,
    resolution: float = 0.25,
    seed: int = 2030,
    units_kelvin: bool = True,
    units_pr_per_second: bool = True,
) -> xr.Dataset:
    times = pd.date_range(start=start, end=end, freq="D")
    lats = np.round(np.arange(lat_min, lat_max + resolution / 2, resolution), 5)
    lons = np.round(np.arange(lon_min, lon_max + resolution / 2, resolution), 5)
    rng = np.random.default_rng(seed)
    shape = (len(times), len(lats), len(lons))

    doy = times.dayofyear.to_numpy()
    seasonal_mean = 17.0 + 5.0 * np.sin(2 * np.pi * (doy - 90) / 365.25)
    base_3d = (seasonal_mean[:, None, None] + rng.normal(0, 0.5, shape)).astype("float32")
    tas = base_3d + 273.15 if units_kelvin else base_3d
    tasmin = tas - rng.uniform(3, 7, shape).astype("float32")
    tasmax = tas + rng.uniform(3, 7, shape).astype("float32")

    long_rains = np.exp(-((doy - 105) ** 2) / 600.0)
    short_rains = np.exp(-((doy - 320) ** 2) / 600.0)
    pr_intensity = (
        rng.exponential(2.0 + 25.0 * long_rains + 20.0 * short_rains, size=shape[0])[
            :, None, None
        ]
        * rng.random(shape).astype("float32")
    ).astype("float32")
    pr = pr_intensity / 86400.0 if units_pr_per_second else pr_intensity

    pr_units = "kg m-2 s-1" if units_pr_per_second else "mm/day"
    tas_units = "K" if units_kelvin else "degC"

    return xr.Dataset(
        data_vars={
            "tas": (("time", "lat", "lon"), tas, {"units": tas_units}),
            "tasmin": (("time", "lat", "lon"), tasmin, {"units": tas_units}),
            "tasmax": (("time", "lat", "lon"), tasmax, {"units": tas_units}),
            "pr": (("time", "lat", "lon"), pr, {"units": pr_units}),
        },
        coords={
            "time": ("time", times),
            "lat": ("lat", lats, {"units": "degrees_north"}),
            "lon": ("lon", lons, {"units": "degrees_east"}),
        },
        attrs={
            "title": "synthetic NEX-GDDP-shaped projection",
            "Conventions": "CF-1.8",
        },
    )
