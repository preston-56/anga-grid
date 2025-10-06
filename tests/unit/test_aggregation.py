from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.aggregation import aggregate_seasonal
from anga_grid.exceptions import AngaGridError
from anga_grid.season import SEASONS, Season


def _three_year_series() -> xr.DataArray:
    times = pd.date_range("1991-01-01", "1993-12-31", freq="D")
    data = np.ones(len(times), dtype="float32")
    return xr.DataArray(data, coords={"time": times}, dims=["time"])


def test_aggregate_sum_over_long_rains_returns_per_year() -> None:
    da = _three_year_series()
    result = aggregate_seasonal(da, SEASONS["long-rains"], reducer="sum")
    assert "season_year" in result.dims
    assert result.sizes["season_year"] == 3
    expected = SEASONS["long-rains"].length_days
    assert float(result.values[0]) == pytest.approx(expected)


def test_aggregate_mean_returns_one_per_year() -> None:
    da = _three_year_series()
    result = aggregate_seasonal(da, SEASONS["long-rains"], reducer="mean")
    for v in result.values:
        assert float(v) == pytest.approx(1.0)


def test_aggregate_with_callable_reducer() -> None:
    da = _three_year_series()
    result = aggregate_seasonal(
        da, SEASONS["long-rains"], reducer=lambda x: x.max()
    )
    for v in result.values:
        assert float(v) == pytest.approx(1.0)


def test_aggregate_rejects_unknown_reducer() -> None:
    da = _three_year_series()
    with pytest.raises(AngaGridError):
        aggregate_seasonal(da, SEASONS["long-rains"], reducer="garbage")


def test_aggregate_rejects_non_str_non_callable_reducer() -> None:
    da = _three_year_series()
    with pytest.raises(AngaGridError):
        aggregate_seasonal(
            da, SEASONS["long-rains"], reducer=42  # type: ignore[arg-type]
        )


def test_aggregate_rejects_missing_time_dim() -> None:
    da = xr.DataArray([1, 2, 3], dims=["x"])
    with pytest.raises(AngaGridError):
        aggregate_seasonal(da, SEASONS["long-rains"])


def test_aggregate_max_and_min() -> None:
    times = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    values = np.arange(len(times), dtype="float32")
    da = xr.DataArray(values, coords={"time": times}, dims=["time"])
    long_rains = SEASONS["long-rains"]
    out_max = aggregate_seasonal(da, long_rains, reducer="max")
    out_min = aggregate_seasonal(da, long_rains, reducer="min")
    assert float(out_max.values[0]) > float(out_min.values[0])


def test_aggregate_count() -> None:
    da = _three_year_series()
    result = aggregate_seasonal(da, SEASONS["long-rains"], reducer="count")
    expected = SEASONS["long-rains"].length_days
    for v in result.values:
        assert int(v) == expected


def test_aggregate_with_2d_grid() -> None:
    times = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    lats = [-0.5, 0.0, 0.5]
    lons = [35.0, 35.5, 36.0]
    data = np.ones((len(times), 3, 3), dtype="float32") * 2.0
    da = xr.DataArray(
        data, coords={"time": times, "lat": lats, "lon": lons},
        dims=["time", "lat", "lon"],
    )
    result = aggregate_seasonal(da, SEASONS["long-rains"], reducer="sum")
    expected_per_cell = 2.0 * SEASONS["long-rains"].length_days
    assert result.shape == (1, 3, 3)
    assert float(result.values.mean()) == pytest.approx(expected_per_cell)


def test_aggregate_with_wrap_around_season() -> None:
    times = pd.date_range("1991-01-01", "1992-12-31", freq="D")
    da = xr.DataArray(
        np.ones(len(times), dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )
    wrap = Season(name="wrap", start_doy=350, end_doy=10)
    result = aggregate_seasonal(da, wrap, reducer="sum")
    assert "season_year" in result.dims
    assert result.sum().item() > 0
