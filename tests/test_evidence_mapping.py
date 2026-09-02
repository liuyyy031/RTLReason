import unittest
from unittest.mock import patch

from rtlreason.verification.evidence import formal_evidence
from rtlreason.verification.sby import FormalResult


class FormalEvidenceMappingTests(unittest.TestCase):
    @patch("rtlreason.verification.evidence.run_bounded_formal")
    def test_unmapped_counterexample_does_not_accuse_every_obligation(
        self, run_formal
    ) -> None:
        run_formal.return_value = FormalResult(True, False, 2, "DONE (FAIL)")
        _, evidence = formal_evidence(
            "candidate.sv",
            "harness.sv",
            formal_obligations={"O_RESET", "O_ORDERING"},
            task_id="demo",
        )
        self.assertEqual(evidence[0].status, "fail")
        self.assertEqual(evidence[0].obligations, ())
        self.assertEqual(
            evidence[0].details["configured_obligations"],
            ("O_ORDERING", "O_RESET"),
        )
        self.assertEqual(
            evidence[0].details["obligation_mapping"],
            "unresolved_counterexample",
        )

    @patch("rtlreason.verification.evidence.run_bounded_formal")
    def test_formal_pass_covers_configured_obligations(self, run_formal) -> None:
        run_formal.return_value = FormalResult(True, True, 0, "DONE (PASS)")
        _, evidence = formal_evidence(
            "candidate.sv",
            "harness.sv",
            formal_obligations={"O_RESET", "O_ORDERING"},
            task_id="demo",
        )
        self.assertEqual(evidence[0].obligations, ("O_ORDERING", "O_RESET"))
        self.assertEqual(
            evidence[0].details["obligation_mapping"],
            "all_properties_passed",
        )


if __name__ == "__main__":
    unittest.main()
