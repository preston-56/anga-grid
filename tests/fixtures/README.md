# Committed test fixtures

Five small NetCDFs covering the four provider shapes plus a multi-year
CHIRPS for trend / SPI scenarios. All five are generated from
`anga_grid.synthetic.*` with seed=1991 (or 2030 for the projection
sample) and a Njoro-sized bounding box, so every byte is reproducible.

| File | Source builder | Period | Size |
|---|---|---|---|
| `chirps_njoro_1991.nc` | `synthetic_chirps` | 1991 daily | 72 KB |
| `chirps_njoro_1991_1995.nc` | `synthetic_chirps_multiyear` | 1991-1995 daily | 323 KB |
| `agera5_njoro_1991_long_rains.nc` | `synthetic_agera5` | 1991 Mar-Aug daily | 87 KB |
| `tamsat_njoro_1991.nc` | `synthetic_tamsat` | 1991 daily | 115 KB |
| `nex_gddp_njoro_ssp245_2030.nc` | `synthetic_nex_gddp` | 2030 Jan-Jun daily | 23 KB |

## Why commit them

The `anga_grid.synthetic` builders are the canonical way to make
test inputs, but a committed fixture set helps in three places where
on-the-fly generation is the wrong tool:

1. **Examples scripts** that should run with zero compute setup -
   the example points at the fixture path and prints results.
2. **CI** for the example-script smoke test, where re-generating
   the data on every run wastes a few seconds per fixture.
3. **External users running the README quick-look** without
   pulling real CHIRPS first; the fixtures give them a working
   `--source-override` target.

## Regenerating

```bash
uv run python tests/fixtures/regenerate.py
```

Output is byte-identical given the seed; if `git status` shows the
fixtures changing after a re-run, the synthetic builders have
drifted and tests/integration/test_synthetic_data_consistency.py
should have caught it.

## Why these are committed and `*.nc` is otherwise gitignored

The repo's `.gitignore` excludes `*.nc` so casual `data/` and `out/`
runs don't get accidentally committed. The `!tests/fixtures/**/*.nc`
override carves out exactly this directory.
