from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.evapotranspiration import (
    reference_et,
    saturation_vapour_pressure,
    slope_saturation_vapour_pressure,
)


def _series(values: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_saturation_vapour_pressure_at_zero_c() -> None:
    es = saturation_vapour_pressure(xr.DataArray([0.0]))
    assert float(es.values[0]) == pytest.approx(0.611, rel=0.01)


def test_saturation_vapour_pressure_at_20c() -> None:
    es = saturation_vapour_pressure(xr.DataArray([20.0]))
    assert float(es.values[0]) == pytest.approx(2.339, rel=0.01)


def test_saturation_vapour_pressure_monotonic_in_temperature() -> None:
    temps = xr.DataArray(np.linspace(-10, 40, 51, dtype="float32"))
    es = saturation_vapour_pressure(temps)
    diffs = np.diff(es.values)
    assert (diffs > 0).all()


def test_slope_satvp_is_positive() -> None:
    slope = slope_saturation_vapour_pressure(xr.DataArray([20.0]))
    assert float(slope.values[0]) > 0


def test_reference_et_returns_dataarray_with_time_dim() -> None:
    n = 30
    t_min = _series([15.0] * n)
    t_max = _series([25.0] * n)
    sr = _series([20.0] * n)
    wind = _series([2.0] * n)
    rh = _series([60.0] * n)
    et = reference_et(t_min, t_max, sr, wind, rh)
    assert "time" in et.dims
    assert et.sizes["time"] == n


def test_reference_et_is_non_negative() -> None:
    t_min = _series([-5.0, 0.0, 5.0])
    t_max = _series([0.0, 5.0, 10.0])
    sr = _series([5.0, 5.0, 5.0])
    wind = _series([1.0, 1.0, 1.0])
    rh = _series([90.0, 90.0, 90.0])
    et = reference_et(t_min, t_max, sr, wind, rh)
    assert (et.values >= 0).all()


def test_reference_et_increases_with_solar_radiation() -> None:
    t_min = _series([15.0])
    t_max = _series([25.0])
    wind = _series([2.0])
    rh = _series([60.0])
    low_sr = _series([5.0])
    high_sr = _series([25.0])
    et_low = reference_et(t_min, t_max, low_sr, wind, rh)
    et_high = reference_et(t_min, t_max, high_sr, wind, rh)
    assert float(et_high.values[0]) > float(et_low.values[0])


def test_reference_et_increases_with_temperature() -> None:
    sr = _series([15.0])
    wind = _series([2.0])
    rh = _series([60.0])
    et_cool = reference_et(_series([10.0]), _series([20.0]), sr, wind, rh)
    et_warm = reference_et(_series([20.0]), _series([30.0]), sr, wind, rh)
    assert float(et_warm.values[0]) > float(et_cool.values[0])


def test_reference_et_decreases_with_humidity() -> None:
    t_min = _series([15.0])
    t_max = _series([25.0])
    sr = _series([15.0])
    wind = _series([2.0])
    dry = reference_et(t_min, t_max, sr, wind, _series([30.0]))
    humid = reference_et(t_min, t_max, sr, wind, _series([90.0]))
    assert float(dry.values[0]) > float(humid.values[0])


def test_reference_et_njoro_july_in_expected_range() -> None:
    t_min = _series([8.0])
    t_max = _series([22.0])
    sr = _series([18.0])
    wind = _series([1.5])
    rh = _series([65.0])
    et = reference_et(t_min, t_max, sr, wind, rh, elevation_m=2150.0)
    assert 3.0 <= float(et.values[0]) <= 6.5


def test_reference_et_attaches_provenance_attrs() -> None:
    n = 5
    t_min = _series([15.0] * n)
    t_max = _series([25.0] * n)
    sr = _series([20.0] * n)
    wind = _series([2.0] * n)
    rh = _series([60.0] * n)
    et = reference_et(t_min, t_max, sr, wind, rh)
    assert et.attrs["indicator"] == "reference_et"
    assert et.attrs["units"] == "mm/day"
    assert et.attrs["method"] == "FAO-56 Penman-Monteith"


def test_reference_et_extends_manifest_history() -> None:
    n = 5
    t_min = _series([15.0] * n)
    t_min.attrs["source"] = "AgERA5-v1.1"
    t_max = _series([25.0] * n)
    sr = _series([20.0] * n)
    wind = _series([2.0] * n)
    rh = _series([60.0] * n)
    et = reference_et(t_min, t_max, sr, wind, rh)
    assert "history" in et.attrs
    operations = [p.split("|")[1] for p in et.attrs["history"].split(" | ")]
    assert "reference_et" in operations


def test_reference_et_rejects_missing_time_dim() -> None:
    t_min = xr.DataArray([15.0, 16.0], dims=["x"])
    t_max = _series([25.0, 26.0])
    sr = _series([20.0, 20.0])
    wind = _series([2.0, 2.0])
    rh = _series([60.0, 60.0])
    with pytest.raises(IndicatorError, match="t_min"):
        reference_et(t_min, t_max, sr, wind, rh)


def test_reference_et_2d_grid() -> None:
    n = 30
    shape = (n, 2, 2)
    base = np.ones(shape, dtype="float32")
    times = pd.date_range("1991-01-01", periods=n, freq="D")
    coords = {"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]}
    t_min = xr.DataArray(base * 15.0, coords=coords, dims=["time", "lat", "lon"])
    t_max = xr.DataArray(base * 25.0, coords=coords, dims=["time", "lat", "lon"])
    sr = xr.DataArray(base * 20.0, coords=coords, dims=["time", "lat", "lon"])
    wind = xr.DataArray(base * 2.0, coords=coords, dims=["time", "lat", "lon"])
    rh = xr.DataArray(base * 60.0, coords=coords, dims=["time", "lat", "lon"])
    et = reference_et(t_min, t_max, sr, wind, rh)
    assert et.shape == shape
    assert (et.values > 0).all()
