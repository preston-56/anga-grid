# Troubleshooting

The most common operational failure modes and what to do about them.

## ProviderError: not wired in vX.Y

```
anga_grid.exceptions.ProviderError: CHIRPS network fetch is not wired
in v0.1; pass source_override with a path to a local NetCDF or Zarr
replica
```

Network fetch is roadmap (see ADR 0002). Pass `--source-override
/path/to/local.nc` (CLI) or `source_override=Path("/path/to/local.nc")`
(Python).

## ProviderError: subset is empty along time

The bbox+time-range you asked for has no overlap with the local
replica. Common causes:

1. The replica covers a year range that doesn't include your
   requested window.
2. The replica's `time` coordinate is in CF-encoded `days since
   ...` form and didn't decode (rare; check `xr.open_dataset(path,
   decode_times=True)`).
3. The CLI date format is wrong — must be `YYYY-MM-DD`.

## ProviderError: none of {...} found in dataset

The local replica's rainfall variable doesn't match the names the
provider's canonicalisation handles. CHIRPS handles `precip`,
`precipitation`, `rainfall`. If your replica uses something else,
rename the variable before passing it in:

```python
ds = xr.open_dataset(path).rename({"my_var": "precip"})
ds.to_netcdf(canonical_path)
```

## ImportError on xclim function

xclim renames its internals between versions. SPI in particular has
moved between `xclim.indices.standardized_precipitation_index` and
similar paths. The provider tries the canonical path and falls back
to a numpy-only standardisation if the import fails. If you see SPI
output that looks like a plain z-score rather than a gamma-fit
distribution, you're on the fallback — pin a known-good xclim
version (>=0.49 ships the canonical name).

## AlignmentError on multi-dataset workflows

CHIRPS is 0.05°, AgERA5 is 0.1°, TAMSAT is 0.0375°, NEX-GDDP is
0.25°. They don't align by default. Use xarray's
`interp_like(target)` or `regrid` (via xesmf if you've got it
available) to reproject one to the other before combining. The WRSI
example regrids by constructing both inputs at matching resolution
via `synthetic_*(resolution=0.1)`.

## Manifest history loses an operation

`Manifest.from_attrs` requires the input `xarray` object to carry
the `source` attr. When you do `ds["precip"]`, the resulting
DataArray inherits its variable-level attrs but not the
Dataset-level attrs unless the provider mirrored them
(CHIRPS/AgERA5/TAMSAT/NEX-GDDP all do, but a custom provider might
not). If your downstream indicator output is missing history,
check that the input DataArray has `source` in its attrs.

## CI lint failure on a clean local check

CI runs ruff against pinned versions; if your local ruff is newer
it might silently fix something CI's older version flags. Run
`uv pip install --upgrade-package ruff` and the local check should
match.





