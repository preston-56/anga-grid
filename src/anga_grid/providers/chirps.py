from __future__ import annotations

from dataclasses import dataclass
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
            "with a path to a local NetCDF/Zarr replica"
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
        ds = xr.open_dataset(path, decode_cf=True)
        ds = self._subset(ds, bbox, time_range)
        ds.attrs.setdefault("source", "CHIRPS-2.0")
        ds.attrs.setdefault("provider", self.name)
        ds.attrs.setdefault(
            "subset_bbox",
            f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}",
        )
        ds.attrs.setdefault(
            "subset_time", f"{time_range.start.isoformat()}/{time_range.end.isoformat()}"
        )
        return ds

    @staticmethod
    def _subset(
        ds: xr.Dataset, bbox: BoundingBox, time_range: TimeRange
    ) -> xr.Dataset:
        lat_name = _coord(ds, ("lat", "latitude", "y"))
        lon_name = _coord(ds, ("lon", "longitude", "x"))
        time_name = _coord(ds, ("time", "T"))
        out = ds.sel(
            {
                lat_name: slice(bbox.min_lat, bbox.max_lat),
                lon_name: slice(bbox.min_lon, bbox.max_lon),
                time_name: slice(
                    time_range.start.isoformat(), time_range.end.isoformat()
                ),
            }
        )
        if out[lat_name].size == 0 or out[lon_name].size == 0:
            out = ds.sel(
                {
                    lat_name: slice(bbox.max_lat, bbox.min_lat),
                    lon_name: slice(bbox.min_lon, bbox.max_lon),
                    time_name: slice(
                        time_range.start.isoformat(),
                        time_range.end.isoformat(),
                    ),
                }
            )
        return out


def _coord(ds: xr.Dataset, candidates: tuple[str, ...]) -> str:
    for c in candidates:
        if c in ds.coords or c in ds.dims:
            return c
    raise ProviderError(f"none of {candidates} found in dataset")
