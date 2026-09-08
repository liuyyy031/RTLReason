from __future__ import annotations

import json
import hashlib
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rtlreason.config import Settings
from rtlreason.dataset import load_task
from rtlreason.evaluator.attribution import attribute_errors
from rtlreason.evaluator.dependency import (
    build_obligation_associations,
    build_inferred_dependency_graph,
    compare_claimed_dependencies,
    dependency_evidence_summary,
)
from rtlreason.evaluator.schema import validate_process
from rtlreason.evaluator.semantic import (
    apply_deterministic_schema_issues,
    normalize_assessments,
)
from rtlreason.hy3 import Hy3Client, extract_json_object
from rtlreason.hy3.prompts import (
    JUDGE_PROMPT_VERSION,
    build_judge_messages,
    build_solver_messages,
    parse_assessments,
)
from rtlreason.models import ProcessArtifact, TaskAssets, VerificationEvidence
from rtlreason.verification.evidence import formal_evidence, simulation_evidence


@dataclass(frozen=True)
class ExperimentResult:
    run_dir: Path
    process_path: Path
    rtl_path: Path
    evidence_path: Path
    report_path: Path
    final_rtl_correct: bool | None


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _real_output_origin(model: str) -> str:
    return "real_hy3" if model.strip().lower() == "hy3" else "real_model_output"


def assert_candidate_generation_allowed(
    task: TaskAssets,
    settings: Settings,
    *,
    max_tokens: int,
    semantic_evaluation: bool,
) -> None:
    admission_path = task.root / "admission.json"
    if not admission_path.is_file():
        return
    try:
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Could not validate candidate-generation gate for {task.task_id}: {exc}"
        ) from exc
    if not isinstance(admission, dict):
        raise ValueError(
            f"Candidate-generation gate for {task.task_id} must be a JSON object"
        )
    if admission.get("candidate_generation_allowed") is False:
        blocker = admission.get("candidate_generation_blocker", "task_not_admitted")
        raise ValueError(
            f"Candidate generation is blocked for {task.task_id}: {blocker}"
        )
    plan_ref = admission.get("candidate_generation_plan")
    if not plan_ref:
        return
    project_root = task.root.parents[2]
    plan_path = project_root / str(plan_ref)
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Could not validate frozen generation plan for {task.task_id}: {exc}"
        ) from exc
    if plan.get("status") not in {
        "generation_plan_frozen",
        "generation_plan_amended",
    }:
        raise ValueError("Candidate generation plan is not frozen")
    samples = plan.get("samples", [])
    if sum(item.get("task_id") == task.task_id for item in samples) != 1:
        raise ValueError(
            f"Frozen generation plan must contain {task.task_id} exactly once"
        )
    config = {
        **plan.get("generation_configuration", {}),
        **plan.get("task_generation_overrides", {}).get(task.task_id, {}),
    }
    actual = {
        "model": settings.model,
        "base_url": settings.base_url,
        "temperature": settings.temperature,
        "reasoning_effort": settings.reasoning_effort,
        "max_tokens": max_tokens,
        "timeout_seconds": settings.timeout_seconds,
        "total_timeout_seconds": settings.total_timeout_seconds,
        "max_retries": settings.max_retries,
    }
    mismatches = {
        key: {"expected": config.get(key), "actual": value}
        for key, value in actual.items()
        if config.get(key) != value
    }
    if mismatches:
        raise ValueError(
            "Runtime settings do not match frozen generation plan: "
            + json.dumps(mismatches, ensure_ascii=False, sort_keys=True)
        )
    if semantic_evaluation and not plan["generation_policy"].get(
        "semantic_judge_during_collection", False
    ):
        raise ValueError(
            "Semantic Judge is frozen off during candidate collection; use --skip-judge"
        )
    for relative_path, expected in plan.get("frozen_inputs", {}).items():
        source = project_root / relative_path
        actual_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual_digest != expected:
            raise ValueError(
                f"Frozen generation input changed: {relative_path}"
            )


def _rtl_verdict(
    evidence: list[VerificationEvidence], *, formal_required: bool
) -> bool | None:
    if any(item.is_failure for item in evidence):
        return False
    simulation_passed = any(
        item.source == "iverilog" and item.status == "pass" for item in evidence
    )
    formal_passed = any(
        item.source == "symbiyosys" and item.status == "pass" for item in evidence
    )
    if simulation_passed and (formal_passed or not formal_required):
        return True
    return None


