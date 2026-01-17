"""Fetch synthetic CHIRPS over Njoro and compute SPI-3 for the long rains.

Usage (from a checkout):

    uv run python examples/01_chirps_njoro_spi.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from anga_grid.indicators import compute_spi
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.season import SEASONS
from anga_grid.types import TimeRange, resolve_region


def main() -> None:
    bbox = resolve_region("njoro")
    time_range = TimeRange(start=date(1991, 1, 1), end=date(1993, 12, 31))

    from anga_grid.synthetic.chirps import synthetic_chirps_multiyear

    with TemporaryDirectory() as raw:
        synthetic_path = Path(raw) / "synthetic-chirps.nc"
        synthetic_chirps_multiyear(years=(1991, 1993)).to_netcdf(synthetic_path)

        provider = CHIRPSProvider(
            cache_dir=Path(raw) / "cache",
            source_override=synthetic_path,
        )
        ds = provider.fetch(bbox, time_range)
        spi = compute_spi(
            ds["precip"],
            window_months=3,
            season=SEASONS["long-rains"],
            baseline=(1991, 1993),
        )

    print(f"fetched {ds.sizes['time']} days over {ds.sizes['lat']}x{ds.sizes['lon']} cells")
    print(f"spi-3 long-rains output: {spi.sizes['time']} time points")
    print(f"manifest history: {spi.attrs.get('history', '')}")


if __name__ == "__main__":
    main()
