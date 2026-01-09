from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    label: str
    description: str
    radiative_forcing_wm2: float
    representative_concentration_path: str = ""


HISTORICAL = Scenario(
    name="historical",
    label="Historical",
    description="CMIP6 historical run, 1950-2014",
    radiative_forcing_wm2=0.0,
)

SSP126 = Scenario(
    name="ssp126",
    label="SSP1-2.6 (sustainability)",
    description="Low forcing; net-zero CO2 by ~2075",
    radiative_forcing_wm2=2.6,
    representative_concentration_path="RCP2.6",
)

SSP245 = Scenario(
    name="ssp245",
    label="SSP2-4.5 (middle of the road)",
    description="Intermediate forcing; emissions stabilise mid-century",
    radiative_forcing_wm2=4.5,
    representative_concentration_path="RCP4.5",
)

SSP370 = Scenario(
    name="ssp370",
    label="SSP3-7.0 (regional rivalry)",
    description="High forcing; rising emissions, weak mitigation",
    radiative_forcing_wm2=7.0,
    representative_concentration_path="RCP7.0",
)

SSP585 = Scenario(
    name="ssp585",
    label="SSP5-8.5 (fossil-fueled development)",
    description="Very high forcing; emissions roughly triple by 2100",
    radiative_forcing_wm2=8.5,
    representative_concentration_path="RCP8.5",
)


SCENARIOS: dict[str, Scenario] = {
    s.name: s for s in (HISTORICAL, SSP126, SSP245, SSP370, SSP585)
}


def get_scenario(name: str) -> Scenario:
    key = name.strip().lower()
    if key not in SCENARIOS:
        raise ValueError(
            f"unknown scenario {name!r}; known: {sorted(SCENARIOS)}"
        )
    return SCENARIOS[key]
