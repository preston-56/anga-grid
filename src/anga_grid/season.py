from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from anga_grid.exceptions import SeasonError
from anga_grid.types import BoundingBox

if TYPE_CHECKING:
    import xarray as xr


@dataclass(frozen=True, slots=True)
class Season:
    name: str
    start_doy: int
    end_doy: int
    region: BoundingBox | None = None
    definition_source: str = ""
    baseline_years: tuple[int, int] | None = field(default=None)

    def __post_init__(self) -> None:
        if not 1 <= self.start_doy <= 366:
            raise SeasonError(f"start_doy out of range: {self.start_doy}")
        if not 1 <= self.end_doy <= 366:
            raise SeasonError(f"end_doy out of range: {self.end_doy}")
        if self.baseline_years is not None:
            a, b = self.baseline_years
            if a > b:
                raise SeasonError(f"baseline reversed: {a}..{b}")

    @property
    def wraps_year(self) -> bool:
        return self.start_doy > self.end_doy

    def applies_to(self, lat: float, lon: float) -> bool:
        if self.region is None:
            return True
        return self.region.contains(lat, lon)

    def subset(self, da: xr.DataArray) -> xr.DataArray:
        if "time" not in da.dims:
            raise SeasonError("DataArray must have a 'time' dimension")
        doy = da["time"].dt.dayofyear
        if self.wraps_year:
            mask = (doy >= self.start_doy) | (doy <= self.end_doy)
        else:
            mask = (doy >= self.start_doy) & (doy <= self.end_doy)
        return da.where(mask, drop=True)


SEASONS: dict[str, Season] = {}
