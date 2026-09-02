from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


STAGE_ORDER = {f"S{index}": index for index in range(1, 6)}


@dataclass(frozen=True)
class BehavioralObligation:
    id: str
    statement: str
    category: str = "behavior"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BehavioralObligation":
        return cls(
            id=str(data["id"]),
            statement=str(data["statement"]),
            category=str(data.get("category", "behavior")),
        )


@dataclass(frozen=True)
class ProcessItem:
    id: str
    stage: str
    claim: str
    maps_to: tuple[str, ...] = ()
    claimed_dependencies: tuple[str, ...] = ()
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    rtl_blocks: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, stage: str, data: dict[str, Any]) -> "ProcessItem":
        return cls(
            id=str(data["id"]),
            stage=stage,
            claim=str(data.get("claim", "")).strip(),
            maps_to=tuple(map(str, data.get("maps_to", []))),
            claimed_dependencies=tuple(
                map(str, data.get("claimed_dependencies", []))
            ),
            reads=tuple(map(str, data.get("reads", []))),
            writes=tuple(map(str, data.get("writes", []))),
            rtl_blocks=tuple(map(str, data.get("rtl_blocks", []))),
        )


@dataclass(frozen=True)
class ProcessStage:
    id: str
    title: str
    items: tuple[ProcessItem, ...]


@dataclass(frozen=True)
class RTLArtifact:
    language: str
    module_name: str
    code: str


@dataclass(frozen=True)
class ProcessArtifact:
    task_id: str
    architecture_summary: str
    stages: tuple[ProcessStage, ...]
    rtl: RTLArtifact
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessArtifact":
        stages: list[ProcessStage] = []
        for stage_data in data.get("stages", []):
            stage_id = str(stage_data["id"])
            stages.append(
                ProcessStage(
                    id=stage_id,
                    title=str(stage_data.get("title", "")),
                    items=tuple(
                        ProcessItem.from_dict(stage_id, item)
                        for item in stage_data.get("items", [])
                    ),
                )
            )
        rtl_data = data.get("rtl", {})
        return cls(
            task_id=str(data.get("task_id", "")),
            architecture_summary=str(data.get("architecture_summary", "")),
            stages=tuple(stages),
            rtl=RTLArtifact(
                language=str(rtl_data.get("language", "systemverilog")),
                module_name=str(rtl_data.get("module_name", "")),
                code=str(rtl_data.get("code", "")),
            ),
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_json(cls, text: str) -> "ProcessArtifact":
        return cls.from_dict(json.loads(text))

    @property
    def items(self) -> tuple[ProcessItem, ...]:
        return tuple(item for stage in self.stages for item in stage.items)

    def item_map(self) -> dict[str, ProcessItem]:
        return {item.id: item for item in self.items}

    def item_positions(self) -> dict[str, tuple[int, int]]:
        """Return total process order as ``(stage order, item order)``."""
        positions: dict[str, tuple[int, int]] = {}
        for stage in self.stages:
            stage_order = STAGE_ORDER.get(stage.id, len(STAGE_ORDER) + 1)
            for item_order, item in enumerate(stage.items):
                positions.setdefault(item.id, (stage_order, item_order))
        return positions

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskAssets:
    task_id: str
    root: Path
    problem: str
    interface_semantics: dict[str, Any]
    obligations: tuple[BehavioralObligation, ...]
    difficulty: dict[str, Any]
    provenance: dict[str, Any]
    verification: dict[str, Any]
    error_taxonomy: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def obligation_ids(self) -> set[str]:
        return {obligation.id for obligation in self.obligations}


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[str, ...]
    edges: tuple[DependencyEdge, ...]

    def parents_of(self, node: str) -> set[str]:
        return {edge.source for edge in self.edges if edge.target == node}

    def ancestors_of(self, node: str) -> set[str]:
        ancestors: set[str] = set()
        pending = list(self.parents_of(node))
        while pending:
            parent = pending.pop()
            if parent in ancestors:
                continue
            ancestors.add(parent)
            pending.extend(self.parents_of(parent))
        return ancestors

    @property
    def digest(self) -> str:
        canonical = {
            "nodes": sorted(self.nodes),
            "edges": sorted(
                (edge.source, edge.target, sorted(edge.reasons)) for edge in self.edges
            ),
        }
        payload = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ItemAssessment:
    item_id: str
    status: str
    error_type_l1: str | None = None
    error_type_l2: str | None = None
    explanation: str = ""
    confidence: float = 0.0

    @property
    def is_error(self) -> bool:
        return self.status == "incorrect"


@dataclass(frozen=True)
class VerificationEvidence:
    id: str
    source: str
    status: str
    obligations: tuple[str, ...]
    summary: str
    cycle: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_failure(self) -> bool:
        return self.status == "fail"


@dataclass(frozen=True)
class AttributionResult:
    process_correct: bool | None
    root_errors: tuple[str, ...]
    earliest_error_stage: str | None
    primary_error_item: str | None
    violated_obligations: tuple[str, ...]
    graph_digest: str


def stage_of_item_id(item_id: str) -> str:
    prefix = item_id.split(".", 1)[0]
    return prefix if prefix in STAGE_ORDER else "S5"


def unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
