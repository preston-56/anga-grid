from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from anga_grid.exceptions import IndicatorError

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
    if "time" not in pr.dims:
        raise IndicatorError("input must have a 'time' dimension")

    work = pr
    if season is not None:
        work = season.subset(work)

    wet = work.rolling(
        time=criteria.wet_window_days, min_periods=criteria.wet_window_days
    ).sum() >= criteria.wet_threshold_mm

    is_dry = work < criteria.dry_threshold_mm
    longest_dry_run = _max_consecutive_true(
        is_dry, window=criteria.followup_days
    )
    no_dry_spell = longest_dry_run < criteria.dry_spell_days

    candidate = wet & no_dry_spell.shift(time=-(criteria.wet_window_days - 1))
    onset = _first_true_doy(candidate)

    onset.attrs["indicator"] = "onset"
    onset.attrs["wet_window_days"] = criteria.wet_window_days
    onset.attrs["wet_threshold_mm"] = criteria.wet_threshold_mm
    onset.attrs["followup_days"] = criteria.followup_days
    onset.attrs["dry_spell_days"] = criteria.dry_spell_days
    onset.attrs["dry_threshold_mm"] = criteria.dry_threshold_mm
    if season is not None:
        onset.attrs["season"] = season.name
    return onset


def _max_consecutive_true(
    da: xr.DataArray, *, window: int
) -> xr.DataArray:
    import numpy as np
    import xarray as xr

    arr = da.astype("int8")
    runs = arr.rolling(time=window, min_periods=1).construct("offset")
    cumulative = runs.cumsum(dim="offset")
    transition = runs.where(runs == 1, 0).diff("offset", label="upper") == -1
    longest = cumulative.where(transition).max(dim="offset", skipna=True)
    fallback = arr.rolling(time=window, min_periods=1).sum()
    out = xr.where(np.isnan(longest), fallback, longest)
    return out.transpose(*da.dims)


def _first_true_doy(da: xr.DataArray) -> xr.DataArray:
    import numpy as np
    import xarray as xr

    doy = da["time"].dt.dayofyear
    candidate = xr.where(da, doy, np.iinfo("int32").max)
    first = candidate.min(dim="time")
    return first.where(first != np.iinfo("int32").max)
