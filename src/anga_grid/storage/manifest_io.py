from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.provenance import Manifest, read, stamp
from anga_grid.storage.format import Format
from anga_grid.storage.io import open_dataset, write

if TYPE_CHECKING:
    import xarray as xr


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
