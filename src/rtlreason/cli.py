from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path

from rtlreason.config import Settings
from rtlreason.dataset import (
    DatasetError,
    find_project_root,
    load_task,
    load_task_manifest,
    summarize_task_manifest,
)
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
from rtlreason.evaluator.metrics import ValidationCase, compute_core_metrics
from rtlreason.evaluator.baselines import (
    compare_baselines_stratified,
    load_gold_records,
)
from rtlreason.experiment import run_artifact_experiment, run_experiment
from rtlreason.hy3 import Hy3Client, extract_json_object
from rtlreason.hy3.prompts import (
    JUDGE_PROMPT_VERSION,
    build_judge_messages,
    build_solver_messages,
    parse_assessments,
)
from rtlreason.models import ItemAssessment, ProcessArtifact, VerificationEvidence
from rtlreason.mutations import build_controlled_mutation
from rtlreason.reference import FifoReferenceModel
from rtlreason.validation import (
    audit_review_pool,
    build_adjudication_candidate,
    build_blinded_review_packet,
    build_gold_evaluation_snapshot,
    promote_adjudicated_case,
)
from rtlreason.verification.evidence import formal_evidence, simulation_evidence
from rtlreason.verification.toolchain import detect_toolchain


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def command_doctor(args: argparse.Namespace) -> int:
    settings = Settings.from_env(args.env_file)
    print(f"project_root: {find_project_root(args.project_root)}")
    print(f"HY3_API_KEY configured: {'yes' if settings.is_configured else 'no'}")
    print(f"Hy3 base URL: {settings.base_url}")
    print(f"Hy3 model: {settings.model}")
    for tool in detect_toolchain():
        state = "available" if tool.available else "missing"
        suffix = f" ({tool.version})" if tool.version else ""
        print(f"{tool.name}: {state}{suffix}")
    if args.check_api:
        if not settings.is_configured:
            print("TokenHub API: not checked (HY3_API_KEY missing)")
            return 2
        models = Hy3Client(settings).list_models()
        model_ids = {str(item.get("id", "")) for item in models}
        print(f"TokenHub API: reachable ({len(models)} models)")
        print(f"configured model available: {'yes' if settings.model in model_ids else 'no'}")
    return 0


def command_task_show(args: argparse.Namespace) -> int:
    task = load_task(args.task_id, project_root=args.project_root)
    print(_json_dump({
        "task_id": task.task_id,
        "problem": task.problem,
        "interface_semantics": task.interface_semantics,
        "obligations": [asdict(item) for item in task.obligations],
        "difficulty": task.difficulty,
        "provenance": task.provenance,
        "error_taxonomy": task.error_taxonomy,
    }))
    return 0


def command_solve(args: argparse.Namespace) -> int:
    task = load_task(args.task_id, project_root=args.project_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    settings = Settings.from_env(args.env_file)
    client = Hy3Client(settings)
    response = client.chat(
        build_solver_messages(task), thinking=True, max_tokens=args.max_tokens
    )
    raw_output = output.with_suffix(output.suffix + ".response.txt")
    if response.finish_reason == "length":
        raw_output.write_text(response.content, encoding="utf-8")
        raise ValueError(
            f"Hy3 output reached max_tokens; final response saved to {raw_output}"
        )
    try:
        payload = extract_json_object(
            response.content, required_keys={"task_id", "stages", "rtl"}
        )
    except ValueError:
        raw_output.write_text(response.content, encoding="utf-8")
        print(f"saved unparsed final response: {raw_output}")
        raise
    metadata = dict(payload.get("metadata", {}))
    metadata["generation"] = {
        "provider": "Tencent Cloud TokenHub",
        "model": response.model,
        "request_id": response.request_id,
        "usage": response.usage,
        "finish_reason": response.finish_reason,
    }
    payload["metadata"] = metadata
    process = ProcessArtifact.from_dict(payload)
    issues = validate_process(process, task)
    output.write_text(_json_dump(process.to_dict()) + "\n", encoding="utf-8")
    if args.rtl_output:
        rtl_output = Path(args.rtl_output)
        rtl_output.parent.mkdir(parents=True, exist_ok=True)
        rtl_output.write_text(process.rtl.code.rstrip() + "\n", encoding="utf-8")
        print(f"saved RTL: {rtl_output}")
    print(f"saved: {output}")
    print(f"schema_issues: {len(issues)}")
    if issues:
        raw_output.write_text(response.content, encoding="utf-8")
        print(f"saved nonconforming final response: {raw_output}")
        print(_json_dump([asdict(issue) for issue in issues]))
        return 2
    return 0


def _load_evidence(path: str | None) -> list[VerificationEvidence]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        VerificationEvidence(
            id=str(item["id"]),
            source=str(item["source"]),
            status=str(item["status"]),
            obligations=tuple(map(str, item.get("obligations", []))),
            summary=str(item.get("summary", "")),
            cycle=item.get("cycle"),
            details=dict(item.get("details", {})),
        )
        for item in data
    ]


