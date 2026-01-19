from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from anga_grid.exceptions import IndicatorError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr

    from anga_grid.season import Season


def annual_trend(
    da: xr.DataArray,
    reducer: str = "sum",
) -> xr.DataArray:
    if "time" not in da.dims:
        raise IndicatorError("input DataArray must have a 'time' dimension")
    yearly = _annual_aggregate(da, reducer)
    return _slope_per_year(yearly, reducer=reducer, source_attrs=da.attrs)


def seasonal_trend(
    da: xr.DataArray,
    season: Season,
    reducer: str = "sum",
) -> xr.DataArray:
    if "time" not in da.dims:
        raise IndicatorError("input DataArray must have a 'time' dimension")
    sliced = season.subset(da)
    yearly = _annual_aggregate(sliced, reducer)
    result = _slope_per_year(yearly, reducer=reducer, source_attrs=da.attrs)
    result.attrs["season"] = season.name
    if season.definition_source:
        result.attrs["season_source"] = season.definition_source
    _record_history(result, "seasonal_trend", season=season.name, reducer=reducer)
    return result


def _annual_aggregate(da: xr.DataArray, reducer: str) -> xr.DataArray:
    grouped = da.groupby(da["time"].dt.year)
    op = reducer.lower()
    if op == "sum":
        out = grouped.sum(skipna=True)
    elif op == "mean":
        out = grouped.mean(skipna=True)
    elif op == "max":
        out = grouped.max(skipna=True)
    elif op == "min":
        out = grouped.min(skipna=True)
    else:
        raise IndicatorError(f"unknown reducer: {reducer}")
    return out.rename({"year": "season_year"})


def _slope_per_year(
    yearly: xr.DataArray,
    reducer: str,
    source_attrs: dict[str, object],
) -> xr.DataArray:
    import xarray as xr

    if yearly.sizes["season_year"] < 2:
        raise IndicatorError(
            "trend requires at least 2 distinct years; got "
            f"{yearly.sizes['season_year']}"
        )

    years = yearly["season_year"].values.astype("float64")
    spatial_dims = [d for d in yearly.dims if d != "season_year"]

    def _ols_slope(values: np.ndarray) -> float:
        valid = ~np.isnan(values)
        if int(valid.sum()) < 2:
            return float("nan")
        x = years[valid]
        y = values[valid]
        x_mean = x.mean()
        y_mean = y.mean()
        denom = float(((x - x_mean) ** 2).sum())
        if denom == 0:
            return float("nan")
        return float(((x - x_mean) * (y - y_mean)).sum() / denom)

    slope = xr.apply_ufunc(
        _ols_slope,
        yearly,
        input_core_dims=[["season_year"]],
        output_core_dims=[[]],
        vectorize=True,
        dask="forbidden",
        output_dtypes=[np.float64],
    )
    if spatial_dims and not slope.dims:
        slope = slope.expand_dims(spatial_dims)

    slope.attrs.update(source_attrs)
    slope.attrs["indicator"] = f"annual_{reducer}_trend"
    slope.attrs["units"] = "value/year"
    slope.attrs["years_min"] = int(years.min())
    slope.attrs["years_max"] = int(years.max())
    slope.attrs["years_n"] = int(yearly.sizes["season_year"])
    slope.attrs["reducer"] = reducer
    _record_history(slope, "annual_trend", reducer=reducer)
    return slope


def _record_history(result: xr.DataArray, operation: str, **params: object) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    manifest.record(operation, **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
