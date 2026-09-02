import unittest

from rtlreason.evaluator.attribution import attribute_errors
from rtlreason.evaluator.dependency import (
    build_inferred_dependency_graph,
    build_obligation_associations,
    compare_claimed_dependencies,
    dependency_evidence_summary,
)
from rtlreason.evaluator.schema import validate_process
from rtlreason.models import (
    ItemAssessment,
    ProcessArtifact,
    ProcessItem,
    ProcessStage,
    RTLArtifact,
    VerificationEvidence,
)


def process_fixture() -> ProcessArtifact:
    return ProcessArtifact(
        task_id="fifo_sync_v1",
        architecture_summary="fixture",
        stages=(
            ProcessStage(
                "S1", "Specification Understanding",
                (ProcessItem("S1.1", "S1", "boundary rule", ("O_FULL_SIMULTANEOUS",), writes=("acceptance_policy",)),),
            ),
            ProcessStage(
                "S2", "Architecture / State Modeling",
                (ProcessItem("S2.1", "S2", "state", ("O_OCCUPANCY",), reads=("acceptance_policy",), writes=("count",)),),
            ),
            ProcessStage(
                "S3", "Transition & Temporal Rules",
                (
                    ProcessItem("S3.1", "S3", "transition", ("O_OCCUPANCY",), reads=("count",), writes=("next_count",)),
                    ProcessItem("S3.2", "S3", "use transition", ("O_OCCUPANCY",), claimed_dependencies=("S3.1",), reads=("next_count",)),
                ),
            ),
            ProcessStage(
                "S4", "Candidate Properties",
                (ProcessItem("S4.1", "S4", "property", ("O_OCCUPANCY",), reads=("next_count",)),),
            ),
            ProcessStage(
                "S5", "RTL Implementation",
                (ProcessItem("S5.1", "S5", "RTL", ("O_FLAGS",), reads=("acceptance_policy", "next_count"), rtl_blocks=("seq",)),),
            ),
        ),
        rtl=RTLArtifact("systemverilog", "fifo_sync", "module fifo_sync; endmodule"),
    )


