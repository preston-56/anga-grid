# Glossary

Domain terms used across the documentation, grouped by where they
come from.

## Climatological

- **SPI** — Standardised Precipitation Index. McKee 1995. A
  z-score of cumulative rainfall over an N-month window against a
  baseline-period gamma fit. Negative = drier than baseline.
- **SPEI** — Standardised Precipitation-Evapotranspiration Index.
  Vicente-Serrano 2010. Like SPI but using precipitation minus
  reference ET as the input. Roadmap, not in v0.5.
- **WRSI** — Water Requirement Satisfaction Index. The ratio of
  cumulative actual ET to cumulative water requirement (kc * et0)
  over a crop's growing window, expressed as percent. <60% maps to
  crop failure in standard FEWS NET interpretation.
- **GDD** — Growing Degree Days. Cumulative heat above a crop-
  specific base temperature. Used to time phenological stages.
- **ET0 / Reference ET** — Evapotranspiration from a hypothetical
  reference grass surface, computed via FAO-56 Penman-Monteith.

## Operational

- **KMD** — Kenya Meteorological Department. Issues seasonal climate
  outlook bulletins; defines the bimodal long-rains / short-rains
  windows.
- **ICPAC** — IGAD Climate Prediction and Applications Centre. Issues
  the Greater Horn of Africa Climate Outlook Forum (GHACOF) consensus
  statements.
- **NDMA** — National Drought Management Authority (Kenya). Uses the
  four-phase normal/alert/alarm/emergency drought categorisation
  surfaced in `severity.ndma_phase`.
- **FEWS NET** — Famine Early Warning Systems Network. Tercile and
  quintile climate outlook conventions match `severity.tercile_*`.

## Seasonal

- **Long rains / *masika* / *gu*** — March-May (bimodal regime).
- **Short rains / *vuli* / *deyr*** — October-December (bimodal regime).
- **Coastal long rains** — March-June for the Kenyan coast and
  northern Tanzania (extends ~1 month past the inland MAM window).
- **Unimodal regime** — Single rainy season north of ~3°N, typically
  April-August. Modelled as `northern-unimodal` in `season.SEASONS`.
- **Highland delayed onset** — Rift Valley highlands plant ~2 weeks
  later than lowlands at the same latitude. Captured in
  `highland-long-rains`.

## Datasets

- **CHIRPS** — Climate Hazards Center Infrared Precipitation with
  Station data. UCSB. Africa daily, 0.05°, 1981-present.
- **AgERA5** — ECMWF ERA5 reanalysis post-processed for agronomic
  use. Copernicus. 0.1°, daily, 1979-present.
- **TAMSAT** — Tropical Applications of Meteorology using SATellite
  data. University of Reading. Africa-only, 0.0375°, daily,
  1983-present.
- **NEX-GDDP-CMIP6** — NASA Earth Exchange Global Daily Downscaled
  Projections, CMIP6 ensemble. 0.25°, daily, 1950-2100 across five
  SSP scenarios.

## Computational

- **Manifest** — anga-grid's provenance record on every output. Lives
  in `xarray.attrs`. See ADR 0003.
- **Provider** — A dataset reader. Implements the `Provider`
  Protocol (`fetch(bbox, time_range) -> xr.Dataset`).
- **Season** — The first-class window concept the library is built
  around. See ADR 0001.
- **AdminRegion** / **PolygonRegion** — Bounding-box and polygon
  spatial regions for `roll_up` and `polygon_roll_up`.
