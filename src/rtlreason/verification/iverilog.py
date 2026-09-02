from __future__ import annotations

import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from rtlreason.verification.toolchain import eda_subprocess_env, resolve_executable


@dataclass(frozen=True)
class SimulationResult:
    available: bool
    passed: bool | None
    compile_returncode: int | None
    run_returncode: int | None
    output: str
    vcd_path: Path | None = None


def run_iverilog(
    rtl_path: str | Path,
    testbench_path: str | Path,
    *,
    top: str = "tb_fifo_sync",
    vcd_name: str | None = None,
    artifact_dir: str | Path | None = None,
) -> SimulationResult:
    iverilog = resolve_executable("iverilog")
    vvp = resolve_executable("vvp")
    if not iverilog or not vvp:
        return SimulationResult(False, None, None, None, "Icarus Verilog is unavailable")

    rtl = Path(rtl_path).resolve()
    testbench = Path(testbench_path).resolve()
    destination = Path(
        artifact_dir or (Path.cwd() / "artifacts" / "simulation")
    ).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    work = destination / f".work-{uuid.uuid4().hex}"
    work.mkdir(parents=False, exist_ok=False)
    try:
        executable = work / "simv"
        compile_result = subprocess.run(
            [
                iverilog,
                "-g2012",
                "-s",
                top,
                "-o",
                str(executable),
                str(rtl),
                str(testbench),
            ],
            capture_output=True,
            env=eda_subprocess_env(iverilog),
            text=True,
            timeout=60,
            check=False,
        )
        compile_output = compile_result.stdout + compile_result.stderr
        if compile_result.returncode != 0:
            return SimulationResult(
                True, False, compile_result.returncode, None, compile_output
            )
        run_result = subprocess.run(
            [vvp, str(executable)],
            cwd=work,
            capture_output=True,
            env=eda_subprocess_env(vvp),
            text=True,
            timeout=60,
            check=False,
        )
        output = compile_output + run_result.stdout + run_result.stderr
        passed = run_result.returncode == 0 and "RTLREASON_RESULT:PASS" in output
        source_vcd = work / (vcd_name or "fifo_sync.vcd")
        saved_vcd: Path | None = None
        if source_vcd.exists():
            saved_vcd = destination / source_vcd.name
            shutil.copy2(source_vcd, saved_vcd)
        return SimulationResult(
            True,
            passed,
            compile_result.returncode,
            run_result.returncode,
            output,
            saved_vcd,
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)
