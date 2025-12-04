from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError
from anga_grid.logging import get_logger
from anga_grid.providers.agera5.manifest import apply_manifest, build_manifest
from anga_grid.providers.agera5.schema import canonicalize
from anga_grid.providers.agera5.variables import AGERA5_DEFAULT_VARIABLES
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr

_log = get_logger("providers.agera5")


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

        ds = canonicalize(ds)
        ds = self._subset(ds, bbox, time_range)
        ds = self._select_requested_vars(ds)
        ds = self._validate(ds)
        return apply_manifest(
            ds, build_manifest(self.name, self.variables, bbox, time_range)
        )

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

    @staticmethod
    def _subset(
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

    @staticmethod
    def _validate(ds: xr.Dataset) -> xr.Dataset:
        if ds.sizes.get("time", 0) == 0:
            raise ProviderError("subset is empty along time")
        if ds.sizes.get("lat", 0) == 0 or ds.sizes.get("lon", 0) == 0:
            raise ProviderError("subset is empty along lat/lon")
        if not ds.data_vars:
            raise ProviderError("no AgERA5 variables present after canonicalization")
        return ds
