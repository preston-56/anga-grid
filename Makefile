.PHONY: help install test lint typecheck cover clean

help:
	@echo "make install     - uv sync with dev extras"
	@echo "make test        - run the full pytest suite"
	@echo "make lint        - ruff check"
	@echo "make typecheck   - mypy on src/"
	@echo "make cover       - pytest with coverage report"
	@echo "make smoke       - just the smoke test layer"
	@echo "make clean       - remove caches and build artifacts"

install:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/

cover:
	uv run pytest --cov=anga_grid --cov-report=term-missing --cov-fail-under=80

smoke:
	uv run pytest -m smoke -q

regression:
	uv run pytest -m regression -q

performance:
	uv run pytest -m performance -q

roundtrip:
	uv run pytest -m roundtrip -q

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov .hypothesis
	find . -type d -name __pycache__ -exec rm -rf {} +
