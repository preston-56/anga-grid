from __future__ import annotations

import pytest

from anga_grid.cropping import (
    CALENDARS_BY_REGION,
    EMBU_LONG_RAINS_CALENDAR,
    GARISSA_UNIMODAL_CALENDAR,
    KISUMU_LONG_RAINS_CALENDAR,
    MOMBASA_LONG_RAINS_CALENDAR,
    NAKURU_LONG_RAINS_CALENDAR,
    NAKURU_SHORT_RAINS_CALENDAR,
    get_calendar,
)
from anga_grid.exceptions import AngaGridError


def test_catalog_lists_six_calendars() -> None:
    assert len(CALENDARS_BY_REGION) == 6


def test_get_calendar_case_insensitive() -> None:
    assert get_calendar("Nakuru-Long-Rains") is NAKURU_LONG_RAINS_CALENDAR


def test_get_calendar_unknown_raises() -> None:
    with pytest.raises(AngaGridError, match="unknown calendar"):
        get_calendar("antarctic")


def test_kisumu_planting_earlier_than_nakuru() -> None:
    nakuru = NAKURU_LONG_RAINS_CALENDAR.for_crop("maize")
    kisumu = KISUMU_LONG_RAINS_CALENDAR.for_crop("maize")
    assert kisumu.planting_doy < nakuru.planting_doy


def test_garissa_planting_later_than_nakuru() -> None:
    nakuru = NAKURU_LONG_RAINS_CALENDAR.for_crop("maize")
    garissa = GARISSA_UNIMODAL_CALENDAR.for_crop("sorghum")
    assert garissa.planting_doy > nakuru.planting_doy


def test_mombasa_uses_coastal_long_rains_season() -> None:
    entry = MOMBASA_LONG_RAINS_CALENDAR.for_crop("maize")
    assert entry.season == "coastal-long-rains"


def test_garissa_uses_unimodal_season() -> None:
    entry = GARISSA_UNIMODAL_CALENDAR.for_crop("sorghum")
    assert entry.season == "northern-unimodal"


def test_embu_calendar_has_maize_and_beans() -> None:
    crops = {e.crop for e in EMBU_LONG_RAINS_CALENDAR.entries}
    assert crops == {"maize", "beans"}


def test_short_rains_planting_doy_after_long_rains() -> None:
    long_rains = NAKURU_LONG_RAINS_CALENDAR.for_crop("maize")
    short_rains = NAKURU_SHORT_RAINS_CALENDAR.for_crop("maize")
    assert short_rains.planting_doy > long_rains.planting_doy


def test_each_calendar_for_crop_lookup_works() -> None:
    for cal in CALENDARS_BY_REGION.values():
        for entry in cal.entries:
            looked = cal.for_crop(entry.crop)
            assert looked is entry


def test_green_grams_short_cycle_in_mombasa_and_garissa() -> None:
    mombasa = MOMBASA_LONG_RAINS_CALENDAR.for_crop("green-grams")
    garissa = GARISSA_UNIMODAL_CALENDAR.for_crop("green-grams")
    assert mombasa.days_to_harvest <= 80
    assert garissa.days_to_harvest <= 85


def test_phenology_windows_remain_chronological_for_all_regions() -> None:
    for cal in CALENDARS_BY_REGION.values():
        for entry in cal.entries:
            starts = [
                entry.land_preparation().start_doy,
                entry.sowing().start_doy,
                entry.flowering().start_doy,
                entry.grain_filling().start_doy,
                entry.harvest().start_doy,
            ]
            assert starts == sorted(starts), f"{cal.name}/{entry.crop} out of order"
