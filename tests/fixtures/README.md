# Committed test fixtures

Twelve small NetCDFs covering the four provider shapes plus regional
variety, multi-year baselines, and the three SSP scenarios most-used
in operational outlook work. All twelve are generated from
`anga_grid.synthetic.*` with fixed seeds (1991 for observational,
2030 for projection), so every byte is reproducible.

| File | Source builder | Period / scope | Size |
|---|---|---|---|
| `chirps_njoro_1991.nc` | `synthetic_chirps` | 1991 daily, Njoro | 73 KB |
| `chirps_njoro_1991_1995.nc` | `synthetic_chirps_multiyear` | 1991-1995, Njoro | 331 KB |
| `chirps_njoro_1991_2020.nc` | `synthetic_chirps_multiyear` | 1991-2020 WMO baseline, Njoro | 1.85 MB |
| `chirps_kisumu_1991.nc` | `synthetic_chirps` | 1991 daily, Kisumu (Lake Victoria) | 185 KB |
| `chirps_mombasa_1991.nc` | `synthetic_chirps` | 1991 daily, Mombasa coastal | 154 KB |
| `agera5_njoro_1991_long_rains.nc` | `synthetic_agera5` | 1991 Mar-Aug, Njoro | 87 KB |
| `agera5_njoro_1991_full_year.nc` | `synthetic_agera5` | 1991 full year, Njoro | 156 KB |
| `tamsat_njoro_1991.nc` | `synthetic_tamsat` | 1991 daily, Njoro | 115 KB |
| `tamsat_njoro_1991_1995.nc` | `synthetic_tamsat` | 1991-1995, Njoro | 537 KB |
| `nex_gddp_njoro_ssp126_2030.nc` | `synthetic_nex_gddp` | 2030, SSP1-2.6 | 37 KB |
| `nex_gddp_njoro_ssp245_2030.nc` | `synthetic_nex_gddp` | 2030, SSP2-4.5 | 37 KB |
| `nex_gddp_njoro_ssp585_2030.nc` | `synthetic_nex_gddp` | 2030, SSP5-8.5 | 37 KB |

Total: ~3.55 MB (capped at 4 MB by an integration-test guard).

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
