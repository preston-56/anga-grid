from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError
from anga_grid.logging import get_logger
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr

_log = get_logger("providers.chirps")

CHIRPS_FILL_VALUE = -9999.0
CHIRPS_URL_PATTERN = (
    "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/"
    "tifs/p05/{year}/chirps-v2.0.{year}.{month:02d}.{day:02d}.tif.gz"
)
CHIRPS_PRECIP_CANDIDATES: tuple[str, ...] = ("precip", "precipitation", "rainfall")


@dataclass(frozen=True, slots=True)
class CHIRPSProvider:
    cache_dir: Path
    source_override: Path | None = None
    name: str = "chirps-v2.0"

    def fetch(self, bbox: BoundingBox, time_range: TimeRange) -> xr.Dataset:
        if self.source_override is not None:
            return self._open_local(self.source_override, bbox, time_range)
        raise ProviderError(
            "CHIRPS network fetch is not wired in v0.1; pass source_override "
            "with a path to a local NetCDF or Zarr replica"
        )

    def _open_local(
        self,
        path: Path,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        import xarray as xr

        if not path.exists():
            raise ProviderError(f"CHIRPS source not found: {path}")
        _log.info("opening CHIRPS source", extra={"path": str(path)})

        if path.is_dir() and path.suffix == ".zarr":
            ds = xr.open_zarr(path)
        else:
            ds = xr.open_dataset(path, decode_cf=True, mask_and_scale=True)

        ds = self._canonicalize(ds)
        ds = self._subset(ds, bbox, time_range)
        ds = self._validate(ds)
        return self._stamp_provenance(ds, bbox, time_range)

    def _canonicalize(self, ds: xr.Dataset) -> xr.Dataset:
        renames: dict[str, str] = {}
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
                renames[source_name] = target
        if renames:
            ds = ds.rename(renames)
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
            ds["lat"].size > 1
            and float(ds["lat"][0]) > float(ds["lat"][-1])
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

    def _validate(self, ds: xr.Dataset) -> xr.Dataset:
        precip_name = self._find_precip(ds)
        if ds.sizes.get("time", 0) == 0:
            raise ProviderError("subset is empty along time")
        if ds.sizes.get("lat", 0) == 0 or ds.sizes.get("lon", 0) == 0:
            raise ProviderError("subset is empty along lat/lon")
        if precip_name != "precip":
            ds = ds.rename({precip_name: "precip"})
        return ds

    @staticmethod
    def _find_precip(ds: xr.Dataset) -> str:
        for candidate in CHIRPS_PRECIP_CANDIDATES:
            if candidate in ds.data_vars:
                return candidate
        raise ProviderError(
            f"none of {CHIRPS_PRECIP_CANDIDATES} found in dataset; "
            f"variables are {list(ds.data_vars)}"
        )

    def _stamp_provenance(
        self,
        ds: xr.Dataset,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        now = datetime.now(UTC).isoformat()
        ds.attrs.setdefault("source", "CHIRPS-2.0")
        ds.attrs.setdefault("provider", self.name)
        ds.attrs["subset_bbox"] = (
            f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}"
        )
        ds.attrs["subset_time"] = (
            f"{time_range.start.isoformat()}/{time_range.end.isoformat()}"
        )
        ds.attrs["retrieved_at"] = now
        ds.attrs["bias_caveat"] = (
            "CHIRPS underestimates rainfall over complex topography "
            "(Mau Escarpment, Mt. Kenya windward, Aberdares)"
        )
        return ds
