from __future__ import annotations

from dataclasses import dataclass

from rtlreason.models import ProcessArtifact, STAGE_ORDER, TaskAssets


@dataclass(frozen=True)
class SchemaIssue:
    code: str
    message: str
    item_id: str | None = None


def _valid_interface_trace(reference: str, interface: dict) -> bool:
    """Return whether interface_semantics.a.b names a real frozen field."""
    prefix = "interface_semantics."
    if not reference.startswith(prefix):
        return False
    current: object = interface
    for part in reference[len(prefix) :].split("."):
        if not part or not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def validate_process(
    process: ProcessArtifact, task: TaskAssets | None = None
) -> list[SchemaIssue]:
    issues: list[SchemaIssue] = []
    stage_ids = [stage.id for stage in process.stages]
    if stage_ids != list(STAGE_ORDER):
        issues.append(
            SchemaIssue(
                "STAGE_ORDER",
                f"Expected stages S1..S5 in order, got {stage_ids}",
            )
        )
    if task is not None and process.task_id != task.task_id:
        issues.append(
            SchemaIssue(
                "TASK_ID_MISMATCH",
                f"Expected task_id {task.task_id}, got {process.task_id}",
            )
        )

    for stage in process.stages:
        if not stage.items:
            issues.append(
                SchemaIssue("EMPTY_STAGE", f"Stage {stage.id} contains no items")
            )

    seen: set[str] = set()
    item_map = process.item_map()
    item_positions = process.item_positions()
    for item in process.items:
        if item.id in seen:
            issues.append(SchemaIssue("DUPLICATE_ID", "Duplicate item ID", item.id))
        seen.add(item.id)
        if not item.id.startswith(f"{item.stage}."):
            issues.append(
                SchemaIssue(
                    "ITEM_STAGE_MISMATCH",
                    f"Item ID does not match stage {item.stage}",
                    item.id,
                )
            )
        if not item.claim:
            issues.append(SchemaIssue("EMPTY_CLAIM", "Item claim is empty", item.id))
        for dependency in item.claimed_dependencies:
            parent = item_map.get(dependency)
            if parent is None:
                issues.append(
                    SchemaIssue(
                        "UNKNOWN_CLAIMED_DEPENDENCY",
                        f"Unknown dependency {dependency}",
                        item.id,
                    )
                )
            elif item_positions[parent.id] >= item_positions[item.id]:
                issues.append(
                    SchemaIssue(
                        "NON_CAUSAL_CLAIMED_DEPENDENCY",
                        f"Dependency {dependency} is not earlier in process order",
                        item.id,
                    )
                )
        if task is not None:
            unknown = {
                reference
                for reference in item.maps_to
                if reference not in task.obligation_ids
                and not _valid_interface_trace(
                    reference, task.interface_semantics
                )
            }
            if unknown:
                issues.append(
                    SchemaIssue(
                        "UNKNOWN_OBLIGATION",
                        f"Unknown obligations: {sorted(unknown)}",
                        item.id,
                    )
                )

    claimed_graph = {
        item.id: [
            dependency
            for dependency in item.claimed_dependencies
            if dependency in item_map
        ]
        for item in process.items
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_nodes: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycle_nodes.update(path[cycle_start:])
            return
        if node in visited:
            return
        visiting.add(node)
        path.append(node)
        for parent in claimed_graph.get(node, []):
            visit(parent, path)
        path.pop()
        visiting.remove(node)
        visited.add(node)

    for item_id in claimed_graph:
        visit(item_id, [])
    for item_id in sorted(cycle_nodes):
        issues.append(
            SchemaIssue(
                "CLAIMED_DEPENDENCY_CYCLE",
                "Claimed dependencies contain a directed cycle",
                item_id,
            )
        )

    if not process.rtl.module_name:
        issues.append(SchemaIssue("MISSING_MODULE", "RTL module name is missing"))
    if not process.rtl.code.strip():
        issues.append(SchemaIssue("MISSING_RTL", "RTL code is empty"))
    required_module = (
        task.interface_semantics.get("module_name") if task is not None else None
    )
    if required_module and process.rtl.module_name != required_module:
        issues.append(
            SchemaIssue(
                "MODULE_NAME_MISMATCH",
                f"This task requires module name {required_module}",
            )
        )
    return issues
