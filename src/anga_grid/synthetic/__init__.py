"""Schema-compatible synthetic datasets for tests, examples, and demos.

These builders produce xarray.Dataset objects with the variable
names, units, and CF attrs each provider's canonicalisation expects.
The intent is twofold:

1. Tests can run end-to-end without network or licensed data.
2. New users walking the README's Quick Look on a fresh machine
   have a one-line route to a working --source-override file.

Output is deterministic given the seed argument, so regression
tests can pin numerical values.
"""

from anga_grid.synthetic.agera5 import synthetic_agera5
from anga_grid.synthetic.chirps import synthetic_chirps, synthetic_chirps_multiyear
from anga_grid.synthetic.nex_gddp import synthetic_nex_gddp
from anga_grid.synthetic.tamsat import synthetic_tamsat

__all__ = [
    "synthetic_agera5",
    "synthetic_chirps",
    "synthetic_chirps_multiyear",
    "synthetic_nex_gddp",
    "synthetic_tamsat",
]
