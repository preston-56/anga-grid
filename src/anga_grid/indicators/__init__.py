"""Climate-indicator surface.

Each indicator lives in its own themed sub-package; the top-level
re-exports give callers a flat 'from anga_grid.indicators import X'
without having to know the file layout.
"""

from anga_grid.indicators.dry_spell import dry_spell_count
from anga_grid.indicators.evapotranspiration import reference_et
from anga_grid.indicators.gdd import growing_degree_days
from anga_grid.indicators.onset import detect_onset
from anga_grid.indicators.spi import compute_spi
from anga_grid.indicators.temperature_extremes import (
    cold_days,
    frost_days,
    hot_days,
    tropical_nights,
)
from anga_grid.indicators.trend import annual_trend, seasonal_trend
from anga_grid.indicators.wrsi import water_requirement_satisfaction_index

__all__ = [
    "annual_trend",
    "cold_days",
    "compute_spi",
    "detect_onset",
    "dry_spell_count",
    "frost_days",
    "growing_degree_days",
    "hot_days",
    "reference_et",
    "seasonal_trend",
    "tropical_nights",
    "water_requirement_satisfaction_index",
]
