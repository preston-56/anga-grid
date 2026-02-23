"""Regenerate the committed test fixtures from the synthetic builders.

Run from the repo root:

    uv run python tests/fixtures/regenerate.py

The output is deterministic given the seed argument on each
synthetic_*() call, so a clean re-run produces byte-identical files.
If the byte-identity claim ever stops holding, the synthetic builders
have a bug and tests/integration/test_synthetic_data_consistency.py
should catch it before this script runs.
"""

from __future__ import annotations

from pathlib import Path

from anga_grid.providers.nex_gddp.scenarios import SSP126, SSP245, SSP585
from anga_grid.synthetic import (
    synthetic_agera5,
    synthetic_chirps,
    synthetic_chirps_multiyear,
    synthetic_nex_gddp,
    synthetic_tamsat,
)

_FIXTURE_DIR = Path(__file__).parent / "data"

_NJORO_BBOX = {
    "lat_min": -0.5,
    "lat_max": -0.2,
    "lon_min": 35.85,
    "lon_max": 36.1,
}
_KISUMU_BBOX = {
    "lat_min": -0.30,
    "lat_max": 0.20,
    "lon_min": 34.50,
    "lon_max": 35.00,
}
_MOMBASA_BBOX = {
    "lat_min": -4.20,
    "lat_max": -3.80,
    "lon_min": 39.40,
    "lon_max": 39.90,
}


def main() -> None:
    _FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    # CHIRPS - single year baseline at Njoro
    synthetic_chirps(
        start="1991-01-01", end="1991-12-31",
        resolution=0.05, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "chirps_njoro_1991.nc")

    # CHIRPS - five years for SPI windowing demo
    synthetic_chirps_multiyear(
        years=(1991, 1995),
        resolution=0.05, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "chirps_njoro_1991_1995.nc")

    # CHIRPS - 30-year WMO climatology baseline at Njoro
    synthetic_chirps_multiyear(
        years=(1991, 2020),
        resolution=0.05, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "chirps_njoro_1991_2020.nc")

    # CHIRPS - regional variety: Kisumu (Lake Victoria basin)
    synthetic_chirps(
        start="1991-01-01", end="1991-12-31",
        resolution=0.05, seed=1991, **_KISUMU_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "chirps_kisumu_1991.nc")

    # CHIRPS - regional variety: Mombasa coastal
    synthetic_chirps(
        start="1991-01-01", end="1991-12-31",
        resolution=0.05, seed=1991, **_MOMBASA_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "chirps_mombasa_1991.nc")

    # AgERA5 - long-rains slice (matches WRSI example)
    synthetic_agera5(
        start="1991-03-01", end="1991-08-31",
        resolution=0.1, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "agera5_njoro_1991_long_rains.nc")

    # AgERA5 - full year for monthly indicator chains
    synthetic_agera5(
        start="1991-01-01", end="1991-12-31",
        resolution=0.1, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "agera5_njoro_1991_full_year.nc")

    # TAMSAT - single year baseline at Njoro
    synthetic_tamsat(
        start="1991-01-01", end="1991-12-31",
        resolution=0.0375, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "tamsat_njoro_1991.nc")

    # TAMSAT - five years for cross-dataset trend comparison
    synthetic_tamsat(
        start="1991-01-01", end="1995-12-31",
        resolution=0.0375, seed=1991, **_NJORO_BBOX,
    ).to_netcdf(_FIXTURE_DIR / "tamsat_njoro_1991_1995.nc")

    # NEX-GDDP - the three SSP scenarios that matter for outlook work
    for scenario in (SSP126, SSP245, SSP585):
        synthetic_nex_gddp(
            start="2030-01-01", end="2030-12-31",
            resolution=0.25, seed=2030, **_NJORO_BBOX,
        ).to_netcdf(
            _FIXTURE_DIR / f"nex_gddp_njoro_{scenario.name}_2030.nc"
        )

    print("Wrote fixtures:")
    total = 0
    for path in sorted(_FIXTURE_DIR.glob("*.nc")):
        sz = path.stat().st_size
        total += sz
        print(f"  {path.name}: {sz:>12,} bytes")
    print(f"  total: {total:>12,} bytes ({total / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