class DependencyAndAttributionTests(unittest.TestCase):
    def test_graph_is_static_and_has_def_use_edges(self) -> None:
        process = process_fixture()
        graph = build_inferred_dependency_graph(process)
        edges = {(edge.source, edge.target): edge.reasons for edge in graph.edges}
        self.assertIn(("S1.1", "S2.1"), edges)
        self.assertIn("def_use:acceptance_policy", edges[("S1.1", "S2.1")])
        self.assertEqual(graph.digest, build_inferred_dependency_graph(process).digest)

    def test_same_stage_earlier_item_dependency_is_valid(self) -> None:
        process = process_fixture()
        issues = validate_process(process)
        self.assertFalse(
            any(issue.code == "NON_CAUSAL_CLAIMED_DEPENDENCY" for issue in issues)
        )
        graph = build_inferred_dependency_graph(process)
        edges = {(edge.source, edge.target) for edge in graph.edges}
        self.assertIn(("S3.1", "S3.2"), edges)
        comparison = compare_claimed_dependencies(process, graph)
        self.assertEqual(
            comparison["S3.2"]["confirmed_claimed_edges"], ["S3.1"]
        )
        self.assertEqual(comparison["S3.2"]["unverified_claimed_edges"], [])

    def test_shared_obligation_alone_is_not_a_causal_edge(self) -> None:
        process = process_fixture()
        graph = build_inferred_dependency_graph(process)
        causal_edges = {(edge.source, edge.target) for edge in graph.edges}
        self.assertNotIn(("S2.1", "S4.1"), causal_edges)
        associations = {
            (edge.source, edge.target)
            for edge in build_obligation_associations(process)
        }
        self.assertIn(("S2.1", "S4.1"), associations)

    def test_def_use_links_only_nearest_reaching_definition(self) -> None:
        process = process_fixture()
        stages = list(process.stages)
        stages[1] = ProcessStage(
            "S2",
            "Architecture / State Modeling",
            (
                ProcessItem(
                    "S2.1",
                    "S2",
                    "state",
                    ("O_OCCUPANCY",),
                    reads=("acceptance_policy",),
                    writes=("count", "acceptance_policy"),
                ),
            ),
        )
        revised = ProcessArtifact(
            process.task_id,
            process.architecture_summary,
            tuple(stages),
            process.rtl,
        )
        edges = {
            (edge.source, edge.target): edge.reasons
            for edge in build_inferred_dependency_graph(revised).edges
        }
        self.assertIn(("S2.1", "S5.1"), edges)
        self.assertNotIn(("S1.1", "S5.1"), edges)

    def test_supported_s4_derivation_beats_later_generic_writer(self) -> None:
        process = ProcessArtifact(
            task_id="edge_v1",
            architecture_summary="property derivation fixture",
            stages=(
                ProcessStage("S1", "Specification Understanding", ()),
                ProcessStage("S2", "Architecture / State Modeling", ()),
                ProcessStage(
                    "S3",
                    "Transition & Temporal Rules",
                    (
                        ProcessItem(
                            "S3.1",
                            "S3",
                            "transition equation",
                            ("O_RISE",),
                            reads=("previous",),
                            writes=("pulse",),
                        ),
                        ProcessItem(
                            "S3.2",
                            "S3",
                            "later boundary summary",
                            ("O_BOUNDARY",),
                            writes=("previous", "pulse"),
                        ),
                    ),
                ),
                ProcessStage(
                    "S4",
                    "Candidate Properties",
                    (
                        ProcessItem(
                            "S4.1",
                            "S4",
                            "rise property",
                            ("O_RISE",),
                            claimed_dependencies=("S3.1",),
                            reads=("previous", "pulse"),
                        ),
                    ),
                ),
                ProcessStage("S5", "RTL Implementation", ()),
            ),
            rtl=RTLArtifact("systemverilog", "edge", "module edge; endmodule"),
        )
        edges = {
            (edge.source, edge.target): edge.reasons
            for edge in build_inferred_dependency_graph(process).edges
        }
        self.assertIn(("S3.1", "S4.1"), edges)
        self.assertNotIn(("S3.2", "S4.1"), edges)
        self.assertIn(
            "property_derivation:def_use:pulse",
            edges[("S3.1", "S4.1")],
        )

    def test_missing_structural_fields_are_reported_not_inferred(self) -> None:
        process = process_fixture()
        bare = ProcessArtifact(
            task_id=process.task_id,
            architecture_summary=process.architecture_summary,
            stages=(
                process.stages[0],
                process.stages[1],
                ProcessStage(
                    "S3",
                    "Transition & Temporal Rules",
                    (
                        ProcessItem("S3.1", "S3", "first", ("O_OCCUPANCY",)),
                        ProcessItem(
                            "S3.2",
                            "S3",
                            "second",
                            ("O_OCCUPANCY",),
                            claimed_dependencies=("S3.1",),
                        ),
                    ),
                ),
                process.stages[3],
                process.stages[4],
            ),
            rtl=process.rtl,
        )
        graph = build_inferred_dependency_graph(bare)
        self.assertNotIn(
            ("S3.1", "S3.2"),
            {(edge.source, edge.target) for edge in graph.edges},
        )
        comparison = compare_claimed_dependencies(bare, graph)
        self.assertEqual(
            comparison["S3.2"]["unverified_claimed_edges"], ["S3.1"]
        )
        summary = dependency_evidence_summary(bare)
        self.assertEqual(summary["status"], "insufficient_evidence")
        self.assertIn("S3.2", summary["gaps"])

    def test_forward_same_stage_dependency_and_cycle_are_rejected(self) -> None:
        process = process_fixture()
        cyclic = ProcessArtifact(
            task_id=process.task_id,
            architecture_summary=process.architecture_summary,
            stages=(
                process.stages[0],
                process.stages[1],
                ProcessStage(
                    "S3",
                    "Transition & Temporal Rules",
                    (
                        ProcessItem(
                            "S3.1", "S3", "first", claimed_dependencies=("S3.2",)
                        ),
                        ProcessItem(
                            "S3.2", "S3", "second", claimed_dependencies=("S3.1",)
                        ),
                    ),
                ),
                process.stages[3],
                process.stages[4],
            ),
            rtl=process.rtl,
        )
        codes = [issue.code for issue in validate_process(cyclic)]
        self.assertIn("NON_CAUSAL_CLAIMED_DEPENDENCY", codes)
        self.assertIn("CLAIMED_DEPENDENCY_CYCLE", codes)

    def test_downstream_eda_failure_can_reach_upstream_root(self) -> None:
        process = process_fixture()
        graph = build_inferred_dependency_graph(process)
        assessments = [
            ItemAssessment(item.id, "incorrect" if item.id in {"S1.1", "S5.1"} else "correct")
            for item in process.items
        ]
        evidence = [
            VerificationEvidence(
                "sim:1", "iverilog", "fail", ("O_FLAGS",), "flag failure"
            )
        ]
        result = attribute_errors(process, graph, assessments, evidence)
        self.assertEqual(result.primary_error_item, "S1.1")
        self.assertEqual(result.earliest_error_stage, "S1")
        self.assertEqual(result.graph_digest, graph.digest)


if __name__ == "__main__":
    unittest.main()
