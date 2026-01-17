from __future__ import annotations

import json
from pathlib import Path

import pytest
import xarray as xr
from click.testing import CliRunner

from anga_grid.cli.main import cli
from anga_grid.synthetic.chirps import synthetic_chirps, synthetic_chirps_multiyear


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def synthetic_nc(tmp_path: Path) -> Path:
    ds = synthetic_chirps_multiyear(years=(1991, 1993))
    p = tmp_path / "synthetic-chirps.nc"
    ds.to_netcdf(p)
    return p


def test_help_shows_subcommands(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "fetch" in result.output
    assert "compute" in result.output
    assert "seasons" in result.output


def test_version_flag(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "anga" in result.output


def test_seasons_list_table(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["seasons", "list"])
    assert result.exit_code == 0
    assert "long-rains" in result.output
    assert "short-rains" in result.output


def test_seasons_list_json(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["seasons", "list", "--format", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    names = {row["name"] for row in parsed}
    assert "long-rains" in names
    assert "gha-mam" in names


def test_fetch_chirps_writes_netcdf(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    out = tmp_path / "chirps-nakuru.nc"
    result = runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "nakuru",
            "--start", "1991-01-01",
            "--end", "1991-03-31",
            "--cache-dir", str(tmp_path / "cache"),
            "--output", str(out),
            "--source-override", str(synthetic_nc),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    reread = xr.open_dataset(out)
    assert "precip" in reread.data_vars


def test_fetch_chirps_rejects_unknown_region(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    result = runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "mars",
            "--start", "1991-01-01",
            "--end", "1991-03-31",
            "--cache-dir", str(tmp_path / "cache"),
            "--output", str(tmp_path / "out.nc"),
            "--source-override", str(synthetic_nc),
        ],
    )
    assert result.exit_code != 0


def test_compute_spi_end_to_end(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    spi_out = tmp_path / "spi3.nc"

    fetch_result = runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "njoro",
            "--start", "1991-01-01",
            "--end", "1993-12-31",
            "--cache-dir", str(cache),
            "--output", str(chirps_out),
            "--source-override", str(synthetic_nc),
        ],
    )
    assert fetch_result.exit_code == 0, fetch_result.output

    spi_result = runner.invoke(
        cli,
        [
            "compute", "spi",
            "--input", str(chirps_out),
            "--window", "3",
            "--baseline", "1991-1993",
            "--output", str(spi_out),
        ],
    )
    assert spi_result.exit_code == 0, spi_result.output
    assert spi_out.exists()
    reread = xr.open_dataset(spi_out)
    assert "spi3" in reread.data_vars


def test_compute_onset_end_to_end(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    onset_out = tmp_path / "onset.nc"

    runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "njoro",
            "--start", "1991-01-01",
            "--end", "1991-12-31",
            "--cache-dir", str(cache),
            "--output", str(chirps_out),
            "--source-override", str(synthetic_nc),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "compute", "onset",
            "--input", str(chirps_out),
            "--season", "long-rains",
            "--output", str(onset_out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert onset_out.exists()
    reread = xr.open_dataset(onset_out)
    assert "onset_doy" in reread.data_vars


def test_compute_spi_rejects_bad_baseline(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    chirps_out = tmp_path / "chirps.nc"
    ds = synthetic_chirps(start="1991-01-01", end="1991-12-31")
    ds.to_netcdf(chirps_out)

    result = runner.invoke(
        cli,
        [
            "compute", "spi",
            "--input", str(chirps_out),
            "--window", "3",
            "--baseline", "not-a-year",
            "--output", str(tmp_path / "out.nc"),
        ],
    )
    assert result.exit_code != 0
