from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.correction import (
    DeltaChange,
    LinearScaling,
    MonthlyLinearScaling,
)
from anga_grid.exceptions import AngaGridError


def _series(values: list[float], start: str = "1991-01-01") -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_linear_scaling_fit_recovers_factor() -> None:
    source = _series([10.0] * 30)
    reference = _series([15.0] * 30)
    fitted = LinearScaling.fit(source, reference)
    assert float(fitted.factors.values) == pytest.approx(1.5)


def test_linear_scaling_apply_scales_values() -> None:
    source = _series([10.0] * 30)
    reference = _series([15.0] * 30)
    fitted = LinearScaling.fit(source, reference)
    corrected = fitted.apply(source)
    assert float(corrected.values.mean()) == pytest.approx(15.0)


def test_linear_scaling_does_not_introduce_negatives() -> None:
    source = _series([1.0, 0.0, 2.0, 0.0, 5.0])
    reference = _series([2.0, 0.0, 4.0, 0.0, 10.0])
    fitted = LinearScaling.fit(source, reference)
    corrected = fitted.apply(source)
    assert float(corrected.min()) >= 0.0


def test_linear_scaling_zero_source_returns_unchanged() -> None:
    source = _series([0.0] * 10)
    reference = _series([5.0] * 10)
    fitted = LinearScaling.fit(source, reference)
    corrected = fitted.apply(source)
    assert float(corrected.values.mean()) == pytest.approx(0.0)


def test_delta_change_fit_recovers_offset() -> None:
    source = _series([10.0] * 30)
    reference = _series([12.5] * 30)
    fitted = DeltaChange.fit(source, reference)
    assert float(fitted.deltas.values) == pytest.approx(2.5)


def test_delta_change_apply_shifts_values() -> None:
    source = _series([10.0, 12.0, 8.0, 11.0])
    reference = _series([15.0, 17.0, 13.0, 16.0])
    fitted = DeltaChange.fit(source, reference)
    corrected = fitted.apply(source)
    expected = np.array([15.0, 17.0, 13.0, 16.0], dtype="float32")
    np.testing.assert_allclose(corrected.values, expected, rtol=1e-3)


def test_monthly_linear_scaling_handles_seasonal_variation() -> None:
    times = pd.date_range("1991-01-01", "1991-12-31", freq="D")
    months = times.month.to_numpy()
    source_values = np.where(months <= 6, 1.0, 5.0).astype("float32")
    reference_values = np.where(months <= 6, 2.0, 7.5).astype("float32")
    source = xr.DataArray(source_values, coords={"time": times}, dims=["time"])
    reference = xr.DataArray(reference_values, coords={"time": times}, dims=["time"])
    fitted = MonthlyLinearScaling.fit(source, reference)
    corrected = fitted.apply(source)
    h1_mean = float(corrected.sel(time=slice("1991-01-01", "1991-06-30")).mean())
    h2_mean = float(corrected.sel(time=slice("1991-07-01", "1991-12-31")).mean())
    assert h1_mean == pytest.approx(2.0, rel=0.01)
    assert h2_mean == pytest.approx(7.5, rel=0.01)


def test_correction_apply_rejects_missing_time() -> None:
    source = _series([10.0] * 5)
    reference = _series([12.0] * 5)
    fitted = LinearScaling.fit(source, reference)
    no_time = xr.DataArray([1.0, 2.0], dims=["x"])
    with pytest.raises(AngaGridError):
        fitted.apply(no_time)


def test_validate_rejects_spatial_mismatch() -> None:
    times = pd.date_range("1991-01-01", periods=5, freq="D")
    src = xr.DataArray(
        np.ones((5, 2, 2), dtype="float32"),
        coords={"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]},
        dims=["time", "lat", "lon"],
    )
    ref = xr.DataArray(
        np.ones((5, 3, 3), dtype="float32"),
        coords={
            "time": times,
            "lat": [-0.5, 0.0, 0.5],
            "lon": [35.0, 35.5, 36.0],
        },
        dims=["time", "lat", "lon"],
    )
    with pytest.raises(AngaGridError):
        LinearScaling.fit(src, ref)


def test_correction_extends_manifest_history() -> None:
    source = _series([10.0] * 30)
    source.attrs["source"] = "CHIRPS-2.0"
    reference = _series([15.0] * 30)
    fitted = LinearScaling.fit(source, reference)
    corrected = fitted.apply(source)
    assert "history" in corrected.attrs
    operations = [p.split("|")[1] for p in corrected.attrs["history"].split(" | ")]
    assert "bias_correction" in operations


def test_correction_stamps_method_attr() -> None:
    source = _series([10.0] * 30)
    source.attrs["source"] = "x"
    reference = _series([15.0] * 30)
    fitted = LinearScaling.fit(source, reference)
    corrected = fitted.apply(source)
    assert corrected.attrs["bias_corrected"] == "linear_scaling"


def test_delta_change_attrs_method() -> None:
    source = _series([10.0] * 5)
    source.attrs["source"] = "y"
    reference = _series([12.0] * 5)
    corrected = DeltaChange.fit(source, reference).apply(source)
    assert corrected.attrs["bias_corrected"] == "delta_change"
