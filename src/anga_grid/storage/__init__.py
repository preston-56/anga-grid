"""Format-agnostic xarray Dataset persistence with manifest preservation.

write/open_dataset auto-detect zarr vs netcdf from the path suffix
so callers don't have to special-case file extensions.
write_with_manifest is the variant that records a 'write' step into
the provenance manifest before persisting; pair with read_manifest
on the read side for round-trip provenance.
"""

from anga_grid.storage.format import Format, ZarrMode, detect_format
from anga_grid.storage.io import open_dataset, write
from anga_grid.storage.manifest_io import read_manifest, write_with_manifest

__all__ = [
    "Format",
    "ZarrMode",
    "detect_format",
    "open_dataset",
    "read_manifest",
    "write",
    "write_with_manifest",
]
