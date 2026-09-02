from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolStatus:
    name: str
    available: bool
    path: str | None
    version: str | None


TOOL_COMMANDS = {
    "iverilog": ["iverilog", "-V"],
    "vvp": ["vvp", "-V"],
    "verilator": ["verilator", "--version"],
    "yosys": ["yosys", "-V"],
    "sby": ["sby", "--version"],
}


def resolve_executable(name: str) -> str | None:
    """Resolve an EDA tool from an explicit suite bin before consulting PATH."""
    configured_bin = os.getenv("RTLREASON_EDA_BIN", "").strip()
    if configured_bin:
        base = Path(configured_bin).expanduser()
        candidate_names = [f"{name}.exe", f"{name}.cmd", f"{name}.bat"]
        if name == "verilator":
            candidate_names.append("verilator_bin.exe")
        candidate_names.append(name)
        for candidate_name in candidate_names:
            candidate = base / candidate_name
            if candidate.is_file():
                return str(candidate.resolve())
    return shutil.which(name)


def eda_subprocess_env(executable: str | None = None) -> dict[str, str]:
    """Build the environment needed by a portable OSS CAD Suite install."""
    environment = os.environ.copy()
    configured_bin = os.getenv("RTLREASON_EDA_BIN", "").strip()
    bin_path = Path(configured_bin).resolve() if configured_bin else None
    if bin_path is None and executable:
        candidate = Path(executable).resolve().parent
        if candidate.name.lower() == "bin":
            bin_path = candidate
    if bin_path is None:
        return environment

    suite_root = bin_path.parent
    lib_path = suite_root / "lib"
    prefixes = [str(bin_path)]
    if lib_path.is_dir():
        prefixes.append(str(lib_path))
    current_path = environment.get("PATH", "")
    environment["PATH"] = os.pathsep.join([*prefixes, current_path])
    environment.setdefault("YOSYSHQ_ROOT", f"{suite_root}{os.sep}")
    certificate = suite_root / "etc" / "cacert.pem"
    if certificate.is_file():
        environment.setdefault("SSL_CERT_FILE", str(certificate))
    return environment


def detect_toolchain() -> list[ToolStatus]:
    results: list[ToolStatus] = []
    for name, command in TOOL_COMMANDS.items():
        path = resolve_executable(command[0])
        version = None
        if path:
            try:
                completed = subprocess.run(
                    [path, *command[1:]],
                    env=eda_subprocess_env(path),
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                output = (completed.stdout or completed.stderr).strip().splitlines()
                version = output[0] if output else None
            except (OSError, subprocess.SubprocessError) as exc:
                version = f"unusable: {exc}"
        results.append(ToolStatus(name, bool(path), path, version))
    return results
