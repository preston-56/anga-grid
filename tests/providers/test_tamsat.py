from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from anga_grid.exceptions import ProviderError
from anga_grid.provenance import read
from anga_grid.providers.tamsat import TAMSATProvider
from anga_grid.synthetic.tamsat import synthetic_tamsat
from anga_grid.types import BoundingBox, TimeRange


@pytest.fixture
def synthetic_nc(tmp_path: Path) -> Path:
    ds = synthetic_tamsat(start="1991-01-01", end="1991-03-31")
    p = tmp_path / "tamsat.nc"
    ds.to_netcdf(p)
    return p


def test_fetch_without_override_raises(tmp_path: Path) -> None:
    provider = TAMSATProvider(cache_dir=tmp_path)
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="not wired in v0.3"):
        provider.fetch(bbox, tr)


def test_fetch_returns_precip_dataset(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 3, 31))
    ds = provider.fetch(bbox, tr)
    assert "precip" in ds.data_vars
    assert ds.sizes["time"] > 0


def test_fetch_renames_rfe_to_precip(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert "rfe" not in ds.data_vars
    assert "precip" in ds.data_vars


def test_fetch_stamps_manifest_with_convective_caveat(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    manifest = read(ds)
    assert manifest.source == "TAMSAT-v3.1"
    assert any("convective" in c for c in manifest.caveats)


def test_fetch_records_version_in_history(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = TAMSATProvider(
        cache_dir=tmp_path, source_override=synthetic_nc, version="3.1"
    )
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    history = ds.attrs.get("history", "")
    assert "tamsat_version=3.1" in history


def test_fetch_with_rfe_filled_variable_name(tmp_path: Path) -> None:
    ds = synthetic_tamsat(start="1991-01-01", end="1991-01-31").rename(
        {"rfe": "rfe_filled"}
    )
    p = tmp_path / "tamsat-filled.nc"
    ds.to_netcdf(p)
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=p)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    out = provider.fetch(bbox, tr)
    assert "precip" in out.data_vars


def test_fetch_subset_respects_bbox(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-0.5, max_lat=-0.3, min_lon=35.8, max_lon=36.1)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert float(ds["lat"].min()) >= bbox.min_lat - 0.05
    assert float(ds["lat"].max()) <= bbox.max_lat + 0.05


def test_fetch_raises_on_missing_source(tmp_path: Path) -> None:
    provider = TAMSATProvider(
        cache_dir=tmp_path, source_override=tmp_path / "no-such-file.nc"
    )
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="not found"):
        provider.fetch(bbox, tr)


def test_fetch_raises_on_empty_time_subset(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(2050, 1, 1), end=date(2050, 12, 31))
    with pytest.raises(ProviderError, match="empty along time"):
        provider.fetch(bbox, tr)


def test_fetch_raises_on_unknown_variable(tmp_path: Path) -> None:
    ds = synthetic_tamsat(start="1991-01-01", end="1991-01-31").rename(
        {"rfe": "weird_name"}
    )
    p = tmp_path / "bad-var.nc"
    ds.to_netcdf(p)
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=p)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="none of"):
        provider.fetch(bbox, tr)


def test_provider_implements_protocol() -> None:
    from anga_grid.providers.base import Provider

    p = TAMSATProvider(cache_dir=Path("/tmp"))
    assert isinstance(p, Provider)
