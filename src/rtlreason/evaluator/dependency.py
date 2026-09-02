from __future__ import annotations

from collections import defaultdict

from rtlreason.models import (
    DependencyEdge,
    DependencyGraph,
    ProcessArtifact,
    ProcessItem,
)


def _ordered_item_pairs(
    process: ProcessArtifact,
) -> list[tuple[ProcessItem, ProcessItem]]:
    items = list(process.items)
    positions = process.item_positions()
    return [
        (source, target)
        for source in items
        for target in items
        if positions[source.id] < positions[target.id]
    ]


def _supported_property_parents(
    target: ProcessItem, predecessors: list[ProcessItem]
) -> list[tuple[ProcessItem, set[str]]]:
    """Verify S4 derivation claims with structural def-use/trace evidence."""
    if target.stage != "S4" or not target.claimed_dependencies:
        return []
    claimed = set(target.claimed_dependencies)
    supported: list[tuple[ProcessItem, set[str]]] = []
    for source in predecessors:
        if source.id not in claimed:
            continue
        def_use = sorted(set(source.writes) & set(target.reads))
        trace = sorted(set(source.rtl_blocks) & set(target.rtl_blocks))
        if not def_use and not trace:
            continue
        reasons = {
            *(f"property_derivation:def_use:{signal}" for signal in def_use),
            *(f"property_derivation:rtl_traceability:{block}" for block in trace),
        }
        supported.append((source, reasons))
    return supported


def build_inferred_dependency_graph(process: ProcessArtifact) -> DependencyGraph:
    """Build a static nearest-definition graph without dynamic EDA evidence."""
    positions = process.item_positions()
    items = sorted(process.items, key=lambda item: positions[item.id])
    item_map = {item.id: item for item in items}
    reason_map: dict[tuple[str, str], set[str]] = defaultdict(set)
    for target_index, target in enumerate(items):
        predecessors = items[:target_index]
        property_parents = _supported_property_parents(target, predecessors)
        if property_parents:
            for source, reasons in property_parents:
                reason_map[(source.id, target.id)].update(reasons)
            continue
        for signal in sorted(set(target.reads)):
            source = next(
                (
                    candidate
                    for candidate in reversed(predecessors)
                    if signal in candidate.writes
                ),
                None,
            )
            if source is not None:
                reason_map[(source.id, target.id)].add(f"def_use:{signal}")
        for block in sorted(set(target.rtl_blocks)):
            source = next(
                (
                    candidate
                    for candidate in reversed(predecessors)
                    if block in candidate.rtl_blocks
                ),
                None,
            )
            if source is not None:
                reason_map[(source.id, target.id)].add(
                    f"rtl_traceability:{block}"
                )

    for (source_id, target_id), reasons in reason_map.items():
        shared_obligations = sorted(
            set(item_map[source_id].maps_to) & set(item_map[target_id].maps_to)
        )
        reasons.update(
            f"shared_obligation_context:{value}"
            for value in shared_obligations
        )

    edges = tuple(
        DependencyEdge(source, target, tuple(sorted(reasons)))
        for (source, target), reasons in sorted(reason_map.items())
    )
    return DependencyGraph(tuple(sorted(item.id for item in items)), edges)


def build_obligation_associations(
    process: ProcessArtifact,
) -> tuple[DependencyEdge, ...]:
    """Build non-causal associations for diagnostics, never attribution."""
    associations: list[DependencyEdge] = []
    for source, target in _ordered_item_pairs(process):
        shared = sorted(set(source.maps_to) & set(target.maps_to))
        if shared:
            associations.append(
                DependencyEdge(
                    source.id,
                    target.id,
                    tuple(f"shared_obligation:{value}" for value in shared),
                )
            )
    return tuple(associations)


def dependency_evidence_summary(process: ProcessArtifact) -> dict[str, object]:
    """Describe whether declared dependency claims have structural evidence."""
    items = list(process.items)
    structurally_annotated = [
        item for item in items if item.reads or item.writes or item.rtl_blocks
    ]
    gaps = {
        item.id: ["claimed_dependency_has_no_structural_traceability"]
        for item in items
        if item.claimed_dependencies
        and not (item.reads or item.writes or item.rtl_blocks)
    }
    claimed_dependency_count = sum(
        len(item.claimed_dependencies) for item in items
    )
    if claimed_dependency_count == 0:
        status = "not_applicable"
    elif gaps:
        status = "insufficient_evidence"
    else:
        status = "structurally_annotated"
    return {
        "status": status,
        "item_count": len(items),
        "claimed_dependency_count": claimed_dependency_count,
        "items_with_structural_traceability": len(structurally_annotated),
        "structural_traceability_coverage": (
            len(structurally_annotated) / len(items) if items else None
        ),
        "gaps": gaps,
    }


def compare_claimed_dependencies(
    process: ProcessArtifact, graph: DependencyGraph
) -> dict[str, dict[str, list[str]]]:
    inferred = {(edge.source, edge.target) for edge in graph.edges}
    result: dict[str, dict[str, list[str]]] = {}
    for item in process.items:
        claimed = set(item.claimed_dependencies)
        predicted = {source for source, target in inferred if target == item.id}
        missing = sorted(predicted - claimed)
        confirmed = sorted(claimed & predicted)
        unverified = sorted(claimed - predicted)
        if claimed or predicted:
            result[item.id] = {
                "confirmed_claimed_edges": confirmed,
                "missing_claimed_edges": missing,
                "unverified_claimed_edges": unverified,
            }
    return result


def claimed_dependency_mismatches(
    process: ProcessArtifact, graph: DependencyGraph
) -> dict[str, dict[str, list[str]]]:
    """Backward-compatible alias for the tri-state claimed-edge comparison."""
    return compare_claimed_dependencies(process, graph)
