from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import AngaGridError
from anga_grid.provenance import Manifest, read
from anga_grid.storage import (
    detect_format,
    open_dataset,
    read_manifest,
    write,
    write_with_manifest,
)


def _toy_dataset() -> xr.Dataset:
    times = pd.date_range("2024-01-01", periods=5, freq="D")
    data = np.arange(5, dtype="float32")
    return xr.Dataset(
        data_vars={"x": (("time",), data)},
        coords={"time": times},
        attrs={"source": "synthetic-toy"},
    )


def test_detect_format_zarr(tmp_path: Path) -> None:
    assert detect_format(tmp_path / "out.zarr") == "zarr"


def test_detect_format_netcdf(tmp_path: Path) -> None:
    assert detect_format(tmp_path / "out.nc") == "netcdf"
    assert detect_format(tmp_path / "out.nc4") == "netcdf"


def test_detect_format_unknown_raises(tmp_path: Path) -> None:
    with pytest.raises(AngaGridError):
        detect_format(tmp_path / "out.bin")


def test_write_and_open_zarr(tmp_path: Path) -> None:
    ds = _toy_dataset()
    out = tmp_path / "round.zarr"
    write(ds, out)
    reopened = open_dataset(out)
    assert "x" in reopened.data_vars
    assert reopened.sizes["time"] == 5


def test_write_and_open_netcdf(tmp_path: Path) -> None:
    ds = _toy_dataset()
    out = tmp_path / "round.nc"
    write(ds, out)
    reopened = open_dataset(out)
    assert "x" in reopened.data_vars


def test_write_dataarray_promotes_to_dataset(tmp_path: Path) -> None:
    da = _toy_dataset()["x"]
    da.name = "x"
    out = tmp_path / "da.nc"
    write(da, out)
    reopened = open_dataset(out)
    assert "x" in reopened.data_vars


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "data.nc"
    write(_toy_dataset(), out)
    assert out.exists()


def test_write_with_manifest_records_step(tmp_path: Path) -> None:
    out = tmp_path / "with-manifest.nc"
    m = Manifest(source="CHIRPS-2.0", provider="chirps-v2.0")
    m.add_caveat("complex topography bias")
    write_with_manifest(_toy_dataset(), out, m, operation="snapshot")
    reopened = open_dataset(out)
    restored = read(reopened)
    operations = [s.operation for s in restored.steps]
    assert "snapshot" in operations
    assert "complex topography bias" in restored.caveats


def test_read_manifest_returns_manifest(tmp_path: Path) -> None:
    out = tmp_path / "m.nc"
    m = Manifest(source="CHIRPS-2.0")
    m.record("fetch", region="njoro")
    write_with_manifest(_toy_dataset(), out, m, operation="snapshot")
    restored = read_manifest(out)
    assert restored.source == "CHIRPS-2.0"
    operations = [s.operation for s in restored.steps]
    assert "fetch" in operations
    assert "snapshot" in operations


def test_open_dataset_missing_file(tmp_path: Path) -> None:
    with pytest.raises(AngaGridError):
        open_dataset(tmp_path / "no-such-file.nc")


def test_open_dataset_unknown_format(tmp_path: Path) -> None:
    p = tmp_path / "data.xyz"
    p.write_bytes(b"")
    with pytest.raises(AngaGridError):
        open_dataset(p)
