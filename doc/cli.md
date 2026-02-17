# CLI reference

All commands take `--log-level {DEBUG,INFO,WARNING,ERROR}` and
`--json-log/--text-log` on the root.

## anga fetch

Pull a subset of a dataset into local storage. v0.5 requires
`--source-override` pointing at a local NetCDF/Zarr replica;
network fetch is roadmap.

```bash
anga fetch chirps --region nakuru \
  --start 1991-01-01 --end 2024-12-31 \
  --source-override ~/data/chirps-v2.0.africa_daily.nc \
  --output ./data/chirps-nakuru.zarr
```

Other providers wire similarly under `anga fetch agera5`,
`anga fetch tamsat`, `anga fetch nex-gddp` (added in v0.6 alongside
their network paths).

## anga compute spi

Standardised Precipitation Index. Wraps
`xclim.indices.standardized_precipitation_index` with a numpy
fallback when the xclim signature drifts.

```bash
anga compute spi --input chirps.zarr --window 3 \
  --season long-rains --baseline 1991-2020 \
  --output spi3-longrains.nc
```

## anga compute onset

Camberlin-Okoola operational onset detection. Defaults to 20mm in
3 days followed by no >=10-day dry spell in the next 30 days.

```bash
anga compute onset --input chirps.zarr \
  --season long-rains \
  --output onset.nc
```

## anga rollup

Spatial aggregation over named admin regions.

```bash
anga rollup --input spi3.nc --scope nakuru-wards \
  --reducer mean --output spi3-by-ward.nc
```

`--scope` accepts `nakuru-wards` and `nakuru-county` in v0.5.

## anga classify

KMD seven-band SPI severity or NDMA four-phase drought categorisation.

```bash
anga classify --input spi3.nc --scheme kmd --summary \
  --output severity.nc
```

`--summary` prints the {label: fraction} breakdown to stdout.

## anga trend

Per-cell linear trend (annual or seasonally-windowed).

```bash
anga trend --input chirps.zarr --reducer sum \
  --season long-rains --output trend.nc
```

Output is a single value per spatial cell: the OLS slope of the
annual aggregate against year, in units of (input units)/year.

## anga quintile

Tercile or quintile climate classification. Useful for FEWS NET-style
outlook maps and KMD seasonal review tables.

```bash
anga quintile --input seasonal-totals.nc --scheme tercile \
  --baseline 1991-2020 --output tercile.nc
```

## anga seasons list

Show the seasonal catalog (KMD bimodal, ICPAC GHA, regional variants).
`--format json` for machine consumption.
