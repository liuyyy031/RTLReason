import json
import unittest
import shutil
import uuid
from pathlib import Path

from rtlreason.config import Settings
from rtlreason.experiment import run_artifact_experiment, run_experiment
from rtlreason.hy3 import Hy3Response
from rtlreason.validation import build_adjudication_candidate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat(self, messages, **kwargs):
        self.calls += 1
        if self.calls == 1:
            payload = {
                "task_id": "fifo_sync_v1",
                "architecture_summary": "counter fixture",
                "stages": [
                    {"id": "S1", "title": "Specification Understanding", "items": [{"id": "S1.1", "claim": "understand reset", "maps_to": ["O_RESET"]}]},
                    {"id": "S2", "title": "Architecture / State Modeling", "items": [{"id": "S2.1", "claim": "track count", "maps_to": ["O_OCCUPANCY"], "writes": ["count"]}]},
                    {"id": "S3", "title": "Transition & Temporal Rules", "items": [{"id": "S3.1", "claim": "update count", "maps_to": ["O_OCCUPANCY"], "reads": ["count"]}]},
                    {"id": "S4", "title": "Candidate Properties", "items": [{"id": "S4.1", "claim": "count bounded", "maps_to": ["O_OCCUPANCY"]}]},
                    {"id": "S5", "title": "RTL Implementation", "items": [{"id": "S5.1", "claim": "implement module", "maps_to": ["O_RESET"]}]},
                ],
                "rtl": {"language": "systemverilog", "module_name": "fifo_sync", "code": "module fifo_sync; endmodule"},
            }
        else:
            payload = {
                "assessments": [
                    {"item_id": f"S{stage}.1", "status": "correct", "confidence": 1.0}
                    for stage in range(1, 6)
                ]
            }
        return Hy3Response(json.dumps(payload), "hy3", {"total_tokens": 1}, f"r{self.calls}")


class JudgeOnlyClient:
    def chat(self, messages, **kwargs):
        payload = {
            "assessments": [
                {"item_id": f"S{stage}.1", "status": "correct", "confidence": 1.0}
                for stage in range(1, 6)
            ]
        }
        return Hy3Response(json.dumps(payload), "hy3", {"total_tokens": 1}, "judge-only")


class DeepSeekFakeClient(FakeClient):
    def chat(self, messages, **kwargs):
        response = super().chat(messages, **kwargs)
        return Hy3Response(
            response.content,
            "deepseek-v4-flash",
            response.usage,
            response.request_id,
        )


class ExperimentTests(unittest.TestCase):
    def test_non_hy3_generation_is_not_mislabeled(self) -> None:
        directory = PROJECT_ROOT / "tests" / "work" / f"deepseek-{uuid.uuid4().hex}"
        directory.mkdir(parents=True)
        try:
            client = DeepSeekFakeClient()
            run_experiment(
                "fifo_sync_v1",
                project_root=PROJECT_ROOT,
                run_dir=directory,
                settings=Settings(api_key="unused", model="deepseek-v4-flash"),
                formal_required=False,
                semantic_evaluation=False,
                client=client,
            )
            report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(client.calls, 1)
            self.assertEqual(report["semantic_evaluator"]["status"], "not_run")
            self.assertIsNone(report["attribution"]["process_correct"])
            candidate = build_adjudication_candidate(
                case_id="deepseek-output",
                task_id="fifo_sync_v1",
                run_dir=directory,
                project_root=PROJECT_ROOT,
            )
            self.assertEqual(candidate["candidate_origin"], "real_model_output")
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_auditable_run_with_optional_eda_tools(self) -> None:
        directory = PROJECT_ROOT / "tests" / "work" / f"run-{uuid.uuid4().hex}"
        directory.mkdir(parents=True)
        try:
            result = run_experiment(
                "fifo_sync_v1",
                project_root=PROJECT_ROOT,
                run_dir=directory,
                settings=Settings(api_key="unused"),
                formal_required=False,
                client=FakeClient(),
            )
            report = json.loads(result.report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["dependency_graph"]["construction"], "static_before_eda")
            self.assertEqual(report["dependency_graph"]["digest"], report["attribution"]["graph_digest"])
            expected_rtl = (
                False if report["verification"]["simulation_available"] else None
            )
            self.assertEqual(
                report["verification"]["final_rtl_correct"], expected_rtl
            )
            self.assertEqual(report["candidate_generation"]["request_id"], "r1")
            self.assertEqual(report["semantic_evaluator"]["request_id"], "r2")
            self.assertTrue(report["semantic_evaluator"]["gold_labels_required_for_validation"])
            candidate = build_adjudication_candidate(
                case_id="pending-1",
                task_id="fifo_sync_v1",
                run_dir=directory,
                project_root=PROJECT_ROOT,
            )
            self.assertEqual(
                candidate["adjudication"]["status"], "pending_human"
            )
            self.assertFalse(candidate["adjudication"]["gold_fields_present"])
            self.assertEqual(candidate["candidate_origin"], "real_hy3")
            self.assertNotIn("gold_process_correct", candidate)

            artifact_directory = (
                PROJECT_ROOT / "tests" / "work" / f"artifact-{uuid.uuid4().hex}"
            )
            artifact = run_artifact_experiment(
                "fifo_sync_v1",
                process_path=result.process_path,
                project_root=PROJECT_ROOT,
                run_dir=artifact_directory,
                settings=Settings(api_key="unused"),
                formal_required=False,
                client=JudgeOnlyClient(),
            )
            artifact_report = json.loads(
                artifact.report_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                artifact_report["candidate_generation"]["origin"],
                "provided_artifact",
            )
            self.assertEqual(
                artifact_report["semantic_evaluator"]["request_id"],
                "judge-only",
            )
            shutil.rmtree(artifact_directory, ignore_errors=True)
        finally:
            shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
