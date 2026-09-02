from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BASE_URL = "https://tokenhub.tencentmaas.com/v1"


def load_env_file(path: str | Path = ".env", *, override: bool = False) -> bool:
    """Load a small dotenv file without logging any values."""
    env_path = Path(path)
    if not env_path.is_file():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value
    return True


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = "hy3"
    timeout_seconds: float = 180.0
    total_timeout_seconds: float = 600.0
    max_retries: int = 4
    temperature: float = 0.2
    reasoning_effort: str = "high"

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "Settings":
        load_env_file(env_file)
        return cls(
            api_key=os.getenv("HY3_API_KEY", "").strip(),
            base_url=os.getenv("HY3_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            model=os.getenv("HY3_MODEL", "hy3"),
            timeout_seconds=float(os.getenv("HY3_TIMEOUT_SECONDS", "180")),
            total_timeout_seconds=float(
                os.getenv("HY3_TOTAL_TIMEOUT_SECONDS", "600")
            ),
            max_retries=int(os.getenv("HY3_MAX_RETRIES", "4")),
            temperature=float(os.getenv("HY3_TEMPERATURE", "0.2")),
            reasoning_effort=os.getenv("HY3_REASONING_EFFORT", "high"),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
