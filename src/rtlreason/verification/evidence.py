from __future__ import annotations

import re
from pathlib import Path

from rtlreason.models import VerificationEvidence
from rtlreason.verification.iverilog import SimulationResult, run_iverilog
from rtlreason.verification.sby import FormalResult, run_bounded_formal


_OBLIGATION_FAILURE = re.compile(r"OBLIGATION_FAIL:([A-Z0-9_]+)")


def simulation_evidence(
    rtl_path: str | Path,
    testbench_path: str | Path,
    *,
    all_obligations: set[str],
    task_id: str = "fifo_sync",
    top: str = "tb_fifo_sync",
    vcd_name: str | None = None,
    artifact_dir: str | Path | None = None,
) -> tuple[SimulationResult, list[VerificationEvidence]]:
    result = run_iverilog(
        rtl_path,
        testbench_path,
        top=top,
        vcd_name=vcd_name,
        artifact_dir=artifact_dir,
    )
    if not result.available:
        return result, []
    if result.passed:
        obligations = tuple(sorted(all_obligations))
        return result, [
            VerificationEvidence(
                id=f"simulation:{task_id}",
                source="iverilog",
                status="pass",
                obligations=obligations,
                summary="Trusted directed simulation passed.",
            )
        ]

    detected = set(_OBLIGATION_FAILURE.findall(result.output)) & all_obligations
    obligations = tuple(sorted(detected or all_obligations))
    return result, [
        VerificationEvidence(
            id=f"simulation:{task_id}",
            source="iverilog",
            status="fail",
            obligations=obligations,
            summary="Trusted directed simulation failed.",
            details={
                "compile_returncode": result.compile_returncode,
                "run_returncode": result.run_returncode,
            },
        )
    ]


def formal_evidence(
    rtl_path: str | Path,
    harness_path: str | Path,
    *,
    formal_obligations: set[str],
    task_id: str = "fifo_sync",
    depth: int = 24,
    top: str = "fifo_formal",
    artifact_dir: str | Path | None = None,
) -> tuple[FormalResult, list[VerificationEvidence]]:
    result = run_bounded_formal(
        rtl_path,
        harness_path,
        depth=depth,
        top=top,
        artifact_dir=artifact_dir,
    )
    if not result.available:
        return result, []
    if result.passed is True:
        status = "pass"
        summary = f"Trusted bounded safety check passed (depth {depth})."
        mapped_obligations = tuple(sorted(formal_obligations))
    elif result.passed is False:
        status = "fail"
        summary = (
            "Trusted bounded safety check found a counterexample; the failing "
            "assertion is not yet mapped to a specific obligation."
        )
        mapped_obligations = ()
    else:
        status = "error"
        summary = "Formal toolchain error; no property verdict was produced."
        mapped_obligations = ()
    return result, [
        VerificationEvidence(
            id=f"formal:{task_id}_safety",
            source="symbiyosys",
            status=status,
            obligations=mapped_obligations,
            summary=summary,
            details={
                "returncode": result.returncode,
                "property_class": "safety",
                "formal_mode": "bmc",
                "depth": depth,
                "configured_obligations": tuple(sorted(formal_obligations)),
                "obligation_mapping": (
                    "all_properties_passed"
                    if result.passed is True
                    else "unresolved_counterexample"
                    if result.passed is False
                    else "unavailable"
                ),
            },
        )
    ]
