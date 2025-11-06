from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.exceptions import IndicatorError
from anga_grid.provenance import Manifest

if TYPE_CHECKING:
    import xarray as xr

    from anga_grid.season import Season


def compute_spi(
    pr: xr.DataArray,
    window_months: int,
    season: Season | None = None,
    baseline: tuple[int, int] | None = None,
    dist: str = "gamma",
) -> xr.DataArray:
    if window_months < 1:
        raise IndicatorError(f"window_months must be >= 1, got {window_months}")
    if "time" not in pr.dims:
        raise IndicatorError("input DataArray must have a 'time' dimension")

    units = pr.attrs.get("units", "mm/day")
    pr_with_units = pr.copy()
    pr_with_units.attrs["units"] = units

    if baseline is None and pr.sizes["time"] > 0:
        years = pr["time"].dt.year
        baseline = (int(years.min().item()), int(years.max().item()))

    result = _spi_via_xclim(pr_with_units, window_months, dist, baseline)
    if result is None:
        result = _spi_fallback(pr_with_units, window_months, baseline)

    if season is not None:
        result = season.subset(result)

    result.attrs.update(pr.attrs)
    result.attrs["indicator"] = "spi"
    result.attrs["window_months"] = window_months
    result.attrs["distribution"] = dist
    if baseline is not None:
        result.attrs["baseline"] = f"{baseline[0]}-{baseline[1]}"
    if season is not None:
        result.attrs["season"] = season.name
        if season.definition_source:
            result.attrs["season_source"] = season.definition_source

    _record_history(result, season, window_months, baseline, dist)
    return result


def _record_history(
    result: xr.DataArray,
    season: Season | None,
    window_months: int,
    baseline: tuple[int, int] | None,
    dist: str,
) -> None:
    if "source" not in result.attrs:
        return
    manifest = Manifest.from_attrs(dict(result.attrs))
    params = {"window_months": window_months, "distribution": dist}
    if baseline is not None:
        params["baseline"] = f"{baseline[0]}-{baseline[1]}"
    if season is not None:
        params["season"] = season.name
    manifest.record("compute_spi", **params)
    for key, value in manifest.as_attrs().items():
        result.attrs[key] = value


def _spi_via_xclim(
    pr: xr.DataArray,
    window_months: int,
    dist: str,
    baseline: tuple[int, int] | None,
) -> xr.DataArray | None:
    try:
        from xclim.indices import standardized_precipitation_index
    except ImportError:
        return None

    cal_start = f"{baseline[0]}-01-01" if baseline is not None else None
    cal_end = f"{baseline[1]}-12-31" if baseline is not None else None

    try:
        result = standardized_precipitation_index(
            pr=pr,
            freq="MS",
            window=window_months,
            dist=dist,
            method="APP",
            cal_start=cal_start,
            cal_end=cal_end,
        )
    except (TypeError, ValueError):
        return None
    return result


def _spi_fallback(
    pr: xr.DataArray,
    window_months: int,
    baseline: tuple[int, int] | None,
) -> xr.DataArray:
    monthly = pr.resample(time="MS").sum(skipna=True)
    rolling = monthly.rolling(
        time=window_months, min_periods=window_months
    ).sum()
    return _standardize(rolling, baseline)


def _standardize(
    da: xr.DataArray, baseline: tuple[int, int] | None
) -> xr.DataArray:
    if baseline is None:
        ref = da
    else:
        years = da["time"].dt.year
        ref = da.where((years >= baseline[0]) & (years <= baseline[1]))

    mu = ref.mean(dim="time", skipna=True)
    sd = ref.std(dim="time", skipna=True)
    sd = sd.where(sd > 0)
    return (da - mu) / sd
