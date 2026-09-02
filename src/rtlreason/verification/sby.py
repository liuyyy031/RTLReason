from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from rtlreason.verification.toolchain import eda_subprocess_env, resolve_executable


@dataclass(frozen=True)
class FormalResult:
    available: bool
    passed: bool | None
    returncode: int | None
    output: str


def classify_sby_result(returncode: int, output: str) -> bool | None:
    """Map an SBY outcome to proof pass/fail without treating tool errors as fails."""
    outcomes = re.findall(r"DONE \((PASS|FAIL|UNKNOWN|ERROR)", output.upper())
    if outcomes:
        if outcomes[-1] == "PASS":
            return True
        if outcomes[-1] == "FAIL":
            return False
        return None
    if returncode == 0:
        return True
    return None


def run_sby(config_path: str | Path) -> FormalResult:
    executable = resolve_executable("sby")
    if not executable:
        return FormalResult(False, None, None, "SymbiYosys is unavailable")
    config = Path(config_path).resolve()
    result = subprocess.run(
        [executable, "-f", str(config)],
        cwd=config.parent,
        capture_output=True,
        env=eda_subprocess_env(executable),
        text=True,
        timeout=300,
        check=False,
    )
    output = result.stdout + result.stderr
    return FormalResult(
        True,
        classify_sby_result(result.returncode, output),
        result.returncode,
        output,
    )


def run_bounded_formal(
    rtl_path: str | Path,
    harness_path: str | Path,
    *,
    depth: int = 24,
    top: str = "fifo_formal",
    artifact_dir: str | Path | None = None,
) -> FormalResult:
    """Run a task-specific bounded safety harness in an isolated work directory."""
    if not resolve_executable("sby"):
        return FormalResult(False, None, None, "SymbiYosys is unavailable")
    configured_workdir = os.getenv("RTLREASON_FORMAL_WORKDIR", "").strip()
    requested_destination = Path(
        configured_workdir
        or artifact_dir
        or (Path.cwd() / "artifacts" / "formal")
    ).resolve()
    if (
        os.name == "nt"
        and not configured_workdir
        and not str(requested_destination).isascii()
    ):
        # OSS CAD Suite's bundled Python cannot open an SBY file through a
        # non-ASCII Windows path. Keep the ephemeral SBY workspace in an
        # ASCII-safe temp root; returned evidence remains task/run scoped.
        destination = Path(tempfile.gettempdir()) / "rtlreason-formal"
    else:
        destination = requested_destination
    destination.mkdir(parents=True, exist_ok=True)
    work = destination / f".work-{uuid.uuid4().hex}"
    work.mkdir(parents=False, exist_ok=False)
    try:
        shutil.copy2(Path(rtl_path).resolve(), work / "candidate.sv")
        shutil.copy2(Path(harness_path).resolve(), work / "harness.sv")
        config = work / "task.sby"
        config.write_text(
            "\n".join(
                [
                    "[options]", "mode bmc", f"depth {depth}",
                    "multiclock on", "", "[engines]", "smtbmc boolector",
                    "", "[script]",
                    "read -formal candidate.sv harness.sv",
                    f"prep -top {top}", "", "[files]",
                    "candidate.sv", "harness.sv", "",
                ]
            ),
            encoding="utf-8",
        )
        result = run_sby(config)
        if result.returncode not in (None, 0):
            diagnostics: list[str] = []
            for log_path in sorted((work / "task").glob("**/*.log")):
                try:
                    content = log_path.read_text(
                        encoding="utf-8", errors="replace"
                    )
                except OSError:
                    continue
                diagnostics.append(
                    f"\n--- {log_path.relative_to(work)} ---\n{content[-12000:]}"
                )
            if diagnostics:
                result = FormalResult(
                    result.available,
                    result.passed,
                    result.returncode,
                    result.output + "".join(diagnostics),
                )
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_fifo_formal(
    rtl_path: str | Path,
    harness_path: str | Path,
    *,
    depth: int = 24,
    top: str = "fifo_formal",
    artifact_dir: str | Path | None = None,
) -> FormalResult:
    """Backward-compatible alias for the original FIFO-only API."""
    return run_bounded_formal(
        rtl_path,
        harness_path,
        depth=depth,
        top=top,
        artifact_dir=artifact_dir,
    )
