from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from click.testing import CliRunner

from anga_grid.cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def annual_dataset(tmp_path: Path) -> Path:
    n = 10
    times = pd.date_range("1991-01-01", periods=n, freq="YS")
    data = np.arange(n, dtype="float32")
    ds = xr.Dataset(
        {"x": (("time",), data)},
        coords={"time": times},
        attrs={"source": "synthetic"},
    )
    p = tmp_path / "annual.nc"
    ds.to_netcdf(p)
    return p


def test_trend_writes_output(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    out = tmp_path / "trend.nc"
    result = runner.invoke(
        cli,
        ["trend", "--input", str(annual_dataset), "--output", str(out), "--reducer", "mean"],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_trend_rejects_unknown_var(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    result = runner.invoke(
        cli,
        [
            "trend",
            "--input", str(annual_dataset),
            "--output", str(tmp_path / "out.nc"),
            "--var", "nonexistent",
        ],
    )
    assert result.exit_code != 0


def test_trend_rejects_unknown_season(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    result = runner.invoke(
        cli,
        [
            "trend",
            "--input", str(annual_dataset),
            "--output", str(tmp_path / "out.nc"),
            "--season", "fake-season",
        ],
    )
    assert result.exit_code != 0


def test_quintile_tercile_writes_output(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    out = tmp_path / "tercile.nc"
    result = runner.invoke(
        cli,
        [
            "quintile",
            "--input", str(annual_dataset),
            "--output", str(out),
            "--scheme", "tercile",
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_quintile_quintile_writes_output(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    out = tmp_path / "quintile.nc"
    result = runner.invoke(
        cli,
        [
            "quintile",
            "--input", str(annual_dataset),
            "--output", str(out),
            "--scheme", "quintile",
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_quintile_baseline_parsed(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    out = tmp_path / "baseline.nc"
    result = runner.invoke(
        cli,
        [
            "quintile",
            "--input", str(annual_dataset),
            "--output", str(out),
            "--baseline", "1991-1995",
        ],
    )
    assert result.exit_code == 0, result.output


def test_quintile_rejects_bad_baseline(
    runner: CliRunner, tmp_path: Path, annual_dataset: Path
) -> None:
    result = runner.invoke(
        cli,
        [
            "quintile",
            "--input", str(annual_dataset),
            "--output", str(tmp_path / "out.nc"),
            "--baseline", "not-a-year",
        ],
    )
    assert result.exit_code != 0


def test_root_help_lists_trend_and_quintile(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert "trend" in result.output
    assert "quintile" in result.output
