from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any


def build_controlled_mutation(
    source_process: dict[str, Any],
    *,
    source_path: str | Path,
    replacement_rtl: str | None,
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Apply an explicit controlled mutation without creating Gold labels."""
    for field in (
        "mutation_id",
        "task_id",
        "target_item_id",
        "replacement_claim",
        "rationale",
        "expected_violations",
    ):
        if field not in spec:
            raise ValueError(f"mutation spec misses {field}")
    if source_process.get("task_id") != spec["task_id"]:
        raise ValueError("mutation task_id does not match source process")
    if not isinstance(spec["expected_violations"], list):
        raise ValueError("expected_violations must be an array")
    scope = str(spec.get("mutation_scope", "process_and_rtl"))
    if scope not in {"process_only", "process_and_rtl"}:
        raise ValueError(
            "mutation_scope must be process_only or process_and_rtl"
        )
    if scope == "process_and_rtl" and (
        replacement_rtl is None or not replacement_rtl.strip()
    ):
        raise ValueError("process_and_rtl mutation requires replacement RTL")

    mutated = copy.deepcopy(source_process)
    target_id = str(spec["target_item_id"])
    matches = []
    for stage in mutated.get("stages", []):
        for item in stage.get("items", []):
            if item.get("id") == target_id:
                matches.append(item)
    if len(matches) != 1:
        raise ValueError(
            f"target_item_id must match exactly one process item; found {len(matches)}"
        )
    original_claim = str(matches[0].get("claim", ""))
    replacement_claim = str(spec["replacement_claim"]).strip()
    if not replacement_claim or replacement_claim == original_claim:
        raise ValueError("replacement_claim must be non-empty and different")
    matches[0]["claim"] = replacement_claim

    rtl = mutated.get("rtl")
    if not isinstance(rtl, dict):
        raise ValueError("source process has no RTL object")
    if scope == "process_and_rtl":
        assert replacement_rtl is not None
        rtl["code"] = replacement_rtl.rstrip()
    source = Path(source_path).resolve()
    metadata = mutated.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("source process metadata must be an object")
    metadata["controlled_mutation"] = {
        "schema_version": "1.0",
        "mutation_id": str(spec["mutation_id"]),
        "mutation_scope": scope,
        "operator": (
            "replace_process_claim"
            if scope == "process_only"
            else "replace_process_claim_and_rtl"
        ),
        "source_process": source.as_posix(),
        "source_process_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "target_item_id": target_id,
        "original_claim": original_claim,
        "replacement_claim": replacement_claim,
        "rationale": str(spec["rationale"]),
        "expected_violations": list(map(str, spec["expected_violations"])),
    }
    return mutated
