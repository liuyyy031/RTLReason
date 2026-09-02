from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rtlreason.evaluator.metrics import ValidationCase, compute_core_metrics
from rtlreason.models import stage_of_item_id


BASELINES = ("eda_only", "semantic_only", "full")


def load_gold_records(path: str | Path) -> list[dict[str, Any]]:
    """Load one Gold record, a list/bundle, or every JSON record in a directory."""
    source = Path(path)
    if source.is_dir():
        records: list[dict[str, Any]] = []
        for item in sorted(source.rglob("*.json")):
            records.extend(load_gold_records(item))
        if not records:
            raise ValueError(f"no Gold JSON records found in {source}")
        return records
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and isinstance(data.get("cases"), list):
        records = data["cases"]
    elif isinstance(data, dict):
        records = [data]
    else:
        raise ValueError("Gold input must be a record, list, bundle, or directory")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Gold record {index} must be an object")
        for field in (
            "case_id",
            "gold_rtl_correct",
            "gold_process_correct",
            "annotation",
        ):
            if field not in record:
                raise ValueError(f"Gold record {index} misses {field}")
        annotation = record["annotation"]
        if (
            not isinstance(annotation, dict)
            or annotation.get("independent_of_tested_model") is not True
        ):
            raise ValueError(
                f"Gold record {index} is not independently annotated"
            )
    return records


def _copy_gold(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": record["case_id"],
        "gold_rtl_correct": record["gold_rtl_correct"],
        "gold_process_correct": record["gold_process_correct"],
        "gold_first_error_stage": record.get("gold_first_error_stage"),
        "gold_root_error": record.get("gold_root_error"),
        "gold_error_type_l1": record.get("gold_error_type_l1"),
        "gold_parent_dependency": record.get("gold_parent_dependency", []),
        "gold_affected_obligation": record.get(
            "gold_affected_obligation", []
        ),
    }


def _semantic_prediction(record: dict[str, Any]) -> dict[str, Any]:
    prediction = record.get("evaluator_prediction", {})
    if not isinstance(prediction, dict):
        prediction = {}
    focus = [
        item
        for item in prediction.get("review_focus", [])
        if isinstance(item, dict)
    ]
    incorrect = [item for item in focus if item.get("status") == "incorrect"]
    unknown = [item for item in focus if item.get("status") == "unknown"]

    process = record.get("candidate_process", {})
    order: dict[str, int] = {}
    if isinstance(process, dict):
        for stage in process.get("stages", []):
            if not isinstance(stage, dict):
                continue
            for item in stage.get("items", []):
                if isinstance(item, dict) and "id" in item:
                    order.setdefault(str(item["id"]), len(order))
    incorrect.sort(key=lambda item: order.get(str(item.get("item_id")), 10**9))
    primary = incorrect[0] if incorrect else None
    primary_id = str(primary["item_id"]) if primary else None
    process_correct: bool | None
    if incorrect:
        process_correct = False
    elif unknown:
        process_correct = None
    else:
        process_correct = True
    return {
        "predicted_process_correct": process_correct,
        "predicted_first_error_stage": (
            stage_of_item_id(primary_id) if primary_id else None
        ),
        "predicted_root_error": primary_id,
        "predicted_error_type_l1": (
            primary.get("error_type_l1") if primary else None
        ),
        "predicted_parent_dependency": [],
        "predicted_affected_obligations": [],
    }


def apply_baseline(
    record: dict[str, Any], baseline: str
) -> dict[str, Any]:
    if baseline not in BASELINES:
        raise ValueError(f"unknown baseline {baseline!r}; choose from {BASELINES}")
    result = _copy_gold(record)
    if baseline == "full":
        for field in (
            "predicted_rtl_correct",
            "predicted_process_correct",
            "predicted_first_error_stage",
            "predicted_root_error",
            "predicted_error_type_l1",
            "predicted_parent_dependency",
            "predicted_affected_obligations",
        ):
            result[field] = record.get(field)
        return result

    rtl_prediction = record.get("predicted_rtl_correct")
    result["predicted_rtl_correct"] = rtl_prediction
    if baseline == "eda_only":
        result.update(
            {
                "predicted_process_correct": rtl_prediction,
                "predicted_first_error_stage": None,
                "predicted_root_error": None,
                "predicted_error_type_l1": None,
                "predicted_parent_dependency": [],
                "predicted_affected_obligations": record.get(
                    "predicted_affected_obligations", []
                ),
            }
        )
    else:
        result.update(_semantic_prediction(record))
    return result


def compare_baselines(
    records: list[dict[str, Any]],
    baselines: tuple[str, ...] = BASELINES,
) -> dict[str, Any]:
    if not records:
        raise ValueError("at least one Gold record is required")
    return {
        baseline: compute_core_metrics(
            [
                ValidationCase.from_dict(apply_baseline(record, baseline))
                for record in records
            ]
        )
        for baseline in baselines
    }


def compare_baselines_stratified(
    records: list[dict[str, Any]],
    layer_by_task: dict[str, str],
    baselines: tuple[str, ...] = BASELINES,
) -> dict[str, Any]:
    """Report overall and layer-specific results under one frozen manifest."""
    unknown = sorted(
        {
            str(record.get("task_id", ""))
            for record in records
            if str(record.get("task_id", "")) not in layer_by_task
        }
    )
    if unknown:
        raise ValueError(f"Gold records have tasks outside the manifest: {unknown}")
    by_layer: dict[str, Any] = {}
    for layer in ("basic", "intermediate", "hard"):
        subset = [
            record
            for record in records
            if layer_by_task[str(record["task_id"])] == layer
        ]
        by_layer[layer] = {
            "case_count": len(subset),
            "metrics": compare_baselines(subset, baselines) if subset else None,
        }
    return {
        "case_count": len(records),
        "overall": compare_baselines(records, baselines),
        "by_layer": by_layer,
    }
