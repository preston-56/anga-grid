from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from anga_grid.exceptions import ProviderError
from anga_grid.logging import get_logger
from anga_grid.providers.nex_gddp.manifest import apply_manifest, build_manifest
from anga_grid.providers.nex_gddp.scenarios import HISTORICAL, Scenario
from anga_grid.providers.nex_gddp.schema import (
    canonicalize,
    convert_units,
    validate_required_variables,
)
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr

_log = get_logger("providers.nex_gddp")


DEFAULT_VARIABLES: tuple[str, ...] = (
    "tas_mean",
    "tas_min",
    "tas_max",
    "precipitation",
)


@dataclass(frozen=True, slots=True)
class NEXGDDPProvider:
    cache_dir: Path
    source_override: Path | None = None
    scenario: Scenario = HISTORICAL
    model: str = "GFDL-ESM4"
    variables: tuple[str, ...] = field(default_factory=lambda: DEFAULT_VARIABLES)
    name: str = "nex-gddp-cmip6"

    def fetch(self, bbox: BoundingBox, time_range: TimeRange) -> xr.Dataset:
        if self.source_override is not None:
            return self._open_local(self.source_override, bbox, time_range)
        raise ProviderError(
            "NEX-GDDP network fetch is not wired in v0.4; pass "
            "source_override with a path to a local NetCDF/Zarr replica"
        )

    def _open_local(
        self,
        path: Path,
        bbox: BoundingBox,
        time_range: TimeRange,
    ) -> xr.Dataset:
        import xarray as xr

        if not path.exists():
            raise ProviderError(f"NEX-GDDP source not found: {path}")
        _log.info(
            "opening NEX-GDDP source",
            extra={
                "path": str(path),
                "scenario": self.scenario.name,
                "model": self.model,
            },
        )

        if path.is_dir() and path.suffix == ".zarr":
            ds = xr.open_zarr(path)
        elif path.is_dir():
            ncs = sorted(path.glob("*.nc"))
            if not ncs:
                raise ProviderError(f"no NetCDFs found under {path}")
            ds = xr.open_mfdataset(
                [str(p) for p in ncs], combine="by_coords", decode_cf=True
            )
        else:
            ds = xr.open_dataset(path, decode_cf=True, mask_and_scale=True)

        ds = canonicalize(ds)
        ds = convert_units(ds)
        ds = self._subset(ds, bbox, time_range)
        ds = self._select_variables(ds)
        ds = validate_required_variables(ds, self.variables)
        ds = self._validate(ds)
        return apply_manifest(
            ds,
            build_manifest(
                self.name, self.scenario, self.model, bbox, time_range, self.variables
            ),
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
            time=slice(
                time_range.start.isoformat(),
                time_range.end.isoformat(),
            ),
        )

    def _select_variables(self, ds: xr.Dataset) -> xr.Dataset:
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
        return ds
