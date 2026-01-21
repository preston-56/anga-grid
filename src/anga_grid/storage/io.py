from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.exceptions import AngaGridError
from anga_grid.storage.format import Format, ZarrMode, detect_format

if TYPE_CHECKING:
    import xarray as xr


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
