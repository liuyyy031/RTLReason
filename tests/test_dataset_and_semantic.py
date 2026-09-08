import json
import unittest
from pathlib import Path

from rtlreason.dataset import load_task
from rtlreason.evaluator.schema import SchemaIssue
from rtlreason.evaluator.schema import validate_process
from rtlreason.evaluator.semantic import (
    apply_deterministic_schema_issues,
    normalize_assessments,
)
from rtlreason.models import ItemAssessment
from tests.test_dependency_attribution import process_fixture


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DatasetAndSemanticTests(unittest.TestCase):
    def test_fifo_assets_load(self) -> None:
        task = load_task("fifo_sync_v1", project_root=PROJECT_ROOT)
        self.assertEqual(task.interface_semantics["acceptance"]["simultaneous_when_full"], "accept_read_and_write")
        self.assertIn("O_ORDERING", task.obligation_ids)
        self.assertEqual(task.provenance["created_by"], "human-designed trusted asset")

    def test_all_trusted_tasks_load_with_verification_manifests(self) -> None:
        task_ids = (
            "fifo_sync_v1",
            "counter_enable_v1",
            "shift_register_v1",
            "round_robin_arbiter_v1",
            "ready_valid_slice_v1",
            "request_ack_timeout_v1",
            "ready_valid_fifo2_v1",
            "sequence_detector_1011_v1",
            "pulse_stretcher_v1",
            "grant_hold_arbiter_v1",
            "debounce_filter_v1",
            "token_bucket_v1",
            "saturating_counter_v1",
            "serial_parity_v1",
            "programmable_timer_v1",
            "interrupt_pending_v1",
            "stream_width_adapter_v1",
            "apb_register_bank_v1",
        )
        for task_id in task_ids:
            with self.subTest(task_id=task_id):
                task = load_task(task_id, project_root=PROJECT_ROOT)
                self.assertTrue(task.obligation_ids)
                self.assertIn("simulation", task.verification)
                self.assertIn("formal", task.verification)
                self.assertTrue(
                    (task.root / task.verification["simulation"]["testbench"]).is_file()
                )

    def test_missing_assessment_becomes_unknown(self) -> None:
        process = process_fixture()
        normalized, issues = normalize_assessments(
            process, [ItemAssessment("S1.1", "correct", confidence=2.0)]
        )
        self.assertEqual(len(normalized), len(process.items))
        self.assertEqual(normalized[0].confidence, 1.0)
        self.assertTrue(any("missing assessment" in issue for issue in issues))
        self.assertEqual(normalized[-1].status, "unknown")

    def test_schema_evidence_overrides_model_judge(self) -> None:
        assessments = [ItemAssessment("S3.1", "correct", confidence=0.9)]
        issues = [
            SchemaIssue(
                "NON_CAUSAL_CLAIMED_DEPENDENCY",
                "same-stage dependency",
                "S3.1",
            )
        ]
        effective, overrides, global_error = apply_deterministic_schema_issues(
            assessments, issues
        )
        self.assertEqual(effective[0].status, "incorrect")
        self.assertEqual(effective[0].error_type_l1, "Format/Traceability")
        self.assertEqual(len(overrides), 1)
        self.assertFalse(global_error)

    def test_real_interface_semantics_trace_is_not_unknown_obligation(self) -> None:
        task = load_task("ready_valid_slice_v1", project_root=PROJECT_ROOT)
        candidate_path = (
            PROJECT_ROOT
            / "datasets"
            / "validation"
            / "candidates"
            / "dev-candidate-ready-valid-002.json"
        )
        from rtlreason.models import ProcessArtifact

        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        process = ProcessArtifact.from_dict(candidate["candidate_process"])
        issues = validate_process(process, task)
        self.assertFalse(
            any(issue.code == "UNKNOWN_OBLIGATION" for issue in issues)
        )


if __name__ == "__main__":
    unittest.main()
