from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.wrsi import (
    MAIZE,
    SORGHUM,
    CropProfile,
    water_requirement_satisfaction_index,
)
from anga_grid.indicators.wrsi.compute import _build_kc_curve


def _series(values: list[float], start: str = "1991-03-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_kc_curve_length_matches_total_days() -> None:
    curve = _build_kc_curve(MAIZE)
    assert curve.shape == (MAIZE.total_days,)


def test_kc_curve_starts_at_kc_init() -> None:
    curve = _build_kc_curve(MAIZE)
    assert curve[0] == pytest.approx(MAIZE.kc_init)


def test_kc_curve_peaks_at_kc_mid() -> None:
    curve = _build_kc_curve(MAIZE)
    end_init = MAIZE.init_days
    end_devt = end_init + MAIZE.devt_days
    assert curve[end_devt - 1] == pytest.approx(MAIZE.kc_mid, rel=1e-3)


def test_kc_curve_ends_at_kc_end() -> None:
    curve = _build_kc_curve(MAIZE)
    assert curve[-1] == pytest.approx(MAIZE.kc_end, rel=1e-3)


def test_wrsi_perfect_supply_returns_100() -> None:
    n = MAIZE.total_days
    rain = _series([20.0] * n)
    et = _series([1.0] * n)
    wrsi = water_requirement_satisfaction_index(rain, et)
    assert float(wrsi.values) == pytest.approx(100.0)


def test_wrsi_zero_rainfall_returns_0() -> None:
    n = MAIZE.total_days
    rain = _series([0.0] * n)
    et = _series([5.0] * n)
    wrsi = water_requirement_satisfaction_index(rain, et)
    assert float(wrsi.values) == pytest.approx(0.0)


def test_wrsi_partial_supply_lands_between_0_and_100() -> None:
    n = MAIZE.total_days
    rain = _series([2.0] * n)
    et = _series([5.0] * n)
    wrsi = water_requirement_satisfaction_index(rain, et)
    val = float(wrsi.values)
    assert 0.0 < val < 100.0


def test_wrsi_rejects_mismatched_time_lengths() -> None:
    rain = _series([1.0] * 10)
    et = _series([1.0] * 20)
    with pytest.raises(IndicatorError, match="time-dim mismatch"):
        water_requirement_satisfaction_index(rain, et)


def test_wrsi_rejects_too_short_time_axis() -> None:
    rain = _series([1.0] * 30)
    et = _series([1.0] * 30)
    with pytest.raises(IndicatorError, match="insufficient time"):
        water_requirement_satisfaction_index(rain, et)


def test_wrsi_rejects_missing_time_dim() -> None:
    rain = xr.DataArray([1.0, 2.0], dims=["x"])
    et = _series([1.0, 2.0])
    with pytest.raises(IndicatorError):
        water_requirement_satisfaction_index(rain, et)


def test_wrsi_respects_planting_doy() -> None:
    n = MAIZE.total_days * 2
    times = pd.date_range("1991-01-01", periods=n, freq="D")
    rain = xr.DataArray(np.zeros(n, dtype="float32"), coords={"time": times}, dims=["time"])
    rain.values[MAIZE.total_days:] = 100.0
    et = xr.DataArray(np.ones(n, dtype="float32") * 5.0, coords={"time": times}, dims=["time"])
    wrsi_early = water_requirement_satisfaction_index(
        rain, et, planting_doy=1
    )
    wrsi_late = water_requirement_satisfaction_index(
        rain, et, planting_doy=int(times[MAIZE.total_days].dayofyear)
    )
    assert float(wrsi_early.values) < float(wrsi_late.values)


def test_wrsi_2d_grid() -> None:
    n = MAIZE.total_days
    shape = (n, 2, 2)
    times = pd.date_range("1991-03-01", periods=n, freq="D")
    coords = {"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]}
    rain = xr.DataArray(
        np.ones(shape, dtype="float32") * 10.0,
        coords=coords, dims=["time", "lat", "lon"],
    )
    et = xr.DataArray(
        np.ones(shape, dtype="float32") * 5.0,
        coords=coords, dims=["time", "lat", "lon"],
    )
    wrsi = water_requirement_satisfaction_index(rain, et)
    assert wrsi.shape == (2, 2)


def test_wrsi_attaches_provenance_attrs() -> None:
    n = MAIZE.total_days
    rain = _series([5.0] * n)
    et = _series([3.0] * n)
    wrsi = water_requirement_satisfaction_index(rain, et)
    assert wrsi.attrs["indicator"] == "wrsi"
    assert wrsi.attrs["crop"] == "maize"
    assert wrsi.attrs["units"] == "%"


def test_wrsi_extends_manifest_history() -> None:
    n = MAIZE.total_days
    rain = _series([5.0] * n)
    rain.attrs["source"] = "CHIRPS-2.0"
    et = _series([3.0] * n)
    wrsi = water_requirement_satisfaction_index(rain, et)
    assert "history" in wrsi.attrs
    operations = [p.split("|")[1] for p in wrsi.attrs["history"].split(" | ")]
    assert "wrsi" in operations


def test_wrsi_different_crops_yield_different_results() -> None:
    n = max(MAIZE.total_days, SORGHUM.total_days)
    rain = _series([2.0] * n)
    et = _series([3.0] * n)
    wrsi_maize = water_requirement_satisfaction_index(rain, et, crop=MAIZE)
    wrsi_sorghum = water_requirement_satisfaction_index(rain, et, crop=SORGHUM)
    assert float(wrsi_maize.values) != float(wrsi_sorghum.values)


def test_crop_profile_total_days_is_sum() -> None:
    p = CropProfile(
        name="test",
        init_days=10, devt_days=20, mid_days=30, late_days=10,
        kc_init=0.3, kc_mid=1.0, kc_end=0.5,
    )
    assert p.total_days == 70
