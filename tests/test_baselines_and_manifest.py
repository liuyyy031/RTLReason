import unittest
from pathlib import Path

from rtlreason.dataset import load_task_manifest, summarize_task_manifest
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
        self.assertEqual(summary["task_count"], 20)
        self.assertEqual(
            summary["by_layer"],
            {"basic": 6, "hard": 5, "intermediate": 9},
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
