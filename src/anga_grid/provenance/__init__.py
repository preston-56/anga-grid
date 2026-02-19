"""Provenance manifest for every output anga-grid produces.

Manifest is the structured form; Step is one operation entry inside
the history chain. stamp() writes a manifest into a Dataset's attrs,
read() reconstitutes it, merge() composes parent + child manifests
when an indicator's input was itself produced by an earlier
indicator.

See doc/adr/0003-manifest-as-attrs.md for the rationale on the
xarray-attrs encoding (instead of a sidecar file or PROV-O).
"""

from anga_grid.provenance.manifest import Manifest
from anga_grid.provenance.ops import merge, read, stamp
from anga_grid.provenance.steps import Step

__all__ = ["Manifest", "Step", "merge", "read", "stamp"]
