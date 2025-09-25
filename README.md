# anga-grid

Gridded climate indicators for East African agriculture — anchored in
Njoro and Molo (Nakuru County, Kenya), built for agronomy researchers
and operational drought-monitoring services.

> *anga* (Swahili) — sky, atmosphere.

---

## What this is

anga-grid takes raw gridded climate data — CHIRPS rainfall, AgERA5
reanalysis, TAMSAT African rainfall estimates, NEX-GDDP downscaled
climate projections — and produces the indicators that East African
agronomists and drought-monitoring agencies actually use, with the
seasonal calendars, topographic corrections, and provenance metadata
that operational work requires.

Most general-purpose climate libraries (`xclim`, `xarray`-based
toolkits) treat every region of the world the same way. They aggregate
to calendar quarters, apply uniform bias models, and compute
indicator windows centered on dates that don't match how rain actually
falls in East Africa. That's fine for global comparative work and not
fine for telling a farmer in Njoro whether the long rains are likely
to start in the third week of March or the first week of April.

anga-grid encodes the things you have to know to do this work
correctly in East Africa, and surfaces them as defaults rather than
buried configuration:

- **Bimodal seasonal calendars.** Long rains (*masika*, March–May) and
  short rains (*vuli*, October–December) are first-class concepts.
  Sub-regional variations — the unimodal pattern north of ~3° N, the
  delayed onset over the Rift Valley highlands — are configurable
  rather than averaged away.
- **Onset and cessation detection.** Not "rainfall in MAM" but "when
  did the rains actually start this season?" The library implements
  the operational onset definitions used in East African agromet —
  20mm in 3 days followed by no 10-day dry spell in the next 30 — and
  exposes them as composable rules.
- **Topographic awareness.** CHIRPS is known to underestimate rainfall
  over complex terrain like the Mau Escarpment and the slopes around
  Mt. Kenya. anga-grid surfaces these biases in metadata rather than
  silently passing them through, and offers documented correction
  options.
- **Agronomic indicators, not just meteorological ones.** Critical
  flowering-period dryness for maize, water-requirement satisfaction
  index, dry-spell frequency during land preparation windows — the
  indicators agronomists ask for, computed correctly for the cropping
  calendar.
- **NDMA-compatible outputs.** Drought severity categories match the
  Kenya Meteorological Department / National Drought Management
  Authority operational thresholds. County and ward-level rollups use
  the current administrative boundaries.
- **Provenance you can audit.** Every output carries a manifest:
  source dataset and version, spatial subset, temporal window,
  calendar definition, correction method, code version. The work is
  reproducible and the lineage is legible.

## What this is not

- **Not a replacement for `xarray` or `xclim`.** anga-grid uses
  `xarray` as its core data model and depends on it heavily. Where
  `xclim` already has a correct, well-tested implementation of a
  generic indicator, anga-grid calls into it rather than reinventing.
  The value-add is the East African specialization, not the
  underlying numerics.
- **Not a forecasting system.** anga-grid computes indicators from
  observational reanalysis and projection data. It doesn't run
  weather models, doesn't issue forecasts, and doesn't claim
  predictive skill beyond what the source datasets provide.
- **Not a global library.** It's anchored on East Africa. Some
  functions will work elsewhere (the dataset readers, the basic
  aggregations); the seasonal logic, the bias corrections, and the
  default geographic configuration are East African and we will not
  generalize them at the cost of correctness here.
- **Not a research framework.** Climate scientists building novel
  analyses should probably use `xarray` + `xclim` directly. anga-grid
  is opinionated toward operational reliability and reproducibility,
  not flexibility.

## Why it exists

I grew up in Njoro. The decisions that matter to farmers and to the
drought-response agencies that support them — when to plant, when to
trigger anticipatory action, how to allocate resources between
counties — are made against climate data products that were designed
for a global audience and then adapted, often badly, to local
realities.

The pattern I keep seeing: someone copies a generic SPI computation,
runs it against CHIRPS for Kenya, doesn't notice that the season
boundaries are wrong, and produces a "drought index" that says nothing
useful about the actual cropping season. The bug isn't in the SPI
math; it's in everything around it — the calendar, the spatial
subset, the source-data caveats nobody flagged.

anga-grid exists so that the work of doing this right, once, can be
shared across the agronomists and operational services that need it.

## Status

**v0.1 — under active development.** Current scope: CHIRPS daily
rainfall, monthly and seasonal aggregation, SPI computation, onset
detection. AgERA5 and TAMSAT integration, NEX-GDDP projection
handling, and county-level rollups are on the roadmap; see
[doc/roadmap.md](doc/roadmap.md).

## Quick look

```bash
# Install
pip install anga-grid

# Fetch CHIRPS rainfall for Nakuru County, 1991–2024
anga fetch chirps \
  --region nakuru \
  --start 1991-01-01 \
  --end 2024-12-31 \
  --output ./data/chirps-nakuru.zarr

# Compute SPI-3 for the long rains seasons, using climatological
# baseline 1991–2020
anga compute spi \
  --input ./data/chirps-nakuru.zarr \
  --window 3 \
  --season long-rains \
  --baseline 1991-2020 \
  --output ./out/spi3-longrains-nakuru.nc

# Detect onset of long rains for the 2024 season
anga compute onset \
  --input ./data/chirps-nakuru.zarr \
  --season long-rains-2024 \
  --output ./out/onset-2024.nc
```

See [examples/](examples/) for worked end-to-end analyses.

## Documentation

- [Architecture overview](doc/architecture.md) — design decisions and
  trade-offs
- [Architecture decision records](doc/adr/) — why specific choices
  were made
- [Datasets](doc/datasets.md) — what each source provides, conventions,
  known caveats
- [Operations](doc/operations.md) — deployment, configuration,
  observability
- [Seasonal calendars](doc/calendars.md) — how anga-grid models East
  African rainfall seasons and why

## Contributing

Issues and pull requests welcome, especially from agronomists,
extension officers, and operational meteorologists who can tell us
where the defaults are wrong. Code-only contributions are also
welcome.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgements

CHIRPS data is produced by the Climate Hazards Center at UC Santa
Barbara (Funk et al. 2015). AgERA5 is produced by ECMWF for the
Copernicus Climate Change Service. TAMSAT is produced by the
University of Reading. NEX-GDDP-CMIP6 is produced by NASA Earth
Exchange. anga-grid stands on the shoulders of `xarray`, `xclim`,
`pint`, `zarr`, and the broader Pangeo community.
