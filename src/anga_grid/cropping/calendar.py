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
