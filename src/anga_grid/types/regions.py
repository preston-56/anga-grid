from __future__ import annotations

from anga_grid.exceptions import AngaGridError
from anga_grid.types.geometry import BoundingBox

NAKURU_BBOX = BoundingBox(
    min_lat=-1.20, max_lat=0.05, min_lon=35.55, max_lon=36.55
)
NJORO_BBOX = BoundingBox(
    min_lat=-0.40, max_lat=-0.25, min_lon=35.90, max_lon=36.05
)
MOLO_BBOX = BoundingBox(
    min_lat=-0.30, max_lat=-0.15, min_lon=35.70, max_lon=35.85
)

REGION_BBOXES: dict[str, BoundingBox] = {
    "nakuru": NAKURU_BBOX,
    "njoro": NJORO_BBOX,
    "molo": MOLO_BBOX,
}


def resolve_region(name: str) -> BoundingBox:
    key = name.strip().lower()
    if key not in REGION_BBOXES:
        raise AngaGridError(
            f"unknown region {name!r}; known: {sorted(REGION_BBOXES)}"
        )
    return REGION_BBOXES[key]
