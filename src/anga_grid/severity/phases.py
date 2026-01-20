from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


NDMA_LABELS: dict[str, tuple[float, float]] = {
    "normal": (-1.0, float("inf")),
    "alert": (-1.5, -1.0),
    "alarm": (-2.0, -1.5),
    "emergency": (float("-inf"), -2.0),
}


def ndma_phase(spi: xr.DataArray) -> xr.DataArray:
    import xarray as xr

    out = xr.full_like(spi, fill_value="normal", dtype=object)
    out = xr.where(spi <= -2.0, "emergency", out)
    out = xr.where((spi > -2.0) & (spi <= -1.5), "alarm", out)
    out = xr.where((spi > -1.5) & (spi <= -1.0), "alert", out)
    out = xr.where(spi > -1.0, "normal", out)

    out.attrs.update(spi.attrs)
    out.attrs["classification"] = "ndma_phase"
    out.attrs["phases"] = ",".join(NDMA_LABELS.keys())

    _record_history(out, "ndma_phase", len(NDMA_LABELS))
    return out


def _record_history(
    result: xr.DataArray, operation: str, n_bands: int
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record(operation, n_bands=n_bands)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
