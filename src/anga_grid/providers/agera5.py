from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError
from anga_grid.logging import get_logger
from anga_grid.provenance import Manifest, stamp
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr

_log = get_logger("providers.agera5")

AGERA5_DEFAULT_VARIABLES: tuple[str, ...] = (
    "temperature_air_mean_daily",
    "temperature_air_min_daily",
    "temperature_air_max_daily",
    "precipitation_flux",
    "solar_radiation_flux",
    "vapour_pressure_daily",
    "wind_speed_10m_mean_daily",
    "relative_humidity_2m_12h",
)

AGERA5_VAR_RENAMES: dict[str, str] = {
    "Temperature_Air_Mean_Daily": "temperature_air_mean_daily",
    "Temperature_Air_Min_Daily": "temperature_air_min_daily",
    "Temperature_Air_Max_Daily": "temperature_air_max_daily",
    "Precipitation_Flux": "precipitation_flux",
    "Solar_Radiation_Flux": "solar_radiation_flux",
    "Vapour_Pressure_Mean": "vapour_pressure_daily",
    "Wind_Speed_10m_Mean": "wind_speed_10m_mean_daily",
    "Relative_Humidity_2m_12h": "relative_humidity_2m_12h",
}


@dataclass(frozen=True, slots=True)
class AgERA5Provider:
    cache_dir: Path
    source_override: Path | None = None
    variables: tuple[str, ...] = field(default_factory=lambda: AGERA5_DEFAULT_VARIABLES)
    name: str = "agera5-v1.1"

    def fetch(self, bbox: BoundingBox, time_range: TimeRange) -> xr.Dataset:
        if self.source_override is not None:
            return self._open_local(self.source_override, bbox, time_range)
        raise ProviderError(
            "AgERA5 network fetch is not wired in v0.2; pass source_override "
            "with a path to a local NetCDF/Zarr replica or a directory of "
            "per-variable NetCDFs"
        )

    def _open_local(
        self,
        path: Path,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        import xarray as xr

        if not path.exists():
            raise ProviderError(f"AgERA5 source not found: {path}")
        _log.info("opening AgERA5 source", extra={"path": str(path)})

        if path.is_dir() and path.suffix == ".zarr":
            ds = xr.open_zarr(path)
        elif path.is_dir():
            ds = self._open_directory(path)
        else:
            ds = xr.open_dataset(path, decode_cf=True, mask_and_scale=True)

        ds = self._canonicalize(ds)
        ds = self._subset(ds, bbox, time_range)
        ds = self._select_requested_vars(ds)
        ds = self._validate(ds)
        return self._stamp_provenance(ds, bbox, time_range)

    def _open_directory(self, path: Path) -> xr.Dataset:
        import xarray as xr

        ncs = sorted(path.glob("*.nc"))
        if not ncs:
            raise ProviderError(f"no NetCDFs found under {path}")
        try:
            return xr.open_mfdataset(
                [str(p) for p in ncs],
                combine="by_coords",
                decode_cf=True,
                mask_and_scale=True,
            )
        except (ValueError, OSError) as exc:
            raise ProviderError(f"failed to combine {len(ncs)} files: {exc}") from exc

    def _canonicalize(self, ds: xr.Dataset) -> xr.Dataset:
        coord_renames: dict[str, str] = {}
        for source_name, target in (
            ("latitude", "lat"),
            ("y", "lat"),
            ("longitude", "lon"),
            ("x", "lon"),
            ("T", "time"),
        ):
            if (source_name in ds.coords or source_name in ds.dims) and (
                target not in ds.coords and target not in ds.dims
            ):
                coord_renames[source_name] = target
        if coord_renames:
            ds = ds.rename(coord_renames)

        var_renames = {
            source: target
            for source, target in AGERA5_VAR_RENAMES.items()
            if source in ds.data_vars and target not in ds.data_vars
        }
        if var_renames:
            ds = ds.rename(var_renames)
        return ds

    def _subset(
        self,
        ds: xr.Dataset,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        if "lat" not in ds.coords or "lon" not in ds.coords:
            raise ProviderError("dataset missing 'lat'/'lon' coordinates")
        if "time" not in ds.coords:
            raise ProviderError("dataset missing 'time' coordinate")

        lat_descending = (
            ds["lat"].size > 1 and float(ds["lat"][0]) > float(ds["lat"][-1])
        )
        lat_slice = (
            slice(bbox.max_lat, bbox.min_lat)
            if lat_descending
            else slice(bbox.min_lat, bbox.max_lat)
        )
        return ds.sel(
            lat=lat_slice,
            lon=slice(bbox.min_lon, bbox.max_lon),
            time=slice(
                time_range.start.isoformat(),
                time_range.end.isoformat(),
            ),
        )

    def _select_requested_vars(self, ds: xr.Dataset) -> xr.Dataset:
        keep = [v for v in self.variables if v in ds.data_vars]
        if not keep:
            return ds
        return ds[keep]

    def _validate(self, ds: xr.Dataset) -> xr.Dataset:
        if ds.sizes.get("time", 0) == 0:
            raise ProviderError("subset is empty along time")
        if ds.sizes.get("lat", 0) == 0 or ds.sizes.get("lon", 0) == 0:
            raise ProviderError("subset is empty along lat/lon")
        if not ds.data_vars:
            raise ProviderError("no AgERA5 variables present after canonicalization")
        return ds

    def _stamp_provenance(
        self,
        ds: xr.Dataset,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        m = Manifest(
            source="AgERA5-v1.1",
            source_version="1.1",
            provider=self.name,
            subset_bbox=(
                f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}"
            ),
            subset_time=(
                f"{time_range.start.isoformat()}/{time_range.end.isoformat()}"
            ),
            retrieved_at=datetime.now(UTC).isoformat(),
        )
        m.add_caveat(
            "AgERA5 daily aggregates derived from hourly ERA5; "
            "wind and humidity diurnal cycles are summarized, not preserved"
        )
        m.record(
            "fetch",
            region_bbox=m.subset_bbox,
            time_range=m.subset_time,
            variables=",".join(self.variables),
        )
        stamp(ds, m)
        for var in ds.data_vars:
            for key, value in m.as_attrs().items():
                ds[var].attrs.setdefault(key, value)
        return ds