def _load_assessments(path: str) -> list[ItemAssessment]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_items = data.get("assessments", data) if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        raise ValueError("assessment file must contain a list or an assessments list")
    return [
        ItemAssessment(
            item_id=str(item["item_id"]),
            status=str(item.get("status", "unknown")),
            error_type_l1=item.get("error_type_l1"),
            error_type_l2=item.get("error_type_l2"),
            explanation=str(item.get("explanation", "")),
            confidence=float(item.get("confidence", 0.0)),
        )
        for item in raw_items
    ]


def command_reference_demo(args: argparse.Namespace) -> int:
    task = load_task(args.task_id, project_root=args.project_root)
    if task.task_id != "fifo_sync_v1":
        raise ValueError("no executable reference demo is registered for this task")
    model = FifoReferenceModel(depth=4, data_width=8)
    sequence = [
        {"rst": True},
        {"wr_en": True, "rd_en": True, "din": 0xA1},
        {"rd_en": True},
        {"wr_en": True, "din": 0x11},
        {"wr_en": True, "din": 0x22},
    ]
    print(_json_dump([asdict(model.step(**inputs)) for inputs in sequence]))
    return 0


def command_verify_sim(args: argparse.Namespace) -> int:
    task = load_task(args.task_id, project_root=args.project_root)
    config = task.verification["simulation"]
    testbench = task.root / config["testbench"]
    artifact_dir = args.artifact_dir
    if artifact_dir is None and args.output:
        artifact_dir = str(Path(args.output).parent / "simulation-artifacts")
    result, evidence = simulation_evidence(
        args.rtl,
        testbench,
        all_obligations=task.obligation_ids,
        task_id=task.task_id,
        top=str(config["top"]),
        vcd_name=config.get("vcd"),
        artifact_dir=artifact_dir,
    )
    payload = {
        "available": result.available,
        "passed": result.passed,
        "compile_returncode": result.compile_returncode,
        "run_returncode": result.run_returncode,
        "evidence": [asdict(item) for item in evidence],
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(_json_dump(payload["evidence"]) + "\n", encoding="utf-8")
        print(f"saved: {output}")
    print(_json_dump(payload))
    if not result.available:
        return 4
    return 0 if result.passed else 3


def command_verify_formal(args: argparse.Namespace) -> int:
    task = load_task(args.task_id, project_root=args.project_root)
    config = task.verification["formal"]
    if not config.get("enabled", False):
        print(f"Formal verification is disabled for {task.task_id}", file=sys.stderr)
        return 4
    harness = task.root / config["harness"]
    formal_obligations = set(config.get("obligations", [])) & task.obligation_ids
    depth = int(config.get("depth", 24))
    result, evidence = formal_evidence(
        args.rtl,
        harness,
        formal_obligations=formal_obligations,
        task_id=task.task_id,
        depth=depth,
        top=str(config["top"]),
        artifact_dir=args.artifact_dir,
    )
    payload = {
        "available": result.available,
        "passed": result.passed,
        "returncode": result.returncode,
        "property_class": "safety",
        "evidence": [asdict(item) for item in evidence],
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(_json_dump(payload["evidence"]) + "\n", encoding="utf-8")
        print(f"saved: {output}")
    print(_json_dump(payload))
    if not result.available:
        return 4
    if result.passed is None:
        return 5
    return 0 if result.passed else 3


def command_evaluate(args: argparse.Namespace) -> int:
    task = load_task(args.task_id, project_root=args.project_root)
    process = ProcessArtifact.from_json(Path(args.process).read_text(encoding="utf-8"))
    issues = validate_process(process, task)
    graph = build_inferred_dependency_graph(process)
    claimed_comparison = compare_claimed_dependencies(process, graph)
    obligation_associations = build_obligation_associations(process)
    dependency_evidence = dependency_evidence_summary(process)

    evaluator_metadata = {"mode": "offline_independent_assessments"}
    if args.assessments:
        raw_assessments = _load_assessments(args.assessments)
    else:
        settings = Settings.from_env(args.env_file)
        if not settings.is_configured:
            print(
                "HY3_API_KEY is required unless --assessments is supplied",
                file=sys.stderr,
            )
            return 2
        client = Hy3Client(settings)
        response = client.chat(build_judge_messages(task, process), thinking=True)
        if response.finish_reason == "length":
            raw_judge = Path(args.output).with_suffix(".judge.response.txt")
            raw_judge.parent.mkdir(parents=True, exist_ok=True)
            raw_judge.write_text(response.content, encoding="utf-8")
            raise ValueError(
                f"Hy3 judge reached max_tokens; final response saved to {raw_judge}"
            )
        raw_assessments = parse_assessments(
            extract_json_object(response.content, required_keys={"assessments"})
        )
        evaluator_metadata = {
            "mode": "hy3_semantic_judge",
            "provider": "Tencent Cloud TokenHub",
            "model": response.model,
            "request_id": response.request_id,
            "usage": response.usage,
            "finish_reason": response.finish_reason,
            "prompt_version": JUDGE_PROMPT_VERSION,
        }
    semantic_assessments, assessment_issues = normalize_assessments(
        process, raw_assessments
    )
    assessments, deterministic_overrides, global_schema_error = (
        apply_deterministic_schema_issues(semantic_assessments, issues)
    )
    evidence = _load_evidence(args.evidence)
    result = attribute_errors(process, graph, assessments, evidence)
    if global_schema_error:
        result = replace(result, process_correct=False)
    report = {
        "task_id": task.task_id,
        "schema_issues": [asdict(issue) for issue in issues],
        "dependency_graph": {
            "digest": graph.digest,
            "nodes": graph.nodes,
            "edges": [asdict(edge) for edge in graph.edges],
            "claimed_dependency_comparison": claimed_comparison,
            "obligation_associations": [
                asdict(edge) for edge in obligation_associations
            ],
            "evidence_summary": dependency_evidence,
        },
        "semantic_assessments": [asdict(item) for item in semantic_assessments],
        "assessments": [asdict(item) for item in assessments],
        "assessment_issues": assessment_issues,
        "deterministic_overrides": deterministic_overrides,
        "semantic_evaluator": evaluator_metadata,
        "evidence": [asdict(item) for item in evidence],
        "attribution": asdict(result),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dump(report) + "\n", encoding="utf-8")
    print(f"saved: {output}")
    return 0


def command_metrics(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw_cases = data.get("cases", data) if isinstance(data, dict) else data
    if not isinstance(raw_cases, list):
        raise ValueError("metrics input must be a list or contain a cases list")
    metrics = compute_core_metrics(
        [ValidationCase.from_dict(item) for item in raw_cases]
    )
    rendered = _json_dump(metrics)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"saved: {output}")
    print(rendered)
    return 0


def command_baseline_metrics(args: argparse.Namespace) -> int:
    records = load_gold_records(args.input)
    root = Path(args.project_root or find_project_root()).resolve()
    manifest = load_task_manifest(project_root=root)
    layer_by_task = {
        str(item["task_id"]): str(item["layer"])
        for item in manifest["tasks"]
    }
    rendered = _json_dump(
        compare_baselines_stratified(records, layer_by_task)
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"saved: {output}")
    print(rendered)
    return 0


def command_dataset_summary(args: argparse.Namespace) -> int:
    root = Path(args.project_root or find_project_root()).resolve()
    summary = summarize_task_manifest(load_task_manifest(project_root=root))
    print(_json_dump(summary))
    return 0


def command_queue_case(args: argparse.Namespace) -> int:
    root = Path(args.project_root or find_project_root()).resolve()
    load_task(args.task_id, project_root=root)
    record = build_adjudication_candidate(
        case_id=args.case_id,
        task_id=args.task_id,
        run_dir=args.run_dir,
        project_root=root,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dump(record) + "\n", encoding="utf-8")
    print(f"saved: {output}")
    return 0


def command_promote_case(args: argparse.Namespace) -> int:
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    annotation = json.loads(Path(args.annotation).read_text(encoding="utf-8"))
    record = promote_adjudicated_case(
        candidate, annotation, split=args.split
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dump(record) + "\n", encoding="utf-8")
    print(f"saved: {output}")
    return 0


def command_blind_case(args: argparse.Namespace) -> int:
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    packet = build_blinded_review_packet(candidate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dump(packet) + "\n", encoding="utf-8")
    print(f"saved: {output}")
    return 0


def command_audit_review_pool(args: argparse.Namespace) -> int:
    result = audit_review_pool(args.candidates, args.review_packets)
    print(_json_dump(result))
    return 0 if result["valid"] else 3


def command_snapshot_gold(args: argparse.Namespace) -> int:
    gold_path = Path(args.gold).resolve()
    report_path = Path(args.report).resolve()
    process_path = report_path.parent / "process.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    evaluated_process = json.loads(process_path.read_text(encoding="utf-8"))
    if not isinstance(gold, dict) or not isinstance(report, dict):
        raise ValueError("Gold and report must be JSON objects")
    if evaluated_process != gold.get("candidate_process"):
        raise ValueError("report process.json does not match the Gold candidate")
    root = Path(args.project_root or find_project_root()).resolve()

    def display_path(path: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()

    snapshot = build_gold_evaluation_snapshot(
        gold,
        report,
        source_gold=display_path(gold_path),
        source_gold_sha256=hashlib.sha256(gold_path.read_bytes()).hexdigest(),
        source_report=display_path(report_path),
        source_report_sha256=hashlib.sha256(
            report_path.read_bytes()
        ).hexdigest(),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dump(snapshot) + "\n", encoding="utf-8")
    print(f"saved: {output}")
    return 0


def command_run(args: argparse.Namespace) -> int:
    settings = Settings.from_env(args.env_file)
    result = run_experiment(
        args.task_id,
        project_root=args.project_root or find_project_root(),
        run_dir=args.run_dir,
        settings=settings,
        formal_required=not args.skip_formal,
        max_tokens=args.max_tokens,
    )
    print(_json_dump(asdict(result)))
    return 0


def command_run_artifact(args: argparse.Namespace) -> int:
    settings = Settings.from_env(args.env_file)
    result = run_artifact_experiment(
        args.task_id,
        process_path=args.process,
        project_root=args.project_root or find_project_root(),
        run_dir=args.run_dir,
        settings=settings,
        formal_required=not args.skip_formal,
    )
    print(_json_dump(asdict(result)))
    return 0


def command_mutate_process(args: argparse.Namespace) -> int:
    source = Path(args.source).resolve()
    source_process = json.loads(source.read_text(encoding="utf-8"))
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    replacement_rtl = (
        Path(args.rtl).read_text(encoding="utf-8") if args.rtl else None
    )
    mutated = build_controlled_mutation(
        source_process,
        source_path=source,
        replacement_rtl=replacement_rtl,
        spec=spec,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dump(mutated) + "\n", encoding="utf-8")
    print(f"saved: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rtlreason")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument(
        "--eda-bin", help="Explicit OSS CAD Suite bin directory"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check configuration and EDA tools")
    doctor.add_argument(
        "--check-api", action="store_true", help="Call TokenHub GET /models"
    )
    doctor.set_defaults(func=command_doctor)

    task = subparsers.add_parser("task-show", help="Print normalized task assets")
    task.add_argument("task_id")
    task.set_defaults(func=command_task_show)

    reference = subparsers.add_parser(
        "reference-demo", help="Run the architecture-independent reference model"
    )
    reference.add_argument("task_id")
    reference.set_defaults(func=command_reference_demo)

    verify_sim = subparsers.add_parser(
        "verify-sim", help="Run a candidate RTL against trusted simulation"
    )
    verify_sim.add_argument("task_id")
    verify_sim.add_argument("--rtl", required=True)
    verify_sim.add_argument("--output", help="Write evidence JSON")
    verify_sim.add_argument("--artifact-dir", help="Persist waveform artifacts")
    verify_sim.set_defaults(func=command_verify_sim)

    verify_formal = subparsers.add_parser(
        "verify-formal", help="Run the candidate against FIFO safety properties"
    )
    verify_formal.add_argument("task_id")
    verify_formal.add_argument("--rtl", required=True)
    verify_formal.add_argument("--output", help="Write evidence JSON")
    verify_formal.add_argument("--artifact-dir", help="Formal work artifact directory")
    verify_formal.set_defaults(func=command_verify_formal)

    solve = subparsers.add_parser("solve", help="Ask Hy3 for S1-S5 and RTL")
    solve.add_argument("task_id")
    solve.add_argument("--output", required=True)
    solve.add_argument("--rtl-output", help="Also write extracted RTL source")
    solve.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("HY3_MAX_TOKENS", "24000")),
    )
    solve.set_defaults(func=command_solve)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate one process artifact")
    evaluate.add_argument("task_id")
    evaluate.add_argument("--process", required=True)
    evaluate.add_argument("--evidence")
    evaluate.add_argument(
        "--assessments", help="Use independent/offline semantic assessments JSON"
    )
    evaluate.add_argument("--output", required=True)
    evaluate.set_defaults(func=command_evaluate)

    metrics = subparsers.add_parser(
        "metrics", help="Compute task-2 metrics from independent gold cases"
    )
    metrics.add_argument("--input", required=True)
    metrics.add_argument("--output")
    metrics.set_defaults(func=command_metrics)

    baseline_metrics = subparsers.add_parser(
        "baseline-metrics",
        help="Compare EDA-only, Semantic-only, and full RTLReason on Gold data",
    )
    baseline_metrics.add_argument("--input", required=True)
    baseline_metrics.add_argument("--output")
    baseline_metrics.set_defaults(func=command_baseline_metrics)

    dataset_summary = subparsers.add_parser(
        "dataset-summary", help="Validate and summarize the frozen task layers"
    )
    dataset_summary.set_defaults(func=command_dataset_summary)

    queue_case = subparsers.add_parser(
        "queue-case", help="Export a run for independent human adjudication"
    )
    queue_case.add_argument("task_id")
    queue_case.add_argument("--run-dir", required=True)
    queue_case.add_argument("--case-id", required=True)
    queue_case.add_argument("--output", required=True)
    queue_case.set_defaults(func=command_queue_case)

    promote_case = subparsers.add_parser(
        "promote-case",
        help="Promote independent human labels into a Gold validation record",
    )
    promote_case.add_argument("--candidate", required=True)
    promote_case.add_argument("--annotation", required=True)
    promote_case.add_argument(
        "--split", required=True, choices=("development", "held_out")
    )
    promote_case.add_argument("--output", required=True)
    promote_case.set_defaults(func=command_promote_case)

    blind_case = subparsers.add_parser(
        "blind-case",
        help="Create a reviewer packet with evaluator predictions removed",
    )
    blind_case.add_argument("--candidate", required=True)
    blind_case.add_argument("--output", required=True)
    blind_case.set_defaults(func=command_blind_case)

    audit_pool = subparsers.add_parser(
        "audit-review-pool",
        help="Check blind-packet parity and sensitive-field leakage",
    )
    audit_pool.add_argument("--candidates", required=True)
    audit_pool.add_argument("--review-packets", required=True)
    audit_pool.set_defaults(func=command_audit_review_pool)

    snapshot_gold = subparsers.add_parser(
        "snapshot-gold",
        help="Combine frozen Gold labels with a versioned evaluator report",
    )
    snapshot_gold.add_argument("--gold", required=True)
    snapshot_gold.add_argument("--report", required=True)
    snapshot_gold.add_argument("--output", required=True)
    snapshot_gold.set_defaults(func=command_snapshot_gold)

    run = subparsers.add_parser(
        "run", help="Run generation, frozen-graph evaluation, EDA, and attribution"
    )
    run.add_argument("task_id")
    run.add_argument("--run-dir", required=True)
    run.add_argument("--skip-formal", action="store_true")
    run.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("HY3_MAX_TOKENS", "24000")),
    )
    run.set_defaults(func=command_run)

    run_artifact = subparsers.add_parser(
        "run-artifact",
        help="Evaluate an existing S1-S5 process without calling the solver",
    )
    run_artifact.add_argument("task_id")
    run_artifact.add_argument("--process", required=True)
    run_artifact.add_argument("--run-dir", required=True)
    run_artifact.add_argument("--skip-formal", action="store_true")
    run_artifact.set_defaults(func=command_run_artifact)

    mutate_process = subparsers.add_parser(
        "mutate-process",
        help="Create a controlled process-only or process/RTL mutation",
    )
    mutate_process.add_argument("--source", required=True)
    mutate_process.add_argument("--spec", required=True)
    mutate_process.add_argument(
        "--rtl",
        help="Replacement RTL (required for process_and_rtl mutations)",
    )
    mutate_process.add_argument("--output", required=True)
    mutate_process.set_defaults(func=command_mutate_process)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.eda_bin:
        os.environ["RTLREASON_EDA_BIN"] = str(Path(args.eda_bin).resolve())
    try:
        return int(args.func(args))
    except (DatasetError, ValueError, OSError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
