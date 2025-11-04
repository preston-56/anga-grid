from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import ProvenanceError
from anga_grid.provenance import Manifest, Step, merge, read, stamp


def _empty_ds() -> xr.Dataset:
    return xr.Dataset(
        data_vars={
            "x": (("time",), np.zeros(3, dtype="float32")),
        },
        coords={"time": pd.date_range("2024-01-01", periods=3, freq="D")},
    )


def test_manifest_as_attrs_includes_minimum() -> None:
    m = Manifest(source="CHIRPS-2.0")
    attrs = m.as_attrs()
    assert attrs["source"] == "CHIRPS-2.0"
    assert "code_version" in attrs


def test_manifest_record_appends_history() -> None:
    m = Manifest(source="x")
    m.record("subset", region="njoro")
    m.record("indicator", name="spi", window=3)
    attrs = m.as_attrs()
    assert "history" in attrs
    assert attrs["history"].count(" | ") == 1
    assert "region=njoro" in attrs["history"]
    assert "name=spi" in attrs["history"]


def test_manifest_add_caveat_dedupes() -> None:
    m = Manifest(source="x")
    m.add_caveat("a caveat")
    m.add_caveat("a caveat")
    m.add_caveat("second")
    assert m.caveats == ["a caveat", "second"]
    assert m.as_attrs()["caveats"] == "a caveat; second"


def test_stamp_writes_attrs_to_dataset() -> None:
    ds = _empty_ds()
    m = Manifest(source="CHIRPS", provider="chirps-v2.0")
    stamp(ds, m)
    assert ds.attrs["source"] == "CHIRPS"
    assert ds.attrs["provider"] == "chirps-v2.0"


def test_read_roundtrips_manifest() -> None:
    m = Manifest(source="CHIRPS", provider="chirps-v2.0")
    m.add_caveat("complex topography bias")
    m.record("subset", bbox="njoro")
    ds = stamp(_empty_ds(), m)
    out = read(ds)
    assert out.source == "CHIRPS"
    assert "complex topography bias" in out.caveats
    assert any(s.operation == "subset" for s in out.steps)


def test_read_raises_on_missing_source() -> None:
    ds = _empty_ds()
    with pytest.raises(ProvenanceError):
        read(ds)


def test_merge_combines_steps_and_caveats() -> None:
    parent = Manifest(source="CHIRPS")
    parent.add_caveat("CHIRPS complex topography bias")
    parent.record("fetch", region="njoro")
    child = Manifest(source="CHIRPS", provider="chirps-v2.0")
    child.record("spi", window=3, baseline="1991-2020")
    out = merge(parent, child, operation="compose")
    assert "CHIRPS complex topography bias" in out.caveats
    operations = [s.operation for s in out.steps]
    assert operations == ["fetch", "spi", "compose"]


def test_serialize_step_roundtrip() -> None:
    step = Step(
        operation="subset",
        parameters={"region": "njoro", "year": "1991"},
        timestamp="2025-09-30T12:00:00+00:00",
    )
    text = step.serialize()
    assert "operation=subset" not in text
    assert "subset" in text
    assert "region=njoro" in text


def test_history_token_with_bad_param_raises() -> None:
    ds = _empty_ds()
    ds.attrs["source"] = "CHIRPS"
    ds.attrs["history"] = "2025|op|bad-no-equals"
    with pytest.raises(ProvenanceError):
        read(ds)