def _evaluate_process(
    *,
    task: TaskAssets,
    process: ProcessArtifact,
    destination: Path,
    api: Hy3Client,
    formal_required: bool,
    candidate_generation: dict[str, Any],
    semantic_evaluation: bool = True,
) -> ExperimentResult:
    """Run the one shared static-graph, EDA, Judge, and attribution pipeline."""
    process_path = destination / "process.json"
    rtl_path = destination / "candidate.sv"
    _write_json(process_path, process.to_dict())
    rtl_path.write_text(process.rtl.code.rstrip() + "\n", encoding="utf-8")
    schema_issues = validate_process(process, task)

    # Methodological boundary: freeze the static graph before any dynamic EDA
    # result exists.  The evidence functions below cannot mutate this value.
    graph = build_inferred_dependency_graph(process)
    frozen_graph_digest = graph.digest
    claimed_comparison = compare_claimed_dependencies(process, graph)
    obligation_associations = build_obligation_associations(process)
    dependency_evidence = dependency_evidence_summary(process)

    simulation_config = task.verification["simulation"]
    simulation, simulation_items = simulation_evidence(
        rtl_path,
        task.root / simulation_config["testbench"],
        all_obligations=task.obligation_ids,
        task_id=task.task_id,
        top=str(simulation_config["top"]),
        vcd_name=simulation_config.get("vcd"),
        artifact_dir=destination / "artifacts",
    )
    evidence = list(simulation_items)
    formal = None
    formal_config = task.verification["formal"]
    effective_formal_required = formal_required and bool(
        formal_config.get("enabled", False)
    )
    if effective_formal_required:
        formal_obligations = set(
            formal_config.get("obligations", task.obligation_ids)
        ) & task.obligation_ids
        formal, formal_items = formal_evidence(
            rtl_path,
            task.root / formal_config["harness"],
            formal_obligations=formal_obligations,
            task_id=task.task_id,
            depth=int(formal_config.get("depth", 24)),
            top=str(formal_config["top"]),
            artifact_dir=destination / "artifacts" / "formal",
        )
        evidence.extend(formal_items)
    if graph.digest != frozen_graph_digest:
        raise AssertionError("EDA evidence changed the frozen dependency graph")
    evidence_path = destination / "evidence.json"
    _write_json(evidence_path, [asdict(item) for item in evidence])

    if semantic_evaluation:
        judged = api.chat(build_judge_messages(task, process), thinking=True)
        (destination / "judge.response.txt").write_text(
            judged.content, encoding="utf-8"
        )
        if judged.finish_reason == "length":
            raise ValueError("Hy3 judge reached max_tokens; see judge.response.txt")
        raw_assessments = parse_assessments(
            extract_json_object(judged.content, required_keys={"assessments"})
        )
        semantic_assessments, assessment_issues = normalize_assessments(
            process, raw_assessments
        )
        assessments, deterministic_overrides, global_schema_error = (
            apply_deterministic_schema_issues(semantic_assessments, schema_issues)
        )
        attribution = attribute_errors(process, graph, assessments, evidence)
        if global_schema_error:
            attribution = replace(attribution, process_correct=False)
        attribution_payload = asdict(attribution)
        semantic_evaluator = {
            "provider": "Tencent Cloud TokenHub",
            "model": judged.model,
            "request_id": judged.request_id,
            "usage": judged.usage,
            "finish_reason": judged.finish_reason,
            "prompt_version": JUDGE_PROMPT_VERSION,
            "same_model_family_as_candidate": (
                judged.model == candidate_generation.get("model")
                if candidate_generation.get("model")
                else None
            ),
            "gold_labels_required_for_validation": True,
        }
    else:
        semantic_assessments = []
        assessments = []
        assessment_issues = []
        deterministic_overrides = []
        violated_obligations = sorted(
            {
                obligation
                for item in evidence
                if item.is_failure
                for obligation in item.obligations
            }
        )
        attribution_payload = {
            "process_correct": None,
            "root_errors": [],
            "earliest_error_stage": None,
            "primary_error_item": None,
            "violated_obligations": violated_obligations,
            "graph_digest": graph.digest,
            "status": "not_run",
        }
        semantic_evaluator = {
            "status": "not_run",
            "reason": "independent_collection_verify_only",
            "gold_labels_required_for_validation": True,
        }
    final_rtl_correct = _rtl_verdict(
        evidence, formal_required=effective_formal_required
    )
    report = {
        "schema_version": "1.0",
        "task_id": task.task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trusted_asset_version": task.provenance.get("version"),
        "schema_issues": [asdict(item) for item in schema_issues],
        "dependency_graph": {
            "construction": "static_before_eda",
            "digest": graph.digest,
            "nodes": graph.nodes,
            "edges": [asdict(edge) for edge in graph.edges],
            "claimed_dependency_comparison": claimed_comparison,
            "obligation_associations": [
                asdict(edge) for edge in obligation_associations
            ],
            "evidence_summary": dependency_evidence,
        },
        "verification": {
            "final_rtl_correct": final_rtl_correct,
            "formal_required": effective_formal_required,
            "simulation_available": simulation.available,
            "formal_available": formal.available if formal is not None else None,
        },
        "evidence": [asdict(item) for item in evidence],
        "candidate_generation": {
            **candidate_generation,
        },
        "semantic_evaluator": semantic_evaluator,
        "semantic_assessments": [asdict(item) for item in semantic_assessments],
        "assessments": [asdict(item) for item in assessments],
        "assessment_issues": assessment_issues,
        "deterministic_overrides": deterministic_overrides,
        "attribution": attribution_payload,
    }
    report_path = destination / "report.json"
    _write_json(report_path, report)
    return ExperimentResult(
        run_dir=destination,
        process_path=process_path,
        rtl_path=rtl_path,
        evidence_path=evidence_path,
        report_path=report_path,
        final_rtl_correct=final_rtl_correct,
    )


