from __future__ import annotations

from rtlreason.models import (
    AttributionResult,
    DependencyGraph,
    ItemAssessment,
    ProcessArtifact,
    STAGE_ORDER,
    VerificationEvidence,
    stage_of_item_id,
)


def attribute_errors(
    process: ProcessArtifact,
    graph: DependencyGraph,
    assessments: list[ItemAssessment],
    evidence: list[VerificationEvidence],
) -> AttributionResult:
    """Attribute failures on a graph that was frozen before EDA evidence existed."""
    assessment_map = {item.item_id: item for item in assessments}
    failed_obligations = {
        obligation
        for item in evidence
        if item.is_failure
        for obligation in item.obligations
    }
    process_items = process.item_map()
    semantic_errors = {
        item_id for item_id, assessment in assessment_map.items() if assessment.is_error
    }

    if failed_obligations:
        affected = {
            item.id
            for item in process.items
            if set(item.maps_to) & failed_obligations
        }
        relevant = set(affected)
        for item_id in affected:
            relevant.update(graph.ancestors_of(item_id))
        candidates = semantic_errors & relevant
        if not candidates:
            candidates = semantic_errors
    else:
        candidates = semantic_errors

    roots = []
    for candidate in sorted(candidates):
        erroneous_ancestors = graph.ancestors_of(candidate) & candidates
        if not erroneous_ancestors:
            roots.append(candidate)

    roots.sort(key=lambda value: (STAGE_ORDER[stage_of_item_id(value)], value))
    earliest = stage_of_item_id(roots[0]) if roots else None
    process_correct: bool | None
    if any(assessment.status == "unknown" for assessment in assessments):
        process_correct = None if not semantic_errors else False
    else:
        process_correct = not semantic_errors

    return AttributionResult(
        process_correct=process_correct,
        root_errors=tuple(roots),
        earliest_error_stage=earliest,
        primary_error_item=roots[0] if roots else None,
        violated_obligations=tuple(sorted(failed_obligations)),
        graph_digest=graph.digest,
    )
