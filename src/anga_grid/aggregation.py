from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from anga_grid.exceptions import AngaGridError

if TYPE_CHECKING:
    import xarray as xr

    from anga_grid.season import Season

Reducer = str | Callable[["xr.DataArray"], "xr.DataArray"]


def aggregate_seasonal(
    da: xr.DataArray,
    season: Season,
    reducer: Reducer = "sum",
) -> xr.DataArray:
    if "time" not in da.dims:
        raise AngaGridError("input DataArray must have a 'time' dimension")

    sliced = season.subset(da)
    grouped: Any = sliced.groupby(sliced["time"].dt.year)
    return _apply_reducer(grouped, reducer)


def _apply_reducer(grouped: Any, reducer: Reducer) -> xr.DataArray:
    if callable(reducer):
        result = grouped.map(reducer)
    elif isinstance(reducer, str):
        op = reducer.lower()
        if op == "sum":
            result = grouped.sum(skipna=True)
        elif op == "mean":
            result = grouped.mean(skipna=True)
        elif op == "max":
            result = grouped.max(skipna=True)
        elif op == "min":
            result = grouped.min(skipna=True)
        elif op == "count":
            result = grouped.count()
        else:
            raise AngaGridError(f"unknown reducer: {reducer}")
    else:
        raise AngaGridError(f"reducer must be str or callable, got {type(reducer)}")
    return result.rename({"year": "season_year"})
