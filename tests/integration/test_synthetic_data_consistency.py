from __future__ import annotations

import pytest

from anga_grid.synthetic import (
    synthetic_agera5,
    synthetic_chirps,
    synthetic_nex_gddp,
    synthetic_tamsat,
)


def test_synthetic_chirps_has_expected_variables() -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-01-31")
    assert "precip" in ds.data_vars
    assert ds["precip"].attrs.get("units") == "mm/day"


def test_synthetic_agera5_has_eight_default_variables() -> None:
    ds = synthetic_agera5(start="1991-01-01", end="1991-01-31")
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
    assert set(ds.data_vars) == expected


def test_synthetic_tamsat_has_rfe() -> None:
    ds = synthetic_tamsat(start="1991-01-01", end="1991-01-31")
    assert "rfe" in ds.data_vars


def test_synthetic_nex_gddp_has_cmip6_var_names() -> None:
    ds = synthetic_nex_gddp(start="2030-01-01", end="2030-01-31")
    for name in ("tas", "tasmin", "tasmax", "pr"):
        assert name in ds.data_vars


def test_synthetic_agera5_temperature_min_lt_max() -> None:
    ds = synthetic_agera5(start="1991-01-01", end="1991-01-31")
    diff = (
        ds["temperature_air_max_daily"] - ds["temperature_air_min_daily"]
    ).values
    assert (diff > 0).all()


def test_synthetic_chirps_seed_determinism() -> None:
    a = synthetic_chirps(start="1991-01-01", end="1991-01-31", seed=42)
    b = synthetic_chirps(start="1991-01-01", end="1991-01-31", seed=42)
    diff = abs(a["precip"].values - b["precip"].values).max()
    assert diff == pytest.approx(0.0)


def test_synthetic_chirps_seasonality_peaks_near_doy_105() -> None:
    ds = synthetic_chirps(start="1991-01-01", end="1991-12-31")
    means_by_month = ds["precip"].resample(time="MS").mean().mean(dim=("lat", "lon"))
    peak_month = int(means_by_month.argmax(dim="time").item()) + 1
    assert 3 <= peak_month <= 5


def test_synthetic_nex_gddp_units_match_cmip6_conventions() -> None:
    ds = synthetic_nex_gddp(start="2030-01-01", end="2030-01-31")
    assert ds["tas"].attrs["units"] == "K"
    assert ds["pr"].attrs["units"] == "kg m-2 s-1"


def test_synthetic_chirps_resolution_arg_matches_step() -> None:
    ds = synthetic_chirps(
        start="1991-01-01", end="1991-01-02",
        lat_min=-1.0, lat_max=0.0, lon_min=35.0, lon_max=36.0,
        resolution=0.1,
    )
    lat_step = float(ds["lat"][1] - ds["lat"][0])
    lon_step = float(ds["lon"][1] - ds["lon"][0])
    assert lat_step == pytest.approx(0.1)
    assert lon_step == pytest.approx(0.1)
