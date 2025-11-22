from __future__ import annotations

from pathlib import Path

import pytest
import xarray as xr
from click.testing import CliRunner

from anga_grid.cli.main import cli
from tests.fixtures.synthetic import synthetic_chirps_multiyear


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def synthetic_nc(tmp_path: Path) -> Path:
    ds = synthetic_chirps_multiyear(years=(1991, 1993))
    p = tmp_path / "synthetic-chirps.nc"
    ds.to_netcdf(p)
    return p


def test_rollup_wards(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    rollup_out = tmp_path / "rollup.nc"

    runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "nakuru",
            "--start", "1991-01-01",
            "--end", "1991-06-30",
            "--cache-dir", str(cache),
            "--output", str(chirps_out),
            "--source-override", str(synthetic_nc),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "rollup",
            "--input", str(chirps_out),
            "--output", str(rollup_out),
            "--scope", "nakuru-wards",
            "--reducer", "mean",
        ],
    )
    assert result.exit_code == 0, result.output
    assert rollup_out.exists()
    ds = xr.open_dataset(rollup_out)
    assert "region" in ds.dims
    assert ds.sizes["region"] == 4


def test_rollup_county(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    rollup_out = tmp_path / "rollup.nc"

    runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "nakuru",
            "--start", "1991-01-01",
            "--end", "1991-06-30",
            "--cache-dir", str(cache),
            "--output", str(chirps_out),
            "--source-override", str(synthetic_nc),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "rollup",
            "--input", str(chirps_out),
            "--output", str(rollup_out),
            "--scope", "nakuru-county",
        ],
    )
    assert result.exit_code == 0, result.output
    ds = xr.open_dataset(rollup_out)
    assert ds.sizes["region"] == 1


def test_classify_kmd_end_to_end(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    spi_out = tmp_path / "spi.nc"
    severity_out = tmp_path / "severity.nc"

    runner.invoke(
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
    runner.invoke(
        cli,
        [
            "compute", "spi",
            "--input", str(chirps_out),
            "--window", "3",
            "--baseline", "1991-1993",
            "--output", str(spi_out),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "classify",
            "--input", str(spi_out),
            "--output", str(severity_out),
            "--scheme", "kmd",
            "--summary",
        ],
    )
    assert result.exit_code == 0, result.output
    ds = xr.open_dataset(severity_out)
    assert ds[next(iter(ds.data_vars))].dtype.kind == "i"


def test_classify_ndma_writes_phase(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    spi_out = tmp_path / "spi.nc"
    phase_out = tmp_path / "phase.nc"

    runner.invoke(
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
    runner.invoke(
        cli,
        [
            "compute", "spi",
            "--input", str(chirps_out),
            "--window", "3",
            "--output", str(spi_out),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "classify",
            "--input", str(spi_out),
            "--output", str(phase_out),
            "--scheme", "ndma",
        ],
    )
    assert result.exit_code == 0, result.output
    assert phase_out.exists()
    assert xr.open_dataset(phase_out).sizes["time"] > 0


def test_rollup_help_lists_scopes(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["rollup", "--help"])
    assert result.exit_code == 0
    assert "nakuru-wards" in result.output
    assert "nakuru-county" in result.output


def test_classify_help_lists_schemes(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["classify", "--help"])
    assert result.exit_code == 0
    assert "kmd" in result.output
    assert "ndma" in result.output


def test_root_help_lists_new_commands(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert "rollup" in result.output
    assert "classify" in result.output


def test_rollup_rejects_var_not_in_dataset(
    runner: CliRunner, tmp_path: Path, synthetic_nc: Path
) -> None:
    cache = tmp_path / "cache"
    chirps_out = tmp_path / "chirps.nc"
    runner.invoke(
        cli,
        [
            "fetch", "chirps",
            "--region", "nakuru",
            "--start", "1991-01-01",
            "--end", "1991-06-30",
            "--cache-dir", str(cache),
            "--output", str(chirps_out),
            "--source-override", str(synthetic_nc),
        ],
    )
    result = runner.invoke(
        cli,
        [
            "rollup",
            "--input", str(chirps_out),
            "--output", str(tmp_path / "out.nc"),
            "--var", "nonexistent",
        ],
    )
    assert result.exit_code != 0
