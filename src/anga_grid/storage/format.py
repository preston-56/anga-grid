from __future__ import annotations

from pathlib import Path
from typing import Literal

from anga_grid.exceptions import AngaGridError

Format = Literal["zarr", "netcdf"]
ZarrMode = Literal["w", "w-", "a", "a-", "r+", "r"]


def detect_format(path: Path) -> Format:
    name = path.name.lower()
    if name.endswith(".zarr") or path.is_dir():
        return "zarr"
    if name.endswith(".nc") or name.endswith(".nc4") or name.endswith(".netcdf"):
        return "netcdf"
    raise AngaGridError(
        f"cannot infer format from {path}; use .zarr or .nc / .nc4"
    )
