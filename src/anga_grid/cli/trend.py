from __future__ import annotations

from pathlib import Path

import click

from anga_grid.indicators.trend import annual_trend, seasonal_trend
from anga_grid.season import SEASONS
from anga_grid.storage import open_dataset, write


@click.command("trend")
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
    "--reducer",
    type=click.Choice(["sum", "mean", "max", "min"]),
    default="sum",
    show_default=True,
)
@click.option("--season", "season_key", default=None)
@click.option("--var", default=None, help="variable to analyse (default: first data_var)")
def trend_cmd(
    input_path: Path,
    output: Path,
    reducer: str,
    season_key: str | None,
    var: str | None,
) -> None:
    ds = open_dataset(input_path)
    target = var or next(iter(ds.data_vars))
    if target not in ds.data_vars:
        raise click.BadParameter(
            f"variable {target!r} not in input; available: {list(ds.data_vars)}"
        )

    if season_key is not None:
        if season_key not in SEASONS:
            raise click.BadParameter(
                f"unknown season {season_key!r}; available: {sorted(SEASONS)}"
            )
        result = seasonal_trend(ds[target], season=SEASONS[season_key], reducer=reducer)
        out_name = f"{target}_seasonal_trend"
    else:
        result = annual_trend(ds[target], reducer=reducer)
        out_name = f"{target}_annual_trend"

    write(result.to_dataset(name=out_name), output)
    click.echo(f"wrote {output}")
