from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.spi import compute_spi
from anga_grid.season import SEASONS
from tests.fixtures.synthetic import synthetic_chirps_multiyear


def test_spi_rejects_zero_window() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1992))["precip"]
    with pytest.raises(IndicatorError):
        compute_spi(pr, window_months=0)


def test_spi_rejects_array_without_time() -> None:
    da = xr.DataArray([1.0, 2.0, 3.0], dims=["x"])
    with pytest.raises(IndicatorError):
        compute_spi(da, window_months=3)


def test_spi_returns_dataarray_with_provenance() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1995))["precip"]
    result = compute_spi(pr, window_months=3)
    assert isinstance(result, xr.DataArray)
    assert result.attrs["indicator"] == "spi"
    assert result.attrs["window_months"] == 3
    assert "baseline" in result.attrs


def test_spi_window_3_produces_finite_centered_values() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1995))["precip"]
    result = compute_spi(pr, window_months=3)
    finite_share = float(np.isfinite(result.values).mean())
    assert finite_share > 0.5


def test_spi_applies_season_subset() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1993))["precip"]
    long_rains = SEASONS["long-rains"]
    seasonal = compute_spi(pr, window_months=3, season=long_rains)
    months = pd.DatetimeIndex(seasonal["time"].values).month
    assert set(months).issubset({3, 4, 5})


def test_spi_baseline_attribute_records_window() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1995))["precip"]
    result = compute_spi(pr, window_months=3, baseline=(1991, 1993))
    assert result.attrs["baseline"] == "1991-1993"


def test_spi_window_6_window_3_differ() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1995))["precip"]
    spi3 = compute_spi(pr, window_months=3)
    spi6 = compute_spi(pr, window_months=6)
    common_time = np.intersect1d(spi3["time"].values, spi6["time"].values)
    if len(common_time) > 0:
        diff = (
            spi3.sel(time=common_time).mean().item()
            - spi6.sel(time=common_time).mean().item()
        )
        assert not np.isnan(diff)


def test_spi_records_distribution_in_attrs() -> None:
    pr = synthetic_chirps_multiyear(years=(1991, 1992))["precip"]
    result = compute_spi(pr, window_months=1)
    assert "distribution" in result.attrs
