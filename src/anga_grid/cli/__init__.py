"""click-based CLI surface for anga-grid.

Each subcommand lives in its own module under cli/ and registers
itself onto the root group in cli.main. Adding a new subcommand
means: write the module, import its command into cli.main, call
cli.add_command on it. See cli.trend for the smallest pattern.
"""

from anga_grid.cli.main import cli

__all__ = ["cli"]
