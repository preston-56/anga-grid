# Data sources

Where each dataset comes from and how to obtain a local replica
suitable for `--source-override`.

## CHIRPS-2.0

- Distributor: Climate Hazards Center, UC Santa Barbara.
- Africa daily NetCDF browse:
  <https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/>
- Variable layout: per-month or per-year NetCDFs at 0.05° with
  `precip` (mm/day), `latitude`, `longitude`, `time` coords.
- Concatenation: anga-grid's CHIRPS provider opens a single file.
  For a multi-year analysis, pre-concatenate with `xr.open_mfdataset`
  and write a single NetCDF before pointing `--source-override` at it.
- Citation: Funk et al. (2015), *Scientific Data* 2, 150066.

## AgERA5

- Distributor: Copernicus Climate Change Service.
- Catalogue entry:
  <https://cds.climate.copernicus.eu/cdsapp#!/dataset/sis-agrometeorological-indicators>
- Access: requires a CDS account and the `cdsapi` client. Eight
  default variables (temp min/mean/max, precipitation_flux, solar
  radiation, vapour pressure, 10m wind, RH at 12h).
- Variable naming: Copernicus distributes Capital_Case names which
  the provider canonicalises to lower_snake_case.
- Citation: ECMWF/Copernicus AgERA5 user guide (current edition).

## TAMSAT-3.1

- Distributor: TAMSAT, University of Reading.
- Browse:
  <https://www.tamsat.org.uk/data/index.cgi>
- Variable layout: 0.0375° daily Africa-only NetCDF with `rfe` (or
  `rfe_filled`) in mm/day. Provider canonicalises to `precip`.
- Citation: Maidment et al. (2017), *Scientific Data* 4, 170063.

## NEX-GDDP-CMIP6

- Distributor: NASA Earth Exchange.
- Browse and S3 access:
  <https://www.nccs.nasa.gov/services/data-collections/land-based-products/nex-gddp-cmip6>
- Variable layout: per-model, per-scenario, per-variable, per-year
  NetCDFs at 0.25°. Tas/tasmin/tasmax in Kelvin, pr in kg/m^2/s -
  the provider auto-converts to Celsius and mm/day.
- Five scenarios catalogued: historical, ssp126, ssp245, ssp370,
  ssp585.
- Citation: Thrasher et al. (2022), *Scientific Data* 9, 262.

## Suggested local cache layout

```
~/data/
  chirps/
    chirps-v2.0.africa_daily.1991-2024.nc
  agera5/
    agera5-1991-2024-nakuru-bbox.zarr/
  tamsat/
    tamsat-v3.1-africa-1991-2024.nc
  nex-gddp/
    GFDL-ESM4-historical-1991-2014.nc
    GFDL-ESM4-ssp245-2015-2100.nc
```

Pointing `--source-override` at the per-dataset file/dir is the
expected pattern. The provider's `cache_dir` argument is currently
unused (reserved for v0.6 network fetch).
