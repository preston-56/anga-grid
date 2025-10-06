from __future__ import annotations

from datetime import date, datetime

import pytest

from anga_grid.exceptions import AngaGridError
from anga_grid.types import (
    BoundingBox,
    GridSpec,
    REGION_BBOXES,
    TimeRange,
    resolve_region,
)


def test_bbox_rejects_out_of_range_latitude() -> None:
    with pytest.raises(AngaGridError):
        BoundingBox(min_lat=-100, max_lat=10, min_lon=0, max_lon=10)


def test_bbox_rejects_out_of_range_longitude() -> None:
    with pytest.raises(AngaGridError):
        BoundingBox(min_lat=0, max_lat=10, min_lon=-200, max_lon=10)


def test_bbox_rejects_reversed_lat() -> None:
    with pytest.raises(AngaGridError):
        BoundingBox(min_lat=5, max_lat=-5, min_lon=0, max_lon=10)


def test_bbox_rejects_reversed_lon() -> None:
    with pytest.raises(AngaGridError):
        BoundingBox(min_lat=0, max_lat=10, min_lon=20, max_lon=10)


def test_bbox_lat_lon_span() -> None:
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    assert bbox.lat_span == pytest.approx(2.0)
    assert bbox.lon_span == pytest.approx(2.0)


def test_bbox_contains_interior_point() -> None:
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    assert bbox.contains(0.0, 36.0)
    assert bbox.contains(-1.0, 35.0)
    assert bbox.contains(1.0, 37.0)


def test_bbox_excludes_outside_point() -> None:
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    assert not bbox.contains(2.0, 36.0)
    assert not bbox.contains(0.0, 40.0)


def test_time_range_days() -> None:
    tr = TimeRange(start=date(2024, 1, 1), end=date(2024, 1, 31))
    assert tr.days == 31


def test_time_range_coerces_datetime() -> None:
    tr = TimeRange(start=datetime(2024, 1, 1, 12, 0), end=datetime(2024, 1, 5, 8, 0))
    assert tr.start == date(2024, 1, 1)
    assert tr.end == date(2024, 1, 5)


def test_time_range_coerces_iso_string() -> None:
    tr = TimeRange(start="2024-01-01", end="2024-01-03")  # type: ignore[arg-type]
    assert tr.days == 3


def test_time_range_rejects_reversed() -> None:
    with pytest.raises(AngaGridError):
        TimeRange(start=date(2024, 5, 1), end=date(2024, 1, 1))


def test_gridspec_rejects_non_positive_resolution() -> None:
    with pytest.raises(AngaGridError):
        GridSpec(resolution_degrees=0)
    with pytest.raises(AngaGridError):
        GridSpec(resolution_degrees=-0.05)


def test_gridspec_rejects_implausible_resolution() -> None:
    with pytest.raises(AngaGridError):
        GridSpec(resolution_degrees=10.0)


def test_gridspec_cell_count_against_bbox() -> None:
    bbox = BoundingBox(min_lat=-1, max_lat=1, min_lon=35, max_lon=37)
    spec = GridSpec(resolution_degrees=0.05)
    rows, cols = spec.cells(bbox)
    assert rows == 40
    assert cols == 40


def test_region_catalog_known_keys() -> None:
    assert "nakuru" in REGION_BBOXES
    assert "njoro" in REGION_BBOXES
    assert "molo" in REGION_BBOXES


def test_resolve_region_case_insensitive() -> None:
    a = resolve_region("Nakuru")
    b = resolve_region("nakuru")
    assert a == b


def test_resolve_region_raises_on_unknown() -> None:
    with pytest.raises(AngaGridError):
        resolve_region("atlantis")
