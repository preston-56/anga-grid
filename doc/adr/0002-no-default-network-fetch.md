# ADR 0002: No default network fetch in providers

**Status:** Accepted
**Date:** 2026-02-16

## Context

Each provider in `anga_grid.providers.*` has a `fetch(bbox, time_range)`
method that returns an `xarray.Dataset`. The natural temptation is to
wire that method to download the requested subset from the upstream
distributor (UCSB for CHIRPS, Copernicus for AgERA5, Reading for TAMSAT,
NASA for NEX-GDDP) the first time it's called, with a local cache to
avoid re-downloading.

We've explicitly *not* done this through v0.5. Every provider raises
`ProviderError` if `source_override` isn't set, which forces every
caller to point at a local replica.

## Decision

The default behaviour stays "no network." Network fetch will land in
v0.6 behind an explicit `--allow-network` CLI flag (and a
`ProviderConfig(allow_network=True)` constructor knob).

The default-deny posture serves three operational properties:

1. **Air-gapped pipelines.** Several of the most likely downstream
   users (KMD, county-level early-warning teams) run on networks
   without general internet egress. A library that defaults to
   network access is a library that can't be deployed without a
   special exception.
2. **Reproducible bulletin runs.** Drought bulletins go through
   review cycles that may rerun the same analysis weeks later. If
   the provider silently re-downloads from the upstream and the
   upstream has issued a corrective republication in the interim,
   the rerun produces different numbers without anyone noticing.
   A local-replica posture makes the input data version explicit.
3. **Cost predictability.** AgERA5 and NEX-GDDP downloads from
   Copernicus and NASA are not free at scale, and an accidental
   `fetch` over a wide bbox over a long time range can be a
   meaningful surprise.

## Consequences

**Positive:**

- Operational pipelines built on anga-grid have a clear input-data
  manifest because the file path is part of every invocation.
- Test isolation is trivial: tests use synthetic NetCDFs via
  `anga_grid.synthetic.*` and never need a network mock.
- The same `fetch()` code path runs in development, in CI, and in
  production: there's no "oh this only works because the cache is
  warm" failure mode.

**Negative:**

- New users have a higher first-run cost: they need to obtain a
  CHIRPS NetCDF before they can do anything useful. The README
  Quick Look has been adjusted to make this explicit.
- The roadmap network-fetch implementation will need careful
  cache-validation logic to not re-introduce the silent-re-download
  problem.

## Alternatives considered

**A. Default to network fetch with a `cache_dir` and a
fallback-to-cache.** Rejected because the silent-stale-cache
failure mode is worse than the explicit-no-data failure mode the
current design produces. A pipeline that produces wrong numbers
because the upstream republished is harder to catch than one that
errors out.

**B. Provide network fetch behind an env var.** Rejected because env
vars are an out-of-band configuration channel; an operator can set
`ANGA_ALLOW_NETWORK=1` once and then forget about it for months. A
CLI flag that has to appear on every invocation is harder to lose
track of.
