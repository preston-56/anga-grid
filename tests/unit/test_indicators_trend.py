from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.trend import annual_trend, seasonal_trend
from anga_grid.season import SEASONS


def _multi_year_series(years: int = 5, daily: float = 1.0) -> xr.DataArray:
    times = pd.date_range("1991-01-01", periods=365 * years, freq="D")
    return xr.DataArray(
        np.full(len(times), daily, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_annual_trend_rejects_missing_time() -> None:
    da = xr.DataArray([1.0, 2.0], dims=["x"])
    with pytest.raises(IndicatorError):
        annual_trend(da)


def test_annual_trend_constant_series_has_zero_slope() -> None:
    da = _multi_year_series(years=5)
    slope = annual_trend(da, reducer="mean")
    assert float(slope.values) == pytest.approx(0.0, abs=1e-3)


def test_annual_trend_with_linear_increase_recovers_slope() -> None:
    times = pd.date_range("1991-01-01", periods=365 * 5, freq="D")
    year_offset = times.year.to_numpy() - 1991
    daily = (1.0 + year_offset).astype("float32")
    da = xr.DataArray(daily, coords={"time": times}, dims=["time"])
    slope = annual_trend(da, reducer="mean")
    assert float(slope.values) == pytest.approx(1.0, rel=0.01)


def test_annual_trend_rejects_too_short() -> None:
    times = pd.date_range("1991-01-01", periods=10, freq="D")
    da = xr.DataArray(np.ones(10, dtype="float32"), coords={"time": times}, dims=["time"])
    with pytest.raises(IndicatorError, match="at least 2"):
        annual_trend(da)


def test_annual_trend_rejects_unknown_reducer() -> None:
    da = _multi_year_series()
    with pytest.raises(IndicatorError, match="unknown reducer"):
        annual_trend(da, reducer="garbage")


def test_annual_trend_attaches_provenance_attrs() -> None:
    da = _multi_year_series(years=5)
    slope = annual_trend(da, reducer="sum")
    assert slope.attrs["indicator"] == "annual_sum_trend"
    assert slope.attrs["units"] == "value/year"
    assert slope.attrs["years_n"] == 5
    assert slope.attrs["reducer"] == "sum"


def test_annual_trend_extends_manifest_history() -> None:
    da = _multi_year_series(years=5)
    da.attrs["source"] = "CHIRPS-2.0"
    slope = annual_trend(da)
    assert "history" in slope.attrs
    operations = [p.split("|")[1] for p in slope.attrs["history"].split(" | ")]
    assert "annual_trend" in operations


def test_annual_trend_2d_grid() -> None:
    times = pd.date_range("1991-01-01", periods=365 * 4, freq="D")
    year_offset = times.year.to_numpy() - 1991
    shape = (len(times), 2, 2)
    base = np.ones(shape, dtype="float32") * year_offset[:, None, None]
    da = xr.DataArray(
        base.astype("float32"),
        coords={"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]},
        dims=["time", "lat", "lon"],
    )
    slope = annual_trend(da, reducer="mean")
    assert slope.shape == (2, 2)
    assert float(slope.values.mean()) == pytest.approx(1.0, rel=0.01)


def test_seasonal_trend_records_season_attr() -> None:
    times = pd.date_range("1991-01-01", periods=365 * 4, freq="D")
    da = xr.DataArray(
        np.ones(len(times), dtype="float32"),
        coords={"time": times}, dims=["time"],
    )
    slope = seasonal_trend(da, season=SEASONS["long-rains"])
    assert slope.attrs["season"] == "long-rains"


def test_seasonal_trend_with_synthetic_increasing_long_rains() -> None:
    times = pd.date_range("1991-01-01", periods=365 * 5, freq="D")
    doy = times.dayofyear.to_numpy()
    year_offset = times.year.to_numpy() - 1991
    in_window = (doy >= 60) & (doy <= 151)
    daily = np.where(in_window, year_offset.astype("float32"), 0.0).astype("float32")
    da = xr.DataArray(daily, coords={"time": times}, dims=["time"])
    slope = seasonal_trend(da, season=SEASONS["long-rains"], reducer="mean")
    assert float(slope.values) > 0


def test_annual_trend_with_nans_skips_them() -> None:
    times = pd.date_range("1991-01-01", periods=365 * 3, freq="D")
    daily = np.ones(len(times), dtype="float32")
    daily[: 365] = np.nan
    da = xr.DataArray(daily, coords={"time": times}, dims=["time"])
    slope = annual_trend(da, reducer="mean")
    assert float(slope.values) == pytest.approx(0.0, abs=1e-3)
