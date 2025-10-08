from __future__ import annotations

import io
import json
import logging

from anga_grid.logging import configure, get_logger


def test_get_logger_returns_namespaced() -> None:
    log = get_logger("subsystem")
    assert log.name == "anga_grid.subsystem"


def test_configure_idempotent() -> None:
    configure()
    handlers_before = list(logging.getLogger("anga_grid").handlers)
    configure()
    handlers_after = list(logging.getLogger("anga_grid").handlers)
    assert len(handlers_after) == len(handlers_before)


def test_json_formatter_emits_json_with_extras(monkeypatch: object) -> None:
    log = logging.Logger("anga_grid.tests.json")
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    from anga_grid.logging import _JSONFormatter

    handler.setFormatter(_JSONFormatter())
    log.addHandler(handler)
    log.warning("boom", extra={"job_id": "abc-123"})
    handler.flush()
    payload = json.loads(buf.getvalue().strip())
    assert payload["msg"] == "boom"
    assert payload["level"] == "WARNING"
    assert payload["job_id"] == "abc-123"


def test_json_formatter_includes_exception() -> None:
    from anga_grid.logging import _JSONFormatter

    log = logging.Logger("anga_grid.tests.exc")
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(_JSONFormatter())
    log.addHandler(handler)
    try:
        raise RuntimeError("nope")
    except RuntimeError:
        log.exception("failed")
    handler.flush()
    payload = json.loads(buf.getvalue().strip())
    assert "RuntimeError" in payload["exc"]
