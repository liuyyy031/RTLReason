from __future__ import annotations

import hashlib
import copy
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_adjudication_candidate(
    *,
    case_id: str,
    task_id: str,
    run_dir: str | Path,
    project_root: str | Path,
) -> dict[str, object]:
    """Package a real run for human review without creating Gold labels."""
    root = Path(project_root).resolve()
    run = Path(run_dir).resolve()
    process_path = run / "process.json"
    evidence_path = run / "evidence.json"
    report_path = run / "report.json"
    process = _read_json(process_path)
    evidence = _read_json(evidence_path)
    report = _read_json(report_path)
    if not isinstance(process, dict) or not isinstance(report, dict):
        raise ValueError("process.json and report.json must contain JSON objects")
    if process.get("task_id") != task_id or report.get("task_id") != task_id:
        raise ValueError("run task_id does not match queue-case task_id")

    try:
        source_run = run.relative_to(root).as_posix()
    except ValueError:
        source_run = run.as_posix()
    prediction = _prediction_from_report(report)
    return {
        "schema_version": "1.0",
        "case_id": case_id,
        "task_id": task_id,
        "candidate_origin": (
            "controlled_mutation"
            if report.get("candidate_generation", {}).get("origin")
            == "controlled_mutation"
            else "real_hy3"
        ),
        "source_run": source_run,
        "source_hashes": {
            "process_sha256": _sha256(process_path),
            "evidence_sha256": _sha256(evidence_path),
            "report_sha256": _sha256(report_path),
        },
        "candidate_process": process,
        "trusted_evidence": evidence,
        "evaluator_prediction": prediction,
        "api_provenance": {
            "candidate_generation": report.get("candidate_generation", {}),
            "semantic_evaluator": report.get("semantic_evaluator", {}),
        },
        "adjudication": {
            "status": "pending_human",
            "independent_gold_required": True,
            "gold_fields_present": False,
            "guideline_version": "1.0",
        },
    }


