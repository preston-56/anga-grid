from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import AngaGridError
from anga_grid.rollup import (
    NAKURU_COUNTY,
    NAKURU_WARDS,
    AdminRegion,
    roll_up,
)
from anga_grid.types import BoundingBox


def _grid(values_const: float = 1.0) -> xr.DataArray:
    times = pd.date_range("1991-01-01", "1991-01-31", freq="D")
    lats = np.arange(-1.2, 0.06, 0.05, dtype="float64")
    lons = np.arange(35.55, 36.56, 0.05, dtype="float64")
    data = np.ones((len(times), len(lats), len(lons)), dtype="float32") * values_const
    return xr.DataArray(
        data,
        coords={"time": times, "lat": lats, "lon": lons},
        dims=["time", "lat", "lon"],
    )


def test_roll_up_mean_constant_field() -> None:
    da = _grid(values_const=5.0)
    result = roll_up(da, list(NAKURU_WARDS))
    assert "region" in result.dims
    assert result.sizes["region"] == len(NAKURU_WARDS)
    np.testing.assert_allclose(result.values, 5.0)


def test_roll_up_records_region_names() -> None:
    da = _grid()
    result = roll_up(da, list(NAKURU_WARDS))
    names = list(result["region"].values)
    assert "njoro" in names
    assert "molo" in names


def test_roll_up_sum_scales_with_cells() -> None:
    da = _grid(values_const=1.0)
    result_mean = roll_up(da, [NAKURU_COUNTY], reducer="mean")
    result_sum = roll_up(da, [NAKURU_COUNTY], reducer="sum")
    assert float(result_sum.values.mean()) > float(result_mean.values.mean())


def test_roll_up_with_callable_reducer() -> None:
    da = _grid(values_const=3.0)
    result = roll_up(
        da, [NAKURU_COUNTY], reducer=lambda x: x.max(dim=("lat", "lon"))
    )
    np.testing.assert_allclose(result.values, 3.0)


def test_roll_up_rejects_empty_regions() -> None:
    with pytest.raises(AngaGridError, match="regions list cannot be empty"):
        roll_up(_grid(), [])


def test_roll_up_rejects_missing_lat_lon() -> None:
    times = pd.date_range("1991-01-01", "1991-01-31", freq="D")
    da = xr.DataArray(np.ones(len(times)), coords={"time": times}, dims=["time"])
    with pytest.raises(AngaGridError, match="lat"):
        roll_up(da, [NAKURU_COUNTY])


def test_roll_up_rejects_unknown_reducer() -> None:
    with pytest.raises(AngaGridError, match="unknown reducer"):
        roll_up(_grid(), [NAKURU_COUNTY], reducer="garbage")


def test_roll_up_rejects_region_outside_grid() -> None:
    da = _grid()
    far_away = AdminRegion(
        name="middle-pacific",
        level="county",
        bbox=BoundingBox(min_lat=-5, max_lat=-4, min_lon=-180, max_lon=-179),
    )
    with pytest.raises(AngaGridError, match="no grid cells"):
        roll_up(da, [far_away])


def test_roll_up_extends_manifest_history() -> None:
    da = _grid(values_const=2.0)
    da.attrs["source"] = "CHIRPS-2.0"
    result = roll_up(da, list(NAKURU_WARDS))
    assert "history" in result.attrs
    operations = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "roll_up" in operations


def test_roll_up_with_descending_latitude() -> None:
    base = _grid()
    flipped = base.reindex(lat=base["lat"].values[::-1])
    result = roll_up(flipped, [NAKURU_COUNTY])
    np.testing.assert_allclose(result.values, 1.0)


def test_admin_region_constants_well_formed() -> None:
    for ward in NAKURU_WARDS:
        assert ward.level == "ward"
        assert ward.code.startswith("NKR-")
        assert ward.bbox.lat_span > 0
        assert ward.bbox.lon_span > 0
    assert NAKURU_COUNTY.level == "county"
