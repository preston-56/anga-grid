# Seasonal calendars

This document is the operational reference for the seasonal definitions
anga-grid ships as defaults. The reasoning behind treating seasons as
first-class types — rather than as Gregorian-quarter shifts or as a
config dict — lives in `adr/0001-seasonal-calendars.md`.

## The bimodal regime (Kenya, eastern Uganda, northern Tanzania)

East Africa's rainfall is dominated by the migration of the
Inter-Tropical Convergence Zone, which crosses the equator twice per
year. The result is two rainy seasons separated by two dry seasons.

- **Long rains (*masika*, *gu* in northern Somali areas)** —
  approximately March through May. The wetter of the two seasons in
  most of Kenya and Tanzania. Maize, beans, and many horticultural
  crops depend on it. KMD's operational definition covers MAM (March,
  April, May); ICPAC's GHACOF outlooks use the same window for the
  bimodal subset of their domain.
- **Short rains (*vuli*, *deyr*)** — approximately October through
  December. Often more variable interannually than the long rains.
  Some sub-regions (coastal Kenya, southeastern Kenya) get a larger
  share of annual rainfall from the short rains than from the long.
  KMD operational definition: OND.

## Sub-regional variation

The bimodal definitions above are accurate over most of central and
southern Kenya. anga-grid recognizes three documented departures from
this baseline:

1. **Unimodal regime north of ~3° N.** Parts of northern Kenya, the
   Karamoja cluster, and southern Ethiopia have a single rainy season
   (long rains only, often extending through August in places). The
   `Season.applies_to(lat, lon)` mechanism gates the bimodal defaults
   so they aren't applied where they're wrong.
2. **Coastal long rains.** From the Kenya coast through northeastern
   Tanzania, the long rains can extend through July. The default
   coastal season is MAMJ rather than MAM; users analyzing
   specifically the Kenya coast should use the `coastal-long-rains`
   season key.
3. **Highland delayed onset.** Over the Rift Valley highlands
   (Nakuru, Bomet, Nandi), long-rains onset is typically 1–3 weeks
   later than over the lowlands at the same latitude. The default
   `Season` definitions use the lowland onset window; onset-anchored
   analyses (the `onset.detect` indicator) reflect the actual highland
   timing by construction.

## Citations and authoritative sources

- Camberlin, P., & Okoola, R. E. (2003). The onset and cessation of
  the "long rains" in eastern Africa and their interannual
  variability. *Theoretical and Applied Climatology*, 75(1), 43–54.
- Kenya Meteorological Department, seasonal climate outlook bulletins.
  https://meteo.go.ke/
- ICPAC (IGAD Climate Prediction and Applications Centre), GHACOF
  consensus statements. https://www.icpac.net/
- Liebmann, B., et al. (2012). Seasonality of African precipitation
  from 1996 to 2009. *Journal of Climate*, 25(12), 4304–4322.
  *(Used for the unimodal/bimodal boundary north of ~3° N.)*

When KMD or ICPAC update their operational definitions, the catalog
in `src/anga_grid/season.py` is updated in lockstep and the change is
documented in this file under a "Revisions" section. The change is also
noted in the relevant ADR.
