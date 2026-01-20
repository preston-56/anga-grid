from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anga_grid.aggregation.reducers import Reducer, apply_reducer
from anga_grid.exceptions import AngaGridError

if TYPE_CHECKING:
    import xarray as xr

    from anga_grid.season import Season


def aggregate_seasonal(
    da: xr.DataArray,
    season: Season,
    reducer: Reducer = "sum",
) -> xr.DataArray:
    if "time" not in da.dims:
        raise AngaGridError("input DataArray must have a 'time' dimension")

    sliced = season.subset(da)
    grouped: Any = sliced.groupby(sliced["time"].dt.year)
    return apply_reducer(grouped, reducer)
