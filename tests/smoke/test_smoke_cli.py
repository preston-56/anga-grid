from __future__ import annotations

import pytest
from click.testing import CliRunner

from anga_grid.cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.mark.smoke
def test_cli_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


@pytest.mark.smoke
def test_cli_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


@pytest.mark.smoke
@pytest.mark.parametrize(
    "subcommand", ["fetch", "compute", "seasons", "rollup", "classify"]
)
def test_cli_subcommand_help(runner: CliRunner, subcommand: str) -> None:
    result = runner.invoke(cli, [subcommand, "--help"])
    assert result.exit_code == 0
    assert subcommand in result.output or "Usage:" in result.output


@pytest.mark.smoke
def test_cli_seasons_list_runs(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["seasons", "list"])
    assert result.exit_code == 0
    assert "long-rains" in result.output


@pytest.mark.smoke
def test_cli_seasons_list_json_runs(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["seasons", "list", "--format", "json"])
    assert result.exit_code == 0
    assert "[" in result.output and "]" in result.output
