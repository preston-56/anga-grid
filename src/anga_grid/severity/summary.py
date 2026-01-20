from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import AngaGridError
from anga_grid.severity.bands import KMD_SPI_BANDS, SeverityBand

if TYPE_CHECKING:
    import xarray as xr


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
