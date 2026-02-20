from __future__ import annotations

from pathlib import Path
from typing import Literal

from anga_grid.exceptions import AngaGridError

Format = Literal["zarr", "netcdf"]
ZarrMode = Literal["w", "w-", "a", "a-", "r+", "r"]


_NETCDF_SUFFIXES: tuple[str, ...] = (".nc", ".nc4", ".netcdf", ".cdf")


def detect_format(path: Path) -> Format:
    name = path.name.lower()
    if name.endswith(".zarr") or path.is_dir():
        return "zarr"
    if any(name.endswith(suffix) for suffix in _NETCDF_SUFFIXES):
        return "netcdf"
    raise AngaGridError(
        f"cannot infer format from {path}; use .zarr or one of {_NETCDF_SUFFIXES}"
    )
