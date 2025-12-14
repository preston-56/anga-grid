from __future__ import annotations

import pytest


@pytest.mark.smoke
def test_package_imports() -> None:
    import anga_grid

    assert anga_grid.__version__


@pytest.mark.smoke
def test_cli_entry_point_imports() -> None:
    from anga_grid.cli.main import cli

    assert cli.name == "cli"


@pytest.mark.smoke
def test_provider_protocol_imports() -> None:
    from anga_grid.providers import (
        AgERA5Provider,
        CHIRPSProvider,
        Provider,
        TAMSATProvider,
    )

    assert AgERA5Provider is not None
    assert CHIRPSProvider is not None
    assert TAMSATProvider is not None
    assert Provider is not None


@pytest.mark.smoke
def test_indicator_modules_import() -> None:
    from anga_grid.indicators import (
        compute_spi,
        detect_onset,
        dry_spell_count,
        growing_degree_days,
    )
    from anga_grid.indicators.evapotranspiration import reference_et
    from anga_grid.indicators.wrsi import water_requirement_satisfaction_index

    assert compute_spi is not None
    assert detect_onset is not None
    assert dry_spell_count is not None
    assert growing_degree_days is not None
    assert reference_et is not None
    assert water_requirement_satisfaction_index is not None


@pytest.mark.smoke
def test_season_catalog_non_empty() -> None:
    from anga_grid.season import SEASONS

    assert "long-rains" in SEASONS
    assert "short-rains" in SEASONS


@pytest.mark.smoke
def test_region_catalog_non_empty() -> None:
    from anga_grid.types import REGION_BBOXES

    for name in ("nakuru", "njoro", "molo"):
        assert name in REGION_BBOXES


@pytest.mark.smoke
def test_severity_bands_well_formed() -> None:
    from anga_grid.severity import KMD_SPI_BANDS, NDMA_LABELS

    assert len(KMD_SPI_BANDS) == 7
    assert "emergency" in NDMA_LABELS
