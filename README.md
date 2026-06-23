# anga-grid

[![PyPI](https://img.shields.io/pypi/v/anga-grid.svg)](https://pypi.org/project/anga-grid/)
[![Python](https://img.shields.io/pypi/pyversions/anga-grid.svg)](https://pypi.org/project/anga-grid/)
[![License](https://img.shields.io/pypi/l/anga-grid.svg)](https://github.com/preston-56/anga-grid/blob/main/LICENSE)
[![CI](https://github.com/preston-56/anga-grid/actions/workflows/ci.yml/badge.svg)](https://github.com/preston-56/anga-grid/actions/workflows/ci.yml)

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

**v0.5 — under active development.** Current operational surface:

- **Providers** (four datasets): CHIRPS-2.0 daily rainfall, AgERA5
  daily reanalysis (eight variables), TAMSAT-3.1 African rainfall,
  NEX-GDDP-CMIP6 downscaled projections (five SSP scenarios).
- **Indicators**: SPI (gamma + fallback standardisation), operational
  onset, dry-spell counts, growing degree days (maize/sorghum/wheat),
  reference ET (FAO-56 Penman-Monteith), WRSI for maize/sorghum/beans,
  annual/seasonal trend, hot/cold/frost/tropical-night counts.
- **Classifications**: KMD seven-band SPI severity, NDMA four-phase
  drought categorisation, FEWS-NET tercile and quintile maps.
- **Spatial aggregation**: bbox-based and polygon-based rollups; ships
  with the Nakuru ward and county catalog plus cropping calendars for
  Nakuru, Embu, Kisumu, Mombasa, and Garissa.
- **Bias correction**: linear scaling, delta change, monthly linear
  scaling.
- **Storage**: zarr / NetCDF read/write with manifest preservation.

## Quick look

### Install

```bash
# Two install modes; pick the one that matches your situation.

# (a) As a system tool, on PATH everywhere:
uv tool install anga-grid

# (b) Inside a uv-managed project:
uv add anga-grid

# (c) Inside a plain venv (PEP 668 systems will reject pip outside a venv):
pip install anga-grid
```

### Run

The commands below work on a fresh clone — they point at the
committed synthetic fixtures under `tests/fixtures/data/`. Substitute
your real CHIRPS / AgERA5 path when you have one.

If you installed via mode (b) or are running from a checkout, prefix
each command with `uv run` (or `source .venv/bin/activate` once and
drop the prefix). Mode (a) puts `anga` on PATH directly.

```bash
mkdir -p out

# Fetch a CHIRPS subset over Njoro from the committed fixture.
# In v0.6 --source-override goes away in favour of network fetch.
uv run anga fetch chirps \
  --region njoro \
  --start 1991-01-01 \
  --end 1995-12-31 \
  --source-override tests/fixtures/data/chirps_njoro_1991_1995.nc \
  --output out/chirps-njoro.nc

# Compute SPI-3 for the long rains, against the in-window baseline.
uv run anga compute spi \
  --input out/chirps-njoro.nc \
  --window 3 \
  --season long-rains \
  --baseline 1991-1995 \
  --output out/spi3-longrains-njoro.nc

# Detect long-rains onset for each year in the input.
uv run anga compute onset \
  --input out/chirps-njoro.nc \
  --season long-rains \
  --output out/onset-longrains.nc

# Roll up SPI to county-level (the Njoro fixture sits inside the
# Nakuru county bbox; for ward-level rollups use a wider input).
uv run anga rollup \
  --input out/spi3-longrains-njoro.nc \
  --scope nakuru-county \
  --reducer mean \
  --output out/spi3-county.nc

# Classify SPI into the KMD seven-band severity, print a summary.
uv run anga classify \
  --input out/spi3-longrains-njoro.nc \
  --scheme kmd \
  --summary \
  --output out/severity.nc

# Compute a long-term seasonal trend.
uv run anga trend \
  --input out/chirps-njoro.nc \
  --season long-rains \
  --reducer sum \
  --output out/trend.nc

# Tercile classification with an explicit baseline window.
uv run anga quintile \
  --input out/spi3-longrains-njoro.nc \
  --scheme tercile \
  --baseline 1991-1995 \
  --output out/tercile.nc
```

See [examples](https://github.com/preston-56/anga-grid/tree/main/examples) for worked end-to-end analyses, including
a full WRSI(maize) computation against CHIRPS + AgERA5 reference ET,
and the trend + tercile chain over a synthetic decade.

## Documentation

Start at [Documentation](https://github.com/preston-56/anga-grid/tree/main/doc)

- [Installation](https://github.com/preston-56/anga-grid/blob/main/doc/installation.md)
- [CLI reference](https://github.com/preston-56/anga-grid/blob/main/doc/cli.md)
- [Data sources](https://github.com/preston-56/anga-grid/blob/main/doc/data-sources.md)
- [Operations](https://github.com/preston-56/anga-grid/blob/main/doc/operations.md)
- [Troubleshooting](https://github.com/preston-56/anga-grid/blob/main/doc/troubleshooting.md)
- [Architecture overview](https://github.com/preston-56/anga-grid/blob/main/doc/architecture.md)
- [Decision records](https://github.com/preston-56/anga-grid/tree/main/doc/adr)

## Contributing

Issues and pull requests welcome, especially from agronomists,
extension officers, and operational meteorologists who can tell us
where the defaults are wrong. Code-only contributions are also
welcome.

See [CONTRIBUTING.md](https://github.com/preston-56/anga-grid/blob/main/CONTRIBUTING.md) for the local check loop and
[doc/contributing-calendars.md](https://github.com/preston-56/anga-grid/blob/main/doc/contributing-calendars.md)

## License

MIT. See [LICENSE](https://github.com/preston-56/anga-grid/blob/main/LICENSE).

## Acknowledgements

CHIRPS data is produced by the Climate Hazards Center at UC Santa
Barbara (Funk et al. 2015). AgERA5 is produced by ECMWF for the
Copernicus Climate Change Service. TAMSAT is produced by the
University of Reading. NEX-GDDP-CMIP6 is produced by NASA Earth
Exchange. anga-grid stands on the shoulders of `xarray`, `xclim`,
`pint`, `zarr`, and the broader Pangeo community.