def run_experiment(
    task_id: str,
    *,
    project_root: str | Path,
    run_dir: str | Path,
    settings: Settings,
    formal_required: bool = True,
    max_tokens: int = 24000,
    semantic_evaluation: bool = True,
    client: Hy3Client | None = None,
) -> ExperimentResult:
    """Run one auditable Hy3 generation-and-evaluation experiment."""
    task = load_task(task_id, project_root=project_root)
    assert_candidate_generation_allowed(
        task,
        settings,
        max_tokens=max_tokens,
        semantic_evaluation=semantic_evaluation,
    )
    destination = Path(run_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    api = client or Hy3Client(settings)

    generated = api.chat(
        build_solver_messages(task), thinking=True, max_tokens=max_tokens
    )
    (destination / "generation.response.txt").write_text(
        generated.content, encoding="utf-8"
    )
    if generated.finish_reason == "length":
        raise ValueError(
            "Hy3 generation reached max_tokens; see generation.response.txt"
        )
    payload = extract_json_object(
        generated.content, required_keys={"task_id", "stages", "rtl"}
    )
    metadata = dict(payload.get("metadata", {}))
    metadata["generation"] = {
        "provider": "Tencent Cloud TokenHub",
        "model": generated.model,
        "request_id": generated.request_id,
        "usage": generated.usage,
        "finish_reason": generated.finish_reason,
    }
    payload["metadata"] = metadata
    process = ProcessArtifact.from_dict(payload)
    return _evaluate_process(
        task=task,
        process=process,
        destination=destination,
        api=api,
        formal_required=formal_required,
        candidate_generation={
            "origin": _real_output_origin(generated.model),
            "provider": "Tencent Cloud TokenHub",
            "model": generated.model,
            "request_id": generated.request_id,
            "usage": generated.usage,
            "finish_reason": generated.finish_reason,
        },
        semantic_evaluation=semantic_evaluation,
    )


def run_artifact_experiment(
    task_id: str,
    *,
    process_path: str | Path,
    project_root: str | Path,
    run_dir: str | Path,
    settings: Settings,
    formal_required: bool = True,
    semantic_evaluation: bool = True,
    client: Hy3Client | None = None,
) -> ExperimentResult:
    """Evaluate an existing process artifact without invoking the Hy3 solver."""
    task = load_task(task_id, project_root=project_root)
    source = Path(process_path).resolve()
    process = ProcessArtifact.from_json(source.read_text(encoding="utf-8"))
    if process.task_id != task_id:
        raise ValueError("process artifact task_id does not match requested task")
    destination = Path(run_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    api = client or Hy3Client(settings)
    embedded_generation = process.metadata.get("generation", {})
    if not isinstance(embedded_generation, dict):
        embedded_generation = {}
    return _evaluate_process(
        task=task,
        process=process,
        destination=destination,
        api=api,
        formal_required=formal_required,
        candidate_generation={
            "origin": (
                "controlled_mutation"
                if "controlled_mutation" in process.metadata
                else "provided_artifact"
            ),
            "source_process": source.as_posix(),
            "source_process_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "embedded_generation": embedded_generation,
        },
        semantic_evaluation=semantic_evaluation,
    )
