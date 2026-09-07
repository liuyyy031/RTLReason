import json
import shutil
import unittest
import uuid
from pathlib import Path

from rtlreason.validation import (
    ANNOTATION_GUIDELINE_VERSION,
    READJUDICATION_REQUIRED_CASES,
    audit_review_pool,
    build_adjudication_candidate,
    build_blinded_review_packet,
    build_gold_evaluation_snapshot,
    promote_adjudicated_case,
)


def pending_candidate() -> dict:
    return {
        "case_id": "case-1",
        "task_id": "fifo_sync_v1",
        "candidate_origin": "real_hy3",
        "candidate_process": {"task_id": "fifo_sync_v1", "stages": []},
        "source_hashes": {"process_sha256": "abc"},
        "trusted_evidence": [],
        "api_provenance": {},
        "evaluator_prediction": {
            "rtl_correct": True,
            "process_correct": False,
            "earliest_error_stage": "S3",
            "primary_error_item": "S3.2",
            "violated_obligations": [],
            "review_focus": [
                {
                    "item_id": "S3.2",
                    "status": "incorrect",
                    "error_type_l1": "Transition Logic",
                    "error_type_l2": "Simultaneous Operation Error",
                }
            ],
            "dependency_graph": {
                "edges": [
                    {"source": "S2.1", "target": "S3.2"},
                    {"source": "S1.1", "target": "S2.1"},
                ]
            },
        },
        "adjudication": {
            "status": "pending_human",
            "independent_gold_required": True,
            "gold_fields_present": False,
        },
    }


def error_annotation() -> dict:
    return {
        "annotator_id": "reviewer-01",
        "annotator_role": "independent RTL reviewer",
        "guideline_version": ANNOTATION_GUIDELINE_VERSION,
        "independent_of_tested_model": True,
        "status": "single_annotated",
        "gold_rtl_correct": True,
        "gold_process_correct": False,
        "gold_first_error_stage": "S3",
        "gold_root_error": "S3.1",
        "gold_error_type_l1": "Transition Logic",
        "gold_error_type_l2": "Guard Condition Omission",
        "gold_parent_dependency": [
            {"source": "S2.1", "target": "S3.1"}
        ],
        "gold_affected_obligation": [],
        "notes": "Independent review.",
    }


