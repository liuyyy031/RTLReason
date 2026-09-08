from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from rtlreason.models import BehavioralObligation, TaskAssets


class DatasetError(RuntimeError):
    pass


def find_project_root(start: str | Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "datasets"
        ).is_dir():
            return candidate
    raise DatasetError("Could not find RTLReason project root")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"Could not load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DatasetError(f"Expected an object in {path}")
    return value


def load_task(
    task_id: str, *, project_root: str | Path | None = None
) -> TaskAssets:
    root = (
        Path(project_root).resolve() if project_root is not None else find_project_root()
    )
    task_root = root / "datasets" / "tasks" / task_id
    if not task_root.is_dir():
        raise DatasetError(f"Unknown task: {task_id}")

    problem = (task_root / "problem.md").read_text(encoding="utf-8")
    interface = _load_json(task_root / "interface_semantics.json")
    difficulty = _load_json(task_root / "difficulty.json")
    provenance = _load_json(task_root / "provenance.json")
    verification = _load_json(task_root / "verification.json")
    taxonomy_path = root / "datasets" / "error_taxonomy.yaml"
    taxonomy_document = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    taxonomy = {
        str(level): tuple(map(str, subtypes))
        for level, subtypes in taxonomy_document.get("levels", {}).items()
    }
    if not taxonomy:
        raise DatasetError("error taxonomy is empty")
    obligations_path = task_root / "behavioral_obligations.yaml"
    raw_obligations = yaml.safe_load(obligations_path.read_text(encoding="utf-8"))
    obligations = tuple(
        BehavioralObligation.from_dict(item)
        for item in raw_obligations.get("obligations", [])
    )
    if not obligations:
        raise DatasetError(f"Task {task_id} has no behavioral obligations")
    if interface.get("task_id") != task_id:
        raise DatasetError("interface semantics task_id does not match directory")
    obligation_ids = [item.id for item in obligations]
    if len(obligation_ids) != len(set(obligation_ids)):
        raise DatasetError(f"Task {task_id} has duplicate obligation IDs")
    required_interface_sections = {"reset", "ports", "acceptance"}
    has_clock_definition = "clock" in interface or "clocks" in interface
    if not has_clock_definition:
        required_interface_sections.add("clock")
    missing_sections = required_interface_sections - set(interface)
    if missing_sections:
        raise DatasetError(
            f"Task {task_id} interface semantics misses {sorted(missing_sections)}"
        )
    for section in ("simulation", "formal"):
        if section not in verification:
            raise DatasetError(
                f"Task {task_id} verification config misses {section}"
            )
    simulation = verification["simulation"]
    formal = verification["formal"]
    for field in ("testbench", "top"):
        if not simulation.get(field):
            raise DatasetError(
                f"Task {task_id} simulation config misses {field}"
            )
    if formal.get("enabled", False):
        for field in ("harness", "top", "depth"):
            if not formal.get(field):
                raise DatasetError(
                    f"Task {task_id} formal config misses {field}"
                )
        unknown_formal = set(formal.get("obligations", [])) - set(obligation_ids)
        if unknown_formal:
            raise DatasetError(
                f"Task {task_id} formal config has unknown obligations "
                f"{sorted(unknown_formal)}"
            )
    for asset_name in filter(None, (simulation.get("testbench"), formal.get("harness"))):
        asset_path = (task_root / str(asset_name)).resolve()
        if not asset_path.is_relative_to(task_root.resolve()) or not asset_path.is_file():
            raise DatasetError(
                f"Task {task_id} verification asset is missing or outside task: "
                f"{asset_name}"
            )
    return TaskAssets(
        task_id=task_id,
        root=task_root,
        problem=problem,
        interface_semantics=interface,
        obligations=obligations,
        difficulty=difficulty,
        provenance=provenance,
        verification=verification,
        error_taxonomy=taxonomy,
    )
