from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from rtlreason.dataset.loader import DatasetError, find_project_root


LAYERS = ("basic", "intermediate", "hard")
STAGED_ADMISSION_STATUSES = {"planned", "assets_complete", "independently_reviewed"}


def _admitted_asset_ids(task_root: Path) -> list[str]:
    admitted: list[str] = []
    for task_dir in task_root.iterdir():
        if not task_dir.is_dir():
            continue
        admission_path = task_dir / "admission.json"
        if not admission_path.is_file():
            # Legacy trusted tasks predate explicit admission records.
            admitted.append(task_dir.name)
            continue
        try:
            admission = json.loads(admission_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DatasetError(
                f"Could not load task admission record {admission_path}: {exc}"
            ) from exc
        if not isinstance(admission, dict):
            raise DatasetError(f"Task admission record must be an object: {admission_path}")
        status = admission.get("status")
        if status == "trusted_frozen":
            admitted.append(task_dir.name)
        elif status not in STAGED_ADMISSION_STATUSES:
            raise DatasetError(
                f"Task {task_dir.name} has invalid admission status: {status!r}"
            )
    return sorted(admitted)


def load_task_manifest(
    *, project_root: str | Path | None = None
) -> dict[str, Any]:
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else find_project_root()
    )
    path = root / "datasets" / "task_manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"Could not load task manifest: {exc}") from exc
    entries = manifest.get("tasks") if isinstance(manifest, dict) else None
    if not isinstance(entries, list) or not entries:
        raise DatasetError("task manifest must contain a non-empty tasks list")
    ids: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise DatasetError(f"task manifest entry {index} must be an object")
        task_id = str(entry.get("task_id", ""))
        layer = entry.get("layer")
        family = str(entry.get("family", ""))
        if not task_id or layer not in LAYERS or not family:
            raise DatasetError(
                f"task manifest entry {index} needs task_id, valid layer, family"
            )
        ids.append(task_id)
    if len(ids) != len(set(ids)):
        raise DatasetError("task manifest contains duplicate task IDs")
    task_root = root / "datasets" / "tasks"
    asset_ids = _admitted_asset_ids(task_root)
    if sorted(ids) != asset_ids:
        missing = sorted(set(asset_ids) - set(ids))
        unknown = sorted(set(ids) - set(asset_ids))
        raise DatasetError(
            f"task manifest mismatch: missing={missing}, unknown={unknown}"
        )
    return manifest


def summarize_task_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    tasks = manifest["tasks"]
    return {
        "schema_version": manifest.get("schema_version"),
        "manifest_version": manifest.get("manifest_version"),
        "task_count": len(tasks),
        "by_layer": dict(sorted(Counter(item["layer"] for item in tasks).items())),
        "by_family": dict(
            sorted(Counter(item["family"] for item in tasks).items())
        ),
        "tasks": tasks,
    }
