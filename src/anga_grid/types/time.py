from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from anga_grid.exceptions import AngaGridError


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
