import unittest
from pathlib import Path

from rtlreason.mutations import build_controlled_mutation
from rtlreason.validation import build_blinded_review_packet


def source_process() -> dict:
    return {
        "task_id": "demo_v1",
        "stages": [
            {"id": "S3", "items": [{"id": "S3.1", "claim": "correct"}]}
        ],
        "rtl": {"code": "module old; endmodule"},
        "metadata": {},
    }


def mutation_spec() -> dict:
    return {
        "mutation_id": "m1",
        "task_id": "demo_v1",
        "mutation_scope": "process_and_rtl",
        "target_item_id": "S3.1",
        "replacement_claim": "incorrect boundary rule",
        "rationale": "test mutation",
        "expected_violations": ["O_BOUNDARY"],
    }


class MutationTests(unittest.TestCase):
    def test_mutation_changes_exactly_target_and_rtl(self) -> None:
        mutated = build_controlled_mutation(
            source_process(),
            source_path=Path(__file__),
            replacement_rtl="module new; endmodule",
            spec=mutation_spec(),
        )
        self.assertEqual(
            mutated["stages"][0]["items"][0]["claim"],
            "incorrect boundary rule",
        )
        self.assertEqual(mutated["rtl"]["code"], "module new; endmodule")
        self.assertEqual(
            mutated["metadata"]["controlled_mutation"]["target_item_id"],
            "S3.1",
        )

    def test_missing_target_is_rejected(self) -> None:
        spec = mutation_spec()
        spec["target_item_id"] = "S4.9"
        with self.assertRaisesRegex(ValueError, "exactly one"):
            build_controlled_mutation(
                source_process(),
                source_path=Path(__file__),
                replacement_rtl="module new; endmodule",
                spec=spec,
            )

    def test_process_only_mutation_preserves_rtl(self) -> None:
        spec = mutation_spec()
        spec["mutation_scope"] = "process_only"
        spec["expected_violations"] = []
        mutated = build_controlled_mutation(
            source_process(),
            source_path=Path(__file__),
            replacement_rtl=None,
            spec=spec,
        )
        self.assertEqual(mutated["rtl"]["code"], "module old; endmodule")
        provenance = mutated["metadata"]["controlled_mutation"]
        self.assertEqual(provenance["mutation_scope"], "process_only")
        self.assertEqual(provenance["operator"], "replace_process_claim")

    def test_process_and_rtl_mutation_requires_rtl(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires replacement RTL"):
            build_controlled_mutation(
                source_process(),
                source_path=Path(__file__),
                replacement_rtl=None,
                spec=mutation_spec(),
            )

    def test_blinded_packet_removes_mutation_intent(self) -> None:
        candidate = {
            "case_id": "m1",
            "task_id": "demo_v1",
            "candidate_origin": "controlled_mutation",
            "candidate_process": source_process(),
            "trusted_evidence": [],
            "adjudication": {
                "status": "pending_human",
                "independent_gold_required": True,
                "gold_fields_present": False,
            },
        }
        candidate["candidate_process"]["metadata"]["controlled_mutation"] = {
            "target_item_id": "S3.1",
            "expected_violations": ["O_BOUNDARY"],
        }
        packet = build_blinded_review_packet(candidate)
        self.assertNotIn(
            "controlled_mutation", packet["candidate_process"]["metadata"]
        )
        self.assertIn(
            "controlled_mutation", candidate["candidate_process"]["metadata"]
        )
