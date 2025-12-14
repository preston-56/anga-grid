from __future__ import annotations

import time

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.indicators import compute_spi, detect_onset, dry_spell_count
from anga_grid.indicators.evapotranspiration import reference_et
from anga_grid.season import SEASONS

_GRID = (5, 5)
_DAYS_PER_YEAR = 365


def _build_grid(years: int) -> xr.DataArray:
    n_time = _DAYS_PER_YEAR * years
    times = pd.date_range("1991-01-01", periods=n_time, freq="D")
    rng = np.random.default_rng(2025)
    doy = times.dayofyear.to_numpy()
    seasonal = (
        2.0
        + 10.0 * np.exp(-((doy - 105) ** 2) / 600.0)
        + 8.0 * np.exp(-((doy - 320) ** 2) / 600.0)
    )
    data = rng.exponential(seasonal[:, None, None], size=(n_time, *_GRID)).astype(
        "float32"
    )
    return xr.DataArray(
        data,
        coords={
            "time": times,
            "lat": np.linspace(-1.0, 0.0, _GRID[0]),
            "lon": np.linspace(35.5, 36.5, _GRID[1]),
        },
        dims=["time", "lat", "lon"],
    )


@pytest.mark.performance
def test_spi_three_year_grid_under_5s() -> None:
    pr = _build_grid(years=3)
    started = time.perf_counter()
    result = compute_spi(pr, window_months=3)
    elapsed = time.perf_counter() - started
    assert elapsed < 5.0
    assert result.size > 0


@pytest.mark.performance
def test_onset_three_year_grid_under_5s() -> None:
    pr = _build_grid(years=3)
    started = time.perf_counter()
    result = detect_onset(pr, season=SEASONS["long-rains"])
    elapsed = time.perf_counter() - started
    assert elapsed < 5.0
    assert result.shape == _GRID


@pytest.mark.performance
def test_dry_spell_three_year_grid_under_5s() -> None:
    pr = _build_grid(years=3)
    started = time.perf_counter()
    result = dry_spell_count(pr)
    elapsed = time.perf_counter() - started
    assert elapsed < 5.0
    assert "season_year" in result.dims


@pytest.mark.performance
def test_reference_et_one_year_grid_under_2s() -> None:
    n_time = _DAYS_PER_YEAR
    times = pd.date_range("1991-01-01", periods=n_time, freq="D")
    shape = (n_time, *_GRID)
    coords = {
        "time": times,
        "lat": np.linspace(-1.0, 0.0, _GRID[0]),
        "lon": np.linspace(35.5, 36.5, _GRID[1]),
    }
    dims = ["time", "lat", "lon"]
    base = np.ones(shape, dtype="float32")
    t_min = xr.DataArray(base * 15.0, coords=coords, dims=dims)
    t_max = xr.DataArray(base * 25.0, coords=coords, dims=dims)
    sr = xr.DataArray(base * 18.0, coords=coords, dims=dims)
    wind = xr.DataArray(base * 2.0, coords=coords, dims=dims)
    rh = xr.DataArray(base * 60.0, coords=coords, dims=dims)

    started = time.perf_counter()
    result = reference_et(t_min, t_max, sr, wind, rh)
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert result.size == n_time * _GRID[0] * _GRID[1]


@pytest.mark.performance
def test_spi_scales_with_grid_size_sub_quadratically() -> None:
    grid_small = _build_grid(years=1).isel(lat=slice(0, 2), lon=slice(0, 2))
    grid_full = _build_grid(years=1)

    started_small = time.perf_counter()
    compute_spi(grid_small, window_months=3)
    elapsed_small = time.perf_counter() - started_small

    started_full = time.perf_counter()
    compute_spi(grid_full, window_months=3)
    elapsed_full = time.perf_counter() - started_full

    cells_ratio = (_GRID[0] * _GRID[1]) / 4.0
    assert elapsed_full < cells_ratio * 1.5 * max(elapsed_small, 0.05)
