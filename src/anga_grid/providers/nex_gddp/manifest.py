from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from anga_grid.provenance import Manifest, stamp
from anga_grid.providers.nex_gddp.scenarios import Scenario
from anga_grid.types import BoundingBox, TimeRange

if TYPE_CHECKING:
    import xarray as xr


PROJECTION_CAVEAT = (
    "NEX-GDDP-CMIP6 statistically downscaled projections; "
    "ensemble members differ in regional skill, especially for "
    "East African short-rains variability"
)


def build_manifest(
    provider_name: str,
    scenario: Scenario,
    model: str,
    bbox: BoundingBox,
    time_range: TimeRange,
    variables: tuple[str, ...],
) -> Manifest:
    m = Manifest(
        source="NEX-GDDP-CMIP6",
        source_version=f"{model}/{scenario.name}",
        provider=provider_name,
        subset_bbox=(
            f"{bbox.min_lat},{bbox.min_lon},{bbox.max_lat},{bbox.max_lon}"
        ),
        subset_time=(
            f"{time_range.start.isoformat()}/{time_range.end.isoformat()}"
        ),
        retrieved_at=datetime.now(UTC).isoformat(),
    )
    m.add_caveat(PROJECTION_CAVEAT)
    if scenario.radiative_forcing_wm2 > 0:
        m.add_caveat(
            f"Scenario {scenario.label}: {scenario.description} "
            f"(radiative forcing ~{scenario.radiative_forcing_wm2} W/m²)"
        )
    m.record(
        "fetch",
        scenario=scenario.name,
        model=model,
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
