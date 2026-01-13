from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import AngaGridError
from anga_grid.rollup import PolygonRegion, polygon_roll_up
from anga_grid.rollup.polygon import _points_in_polygon


def _grid(values_const: float = 1.0) -> xr.DataArray:
    times = pd.date_range("1991-01-01", "1991-01-31", freq="D")
    lats = np.linspace(-1.0, 0.0, 21, dtype="float64")
    lons = np.linspace(35.0, 36.0, 21, dtype="float64")
    data = (
        np.ones((len(times), len(lats), len(lons)), dtype="float32") * values_const
    )
    return xr.DataArray(
        data, coords={"time": times, "lat": lats, "lon": lons},
        dims=["time", "lat", "lon"],
    )


def test_polygon_region_from_points_normalises_floats() -> None:
    region = PolygonRegion.from_points(
        "test", [(-1, 35), (-1, 36), (0, 36), (0, 35)]
    )
    assert all(isinstance(lat, float) for lat, _ in region.ring)


def test_polygon_region_rejects_too_few_vertices() -> None:
    with pytest.raises(AngaGridError, match="at least 3"):
        PolygonRegion.from_points("triangle?", [(0, 0), (1, 1)])


def test_polygon_bbox_property_matches_extents() -> None:
    region = PolygonRegion.from_points(
        "box", [(-1, 35), (-1, 36), (0, 36), (0, 35)]
    )
    bbox = region.bbox
    assert bbox == (-1.0, 35.0, 0.0, 36.0)


def test_points_in_polygon_classifies_centre_and_corner() -> None:
    ring = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0))
    lats = np.array([5.0, -1.0, 11.0, 5.0])
    lons = np.array([5.0, 5.0, 5.0, 11.0])
    inside = _points_in_polygon(lats, lons, ring)
    assert bool(inside[0]) is True
    assert bool(inside[1]) is False
    assert bool(inside[2]) is False
    assert bool(inside[3]) is False


def test_polygon_roll_up_constant_field_returns_constant() -> None:
    da = _grid(values_const=4.0)
    region = PolygonRegion.from_points(
        "interior",
        [(-0.8, 35.2), (-0.8, 35.8), (-0.2, 35.8), (-0.2, 35.2)],
    )
    result = polygon_roll_up(da, [region])
    np.testing.assert_allclose(result.values, 4.0)


def test_polygon_roll_up_two_regions() -> None:
    da = _grid()
    a = PolygonRegion.from_points(
        "north", [(-0.4, 35.2), (-0.4, 35.8), (-0.1, 35.8), (-0.1, 35.2)]
    )
    b = PolygonRegion.from_points(
        "south", [(-0.9, 35.2), (-0.9, 35.8), (-0.6, 35.8), (-0.6, 35.2)]
    )
    result = polygon_roll_up(da, [a, b])
    assert "region" in result.dims
    assert result.sizes["region"] == 2
    assert list(result["region"].values) == ["north", "south"]


def test_polygon_roll_up_rejects_polygon_outside_grid() -> None:
    da = _grid()
    far = PolygonRegion.from_points(
        "pacific", [(-30.0, -150.0), (-30.0, -149.0), (-29.0, -149.0)]
    )
    with pytest.raises(AngaGridError, match="no grid cells"):
        polygon_roll_up(da, [far])


def test_polygon_roll_up_rejects_unknown_reducer() -> None:
    da = _grid()
    region = PolygonRegion.from_points(
        "interior", [(-0.8, 35.2), (-0.8, 35.8), (-0.2, 35.5)]
    )
    with pytest.raises(AngaGridError, match="unknown reducer"):
        polygon_roll_up(da, [region], reducer="garbage")


def test_polygon_roll_up_with_callable_reducer() -> None:
    da = _grid(values_const=3.0)
    region = PolygonRegion.from_points(
        "interior", [(-0.8, 35.2), (-0.8, 35.8), (-0.2, 35.8), (-0.2, 35.2)]
    )
    result = polygon_roll_up(
        da, [region], reducer=lambda x: x.max(dim=("lat", "lon"))
    )
    np.testing.assert_allclose(result.values, 3.0)


def test_polygon_roll_up_extends_manifest_history() -> None:
    da = _grid()
    da.attrs["source"] = "synthetic"
    region = PolygonRegion.from_points(
        "interior", [(-0.8, 35.2), (-0.8, 35.8), (-0.2, 35.8), (-0.2, 35.2)]
    )
    result = polygon_roll_up(da, [region])
    operations = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "polygon_roll_up" in operations


def test_polygon_roll_up_rejects_empty_regions() -> None:
    with pytest.raises(AngaGridError, match="regions list cannot be empty"):
        polygon_roll_up(_grid(), [])


def test_polygon_roll_up_rejects_missing_lat_lon() -> None:
    times = pd.date_range("1991-01-01", periods=10, freq="D")
    da = xr.DataArray(np.ones(len(times)), coords={"time": times}, dims=["time"])
    region = PolygonRegion.from_points(
        "x", [(-1, 35), (-1, 36), (0, 36), (0, 35)]
    )
    with pytest.raises(AngaGridError, match="lat"):
        polygon_roll_up(da, [region])


def test_polygon_roll_up_carries_polygon_regions_attr() -> None:
    da = _grid()
    region = PolygonRegion.from_points(
        "interior", [(-0.8, 35.2), (-0.8, 35.8), (-0.2, 35.8), (-0.2, 35.2)]
    )
    result = polygon_roll_up(da, [region])
    assert "polygon_regions" in result.attrs
    assert "interior" in result.attrs["polygon_regions"]
