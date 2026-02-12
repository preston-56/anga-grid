from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.exceptions import IndicatorError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr

    from anga_grid.season import Season


def hot_days(
    t_max: xr.DataArray,
    threshold_c: float = 32.0,
    season: Season | None = None,
) -> xr.DataArray:
    return _count_above(t_max, threshold_c, season, indicator="hot_days")


def cold_days(
    t_min: xr.DataArray,
    threshold_c: float = 10.0,
    season: Season | None = None,
) -> xr.DataArray:
    return _count_below(t_min, threshold_c, season, indicator="cold_days")


def frost_days(
    t_min: xr.DataArray,
    threshold_c: float = 0.0,
    season: Season | None = None,
) -> xr.DataArray:
    return _count_below(t_min, threshold_c, season, indicator="frost_days")


def tropical_nights(
    t_min: xr.DataArray,
    threshold_c: float = 20.0,
    season: Season | None = None,
) -> xr.DataArray:
    return _count_above(t_min, threshold_c, season, indicator="tropical_nights")


def _count_above(
    da: xr.DataArray,
    threshold_c: float,
    season: Season | None,
    indicator: str,
) -> xr.DataArray:
    return _annual_count(da, indicator, threshold_c, season, predicate="above")


def _count_below(
    da: xr.DataArray,
    threshold_c: float,
    season: Season | None,
    indicator: str,
) -> xr.DataArray:
    return _annual_count(da, indicator, threshold_c, season, predicate="below")


def _annual_count(
    da: xr.DataArray,
    indicator: str,
    threshold_c: float,
    season: Season | None,
    predicate: str,
) -> xr.DataArray:
    if "time" not in da.dims:
        raise IndicatorError(f"{indicator} input must have a 'time' dimension")

    work = da if season is None else season.subset(da)
    if predicate == "above":
        mask = work > threshold_c
    elif predicate == "below":
        mask = work < threshold_c
    else:
        raise IndicatorError(f"unknown predicate {predicate}")

    counts = mask.astype("int32").groupby(work["time"].dt.year).sum().rename(
        {"year": "season_year"}
    )
    counts.attrs.update(da.attrs)
    counts.attrs["indicator"] = indicator
    counts.attrs["threshold_c"] = threshold_c
    counts.attrs["units"] = "days"
    if season is not None:
        counts.attrs["season"] = season.name
        if season.definition_source:
            counts.attrs["season_source"] = season.definition_source
    _record_history(counts, indicator, threshold_c=threshold_c)
    return counts


def _record_history(result: xr.DataArray, operation: str, **params: object) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record(operation, **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
