from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import AngaGridError
from anga_grid.severity import (
    KMD_SPI_BANDS,
    NDMA_LABELS,
    classify_spi,
    ndma_phase,
    severity_summary,
)


def _spi_series(values: list[float]) -> xr.DataArray:
    times = pd.date_range("1991-01-01", periods=len(values), freq="ME")
    return xr.DataArray(
        np.asarray(values, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_classify_normal_is_zero() -> None:
    spi = _spi_series([0.0, 0.5, -0.5, 0.99])
    result = classify_spi(spi)
    np.testing.assert_array_equal(result.values, [0, 0, 0, 0])


def test_classify_moderate_drought() -> None:
    spi = _spi_series([-1.0, -1.25, -1.49])
    result = classify_spi(spi)
    np.testing.assert_array_equal(result.values, [-1, -1, -1])


def test_classify_severe_drought() -> None:
    spi = _spi_series([-1.5, -1.75, -1.99])
    result = classify_spi(spi)
    np.testing.assert_array_equal(result.values, [-2, -2, -2])


def test_classify_extreme_drought() -> None:
    spi = _spi_series([-2.0, -3.5, -10.0])
    result = classify_spi(spi)
    np.testing.assert_array_equal(result.values, [-3, -3, -3])


def test_classify_extremely_wet() -> None:
    spi = _spi_series([2.0, 3.5, 10.0])
    result = classify_spi(spi)
    np.testing.assert_array_equal(result.values, [3, 3, 3])


def test_classify_rejects_empty_bands() -> None:
    spi = _spi_series([0.0])
    with pytest.raises(AngaGridError, match="bands tuple cannot be empty"):
        classify_spi(spi, bands=())


def test_classify_attaches_labels_attr() -> None:
    spi = _spi_series([0.0, -1.0, -2.0])
    result = classify_spi(spi)
    assert "moderate drought" in result.attrs["band_labels"]
    assert "extreme drought" in result.attrs["band_labels"]


def test_ndma_phase_normal_above_minus_one() -> None:
    spi = _spi_series([0.0, 0.5, -0.5, 0.99])
    result = ndma_phase(spi)
    for v in result.values:
        assert v == "normal"


def test_ndma_phase_emergency_below_minus_two() -> None:
    spi = _spi_series([-2.0, -3.5])
    result = ndma_phase(spi)
    for v in result.values:
        assert v == "emergency"


def test_ndma_phase_alert_band() -> None:
    spi = _spi_series([-1.0, -1.25])
    result = ndma_phase(spi)
    for v in result.values:
        assert v == "alert"


def test_ndma_phase_records_phases_attr() -> None:
    spi = _spi_series([0.0])
    result = ndma_phase(spi)
    assert result.attrs["classification"] == "ndma_phase"
    for phase in NDMA_LABELS:
        assert phase in result.attrs["phases"]


def test_severity_summary_counts_to_one() -> None:
    spi = _spi_series([0.0, 0.0, -1.5, -1.5, 2.5])
    classified = classify_spi(spi)
    summary = severity_summary(classified)
    assert abs(sum(summary.values()) - 1.0) < 1e-6


def test_severity_summary_rejects_non_classified_input() -> None:
    spi = _spi_series([0.0, 0.0])
    with pytest.raises(AngaGridError, match="severity classification"):
        severity_summary(spi)


def test_severity_summary_empty_input_returns_zeros() -> None:
    empty = xr.DataArray(np.array([], dtype="int8"), dims=["time"])
    empty.attrs["classification"] = "spi_severity"
    out = severity_summary(empty)
    for v in out.values():
        assert v == 0.0


def test_classify_extends_manifest_history() -> None:
    spi = _spi_series([0.0, -1.5, -2.5])
    spi.attrs["source"] = "CHIRPS-2.0"
    result = classify_spi(spi)
    assert "history" in result.attrs
    operations = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "classify_spi" in operations


def test_kmd_bands_are_ordered_and_unique() -> None:
    codes = [b.code for b in KMD_SPI_BANDS]
    assert codes == sorted(codes)
    assert len(set(codes)) == len(codes)
