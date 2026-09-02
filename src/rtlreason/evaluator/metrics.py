from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ValidationCase:
    case_id: str
    gold_rtl_correct: bool
    predicted_rtl_correct: bool | None
    gold_process_correct: bool
    predicted_process_correct: bool | None
    gold_first_error_stage: str | None = None
    predicted_first_error_stage: str | None = None
    gold_error_type_l1: str | None = None
    predicted_error_type_l1: str | None = None
    gold_root_error: str | None = None
    predicted_root_error: str | None = None
    gold_parent_dependency: tuple[tuple[str, str], ...] = ()
    predicted_parent_dependency: tuple[tuple[str, str], ...] = ()
    gold_affected_obligations: tuple[str, ...] = ()
    predicted_affected_obligations: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationCase":
        def edges(name: str) -> tuple[tuple[str, str], ...]:
            return tuple(
                (str(item["source"]), str(item["target"]))
                for item in data.get(name, [])
            )

        return cls(
            case_id=str(data["case_id"]),
            gold_rtl_correct=bool(data["gold_rtl_correct"]),
            predicted_rtl_correct=data.get("predicted_rtl_correct"),
            gold_process_correct=bool(data["gold_process_correct"]),
            predicted_process_correct=data.get("predicted_process_correct"),
            gold_first_error_stage=data.get("gold_first_error_stage"),
            predicted_first_error_stage=data.get("predicted_first_error_stage"),
            gold_error_type_l1=data.get("gold_error_type_l1"),
            predicted_error_type_l1=data.get("predicted_error_type_l1"),
            gold_root_error=data.get("gold_root_error"),
            predicted_root_error=data.get("predicted_root_error"),
            gold_parent_dependency=edges("gold_parent_dependency"),
            predicted_parent_dependency=edges("predicted_parent_dependency"),
            gold_affected_obligations=tuple(
                map(
                    str,
                    data.get(
                        "gold_affected_obligations",
                        data.get("gold_affected_obligation", []),
                    ),
                )
            ),
            predicted_affected_obligations=tuple(
                map(str, data.get("predicted_affected_obligations", []))
            ),
        )


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _macro_f1(pairs: Iterable[tuple[Any, Any]]) -> float | None:
    materialized = list(pairs)
    labels = {gold for gold, _ in materialized if gold is not None}
    if not labels:
        return None
    scores = []
    for label in sorted(labels, key=str):
        tp = sum(gold == label and predicted == label for gold, predicted in materialized)
        fp = sum(gold != label and predicted == label for gold, predicted in materialized)
        fn = sum(gold == label and predicted != label for gold, predicted in materialized)
        denominator = 2 * tp + fp + fn
        scores.append((2 * tp / denominator) if denominator else 0.0)
    return sum(scores) / len(scores)


def compute_core_metrics(cases: list[ValidationCase]) -> dict[str, Any]:
    """Compute the frozen task-2 core metrics from independent gold labels."""
    if not cases:
        raise ValueError("at least one validation case is required")
    identifiers = [case.case_id for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("validation case IDs must be unique")

    rtl_accuracy = _safe_ratio(
        sum(case.predicted_rtl_correct == case.gold_rtl_correct for case in cases),
        len(cases),
    )
    process_accuracy = _safe_ratio(
        sum(
            case.predicted_process_correct == case.gold_process_correct
            for case in cases
        ),
        len(cases),
    )
    process_macro_f1 = _macro_f1(
        (case.gold_process_correct, case.predicted_process_correct) for case in cases
    )

    error_cases = [case for case in cases if not case.gold_process_correct]
    first_error_accuracy = _safe_ratio(
        sum(
            case.predicted_first_error_stage == case.gold_first_error_stage
            for case in error_cases
        ),
        len(error_cases),
    )
    correct_process_cases = [case for case in cases if case.gold_process_correct]
    false_positive_rate = _safe_ratio(
        sum(case.predicted_process_correct is False for case in correct_process_cases),
        len(correct_process_cases),
    )
    correct_rtl_wrong_process = [
        case
        for case in cases
        if case.gold_rtl_correct and not case.gold_process_correct
    ]
    correct_rtl_wrong_process_recall = _safe_ratio(
        sum(
            case.predicted_process_correct is False
            for case in correct_rtl_wrong_process
        ),
        len(correct_rtl_wrong_process),
    )
    typed_error_cases = [
        case for case in error_cases if case.gold_error_type_l1 is not None
    ]
    error_type_macro_f1 = _macro_f1(
        (case.gold_error_type_l1, case.predicted_error_type_l1)
        for case in typed_error_cases
    )
    rooted_cases = [case for case in error_cases if case.gold_root_error is not None]
    root_error_accuracy = _safe_ratio(
        sum(case.predicted_root_error == case.gold_root_error for case in rooted_cases),
        len(rooted_cases),
    )
    dependency_cases = [case for case in error_cases if case.gold_parent_dependency]
    dependency_exact_accuracy = _safe_ratio(
        sum(
            set(case.predicted_parent_dependency)
            == set(case.gold_parent_dependency)
            for case in dependency_cases
        ),
        len(dependency_cases),
    )
    gold_edges = {
        (case.case_id, source, target)
        for case in dependency_cases
        for source, target in case.gold_parent_dependency
    }
    predicted_edges = {
        (case.case_id, source, target)
        for case in dependency_cases
        for source, target in case.predicted_parent_dependency
    }
    dependency_tp = len(gold_edges & predicted_edges)
    dependency_precision = _safe_ratio(dependency_tp, len(predicted_edges))
    dependency_recall = _safe_ratio(dependency_tp, len(gold_edges))
    dependency_f1 = (
        2 * dependency_precision * dependency_recall
        / (dependency_precision + dependency_recall)
        if dependency_precision is not None
        and dependency_recall is not None
        and dependency_precision + dependency_recall > 0
        else None
    )

    coverage = defaultdict(int)
    for case in cases:
        coverage["total"] += 1
        coverage["predicted_rtl"] += case.predicted_rtl_correct is not None
        coverage["predicted_process"] += case.predicted_process_correct is not None
        coverage["gold_process_errors"] += not case.gold_process_correct
        coverage["correct_rtl_wrong_process"] += (
            case.gold_rtl_correct and not case.gold_process_correct
        )
    return {
        "final_rtl_accuracy": rtl_accuracy,
        "process_correctness_accuracy": process_accuracy,
        "process_correctness_macro_f1": process_macro_f1,
        "stage_first_error_localization_accuracy": first_error_accuracy,
        "process_false_positive_rate": false_positive_rate,
        "correct_rtl_wrong_process_recall": correct_rtl_wrong_process_recall,
        "error_type_l1_macro_f1": error_type_macro_f1,
        "root_error_accuracy": root_error_accuracy,
        "critical_dependency_exact_accuracy": dependency_exact_accuracy,
        "critical_dependency_micro_precision": dependency_precision,
        "critical_dependency_micro_recall": dependency_recall,
        "critical_dependency_micro_f1": dependency_f1,
        "coverage": dict(coverage),
    }
