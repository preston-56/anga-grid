"""Compute long-rains trend over a decade and classify each year into terciles."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import xarray as xr

from anga_grid.indicators.trend import seasonal_trend
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.season import SEASONS
from anga_grid.severity import tercile_classification
from anga_grid.types import TimeRange, resolve_region


def main() -> None:
    bbox = resolve_region("nakuru")
    time_range = TimeRange(start=date(1991, 1, 1), end=date(2000, 12, 31))

    from anga_grid.synthetic.chirps import synthetic_chirps_multiyear

    with TemporaryDirectory() as raw:
        synthetic_path = Path(raw) / "synthetic-chirps.nc"
        synthetic_chirps_multiyear(years=(1991, 2000)).to_netcdf(synthetic_path)

        ds = CHIRPSProvider(
            cache_dir=Path(raw) / "cache",
            source_override=synthetic_path,
        ).fetch(bbox, time_range)

    long_rains = SEASONS["long-rains"]
    spatial_mean = ds["precip"].mean(dim=("lat", "lon"))

    seasonal = seasonal_trend(spatial_mean, season=long_rains, reducer="sum")

    print("=== long-rains trend (mm / year, spatial mean over Nakuru) ===")
    print(f"  slope: {float(seasonal.values):+.2f} mm/year")
    print(f"  attrs: indicator={seasonal.attrs.get('indicator')}, "
          f"season={seasonal.attrs.get('season')}")

    annual_subset = long_rains.subset(spatial_mean)
    yearly = annual_subset.groupby(annual_subset["time"].dt.year).sum(skipna=True)
    annual_da = xr.DataArray(
        yearly.values.astype("float32"),
        coords={"time": pd.to_datetime(
            [f"{int(y)}-01-01" for y in yearly["year"].values]
        )},
        dims=["time"],
    )
    classified = tercile_classification(annual_da, baseline=(1991, 2000))

    print()
    print("=== year-by-year tercile classification (long-rains total) ===")
    for year, label in zip(
        classified["time"].dt.year.values,
        classified.values,
        strict=True,
    ):
        print(f"  {int(year)}: {label}")


if __name__ == "__main__":
    main()
