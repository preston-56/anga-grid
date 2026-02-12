from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.temperature_extremes import (
    cold_days,
    frost_days,
    hot_days,
    tropical_nights,
)
from anga_grid.season import SEASONS


def _series(values: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_hot_days_count_matches_threshold_crossing() -> None:
    da = _series([35.0, 32.5, 30.0, 32.1, 28.0, 33.0])
    result = hot_days(da, threshold_c=32.0)
    assert int(result.values[0]) == 4


def test_cold_days_count_matches_threshold_crossing() -> None:
    da = _series([8.0, 9.5, 11.0, 5.0, 12.0])
    result = cold_days(da, threshold_c=10.0)
    assert int(result.values[0]) == 3


def test_frost_days_zero_when_no_freezing() -> None:
    da = _series([5.0, 4.0, 3.0])
    result = frost_days(da)
    assert int(result.values[0]) == 0


def test_frost_days_counts_freezing() -> None:
    da = _series([-1.0, -2.0, 0.5, -3.0, 4.0])
    result = frost_days(da)
    assert int(result.values[0]) == 3


def test_tropical_nights_count() -> None:
    da = _series([22.0, 19.0, 21.0, 25.0, 18.0])
    result = tropical_nights(da)
    assert int(result.values[0]) == 3


def test_hot_days_rejects_missing_time() -> None:
    da = xr.DataArray([1.0, 2.0], dims=["x"])
    with pytest.raises(IndicatorError):
        hot_days(da)


def test_hot_days_groups_by_year() -> None:
    times = pd.date_range("1991-01-01", periods=730, freq="D")
    data = np.where(times.year == 1992, 35.0, 28.0).astype("float32")
    da = xr.DataArray(data, coords={"time": times}, dims=["time"])
    result = hot_days(da, threshold_c=32.0)
    assert int(result.sel(season_year=1991).item()) == 0
    assert int(result.sel(season_year=1992).item()) > 0


def test_hot_days_with_season_subset() -> None:
    times = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    da = xr.DataArray(
        np.full(len(times), 35.0, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    long_rains = SEASONS["long-rains"]
    result = hot_days(da, threshold_c=32.0, season=long_rains)
    assert int(result.values[0]) == long_rains.length_days


def test_hot_days_attaches_provenance_attrs() -> None:
    da = _series([35.0, 28.0, 33.0])
    result = hot_days(da, threshold_c=32.0)
    assert result.attrs["indicator"] == "hot_days"
    assert result.attrs["threshold_c"] == 32.0
    assert result.attrs["units"] == "days"


def test_hot_days_extends_manifest_history() -> None:
    da = _series([35.0, 28.0, 33.0])
    da.attrs["source"] = "AgERA5-v1.1"
    result = hot_days(da)
    operations = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "hot_days" in operations


def test_hot_days_2d_grid() -> None:
    times = pd.date_range("1991-01-01", periods=10, freq="D")
    rng = np.random.default_rng(0)
    data = rng.uniform(20, 40, (10, 2, 2)).astype("float32")
    da = xr.DataArray(
        data,
        coords={"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]},
        dims=["time", "lat", "lon"],
    )
    result = hot_days(da, threshold_c=32.0)
    assert result.shape == (1, 2, 2)


def test_cold_days_with_custom_threshold() -> None:
    da = _series([5.0, 7.0, 12.0, 8.0])
    less_strict = cold_days(da, threshold_c=10.0)
    very_strict = cold_days(da, threshold_c=6.0)
    assert int(less_strict.values[0]) == 3
    assert int(very_strict.values[0]) == 1
