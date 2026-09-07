from __future__ import annotations

import json
import re
import shutil
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from rtlreason.dataset import find_project_root, load_task, load_task_manifest
from rtlreason.verification.iverilog import run_iverilog


_OBLIGATION_FAILURE = re.compile(r"OBLIGATION_FAIL:([A-Za-z0-9_]+)")


def load_regression_matrix(
    path: str | Path | None = None, *, project_root: str | Path | None = None
) -> dict[str, Any]:
    root = Path(project_root or find_project_root()).resolve()
    matrix_path = Path(path).resolve() if path else root / "datasets" / "mutations" / "regression_matrix.json"
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise ValueError("regression matrix must contain a cases array")
    manifest = load_task_manifest(project_root=root)
    layer_by_task = {item["task_id"]: item["layer"] for item in manifest["tasks"]}
    seen: set[str] = set()
    for index, case in enumerate(data["cases"]):
        if not isinstance(case, dict):
            raise ValueError(f"regression case {index} must be an object")
        required = {"id", "task_id", "rtl", "mutation_class", "expected_obligations", "expected_simulation"}
        missing = required - set(case)
        if missing:
            raise ValueError(f"regression case {index} misses {sorted(missing)}")
        case_id = str(case["id"])
        if case_id in seen:
            raise ValueError(f"duplicate regression case id {case_id}")
        seen.add(case_id)
        task_id = str(case["task_id"])
        if task_id not in layer_by_task:
            raise ValueError(f"regression case {case_id} references unknown task {task_id}")
        task = load_task(task_id, project_root=root)
        rtl = (root / str(case["rtl"])).resolve()
        if not rtl.is_relative_to(root) or not rtl.is_file():
            raise ValueError(f"regression case {case_id} RTL is missing or outside project")
        obligations = case["expected_obligations"]
        if not isinstance(obligations, list) or not obligations:
            raise ValueError(f"regression case {case_id} needs expected obligations")
        unknown = set(map(str, obligations)) - task.obligation_ids
        if unknown:
            raise ValueError(f"regression case {case_id} has unknown obligations {sorted(unknown)}")
        if case["expected_simulation"] != "fail":
            raise ValueError(f"regression case {case_id} must expect simulation failure")
    return data


def summarize_regression_matrix(
    matrix: dict[str, Any], *, project_root: str | Path | None = None
) -> dict[str, Any]:
    root = Path(project_root or find_project_root()).resolve()
    manifest = load_task_manifest(project_root=root)
    layer_by_task = {item["task_id"]: item["layer"] for item in manifest["tasks"]}
    cases = matrix["cases"]
    covered = {str(case["task_id"]) for case in cases}
    return {
        "schema_version": matrix.get("schema_version"),
        "matrix_version": matrix.get("matrix_version"),
        "case_count": len(cases),
        "task_coverage": len(covered),
        "manifest_task_count": len(layer_by_task),
        "uncovered_tasks": sorted(set(layer_by_task) - covered),
        "by_layer": dict(sorted(Counter(layer_by_task[str(case["task_id"])] for case in cases).items())),
        "by_mutation_class": dict(sorted(Counter(str(case["mutation_class"]) for case in cases).items())),
        "gold_status": "controlled_not_independent_gold"
    }


def run_regression_matrix(
    matrix: dict[str, Any], *, project_root: str | Path | None = None
) -> dict[str, Any]:
    """Run known-bad RTL and require every fault to be detected by trusted simulation."""
    root = Path(project_root or find_project_root()).resolve()
    results: list[dict[str, Any]] = []
    artifact_root = root / "tests" / "work" / f"regression-{uuid.uuid4().hex}"
    artifact_root.mkdir(parents=True, exist_ok=False)
    try:
        for case in matrix["cases"]:
            task = load_task(str(case["task_id"]), project_root=root)
            simulation = task.verification["simulation"]
            result = run_iverilog(
                root / str(case["rtl"]),
                task.root / str(simulation["testbench"]),
                top=str(simulation["top"]),
                vcd_name=simulation.get("vcd"),
                artifact_dir=artifact_root / str(case["id"]),
            )
            observed = sorted(set(_OBLIGATION_FAILURE.findall(result.output)))
            expected = list(map(str, case["expected_obligations"]))
            detected = bool(
                result.available
                and result.passed is False
                and set(observed).intersection(expected)
            )
            results.append(
                {
                    "id": case["id"],
                    "task_id": task.task_id,
                    "detected": detected,
                    "simulation_available": result.available,
                    "simulation_passed": result.passed,
                    "expected_obligations": expected,
                    "observed_failed_obligations": observed,
                }
            )
    finally:
        shutil.rmtree(artifact_root, ignore_errors=True)
    return {
        "valid": all(item["detected"] for item in results),
        "case_count": len(results),
        "detected_count": sum(bool(item["detected"]) for item in results),
        "failures": [item for item in results if not item["detected"]],
        "results": results,
        "gold_status": "controlled_not_independent_gold",
    }
