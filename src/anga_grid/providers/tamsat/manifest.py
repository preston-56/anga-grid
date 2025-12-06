from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from anga_grid.provenance import Manifest, stamp
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr


CONVECTIVE_UNDERESTIMATE_CAVEAT = (
    "TAMSAT African-only rainfall estimate; "
    "tends to underestimate convective extremes vs gauge networks"
)


def build_manifest(
    provider_name: str,
    version: str,
    bbox: BoundingBox,
    time_range: TimeRange,
) -> Manifest:
    m = Manifest(
        source=f"TAMSAT-v{version}",
        source_version=version,
        provider=provider_name,
        subset_bbox=(
            f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}"
        ),
        subset_time=(
            f"{time_range.start.isoformat()}/{time_range.end.isoformat()}"
        ),
        retrieved_at=datetime.now(UTC).isoformat(),
    )
    m.add_caveat(CONVECTIVE_UNDERESTIMATE_CAVEAT)
    m.record(
        "fetch",
        region_bbox=m.subset_bbox,
        time_range=m.subset_time,
        tamsat_version=version,
    )
    return m


def apply_manifest(ds: xr.Dataset, manifest: Manifest) -> xr.Dataset:
    stamp(ds, manifest)
    if "precip" in ds.data_vars:
        for key, value in manifest.as_attrs().items():
            ds["precip"].attrs.setdefault(key, value)
    return ds
