from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError
from anga_grid.logging import get_logger
from anga_grid.providers.tamsat.manifest import apply_manifest, build_manifest
from anga_grid.providers.tamsat.schema import canonicalize
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr

_log = get_logger("providers.tamsat")


@dataclass(frozen=True, slots=True)
class TAMSATProvider:
    cache_dir: Path
    source_override: Path | None = None
    version: str = "3.1"
    name: str = "tamsat-v3.1"

    def fetch(self, bbox: BoundingBox, time_range: TimeRange) -> xr.Dataset:
        if self.source_override is not None:
            return self._open_local(self.source_override, bbox, time_range)
        raise ProviderError(
            "TAMSAT network fetch is not wired in v0.3; pass source_override "
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
            raise ProviderError(f"TAMSAT source not found: {path}")
        _log.info("opening TAMSAT source", extra={"path": str(path)})

        if path.is_dir() and path.suffix == ".zarr":
            ds = xr.open_zarr(path)
        elif path.is_dir():
            ncs = sorted(path.glob("*.nc"))
            if not ncs:
                raise ProviderError(f"no NetCDFs under {path}")
            ds = xr.open_mfdataset(
                [str(p) for p in ncs], combine="by_coords", decode_cf=True
            )
        else:
            ds = xr.open_dataset(path, decode_cf=True, mask_and_scale=True)

        ds = canonicalize(ds)
        ds = self._subset(ds, bbox, time_range)
        ds = self._validate(ds)
        return apply_manifest(
            ds, build_manifest(self.name, self.version, bbox, time_range)
        )

    @staticmethod
    def _subset(
        ds: xr.Dataset,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        if "lat" not in ds.coords or "lon" not in ds.coords:
            raise ProviderError("dataset missing lat/lon coords")
        if "time" not in ds.coords:
            raise ProviderError("dataset missing time coord")

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
            time=slice(time_range.start.isoformat(), time_range.end.isoformat()),
        )

    @staticmethod
    def _validate(ds: xr.Dataset) -> xr.Dataset:
        if ds.sizes.get("time", 0) == 0:
            raise ProviderError("subset is empty along time")
        if ds.sizes.get("lat", 0) == 0 or ds.sizes.get("lon", 0) == 0:
            raise ProviderError("subset is empty along lat/lon")
        if "precip" not in ds.data_vars:
            raise ProviderError("precip variable missing post-canonicalization")
        return ds
