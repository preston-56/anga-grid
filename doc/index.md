# Documentation index

Operational walkthroughs and design references, grouped by audience.

## For users

- [installation.md](installation.md) — how to install (uv recommended).
- [cli.md](cli.md) — per-subcommand CLI reference.
- [data-sources.md](data-sources.md) — where to obtain CHIRPS, AgERA5,
  TAMSAT, NEX-GDDP local replicas.
- [datasets.md](datasets.md) — what each source provides, conventions,
  known caveats.
- [calendars.md](calendars.md) — KMD/ICPAC seasonal definitions,
  sub-regional variations.
- [troubleshooting.md](troubleshooting.md) — failure modes and fixes
  for the operational error paths.
- [glossary.md](glossary.md) — domain term lookup.

## For operators

- [operations.md](operations.md) — suggested deployment shape for
  monthly drought-bulletin pipelines, observability, reproducibility
  contract.

## For contributors

- [../CONTRIBUTING.md](../CONTRIBUTING.md) — what we want, what we
  don't, the local check loop.
- [contributing-calendars.md](contributing-calendars.md) — recipe
  for adding a regional cropping calendar.

## For maintainers / reviewers

- [architecture.md](architecture.md) — layered design overview.
- [adr/](adr/) — architecture decision records.
  - [0001 — Seasonal calendars as first-class concepts](adr/0001-seasonal-calendars.md)
  - [0002 — No default network fetch in providers](adr/0002-no-default-network-fetch.md)
  - [0003 — Provenance manifest as xarray attrs](adr/0003-manifest-as-attrs.md)
  - [0004 — Eight test layers, one pytest marker per layer](adr/0004-test-layer-taxonomy.md)
- [../CHANGELOG.md](../CHANGELOG.md) — what shipped per version.
- [roadmap.md](roadmap.md) — what's planned through v1.0.
