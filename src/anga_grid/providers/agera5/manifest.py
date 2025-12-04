from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from anga_grid.provenance import Manifest, stamp
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr


HOURLY_AGGREGATE_CAVEAT = (
    "AgERA5 daily aggregates derived from hourly ERA5; "
    "wind and humidity diurnal cycles are summarized, not preserved"
)


def build_manifest(
    provider_name: str,
    variables: tuple[str, ...],
    bbox: BoundingBox,
    time_range: TimeRange,
) -> Manifest:
    m = Manifest(
        source="AgERA5-v1.1",
        source_version="1.1",
        provider=provider_name,
        subset_bbox=(
            f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}"
        ),
        subset_time=(
            f"{time_range.start.isoformat()}/{time_range.end.isoformat()}"
        ),
        retrieved_at=datetime.now(UTC).isoformat(),
    )
    m.add_caveat(HOURLY_AGGREGATE_CAVEAT)
    m.record(
        "fetch",
        region_bbox=m.subset_bbox,
        time_range=m.subset_time,
        variables=",".join(variables),
    )
    return m


def apply_manifest(ds: xr.Dataset, manifest: Manifest) -> xr.Dataset:
    stamp(ds, manifest)
    for var in ds.data_vars:
        for key, value in manifest.as_attrs().items():
            ds[var].attrs.setdefault(key, value)
    return ds
