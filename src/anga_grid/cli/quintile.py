from __future__ import annotations

from pathlib import Path

import click

from anga_grid.severity import quintile_classification, tercile_classification
from anga_grid.storage import open_dataset, write


@click.command("quintile")
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
    "--scheme",
    type=click.Choice(["tercile", "quintile"]),
    default="tercile",
    show_default=True,
)
@click.option("--baseline", default=None, help="YYYY-YYYY")
@click.option("--var", default=None)
def quintile_cmd(
    input_path: Path,
    output: Path,
    scheme: str,
    baseline: str | None,
    var: str | None,
) -> None:
    ds = open_dataset(input_path)
    target = var or next(iter(ds.data_vars))
    if target not in ds.data_vars:
        raise click.BadParameter(
            f"variable {target!r} not in input; available: {list(ds.data_vars)}"
        )

    baseline_tuple: tuple[int, int] | None = None
    if baseline is not None:
        if "-" not in baseline:
            raise click.BadParameter("--baseline must be YYYY-YYYY")
        a, b = baseline.split("-", 1)
        baseline_tuple = (int(a), int(b))

    if scheme == "tercile":
        result = tercile_classification(ds[target], baseline=baseline_tuple)
        name = f"{target}_tercile"
    else:
        result = quintile_classification(ds[target], baseline=baseline_tuple)
        name = f"{target}_quintile"

    write(result.to_dataset(name=name), output)
    click.echo(f"wrote {output}")
