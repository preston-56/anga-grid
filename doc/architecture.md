# Architecture

anga-grid is organized as a thin set of layers over `xarray` and
`xclim`. Each layer has a small, type-checked interface; the East
African specialization lives at the *seam* between layers, not inside
the numerics.

## Layers

- **`providers/`** — dataset readers. One module per source (CHIRPS,
  AgERA5, TAMSAT, NEX-GDDP). Each provider returns a canonicalized
  `xarray.Dataset` with CF-compliant coordinates and a `provenance`
  attribute block (source, version, retrieval timestamp, spatial subset,
  temporal window).
- **`season`** — the `Season` type. The single concept that distinguishes
  this library from a generic xclim wrapper. See ADR 0001.
- **`aggregation`** — temporal reductions over `Season` windows (sum,
  mean, max, custom callable). Operates on standard xarray dimensions.
- **`indicators/`** — wrappers over `xclim.indices` for generic
  computations (SPI), plus first-party implementations for indicators
  xclim does not have or does not have correctly for East Africa
  (operational onset detection, dry-spell frequency, WRSI roadmap).
- **`cli/`** — `click`-based command surface that composes the layers
  for common operational workflows.

## Relationship to xarray and xclim

`xarray.Dataset` is the only data model — nothing inside the library
holds rainfall in plain numpy arrays once it's been read. Where `xclim`
already has a correct, well-tested implementation of a generic
indicator, anga-grid calls into it; we add the seasonal windowing, the
provenance metadata, and the East African defaults around the call.

## Provenance

Every operation that produces a derived array (aggregation, indicator,
regrid) appends to the `provenance` attribute block on the output. By
the time a result reaches disk, the manifest contains enough metadata
to reconstruct the analysis: source dataset and version, calendar
definition, baseline period, code version. This is the operational
contract anga-grid exists to provide.
