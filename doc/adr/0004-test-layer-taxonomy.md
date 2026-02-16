# ADR 0004: Eight test layers, one pytest marker per layer

**Status:** Accepted
**Date:** 2026-02-16

## Context

The test tree has grown to ~400 tests and was at risk of becoming a
single undifferentiated pile. Different consumers want to run
different subsets:

- CI wants the full sweep
- A pre-commit hook wants the smoke layer in <500ms
- An operational deployment check wants smoke + roundtrip
- A performance regression CI job wants only the bounded-time tests

A single `tests/` flat directory doesn't support that without ugly
filename grepping or fragile `--keyword` matching.

## Decision

The test tree is partitioned into eight directories, each with a
single matching pytest marker:

```
tests/unit/         -m unit         (the default; no marker required)
tests/providers/    -m providers    (per-dataset reader integration)
tests/integration/  -m integration  (CLI and cross-module flows)
tests/property/     -m property     (hypothesis-driven invariants)
tests/smoke/        -m smoke        (import + wiring sanity, <500ms total)
tests/regression/   -m regression   (pinned past-bug behaviours)
tests/performance/  -m performance  (bounded-time benchmark checks)
tests/roundtrip/    -m roundtrip    (write-then-read symmetry)
```

Markers are registered in `pyproject.toml`'s `tool.pytest.ini_options`.

## Consequences

**Positive:**

- `uv run pytest -m smoke` is the documented pre-commit fast loop.
- `uv run pytest -m "regression or roundtrip"` is the documented
  pre-deploy check.
- New test files are discoverable: a regression for past bug X
  goes in `tests/regression/test_regression_X.py`.
- The performance-test layer can fail-fast with bounded timing
  without polluting the unit suite.

**Negative:**

- Some tests legitimately fit in two layers (a provider integration
  test could double as a smoke test). We pick one home and don't
  cross-list; the rule of thumb is "what would I do if this test
  failed?" — the layer that matches the response wins.
- New contributors need to know about the layering. The CONTRIBUTING
  guide lists it; the directory-name discoverability covers the rest.

## Alternatives considered

**A. Single tests/ directory with marker-only categorisation.**
Rejected because file paths are easier to read at a glance than
marker decorators, and editors index file paths better.

**B. tests/{fast,slow}/ binary split.** Rejected because "fast vs
slow" doesn't map cleanly onto the operational use cases above.
Smoke tests are fast and serve a different purpose from unit tests
that happen to also be fast.
