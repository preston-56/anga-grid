# ADR 0003: Provenance manifest as xarray attrs, not a sidecar file

**Status:** Accepted
**Date:** 2026-02-16

## Context

Every output anga-grid produces needs to carry enough metadata to
reconstruct how it was made: source dataset version, spatial subset,
temporal window, indicator parameters, the chain of transforms, and
the bias caveats inherited from upstream. The drought-bulletin
review process depends on this audit trail.

The two natural places to put it:

1. Inline in the dataset's xarray `attrs` (and propagated to NetCDF
   `Conventions` / Zarr `.zattrs`).
2. As a sidecar file alongside the data (manifest.json next to
   foo.nc).

We chose (1) and packaged it as `anga_grid.provenance.Manifest`.

## Decision

The manifest lives in `xarray.Dataset.attrs` (and, for the variables
the producer cares about, mirrored to `DataArray.attrs`). The
serialisation is flat scalar attrs:

- `source`, `source_version`, `provider`, `subset_bbox`,
  `subset_time`, `retrieved_at`, `code_version` as their own attrs
- `caveats` joined with `; `
- `history` as pipe-separated `timestamp|operation|key=value;...`
  entries

`Manifest.from_attrs(dict(ds.attrs))` reconstitutes the structured
form.

## Consequences

**Positive:**

- The manifest survives every NetCDF and Zarr write/read cycle the
  user might do without thinking about it. No "oh I forgot to copy
  the .json" failure mode.
- Standard xarray tooling (`ncdump`, `xr.open_dataset(...).attrs`)
  shows the full provenance immediately.
- Conformant with CF-conventions — the `history` attribute is a
  CF-recognised concept and our format is an extension that adds
  structured parameter capture.

**Negative:**

- Caveats can't contain `; ` since that's the join separator;
  validated in tests but documented as a contract limitation.
- History strings on a long indicator chain can grow into the kilobyte
  range. Acceptable for the drought-bulletin scale; would matter for
  millions-of-cells live processing where it doesn't.
- The Step parameter encoding (`key=value;key2=value2`) doesn't
  support nested structures. Deliberate — anything more elaborate
  belongs in a separate manifest file.

## Alternatives considered

**A. JSON sidecar file (manifest.json).** Rejected because the most
common operational read path (open NetCDF, look at attrs) wouldn't
see it, and the failure mode of "forgot to ship the sidecar" is
silent.

**B. PROV-O / W3C PROV format embedded in attrs.** Considered briefly
and rejected. PROV-O is the standards-grade option but its overhead
(graph nesting, IRI references) is wildly out of proportion to
what an operational drought bulletin needs. We can revisit if a
downstream consumer materialises that needs PROV-O.

**C. xclim's existing `xclim.core.options` history mechanism.**
Rejected because it captures only the xclim-internal call chain,
not the upstream provider provenance or our regional context.
