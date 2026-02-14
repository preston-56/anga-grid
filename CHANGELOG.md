# Changelog

All notable changes to this project go here. Format follows Keep a
Changelog; this project does not yet ship pinned releases - everything
below is on `main`.

## Unreleased — v0.5 work in progress

### Added

- `temperature_extremes` indicator: hot_days, cold_days, frost_days,
  tropical_nights with WMO-ETCCDI default thresholds.
- `severity.quintile` module: tercile and quintile classification with
  optional baseline-period reference.
- `severity.summary` module: per-band fraction breakdown of a
  classified output.
- Per-region cropping calendars: Embu, Kisumu, Mombasa, Garissa.
- CLI: `anga trend` and `anga quintile` subcommands.
- README badges: CI, Python, license, ruff, coverage, region.
- CONTRIBUTING.md, CHANGELOG.md, doc/installation.md.

### Changed

- README install instructions now use `uv tool install` as the
  primary path; the previous `pip install` line broke on PEP 668
  systems.
- README Quick Look fetch example flags `--source-override` since
  network fetch is still roadmap in v0.5.
- `severity.quintile` now drops the stray `quantile` coord that
  `xr.quantile` adds, fixing apply_ufunc dimension errors on
  spatial inputs.

## v0.4 (2026-01)

- NEX-GDDP-CMIP6 provider with five-scenario catalog and unit conversion.
- Polygon-based rollups via vectorised ray-casting (no shapely dep).
- `cropping/` module: phenological windows + Nakuru calendars.
- `anga_grid.synthetic` public package; runnable examples/.
- Top-level files reshaped into themed sub-packages: types, exceptions,
  logging, aggregation, correction, severity, storage, provenance,
  season.

## v0.3 (2025-12)

- TAMSAT-3.1 provider as the third precipitation reader.
- Provider sub-package refactor: chirps/, agera5/ split into
  provider/schema/manifest/variables modules.
- Indicator sub-package refactor: spi/, onset/, dry_spell/, gdd/.
- Reference ET (FAO-56 Penman-Monteith).
- WRSI for maize, sorghum, beans.
- Four new test layers: smoke, regression, performance, roundtrip.

## v0.2 (2025-11)

- Provenance Manifest as a first-class concept.
- Storage helpers (zarr/netcdf write/read with manifest preservation).
- AgERA5 provider for ECMWF/Copernicus reanalysis.
- Dry-spell count and growing degree days indicators.
- Bias correction: linear scaling, delta change, monthly linear scaling.
- County/ward rollups with the Nakuru ward catalog.
- KMD severity bands and NDMA drought phase classification.
- CLI: `anga rollup` and `anga classify` subcommands.

## v0.1 (2025-09 → 2025-10)

- Initial release: CHIRPS provider, Season type with KMD/ICPAC catalog,
  SPI and onset indicators, basic CLI, behavioural test suite, CI.
