---
name: Bug report
about: Report unexpected behaviour with a synthetic-data reproducer
labels: bug
---

## What you expected

<!-- What anga-grid was supposed to do. -->

## What actually happened

<!-- What it did instead. Include the exception trace if any. -->

## Reproducer

```python
from anga_grid.synthetic import synthetic_chirps
# minimal code that triggers the issue against synthetic data
```

## Environment

- anga-grid version:
- Python version:
- OS:
- xarray / xclim versions (from `uv pip list | grep -E 'xarray|xclim'`):

## Manifest contents

If the issue is about provenance / output attrs, paste the relevant
attrs of the offending dataset:

```
ds.attrs
```
