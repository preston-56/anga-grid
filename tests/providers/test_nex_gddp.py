from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pytest

from anga_grid.exceptions import ProviderError
from anga_grid.provenance import read
from anga_grid.providers.nex_gddp import (
    SSP245,
    SSP585,
    NEXGDDPProvider,
)
from anga_grid.providers.nex_gddp.scenarios import HISTORICAL, SCENARIOS, get_scenario
from anga_grid.types import BoundingBox, TimeRange
from tests.fixtures.nex_gddp import synthetic_nex_gddp

_BBOX = BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4)


@pytest.fixture
def synthetic_nc(tmp_path: Path) -> Path:
    ds = synthetic_nex_gddp(start="2030-01-01", end="2030-06-30")
    p = tmp_path / "nex.nc"
    ds.to_netcdf(p)
    return p


def test_fetch_without_override_raises(tmp_path: Path) -> None:
    provider = NEXGDDPProvider(cache_dir=tmp_path)
    with pytest.raises(ProviderError, match="not wired in v0.4"):
        provider.fetch(_BBOX, TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31)))


def test_fetch_returns_canonical_variable_names(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(_BBOX, tr)
    for name in ("tas_mean", "tas_min", "tas_max", "precipitation"):
        assert name in ds.data_vars


def test_fetch_converts_temperature_kelvin_to_celsius(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(_BBOX, tr)
    assert ds["tas_mean"].attrs["units"] == "degC"
    mean_temp = float(ds["tas_mean"].mean())
    assert -10 < mean_temp < 50


def test_fetch_converts_precipitation_to_mm_per_day(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(_BBOX, tr)
    assert ds["precipitation"].attrs["units"] == "mm/day"
    assert float(ds["precipitation"].max()) < 200


def test_fetch_skips_unit_conversion_when_already_correct(tmp_path: Path) -> None:
    ds = synthetic_nex_gddp(
        start="2030-01-01", end="2030-01-31",
        units_kelvin=False, units_pr_per_second=False,
    )
    p = tmp_path / "already-canon.nc"
    ds.to_netcdf(p)
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=p)
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    out = provider.fetch(_BBOX, tr)
    assert out["tas_mean"].attrs["units"] == "degC"
    assert out["precipitation"].attrs["units"] == "mm/day"


def test_fetch_records_scenario_and_model_in_history(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(
        cache_dir=tmp_path, source_override=synthetic_nc,
        scenario=SSP585, model="MPI-ESM1-2-HR",
    )
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(_BBOX, tr)
    history = ds.attrs.get("history", "")
    assert "scenario=ssp585" in history
    assert "model=MPI-ESM1-2-HR" in history


def test_fetch_carries_scenario_caveat_for_high_forcing(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(
        cache_dir=tmp_path, source_override=synthetic_nc, scenario=SSP585
    )
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(_BBOX, tr)
    manifest = read(ds)
    high_forcing = [c for c in manifest.caveats if "8.5" in c]
    assert high_forcing


def test_fetch_historical_scenario_omits_radiative_forcing_caveat(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(
        cache_dir=tmp_path, source_override=synthetic_nc, scenario=HISTORICAL
    )
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(_BBOX, tr)
    manifest = read(ds)
    assert all("W/m" not in c for c in manifest.caveats)


def test_fetch_subset_respects_bbox(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    bbox = BoundingBox(min_lat=-0.5, max_lat=-0.3, min_lon=35.8, max_lon=36.1)
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    ds = provider.fetch(bbox, tr)
    assert float(ds["lat"].min()) >= bbox.min_lat - 0.3
    assert float(ds["lat"].max()) <= bbox.max_lat + 0.3


def test_fetch_raises_on_missing_required_variable(tmp_path: Path) -> None:
    ds = synthetic_nex_gddp(start="2030-01-01", end="2030-01-31").drop_vars(
        ["tasmin", "tasmax"]
    )
    p = tmp_path / "missing-vars.nc"
    ds.to_netcdf(p)
    provider = NEXGDDPProvider(
        cache_dir=tmp_path, source_override=p,
        variables=("tas_mean", "tas_min", "tas_max", "precipitation"),
    )
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    with pytest.raises(ProviderError, match="missing requested variables"):
        provider.fetch(_BBOX, tr)


def test_fetch_raises_on_empty_time_subset(
    tmp_path: Path, synthetic_nc: Path
) -> None:
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=synthetic_nc)
    tr = TimeRange(start=date(2099, 1, 1), end=date(2099, 12, 31))
    with pytest.raises(ProviderError, match="empty along time"):
        provider.fetch(_BBOX, tr)


def test_fetch_raises_on_missing_source(tmp_path: Path) -> None:
    provider = NEXGDDPProvider(
        cache_dir=tmp_path, source_override=tmp_path / "no-such-file.nc"
    )
    tr = TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31))
    with pytest.raises(ProviderError, match="not found"):
        provider.fetch(_BBOX, tr)


def test_provider_implements_protocol() -> None:
    from anga_grid.providers.base import Provider

    p = NEXGDDPProvider(cache_dir=Path("/tmp"))
    assert isinstance(p, Provider)


def test_scenarios_catalog_complete() -> None:
    expected = {"historical", "ssp126", "ssp245", "ssp370", "ssp585"}
    assert set(SCENARIOS.keys()) == expected


def test_get_scenario_case_insensitive() -> None:
    assert get_scenario("SSP585").name == "ssp585"
    with pytest.raises(ValueError, match="unknown scenario"):
        get_scenario("rcp1.5")


def test_scenario_radiative_forcing_monotonic() -> None:
    forcings = [SSP245.radiative_forcing_wm2, SSP585.radiative_forcing_wm2]
    assert forcings == sorted(forcings)
    assert np.isclose(SSP585.radiative_forcing_wm2, 8.5)
