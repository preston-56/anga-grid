from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import xarray as xr


def synthetic_chirps(
    *,
    start: date | str = "1991-01-01",
    end: date | str = "1991-12-31",
    lat_min: float = -1.5,
    lat_max: float = 0.5,
    lon_min: float = 35.5,
    lon_max: float = 36.5,
    resolution: float = 0.05,
    seed: int = 1991,
) -> xr.Dataset:
    times = pd.date_range(start=start, end=end, freq="D")
    lats = np.round(np.arange(lat_min, lat_max + resolution / 2, resolution), 5)
    lons = np.round(np.arange(lon_min, lon_max + resolution / 2, resolution), 5)

    rng = np.random.default_rng(seed)

    doy = times.dayofyear.to_numpy()
    long_rains_peak = np.exp(-((doy - 105) ** 2) / 600.0)
    short_rains_peak = np.exp(-((doy - 320) ** 2) / 600.0)
    daily_climatology = 1.5 + 30.0 * long_rains_peak + 25.0 * short_rains_peak

    wet_today = rng.random((len(times), len(lats), len(lons))) < (
        0.15 + 0.6 * (daily_climatology[:, None, None] / daily_climatology.max())
    )
    intensity = rng.exponential(
        scale=daily_climatology[:, None, None] / 4.0,
        size=(len(times), len(lats), len(lons)),
    )
    precip = np.where(wet_today, intensity, 0.0).astype("float32")

    return xr.Dataset(
        data_vars={
            "precip": (
                ("time", "lat", "lon"),
                precip,
                {"units": "mm/day", "long_name": "daily precipitation"},
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
            "title": "synthetic CHIRPS-shaped daily rainfall",
            "source": "anga_grid.tests.fixtures.synthetic",
            "Conventions": "CF-1.8",
        },
    )


def synthetic_chirps_multiyear(
    *,
    years: tuple[int, int] = (1991, 1993),
    **kwargs: object,
) -> xr.Dataset:
    return synthetic_chirps(
        start=f"{years[0]}-01-01",
        end=f"{years[1]}-12-31",
        **kwargs,  # type: ignore[arg-type]
    )
