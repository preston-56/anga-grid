from __future__ import annotations

import click

from anga_grid.season import SEASONS


@click.group()
def seasons() -> None:
    pass


@seasons.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def seasons_list(fmt: str) -> None:
    if fmt == "json":
        import json

        out = [
            {
                "name": s.name,
                "start_doy": s.start_doy,
                "end_doy": s.end_doy,
                "definition_source": s.definition_source,
            }
            for s in SEASONS.values()
        ]
        click.echo(json.dumps(out, indent=2))
        return

    name_w = max(len(s.name) for s in SEASONS.values())
    src_w = max(len(s.definition_source) for s in SEASONS.values())
    click.echo(
        f"{'season'.ljust(name_w)}  start  end  {'source'.ljust(src_w)}"
    )
    click.echo("-" * (name_w + src_w + 14))
    for s in SEASONS.values():
        click.echo(
            f"{s.name.ljust(name_w)}  {s.start_doy:>5}  {s.end_doy:>3}  "
            f"{s.definition_source.ljust(src_w)}"
        )
