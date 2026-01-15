from __future__ import annotations

import pytest

from anga_grid.cropping import (
    NAKURU_BEANS,
    NAKURU_LONG_RAINS_CALENDAR,
    NAKURU_MAIZE,
    CalendarEntry,
    CroppingCalendar,
    Window,
    flowering_window,
    grain_filling_window,
    land_preparation_window,
    sowing_window,
)
from anga_grid.exceptions import AngaGridError


def test_window_rejects_doy_out_of_range() -> None:
    with pytest.raises(AngaGridError):
        Window(name="x", start_doy=0, end_doy=10)
    with pytest.raises(AngaGridError):
        Window(name="x", start_doy=10, end_doy=400)


def test_window_length_contiguous() -> None:
    assert Window(name="x", start_doy=60, end_doy=151).length_days == 92


def test_window_length_wrapping() -> None:
    w = Window(name="wrap", start_doy=350, end_doy=10)
    assert w.length_days == (366 - 350 + 1) + 10
    assert w.wraps_year


def test_land_preparation_precedes_planting() -> None:
    window = land_preparation_window(planting_doy=80)
    assert window.end_doy < 80
    assert window.length_days <= 21


def test_land_preparation_rejects_zero_lead() -> None:
    with pytest.raises(AngaGridError):
        land_preparation_window(planting_doy=80, lead_days=0)


def test_sowing_window_contains_planting_doy() -> None:
    w = sowing_window(planting_doy=80)
    assert w.start_doy == 80
    assert 80 <= w.end_doy <= 366


def test_flowering_window_appears_after_planting() -> None:
    w = flowering_window(planting_doy=80, days_to_flower=65)
    assert w.start_doy == 145


def test_grain_filling_window_after_flowering() -> None:
    fl = flowering_window(planting_doy=80, days_to_flower=65)
    gf = grain_filling_window(planting_doy=80, days_to_fill=95)
    assert gf.start_doy >= fl.end_doy


def test_calendar_entry_windows_are_chronological() -> None:
    e = NAKURU_MAIZE
    lp = e.land_preparation()
    sw = e.sowing()
    fl = e.flowering()
    gf = e.grain_filling()
    h = e.harvest()
    starts = [lp.start_doy, sw.start_doy, fl.start_doy, gf.start_doy, h.start_doy]
    assert starts == sorted(starts)


def test_for_crop_lookup_case_insensitive() -> None:
    found = NAKURU_LONG_RAINS_CALENDAR.for_crop("MAIZE")
    assert found.crop == "maize"


def test_for_crop_unknown_raises() -> None:
    with pytest.raises(AngaGridError, match="not in calendar"):
        NAKURU_LONG_RAINS_CALENDAR.for_crop("rice")


def test_calendar_has_both_default_crops() -> None:
    crops = {e.crop for e in NAKURU_LONG_RAINS_CALENDAR.entries}
    assert {"maize", "beans"} <= crops


def test_beans_planting_earlier_than_maize_in_nakuru() -> None:
    assert NAKURU_BEANS.planting_doy <= NAKURU_MAIZE.planting_doy + 10


def test_calendar_entry_default_season_blank() -> None:
    e = CalendarEntry(crop="x", region="r", planting_doy=80)
    assert e.season == ""


def test_cropping_calendar_empty_entries_raises_on_lookup() -> None:
    cal = CroppingCalendar(name="empty")
    with pytest.raises(AngaGridError):
        cal.for_crop("anything")
