import unittest
from pathlib import Path

from rtlreason.regression import load_regression_matrix, summarize_regression_matrix


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RegressionMatrixTests(unittest.TestCase):
    def test_matrix_is_valid_and_covers_every_task(self) -> None:
        matrix = load_regression_matrix(project_root=PROJECT_ROOT)
        summary = summarize_regression_matrix(matrix, project_root=PROJECT_ROOT)
        self.assertEqual(summary["case_count"], 22)
        self.assertEqual(summary["task_coverage"], 20)
        self.assertEqual(summary["uncovered_tasks"], [])
        self.assertEqual(summary["gold_status"], "controlled_not_independent_gold")


if __name__ == "__main__":
    unittest.main()
