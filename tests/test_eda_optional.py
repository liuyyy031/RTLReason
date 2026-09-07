import shutil
import unittest
import uuid
from pathlib import Path

from rtlreason.dataset import load_task
from rtlreason.verification.iverilog import run_iverilog
from rtlreason.verification.toolchain import resolve_executable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = PROJECT_ROOT / "datasets" / "tasks" / "fifo_sync_v1"
TESTBENCH = TASK_ROOT / "testbench" / "tb_fifo_sync.sv"


@unittest.skipUnless(
    resolve_executable("iverilog") and resolve_executable("vvp"),
    "Icarus Verilog is unavailable",
)
class OptionalEdaRegressionTests(unittest.TestCase):
    def run_design(self, rtl: Path, task_id: str = "fifo_sync_v1"):
        task = load_task(task_id, project_root=PROJECT_ROOT)
        config = task.verification["simulation"]
        work = PROJECT_ROOT / "tests" / "work" / f"eda-{uuid.uuid4().hex}"
        work.mkdir(parents=True, exist_ok=False)
        try:
            return run_iverilog(
                rtl,
                task.root / config["testbench"],
                top=config["top"],
                vcd_name=config.get("vcd"),
                artifact_dir=work,
            )
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_both_reference_architectures_pass(self) -> None:
        references = TASK_ROOT / "reference_rtl"
        for name in ("count_fifo.sv", "wrapbit_fifo.sv"):
            with self.subTest(name=name):
                self.assertTrue(self.run_design(references / name).passed)

    def test_deliberate_faults_fail(self) -> None:
        faults = PROJECT_ROOT / "tests" / "fixtures" / "fifo_faults"
        for rtl in sorted(faults.glob("*.sv")):
            with self.subTest(name=rtl.name):
                result = self.run_design(rtl)
                self.assertTrue(result.available)
                self.assertFalse(result.passed)

    def test_new_task_references_pass_and_known_faults_fail(self) -> None:
        cases = (
            (
                "counter_enable_v1",
                "counter_enable.sv",
                "counter_wrong_priority.sv",
            ),
            (
                "shift_register_v1",
                "shift_register.sv",
                "shift_wrong_direction.sv",
            ),
            (
                "round_robin_arbiter_v1",
                "round_robin_arbiter.sv",
                "arbiter_fixed_priority.sv",
            ),
            (
                "ready_valid_slice_v1",
                "ready_valid_slice.sv",
                "ready_valid_no_replace.sv",
            ),
            (
                "request_ack_timeout_v1",
                "request_ack_timeout.sv",
                "request_ack_timeout_early.sv",
            ),
            (
                "ready_valid_fifo2_v1",
                "ready_valid_fifo2.sv",
                "ready_valid_fifo2_full_blocks.sv",
            ),
            (
                "sequence_detector_1011_v1",
                "sequence_detector_1011.sv",
                "sequence_detector_no_overlap.sv",
            ),
            (
                "pulse_stretcher_v1",
                "pulse_stretcher.sv",
                "pulse_stretcher_short.sv",
            ),
            (
                "grant_hold_arbiter_v1",
                "grant_hold_arbiter.sv",
                "grant_hold_reselect.sv",
            ),
            (
                "debounce_filter_v1",
                "debounce_filter.sv",
                "debounce_early.sv",
            ),
            (
                "token_bucket_v1",
                "token_bucket.sv",
                "token_bucket_lookahead.sv",
            ),
            (
                "rising_edge_detector_v1",
                "rising_edge_detector.sv",
                "rising_edge_level_detector.sv",
            ),
            (
                "dual_port_ram_sync_v1",
                "dual_port_ram_sync.sv",
                "dual_port_ram_write_first.sv",
            ),
            (
                "saturating_counter_v1",
                "saturating_counter.sv",
                "saturating_counter_wrap.sv",
            ),
            (
                "serial_parity_v1",
                "serial_parity.sv",
                "serial_parity_excludes_final.sv",
            ),
            (
                "programmable_timer_v1",
                "programmable_timer.sv",
                "programmable_timer_late.sv",
            ),
            (
                "interrupt_pending_v1",
                "interrupt_pending.sv",
                "interrupt_pending_clear_dominant.sv",
            ),
            (
                "stream_width_adapter_v1",
                "stream_width_adapter.sv",
                "stream_width_adapter_big_endian.sv",
            ),
            (
                "apb_register_bank_v1",
                "apb_register_bank.sv",
                "apb_register_bank_setup_write.sv",
            ),
        )
        faults = PROJECT_ROOT / "tests" / "fixtures" / "task_faults"
        for task_id, reference_name, fault_name in cases:
            task = load_task(task_id, project_root=PROJECT_ROOT)
            with self.subTest(task_id=task_id, kind="reference"):
                result = self.run_design(
                    task.root / "reference_rtl" / reference_name, task_id
                )
                self.assertTrue(result.passed)
            with self.subTest(task_id=task_id, kind="fault"):
                result = self.run_design(faults / fault_name, task_id)
                self.assertTrue(result.available)
                self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
