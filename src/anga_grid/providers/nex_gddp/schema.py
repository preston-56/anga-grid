from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError

if TYPE_CHECKING:
    import xarray as xr


VARIABLE_RENAMES: dict[str, str] = {
    "tas": "tas_mean",
    "tasmin": "tas_min",
    "tasmax": "tas_max",
    "pr": "precipitation",
    "huss": "specific_humidity",
    "rsds": "shortwave_radiation",
    "sfcWind": "wind_speed",
}

UNIT_CONVERSIONS: dict[str, tuple[str, float, float]] = {
    "tas_mean": ("degC", 1.0, -273.15),
    "tas_min": ("degC", 1.0, -273.15),
    "tas_max": ("degC", 1.0, -273.15),
    "precipitation": ("mm/day", 86400.0, 0.0),
}

_COORD_RENAMES: tuple[tuple[str, str], ...] = (
    ("latitude", "lat"),
    ("longitude", "lon"),
    ("y", "lat"),
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
        for source, target in VARIABLE_RENAMES.items()
        if source in ds.data_vars and target not in ds.data_vars
    }
    if var_renames:
        ds = ds.rename(var_renames)
    return ds


def convert_units(ds: xr.Dataset) -> xr.Dataset:
    for var_name, (target_unit, multiplier, offset) in UNIT_CONVERSIONS.items():
        if var_name not in ds.data_vars:
            continue
        var = ds[var_name]
        current = var.attrs.get("units", "")
        if current == target_unit:
            continue
        converted = var * multiplier + offset
        converted.attrs.update(var.attrs)
        converted.attrs["units"] = target_unit
        converted.attrs["unit_conversion"] = (
            f"from {current!r}: x*{multiplier}+{offset}"
        )
        ds = ds.assign({var_name: converted})
    return ds


def validate_required_variables(
    ds: xr.Dataset, requested: tuple[str, ...]
) -> xr.Dataset:
    missing = [v for v in requested if v not in ds.data_vars]
    if missing:
        raise ProviderError(
            f"NEX-GDDP dataset missing requested variables: {missing}; "
            f"available: {list(ds.data_vars)}"
        )
    return ds
