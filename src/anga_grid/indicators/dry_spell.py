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
class DrySpellCriteria:
    threshold_mm: float = 1.0
    min_length_days: int = 5


DEFAULT_CRITERIA = DrySpellCriteria()


def dry_spell_count(
    pr: xr.DataArray,
    season: Season | None = None,
    criteria: DrySpellCriteria = DEFAULT_CRITERIA,
) -> xr.DataArray:
    import xarray as xr

    if "time" not in pr.dims:
        raise IndicatorError("input must have a 'time' dimension")
    if criteria.min_length_days < 1:
        raise IndicatorError("min_length_days must be >= 1")

    work = pr if season is None else season.subset(pr)
    if work.sizes.get("time", 0) == 0:
        raise IndicatorError("no time samples within the requested window")

    grouped = work.groupby(work["time"].dt.year)
    yearly: list[xr.DataArray] = []
    years: list[int] = []
    for year, slab in grouped:
        count = xr.apply_ufunc(
            _count_dry_spells,
            slab,
            kwargs={
                "threshold": criteria.threshold_mm,
                "min_length": criteria.min_length_days,
            },
            input_core_dims=[["time"]],
            output_core_dims=[[]],
            vectorize=True,
            dask="forbidden",
            output_dtypes=[np.int32],
        )
        yearly.append(count)
        years.append(int(year))

    if not yearly:
        raise IndicatorError("no complete years to count")

    result = xr.concat(yearly, dim="season_year")
    result = result.assign_coords(season_year=years)

    result.attrs.update(pr.attrs)
    result.attrs["indicator"] = "dry_spell_count"
    result.attrs["threshold_mm"] = criteria.threshold_mm
    result.attrs["min_length_days"] = criteria.min_length_days
    if season is not None:
        result.attrs["season"] = season.name
        if season.definition_source:
            result.attrs["season_source"] = season.definition_source

    _record_history(result, season, criteria)
    return result


def _count_dry_spells(
    rain: np.ndarray, threshold: float, min_length: int
) -> int:
    is_dry = rain < threshold
    count = 0
    current = 0
    for value in is_dry:
        if value:
            current += 1
        else:
            if current >= min_length:
                count += 1
            current = 0
    if current >= min_length:
        count += 1
    return count


def _record_history(
    result: xr.DataArray, season: Season | None, criteria: DrySpellCriteria
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    params: dict[str, object] = {
        "threshold_mm": criteria.threshold_mm,
        "min_length_days": criteria.min_length_days,
    }
    if season is not None:
        params["season"] = season.name
    manifest.record("dry_spell_count", **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
