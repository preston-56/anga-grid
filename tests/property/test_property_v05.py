from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from anga_grid.cropping import (
    flowering_window,
    grain_filling_window,
    land_preparation_window,
    sowing_window,
)
from anga_grid.indicators.temperature_extremes import frost_days, hot_days


@pytest.mark.property
@given(
    planting_doy=st.integers(min_value=30, max_value=300),
    days_to_flower=st.integers(min_value=20, max_value=120),
)
def test_flowering_after_sowing_after_land_prep(
    planting_doy: int, days_to_flower: int
) -> None:
    lp = land_preparation_window(planting_doy)
    sw = sowing_window(planting_doy)
    fl = flowering_window(planting_doy, days_to_flower)
    assert lp.start_doy <= lp.end_doy < sw.start_doy
    assert sw.start_doy < fl.start_doy


@pytest.mark.property
@given(planting_doy=st.integers(min_value=30, max_value=200))
def test_grain_filling_after_flowering_in_calendar_order(planting_doy: int) -> None:
    fl = flowering_window(planting_doy, days_to_flower=60)
    gf = grain_filling_window(planting_doy, days_to_fill=90)
    assert gf.start_doy >= fl.start_doy


@pytest.mark.property
@given(
    threshold=st.floats(
        min_value=20.0, max_value=45.0, allow_nan=False, allow_infinity=False
    )
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_hot_days_count_monotone_in_threshold(threshold: float) -> None:
    times = pd.date_range("1991-01-01", periods=30, freq="D")
    rng = np.random.default_rng(0)
    da = xr.DataArray(
        rng.uniform(15, 45, len(times)).astype("float32"),
        coords={"time": times},
        dims=["time"],
    )
    looser = hot_days(da, threshold_c=threshold - 5)
    stricter = hot_days(da, threshold_c=threshold + 5)
    assert int(looser.values[0]) >= int(stricter.values[0])


@pytest.mark.property
@given(
    threshold=st.floats(
        min_value=-5.0, max_value=10.0, allow_nan=False, allow_infinity=False
    )
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_frost_days_count_monotone_in_threshold(threshold: float) -> None:
    times = pd.date_range("1991-01-01", periods=30, freq="D")
    rng = np.random.default_rng(1)
    da = xr.DataArray(
        rng.uniform(-10, 15, len(times)).astype("float32"),
        coords={"time": times},
        dims=["time"],
    )
    looser = frost_days(da, threshold_c=threshold + 2)
    stricter = frost_days(da, threshold_c=threshold - 2)
    assert int(looser.values[0]) >= int(stricter.values[0])
