from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import xarray as xr

from anga_grid.providers.agera5 import AgERA5Provider
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.providers.nex_gddp import NEXGDDPProvider
from anga_grid.providers.tamsat import TAMSATProvider
from anga_grid.types import BoundingBox, TimeRange

_FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "data"

_NJORO_BBOX = BoundingBox(
    min_lat=-0.5, max_lat=-0.2, min_lon=35.85, max_lon=36.1
)


def test_chirps_fixture_present_and_well_formed() -> None:
    path = _FIXTURE_DIR / "chirps_njoro_1991.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    assert "precip" in ds.data_vars
    assert ds.sizes["time"] == 365


def test_chirps_multiyear_fixture_spans_five_years() -> None:
    path = _FIXTURE_DIR / "chirps_njoro_1991_1995.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    years = ds["time"].dt.year.values
    assert int(years.min()) == 1991
    assert int(years.max()) == 1995


def test_agera5_fixture_has_eight_default_variables() -> None:
    path = _FIXTURE_DIR / "agera5_njoro_1991_long_rains.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    expected = {
        "temperature_air_mean_daily",
        "temperature_air_min_daily",
        "temperature_air_max_daily",
        "precipitation_flux",
        "solar_radiation_flux",
        "vapour_pressure_daily",
        "wind_speed_10m_mean_daily",
        "relative_humidity_2m_12h",
    }
    assert expected <= set(ds.data_vars)


def test_tamsat_fixture_carries_rfe_variable() -> None:
    path = _FIXTURE_DIR / "tamsat_njoro_1991.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    assert "rfe" in ds.data_vars


def test_nex_gddp_fixture_carries_cmip6_var_names() -> None:
    path = _FIXTURE_DIR / "nex_gddp_njoro_ssp245_2030.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    for name in ("tas", "tasmin", "tasmax", "pr"):
        assert name in ds.data_vars


def test_chirps_provider_consumes_fixture_via_source_override(
    tmp_path: Path,
) -> None:
    fixture = _FIXTURE_DIR / "chirps_njoro_1991.nc"
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=fixture)
    ds = provider.fetch(
        _NJORO_BBOX,
        TimeRange(start=date(1991, 1, 1), end=date(1991, 12, 31)),
    )
    assert "precip" in ds.data_vars
    assert "source" in ds.attrs
    assert ds.attrs["source"] == "CHIRPS-2.0"


def test_agera5_provider_consumes_fixture_via_source_override(
    tmp_path: Path,
) -> None:
    fixture = _FIXTURE_DIR / "agera5_njoro_1991_long_rains.nc"
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=fixture)
    ds = provider.fetch(
        _NJORO_BBOX,
        TimeRange(start=date(1991, 3, 1), end=date(1991, 8, 31)),
    )
    assert "temperature_air_mean_daily" in ds.data_vars


def test_tamsat_provider_consumes_fixture_via_source_override(
    tmp_path: Path,
) -> None:
    fixture = _FIXTURE_DIR / "tamsat_njoro_1991.nc"
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=fixture)
    ds = provider.fetch(
        _NJORO_BBOX,
        TimeRange(start=date(1991, 1, 1), end=date(1991, 12, 31)),
    )
    assert "precip" in ds.data_vars


def test_nex_gddp_provider_consumes_fixture_via_source_override(
    tmp_path: Path,
) -> None:
    fixture = _FIXTURE_DIR / "nex_gddp_njoro_ssp245_2030.nc"
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=fixture)
    ds = provider.fetch(
        _NJORO_BBOX,
        TimeRange(start=date(2030, 1, 1), end=date(2030, 6, 30)),
    )
    assert "tas_mean" in ds.data_vars
    assert "precipitation" in ds.data_vars


_ALL_FIXTURES = (
    "chirps_njoro_1991.nc",
    "chirps_njoro_1991_1995.nc",
    "chirps_njoro_1991_2020.nc",
    "chirps_kisumu_1991.nc",
    "chirps_mombasa_1991.nc",
    "agera5_njoro_1991_long_rains.nc",
    "agera5_njoro_1991_full_year.nc",
    "tamsat_njoro_1991.nc",
    "tamsat_njoro_1991_1995.nc",
    "nex_gddp_njoro_ssp126_2030.nc",
    "nex_gddp_njoro_ssp245_2030.nc",
    "nex_gddp_njoro_ssp585_2030.nc",
)


@pytest.mark.parametrize("filename", _ALL_FIXTURES)
def test_every_fixture_under_2mb(filename: str) -> None:
    path = _FIXTURE_DIR / filename
    assert path.exists(), f"missing {path}"
    assert path.stat().st_size < 2_000_000, (
        f"{filename} is larger than the 2 MB sanity cap; "
        f"either shrink the bbox/period or add a deliberate exception"
    )


def test_combined_fixture_set_under_4mb() -> None:
    total = sum(
        (_FIXTURE_DIR / name).stat().st_size for name in _ALL_FIXTURES
    )
    assert total < 4_000_000, (
        f"committed fixtures total {total / 1024 / 1024:.2f} MB; "
        f"keep the set under 4 MB so the repo zip stays manageable"
    )


def test_chirps_njoro_climatology_baseline_spans_30_years() -> None:
    path = _FIXTURE_DIR / "chirps_njoro_1991_2020.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    years = ds["time"].dt.year.values
    assert int(years.min()) == 1991
    assert int(years.max()) == 2020


def test_chirps_kisumu_fixture_present() -> None:
    path = _FIXTURE_DIR / "chirps_kisumu_1991.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    assert "precip" in ds.data_vars
    assert float(ds["lat"].mean()) > -1.0


def test_chirps_mombasa_fixture_is_coastal_bbox() -> None:
    path = _FIXTURE_DIR / "chirps_mombasa_1991.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    assert -4.5 < float(ds["lat"].mean()) < -3.5
    assert 39.0 < float(ds["lon"].mean()) < 40.0


def test_agera5_full_year_has_365_or_366_days() -> None:
    path = _FIXTURE_DIR / "agera5_njoro_1991_full_year.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    assert ds.sizes["time"] in (365, 366)


def test_tamsat_multiyear_fixture_spans_five_years() -> None:
    path = _FIXTURE_DIR / "tamsat_njoro_1991_1995.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    years = ds["time"].dt.year.values
    assert int(years.min()) == 1991
    assert int(years.max()) == 1995


@pytest.mark.parametrize("scenario", ["ssp126", "ssp245", "ssp585"])
def test_nex_gddp_three_scenarios_present(scenario: str) -> None:
    path = _FIXTURE_DIR / f"nex_gddp_njoro_{scenario}_2030.nc"
    assert path.exists(), f"missing {path}"
    ds = xr.open_dataset(path)
    assert "tas" in ds.data_vars
    assert "pr" in ds.data_vars
