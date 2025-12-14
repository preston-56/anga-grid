from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from anga_grid.providers.agera5 import AgERA5Provider
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.providers.tamsat import TAMSATProvider
from anga_grid.types import BoundingBox, TimeRange
from tests.fixtures.agera5 import synthetic_agera5
from tests.fixtures.synthetic import synthetic_chirps
from tests.fixtures.tamsat import synthetic_tamsat

_BBOX = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)
_TR = TimeRange(start=date(1991, 1, 1), end=date(1991, 1, 31))


@pytest.mark.regression
def test_chirps_canonicalize_idempotent(tmp_path: Path) -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-01-31")
    p = tmp_path / "chirps.nc"
    ds.to_netcdf(p)
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=p)
    out_a = provider.fetch(_BBOX, _TR)
    out_a.to_netcdf(tmp_path / "round.nc")
    out_b = provider.fetch(_BBOX, _TR)
    assert list(out_a.data_vars) == list(out_b.data_vars)
    assert set(out_a.coords) == set(out_b.coords)


@pytest.mark.regression
def test_chirps_latitude_axis_preserved_after_canon(tmp_path: Path) -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-01-31").rename(
        {"lat": "latitude", "lon": "longitude"}
    )
    p = tmp_path / "alt.nc"
    ds.to_netcdf(p)
    provider = CHIRPSProvider(cache_dir=tmp_path, source_override=p)
    out = provider.fetch(_BBOX, _TR)
    assert "lat" in out.coords
    assert "lon" in out.coords
    assert "latitude" not in out.coords
    assert "longitude" not in out.coords


@pytest.mark.regression
def test_agera5_capitalized_names_normalized(tmp_path: Path) -> None:
    ds = synthetic_agera5(start="1991-01-01", end="1991-01-31").rename(
        {
            "temperature_air_mean_daily": "Temperature_Air_Mean_Daily",
            "precipitation_flux": "Precipitation_Flux",
        }
    )
    p = tmp_path / "agera5-caps.nc"
    ds.to_netcdf(p)
    provider = AgERA5Provider(cache_dir=tmp_path, source_override=p)
    out = provider.fetch(_BBOX, _TR)
    assert "temperature_air_mean_daily" in out.data_vars
    assert "precipitation_flux" in out.data_vars
    assert "Temperature_Air_Mean_Daily" not in out.data_vars


@pytest.mark.regression
def test_tamsat_rfe_filled_routes_to_precip(tmp_path: Path) -> None:
    ds = synthetic_tamsat(start="1991-01-01", end="1991-01-31").rename(
        {"rfe": "rfe_filled"}
    )
    p = tmp_path / "tamsat-filled.nc"
    ds.to_netcdf(p)
    provider = TAMSATProvider(cache_dir=tmp_path, source_override=p)
    out = provider.fetch(_BBOX, _TR)
    assert "precip" in out.data_vars
    assert "rfe_filled" not in out.data_vars
