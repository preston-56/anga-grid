# Operations

How to run anga-grid in an operational drought-monitoring context.

## Suggested deployment shape

For a county-level monthly drought bulletin pipeline:

1. **Daily ingest**. Pull yesterday's CHIRPS and AgERA5 NetCDFs into
   a local cache (cron + curl or rclone, outside anga-grid scope).
2. **Monthly aggregation**. On the 1st of each month, compute SPI-1,
   SPI-3, SPI-6 against the previous month's data with a fixed
   1991-2020 climatological baseline.
3. **Classification**. Pipe each SPI output through `anga classify`
   for the KMD seven-band map and `anga quintile --scheme tercile`
   for the FEWS NET-style outlook.
4. **Spatial rollup**. `anga rollup --scope nakuru-wards` (or your
   own AdminRegion catalog) to get ward-level summaries for the
   bulletin tables.
5. **Bulletin assembly**. Render the resulting NetCDFs into the
   bulletin format your service uses (outside anga-grid scope; many
   services use QGIS or matplotlib templates).

## Reproducibility contract

Every output anga-grid produces carries a `Manifest` in its xarray
attrs. The manifest contains:

- `source` and `source_version` (e.g. `CHIRPS-2.0`, `2.0`)
- `provider` (the reader implementation that produced the input)
- `subset_bbox` and `subset_time`
- `retrieved_at` (UTC ISO timestamp at fetch time)
- `code_version` (the anga-grid version that ran the computation)
- `caveats` (semicolon-separated list of provider-specific bias notes)
- `history` (pipe-separated list of `timestamp|operation|params`
  entries, one per indicator/transform applied)

When a downstream consumer questions a number in the bulletin, the
manifest is the audit trail: it encodes the source dataset version,
the spatial/temporal subset, the indicator parameters, and the
sequence of transforms.

## Configuration

anga-grid does not have a config file. All run-time parameters are
either CLI flags or constructor arguments. This is deliberate: an
operational pipeline that depends on a YAML config is one
out-of-band edit away from producing wrong outputs without anyone
noticing.

If you need to share a setup across many invocations, write a small
shell script or Python wrapper that pins the parameters explicitly.
We do not plan to add config-file support.

## Failure modes to expect

- **Empty subset on time**: the CHIRPS/AgERA5/TAMSAT readers raise
  `ProviderError("subset is empty along time")` when the requested
  date range falls outside what's in your local replica. Log this
  and alert; it usually indicates an ingest pipeline problem.
- **Missing variable**: if your local AgERA5 cache is missing the
  variables a downstream indicator needs, the provider raises
  `ProviderError` with the missing-variable list. Pipe this into
  your monitoring.
- **Network fetch attempt**: in v0.5, calling any provider's
  `fetch()` without `source_override` raises a `ProviderError` with
  "not wired" in the message. The network path is roadmap.

## Observability

The library uses the stdlib `logging` module under the
`anga_grid.*` namespace. Configure once at process start:

```python
from anga_grid.logging import configure
configure(level=logging.INFO, json_output=True)
```

`json_output=True` emits one JSON record per log line, suitable for
log aggregation systems (Loki, Elasticsearch, Cloudwatch).
