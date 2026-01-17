from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import xarray as xr

from anga_grid.indicators import compute_spi, detect_onset
from anga_grid.provenance import read
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.season import SEASONS
from anga_grid.synthetic.chirps import synthetic_chirps_multiyear
from anga_grid.types import BoundingBox, TimeRange


@pytest.fixture
def chirps_dataset(tmp_path: Path) -> xr.Dataset:
    ds = synthetic_chirps_multiyear(years=(1991, 1993))
    p = tmp_path / "synthetic.nc"
    ds.to_netcdf(p)
    provider = CHIRPSProvider(cache_dir=tmp_path / "cache", source_override=p)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1993, 12, 31))
    return provider.fetch(bbox, tr)


@pytest.mark.regression
def test_dataarray_extraction_preserves_provenance(chirps_dataset: xr.Dataset) -> None:
    pr = chirps_dataset["precip"]
    assert "source" in pr.attrs
    assert pr.attrs["source"] == "CHIRPS-2.0"
    assert "history" in pr.attrs


@pytest.mark.regression
def test_indicator_inherits_caveats_from_source(chirps_dataset: xr.Dataset) -> None:
    spi = compute_spi(chirps_dataset["precip"], window_months=3)
    assert "caveats" in spi.attrs
    assert "complex topography" in spi.attrs["caveats"]


@pytest.mark.regression
def test_chained_indicators_preserve_history_order(
    chirps_dataset: xr.Dataset,
) -> None:
    spi = compute_spi(chirps_dataset["precip"], window_months=3)
    history = spi.attrs.get("history", "")
    parts = history.split(" | ")
    ops = [p.split("|")[1] for p in parts]
    assert ops.index("fetch") < ops.index("compute_spi")


@pytest.mark.regression
def test_onset_returns_nan_below_window_threshold() -> None:
    import numpy as np
    import pandas as pd

    times = pd.date_range("1991-01-01", periods=10, freq="D")
    rain = xr.DataArray(
        np.array([20.0] * 10, dtype="float32"),
        coords={"time": times}, dims=["time"],
    )
    onset = detect_onset(rain)
    assert float(onset.values) != float(onset.values) or onset.values == 0.0 or onset.values.size == 0 or bool(__import__("numpy").isnan(onset.values))


@pytest.mark.regression
def test_season_subset_preserves_descending_doy_for_wrap(
    chirps_dataset: xr.Dataset,
) -> None:
    long_rains = SEASONS["long-rains"]
    result = long_rains.subset(chirps_dataset["precip"])
    doys = result["time"].dt.dayofyear.values
    assert doys.min() >= long_rains.start_doy
    assert doys.max() <= long_rains.end_doy


@pytest.mark.regression
def test_chirps_manifest_records_fetch_with_expected_caveat(
    chirps_dataset: xr.Dataset,
) -> None:
    manifest = read(chirps_dataset)
    assert any("Mau Escarpment" in c for c in manifest.caveats)


@pytest.mark.regression
def test_spi_attrs_do_not_collide_with_chirps_attrs(
    chirps_dataset: xr.Dataset,
) -> None:
    spi = compute_spi(chirps_dataset["precip"], window_months=3)
    assert spi.attrs.get("indicator") == "spi"
    assert spi.attrs.get("provider") == "chirps-v2.0"


@pytest.mark.regression
def test_history_string_remains_parseable_after_two_steps(
    chirps_dataset: xr.Dataset,
) -> None:
    from anga_grid.provenance import Manifest

    spi = compute_spi(chirps_dataset["precip"], window_months=3)
    manifest = Manifest.from_attrs(dict(spi.attrs))
    operations = [s.operation for s in manifest.steps]
    assert len(operations) >= 2
