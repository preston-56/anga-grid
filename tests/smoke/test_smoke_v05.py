from __future__ import annotations

import pytest


@pytest.mark.smoke
def test_v05_trend_indicator_imports() -> None:
    from anga_grid.indicators.trend import annual_trend, seasonal_trend

    assert annual_trend is not None
    assert seasonal_trend is not None


@pytest.mark.smoke
def test_v05_evapotranspiration_imports() -> None:
    from anga_grid.indicators.evapotranspiration import (
        reference_et,
        saturation_vapour_pressure,
    )

    assert reference_et is not None
    assert saturation_vapour_pressure is not None


@pytest.mark.smoke
def test_v05_wrsi_imports_with_three_crops() -> None:
    from anga_grid.indicators.wrsi import (
        MAIZE,
        SORGHUM,
        water_requirement_satisfaction_index,
    )

    assert MAIZE.name == "maize"
    assert SORGHUM.name == "sorghum"
    assert water_requirement_satisfaction_index is not None


@pytest.mark.smoke
def test_v05_quintile_classification_imports() -> None:
    from anga_grid.severity import (
        QUINTILE_LABELS,
        TERCILE_LABELS,
        quintile_classification,
        tercile_classification,
    )

    assert len(QUINTILE_LABELS) == 5
    assert len(TERCILE_LABELS) == 3
    assert quintile_classification is not None
    assert tercile_classification is not None


@pytest.mark.smoke
def test_v05_polygon_rollup_imports() -> None:
    from anga_grid.rollup import PolygonRegion, polygon_roll_up

    assert PolygonRegion is not None
    assert polygon_roll_up is not None


@pytest.mark.smoke
def test_v05_cropping_calendars_imports() -> None:
    from anga_grid.cropping import CALENDARS_BY_REGION, get_calendar

    assert "embu-long-rains" in CALENDARS_BY_REGION
    assert "kisumu-long-rains" in CALENDARS_BY_REGION
    assert "mombasa-long-rains" in CALENDARS_BY_REGION
    assert "garissa-unimodal" in CALENDARS_BY_REGION
    assert get_calendar("nakuru-long-rains") is not None


@pytest.mark.smoke
def test_v05_nex_gddp_provider_imports() -> None:
    from anga_grid.providers import NEXGDDPProvider
    from anga_grid.providers.nex_gddp.scenarios import SSP585

    assert NEXGDDPProvider is not None
    assert SSP585.name == "ssp585"


@pytest.mark.smoke
def test_v05_synthetic_helpers_import() -> None:
    from anga_grid.synthetic import (
        synthetic_agera5,
        synthetic_chirps,
        synthetic_nex_gddp,
        synthetic_tamsat,
    )

    for fn in (synthetic_agera5, synthetic_chirps, synthetic_nex_gddp, synthetic_tamsat):
        assert callable(fn)


@pytest.mark.smoke
def test_v05_provenance_split_imports() -> None:
    from anga_grid.provenance import Manifest, Step, merge, read, stamp
    from anga_grid.provenance.steps import now_utc, step_from_serialized

    assert Manifest is not None
    assert Step is not None
    assert all(callable(fn) for fn in (merge, read, stamp, now_utc, step_from_serialized))


@pytest.mark.smoke
def test_v05_storage_split_imports() -> None:
    from anga_grid.storage import (
        detect_format,
        open_dataset,
        read_manifest,
        write,
        write_with_manifest,
    )
    from anga_grid.storage.format import Format, ZarrMode

    assert all(callable(fn) for fn in (detect_format, open_dataset, write, write_with_manifest, read_manifest))
    assert Format is not None
    assert ZarrMode is not None


@pytest.mark.smoke
def test_v05_correction_split_imports() -> None:
    from anga_grid.correction import DeltaChange, LinearScaling, MonthlyLinearScaling
    from anga_grid.correction.base import stamp_correction, validate_pair

    assert all(cls is not None for cls in (DeltaChange, LinearScaling, MonthlyLinearScaling))
    assert callable(stamp_correction)
    assert callable(validate_pair)


@pytest.mark.smoke
def test_v05_severity_split_imports() -> None:
    from anga_grid.severity.bands import KMD_SPI_BANDS, classify_spi
    from anga_grid.severity.phases import NDMA_LABELS, ndma_phase
    from anga_grid.severity.summary import severity_summary

    assert KMD_SPI_BANDS
    assert NDMA_LABELS
    assert callable(classify_spi)
    assert callable(ndma_phase)
    assert callable(severity_summary)


@pytest.mark.smoke
def test_v05_types_split_imports() -> None:
    from anga_grid.types.geometry import BoundingBox, GridSpec
    from anga_grid.types.regions import REGION_BBOXES
    from anga_grid.types.time import TimeRange

    assert all(t is not None for t in (BoundingBox, GridSpec, TimeRange, REGION_BBOXES))
