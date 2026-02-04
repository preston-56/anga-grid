from __future__ import annotations

from dataclasses import dataclass, field

from anga_grid.cropping.windows import (
    Window,
    flowering_window,
    grain_filling_window,
    land_preparation_window,
    sowing_window,
)
from anga_grid.exceptions import AngaGridError


@dataclass(frozen=True, slots=True)
class CalendarEntry:
    crop: str
    region: str
    planting_doy: int
    days_to_flower: int = 65
    days_to_fill: int = 95
    days_to_harvest: int = 130
    season: str = ""

    def land_preparation(self) -> Window:
        return land_preparation_window(self.planting_doy)

    def sowing(self) -> Window:
        return sowing_window(self.planting_doy)

    def flowering(self) -> Window:
        return flowering_window(self.planting_doy, self.days_to_flower)

    def grain_filling(self) -> Window:
        return grain_filling_window(self.planting_doy, self.days_to_fill)

    def harvest(self) -> Window:
        start = min(366, self.planting_doy + self.days_to_harvest)
        end = min(366, start + 14)
        return Window(name="harvest", start_doy=start, end_doy=end)


@dataclass(frozen=True, slots=True)
class CroppingCalendar:
    name: str
    entries: tuple[CalendarEntry, ...] = field(default_factory=tuple)

    def for_crop(self, crop: str) -> CalendarEntry:
        for entry in self.entries:
            if entry.crop.lower() == crop.lower():
                return entry
        raise AngaGridError(
            f"crop {crop!r} not in calendar {self.name!r}; "
            f"available: {[e.crop for e in self.entries]}"
        )


NAKURU_MAIZE = CalendarEntry(
    crop="maize",
    region="nakuru",
    planting_doy=85,
    days_to_flower=65,
    days_to_fill=95,
    days_to_harvest=130,
    season="long-rains",
)

NAKURU_BEANS = CalendarEntry(
    crop="beans",
    region="nakuru",
    planting_doy=82,
    days_to_flower=45,
    days_to_fill=70,
    days_to_harvest=95,
    season="long-rains",
)

NAKURU_SHORT_RAINS_MAIZE = CalendarEntry(
    crop="maize",
    region="nakuru",
    planting_doy=290,
    days_to_flower=60,
    days_to_fill=85,
    days_to_harvest=120,
    season="short-rains",
)


NAKURU_LONG_RAINS_CALENDAR = CroppingCalendar(
    name="nakuru-long-rains",
    entries=(NAKURU_MAIZE, NAKURU_BEANS),
)

NAKURU_SHORT_RAINS_CALENDAR = CroppingCalendar(
    name="nakuru-short-rains",
    entries=(NAKURU_SHORT_RAINS_MAIZE,),
)


EMBU_MAIZE = CalendarEntry(
    crop="maize",
    region="embu",
    planting_doy=70,
    days_to_flower=58,
    days_to_fill=88,
    days_to_harvest=120,
    season="long-rains",
)

EMBU_BEANS = CalendarEntry(
    crop="beans",
    region="embu",
    planting_doy=72,
    days_to_flower=42,
    days_to_fill=68,
    days_to_harvest=92,
    season="long-rains",
)

EMBU_LONG_RAINS_CALENDAR = CroppingCalendar(
    name="embu-long-rains",
    entries=(EMBU_MAIZE, EMBU_BEANS),
)


KISUMU_MAIZE = CalendarEntry(
    crop="maize",
    region="kisumu",
    planting_doy=64,
    days_to_flower=60,
    days_to_fill=85,
    days_to_harvest=115,
    season="long-rains",
)

KISUMU_SORGHUM = CalendarEntry(
    crop="sorghum",
    region="kisumu",
    planting_doy=64,
    days_to_flower=70,
    days_to_fill=100,
    days_to_harvest=130,
    season="long-rains",
)

KISUMU_LONG_RAINS_CALENDAR = CroppingCalendar(
    name="kisumu-long-rains",
    entries=(KISUMU_MAIZE, KISUMU_SORGHUM),
)


MOMBASA_MAIZE = CalendarEntry(
    crop="maize",
    region="mombasa",
    planting_doy=85,
    days_to_flower=65,
    days_to_fill=95,
    days_to_harvest=125,
    season="coastal-long-rains",
)

MOMBASA_GREEN_GRAMS = CalendarEntry(
    crop="green-grams",
    region="mombasa",
    planting_doy=85,
    days_to_flower=35,
    days_to_fill=55,
    days_to_harvest=75,
    season="coastal-long-rains",
)

MOMBASA_LONG_RAINS_CALENDAR = CroppingCalendar(
    name="mombasa-long-rains",
    entries=(MOMBASA_MAIZE, MOMBASA_GREEN_GRAMS),
)


GARISSA_SORGHUM = CalendarEntry(
    crop="sorghum",
    region="garissa",
    planting_doy=110,
    days_to_flower=75,
    days_to_fill=105,
    days_to_harvest=135,
    season="northern-unimodal",
)

GARISSA_GREEN_GRAMS = CalendarEntry(
    crop="green-grams",
    region="garissa",
    planting_doy=110,
    days_to_flower=38,
    days_to_fill=58,
    days_to_harvest=80,
    season="northern-unimodal",
)

GARISSA_UNIMODAL_CALENDAR = CroppingCalendar(
    name="garissa-unimodal",
    entries=(GARISSA_SORGHUM, GARISSA_GREEN_GRAMS),
)


CALENDARS_BY_REGION: dict[str, CroppingCalendar] = {
    "nakuru-long-rains": NAKURU_LONG_RAINS_CALENDAR,
    "nakuru-short-rains": NAKURU_SHORT_RAINS_CALENDAR,
    "embu-long-rains": EMBU_LONG_RAINS_CALENDAR,
    "kisumu-long-rains": KISUMU_LONG_RAINS_CALENDAR,
    "mombasa-long-rains": MOMBASA_LONG_RAINS_CALENDAR,
    "garissa-unimodal": GARISSA_UNIMODAL_CALENDAR,
}


def get_calendar(name: str) -> CroppingCalendar:
    key = name.strip().lower()
    if key not in CALENDARS_BY_REGION:
        raise AngaGridError(
            f"unknown calendar {name!r}; available: {sorted(CALENDARS_BY_REGION)}"
        )
    return CALENDARS_BY_REGION[key]
