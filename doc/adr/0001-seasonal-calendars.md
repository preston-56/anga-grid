# ADR 0001: Seasonal calendars as first-class concepts

**Status:** Accepted
**Date:** 2025-09-22

## Context

The vast majority of climate-indicator libraries assume the Gregorian
calendar quarters (JFM / AMJ / JAS / OND) as the natural unit of
seasonal aggregation. This is reasonable for mid-latitude analyses
where seasons are astronomically defined by solstices and equinoxes.

It is not reasonable for East Africa, where rainfall follows a
bimodal pattern driven by the migration of the Inter-Tropical
Convergence Zone (ITCZ). The two rainy seasons — *masika* (long
rains, roughly March through May) and *vuli* (short rains, roughly
October through December) — do not align with Gregorian quarters,
and applying quarterly aggregation to East African rainfall produces
indicators that are systematically wrong in ways that matter
operationally.

Specifically:

- **AMJ aggregation** averages the wettest months (April–May) with
  the start of the dry season (June). The result understates wet-season
  rainfall and masks early-cessation droughts.
- **OND aggregation** sometimes captures the short rains correctly,
  but in years when the rains begin in late September or extend
  into early January, the season boundary is in the wrong place.
- **Sub-regional variation matters.** The unimodal regime north of
  ~3° N (parts of northern Kenya, southern Ethiopia) doesn't have
  two rainy seasons in the same sense. The bimodal-but-shifted regime
  in coastal Kenya has long rains running March through July rather
  than ending in May. Treating "East Africa" as a single season
  pattern is a known source of error.

Operational services (Kenya Meteorological Department, the regional
ICPAC center, county-level early-warning bodies) work with seasonal
windows that are calibrated to the actual climatology of each
sub-region. The published agronomic indicator definitions used by
extension services assume these windows. Indicators computed against
the wrong window are not just less precise — they answer a different
question than the one being asked.

## Decision

Seasons are first-class objects in anga-grid, not derived from
Gregorian dates. The library exposes a `Season` type that encapsulates:

- a name (`"long-rains"`, `"short-rains"`, etc.)
- a definition (either fixed-date windows or onset-anchored)
- a sub-regional applicability (which spatial regions this definition
  applies to)
- a climatological baseline (which years define "normal" for this
  season in this region)

The default seasonal definitions used by `anga-grid` are those of
the Kenya Meteorological Department for the bimodal regime and ICPAC
for the wider Greater Horn of Africa region. These are documented
explicitly in `doc/calendars.md` with citations, and they are
configurable — users with their own validated definitions can
substitute them.

All temporal aggregation operations in the library accept a `Season`
as their windowing unit, in addition to the standard `freq` argument
that `xarray` and `xclim` users will recognize. Operations that take
no season argument and operate over the full time axis are
unchanged.

Where users do want Gregorian-quarter aggregation (e.g. for
comparison with global studies), it remains available — but it is
not the default for any function whose output is meant to be
interpreted seasonally.

## Consequences

**Positive:**

- Indicators computed by anga-grid match the seasonal windows that
  East African operational services actually use, without users
  having to reconfigure every call.
- Sub-regional differences in seasonal pattern are surfaced as
  metadata rather than averaged away.
- The library has a clear, defensible position on what makes it
  East-Africa-specific rather than being "a generic library with
  a Kenya-focused README."

**Negative:**

- We diverge from the `xclim` convention, which uses `freq="QS-MAR"`
  or similar string codes for season-shifted quarters. Users
  familiar with `xclim` will need to learn the `Season` API.
- We take on the responsibility of maintaining accurate seasonal
  definitions across the region. When KMD or ICPAC updates their
  operational definitions, anga-grid must update accordingly.
- Onset-anchored season definitions (where the season starts when
  rainfall actually begins, rather than on a fixed date) introduce
  computational complexity: a season's temporal extent depends on
  the data itself, not just the calendar. This means certain
  caching strategies that assume fixed temporal windows don't work.

**Neutral:**

- This decision constrains anga-grid to remaining East-Africa-focused.
  Generalizing to other regions would require either a meaningful
  expansion of the seasonal catalog (West African monsoon, Sahel,
  Southern African summer rains) or a different positioning. We
  consider this constraint a feature: the library knows what it is.

## Alternatives considered

**A. Use `xclim`'s string-based season codes (`"QS-MAR"`, `"QS-OCT"`).**
Rejected because:
- They encode seasons as Gregorian-quarter shifts, which is a
  weaker concept than a named, region-specific season.
- They don't carry the sub-regional applicability metadata that
  matters for East Africa.
- They don't support onset-anchored definitions.

**B. Use a config file for seasonal definitions, no Season type.**
Rejected because:
- A first-class type makes seasonal semantics visible in the API
  signatures, which catches errors at call time rather than at
  runtime.
- A type can carry provenance metadata into outputs in a way that
  a config dict cannot cleanly.

**C. Make seasons fully user-defined; ship no defaults.**
Rejected because:
- Shipping no defaults means every user has to know the
  operational seasonal definitions before using the library at all.
  That's a barrier that defeats the project's purpose.
- The defaults are not contentious — they're the published KMD/ICPAC
  windows. Shipping them and citing them is the right move.

## References

- Camberlin, P., & Okoola, R. E. (2003). The onset and cessation of
  the "long rains" in eastern Africa and their interannual
  variability. *Theoretical and Applied Climatology*, 75(1), 43–54.
- Kenya Meteorological Department. *Seasonal climate outlook
  bulletins.* https://meteo.go.ke/
- ICPAC (IGAD Climate Prediction and Applications Centre). *Greater
  Horn of Africa Climate Outlook Forum (GHACOF) consensus statements.*
  https://www.icpac.net/
- Funk, C., et al. (2015). The climate hazards infrared precipitation
  with stations — a new environmental record for monitoring extremes.
  *Scientific Data*, 2, 150066. [CHIRPS technical reference.]
