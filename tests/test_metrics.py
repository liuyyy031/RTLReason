import unittest

from rtlreason.evaluator.metrics import ValidationCase, compute_core_metrics


class MetricsTests(unittest.TestCase):
    def test_core_metrics(self) -> None:
        cases = [
            ValidationCase("a", True, True, True, True),
            ValidationCase("b", False, False, False, False, "S3", "S3", "Transition Logic", "Transition Logic"),
            ValidationCase("c", True, True, False, True, "S2", None, "State Modeling", None),
            ValidationCase("d", True, False, True, False),
        ]
        metrics = compute_core_metrics(cases)
        self.assertEqual(metrics["final_rtl_accuracy"], 0.75)
        self.assertEqual(metrics["process_correctness_accuracy"], 0.5)
        self.assertEqual(metrics["stage_first_error_localization_accuracy"], 0.5)
        self.assertEqual(metrics["process_false_positive_rate"], 0.5)
        self.assertEqual(metrics["correct_rtl_wrong_process_recall"], 0.0)

    def test_duplicate_ids_rejected(self) -> None:
        case = ValidationCase("same", True, True, True, True)
        with self.assertRaises(ValueError):
            compute_core_metrics([case, case])


if __name__ == "__main__":
    unittest.main()