class GoldPromotionTests(unittest.TestCase):
    def test_readjudication_queue_matches_enforced_cases(self) -> None:
        root = Path(__file__).resolve().parents[1]
        queue = json.loads(
            (
                root
                / "datasets"
                / "validation"
                / "readjudication"
                / "v1.1-s4-scope.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(queue["target_guideline_version"], "1.1")
        self.assertEqual(
            {item["case_id"] for item in queue["cases"]},
            set(READJUDICATION_REQUIRED_CASES),
        )

    def test_blinded_packet_removes_evaluator_outputs(self) -> None:
        packet = build_blinded_review_packet(pending_candidate())
        self.assertNotIn("evaluator_prediction", packet)
        self.assertNotIn("api_provenance", packet)
        self.assertTrue(
            packet["review_protocol"]["blinded_to_evaluator_prediction"]
        )

    def test_rejects_non_independent_annotation(self) -> None:
        annotation = error_annotation()
        annotation["independent_of_tested_model"] = False
        with self.assertRaisesRegex(ValueError, "independent"):
            promote_adjudicated_case(
                pending_candidate(), annotation, split="development"
            )

    def test_rejects_missing_root_for_incorrect_process(self) -> None:
        annotation = error_annotation()
        annotation["gold_root_error"] = None
        with self.assertRaisesRegex(ValueError, "requires"):
            promote_adjudicated_case(
                pending_candidate(), annotation, split="development"
            )

    def test_rejects_stale_guideline_for_readjudication_case(self) -> None:
        candidate = pending_candidate()
        candidate["case_id"] = "dev-candidate-rising-edge-001"
        annotation = error_annotation()
        annotation["guideline_version"] = "1.0"
        with self.assertRaisesRegex(ValueError, "requires annotation guideline 1.1"):
            promote_adjudicated_case(
                candidate, annotation, split="development"
            )

    def test_rejects_error_labels_for_correct_process(self) -> None:
        annotation = error_annotation()
        annotation["gold_process_correct"] = True
        with self.assertRaisesRegex(ValueError, "must not contain"):
            promote_adjudicated_case(
                pending_candidate(), annotation, split="development"
            )

    def test_held_out_requires_adjudication(self) -> None:
        with self.assertRaisesRegex(ValueError, "held_out"):
            promote_adjudicated_case(
                pending_candidate(), error_annotation(), split="held_out"
            )

    def test_gold_and_prediction_remain_separate(self) -> None:
        record = promote_adjudicated_case(
            pending_candidate(), error_annotation(), split="development"
        )
        self.assertEqual(record["gold_root_error"], "S3.1")
        self.assertEqual(record["predicted_root_error"], "S3.2")
        self.assertEqual(
            record["predicted_parent_dependency"],
            [{"source": "S2.1", "target": "S3.2"}],
        )
        self.assertEqual(record["annotation"]["annotator_id"], "reviewer-01")

    def test_review_pool_audit_detects_sensitive_leakage(self) -> None:
        root = Path.cwd() / f".test-review-pool-{uuid.uuid4().hex}"
        root.mkdir()
        try:
            candidates = root / "candidates"
            packets = root / "packets"
            candidates.mkdir()
            packets.mkdir()
            candidate = pending_candidate()
            packet = build_blinded_review_packet(candidate)
            (candidates / "case-1.json").write_text(
                json.dumps(candidate), encoding="utf-8"
            )
            packet["candidate_process"]["metadata"] = {
                "controlled_mutation": {"target_item_id": "S3.2"}
            }
            (packets / "case-1.review.json").write_text(
                json.dumps(packet), encoding="utf-8"
            )
            result = audit_review_pool(candidates, packets)
            self.assertFalse(result["valid"])
            self.assertEqual(result["paired_count"], 1)
            self.assertTrue(
                any(
                    item["issue"] == "sensitive_reviewer_field"
                    for item in result["issues"]
                )
            )
        finally:
            shutil.rmtree(root)

    def test_review_pool_audit_detects_candidate_source_mismatch(self) -> None:
        root = Path.cwd() / f".test-review-source-{uuid.uuid4().hex}"
        run_dir = root / "runs" / "case-1"
        candidates = root / "datasets" / "validation" / "candidates"
        packets = root / "datasets" / "validation" / "review_packets"
        run_dir.mkdir(parents=True)
        candidates.mkdir(parents=True)
        packets.mkdir(parents=True)
        try:
            process = {
                "task_id": "fifo_sync_v1",
                "stages": [],
                "metadata": {"generation": {"model": "deepseek-v4-flash"}},
            }
            evidence: list[dict[str, object]] = []
            report = {
                "task_id": "fifo_sync_v1",
                "candidate_generation": {
                    "origin": "real_model_output",
                    "model": "deepseek-v4-flash",
                },
                "semantic_evaluator": {"status": "not_run"},
                "verification": {"final_rtl_correct": True},
                "attribution": {},
                "assessments": [],
                "dependency_graph": {},
            }
            for name, value in (
                ("process.json", process),
                ("evidence.json", evidence),
                ("report.json", report),
            ):
                (run_dir / name).write_text(json.dumps(value), encoding="utf-8")
            candidate = build_adjudication_candidate(
                case_id="case-1",
                task_id="fifo_sync_v1",
                run_dir=run_dir,
                project_root=root,
            )
            candidate["candidate_process"]["metadata"]["generation"][
                "model"
            ] = "hy3"
            packet = build_blinded_review_packet(candidate)
            (candidates / "case-1.json").write_text(
                json.dumps(candidate), encoding="utf-8"
            )
            (packets / "case-1.review.json").write_text(
                json.dumps(packet), encoding="utf-8"
            )

            result = audit_review_pool(
                candidates, packets, project_root=root
            )

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    item["issue"] == "candidate_process_source_mismatch"
                    for item in result["issues"]
                )
            )
        finally:
            shutil.rmtree(root)

    def test_evaluation_snapshot_preserves_gold_and_updates_prediction(self) -> None:
        gold = promote_adjudicated_case(
            pending_candidate(), error_annotation(), split="development"
        )
        report = {
            "task_id": "fifo_sync_v1",
            "verification": {"final_rtl_correct": True},
            "assessments": [
                {
                    "item_id": "S3.1",
                    "status": "incorrect",
                    "error_type_l1": "Transition Logic",
                    "error_type_l2": "Guard Condition Omission",
                }
            ],
            "attribution": {
                "process_correct": False,
                "root_errors": ["S3.1"],
                "earliest_error_stage": "S3",
                "primary_error_item": "S3.1",
                "violated_obligations": [],
            },
            "dependency_graph": {
                "digest": "new-graph",
                "edges": [{"source": "S2.1", "target": "S3.1"}],
            },
            "semantic_evaluator": {"prompt_version": "1.1"},
        }
        snapshot = build_gold_evaluation_snapshot(
            gold,
            report,
            source_gold="development/case.json",
            source_gold_sha256="gold-hash",
            source_report="runs/case/report.json",
            source_report_sha256="report-hash",
        )
        self.assertEqual(snapshot["gold_root_error"], "S3.1")
        self.assertEqual(snapshot["predicted_root_error"], "S3.1")
        self.assertEqual(
            snapshot["predicted_parent_dependency"],
            [{"source": "S2.1", "target": "S3.1"}],
        )
        self.assertFalse(
            snapshot["evaluation_snapshot"]["gold_labels_modified"]
        )
        self.assertEqual(
            snapshot["evaluation_snapshot"]["semantic_prompt_version"],
            "1.1",
        )


if __name__ == "__main__":
    unittest.main()
