from __future__ import annotations

from dataclasses import dataclass

from anga_grid.exceptions import AngaGridError


@dataclass(frozen=True, slots=True)
class Window:
    name: str
    start_doy: int
    end_doy: int

    def __post_init__(self) -> None:
        if not 1 <= self.start_doy <= 366:
            raise AngaGridError(f"start_doy out of range: {self.start_doy}")
        if not 1 <= self.end_doy <= 366:
            raise AngaGridError(f"end_doy out of range: {self.end_doy}")

    @property
    def length_days(self) -> int:
        if self.end_doy >= self.start_doy:
            return self.end_doy - self.start_doy + 1
        return (366 - self.start_doy + 1) + self.end_doy

    @property
    def wraps_year(self) -> bool:
        return self.start_doy > self.end_doy


def land_preparation_window(planting_doy: int, lead_days: int = 21) -> Window:
    if lead_days < 1:
        raise AngaGridError("lead_days must be >= 1")
    start = max(1, planting_doy - lead_days)
    end = max(1, planting_doy - 1)
    return Window(name="land-preparation", start_doy=start, end_doy=end)


def sowing_window(planting_doy: int, span_days: int = 14) -> Window:
    if span_days < 1:
        raise AngaGridError("span_days must be >= 1")
    return Window(
        name="sowing",
        start_doy=planting_doy,
        end_doy=min(366, planting_doy + span_days - 1),
    )


def flowering_window(planting_doy: int, days_to_flower: int = 65) -> Window:
    if days_to_flower < 1:
        raise AngaGridError("days_to_flower must be >= 1")
    start = planting_doy + days_to_flower
    end = start + 14
    return Window(
        name="flowering",
        start_doy=min(366, start),
        end_doy=min(366, end),
    )


def grain_filling_window(planting_doy: int, days_to_fill: int = 95) -> Window:
    start = planting_doy + days_to_fill
    end = start + 21
    return Window(
        name="grain-filling",
        start_doy=min(366, start),
        end_doy=min(366, end),
    )
