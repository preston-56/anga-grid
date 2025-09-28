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

    @property
    def length_days(self) -> int:
        if self.wraps_year:
            return (366 - self.start_doy + 1) + self.end_doy
        return self.end_doy - self.start_doy + 1

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


_KMD_BIMODAL_REGION = BoundingBox(
    min_lat=-12.0, max_lat=3.0, min_lon=33.0, max_lon=42.0
)
_GHA_REGION = BoundingBox(
    min_lat=-12.0, max_lat=18.0, min_lon=21.0, max_lon=52.0
)
_COASTAL_REGION = BoundingBox(
    min_lat=-7.0, max_lat=-1.0, min_lon=38.5, max_lon=42.5
)
_UNIMODAL_NORTH_REGION = BoundingBox(
    min_lat=3.0, max_lat=14.0, min_lon=33.0, max_lon=46.0
)
_RIFT_HIGHLANDS_REGION = BoundingBox(
    min_lat=-1.5, max_lat=1.0, min_lon=35.0, max_lon=36.5
)


SEASONS: dict[str, Season] = {
    "long-rains": Season(
        name="long-rains",
        start_doy=60,
        end_doy=151,
        region=_KMD_BIMODAL_REGION,
        definition_source="KMD-bimodal-MAM",
    ),
    "short-rains": Season(
        name="short-rains",
        start_doy=274,
        end_doy=365,
        region=_KMD_BIMODAL_REGION,
        definition_source="KMD-bimodal-OND",
    ),
    "coastal-long-rains": Season(
        name="coastal-long-rains",
        start_doy=60,
        end_doy=181,
        region=_COASTAL_REGION,
        definition_source="KMD-coastal-MAMJ",
    ),
    "northern-unimodal": Season(
        name="northern-unimodal",
        start_doy=60,
        end_doy=243,
        region=_UNIMODAL_NORTH_REGION,
        definition_source="ICPAC-unimodal-MAMJJA",
    ),
    "highland-long-rains": Season(
        name="highland-long-rains",
        start_doy=74,
        end_doy=165,
        region=_RIFT_HIGHLANDS_REGION,
        definition_source="KMD-highland-shifted",
    ),
    "gha-mam": Season(
        name="gha-mam",
        start_doy=60,
        end_doy=151,
        region=_GHA_REGION,
        definition_source="ICPAC-GHACOF-MAM",
    ),
    "gha-ond": Season(
        name="gha-ond",
        start_doy=274,
        end_doy=365,
        region=_GHA_REGION,
        definition_source="ICPAC-GHACOF-OND",
    ),
}


def get_season(name: str) -> Season:
    if name not in SEASONS:
        raise SeasonError(
            f"unknown season {name!r}; known: {sorted(SEASONS)}"
        )
    return SEASONS[name]


def seasons_at(lat: float, lon: float) -> list[Season]:
    return [s for s in SEASONS.values() if s.applies_to(lat, lon)]
