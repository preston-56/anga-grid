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


def main() -> None:
    _FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    chirps_njoro = synthetic_chirps(
        start="1991-01-01", end="1991-12-31",
        resolution=0.05, seed=1991,
        **_NJORO_BBOX,
    )
    chirps_njoro.to_netcdf(_FIXTURE_DIR / "chirps_njoro_1991.nc")

    chirps_multi = synthetic_chirps_multiyear(
        years=(1991, 1995),
        resolution=0.05, seed=1991,
        **_NJORO_BBOX,
    )
    chirps_multi.to_netcdf(_FIXTURE_DIR / "chirps_njoro_1991_1995.nc")

    agera5 = synthetic_agera5(
        start="1991-03-01", end="1991-08-31",
        resolution=0.1, seed=1991,
        **_NJORO_BBOX,
    )
    agera5.to_netcdf(_FIXTURE_DIR / "agera5_njoro_1991_long_rains.nc")

    tamsat = synthetic_tamsat(
        start="1991-01-01", end="1991-12-31",
        resolution=0.0375, seed=1991,
        **_NJORO_BBOX,
    )
    tamsat.to_netcdf(_FIXTURE_DIR / "tamsat_njoro_1991.nc")

    nex = synthetic_nex_gddp(
        start="2030-01-01", end="2030-06-30",
        resolution=0.25, seed=2030,
        **_NJORO_BBOX,
    )
    nex.to_netcdf(_FIXTURE_DIR / "nex_gddp_njoro_ssp245_2030.nc")

    print("Wrote fixtures:")
    for path in sorted(_FIXTURE_DIR.glob("*.nc")):
        print(f"  {path.name}: {path.stat().st_size:>9,} bytes")


if __name__ == "__main__":
    main()
