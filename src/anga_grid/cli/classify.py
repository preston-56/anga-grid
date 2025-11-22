from __future__ import annotations

from pathlib import Path

import click

from anga_grid.severity import classify_spi, ndma_phase, severity_summary
from anga_grid.storage import open_dataset, write


@click.command("classify")
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
    type=click.Choice(["kmd", "ndma"]),
    default="kmd",
    show_default=True,
)
@click.option("--var", default=None, help="SPI variable name")
@click.option("--summary/--no-summary", default=False)
def classify_cmd(
    input_path: Path,
    output: Path,
    scheme: str,
    var: str | None,
    summary: bool,
) -> None:
    ds = open_dataset(input_path)
    target_var = var or next(iter(ds.data_vars))
    if target_var not in ds.data_vars:
        raise click.BadParameter(
            f"variable {target_var!r} not in input; "
            f"available: {list(ds.data_vars)}"
        )

    if scheme == "kmd":
        result = classify_spi(ds[target_var])
        result_name = f"{target_var}_severity"
    else:
        result = ndma_phase(ds[target_var])
        result_name = f"{target_var}_phase"

    write(result.to_dataset(name=result_name), output)
    click.echo(f"wrote {output}")

    if summary and scheme == "kmd":
        breakdown = severity_summary(result)
        for label, share in breakdown.items():
            click.echo(f"  {label}: {share:.1%}")
