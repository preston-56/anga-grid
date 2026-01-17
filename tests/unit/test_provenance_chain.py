from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from anga_grid.indicators import compute_spi, detect_onset
from anga_grid.provenance import read
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.season import SEASONS
from anga_grid.synthetic.chirps import synthetic_chirps_multiyear
from anga_grid.types import BoundingBox, TimeRange


@pytest.fixture
def chirps_dataset(tmp_path: Path):
    ds = synthetic_chirps_multiyear(years=(1991, 1993))
    p = tmp_path / "synthetic.nc"
    ds.to_netcdf(p)
    provider = CHIRPSProvider(cache_dir=tmp_path / "cache", source_override=p)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1993, 12, 31))
    return provider.fetch(bbox, tr)


def test_chirps_manifest_records_fetch(chirps_dataset) -> None:
    manifest = read(chirps_dataset)
    assert manifest.source == "CHIRPS-2.0"
    operations = [s.operation for s in manifest.steps]
    assert "fetch" in operations


def test_spi_extends_manifest_history(chirps_dataset) -> None:
    spi = compute_spi(
        chirps_dataset["precip"],
        window_months=3,
        season=SEASONS["long-rains"],
        baseline=(1991, 1993),
    )
    assert "history" in spi.attrs
    parts = spi.attrs["history"].split(" | ")
    operations = [p.split("|")[1] for p in parts]
    assert "fetch" in operations
    assert "compute_spi" in operations


def test_onset_extends_manifest_history(chirps_dataset) -> None:
    onset = detect_onset(chirps_dataset["precip"], season=SEASONS["long-rains"])
    assert "history" in onset.attrs
    operations = [p.split("|")[1] for p in onset.attrs["history"].split(" | ")]
    assert "fetch" in operations
    assert "detect_onset" in operations


def test_indicator_carries_caveats_forward(chirps_dataset) -> None:
    spi = compute_spi(chirps_dataset["precip"], window_months=3)
    assert "caveats" in spi.attrs
    assert "complex topography" in spi.attrs["caveats"]


def test_compute_without_source_skips_manifest_recording() -> None:
    import numpy as np
    import pandas as pd
    import xarray as xr

    times = pd.date_range("1991-01-01", "1992-12-31", freq="D")
    da = xr.DataArray(
        np.random.default_rng(0).random(len(times)).astype("float32"),
        coords={"time": times},
        dims=["time"],
    )
    spi = compute_spi(da, window_months=3)
    assert "history" not in spi.attrs
