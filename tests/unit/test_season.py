from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import SeasonError
from anga_grid.season import SEASONS, Season, get_season, seasons_at
from anga_grid.types import BoundingBox


def test_season_rejects_doy_out_of_range() -> None:
    with pytest.raises(SeasonError):
        Season(name="x", start_doy=0, end_doy=30)
    with pytest.raises(SeasonError):
        Season(name="x", start_doy=1, end_doy=400)


def test_season_rejects_reversed_baseline() -> None:
    with pytest.raises(SeasonError):
        Season(name="x", start_doy=1, end_doy=10, baseline_years=(2020, 2010))


def test_wraps_year_when_start_after_end() -> None:
    s = Season(name="rolling", start_doy=300, end_doy=60)
    assert s.wraps_year
    plain = Season(name="mam", start_doy=60, end_doy=151)
    assert not plain.wraps_year


def test_length_days_contiguous() -> None:
    assert Season(name="mam", start_doy=60, end_doy=151).length_days == 92


def test_length_days_wrapping() -> None:
    s = Season(name="end-of-year", start_doy=350, end_doy=10)
    assert s.length_days == (366 - 350 + 1) + 10


def test_applies_to_no_region_returns_true() -> None:
    s = Season(name="global", start_doy=1, end_doy=10)
    assert s.applies_to(0.0, 0.0)
    assert s.applies_to(45.0, 100.0)


def test_applies_to_with_region() -> None:
    bbox = BoundingBox(min_lat=-1.0, max_lat=1.0, min_lon=35.0, max_lon=37.0)
    s = Season(name="r", start_doy=1, end_doy=10, region=bbox)
    assert s.applies_to(0.0, 36.0)
    assert not s.applies_to(5.0, 36.0)
    assert not s.applies_to(0.0, 40.0)


def test_subset_slices_to_season_window() -> None:
    times = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    da = xr.DataArray(np.arange(len(times)), coords={"time": times}, dims=["time"])
    long_rains = SEASONS["long-rains"]
    result = long_rains.subset(da)
    doy_kept = result["time"].dt.dayofyear.values
    assert doy_kept.min() >= long_rains.start_doy
    assert doy_kept.max() <= long_rains.end_doy


def test_subset_wrapping_season_keeps_both_ends() -> None:
    times = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    da = xr.DataArray(np.arange(len(times)), coords={"time": times}, dims=["time"])
    s = Season(name="wraps", start_doy=350, end_doy=10)
    result = s.subset(da)
    doy = result["time"].dt.dayofyear.values
    assert (doy >= 350).any()
    assert (doy <= 10).any()


def test_subset_rejects_missing_time_dim() -> None:
    da = xr.DataArray([1, 2, 3], dims=["x"])
    s = Season(name="x", start_doy=1, end_doy=10)
    with pytest.raises(SeasonError):
        s.subset(da)


def test_catalog_has_kmd_and_icpac_defaults() -> None:
    for key in ("long-rains", "short-rains", "gha-mam", "gha-ond"):
        assert key in SEASONS
        assert SEASONS[key].definition_source


def test_long_rains_applies_to_nakuru() -> None:
    nakuru_lat, nakuru_lon = -0.3, 36.0
    assert SEASONS["long-rains"].applies_to(nakuru_lat, nakuru_lon)
    assert SEASONS["short-rains"].applies_to(nakuru_lat, nakuru_lon)


def test_unimodal_applies_only_north_of_3deg() -> None:
    assert SEASONS["northern-unimodal"].applies_to(8.0, 39.0)
    assert not SEASONS["northern-unimodal"].applies_to(-0.3, 36.0)


def test_get_season_raises_on_unknown() -> None:
    with pytest.raises(SeasonError):
        get_season("nonexistent-season")


def test_seasons_at_nakuru_returns_bimodal_pair() -> None:
    found = {s.name for s in seasons_at(-0.3, 36.0)}
    assert "long-rains" in found
    assert "short-rains" in found
    assert "northern-unimodal" not in found


def test_highland_season_is_two_weeks_later_than_baseline() -> None:
    highland = SEASONS["highland-long-rains"]
    baseline = SEASONS["long-rains"]
    assert highland.start_doy > baseline.start_doy
    assert highland.start_doy - baseline.start_doy >= 10


def test_coastal_season_extends_into_june() -> None:
    coastal = SEASONS["coastal-long-rains"]
    assert coastal.end_doy >= 181
