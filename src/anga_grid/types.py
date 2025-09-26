from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from anga_grid.exceptions import AngaGridError


@dataclass(frozen=True, slots=True)
class BoundingBox:
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.min_lat <= 90.0):
            raise AngaGridError(f"min_lat out of range: {self.min_lat}")
        if not (-90.0 <= self.max_lat <= 90.0):
            raise AngaGridError(f"max_lat out of range: {self.max_lat}")
        if not (-180.0 <= self.min_lon <= 180.0):
            raise AngaGridError(f"min_lon out of range: {self.min_lon}")
        if not (-180.0 <= self.max_lon <= 180.0):
            raise AngaGridError(f"max_lon out of range: {self.max_lon}")
        if self.min_lat > self.max_lat:
            raise AngaGridError(
                f"min_lat {self.min_lat} exceeds max_lat {self.max_lat}"
            )
        if self.min_lon > self.max_lon:
            raise AngaGridError(
                f"min_lon {self.min_lon} exceeds max_lon {self.max_lon}"
            )

    @property
    def lat_span(self) -> float:
        return self.max_lat - self.min_lat

    @property
    def lon_span(self) -> float:
        return self.max_lon - self.min_lon

    def contains(self, lat: float, lon: float) -> bool:
        return (
            self.min_lat <= lat <= self.max_lat
            and self.min_lon <= lon <= self.max_lon
        )


@dataclass(frozen=True, slots=True)
class TimeRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        s = _coerce_date(self.start)
        e = _coerce_date(self.end)
        if s != self.start:
            object.__setattr__(self, "start", s)
        if e != self.end:
            object.__setattr__(self, "end", e)
        if s > e:
            raise AngaGridError(f"start {s} after end {e}")

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def _coerce_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise AngaGridError(f"cannot coerce to date: {value!r}")


@dataclass(frozen=True, slots=True)
class GridSpec:
    resolution_degrees: float
    crs: str = "EPSG:4326"

    def __post_init__(self) -> None:
        if self.resolution_degrees <= 0:
            raise AngaGridError(
                f"resolution must be positive: {self.resolution_degrees}"
            )
        if self.resolution_degrees > 5.0:
            raise AngaGridError(
                f"resolution {self.resolution_degrees}° is implausibly coarse"
            )

    def cells(self, bbox: BoundingBox) -> tuple[int, int]:
        rows = int(round(bbox.lat_span / self.resolution_degrees))
        cols = int(round(bbox.lon_span / self.resolution_degrees))
        return rows, cols


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
