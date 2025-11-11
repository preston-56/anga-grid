from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import xarray as xr


def synthetic_agera5(
    *,
    start: date | str = "1991-01-01",
    end: date | str = "1991-03-31",
    lat_min: float = -1.5,
    lat_max: float = 0.5,
    lon_min: float = 35.5,
    lon_max: float = 36.5,
    resolution: float = 0.1,
    seed: int = 1991,
) -> xr.Dataset:
    times = pd.date_range(start=start, end=end, freq="D")
    lats = np.round(np.arange(lat_min, lat_max + resolution / 2, resolution), 5)
    lons = np.round(np.arange(lon_min, lon_max + resolution / 2, resolution), 5)

    rng = np.random.default_rng(seed)
    shape = (len(times), len(lats), len(lons))

    doy = times.dayofyear.to_numpy()
    long_rains = np.exp(-((doy - 105) ** 2) / 600.0)
    short_rains = np.exp(-((doy - 320) ** 2) / 600.0)

    precip = (
        rng.exponential(scale=2.0 + 30.0 * long_rains + 25.0 * short_rains, size=shape[0])[
            :, None, None
        ]
        * rng.random(shape).astype("float32")
    ).astype("float32")

    t_mean = 17.0 + 5.0 * np.sin(2 * np.pi * (doy - 90) / 365.25)
    t_mean_3d = (t_mean[:, None, None] + rng.normal(0, 0.5, shape)).astype("float32")
    t_min_3d = (t_mean_3d - rng.uniform(3, 7, shape)).astype("float32")
    t_max_3d = (t_mean_3d + rng.uniform(3, 7, shape)).astype("float32")

    radiation = (20e6 + rng.normal(0, 2e6, shape)).astype("float32")
    wind = (1.5 + rng.exponential(1.0, shape)).astype("float32")
    rh = (60.0 + 30.0 * rng.random(shape)).astype("float32")
    vapour = (1500.0 + 500.0 * rng.random(shape)).astype("float32")

    return xr.Dataset(
        data_vars={
            "temperature_air_mean_daily": (("time", "lat", "lon"), t_mean_3d, {"units": "degC"}),
            "temperature_air_min_daily": (("time", "lat", "lon"), t_min_3d, {"units": "degC"}),
            "temperature_air_max_daily": (("time", "lat", "lon"), t_max_3d, {"units": "degC"}),
            "precipitation_flux": (
                ("time", "lat", "lon"),
                precip,
                {"units": "mm/day"},
            ),
            "solar_radiation_flux": (
                ("time", "lat", "lon"),
                radiation,
                {"units": "J m-2 day-1"},
            ),
            "wind_speed_10m_mean_daily": (
                ("time", "lat", "lon"),
                wind,
                {"units": "m/s"},
            ),
            "relative_humidity_2m_12h": (
                ("time", "lat", "lon"),
                rh,
                {"units": "%"},
            ),
            "vapour_pressure_daily": (
                ("time", "lat", "lon"),
                vapour,
                {"units": "hPa"},
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
            "title": "synthetic AgERA5-shaped daily reanalysis",
            "Conventions": "CF-1.8",
        },
    )
