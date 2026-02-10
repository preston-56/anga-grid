from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import xarray as xr

from anga_grid.cli.main import cli
from anga_grid.cropping import CALENDARS_BY_REGION, get_calendar
from anga_grid.provenance import Manifest
from anga_grid.providers.nex_gddp import NEXGDDPProvider
from anga_grid.synthetic.nex_gddp import synthetic_nex_gddp
from anga_grid.types import BoundingBox, TimeRange


@pytest.mark.roundtrip
def test_nex_gddp_fetch_writes_readable_netcdf(tmp_path: Path) -> None:
    src = tmp_path / "raw.nc"
    synthetic_nex_gddp(start="2030-01-01", end="2030-01-31").to_netcdf(src)
    provider = NEXGDDPProvider(cache_dir=tmp_path, source_override=src)
    ds = provider.fetch(
        BoundingBox(min_lat=-1.2, max_lat=0.2, min_lon=35.6, max_lon=36.4),
        TimeRange(start=date(2030, 1, 1), end=date(2030, 1, 31)),
    )
    out = tmp_path / "fetched.nc"
    ds.to_netcdf(out)
    reread = xr.open_dataset(out)
    assert "tas_mean" in reread.data_vars
    assert "precipitation" in reread.data_vars


@pytest.mark.roundtrip
def test_calendar_round_trip_via_get_calendar() -> None:
    for name, expected in CALENDARS_BY_REGION.items():
        retrieved = get_calendar(name)
        assert retrieved is expected


@pytest.mark.roundtrip
def test_manifest_with_unicode_caveat_round_trip() -> None:
    m = Manifest(source="x")
    m.add_caveat("Mau Escarpment & Aberdares: 0.05° underestimate")
    restored = Manifest.from_attrs(dict(m.as_attrs()))
    assert restored.caveats == m.caveats


@pytest.mark.roundtrip
def test_cli_quintile_then_open_writes_classification_attr(tmp_path: Path) -> None:
    import numpy as np
    import pandas as pd
    from click.testing import CliRunner

    runner = CliRunner()
    times = pd.date_range("1991-01-01", periods=10, freq="YS")
    ds = xr.Dataset(
        {"x": (("time",), np.arange(10, dtype="float32"))},
        coords={"time": times},
        attrs={"source": "synthetic"},
    )
    src = tmp_path / "annual.nc"
    ds.to_netcdf(src)

    out = tmp_path / "tercile.nc"
    result = runner.invoke(
        cli,
        [
            "quintile",
            "--input", str(src),
            "--output", str(out),
            "--scheme", "tercile",
        ],
    )
    assert result.exit_code == 0, result.output
    reread = xr.open_dataset(out)
    var = next(iter(reread.data_vars))
    assert reread[var].attrs.get("classification") == "tercile"


@pytest.mark.roundtrip
def test_cli_trend_then_open_writes_indicator_attr(tmp_path: Path) -> None:
    import numpy as np
    import pandas as pd
    from click.testing import CliRunner

    runner = CliRunner()
    times = pd.date_range("1991-01-01", periods=365 * 5, freq="D")
    ds = xr.Dataset(
        {"rain": (("time",), np.ones(len(times), dtype="float32"))},
        coords={"time": times},
        attrs={"source": "synthetic"},
    )
    src = tmp_path / "rain.nc"
    ds.to_netcdf(src)

    out = tmp_path / "trend.nc"
    result = runner.invoke(
        cli,
        ["trend", "--input", str(src), "--output", str(out), "--reducer", "mean"],
    )
    assert result.exit_code == 0, result.output
    reread = xr.open_dataset(out)
    var = next(iter(reread.data_vars))
    assert "trend" in reread[var].attrs.get("indicator", "")
