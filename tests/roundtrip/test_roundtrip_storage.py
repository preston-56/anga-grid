from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.provenance import Manifest, read
from anga_grid.storage import open_dataset, read_manifest, write, write_with_manifest


def _sample_dataset() -> xr.Dataset:
    times = pd.date_range("2024-01-01", periods=20, freq="D")
    rng = np.random.default_rng(42)
    return xr.Dataset(
        data_vars={
            "rain": (
                ("time",),
                rng.exponential(3.0, size=20).astype("float32"),
                {"units": "mm/day"},
            ),
        },
        coords={"time": times},
        attrs={"source": "synthetic-roundtrip"},
    )


@pytest.mark.roundtrip
def test_netcdf_write_read_preserves_values(tmp_path: Path) -> None:
    ds = _sample_dataset()
    out = tmp_path / "round.nc"
    write(ds, out)
    reread = open_dataset(out)
    np.testing.assert_allclose(reread["rain"].values, ds["rain"].values, rtol=1e-6)


@pytest.mark.roundtrip
def test_zarr_write_read_preserves_values(tmp_path: Path) -> None:
    ds = _sample_dataset()
    out = tmp_path / "round.zarr"
    write(ds, out)
    reread = open_dataset(out)
    np.testing.assert_allclose(reread["rain"].values, ds["rain"].values, rtol=1e-6)


@pytest.mark.roundtrip
def test_netcdf_preserves_dataset_attrs(tmp_path: Path) -> None:
    ds = _sample_dataset()
    out = tmp_path / "attrs.nc"
    write(ds, out)
    reread = open_dataset(out)
    assert reread.attrs.get("source") == "synthetic-roundtrip"


@pytest.mark.roundtrip
def test_netcdf_preserves_variable_attrs(tmp_path: Path) -> None:
    ds = _sample_dataset()
    out = tmp_path / "var-attrs.nc"
    write(ds, out)
    reread = open_dataset(out)
    assert reread["rain"].attrs.get("units") == "mm/day"


@pytest.mark.roundtrip
def test_manifest_survives_netcdf_roundtrip(tmp_path: Path) -> None:
    ds = _sample_dataset()
    m = Manifest(source="CHIRPS-2.0", provider="chirps-v2.0")
    m.add_caveat("complex topography bias")
    m.record("fetch", region="njoro")
    m.record("subset", bbox="-1.2,-0.2,35.6,36.4")

    out = tmp_path / "with-manifest.nc"
    write_with_manifest(ds, out, m, operation="snapshot")
    restored = read_manifest(out)

    operations = [s.operation for s in restored.steps]
    assert "fetch" in operations
    assert "subset" in operations
    assert "snapshot" in operations
    assert "complex topography bias" in restored.caveats


@pytest.mark.roundtrip
def test_manifest_survives_zarr_roundtrip(tmp_path: Path) -> None:
    ds = _sample_dataset()
    m = Manifest(source="CHIRPS-2.0")
    m.record("indicator", name="spi", window=3)
    out = tmp_path / "with-manifest.zarr"
    write_with_manifest(ds, out, m, operation="snapshot")
    restored = read_manifest(out)
    operations = [s.operation for s in restored.steps]
    assert "indicator" in operations
    assert "snapshot" in operations


@pytest.mark.roundtrip
def test_manifest_caveats_roundtrip_through_attrs() -> None:
    m = Manifest(source="x")
    m.add_caveat("first caveat")
    m.add_caveat("second caveat without separators")
    attrs = m.as_attrs()
    restored = Manifest.from_attrs(dict(attrs))
    assert len(restored.caveats) == 2
    assert restored.caveats[0] == "first caveat"


@pytest.mark.roundtrip
def test_manifest_history_order_preserved() -> None:
    m = Manifest(source="x")
    m.record("a", k="v1")
    m.record("b", k="v2")
    m.record("c", k="v3")
    restored = Manifest.from_attrs(dict(m.as_attrs()))
    assert [s.operation for s in restored.steps] == ["a", "b", "c"]


@pytest.mark.roundtrip
def test_empty_dataset_roundtrip(tmp_path: Path) -> None:
    times = pd.date_range("2024-01-01", periods=3, freq="D")
    empty = xr.Dataset(coords={"time": times}, attrs={"source": "empty"})
    out = tmp_path / "empty.nc"
    write(empty, out)
    reread = open_dataset(out)
    m = read(reread)
    assert m.source == "empty"
