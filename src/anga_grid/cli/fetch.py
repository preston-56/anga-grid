from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import click

from anga_grid.providers.chirps import CHIRPSProvider
from anga_grid.types import TimeRange, resolve_region

if TYPE_CHECKING:
    import xarray as xr


@click.group()
def fetch() -> None:
    pass


@fetch.command("chirps")
@click.option("--region", required=True, help="region key (e.g. nakuru, njoro, molo)")
@click.option("--start", required=True, type=click.DateTime(["%Y-%m-%d"]))
@click.option("--end", required=True, type=click.DateTime(["%Y-%m-%d"]))
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path, dir_okay=True),
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path("~/.cache/anga-grid").expanduser(),
    show_default=True,
)
@click.option(
    "--source-override",
    type=click.Path(path_type=Path, dir_okay=False, exists=True),
    help="path to a local NetCDF replica (skip the network)",
)
def fetch_chirps(
    region: str,
    start: datetime,
    end: datetime,
    output: Path,
    cache_dir: Path,
    source_override: Path | None,
) -> None:
    bbox = resolve_region(region)
    time_range = TimeRange(start=start.date(), end=end.date())
    cache_dir.mkdir(parents=True, exist_ok=True)
    provider = CHIRPSProvider(cache_dir=cache_dir, source_override=source_override)
    ds = provider.fetch(bbox, time_range)
    _write_dataset(ds, output)
    click.echo(f"wrote {output} ({ds.dims})")


def _write_dataset(ds: xr.Dataset, output: Path) -> None:
    output = output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".zarr" or output.name.endswith(".zarr"):
        ds.to_zarr(output, mode="w")
    else:
        ds.to_netcdf(output)
