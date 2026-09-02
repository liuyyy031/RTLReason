from __future__ import annotations

from rtlreason.models import ItemAssessment, ProcessArtifact
from rtlreason.evaluator.schema import SchemaIssue


VALID_STATUSES = {"correct", "incorrect", "unknown"}

_SCHEMA_ERROR_SUBTYPES = {
    "EMPTY_STAGE": "Missing Stage or Item",
    "DUPLICATE_ID": "Missing Stage or Item",
    "UNKNOWN_OBLIGATION": "Unknown Obligation Mapping",
    "UNKNOWN_CLAIMED_DEPENDENCY": "Unsupported Dependency Claim",
    "NON_CAUSAL_CLAIMED_DEPENDENCY": "Unsupported Dependency Claim",
    "CLAIMED_DEPENDENCY_CYCLE": "Unsupported Dependency Claim",
    "ITEM_STAGE_MISMATCH": "Missing Stage or Item",
    "EMPTY_CLAIM": "Missing Stage or Item",
}


def normalize_assessments(
    process: ProcessArtifact, assessments: list[ItemAssessment]
) -> tuple[list[ItemAssessment], list[str]]:
    """Validate judge output and make omitted items explicitly unknown."""
    item_ids = {item.id for item in process.items}
    normalized: dict[str, ItemAssessment] = {}
    issues: list[str] = []
    for assessment in assessments:
        if assessment.item_id not in item_ids:
            issues.append(f"assessment references unknown item {assessment.item_id}")
            continue
        if assessment.item_id in normalized:
            issues.append(f"duplicate assessment for {assessment.item_id}")
            continue
        status = assessment.status
        if status not in VALID_STATUSES:
            issues.append(
                f"invalid status {status!r} for {assessment.item_id}; treated as unknown"
            )
            status = "unknown"
        confidence = min(1.0, max(0.0, assessment.confidence))
        normalized[assessment.item_id] = ItemAssessment(
            item_id=assessment.item_id,
            status=status,
            error_type_l1=assessment.error_type_l1,
            error_type_l2=assessment.error_type_l2,
            explanation=assessment.explanation,
            confidence=confidence,
        )

    for item in process.items:
        if item.id not in normalized:
            issues.append(f"missing assessment for {item.id}; treated as unknown")
            normalized[item.id] = ItemAssessment(item_id=item.id, status="unknown")
    return [normalized[item.id] for item in process.items], issues


def apply_deterministic_schema_issues(
    assessments: list[ItemAssessment], issues: list[SchemaIssue]
) -> tuple[list[ItemAssessment], list[dict[str, str | None]], bool]:
    """Override model judgments where deterministic schema evidence disagrees."""
    issue_by_item: dict[str, list[SchemaIssue]] = {}
    global_issue = False
    for issue in issues:
        if issue.item_id is None:
            global_issue = True
        else:
            issue_by_item.setdefault(issue.item_id, []).append(issue)

    effective: list[ItemAssessment] = []
    overrides: list[dict[str, str | None]] = []
    for assessment in assessments:
        item_issues = issue_by_item.get(assessment.item_id, [])
        if not item_issues:
            effective.append(assessment)
            continue
        subtype = _SCHEMA_ERROR_SUBTYPES.get(
            item_issues[0].code, "Missing Stage or Item"
        )
        explanation = "; ".join(issue.message for issue in item_issues)
        effective.append(
            ItemAssessment(
                item_id=assessment.item_id,
                status="incorrect",
                error_type_l1="Format/Traceability",
                error_type_l2=subtype,
                explanation=f"Deterministic schema check: {explanation}",
                confidence=1.0,
            )
        )
        overrides.append(
            {
                "item_id": assessment.item_id,
                "judge_status": assessment.status,
                "effective_status": "incorrect",
                "reason": explanation,
            }
        )
    return effective, overrides, global_issue
