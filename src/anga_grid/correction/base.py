from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


def validate_pair(source: xr.DataArray, reference: xr.DataArray) -> None:
    if "time" not in source.dims or "time" not in reference.dims:
        raise AngaGridError("both source and reference must have a 'time' dimension")
    if source.shape[1:] != reference.shape[1:]:
        raise AngaGridError(
            f"spatial shapes differ: {source.shape[1:]} vs {reference.shape[1:]}"
        )


def stamp_correction(
    result: xr.DataArray, source: xr.DataArray, method: str
) -> None:
    result.attrs.update(source.attrs)
    result.attrs["bias_corrected"] = method
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record("bias_correction", method=method)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
