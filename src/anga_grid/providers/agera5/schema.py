from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.providers.agera5.variables import AGERA5_VAR_RENAMES

if TYPE_CHECKING:
    import xarray as xr


_COORD_RENAMES: tuple[tuple[str, str], ...] = (
    ("latitude", "lat"),
    ("y", "lat"),
    ("longitude", "lon"),
    ("x", "lon"),
    ("T", "time"),
)


def canonicalize(ds: xr.Dataset) -> xr.Dataset:
    coord_renames: dict[str, str] = {}
    for source, target in _COORD_RENAMES:
        if (source in ds.coords or source in ds.dims) and (
            target not in ds.coords and target not in ds.dims
        ):
            coord_renames[source] = target
    if coord_renames:
        ds = ds.rename(coord_renames)

    var_renames = {
        source: target
        for source, target in AGERA5_VAR_RENAMES.items()
        if source in ds.data_vars and target not in ds.data_vars
    }
    if var_renames:
        ds = ds.rename(var_renames)
    return ds
