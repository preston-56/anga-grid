from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


PolygonRing = Sequence[tuple[float, float]]
Reducer = str | Callable[["xr.DataArray"], "xr.DataArray"]


@dataclass(frozen=True, slots=True)
class PolygonRegion:
    name: str
    ring: tuple[tuple[float, float], ...]
    code: str = ""

    @classmethod
    def from_points(
        cls, name: str, points: PolygonRing, code: str = ""
    ) -> PolygonRegion:
        if len(points) < 3:
            raise AngaGridError(
                f"polygon ring needs at least 3 vertices, got {len(points)}"
            )
        normalized = tuple((float(lat), float(lon)) for lat, lon in points)
        return cls(name=name, ring=normalized, code=code)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        lats = [p[0] for p in self.ring]
        lons = [p[1] for p in self.ring]
        return min(lats), min(lons), max(lats), max(lons)


def polygon_roll_up(
    da: xr.DataArray,
    regions: list[PolygonRegion] | tuple[PolygonRegion, ...],
    *,
    reducer: Reducer = "mean",
    name_dim: str = "region",
) -> xr.DataArray:
    import xarray as xr

    if not regions:
        raise AngaGridError("regions list cannot be empty")
    if "lat" not in da.dims or "lon" not in da.dims:
        raise AngaGridError("input DataArray must have 'lat' and 'lon' dims")

    per_region: list[xr.DataArray] = []
    for region in regions:
        mask = _ray_cast_mask(da, region)
        masked = da.where(mask)
        if int(mask.sum().item()) == 0:
            raise AngaGridError(
                f"no grid cells fall within polygon region {region.name!r}"
            )
        reduced = _apply_reducer(masked, reducer)
        per_region.append(reduced)

    stacked = xr.concat(per_region, dim=name_dim)
    stacked = stacked.assign_coords({name_dim: [r.name for r in regions]})

    _stamp_history(stacked, da, regions, reducer)
    return stacked


def _ray_cast_mask(da: xr.DataArray, region: PolygonRegion) -> xr.DataArray:
    import xarray as xr

    lats = da["lat"].values
    lons = da["lon"].values
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    mask = _points_in_polygon(lat_grid.ravel(), lon_grid.ravel(), region.ring)
    return xr.DataArray(
        mask.reshape(lat_grid.shape),
        coords={"lat": lats, "lon": lons},
        dims=["lat", "lon"],
    )


def _points_in_polygon(
    lats: np.ndarray, lons: np.ndarray, ring: tuple[tuple[float, float], ...]
) -> np.ndarray:
    n = len(ring)
    inside = np.zeros(lats.shape, dtype=bool)
    for i in range(n):
        lat_a, lon_a = ring[i]
        lat_b, lon_b = ring[(i + 1) % n]
        cond_lat_between = (lats > min(lat_a, lat_b)) & (lats <= max(lat_a, lat_b))
        if lat_b == lat_a:
            continue
        x_intersect = (lats - lat_a) * (lon_b - lon_a) / (lat_b - lat_a) + lon_a
        crossing = cond_lat_between & (lons < x_intersect)
        inside ^= crossing
    return inside


def _apply_reducer(masked: xr.DataArray, reducer: Reducer) -> xr.DataArray:
    if callable(reducer):
        return reducer(masked)
    op = reducer.lower()
    if op == "mean":
        return masked.mean(dim=("lat", "lon"), skipna=True)
    if op == "sum":
        return masked.sum(dim=("lat", "lon"), skipna=True)
    if op == "max":
        return masked.max(dim=("lat", "lon"), skipna=True)
    if op == "min":
        return masked.min(dim=("lat", "lon"), skipna=True)
    if op == "median":
        return masked.median(dim=("lat", "lon"), skipna=True)
    raise AngaGridError(f"unknown reducer: {reducer}")


def _stamp_history(
    result: xr.DataArray,
    source: xr.DataArray,
    regions: list[PolygonRegion] | tuple[PolygonRegion, ...],
    reducer: Reducer,
) -> None:
    result.attrs.update(source.attrs)
    result.attrs["polygon_regions"] = ",".join(r.name for r in regions)
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    reducer_name = reducer if isinstance(reducer, str) else getattr(
        reducer, "__name__", "callable"
    )
    manifest.record(
        "polygon_roll_up",
        regions=",".join(r.name for r in regions),
        reducer=reducer_name,
    )
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
