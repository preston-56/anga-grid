# Datasets

anga-grid v0.1 implements **CHIRPS** end-to-end. The other datasets
listed here are scoped for v0.2 and beyond; they're documented now so
the breadth of the project is visible and so the provider interface
stays honest about what each source can and cannot tell you.

## CHIRPS (v0.1 — implemented)

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

## AgERA5 (roadmap, v0.2)

ECMWF's ERA5 reanalysis post-processed for agronomic use, distributed
by the Copernicus Climate Change Service. 0.1° spatial resolution,
hourly→daily aggregates, 1979–present. Covers temperature, humidity,
solar radiation, wind, and precipitation. anga-grid will use AgERA5 for
the non-rainfall variables that feed agronomic indicators (reference
evapotranspiration, growing degree days).

## TAMSAT (roadmap, v0.2)

Tropical Applications of Meteorology using SATellite data (University
of Reading). African-only rainfall estimate at 0.0375° (~4 km) daily
resolution from 1983. Complementary to CHIRPS — different satellite
retrieval, different bias structure. Useful for sensitivity analysis
when CHIRPS is the primary source.

*Reference:* Maidment et al. (2017), *Scientific Data* 4, 170063.

## NEX-GDDP-CMIP6 (roadmap, v0.3)

NASA Earth Exchange Global Daily Downscaled Projections, CMIP6
ensemble. Statistically downscaled climate projections at 0.25°
resolution to 2100 under multiple SSP scenarios. Will support
projection-vs-observation comparisons and forward indicator runs
under specified scenarios; not used for any "forecast" framing.

*Reference:* Thrasher et al. (2022), *Scientific Data* 9, 262.
