from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CropProfile:
    name: str
    init_days: int
    devt_days: int
    mid_days: int
    late_days: int
    kc_init: float
    kc_mid: float
    kc_end: float

    @property
    def total_days(self) -> int:
        return self.init_days + self.devt_days + self.mid_days + self.late_days


MAIZE = CropProfile(
    name="maize",
    init_days=20,
    devt_days=35,
    mid_days=40,
    late_days=30,
    kc_init=0.30,
    kc_mid=1.20,
    kc_end=0.50,
)

SORGHUM = CropProfile(
    name="sorghum",
    init_days=20,
    devt_days=30,
    mid_days=40,
    late_days=30,
    kc_init=0.30,
    kc_mid=1.05,
    kc_end=0.55,
)

BEANS = CropProfile(
    name="beans",
    init_days=15,
    devt_days=25,
    mid_days=35,
    late_days=20,
    kc_init=0.40,
    kc_mid=1.15,
    kc_end=0.35,
)
