import hashlib
import json
import unittest
from pathlib import Path

from rtlreason.dataset import load_task, load_task_manifest, summarize_task_manifest
from rtlreason.evaluator.baselines import (
    apply_baseline,
    compare_baselines,
    compare_baselines_stratified,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def gold_record() -> dict:
    return {
        "case_id": "correct-rtl-wrong-process",
        "task_id": "ready_valid_fifo2_v1",
        "gold_rtl_correct": True,
        "gold_process_correct": False,
        "gold_first_error_stage": "S3",
        "gold_root_error": "S3.2",
        "gold_error_type_l1": "Transition Logic",
        "gold_parent_dependency": [],
        "gold_affected_obligation": [],
        "predicted_rtl_correct": True,
        "predicted_process_correct": False,
        "predicted_first_error_stage": "S3",
        "predicted_root_error": "S3.2",
        "predicted_error_type_l1": "Transition Logic",
        "predicted_parent_dependency": [],
        "predicted_affected_obligations": [],
        "candidate_process": {
            "stages": [
                {"id": "S3", "items": [{"id": "S3.2"}]},
            ]
        },
        "evaluator_prediction": {
            "review_focus": [
                {
                    "item_id": "S3.2",
                    "status": "incorrect",
                    "error_type_l1": "Transition Logic",
                }
            ]
        },
        "annotation": {
            "independent_of_tested_model": True,
            "status": "adjudicated",
        },
    }


class BaselineAndManifestTests(unittest.TestCase):
    def test_manifest_covers_every_trusted_task_once(self) -> None:
        summary = summarize_task_manifest(
            load_task_manifest(project_root=PROJECT_ROOT)
        )
        self.assertEqual(summary["task_count"], 30)
        self.assertEqual(
            summary["by_layer"],
            {"basic": 8, "hard": 8, "intermediate": 14},
        )

    def test_batch_002_generation_plan_is_frozen(self) -> None:
        plan = json.loads(
            (
                PROJECT_ROOT
                / "datasets"
                / "task_expansion_batch_002.json"
            ).read_text(encoding="utf-8")
        )
        manifest = load_task_manifest(project_root=PROJECT_ROOT)
        current_ids = {task["task_id"] for task in manifest["tasks"]}
        planned = plan["tasks"]
        planned_ids = [task["task_id"] for task in planned]

        self.assertEqual(plan["status"], "generation_plan_frozen")
        self.assertTrue(plan["candidate_generation_allowed"])
        self.assertEqual(
            plan["candidate_generation_plan"],
            "datasets/validation/HELD_OUT_BATCH_002.json",
        )
        self.assertFalse(plan["semantic_evaluation_allowed"])
        self.assertGreaterEqual(plan["minimum_known_bad_per_task"], 2)
        self.assertEqual(len(planned_ids), 10)
        self.assertEqual(len(set(planned_ids)), 10)
        self.assertEqual(
            {wave: sum(task["wave"] == wave for task in planned) for wave in (1, 2, 3)},
            {1: 3, 2: 4, 3: 3},
        )
        status_by_id = {task["task_id"]: task["status"] for task in planned}
        frozen_ids = {
            "gray_code_counter_v1",
            "axi_stream_packet_counter_v1",
            "register_file_bypass_v1",
            "signed_alu_flags_v1",
            "spi_tx_v1",
            "cache_tag_lookup_v1",
            "credit_flow_control_v1",
            "async_handshake_v1",
            "uart_rx_v1",
            "multicycle_multiply_ctrl_v1",
        }
        assets_complete_ids: set[str] = set()
        self.assertTrue(frozen_ids.issubset(current_ids))
        self.assertTrue(
            (set(planned_ids) - frozen_ids).isdisjoint(current_ids)
        )
        self.assertTrue(
            all(status_by_id[task_id] == "trusted_frozen" for task_id in frozen_ids)
        )
        self.assertTrue(
            all(
                status_by_id[task_id] == "assets_complete"
                for task_id in assets_complete_ids
            )
        )
        self.assertTrue(
            all(
                status == "planned"
                for task_id, status in status_by_id.items()
                if task_id not in frozen_ids | assets_complete_ids
            )
        )

    def assert_trusted_frozen_record_is_consistent(self, task_id: str) -> None:
        task = load_task(task_id, project_root=PROJECT_ROOT)
        admission = json.loads(
            (task.root / "admission.json").read_text(encoding="utf-8")
        )
        manifest = load_task_manifest(project_root=PROJECT_ROOT)

        self.assertEqual(admission["status"], "trusted_frozen")
        self.assertTrue(admission["candidate_generation_allowed"])
        self.assertEqual(
            admission["candidate_generation_plan"],
            "datasets/validation/HELD_OUT_BATCH_002.json",
        )
        self.assertEqual(
            admission["independent_asset_review"]["status"], "approved"
        )
        self.assertTrue(admission["checks"]["independent_review_complete"])
        self.assertTrue(admission["checks"]["trusted_assets_finally_frozen"])
        self.assertIn(task_id, {item["task_id"] for item in manifest["tasks"]})
        self.assertEqual(admission["asset_hashes"]["status"], "frozen")
        self.assertEqual(
            {item.id for item in task.obligations},
            set(task.verification["formal"]["obligations"]),
        )
        known_bad = admission["verification_evidence"]["known_bad"]
        self.assertGreaterEqual(len(known_bad), 2)
        self.assertTrue(
            all(item["simulation"]["status"] == "fail" for item in known_bad)
        )
        self.assertTrue(
            all(item["formal"]["status"] == "fail" for item in known_bad)
        )
        for relative_path, expected in admission["asset_hashes"]["files"].items():
            actual = hashlib.sha256(
                (PROJECT_ROOT / relative_path).read_bytes()
            ).hexdigest()
            self.assertEqual(actual, expected, relative_path)

    def test_held_out_batch_002_has_one_frozen_hy3_sample_per_task(self) -> None:
        plan_path = (
            PROJECT_ROOT
            / "datasets"
            / "validation"
            / "HELD_OUT_BATCH_002.json"
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        batch = json.loads(
            (
                PROJECT_ROOT / "datasets" / "task_expansion_batch_002.json"
            ).read_text(encoding="utf-8")
        )
        expected_ids = {item["task_id"] for item in batch["tasks"]}
        samples = plan["samples"]

        self.assertEqual(plan["status"], "generation_plan_amended")
        self.assertEqual(plan["partition_scope"], "task_level_held_out_unseen_tasks")
        self.assertEqual(plan["candidate_model"], "hy3")
        self.assertEqual(plan["candidate_origin"], "real_hy3")
        overrides = plan["task_generation_overrides"]
        self.assertEqual(
            set(overrides), {"spi_tx_v1", "multicycle_multiply_ctrl_v1"}
        )
        self.assertTrue(all(item["model"] == "hy4-preview" for item in overrides.values()))
        self.assertTrue(all(item["total_timeout_seconds"] == 3000.0 for item in overrides.values()))
        self.assertTrue(all(item["candidate_origin"] == "real_model_output" for item in overrides.values()))
        self.assertFalse(plan["generation_policy"]["semantic_judge_during_collection"])
        self.assertTrue(plan["generation_policy"]["retain_first_valid_generation"])
        self.assertFalse(plan["generation_policy"]["resample_based_on_content_or_evidence"])
        self.assertEqual(len(samples), 10)
        self.assertEqual({item["task_id"] for item in samples}, expected_ids)
        self.assertEqual(len({item["case_id"] for item in samples}), 10)
        self.assertEqual(len({item["run_dir"] for item in samples}), 10)
        self.assertTrue(
            all(item["case_id"].startswith("heldout2-candidate-") for item in samples)
        )
        for relative_path, expected in plan["frozen_inputs"].items():
            actual = hashlib.sha256(
                (PROJECT_ROOT / relative_path).read_bytes()
            ).hexdigest()
            self.assertEqual(actual, expected, relative_path)

    def test_evaluator_v15_batch_002_snapshot_matches_sources(self) -> None:
        freeze = json.loads(
            (
                PROJECT_ROOT
                / "datasets"
                / "validation"
                / "EVALUATOR_V1_5_BATCH_002_FREEZE.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(freeze["applies_to_batch"], "held-out-batch-002")
        self.assertEqual(freeze["policy"]["batch_candidate_outputs_seen_at_freeze"], 0)
        self.assertEqual(freeze["policy"]["batch_gold_labels_seen_at_freeze"], 0)
        self.assertFalse(freeze["policy"]["semantic_evaluator_run_on_batch"])
        for relative_path, expected in freeze["sha256"].items():
            actual = hashlib.sha256(
                (PROJECT_ROOT / relative_path).read_bytes()
            ).hexdigest()
            self.assertEqual(actual, expected, relative_path)

    def test_held_out_batch_002_gold_freeze_matches_records(self) -> None:
        freeze = json.loads(
            (
                PROJECT_ROOT
                / "datasets"
                / "validation"
                / "HELD_OUT_BATCH_002_GOLD_FREEZE.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(freeze["status"], "gold_frozen_evaluator_pending")
        self.assertEqual(freeze["case_count"], 10)
        self.assertEqual(freeze["distribution"]["gold_process_correct"], 6)
        self.assertEqual(freeze["distribution"]["gold_process_incorrect"], 4)
        self.assertEqual(freeze["model_partitions"]["hy3"]["case_count"], 8)
        self.assertEqual(
            freeze["model_partitions"]["hy4-preview"]["case_count"], 2
        )
        for group in ("control_hashes", "gold_sha256"):
            for relative_path, expected in freeze[group].items():
                actual = hashlib.sha256(
                    (PROJECT_ROOT / relative_path).read_bytes()
                ).hexdigest()
                self.assertEqual(actual, expected, relative_path)

    def test_held_out_batch_002_evaluation_artifacts_are_frozen(self) -> None:
        result = json.loads(
            (
                PROJECT_ROOT
                / "datasets"
                / "validation"
                / "HELD_OUT_BATCH_002_EVALUATION.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(result["status"], "one_shot_evaluation_complete")
        self.assertEqual(result["case_count"], 10)
        self.assertEqual(result["semantic_evaluator"]["model"], "hy3")
        self.assertFalse(result["semantic_evaluator"]["gold_labels_provided_to_judge"])
        frozen_paths = {
            result["gold_freeze"]["path"]: result["gold_freeze"]["sha256"],
            result["evaluator_freeze"]["path"]: result["evaluator_freeze"]["sha256"],
            **result["artifact_sha256"],
        }
        for relative_path, expected in frozen_paths.items():
            actual = hashlib.sha256(
                (PROJECT_ROOT / relative_path).read_bytes()
            ).hexdigest()
            self.assertEqual(actual, expected, relative_path)

    def test_gray_code_counter_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("gray_code_counter_v1")

    def test_axi_stream_counter_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent(
            "axi_stream_packet_counter_v1"
        )

    def test_register_file_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent(
            "register_file_bypass_v1"
        )

    def test_signed_alu_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("signed_alu_flags_v1")

    def test_spi_tx_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("spi_tx_v1")

    def test_cache_tag_lookup_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("cache_tag_lookup_v1")

    def test_credit_flow_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("credit_flow_control_v1")

    def test_async_handshake_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("async_handshake_v1")

    def test_uart_rx_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent("uart_rx_v1")

    def test_multicycle_multiply_frozen_record_is_consistent(self) -> None:
        self.assert_trusted_frozen_record_is_consistent(
            "multicycle_multiply_ctrl_v1"
        )

    def test_async_handshake_multiclock_risk_gate_is_frozen(self) -> None:
        task = load_task("async_handshake_v1", project_root=PROJECT_ROOT)
        admission = json.loads(
            (task.root / "admission.json").read_text(encoding="utf-8")
        )
        self.assertEqual(admission["status"], "trusted_frozen")
        self.assertEqual(admission["risk_gate"]["status"], "passed")
        self.assertTrue(admission["checks"]["multiclock_formal_reproducible"])
        self.assertEqual(admission["asset_hashes"]["status"], "frozen")
        self.assertEqual(
            {item.id for item in task.obligations},
            set(task.verification["formal"]["obligations"]),
        )

    def test_eda_only_misses_correct_rtl_wrong_process(self) -> None:
        prediction = apply_baseline(gold_record(), "eda_only")
        self.assertTrue(prediction["predicted_process_correct"])
        metrics = compare_baselines([gold_record()])
        self.assertEqual(
            metrics["eda_only"]["correct_rtl_wrong_process_recall"], 0.0
        )
        self.assertEqual(
            metrics["semantic_only"]["correct_rtl_wrong_process_recall"], 1.0
        )
        self.assertEqual(metrics["full"]["root_error_accuracy"], 1.0)

    def test_semantic_only_has_no_dependency_prediction(self) -> None:
        prediction = apply_baseline(gold_record(), "semantic_only")
        self.assertEqual(prediction["predicted_root_error"], "S3.2")
        self.assertEqual(prediction["predicted_parent_dependency"], [])

    def test_stratified_metrics_do_not_mix_difficulty_layers(self) -> None:
        result = compare_baselines_stratified(
            [gold_record()], {"ready_valid_fifo2_v1": "hard"}
        )
        self.assertEqual(result["case_count"], 1)
        self.assertEqual(result["by_layer"]["hard"]["case_count"], 1)
        self.assertIsNone(result["by_layer"]["basic"]["metrics"])

    def test_stratified_metrics_reject_unknown_tasks(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the manifest"):
            compare_baselines_stratified([gold_record()], {})


if __name__ == "__main__":
    unittest.main()
