# Contributing a regional cropping calendar

If your county or region isn't in `CALENDARS_BY_REGION`, the
shortest path to ship support is a calendar PR. Here's the
recipe.

## What we need from you

For each crop you want covered:

- **planting_doy**: the typical sowing day-of-year as practised
  locally. Don't use the season's start_doy from `season.SEASONS`
  unless they actually match for your region.
- **days_to_flower / days_to_fill / days_to_harvest**: phenology
  estimates from a local extension service publication, FAO
  variety reference, or a peer-reviewed agronomy paper from your
  region. Generic global crop coefficients (FAO-56 default
  durations) are a fallback if you don't have anything closer.
- **season**: the key from `season.SEASONS` your calendar anchors
  to. If your region needs a season that isn't catalogued yet,
  that's a separate PR — open it first.

## What we need from the PR

1. New `CalendarEntry` constants in
   `src/anga_grid/cropping/calendar.py`. Naming convention is
   `<REGION>_<CROP>` (uppercase, hyphens replaced by underscores).
2. A `CroppingCalendar` constant assembling those entries, named
   `<REGION>_<SEASON>_CALENDAR`.
3. Add the calendar to `CALENDARS_BY_REGION` with a
   `<region>-<season>` key (lowercase, hyphenated).
4. Re-export both the entries and the calendar from
   `cropping/__init__.py`.
5. Tests in `tests/unit/test_cropping_regions.py` covering at
   minimum: every crop is reachable via `for_crop`, the planting
   DOY makes sense relative to neighbouring regions in the
   catalog, the season key matches an existing `season.SEASONS`
   entry.
6. A citation in the PR description for the planting DOY and
   phenology estimates. Without it the PR can't merge.

## Worked example

Suppose you want to add Trans Nzoia maize:

```python
TRANS_NZOIA_MAIZE = CalendarEntry(
    crop="maize",
    region="trans-nzoia",
    planting_doy=80,        # ~21 March; from KALRO Trans Nzoia 2023 bulletin
    days_to_flower=70,      # H614 / H6213 hybrid avg
    days_to_fill=100,
    days_to_harvest=140,
    season="long-rains",
)

TRANS_NZOIA_LONG_RAINS_CALENDAR = CroppingCalendar(
    name="trans-nzoia-long-rains",
    entries=(TRANS_NZOIA_MAIZE,),
)

CALENDARS_BY_REGION["trans-nzoia-long-rains"] = TRANS_NZOIA_LONG_RAINS_CALENDAR
```

Plus a test:

```python
def test_trans_nzoia_planting_aligns_with_western_pattern() -> None:
    tn = get_calendar("trans-nzoia-long-rains").for_crop("maize")
    kisumu = KISUMU_LONG_RAINS_CALENDAR.for_crop("maize")
    # Western/Rift Valley western flank plant within ~3 weeks of each other
    assert abs(tn.planting_doy - kisumu.planting_doy) <= 21
```

## Things we'll push back on

- Calendars copied from a generic global crop database without a
  local-source check.
- Planting DOYs that don't fall within the relevant Season window.
- Crop names that don't match common usage (use `maize`, not `corn`;
  `green-grams`, not `mung-beans`).
