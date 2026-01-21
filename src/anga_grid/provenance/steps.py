from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from anga_grid.exceptions import ProvenanceError


@dataclass(frozen=True, slots=True)
class Step:
    operation: str
    parameters: dict[str, str] = field(default_factory=dict)
    timestamp: str = ""

    def serialize(self) -> str:
        params = ";".join(f"{k}={v}" for k, v in sorted(self.parameters.items()))
        return f"{self.timestamp}|{self.operation}|{params}"


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def step_from_serialized(s: str) -> Step:
    parts = s.split("|", 2)
    if len(parts) != 3:
        raise ProvenanceError(f"bad history entry: {s!r}")
    ts, op, params = parts
    params_dict: dict[str, str] = {}
    for kv in params.split(";"):
        if not kv:
            continue
        if "=" not in kv:
            raise ProvenanceError(f"bad parameter token: {kv!r}")
        key, value = kv.split("=", 1)
        params_dict[key] = value
    return Step(operation=op, parameters=params_dict, timestamp=ts)
