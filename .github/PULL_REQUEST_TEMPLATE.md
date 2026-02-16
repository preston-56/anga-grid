## What changed

<!-- One sentence per logical change. If this PR bundles unrelated
     changes, please split it. -->

## Why it matters

<!-- The operational or analytical context. Who notices this and
     when? -->

## Local check

- [ ] `uv run ruff check src/ tests/` clean
- [ ] `uv run mypy src/` clean
- [ ] `uv run pytest --cov=anga_grid --cov-fail-under=80` passes
- [ ] If touching defaults / thresholds: citation included in
      commit body or doc/

## Provenance impact

- [ ] Output `Manifest` history records the new operation
- [ ] Caveats list updated if the change affects bias notes
- [ ] No-op if this PR doesn't touch indicator outputs

## Docs touched

- [ ] CHANGELOG updated
- [ ] README Quick Look still accurate
- [ ] doc/ files affected by the change updated
