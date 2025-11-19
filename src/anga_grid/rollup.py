from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest
from anga_grid.types import BoundingBox

if TYPE_CHECKING:
    import xarray as xr

Reducer = str | Callable[["xr.DataArray"], "xr.DataArray"]


@dataclass(frozen=True, slots=True)
class AdminRegion:
    name: str
    level: str
    bbox: BoundingBox
    code: str = ""


NAKURU_WARDS: tuple[AdminRegion, ...] = (
    AdminRegion(
        name="njoro",
        level="ward",
        code="NKR-NJR",
        bbox=BoundingBox(min_lat=-0.40, max_lat=-0.25, min_lon=35.90, max_lon=36.05),
    ),
    AdminRegion(
        name="molo",
        level="ward",
        code="NKR-MOL",
        bbox=BoundingBox(min_lat=-0.30, max_lat=-0.15, min_lon=35.70, max_lon=35.85),
    ),
    AdminRegion(
        name="rongai",
        level="ward",
        code="NKR-RNG",
        bbox=BoundingBox(min_lat=-0.20, max_lat=0.05, min_lon=35.85, max_lon=36.05),
    ),
    AdminRegion(
        name="kuresoi-north",
        level="ward",
        code="NKR-KRN",
        bbox=BoundingBox(min_lat=-0.40, max_lat=-0.20, min_lon=35.50, max_lon=35.75),
    ),
)

NAKURU_COUNTY = AdminRegion(
    name="nakuru",
    level="county",
    code="NKR",
    bbox=BoundingBox(min_lat=-1.20, max_lat=0.05, min_lon=35.55, max_lon=36.55),
)


def roll_up(
    da: xr.DataArray,
    regions: list[AdminRegion] | tuple[AdminRegion, ...],
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
        slab = _subset_to_region(da, region.bbox)
        if slab.size == 0 or slab.sizes.get("lat", 0) == 0 or slab.sizes.get("lon", 0) == 0:
            raise AngaGridError(
                f"no grid cells fall within region {region.name!r}"
            )
        reduced = _apply_reducer(slab, reducer)
        per_region.append(reduced)

    stacked = xr.concat(per_region, dim=name_dim)
    stacked = stacked.assign_coords({name_dim: [r.name for r in regions]})

    _stamp_history(stacked, da, regions, reducer)
    return stacked


def _subset_to_region(da: xr.DataArray, bbox: BoundingBox) -> xr.DataArray:
    lat_descending = (
        da["lat"].size > 1 and float(da["lat"][0]) > float(da["lat"][-1])
    )
    lat_slice = (
        slice(bbox.max_lat, bbox.min_lat)
        if lat_descending
        else slice(bbox.min_lat, bbox.max_lat)
    )
    return da.sel(
        lat=lat_slice,
        lon=slice(bbox.min_lon, bbox.max_lon),
    )


def _apply_reducer(slab: xr.DataArray, reducer: Reducer) -> xr.DataArray:
    if callable(reducer):
        return reducer(slab)
    op = reducer.lower()
    if op == "mean":
        return slab.mean(dim=("lat", "lon"), skipna=True)
    if op == "sum":
        return slab.sum(dim=("lat", "lon"), skipna=True)
    if op == "max":
        return slab.max(dim=("lat", "lon"), skipna=True)
    if op == "min":
        return slab.min(dim=("lat", "lon"), skipna=True)
    if op == "median":
        return slab.median(dim=("lat", "lon"), skipna=True)
    if op == "count":
        valid = slab.notnull() if slab.dtype.kind == "f" else slab.astype(bool)
        return valid.sum(dim=("lat", "lon"))
    raise AngaGridError(f"unknown reducer: {reducer}")


def _stamp_history(
    result: xr.DataArray,
    source: xr.DataArray,
    regions: list[AdminRegion] | tuple[AdminRegion, ...],
    reducer: Reducer,
) -> None:
    result.attrs.update(source.attrs)
    result.attrs["rollup_regions"] = ",".join(r.name for r in regions)
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    reducer_name = reducer if isinstance(reducer, str) else getattr(
        reducer, "__name__", "callable"
    )
    manifest.record(
        "roll_up",
        regions=",".join(r.name for r in regions),
        reducer=reducer_name,
    )
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
