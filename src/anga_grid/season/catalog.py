from __future__ import annotations

from anga_grid.exceptions import SeasonError
from anga_grid.season.types import Season
from anga_grid.types import BoundingBox

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
