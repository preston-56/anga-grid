from __future__ import annotations

from pathlib import Path

import click

from anga_grid.exceptions import AngaGridError
from anga_grid.rollup import NAKURU_COUNTY, NAKURU_WARDS, AdminRegion, roll_up
from anga_grid.storage import open_dataset, write


@click.command("rollup")
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path, dir_okay=True),
)
@click.option(
    "--scope",
    type=click.Choice(["nakuru-wards", "nakuru-county"]),
    default="nakuru-wards",
    show_default=True,
)
@click.option(
    "--reducer",
    type=click.Choice(["mean", "sum", "max", "min", "median", "count"]),
    default="mean",
    show_default=True,
)
@click.option("--var", default=None, help="variable name (defaults to first data_var)")
def rollup_cmd(
    input_path: Path,
    output: Path,
    scope: str,
    reducer: str,
    var: str | None,
) -> None:
    ds = open_dataset(input_path)
    target_var = var or next(iter(ds.data_vars))
    if target_var not in ds.data_vars:
        raise click.BadParameter(
            f"variable {target_var!r} not in input; "
            f"available: {list(ds.data_vars)}"
        )

    regions: list[AdminRegion]
    if scope == "nakuru-wards":
        regions = list(NAKURU_WARDS)
    elif scope == "nakuru-county":
        regions = [NAKURU_COUNTY]
    else:
        raise click.BadParameter(f"unknown scope: {scope}")

    try:
        result = roll_up(ds[target_var], regions, reducer=reducer)
    except AngaGridError as exc:
        raise click.ClickException(str(exc)) from exc

    write(result.to_dataset(name=f"{target_var}_rollup"), output)
    click.echo(f"wrote {output} ({result.sizes['region']} regions)")
