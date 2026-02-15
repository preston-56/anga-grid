# Roadmap

What's planned but not yet shipped, in rough priority order.

## v0.6 — Network fetch and caching

The provider `fetch()` methods currently require `source_override`
pointing at a local replica. v0.6 will add real network fetch with
local caching:

- HTTP downloads to the configured `cache_dir`
- Etag/Last-Modified-based revalidation so re-runs don't re-download
- Concurrent requests with backoff
- Per-provider retry policies that match the operational SLAs of
  CHIRPS, AgERA5, TAMSAT, NEX-GDDP

Will be opt-in via a `--allow-network` CLI flag; default stays
local-only so an air-gapped pipeline never starts a download by
surprise.

## v0.6 — Onset detection v2

The current `detect_onset` uses the operational Camberlin-Okoola
definition with fixed thresholds. v0.6 will add:

- Sub-regional threshold tuning (the highland 25mm/4d variant some
  Kenyan extension services use)
- Optional season-anchored false-onset detection (the "early rain
  but no follow-through" pattern)
- Stricter validation of the wet-window/follow-up parameters against
  the input frequency

## v0.7 — More indicators

- WSPI (weighted SPI) for crop-stage-aware drought scoring
- SPEI (standardised precipitation-evapotranspiration index)
- Heat-stress index (combined hot-day + low-humidity counter)
- Anomaly maps (deviation from baseline mean as fraction of std)

## v0.7 — Shapefile rollups

The `polygon_roll_up` path takes user-constructed `PolygonRegion`
objects. v0.7 will add a thin geopandas-aware reader that ingests
ESRI shapefiles and produces a list of PolygonRegions, with a
sensible mapping from the shapefile's name attribute. Geopandas
will be an optional extra (`uv add 'anga-grid[shapefile]'`).

## v0.8 — Performance pass

- Dask-backed evaluation throughout, gated by an opt-in flag (most
  bulletin runs are small enough that the dask overhead doesn't pay)
- Vectorised indicator implementations where the current per-cell
  apply_ufunc loop is the bottleneck
- Optional zarr append mode for incremental daily ingest

## v0.9 — Documentation site

A real Sphinx or mkdocs site rather than the current Markdown-in-doc/
arrangement. Will fold in the worked examples, ADR navigation, and
indicator reference pages with formula listings.

## v1.0 — Stability commitment

Once the v0.6-v0.9 work lands and beds in for ~6 months across at
least one real operational pipeline, the public API will go to
1.0 with a stability commitment.

## Out of scope

- Forecasts. anga-grid computes indicators from observational
  reanalysis and projection data; it doesn't run weather models or
  issue forecasts beyond what the source datasets provide. We will
  not add a numerical weather prediction module.
- Generalisation outside East Africa. The seasonal logic, bias
  caveats, and default thresholds are East African and will not be
  generalised at the cost of correctness here.
- Replacement of xarray or xclim. anga-grid uses both as
  dependencies; the value-add is the East African specialisation,
  not the underlying numerics.
