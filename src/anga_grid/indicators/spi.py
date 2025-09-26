from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.exceptions import IndicatorError

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
        raise IndicatorError(f"window_months must be ≥ 1, got {window_months}")
    if "time" not in pr.dims:
        raise IndicatorError("input DataArray must have a 'time' dimension")

    if baseline is None and pr.sizes["time"] > 0:
        years = pr["time"].dt.year
        baseline = (int(years.min().item()), int(years.max().item()))

    monthly = pr.resample(time="MS").sum(skipna=True)
    rolling = monthly.rolling(time=window_months, min_periods=window_months).sum()

    if season is not None:
        rolling = season.subset(rolling)

    standardized = _standardize(rolling, baseline=baseline)

    standardized.attrs["indicator"] = "spi"
    standardized.attrs["window_months"] = window_months
    standardized.attrs["distribution"] = dist
    if baseline is not None:
        standardized.attrs["baseline"] = f"{baseline[0]}-{baseline[1]}"
    if season is not None:
        standardized.attrs["season"] = season.name
        if season.definition_source:
            standardized.attrs["season_source"] = season.definition_source
    return standardized


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
