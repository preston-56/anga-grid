from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from anga_grid.indicators import compute_spi, detect_onset
from anga_grid.season import SEASONS

if TYPE_CHECKING:
    import xarray as xr


@click.group()
def compute() -> None:
    pass


@compute.command("spi")
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(path_type=Path, exists=True),
)
@click.option("--window", required=True, type=int)
@click.option("--season", "season_key", default=None)
@click.option("--baseline", default=None, help="YYYY-YYYY")
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path, dir_okay=True),
)
@click.option("--var", default="precip", help="rainfall variable name")
def compute_spi_cmd(
    input_path: Path,
    window: int,
    season_key: str | None,
    baseline: str | None,
    output: Path,
    var: str,
) -> None:
    ds = _open_input(input_path)
    pr = ds[var]
    season = SEASONS.get(season_key) if season_key else None
    baseline_tuple = _parse_baseline(baseline)
    result = compute_spi(pr, window, season=season, baseline=baseline_tuple)
    _write_output(result.to_dataset(name=f"spi{window}"), output)
    click.echo(f"wrote {output}")


@compute.command("onset")
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(path_type=Path, exists=True),
)
@click.option("--season", "season_key", default=None)
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path, dir_okay=True),
)
@click.option("--var", default="precip", help="rainfall variable name")
def compute_onset_cmd(
    input_path: Path,
    season_key: str | None,
    output: Path,
    var: str,
) -> None:
    ds = _open_input(input_path)
    pr = ds[var]
    season = SEASONS.get(season_key) if season_key else None
    result = detect_onset(pr, season=season)
    _write_output(result.to_dataset(name="onset_doy"), output)
    click.echo(f"wrote {output}")


def _open_input(path: Path) -> xr.Dataset:
    import xarray as xr

    if path.suffix == ".zarr" or path.name.endswith(".zarr"):
        return xr.open_zarr(path)
    return xr.open_dataset(path)


def _parse_baseline(value: str | None) -> tuple[int, int] | None:
    if value is None:
        return None
    if "-" not in value:
        raise click.BadParameter("--baseline must be YYYY-YYYY")
    a, b = value.split("-", 1)
    return int(a), int(b)


def _write_output(ds: xr.Dataset, output: Path) -> None:
    output = output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".zarr" or output.name.endswith(".zarr"):
        ds.to_zarr(output, mode="w")
    else:
        ds.to_netcdf(output)
