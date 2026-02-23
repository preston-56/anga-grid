# Datasets

anga-grid v0.5 ships four providers: **CHIRPS**, **AgERA5**,
**TAMSAT**, and **NEX-GDDP-CMIP6**. Each is documented below with the
caveats that matter for East African work; the provider interface is
the same across all four (`fetch()` returns an `xarray.Dataset` carrying
a Provenance Manifest in `attrs`).

## CHIRPS

The Climate Hazards Center InfraRed Precipitation with Station data
(CHIRPS) v2.0 is a quasi-global rainfall dataset spanning 1981–present
at 0.05° spatial resolution and daily temporal resolution. Distributed
by UCSB as monthly NetCDF files using a fill value of `-9999.0` over
land masks; xarray decodes this via CF conventions when present.

**Caveat for East Africa:** CHIRPS is known to underestimate rainfall
over complex topography. The Mau Escarpment, the Aberdares, and the
windward slopes of Mt. Kenya show systematic dry bias when compared to
gauge networks. anga-grid surfaces this as metadata on outputs over
affected pixels rather than silently passing it through.

*Reference:* Funk et al. (2015), *Scientific Data* 2, 150066.

## AgERA5

ECMWF's ERA5 reanalysis post-processed for agronomic use, distributed
by the Copernicus Climate Change Service. 0.1° spatial resolution,
hourly→daily aggregates, 1979–present. anga-grid exposes the eight
variables that drive the agronomic indicators: mean / min / max daily
air temperature, precipitation flux, solar radiation flux, daily
vapour pressure, 10 m mean wind speed, and 12 h relative humidity at
2 m. These feed reference evapotranspiration (FAO-56 Penman-Monteith),
growing degree days, and the WRSI water-balance.

Variable names are normalised to lower-snake-case on read so downstream
code doesn't have to care about Copernicus's mixed-case originals.

## TAMSAT

Tropical Applications of Meteorology using SATellite data (University
of Reading). African-only rainfall estimate at 0.0375° (~4 km) daily
resolution from 1983. Complementary to CHIRPS — different satellite
retrieval, different bias structure. Useful for sensitivity analysis
when CHIRPS is the primary source, and as an independent cross-check
on indicator outputs over the same region and window.

*Reference:* Maidment et al. (2017), *Scientific Data* 4, 170063.

## NEX-GDDP-CMIP6

NASA Earth Exchange Global Daily Downscaled Projections, CMIP6
ensemble. Statistically downscaled climate projections at 0.25°
resolution to 2100. anga-grid exposes the historical run (1950–2014)
plus four SSP scenarios — SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5 —
each carrying its radiative forcing in W·m⁻² and the legacy RCP label
in metadata for cross-referencing older literature.

Used for projection-vs-observation comparisons and for forward
indicator runs under specified scenarios. Not framed as a forecast:
the projections inherit the source-model uncertainty, and anga-grid
preserves the scenario tag through every downstream operation so a
plot or report can never silently mix scenarios.

*Reference:* Thrasher et al. (2022), *Scientific Data* 9, 262.
