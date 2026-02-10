from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.cropping import (
    CALENDARS_BY_REGION,
    NAKURU_LONG_RAINS_CALENDAR,
)
from anga_grid.indicators.evapotranspiration import reference_et
from anga_grid.indicators.trend import annual_trend
from anga_grid.indicators.wrsi import MAIZE, water_requirement_satisfaction_index
from anga_grid.severity import quintile_classification, tercile_classification


def _series(values: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


@pytest.mark.regression
def test_reference_et_no_negative_values_for_realistic_inputs() -> None:
    n = 30
    et = reference_et(
        _series([10.0] * n),
        _series([22.0] * n),
        _series([18.0] * n),
        _series([2.0] * n),
        _series([60.0] * n),
    )
    assert (et.values >= 0).all()


@pytest.mark.regression
def test_wrsi_clamps_above_zero_below_one_hundred() -> None:
    n = MAIZE.total_days
    wrsi = water_requirement_satisfaction_index(
        _series([15.0] * n), _series([2.0] * n)
    )
    val = float(wrsi.values)
    assert 0.0 <= val <= 100.0


@pytest.mark.regression
def test_annual_trend_has_correct_units_string() -> None:
    times = pd.date_range("1991-01-01", periods=365 * 5, freq="D")
    da = xr.DataArray(
        np.ones(len(times), dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    slope = annual_trend(da, reducer="mean")
    assert slope.attrs["units"] == "value/year"


@pytest.mark.regression
def test_tercile_band_labels_match_published_kmd_terms() -> None:
    times = pd.date_range("1991-01-01", periods=10, freq="YS")
    da = xr.DataArray(
        np.arange(10, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    result = tercile_classification(da)
    labels = {str(v) for v in result.values}
    expected = {"below-normal", "near-normal", "above-normal"}
    assert labels <= expected


@pytest.mark.regression
def test_quintile_band_labels_match_fewsnet_terms() -> None:
    times = pd.date_range("1991-01-01", periods=20, freq="YS")
    da = xr.DataArray(
        np.arange(20, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    result = quintile_classification(da)
    labels = {str(v) for v in result.values}
    expected = {"very-dry", "dry", "near-normal", "wet", "very-wet"}
    assert labels <= expected


@pytest.mark.regression
def test_nakuru_short_rains_planting_after_long_rains() -> None:
    long_rains_maize = NAKURU_LONG_RAINS_CALENDAR.for_crop("maize")
    short_rains_maize = CALENDARS_BY_REGION["nakuru-short-rains"].for_crop("maize")
    assert short_rains_maize.planting_doy > long_rains_maize.planting_doy


@pytest.mark.regression
def test_kc_curve_starts_below_peak_above_end() -> None:
    from anga_grid.indicators.wrsi.compute import _build_kc_curve

    curve = _build_kc_curve(MAIZE)
    assert curve[0] < curve[MAIZE.init_days + MAIZE.devt_days - 1]
    assert curve[-1] < curve[MAIZE.init_days + MAIZE.devt_days - 1]


@pytest.mark.regression
def test_calendars_for_each_region_have_one_or_more_crops() -> None:
    for cal in CALENDARS_BY_REGION.values():
        assert len(cal.entries) >= 1


@pytest.mark.regression
def test_reference_et_attrs_include_method_string() -> None:
    n = 5
    et = reference_et(
        _series([15.0] * n),
        _series([25.0] * n),
        _series([20.0] * n),
        _series([2.0] * n),
        _series([60.0] * n),
    )
    assert "FAO-56" in et.attrs["method"]