def _prediction_from_report(report: dict[str, Any]) -> dict[str, Any]:
    assessments = list(report.get("assessments", []))
    review_focus = [
        item
        for item in assessments
        if isinstance(item, dict) and item.get("status") != "correct"
    ]
    verification = report.get("verification", {})
    attribution = report.get("attribution", {})
    if not isinstance(verification, dict) or not isinstance(attribution, dict):
        raise ValueError("report verification and attribution must be objects")
    return {
        "rtl_correct": verification.get("final_rtl_correct"),
        "process_correct": attribution.get("process_correct"),
        "root_errors": attribution.get("root_errors", []),
        "earliest_error_stage": attribution.get("earliest_error_stage"),
        "primary_error_item": attribution.get("primary_error_item"),
        "violated_obligations": attribution.get("violated_obligations", []),
        "review_focus": review_focus,
        "dependency_graph": report.get("dependency_graph", {}),
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sensitive_paths(value: object, prefix: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if key in {
                "evaluator_prediction",
                "api_provenance",
                "controlled_mutation",
            } or key.startswith("gold_"):
                paths.append(child_path)
            paths.extend(_sensitive_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_sensitive_paths(child, f"{prefix}[{index}]"))
    return paths


def audit_review_pool(
    candidate_dir: str | Path, review_packet_dir: str | Path
) -> dict[str, object]:
    """Check candidate/packet parity and reviewer-packet information hygiene."""
    candidates_root = Path(candidate_dir)
    packets_root = Path(review_packet_dir)
    candidates = {
        path.stem: path for path in sorted(candidates_root.glob("*.json"))
    }
    packets = {
        path.name.removesuffix(".review.json"): path
        for path in sorted(packets_root.glob("*.review.json"))
    }
    issues: list[dict[str, str]] = []

    for case_id in sorted(candidates.keys() - packets.keys()):
        issues.append({"case_id": case_id, "issue": "missing_review_packet"})
    for case_id in sorted(packets.keys() - candidates.keys()):
        issues.append({"case_id": case_id, "issue": "orphan_review_packet"})

    for case_id in sorted(candidates.keys() & packets.keys()):
        try:
            candidate = _read_json(candidates[case_id])
            packet = _read_json(packets[case_id])
            if not isinstance(candidate, dict) or not isinstance(packet, dict):
                raise ValueError("candidate and packet must be JSON objects")
            _validate_pending_candidate(candidate)
            if packet.get("case_id") != candidate.get("case_id"):
                issues.append({"case_id": case_id, "issue": "case_id_mismatch"})
            if packet.get("task_id") != candidate.get("task_id"):
                issues.append({"case_id": case_id, "issue": "task_id_mismatch"})
            protocol = packet.get("review_protocol", {})
            if not isinstance(protocol, dict) or protocol.get(
                "blinded_to_evaluator_prediction"
            ) is not True:
                issues.append(
                    {"case_id": case_id, "issue": "missing_blind_protocol"}
                )
            for path in _sensitive_paths(packet):
                issues.append(
                    {
                        "case_id": case_id,
                        "issue": "sensitive_reviewer_field",
                        "path": path,
                    }
                )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(
                {
                    "case_id": case_id,
                    "issue": "invalid_record",
                    "detail": str(exc),
                }
            )

    return {
        "valid": not issues,
        "candidate_count": len(candidates),
        "review_packet_count": len(packets),
        "paired_count": len(candidates.keys() & packets.keys()),
        "issues": issues,
    }


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string or null")
    return value.strip() or None


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be an explicit boolean")
    return value


def _edges(value: object, field: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    result: list[dict[str, str]] = []
    for index, edge in enumerate(value):
        if not isinstance(edge, dict):
            raise ValueError(f"{field}[{index}] must be an object")
        result.append(
            {
                "source": _nonempty_string(
                    edge.get("source"), f"{field}[{index}].source"
                ),
                "target": _nonempty_string(
                    edge.get("target"), f"{field}[{index}].target"
                ),
            }
        )
    return result


def _strings(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return [
        _nonempty_string(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    ]


def _validate_pending_candidate(candidate: dict[str, Any]) -> None:
    if any(key.startswith("gold_") for key in candidate):
        raise ValueError("pending candidate must not contain top-level Gold fields")
    adjudication = candidate.get("adjudication")
    if not isinstance(adjudication, dict):
        raise ValueError("candidate adjudication metadata is missing")
    if adjudication.get("status") != "pending_human":
        raise ValueError("only pending_human candidates can be promoted")
    if adjudication.get("independent_gold_required") is not True:
        raise ValueError("candidate does not require independent Gold annotation")
    if adjudication.get("gold_fields_present") is not False:
        raise ValueError("pending candidate already claims to contain Gold fields")
    for field in ("case_id", "task_id"):
        _nonempty_string(candidate.get(field), f"candidate.{field}")
    if not isinstance(candidate.get("candidate_process"), dict):
        raise ValueError("candidate_process must be an object")


def build_blinded_review_packet(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Create a reviewer-facing packet without evaluator predictions."""
    _validate_pending_candidate(candidate)
    review_process = copy.deepcopy(candidate["candidate_process"])
    metadata = review_process.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("controlled_mutation", None)
    return {
        "schema_version": "1.0",
        "case_id": candidate["case_id"],
        "task_id": candidate["task_id"],
        "candidate_origin": candidate.get("candidate_origin", "real_hy3"),
        "source_run": candidate.get("source_run"),
        "source_hashes": candidate.get("source_hashes", {}),
        "candidate_process": review_process,
        "trusted_evidence": candidate.get("trusted_evidence", []),
        "review_protocol": {
            "blinded_to_evaluator_prediction": True,
            "use_trusted_task_assets": True,
            "annotation_schema": "human_annotation.schema.json",
            "guideline_version": candidate["adjudication"].get(
                "guideline_version", "1.0"
            ),
        },
    }


def _predicted_error_type(
    prediction: dict[str, Any], primary_error: object
) -> tuple[str | None, str | None]:
    for item in prediction.get("review_focus", []):
        if isinstance(item, dict) and item.get("item_id") == primary_error:
            return (
                _optional_string(item.get("error_type_l1"), "error_type_l1"),
                _optional_string(item.get("error_type_l2"), "error_type_l2"),
            )
    return None, None


def _predicted_parent_edges(
    prediction: dict[str, Any], primary_error: object
) -> list[dict[str, str]]:
    if not isinstance(primary_error, str):
        return []
    graph = prediction.get("dependency_graph", {})
    if not isinstance(graph, dict):
        return []
    edges = graph.get("edges", [])
    if not isinstance(edges, list):
        return []
    return [
        {"source": str(edge["source"]), "target": str(edge["target"])}
        for edge in edges
        if isinstance(edge, dict)
        and edge.get("target") == primary_error
        and "source" in edge
    ]


def build_gold_evaluation_snapshot(
    gold: dict[str, Any],
    report: dict[str, Any],
    *,
    source_gold: str,
    source_gold_sha256: str,
    source_report: str,
    source_report_sha256: str,
) -> dict[str, Any]:
    """Attach a new evaluator prediction while preserving frozen Gold labels."""
    required_gold = {
        "gold_rtl_correct",
        "gold_process_correct",
        "gold_first_error_stage",
        "gold_root_error",
        "gold_parent_dependency",
        "gold_affected_obligation",
    }
    missing = required_gold - set(gold)
    if missing:
        raise ValueError(f"Gold record misses {sorted(missing)}")
    if gold.get("task_id") != report.get("task_id"):
        raise ValueError("Gold and report task_id do not match")

    prediction = _prediction_from_report(report)
    predicted_root = prediction.get("primary_error_item")
    predicted_l1, predicted_l2 = _predicted_error_type(
        prediction, predicted_root
    )
    snapshot = copy.deepcopy(gold)
    snapshot.update(
        {
            "predicted_rtl_correct": prediction.get("rtl_correct"),
            "predicted_process_correct": prediction.get("process_correct"),
            "predicted_first_error_stage": prediction.get(
                "earliest_error_stage"
            ),
            "predicted_root_error": predicted_root,
            "predicted_error_type_l1": predicted_l1,
            "predicted_error_type_l2": predicted_l2,
            "predicted_parent_dependency": _predicted_parent_edges(
                prediction, predicted_root
            ),
            "predicted_affected_obligations": prediction.get(
                "violated_obligations", []
            ),
            "evaluator_prediction": prediction,
        }
    )
    api_provenance = snapshot.setdefault("api_provenance", {})
    if not isinstance(api_provenance, dict):
        raise ValueError("Gold api_provenance must be an object")
    semantic_evaluator = report.get("semantic_evaluator", {})
    if not isinstance(semantic_evaluator, dict):
        raise ValueError("report semantic_evaluator must be an object")
    api_provenance["semantic_evaluator"] = semantic_evaluator
    dependency_graph = report.get("dependency_graph", {})
    if not isinstance(dependency_graph, dict):
        raise ValueError("report dependency_graph must be an object")
    snapshot["evaluation_snapshot"] = {
        "source_gold": source_gold,
        "source_gold_sha256": source_gold_sha256,
        "source_report": source_report,
        "source_report_sha256": source_report_sha256,
        "semantic_prompt_version": semantic_evaluator.get("prompt_version"),
        "dependency_graph_digest": dependency_graph.get("digest"),
        "gold_labels_modified": False,
    }
    return snapshot


def promote_adjudicated_case(
    candidate: dict[str, Any],
    annotation: dict[str, Any],
    *,
    split: str,
) -> dict[str, Any]:
    """Promote independent human labels while keeping predictions separate."""
    _validate_pending_candidate(candidate)
    if split not in {"development", "held_out"}:
        raise ValueError("split must be development or held_out")
    if not isinstance(annotation, dict):
        raise ValueError("annotation must be a JSON object")
    if annotation.get("independent_of_tested_model") is not True:
        raise ValueError("annotation must be independent of the tested model")

    status = annotation.get("status")
    if status not in {"single_annotated", "adjudicated"}:
        raise ValueError("annotation.status must be single_annotated or adjudicated")
    if split == "held_out" and status != "adjudicated":
        raise ValueError("held_out promotion requires adjudicated annotation")

    annotator_id = _nonempty_string(
        annotation.get("annotator_id"), "annotation.annotator_id"
    )
    guideline_version = _nonempty_string(
        annotation.get("guideline_version"), "annotation.guideline_version"
    )
    gold_rtl_correct = _boolean(
        annotation.get("gold_rtl_correct"), "annotation.gold_rtl_correct"
    )
    gold_process_correct = _boolean(
        annotation.get("gold_process_correct"),
        "annotation.gold_process_correct",
    )
    first_stage = _optional_string(
        annotation.get("gold_first_error_stage"),
        "annotation.gold_first_error_stage",
    )
    root_error = _optional_string(
        annotation.get("gold_root_error"), "annotation.gold_root_error"
    )
    error_type_l1 = _optional_string(
        annotation.get("gold_error_type_l1"),
        "annotation.gold_error_type_l1",
    )
    error_type_l2 = _optional_string(
        annotation.get("gold_error_type_l2"),
        "annotation.gold_error_type_l2",
    )
    parent_edges = _edges(
        annotation.get("gold_parent_dependency", []),
        "annotation.gold_parent_dependency",
    )
    affected_obligations = _strings(
        annotation.get("gold_affected_obligation", []),
        "annotation.gold_affected_obligation",
    )

    if not gold_process_correct:
        if first_stage is None or root_error is None:
            raise ValueError(
                "an incorrect process requires gold_first_error_stage and "
                "gold_root_error"
            )
    elif any(
        value
        for value in (
            first_stage,
            root_error,
            error_type_l1,
            error_type_l2,
            parent_edges,
            affected_obligations,
        )
    ):
        raise ValueError("a correct process must not contain Gold error labels")

    prediction = candidate.get("evaluator_prediction", {})
    if not isinstance(prediction, dict):
        prediction = {}
    predicted_root = prediction.get("primary_error_item")
    predicted_l1, predicted_l2 = _predicted_error_type(
        prediction, predicted_root
    )
    result = {
        "schema_version": "1.0",
        "case_id": candidate["case_id"],
        "split": split,
        "task_id": candidate["task_id"],
        "candidate_origin": candidate.get("candidate_origin", "real_hy3"),
        "source_run": candidate.get("source_run"),
        "source_hashes": candidate.get("source_hashes", {}),
        "candidate_process": candidate["candidate_process"],
        "trusted_evidence": candidate.get("trusted_evidence", []),
        "gold_rtl_correct": gold_rtl_correct,
        "gold_process_correct": gold_process_correct,
        "gold_first_error_stage": first_stage,
        "gold_root_error": root_error,
        "gold_error_type_l1": error_type_l1,
        "gold_error_type_l2": error_type_l2,
        "gold_parent_dependency": parent_edges,
        "gold_affected_obligation": affected_obligations,
        "predicted_rtl_correct": prediction.get("rtl_correct"),
        "predicted_process_correct": prediction.get("process_correct"),
        "predicted_first_error_stage": prediction.get(
            "earliest_error_stage"
        ),
        "predicted_root_error": predicted_root,
        "predicted_error_type_l1": predicted_l1,
        "predicted_error_type_l2": predicted_l2,
        "predicted_parent_dependency": _predicted_parent_edges(
            prediction, predicted_root
        ),
        "predicted_affected_obligations": prediction.get(
            "violated_obligations", []
        ),
        "evaluator_prediction": prediction,
        "api_provenance": candidate.get("api_provenance", {}),
        "annotation": {
            "independent_of_tested_model": True,
            "status": status,
            "annotator_id": annotator_id,
            "annotator_role": _optional_string(
                annotation.get("annotator_role"),
                "annotation.annotator_role",
            ),
            "guideline_version": guideline_version,
            "notes": str(annotation.get("notes", "")),
        },
    }
    return result
