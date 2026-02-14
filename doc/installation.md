# Installation and project setup

## Installing anga-grid as a user

The recommended path is `uv`, which manages an isolated environment
and the Python version automatically:

```bash
uv tool install anga-grid
```

After this, `anga --help` works directly from your shell. To upgrade,
`uv tool upgrade anga-grid`.

If you're depending on anga-grid from another Python project:

```bash
uv add anga-grid           # uv-managed projects
pip install anga-grid      # inside a venv on systems without uv
```

On PEP 668 systems (Debian/Ubuntu 24.04+, recent Fedora), `pip install`
outside a virtual environment will refuse with an
`externally-managed-environment` error. Either use `uv tool install`,
or create a venv first.

## Setting up for development

```bash
git clone https://github.com/preston-56/anga-grid
cd anga-grid

uv python install 3.12
uv sync --extra dev
```

`uv sync` installs the runtime dependencies (xarray, xclim, pint, zarr,
numpy, pandas, netCDF4, click, pydantic) plus the dev tooling
(pytest, hypothesis, mypy, ruff).

To run the full local check that CI runs:

```bash
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest --cov=anga_grid --cov-report=term-missing --cov-fail-under=80
```

To run just one test layer:

```bash
uv run pytest -m smoke              # fast import/wiring sanity
uv run pytest -m regression         # pinned past-bug behaviours
uv run pytest -m performance        # bounded-time benchmarks
uv run pytest -m roundtrip          # write-then-read symmetry
```

## Local data setup

v0.5 requires a local replica of any dataset you want to use; the
network fetch path is roadmap. The expected file layouts:

- **CHIRPS-2.0**: a single NetCDF or Zarr with `lat`, `lon`, `time`
  coords and a `precip` variable in mm/day. Alternative variable names
  (`precipitation`, `rainfall`) are auto-canonicalised.
- **AgERA5**: a single NetCDF/Zarr or a directory of per-variable
  NetCDFs. The provider canonicalises the Capital_Case names
  Copernicus distributes (`Temperature_Air_Mean_Daily` ->
  `temperature_air_mean_daily`).
- **TAMSAT**: a single NetCDF/Zarr with `rfe`, `rfe_filled`,
  `rainfall`, or `precip` as the rainfall variable.
- **NEX-GDDP-CMIP6**: a single NetCDF/Zarr with CMIP6 variable names
  (`tas`, `tasmin`, `tasmax`, `pr`). Units in Kelvin / kg m^-2 s^-1
  are auto-converted to Celsius / mm/day.

If you don't have the real datasets handy, the synthetic builders in
`anga_grid.synthetic.*` produce shape-compatible NetCDFs sufficient
for development and the example scripts:

```python
from anga_grid.synthetic import synthetic_chirps_multiyear
ds = synthetic_chirps_multiyear(years=(1991, 2000))
ds.to_netcdf("/tmp/synthetic-chirps.nc")
```
