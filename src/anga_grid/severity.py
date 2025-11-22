from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr


@dataclass(frozen=True, slots=True)
class SeverityBand:
    code: int
    label: str
    lower: float
    upper: float


KMD_SPI_BANDS: tuple[SeverityBand, ...] = (
    SeverityBand(code=-3, label="extreme drought", lower=float("-inf"), upper=-2.0),
    SeverityBand(code=-2, label="severe drought", lower=-2.0, upper=-1.5),
    SeverityBand(code=-1, label="moderate drought", lower=-1.5, upper=-1.0),
    SeverityBand(code=0, label="near normal", lower=-1.0, upper=1.0),
    SeverityBand(code=1, label="moderately wet", lower=1.0, upper=1.5),
    SeverityBand(code=2, label="severely wet", lower=1.5, upper=2.0),
    SeverityBand(code=3, label="extremely wet", lower=2.0, upper=float("inf")),
)


NDMA_LABELS: dict[str, tuple[float, float]] = {
    "normal": (-1.0, float("inf")),
    "alert": (-1.5, -1.0),
    "alarm": (-2.0, -1.5),
    "emergency": (float("-inf"), -2.0),
}


def classify_spi(
    spi: xr.DataArray,
    bands: tuple[SeverityBand, ...] = KMD_SPI_BANDS,
) -> xr.DataArray:
    import xarray as xr

    if not bands:
        raise AngaGridError("bands tuple cannot be empty")

    out = xr.full_like(spi, fill_value=0, dtype="int8")
    out = xr.where(spi <= -2.0, -3, out)
    out = xr.where((spi > -2.0) & (spi <= -1.5), -2, out)
    out = xr.where((spi > -1.5) & (spi <= -1.0), -1, out)
    out = xr.where((spi > -1.0) & (spi < 1.0), 0, out)
    out = xr.where((spi >= 1.0) & (spi < 1.5), 1, out)
    out = xr.where((spi >= 1.5) & (spi < 2.0), 2, out)
    out = xr.where(spi >= 2.0, 3, out)

    out.attrs.update(spi.attrs)
    out.attrs["classification"] = "spi_severity"
    out.attrs["band_codes"] = ",".join(str(b.code) for b in bands)
    out.attrs["band_labels"] = ",".join(b.label for b in bands)

    _record_history(out, "classify_spi", len(bands))
    return out


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


def severity_summary(
    classified: xr.DataArray,
    bands: tuple[SeverityBand, ...] = KMD_SPI_BANDS,
) -> dict[str, float]:
    if classified.attrs.get("classification") != "spi_severity":
        raise AngaGridError(
            "summary expects an SPI severity classification output"
        )
    total = int(classified.size)
    if total == 0:
        return {b.label: 0.0 for b in bands}
    counts: dict[str, int] = {b.label: 0 for b in bands}
    values = classified.values
    for band in bands:
        counts[band.label] = int(np.sum(values == band.code))
    return {label: count / total for label, count in counts.items()}


def _record_history(
    result: xr.DataArray, operation: str, n_bands: int
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record(operation, n_bands=n_bands)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
