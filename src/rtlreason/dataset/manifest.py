from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from rtlreason.dataset.loader import DatasetError, find_project_root


LAYERS = ("basic", "intermediate", "hard")


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
    asset_ids = sorted(item.name for item in task_root.iterdir() if item.is_dir())
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
