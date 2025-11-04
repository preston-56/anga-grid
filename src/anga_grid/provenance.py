from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from anga_grid import __version__
from anga_grid.exceptions import ProvenanceError

if TYPE_CHECKING:
    import xarray as xr


@dataclass(frozen=True, slots=True)
class Step:
    operation: str
    parameters: dict[str, str] = field(default_factory=dict)
    timestamp: str = ""

    def serialize(self) -> str:
        params = ";".join(f"{k}={v}" for k, v in sorted(self.parameters.items()))
        return f"{self.timestamp}|{self.operation}|{params}"


@dataclass(slots=True)
class Manifest:
    source: str
    source_version: str = ""
    provider: str = ""
    subset_bbox: str = ""
    subset_time: str = ""
    retrieved_at: str = ""
    code_version: str = __version__
    caveats: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)

    def as_attrs(self) -> dict[str, str]:
        out: dict[str, str] = {
            "source": self.source,
            "code_version": self.code_version,
        }
        if self.source_version:
            out["source_version"] = self.source_version
        if self.provider:
            out["provider"] = self.provider
        if self.subset_bbox:
            out["subset_bbox"] = self.subset_bbox
        if self.subset_time:
            out["subset_time"] = self.subset_time
        if self.retrieved_at:
            out["retrieved_at"] = self.retrieved_at
        if self.caveats:
            out["caveats"] = "; ".join(self.caveats)
        if self.steps:
            out["history"] = " | ".join(s.serialize() for s in self.steps)
        return out

    def record(self, operation: str, **parameters: object) -> None:
        step = Step(
            operation=operation,
            parameters={k: str(v) for k, v in parameters.items()},
            timestamp=_now(),
        )
        self.steps.append(step)

    def add_caveat(self, message: str) -> None:
        if message and message not in self.caveats:
            self.caveats.append(message)

    @classmethod
    def from_attrs(cls, attrs: dict[str, object]) -> Manifest:
        if "source" not in attrs:
            raise ProvenanceError("missing required attr: source")
        m = cls(
            source=str(attrs["source"]),
            source_version=str(attrs.get("source_version", "")),
            provider=str(attrs.get("provider", "")),
            subset_bbox=str(attrs.get("subset_bbox", "")),
            subset_time=str(attrs.get("subset_time", "")),
            retrieved_at=str(attrs.get("retrieved_at", "")),
            code_version=str(attrs.get("code_version", __version__)),
        )
        raw_caveats = str(attrs.get("caveats", ""))
        if raw_caveats:
            m.caveats = [s.strip() for s in raw_caveats.split(";") if s.strip()]
        raw_history = str(attrs.get("history", ""))
        if raw_history:
            m.steps = [_step_from_serialized(s) for s in raw_history.split(" | ") if s]
        return m


def stamp(ds: xr.Dataset, manifest: Manifest) -> xr.Dataset:
    for key, value in manifest.as_attrs().items():
        ds.attrs[key] = value
    return ds


def read(ds: xr.Dataset) -> Manifest:
    return Manifest.from_attrs(dict(ds.attrs))


def merge(parent: Manifest, child: Manifest, operation: str) -> Manifest:
    merged = Manifest(
        source=child.source or parent.source,
        source_version=child.source_version or parent.source_version,
        provider=child.provider or parent.provider,
        subset_bbox=child.subset_bbox or parent.subset_bbox,
        subset_time=child.subset_time or parent.subset_time,
        retrieved_at=child.retrieved_at or parent.retrieved_at,
        code_version=child.code_version,
    )
    merged.caveats = list({*parent.caveats, *child.caveats})
    merged.steps = [*parent.steps, *child.steps]
    merged.record(operation, parent=parent.source, child=child.source)
    return merged


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _step_from_serialized(s: str) -> Step:
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
