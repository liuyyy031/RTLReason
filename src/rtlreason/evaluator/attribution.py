from __future__ import annotations

import re

from rtlreason.models import (
    AttributionResult,
    DependencyGraph,
    ItemAssessment,
    ProcessArtifact,
    STAGE_ORDER,
    VerificationEvidence,
    stage_of_item_id,
)


_INVALID_PROCEDURAL_LABEL = re.compile(
    r"(?m)^\s*([A-Za-z_][A-Za-z0-9_$]*)\s*:\s*"
    r"(?:always(?:_ff|_comb|_latch)?|assign|module)\b"
)


def _compile_failure_root(
    process: ProcessArtifact, evidence: list[VerificationEvidence]
) -> str | None:
    """Locate a precise S5 item for a reproducible malformed block label."""
    compile_failed = any(
        item.source == "iverilog"
        and item.is_failure
        and item.details.get("compile_returncode") not in {None, 0}
        for item in evidence
    )
    if not compile_failed:
        return None
    labels = _INVALID_PROCEDURAL_LABEL.findall(process.rtl.code)
    if not labels:
        return None
    candidates: list[tuple[int, str]] = []
    for item in process.items:
        if item.stage != "S5":
            continue
        claim = item.claim.casefold()
        score = sum(2 for label in labels if label.casefold() in claim)
        score += sum(1 for label in labels if label in item.rtl_blocks)
        if score:
            candidates.append((score, item.id))
    if not candidates:
        return None
    candidates.sort(key=lambda value: (-value[0], value[1]))
    return candidates[0][1]


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

    if failed_obligations and not candidates:
        compile_root = _compile_failure_root(process, evidence)
        if compile_root is not None:
            candidates = {compile_root}

    roots = []
    for candidate in sorted(candidates):
        erroneous_ancestors = graph.ancestors_of(candidate) & candidates
        if not erroneous_ancestors:
            roots.append(candidate)

    roots.sort(key=lambda value: (STAGE_ORDER[stage_of_item_id(value)], value))
    earliest = stage_of_item_id(roots[0]) if roots else None
    process_correct: bool | None
    if semantic_errors or failed_obligations:
        # S5 is part of the evaluated process.  Trusted RTL failure therefore
        # proves that at least one implementation claim is false even when the
        # semantic judge failed to identify a precise item-level root.
        process_correct = False
    elif any(assessment.status == "unknown" for assessment in assessments):
        process_correct = None
    else:
        process_correct = True

    return AttributionResult(
        process_correct=process_correct,
        root_errors=tuple(roots),
        earliest_error_stage=earliest,
        primary_error_item=roots[0] if roots else None,
        violated_obligations=tuple(sorted(failed_obligations)),
        graph_digest=graph.digest,
    )
