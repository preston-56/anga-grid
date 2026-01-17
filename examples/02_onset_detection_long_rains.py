"""Detect long-rains onset over Nakuru ward bboxes for a single year."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from anga_grid.indicators import detect_onset
from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.rollup import NAKURU_WARDS, roll_up
from anga_grid.season import SEASONS
from anga_grid.types import TimeRange, resolve_region


def main() -> None:
    bbox = resolve_region("nakuru")
    time_range = TimeRange(start=date(1991, 1, 1), end=date(1991, 12, 31))

    from anga_grid.synthetic.chirps import synthetic_chirps

    with TemporaryDirectory() as raw:
        synthetic_path = Path(raw) / "synthetic-chirps.nc"
        synthetic_chirps(start="1991-01-01", end="1991-12-31").to_netcdf(synthetic_path)

        provider = CHIRPSProvider(
            cache_dir=Path(raw) / "cache",
            source_override=synthetic_path,
        )
        ds = provider.fetch(bbox, time_range)
        onset = detect_onset(ds["precip"], season=SEASONS["long-rains"])

    onset_per_ward = roll_up(onset, list(NAKURU_WARDS), reducer="median")
    print("ward median onset day-of-year (long rains 1991):")
    for region, value in zip(
        onset_per_ward["region"].values,
        onset_per_ward.values,
        strict=True,
    ):
        printable = "no detection" if value != value else int(value)
        print(f"  {region}: {printable}")


if __name__ == "__main__":
    main()
