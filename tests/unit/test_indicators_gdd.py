from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.gdd import (
    MAIZE_DEFAULTS,
    SORGHUM_DEFAULTS,
    GDDOptions,
    growing_degree_days,
)
from anga_grid.season import SEASONS


def _series(values: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_gdd_rejects_missing_time() -> None:
    t_min = xr.DataArray([10.0, 12.0], dims=["x"])
    t_max = xr.DataArray([20.0, 22.0], dims=["x"])
    with pytest.raises(IndicatorError):
        growing_degree_days(t_min, t_max)


def test_gdd_rejects_mismatched_lengths() -> None:
    t_min = _series([10, 12, 14])
    t_max = _series([20, 22])
    with pytest.raises(IndicatorError):
        growing_degree_days(t_min, t_max)


def test_gdd_rejects_unknown_method() -> None:
    t_min = _series([10] * 10)
    t_max = _series([20] * 10)
    with pytest.raises(IndicatorError):
        growing_degree_days(t_min, t_max, options=GDDOptions(method="exotic"))


def test_gdd_zero_below_base() -> None:
    t_min = _series([5.0] * 30)
    t_max = _series([8.0] * 30)
    result = growing_degree_days(t_min, t_max, options=GDDOptions(t_base_c=10.0))
    assert float(result.values[0]) == pytest.approx(0.0)


def test_gdd_maize_default_30_days() -> None:
    t_min = _series([15.0] * 30)
    t_max = _series([25.0] * 30)
    result = growing_degree_days(t_min, t_max)
    expected = 30 * (20.0 - 10.0)
    assert float(result.values[0]) == pytest.approx(expected)


def test_gdd_capped_at_t_cap() -> None:
    t_min = _series([25.0] * 30)
    t_max = _series([45.0] * 30)
    capped = growing_degree_days(t_min, t_max, options=GDDOptions(t_base_c=10.0, t_cap_c=30.0))
    uncapped = growing_degree_days(t_min, t_max, options=GDDOptions(t_base_c=10.0, t_cap_c=None))
    assert float(capped.values[0]) < float(uncapped.values[0])


def test_gdd_aggregates_by_year() -> None:
    t_min = _series([15.0] * 30 + [15.0] * 30, start="1991-12-15")
    t_max = _series([25.0] * 30 + [25.0] * 30, start="1991-12-15")
    result = growing_degree_days(t_min, t_max)
    assert "season_year" in result.dims
    assert result.sizes["season_year"] == 2


def test_gdd_with_season() -> None:
    times = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    t_min = xr.DataArray(
        np.ones(len(times), dtype="float32") * 15.0,
        coords={"time": times},
        dims=["time"],
    )
    t_max = xr.DataArray(
        np.ones(len(times), dtype="float32") * 25.0,
        coords={"time": times},
        dims=["time"],
    )
    long_rains = SEASONS["long-rains"]
    result = growing_degree_days(t_min, t_max, season=long_rains)
    expected = long_rains.length_days * 10.0
    assert float(result.values[0]) == pytest.approx(expected)


def test_gdd_attaches_provenance_attrs() -> None:
    t_min = _series([15.0] * 30)
    t_max = _series([25.0] * 30)
    result = growing_degree_days(t_min, t_max)
    assert result.attrs["indicator"] == "gdd"
    assert result.attrs["t_base_c"] == 10.0
    assert result.attrs["units"] == "degC-days"


def test_gdd_extends_manifest_history() -> None:
    t_min = _series([15.0] * 30)
    t_max = _series([25.0] * 30)
    t_min.attrs["source"] = "synthetic"
    t_max.attrs["source"] = "synthetic"
    result = growing_degree_days(t_min, t_max)
    assert "history" in result.attrs
    ops = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "gdd" in ops


def test_gdd_2d_grid() -> None:
    n = 30
    base = np.ones((n, 2, 2), dtype="float32")
    times = pd.date_range("1991-01-01", periods=n, freq="D")
    coords = {"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]}
    t_min = xr.DataArray(base * 15.0, coords=coords, dims=["time", "lat", "lon"])
    t_max = xr.DataArray(base * 25.0, coords=coords, dims=["time", "lat", "lon"])
    result = growing_degree_days(t_min, t_max)
    assert result.shape == (1, 2, 2)
    assert float(result.values.mean()) == pytest.approx(n * 10.0)


def test_crop_default_constants_are_distinct() -> None:
    assert MAIZE_DEFAULTS.t_base_c == 10.0
    assert SORGHUM_DEFAULTS.t_base_c == 8.0
    assert MAIZE_DEFAULTS != SORGHUM_DEFAULTS


def test_gdd_modified_method_differs_from_averaging() -> None:
    t_min = _series([5.0] * 30)
    t_max = _series([15.0] * 30)
    averaging = growing_degree_days(
        t_min, t_max,
        options=GDDOptions(t_base_c=10.0, t_cap_c=None, method="averaging"),
    )
    modified = growing_degree_days(
        t_min, t_max,
        options=GDDOptions(t_base_c=10.0, t_cap_c=None, method="modified"),
    )
    assert float(averaging.values[0]) != float(modified.values[0])
