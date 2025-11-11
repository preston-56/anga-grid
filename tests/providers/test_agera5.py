from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from anga_grid.exceptions import ProviderError
from anga_grid.provenance import read
from anga_grid.providers.agera5 import AGERA5_DEFAULT_VARIABLES, AgERA5Provider
from anga_grid.types import BoundingBox, TimeRange
from tests.fixtures.agera5 import synthetic_agera5


@pytest.fixture
def synthetic_nc(tmp_path: Path) -> Path:
    ds = synthetic_agera5(start="1991-01-01", end="1991-03-31")
    p = tmp_path / "agera5.nc"
    ds.to_netcdf(p)
    return p


def test_fetch_without_override_raises(tmp_path: Path) -> None:
    provider = AgERA5Provider(cache_dir=tmp_path)
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="not wired in v0.2"):
        provider.fetch(bbox, tr)


def test_fetch_returns_all_default_variables(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 3, 31))
    ds = provider.fetch(bbox, tr)
    for var in AGERA5_DEFAULT_VARIABLES:
        assert var in ds.data_vars, f"missing {var}"


def test_fetch_subset_by_variable_selection(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = AgERA5Provider(
        cache_dir=tmp_path,
        source_override=synthetic_nc,
        variables=("temperature_air_mean_daily",),
    )
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert set(ds.data_vars) == {"temperature_air_mean_daily"}


def test_fetch_stamps_manifest_with_caveat(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    manifest = read(ds)
    assert manifest.source == "AgERA5-v1.1"
    assert any("ERA5" in c for c in manifest.caveats)
    operations = [s.operation for s in manifest.steps]
    assert "fetch" in operations


def test_fetch_stamps_per_variable_attrs(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    for var in ds.data_vars:
        assert ds[var].attrs.get("source") == "AgERA5-v1.1"


def test_canonicalize_capitalized_var_names(tmp_path: Path) -> None:
    ds = synthetic_agera5(start="1991-01-01", end="1991-01-31")
    renamed = ds.rename({
        "temperature_air_mean_daily": "Temperature_Air_Mean_Daily",
        "precipitation_flux": "Precipitation_Flux",
    })
    p = tmp_path / "caps.nc"
    renamed.to_netcdf(p)
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=p)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    out = provider.fetch(bbox, tr)
    assert "temperature_air_mean_daily" in out.data_vars
    assert "precipitation_flux" in out.data_vars


def test_fetch_subset_respects_bbox(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-0.5, max_lat=-0.3, min_lon=35.8, max_lon=36.1)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert float(ds["lat"].min()) >= bbox.min_lat - 0.11
    assert float(ds["lat"].max()) <= bbox.max_lat + 0.11


def test_fetch_raises_on_missing_source(tmp_path: Path) -> None:
    provider = AgERA5Provider(
        cache_dir=tmp_path, source_override=tmp_path / "no-such-file.nc"
    )
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    with pytest.raises(ProviderError, match="not found"):
        provider.fetch(bbox, tr)


def test_fetch_raises_on_empty_time_subset(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(2050, 1, 1), end=date(2050, 12, 31))
    with pytest.raises(ProviderError, match="empty along time"):
        provider.fetch(bbox, tr)


def test_fetch_from_directory_of_netcdfs(tmp_path: Path) -> None:
    full = synthetic_agera5(start="1991-01-01", end="1991-01-31")
    src_dir = tmp_path / "agera5-files"
    src_dir.mkdir()
    for var in ("temperature_air_mean_daily", "precipitation_flux"):
        full[[var]].to_netcdf(src_dir / f"{var}.nc")

    provider = AgERA5Provider(cache_dir=tmp_path, source_override=src_dir)
    bbox = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
    tr = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert "temperature_air_mean_daily" in ds.data_vars
    assert "precipitation_flux" in ds.data_vars


def test_provider_implements_protocol() -> None:
    from anga_grid.providers.base import Provider

    p = AgERA5Provider(cache_dir=Path("/tmp"))
    assert isinstance(p, Provider)
