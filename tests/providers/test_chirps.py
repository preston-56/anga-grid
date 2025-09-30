from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import xarray as xr

from anga_grid.exceptions import ProviderError
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.types import BoundingBox, TimeRange
from tests.fixtures.synthetic import synthetic_chirps


@pytest.fixture
def synthetic_nc(tmp_path: Path) -> Path:
    ds = synthetic_chirps(start="1991-01-01", end="1991-03-31")
    nc_path = tmp_path / "chirps-1991-q1.nc"
    ds.to_netcdf(nc_path)
    return nc_path


def test_fetch_without_override_raises(tmp_path: Path) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path)
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="not wired in v0.1"):
        provider.fetch(bbox, tr)


def test_fetch_with_override_returns_dataset(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 3, 31))
    ds = provider.fetch(bbox, tr)
    assert "precip" in ds.data_vars
    assert ds.sizes["time"] > 0


def test_fetch_subset_respects_bbox(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(
        min_lat=-0.5, max_lat=-0.3, min_lon=35.8, max_lon=36.1
    )
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert float(ds["lat"].min()) >= bbox.min_lat - 0.06
    assert float(ds["lat"].max()) <= bbox.max_lat + 0.06
    assert float(ds["lon"].min()) >= bbox.min_lon - 0.06
    assert float(ds["lon"].max()) <= bbox.max_lon + 0.06


def test_fetch_subset_respects_time(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 2, 1), end=date(1991, 2, 28))
    ds = provider.fetch(bbox, tr)
    times = ds["time"].dt
    assert int(times.month.min()) == 2
    assert int(times.month.max()) == 2


def test_fetch_writes_provenance_attrs(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert ds.attrs["provider"] == "chirps-v2.0"
    assert "subset_bbox" in ds.attrs
    assert "subset_time" in ds.attrs
    assert "retrieved_at" in ds.attrs
    assert "bias_caveat" in ds.attrs


def test_fetch_canonicalizes_alternate_coord_names(tmp_path: Path) -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-01-31")
    renamed = ds.rename({"lat": "latitude", "lon": "longitude"})
    path = tmp_path / "alt-names.nc"
    renamed.to_netcdf(path)

    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=path)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    out = provider.fetch(bbox, tr)
    assert "lat" in out.coords
    assert "lon" in out.coords


def test_fetch_canonicalizes_alternate_var_name(tmp_path: Path) -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-01-31")
    renamed = ds.rename({"precip": "precipitation"})
    path = tmp_path / "alt-var.nc"
    renamed.to_netcdf(path)

    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=path)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    out = provider.fetch(bbox, tr)
    assert "precip" in out.data_vars


def test_fetch_raises_on_missing_source(tmp_path: Path) -> None:
    provider = CHIRPSProvider(
        cache_dir=tmp_path, source_override=tmp_path / "no-such-file.nc"
    )
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="not found"):
        provider.fetch(bbox, tr)


def test_fetch_raises_on_no_precip_variable(tmp_path: Path) -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-01-31").rename(
        {"precip": "rain_mystery"}
    )
    path = tmp_path / "wrong-var.nc"
    ds.to_netcdf(path)

    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=path)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="none of"):
        provider.fetch(bbox, tr)


def test_fetch_raises_on_empty_time_subset(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(2050, 1, 1), end=date(2050, 12, 31))
    with pytest.raises(ProviderError, match="empty along time"):
        provider.fetch(bbox, tr)


def test_provider_implements_protocol() -> None:
    from anga_grid.providers.base import Provider

    p = CHIRPSProvider(cache_dir=Path("/tmp"))
    assert isinstance(p, Provider)


def test_canonical_dataset_passes_roundtrip(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 2, 28))
    ds = provider.fetch(bbox, tr)
    written = tmp_path / "roundtrip.nc"
    ds.to_netcdf(written)
    reread = xr.open_dataset(written)
    assert "precip" in reread.data_vars
    assert reread.sizes["time"] == ds.sizes["time"]
