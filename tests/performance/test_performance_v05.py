from __future__ import annotations

import time

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.indicators.evapotranspiration import reference_et
from anga_grid.indicators.trend import annual_trend
from anga_grid.indicators.wrsi import MAIZE, water_requirement_satisfaction_index
from anga_grid.severity import quintile_classification, tercile_classification


@pytest.mark.performance
def test_reference_et_5x5_grid_one_year_under_2s() -> None:
    n = 365
    shape = (n, 5, 5)
    base = np.ones(shape, dtype="float32")
    times = pd.date_range("1991-01-01", periods=n, freq="D")
    coords = {
        "time": times,
        "lat": np.linspace(-1.0, 0.0, 5),
        "lon": np.linspace(35.5, 36.5, 5),
    }
    dims = ["time", "lat", "lon"]
    t_min = xr.DataArray(base * 15.0, coords=coords, dims=dims)
    t_max = xr.DataArray(base * 25.0, coords=coords, dims=dims)
    sr = xr.DataArray(base * 18.0, coords=coords, dims=dims)
    wind = xr.DataArray(base * 2.0, coords=coords, dims=dims)
    rh = xr.DataArray(base * 60.0, coords=coords, dims=dims)

    started = time.perf_counter()
    et = reference_et(t_min, t_max, sr, wind, rh)
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert et.shape == shape


@pytest.mark.performance
def test_wrsi_5x5_grid_under_2s() -> None:
    n = MAIZE.total_days
    shape = (n, 5, 5)
    times = pd.date_range("1991-03-01", periods=n, freq="D")
    coords = {
        "time": times,
        "lat": np.linspace(-1.0, 0.0, 5),
        "lon": np.linspace(35.5, 36.5, 5),
    }
    rain = xr.DataArray(
        np.ones(shape, dtype="float32") * 5.0,
        coords=coords, dims=["time", "lat", "lon"],
    )
    et = xr.DataArray(
        np.ones(shape, dtype="float32") * 4.0,
        coords=coords, dims=["time", "lat", "lon"],
    )
    started = time.perf_counter()
    wrsi = water_requirement_satisfaction_index(rain, et)
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert wrsi.shape == (5, 5)


@pytest.mark.performance
def test_annual_trend_decade_grid_under_3s() -> None:
    n = 365 * 10
    shape = (n, 5, 5)
    times = pd.date_range("1991-01-01", periods=n, freq="D")
    da = xr.DataArray(
        np.random.default_rng(0).random(shape).astype("float32"),
        coords={
            "time": times,
            "lat": np.linspace(-1.0, 0.0, 5),
            "lon": np.linspace(35.5, 36.5, 5),
        },
        dims=["time", "lat", "lon"],
    )
    started = time.perf_counter()
    slope = annual_trend(da, reducer="mean")
    elapsed = time.perf_counter() - started
    assert elapsed < 3.0
    assert slope.shape == (5, 5)


@pytest.mark.performance
def test_tercile_classification_under_1s() -> None:
    n = 30
    times = pd.date_range("1991-01-01", periods=n, freq="YS")
    da = xr.DataArray(
        np.random.default_rng(0).random((n, 10, 10)).astype("float32"),
        coords={
            "time": times,
            "lat": np.linspace(-1.0, 0.0, 10),
            "lon": np.linspace(35.5, 36.5, 10),
        },
        dims=["time", "lat", "lon"],
    )
    started = time.perf_counter()
    result = tercile_classification(da)
    elapsed = time.perf_counter() - started
    assert elapsed < 1.0
    assert result.sizes["time"] == n


@pytest.mark.performance
def test_quintile_classification_under_1s() -> None:
    n = 30
    times = pd.date_range("1991-01-01", periods=n, freq="YS")
    da = xr.DataArray(
        np.random.default_rng(0).random((n, 10, 10)).astype("float32"),
        coords={
            "time": times,
            "lat": np.linspace(-1.0, 0.0, 10),
            "lon": np.linspace(35.5, 36.5, 10),
        },
        dims=["time", "lat", "lon"],
    )
    started = time.perf_counter()
    result = quintile_classification(da)
    elapsed = time.perf_counter() - started
    assert elapsed < 1.0
    assert result.sizes["time"] == n
