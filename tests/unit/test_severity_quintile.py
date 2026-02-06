from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from anga_grid.exceptions import AngaGridError
from anga_grid.severity import (
    quintile_classification,
    tercile_classification,
    tercile_summary,
)


def _years_of_data(values_per_year: list[float]) -> xr.DataArray:
    n = len(values_per_year)
    times = pd.date_range("1991-01-01", periods=n, freq="YS")
    return xr.DataArray(
        np.asarray(values_per_year, dtype="float32"),
        coords={"time": times},
        dims=["time"],
    )


def test_tercile_classification_below_normal_is_low_third() -> None:
    da = _years_of_data([10.0, 20.0, 30.0])
    result = tercile_classification(da)
    assert str(result.values[0]) == "below-normal"
    assert str(result.values[2]) == "above-normal"


def test_tercile_classification_rejects_missing_time() -> None:
    da = xr.DataArray([1.0, 2.0], dims=["x"])
    with pytest.raises(AngaGridError):
        tercile_classification(da)


def test_tercile_classification_records_classification_attr() -> None:
    da = _years_of_data([10.0, 20.0, 30.0])
    result = tercile_classification(da)
    assert result.attrs["classification"] == "tercile"


def test_tercile_with_baseline_window_uses_only_baseline_years() -> None:
    da = _years_of_data([1.0] * 5 + [100.0] * 5)
    result = tercile_classification(da, baseline=(1991, 1995))
    assert str(result.values[-1]) == "above-normal"


def test_tercile_summary_sums_to_one() -> None:
    da = _years_of_data([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    classified = tercile_classification(da)
    breakdown = tercile_summary(classified)
    assert sum(breakdown.values()) == pytest.approx(1.0)


def test_tercile_summary_rejects_non_classified_input() -> None:
    da = _years_of_data([1.0, 2.0, 3.0])
    with pytest.raises(AngaGridError, match="tercile classification"):
        tercile_summary(da)


def test_quintile_classification_assigns_five_labels() -> None:
    da = _years_of_data([float(i) for i in range(20)])
    result = quintile_classification(da)
    labels = {str(v) for v in result.values}
    assert {"very-dry", "dry", "near-normal", "wet", "very-wet"} <= labels


def test_quintile_classification_records_breaks_attr() -> None:
    da = _years_of_data([float(i) for i in range(10)])
    result = quintile_classification(da)
    assert result.attrs["quintile_breaks"] == "20,40,60,80"


def test_quintile_classification_rejects_missing_time() -> None:
    da = xr.DataArray([1.0, 2.0], dims=["x"])
    with pytest.raises(AngaGridError):
        quintile_classification(da)


def test_tercile_lower_pct_param_changes_thresholds() -> None:
    da = _years_of_data([float(i) for i in range(10)])
    permissive = tercile_classification(da, lower_pct=20.0, upper_pct=80.0)
    strict = tercile_classification(da, lower_pct=40.0, upper_pct=60.0)
    permissive_below = sum(1 for v in permissive.values if str(v) == "below-normal")
    strict_below = sum(1 for v in strict.values if str(v) == "below-normal")
    assert strict_below >= permissive_below


def test_tercile_classification_extends_manifest_history() -> None:
    da = _years_of_data([float(i) for i in range(10)])
    da.attrs["source"] = "CHIRPS-2.0"
    result = tercile_classification(da)
    assert "history" in result.attrs
    operations = [p.split("|")[1] for p in result.attrs["history"].split(" | ")]
    assert "tercile_classification" in operations


def test_tercile_2d_grid() -> None:
    n = 10
    times = pd.date_range("1991-01-01", periods=n, freq="YS")
    data = np.tile(np.arange(n).reshape(-1, 1, 1), (1, 2, 2)).astype("float32")
    da = xr.DataArray(
        data,
        coords={"time": times, "lat": [-0.5, 0.0], "lon": [35.0, 35.5]},
        dims=["time", "lat", "lon"],
    )
    result = tercile_classification(da)
    assert result.shape == (n, 2, 2)
