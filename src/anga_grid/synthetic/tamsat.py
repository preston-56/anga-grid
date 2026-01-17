from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import xarray as xr


def synthetic_tamsat(
    *,
    start: date | str = "1991-01-01",
    end: date | str = "1991-03-31",
    lat_min: float = -1.5,
    lat_max: float = 0.5,
    lon_min: float = 35.5,
    lon_max: float = 36.5,
    resolution: float = 0.0375,
    seed: int = 1991,
) -> xr.Dataset:
    times = pd.date_range(start=start, end=end, freq="D")
    lats = np.round(np.arange(lat_min, lat_max + resolution / 2, resolution), 5)
    lons = np.round(np.arange(lon_min, lon_max + resolution / 2, resolution), 5)

    rng = np.random.default_rng(seed)

    doy = times.dayofyear.to_numpy()
    long_rains_peak = np.exp(-((doy - 105) ** 2) / 600.0)
    short_rains_peak = np.exp(-((doy - 320) ** 2) / 600.0)
    climatology = 1.5 + 25.0 * long_rains_peak + 22.0 * short_rains_peak

    wet_today = rng.random((len(times), len(lats), len(lons))) < (
        0.18 + 0.55 * (climatology[:, None, None] / climatology.max())
    )
    intensity = rng.exponential(
        scale=climatology[:, None, None] / 4.5,
        size=(len(times), len(lats), len(lons)),
    )
    rfe = np.where(wet_today, intensity, 0.0).astype("float32")

    return xr.Dataset(
        data_vars={
            "rfe": (
                ("time", "lat", "lon"),
                rfe,
                {"units": "mm/day", "long_name": "TAMSAT rainfall estimate"},
            ),
        },
        coords={
            "time": ("time", times),
            "lat": (
                "lat",
                lats,
                {"units": "degrees_north", "standard_name": "latitude"},
            ),
            "lon": (
                "lon",
                lons,
                {"units": "degrees_east", "standard_name": "longitude"},
            ),
        },
        attrs={
            "title": "synthetic TAMSAT-shaped daily rainfall",
            "source": "anga_grid.tests.fixtures.synthetic",
            "Conventions": "CF-1.8",
        },
    )
