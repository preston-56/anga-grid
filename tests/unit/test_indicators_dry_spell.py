from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import IndicatorError
from anga_grid.indicators.dry_spell import DrySpellCriteria, dry_spell_count
from anga_grid.indicators.dry_spell.count import _count_dry_spells
from anga_grid.season import SEASONS


def _series(daily: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(daily), freq="D")
    return xr.DataArray(
        np.asarray(daily, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_count_dry_spells_single_qualifying_run() -> None:
    arr = np.array([0, 0, 0, 0, 0, 0, 5, 0, 0])
    assert _count_dry_spells(arr, threshold=1.0, min_length=5) == 1


def test_count_dry_spells_two_runs() -> None:
    arr = np.array([0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0])
    assert _count_dry_spells(arr, threshold=1.0, min_length=5) == 2


def test_count_dry_spells_ignores_short_runs() -> None:
    arr = np.array([0, 0, 1, 0, 0, 0, 1, 0, 0])
    assert _count_dry_spells(arr, threshold=1.0, min_length=5) == 0


def test_count_dry_spells_handles_trailing_run() -> None:
    arr = np.array([5, 5, 0, 0, 0, 0, 0, 0])
    assert _count_dry_spells(arr, threshold=1.0, min_length=5) == 1


def test_dry_spell_count_rejects_missing_time() -> None:
    da = xr.DataArray([1, 2, 3], dims=["x"])
    with pytest.raises(IndicatorError):
        dry_spell_count(da)


def test_dry_spell_count_rejects_zero_min_length() -> None:
    with pytest.raises(IndicatorError):
        dry_spell_count(_series([0] * 30), criteria=DrySpellCriteria(min_length_days=0))


def test_dry_spell_count_groups_by_year() -> None:
    times_91 = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    times_92 = pd.date_range("1992-01-01", "1992-12-31", freq="D")
    data_91 = np.zeros(len(times_91), dtype="float32")
    data_91[20:60] = 5.0
    data_92 = np.ones(len(times_92), dtype="float32") * 5.0
    da = xr.DataArray(
        np.concatenate([data_91, data_92]),
        coords={"time": times_91.append(times_92)},
        dims=["time"],
    )
    result = dry_spell_count(da, criteria=DrySpellCriteria(min_length_days=10))
    assert "season_year" in result.dims
    assert int(result.sel(season_year=1991).item()) >= 1
    assert int(result.sel(season_year=1992).item()) == 0


def test_dry_spell_count_with_season_subset() -> None:
    times = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    data = np.ones(len(times), dtype="float32") * 5.0
    long_rains = SEASONS["long-rains"]
    in_window = (times.dayofyear >= long_rains.start_doy) & (
        times.dayofyear <= long_rains.end_doy
    )
    data = np.where(in_window, 0.0, data).astype("float32")
    da = xr.DataArray(data, coords={"time": times}, dims=["time"])
    result = dry_spell_count(da, season=long_rains, criteria=DrySpellCriteria(min_length_days=10))
    assert int(result.values[0]) >= 1


def test_dry_spell_count_attaches_provenance_attrs() -> None:
    da = _series([0.0] * 30)
    result = dry_spell_count(da, criteria=DrySpellCriteria(min_length_days=5))
    assert result.attrs["indicator"] == "dry_spell_count"
    assert result.attrs["threshold_mm"] == 1.0
    assert result.attrs["min_length_days"] == 5


def test_dry_spell_count_extends_manifest_history() -> None:
    series = _series([0.0] * 60 + [5.0] * 5)
    series.attrs["source"] = "synthetic"
    series.attrs["code_version"] = "0.1.0"
    result = dry_spell_count(series, criteria=DrySpellCriteria(min_length_days=10))
    assert "history" in result.attrs
    operations = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "dry_spell_count" in operations


def test_dry_spell_count_2d_grid() -> None:
    n_time = 90
    rain = np.zeros((n_time, 2, 2), dtype="float32")
    rain[:30, 0, 0] = 0
    rain[30:35, 0, 0] = 5
    rain[35:65, 0, 0] = 0
    rain[:, 1, 1] = 10.0
    times = pd.date_range("1991-01-01", periods=n_time, freq="D")
    da = xr.DataArray(
        rain,
        coords={
            "time": times,
            "lat": [-0.5, 0.0],
            "lon": [35.0, 35.5],
        },
        dims=["time", "lat", "lon"],
    )
    result = dry_spell_count(da, criteria=DrySpellCriteria(min_length_days=10))
    assert int(result.sel(season_year=1991, lat=-0.5, lon=35.0).item()) >= 2
    assert int(result.sel(season_year=1991, lat=0.0, lon=35.5).item()) == 0
