from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from anga_grid.synthetic.chirps import synthetic_chirps, synthetic_chirps_multiyear


@pytest.fixture
def chirps_one_year() -> xr.Dataset:
    return synthetic_chirps()


@pytest.fixture
def chirps_three_years() -> xr.Dataset:
    return synthetic_chirps_multiyear(years=(1991, 1993))


@pytest.fixture
def chirps_decade() -> xr.Dataset:
    return synthetic_chirps_multiyear(years=(1991, 2000))


@pytest.fixture
def deterministic_rng() -> np.random.Generator:
    return np.random.default_rng(2025)
