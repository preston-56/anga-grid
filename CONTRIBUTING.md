# Contributing to anga-grid

Thanks for considering a contribution. anga-grid is built for
operational use by East African agronomy and drought-monitoring
services, and the project particularly welcomes input from people
working in those domains.

## What we want

The most useful contributions, in order of impact:

1. **Domain corrections.** If a default season window, planting DOY,
   bias caveat, or threshold is wrong for the region you work in,
   open an issue with the correction and a citation we can ground
   the change in (KMD bulletin, ICPAC GHACOF statement, peer-reviewed
   paper, county-level extension service report).
2. **New regional cropping calendars.** The catalog in
   `src/anga_grid/cropping/calendar.py` covers Nakuru, Embu, Kisumu,
   Mombasa, and Garissa. Adding a calendar for your county requires
   planting DOY, days-to-flower / fill / harvest for each crop, and
   the season key it anchors to.
3. **New dataset providers.** If your operational pipeline uses a
   dataset we don't ship a reader for, the fastest path is a PR
   modelled on `providers/chirps/` or `providers/agera5/`.
4. **Bug reports.** Especially ones that include a synthetic-data
   reproducer using `anga_grid.synthetic.*`.

## What we don't want

- Generalisation to other regions at the cost of East African
  correctness. The library is opinionated for a reason; the
  README's "Not a global library" line is load-bearing.
- New abstractions for hypothetical future flexibility. Three
  similar lines is better than a premature abstraction.
- Changes to default thresholds without a citation. The defaults
  match operational KMD/ICPAC/NDMA practice; if you change them
  you owe an explanation.

## How to contribute

### Bug reports and feature requests

Open an issue on
[GitHub](https://github.com/preston-56/anga-grid/issues). Please
include:

- What you expected to happen
- What actually happened
- A minimal reproducer (synthetic input is fine; see
  `anga_grid.synthetic.*` for ready-made data builders)
- Your Python and `anga-grid` versions

### Code contributions

1. Fork the repo and create a topic branch.
2. Set up a dev environment: `uv sync --extra dev`.
3. Make your change with tests. Every new module needs a
   corresponding `tests/unit/test_*.py`.
4. Run the full local check before opening a PR:

   ```bash
   uv run ruff check src/ tests/
   uv run mypy src/
   uv run pytest --cov=anga_grid --cov-fail-under=80
   ```

5. Open a PR with a description of *why* the change matters
   (operational context > technical motivation).

### Commit conventions

- Use a leading scope tag: `feat(providers): ...`, `fix(rollup): ...`,
  `doc: ...`, `test: ...`, `ci: ...`, `refactor(season): ...`.
- Keep each commit to one logical change. The history reads better
  when each commit's diff matches one claim in its subject line.
- Don't bundle code + tests + docs into one giant commit when they
  can land separately.

## Code style

- `ruff check` and `mypy --strict` must pass; CI enforces this.
- Default to no comments. Only add one when the *why* of the code is
  non-obvious. Avoid godoc-style `// FuncName does X` blocks on every
  function; well-named identifiers should carry the load.
- New modules go inside themed sub-packages, not flat at the root.
  See `src/anga_grid/correction/` and `src/anga_grid/severity/` for
  the two-file split pattern.
- Public API symbols are exported via the package `__init__.py`
  re-exports. Internal helpers stay underscore-prefixed.

## Testing layers

The test tree has eight layers, each with its own pytest marker:

- `tests/unit/` — per-module behavioural tests
- `tests/providers/` — per-provider integration against synthetic data
- `tests/integration/` — cross-module end-to-end (CLI etc.)
- `tests/property/` — hypothesis-driven invariants
- `tests/smoke/` — minimum import / wiring sanity
- `tests/regression/` — pinned past-bug behaviours
- `tests/performance/` — bounded-time benchmark checks
- `tests/roundtrip/` — write-then-read symmetry tests

When adding a substantive new module, please touch the relevant
layer(s) — at minimum `tests/unit/` and `tests/smoke/`.

## License

By contributing you agree your changes are released under the MIT
License (see `LICENSE`).
