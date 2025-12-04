from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError

if TYPE_CHECKING:
    import xarray as xr


PRECIP_CANDIDATES: tuple[str, ...] = ("precip", "precipitation", "rainfall")

_COORD_RENAMES: tuple[tuple[str, str], ...] = (
    ("latitude", "lat"),
    ("y", "lat"),
    ("longitude", "lon"),
    ("x", "lon"),
    ("T", "time"),
)


def canonicalize(ds: xr.Dataset) -> xr.Dataset:
    renames: dict[str, str] = {}
    for source, target in _COORD_RENAMES:
        if (source in ds.coords or source in ds.dims) and (
            target not in ds.coords and target not in ds.dims
        ):
            renames[source] = target
    if renames:
        ds = ds.rename(renames)
    return ds


def find_precip(ds: xr.Dataset) -> str:
    for candidate in PRECIP_CANDIDATES:
        if candidate in ds.data_vars:
            return candidate
    raise ProviderError(
        f"none of {PRECIP_CANDIDATES} found in dataset; "
        f"variables are {list(ds.data_vars)}"
    )
