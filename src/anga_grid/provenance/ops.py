from __future__ import annotations

from typing import TYPE_CHECKING

from anga_grid.provenance.manifest import Manifest

if TYPE_CHECKING:
    import xarray as xr


def stamp(ds: xr.Dataset, manifest: Manifest) -> xr.Dataset:
    for key, value in manifest.as_attrs().items():
        ds.attrs[key] = value
    return ds


def read(ds: xr.Dataset) -> Manifest:
    return Manifest.from_attrs(dict(ds.attrs))


def merge(parent: Manifest, child: Manifest, operation: str) -> Manifest:
    merged = Manifest(
        source=child.source or parent.source,
        source_version=child.source_version or parent.source_version,
        provider=child.provider or parent.provider,
        subset_bbox=child.subset_bbox or parent.subset_bbox,
        subset_time=child.subset_time or parent.subset_time,
        retrieved_at=child.retrieved_at or parent.retrieved_at,
        code_version=child.code_version,
    )
    merged.caveats = list({*parent.caveats, *child.caveats})
    merged.steps = [*parent.steps, *child.steps]
    merged.record(operation, parent=parent.source, child=child.source)
    return merged
