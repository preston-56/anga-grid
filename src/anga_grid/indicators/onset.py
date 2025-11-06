from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import IndicatorError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr

    from anga_grid.season import Season


@dataclass(frozen=True, slots=True)
class OnsetCriteria:
    wet_window_days: int = 3
    wet_threshold_mm: float = 20.0
    followup_days: int = 30
    dry_spell_days: int = 10
    dry_threshold_mm: float = 1.0


DEFAULT_CRITERIA = OnsetCriteria()


def detect_onset(
    pr: xr.DataArray,
    season: Season | None = None,
    criteria: OnsetCriteria = DEFAULT_CRITERIA,
) -> xr.DataArray:
    import xarray as xr

    if "time" not in pr.dims:
        raise IndicatorError("input must have a 'time' dimension")

    work = pr if season is None else season.subset(pr)
    if work.sizes.get("time", 0) == 0:
        raise IndicatorError("no time samples within the requested window")

    doys = work["time"].dt.dayofyear.astype("int32").values

    onset = xr.apply_ufunc(
        _onset_1d,
        work,
        kwargs={
            "doys": doys,
            "wet_win": criteria.wet_window_days,
            "wet_thresh": criteria.wet_threshold_mm,
            "follow": criteria.followup_days,
            "dry_days": criteria.dry_spell_days,
            "dry_thresh": criteria.dry_threshold_mm,
        },
        input_core_dims=[["time"]],
        output_core_dims=[[]],
        vectorize=True,
        dask="forbidden",
        output_dtypes=[np.float64],
    )

    onset.attrs.update(pr.attrs)
    onset.attrs["indicator"] = "onset"
    onset.attrs["wet_window_days"] = criteria.wet_window_days
    onset.attrs["wet_threshold_mm"] = criteria.wet_threshold_mm
    onset.attrs["followup_days"] = criteria.followup_days
    onset.attrs["dry_spell_days"] = criteria.dry_spell_days
    onset.attrs["dry_threshold_mm"] = criteria.dry_threshold_mm
    onset.attrs["units"] = "day_of_year"
    if season is not None:
        onset.attrs["season"] = season.name
        if season.definition_source:
            onset.attrs["season_source"] = season.definition_source
    _record_history(onset, season, criteria)
    return onset


def _record_history(
    result: xr.DataArray,
    season: Season | None,
    criteria: OnsetCriteria,
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    params = {
        "wet_window_days": criteria.wet_window_days,
        "wet_threshold_mm": criteria.wet_threshold_mm,
        "followup_days": criteria.followup_days,
        "dry_spell_days": criteria.dry_spell_days,
    }
    if season is not None:
        params["season"] = season.name
    manifest.record("detect_onset", **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value


def _onset_1d(
    rain: np.ndarray,
    doys: np.ndarray,
    wet_win: int,
    wet_thresh: float,
    follow: int,
    dry_days: int,
    dry_thresh: float,
) -> float:
    n = len(rain)
    last_start = n - wet_win - follow
    if last_start < 0:
        return float("nan")

    for i in range(last_start + 1):
        wet_sum = float(rain[i : i + wet_win].sum())
        if wet_sum < wet_thresh:
            continue
        following = rain[i + wet_win : i + wet_win + follow]
        max_dry = 0
        current = 0
        for value in following:
            if float(value) < dry_thresh:
                current += 1
                if current > max_dry:
                    max_dry = current
            else:
                current = 0
            if max_dry >= dry_days:
                break
        if max_dry < dry_days:
            return float(doys[i])

    return float("nan")
