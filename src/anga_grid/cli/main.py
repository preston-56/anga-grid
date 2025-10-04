from __future__ import annotations

import click

from anga_grid import __version__
from anga_grid.cli.compute import compute
from anga_grid.cli.fetch import fetch
from anga_grid.cli.seasons import seasons
from anga_grid.logging import configure


@click.group()
@click.version_option(__version__, prog_name="anga")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    show_default=True,
)
@click.option("--json-log/--text-log", default=False)
def cli(log_level: str, json_log: bool) -> None:
    import logging

    configure(level=getattr(logging, log_level), json_output=json_log)


cli.add_command(fetch)
cli.add_command(compute)
cli.add_command(seasons)


if __name__ == "__main__":
    cli()
