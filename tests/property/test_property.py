from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from anga_grid.aggregation import aggregate_seasonal
from anga_grid.indicators.onset import OnsetCriteria, detect_onset
from anga_grid.season import SEASONS, Season
from anga_grid.types import BoundingBox


@st.composite
def _season_doys(draw: st.DrawFn) -> tuple[int, int]:
    start = draw(st.integers(min_value=1, max_value=300))
    length = draw(st.integers(min_value=10, max_value=90))
    return start, min(366, start + length)


@given(_season_doys())
@settings(max_examples=30, deadline=None)
def test_season_subset_keeps_only_in_window_doys(doys: tuple[int, int]) -> None:
    start, end = doys
    season = Season(name="prop", start_doy=start, end_doy=end)
    times = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    da = xr.DataArray(
        np.arange(len(times), dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    result = season.subset(da)
    if result.size > 0:
        kept_doys = result["time"].dt.dayofyear.values
        if not season.wraps_year:
            assert kept_doys.min() >= start
            assert kept_doys.max() <= end


@given(
    lat=st.floats(min_value=-89, max_value=89, allow_nan=False),
    lon=st.floats(min_value=-179, max_value=179, allow_nan=False),
)
def test_bbox_contains_consistent_with_lat_lon_bounds(
    lat: float, lon: float
) -> None:
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    expected = (-1 <= lat <= 1) and (35 <= lon <= 37)
    assert bbox.contains(lat, lon) == expected


@given(
    rainfall=st.lists(
        st.floats(min_value=0, max_value=50, allow_nan=False), min_size=120, max_size=200
    )
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_onset_returns_within_input_range_or_nan(rainfall: list[float]) -> None:
    times = pd.date_range("1991-01-01", periods=len(rainfall), freq="D")
    da = xr.DataArray(
        np.asarray(rainfall, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    result = detect_onset(
        da,
        criteria=OnsetCriteria(
            wet_window_days=3, wet_threshold_mm=10, followup_days=15, dry_spell_days=8
        ),
    )
    val = float(result.values)
    if not np.isnan(val):
        doys = da["time"].dt.dayofyear.values
        assert val >= float(doys.min())
        assert val <= float(doys.max())


def test_aggregate_then_resubset_yields_full_input_count() -> None:
    times = pd.date_range("1991-01-01", "1993-12-31", freq="D")
    da = xr.DataArray(
        np.ones(len(times), dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    season = SEASONS["long-rains"]
    summed = aggregate_seasonal(da, season, reducer="sum")
    total = float(summed.sum().item())
    assert total == season.length_days * 3
