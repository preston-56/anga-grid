from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest, read, stamp

if TYPE_CHECKING:
    import xarray as xr


Format = Literal["zarr", "netcdf"]


def detect_format(path: Path) -> Format:
    name = path.name.lower()
    if name.endswith(".zarr") or path.is_dir():
        return "zarr"
    if name.endswith(".nc") or name.endswith(".nc4") or name.endswith(".netcdf"):
        return "netcdf"
    raise AngaGridError(
        f"cannot infer format from {path}; use .zarr or .nc / .nc4"
    )


ZarrMode = Literal["w", "w-", "a", "a-", "r+", "r"]


def write(
    obj: xr.Dataset | xr.DataArray,
    path: Path,
    *,
    fmt: Format | None = None,
    mode: ZarrMode = "w",
) -> Path:
    import xarray as xr

    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt is None:
        fmt = detect_format(path)

    if isinstance(obj, xr.DataArray):
        ds = obj.to_dataset(name=obj.name or "data")
    else:
        ds = obj

    if fmt == "zarr":
        ds.to_zarr(path, mode=mode)
    elif fmt == "netcdf":
        ds.to_netcdf(path)
    else:
        raise AngaGridError(f"unknown format: {fmt}")
    return path


def open_dataset(
    path: Path, *, fmt: Format | None = None, decode_cf: bool = True
) -> xr.Dataset:
    import xarray as xr

    path = path.expanduser()
    if not path.exists():
        raise AngaGridError(f"file not found: {path}")
    if fmt is None:
        fmt = detect_format(path)

    if fmt == "zarr":
        return xr.open_zarr(path, decode_cf=decode_cf)
    if fmt == "netcdf":
        return xr.open_dataset(path, decode_cf=decode_cf)
    raise AngaGridError(f"unknown format: {fmt}")


def write_with_manifest(
    obj: xr.Dataset | xr.DataArray,
    path: Path,
    manifest: Manifest,
    *,
    operation: str = "write",
    fmt: Format | None = None,
) -> Path:
    import xarray as xr

    if isinstance(obj, xr.DataArray):
        ds = obj.to_dataset(name=obj.name or "data")
    else:
        ds = obj
    manifest.record(operation, path=str(path))
    stamp(ds, manifest)
    return write(ds, path, fmt=fmt)


def read_manifest(path: Path) -> Manifest:
    ds = open_dataset(path)
    return read(ds)
