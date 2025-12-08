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
class GDDOptions:
    t_base_c: float = 10.0
    t_cap_c: float | None = 30.0
    method: str = "averaging"


MAIZE_DEFAULTS = GDDOptions(t_base_c=10.0, t_cap_c=30.0, method="averaging")
SORGHUM_DEFAULTS = GDDOptions(t_base_c=8.0, t_cap_c=35.0, method="averaging")
WHEAT_DEFAULTS = GDDOptions(t_base_c=0.0, t_cap_c=26.0, method="averaging")


def growing_degree_days(
    t_min: xr.DataArray,
    t_max: xr.DataArray,
    season: Season | None = None,
    options: GDDOptions = MAIZE_DEFAULTS,
) -> xr.DataArray:
    if "time" not in t_min.dims or "time" not in t_max.dims:
        raise IndicatorError("inputs must share a 'time' dimension")
    if t_min.sizes["time"] != t_max.sizes["time"]:
        raise IndicatorError(
            f"t_min and t_max have mismatched time sizes: "
            f"{t_min.sizes['time']} vs {t_max.sizes['time']}"
        )
    if options.method not in ("averaging", "modified"):
        raise IndicatorError(f"unknown GDD method: {options.method}")

    work_min = t_min if season is None else season.subset(t_min)
    work_max = t_max if season is None else season.subset(t_max)

    if options.method == "modified":
        capped_max = (
            work_max.where(work_max <= options.t_cap_c, options.t_cap_c)
            if options.t_cap_c is not None
            else work_max
        )
        capped_min = work_min.where(work_min >= options.t_base_c, options.t_base_c)
        daily = (capped_max + capped_min) / 2.0 - options.t_base_c
    else:
        avg = (work_max + work_min) / 2.0
        if options.t_cap_c is not None:
            avg = avg.where(avg <= options.t_cap_c, options.t_cap_c)
        daily = avg - options.t_base_c

    daily = daily.where(daily > 0, 0.0)

    grouped = daily.groupby(daily["time"].dt.year)
    yearly = grouped.sum(skipna=True)
    yearly = yearly.rename({"year": "season_year"})
    yearly = yearly.astype("float32")
    yearly.values = np.asarray(yearly.values)

    yearly.attrs.update(t_min.attrs)
    yearly.attrs["indicator"] = "gdd"
    yearly.attrs["t_base_c"] = options.t_base_c
    yearly.attrs["method"] = options.method
    if options.t_cap_c is not None:
        yearly.attrs["t_cap_c"] = options.t_cap_c
    yearly.attrs["units"] = "degC-days"
    if season is not None:
        yearly.attrs["season"] = season.name
        if season.definition_source:
            yearly.attrs["season_source"] = season.definition_source

    _record_history(yearly, season, options)
    return yearly


def _record_history(
    result: xr.DataArray, season: Season | None, options: GDDOptions
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    params: dict[str, object] = {
        "t_base_c": options.t_base_c,
        "method": options.method,
    }
    if options.t_cap_c is not None:
        params["t_cap_c"] = options.t_cap_c
    if season is not None:
        params["season"] = season.name
    manifest.record("gdd", **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value
