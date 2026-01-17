"""Compute WRSI for the long-rains maize crop in Nakuru."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from anga_grid.cropping import NAKURU_MAIZE
from anga_grid.indicators.evapotranspiration import reference_et
from anga_grid.indicators.wrsi import (
    MAIZE,
    water_requirement_satisfaction_index,
)
from anga_grid.providers.agera5 import AgERA5Provider
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.types import TimeRange, resolve_region


def main() -> None:
    bbox = resolve_region("nakuru")
    time_range = TimeRange(start=date(1991, 3, 1), end=date(1991, 8, 31))

    from anga_grid.synthetic.agera5 import synthetic_agera5
    from anga_grid.synthetic.chirps import synthetic_chirps

    with TemporaryDirectory() as raw:
        chirps_path = Path(raw) / "chirps.nc"
        agera5_path = Path(raw) / "agera5.nc"
        common_kwargs = {
            "start": "1991-03-01",
            "end": "1991-08-31",
            "lat_min": -1.2,
            "lat_max": 0.0,
            "lon_min": 35.6,
            "lon_max": 36.5,
            "resolution": 0.1,
        }
        synthetic_chirps(**common_kwargs).to_netcdf(chirps_path)
        synthetic_agera5(**common_kwargs).to_netcdf(agera5_path)

        rain = CHIRPSProvider(
            cache_dir=Path(raw) / "cache-chirps",
            source_override=chirps_path,
        ).fetch(bbox, time_range)["precip"]

        agera5 = AgERA5Provider(
            cache_dir=Path(raw) / "cache-agera5",
            source_override=agera5_path,
        ).fetch(bbox, time_range)
        et0 = reference_et(
            agera5["temperature_air_min_daily"],
            agera5["temperature_air_max_daily"],
            agera5["solar_radiation_flux"] / 1e6,
            agera5["wind_speed_10m_mean_daily"],
            agera5["relative_humidity_2m_12h"],
            elevation_m=2150.0,
        )

    wrsi = water_requirement_satisfaction_index(
        rain, et0, crop=MAIZE, planting_doy=NAKURU_MAIZE.planting_doy
    )

    finite = wrsi.values[wrsi.values == wrsi.values]
    if finite.size:
        print(f"WRSI(maize, long rains 1991): mean {finite.mean():.1f}%, "
              f"min {finite.min():.1f}%, max {finite.max():.1f}%")
    else:
        print("WRSI: no finite cells (insufficient overlap between inputs)")


if __name__ == "__main__":
    main()
