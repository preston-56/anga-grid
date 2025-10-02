from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.onset import DEFAULT_CRITERIA, OnsetCriteria, detect_onset
from anga_grid.season import SEASONS


def _build_rainfall(daily_mm: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(daily_mm), freq="D")
    return xr.DataArray(
        np.asarray(daily_mm, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_onset_detects_simple_wet_followed_by_no_dry_spell() -> None:
    seq = [0.0] * 60 + [8.0, 9.0, 8.0] + [3.0] * 30 + [0.0] * 40
    rain = _build_rainfall(seq)
    result = detect_onset(rain)
    expected_doy = 61
    assert float(result.values) == pytest.approx(expected_doy, abs=1)


def test_onset_rejects_wet_window_followed_by_dry_spell() -> None:
    seq = (
        [0.0] * 60
        + [8.0, 9.0, 8.0]
        + [0.0] * 15
        + [3.0] * 30
        + [10.0, 10.0, 10.0]
        + [3.0] * 30
        + [0.0] * 40
    )
    rain = _build_rainfall(seq)
    result = detect_onset(rain)
    assert float(result.values) > 80


def test_onset_returns_nan_when_no_qualifying_window() -> None:
    rain = _build_rainfall([0.0] * 200)
    result = detect_onset(rain)
    assert np.isnan(float(result.values))


def test_onset_returns_nan_for_window_too_short() -> None:
    rain = _build_rainfall([20.0, 20.0, 20.0, 5.0])
    result = detect_onset(rain)
    assert np.isnan(float(result.values))


def test_onset_attaches_provenance_attrs() -> None:
    rain = _build_rainfall([0.0] * 60 + [8.0, 9.0, 8.0] + [3.0] * 100)
    result = detect_onset(rain)
    assert result.attrs["indicator"] == "onset"
    assert result.attrs["wet_window_days"] == 3
    assert result.attrs["wet_threshold_mm"] == 20.0
    assert result.attrs["units"] == "day_of_year"


def test_onset_custom_criteria_picks_different_threshold() -> None:
    seq = [0.0] * 50 + [3.0, 3.0, 3.0] + [2.0] * 35 + [0.0] * 50
    rain = _build_rainfall(seq)
    strict = detect_onset(rain)
    relaxed = detect_onset(
        rain,
        criteria=OnsetCriteria(
            wet_window_days=3,
            wet_threshold_mm=8.0,
            followup_days=30,
            dry_spell_days=10,
            dry_threshold_mm=1.0,
        ),
    )
    assert np.isnan(float(strict.values))
    assert not np.isnan(float(relaxed.values))


def test_onset_rejects_missing_time_dim() -> None:
    da = xr.DataArray([1.0, 2.0, 3.0], dims=["x"])
    with pytest.raises(IndicatorError):
        detect_onset(da)


def test_onset_2d_grid_picks_per_cell() -> None:
    n_time = 200
    rain = np.zeros((n_time, 3, 3), dtype="float32")
    rain[60:63, :, :] = 8.0
    rain[63:93, 0, 0] = 3.0
    rain[63:80, 1, 1] = 0.0
    rain[80:93, 1, 1] = 3.0
    rain[63:93, 2, 2] = 2.0

    times = pd.date_range("1991-01-01", periods=n_time, freq="D")
    da = xr.DataArray(
        rain,
        coords={
            "time": times,
            "lat": [-0.5, 0.0, 0.5],
            "lon": [35.0, 35.5, 36.0],
        },
        dims=["time", "lat", "lon"],
    )
    result = detect_onset(da)
    assert result.shape == (3, 3)
    assert not np.isnan(float(result.sel(lat=-0.5, lon=35.0).values))
    assert np.isnan(float(result.sel(lat=0.0, lon=35.5).values))


def test_onset_with_season_subset() -> None:
    rain = np.zeros(366, dtype="float32")
    rain[65:68] = 8.0
    for d in range(68, 100):
        if d % 5 == 0:
            rain[d] = 5.0
    times = pd.date_range("1991-01-01", periods=366, freq="D")
    da = xr.DataArray(rain, coords={"time": times}, dims=["time"])
    long_rains = SEASONS["long-rains"]
    result = detect_onset(da, season=long_rains)
    onset_doy = float(result.values)
    assert long_rains.start_doy <= onset_doy <= long_rains.end_doy


def test_default_criteria_matches_published_definition() -> None:
    assert DEFAULT_CRITERIA.wet_window_days == 3
    assert DEFAULT_CRITERIA.wet_threshold_mm == 20.0
    assert DEFAULT_CRITERIA.followup_days == 30
    assert DEFAULT_CRITERIA.dry_spell_days == 10
