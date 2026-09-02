from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from rtlreason.config import Settings


class Hy3APIError(RuntimeError):
    """Raised when TokenHub returns a non-retryable or exhausted error."""


@dataclass(frozen=True)
class Hy3Response:
    content: str
    model: str
    usage: dict[str, Any]
    request_id: str | None = None
    finish_reason: str | None = None


Transport = Callable[[urllib.request.Request, float], bytes]


def _default_transport(request: urllib.request.Request, timeout: float) -> bytes:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def extract_json_object(
    text: str, *, required_keys: set[str] | None = None
) -> dict[str, Any]:
    """Extract a JSON object, optionally selecting one with required top keys."""
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        last_fence = stripped.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            stripped = stripped[first_newline + 1 : last_fence].strip()

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and (
            not required_keys or required_keys.issubset(value)
        ):
            return value
    suffix = (
        f" with required keys {sorted(required_keys)}" if required_keys else ""
    )
    raise ValueError(f"Hy3 response did not contain a valid JSON object{suffix}")


class Hy3Client:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: Transport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not settings.api_key:
            raise ValueError("HY3_API_KEY is not configured")
        self.settings = settings
        self._transport = transport or _default_transport
        self._sleep = sleeper

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        thinking: bool = True,
        reasoning_effort: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Hy3Response:
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
            "temperature": (
                self.settings.temperature if temperature is None else temperature
            ),
            "thinking": {"type": "enabled" if thinking else "disabled"},
            "reasoning_effort": reasoning_effort or self.settings.reasoning_effort,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        response = self._request("POST", "/chat/completions", payload)
        try:
            choice = response["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise Hy3APIError("TokenHub response did not contain assistant content") from exc
        return Hy3Response(
            content=str(content),
            model=str(response.get("model", self.settings.model)),
            usage=dict(response.get("usage", {})),
            request_id=response.get("id"),
            finish_reason=choice.get("finish_reason"),
        )

    def list_models(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/models", None)
        return list(response.get("data", []))

    def _request(
        self, method: str, path: str, payload: dict[str, Any] | None
    ) -> dict[str, Any]:
        url = f"{self.settings.base_url}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "RTLReason/0.1",
            },
        )

        deadline = time.monotonic() + self.settings.total_timeout_seconds
        for attempt in range(self.settings.max_retries + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Hy3APIError("TokenHub request exceeded its total time limit")
            try:
                raw = self._transport(
                    request, min(self.settings.timeout_seconds, remaining)
                )
                value = json.loads(raw.decode("utf-8"))
                if not isinstance(value, dict):
                    raise Hy3APIError("TokenHub returned a non-object JSON response")
                return value
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:2000]
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if retryable and attempt < self.settings.max_retries:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    delay = float(retry_after) if retry_after else self._backoff(attempt)
                    if delay >= deadline - time.monotonic():
                        raise Hy3APIError(
                            "TokenHub request exceeded its total time limit"
                        ) from exc
                    self._sleep(delay)
                    continue
                raise Hy3APIError(f"TokenHub HTTP {exc.code}: {body}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < self.settings.max_retries:
                    delay = self._backoff(attempt)
                    if delay >= deadline - time.monotonic():
                        raise Hy3APIError(
                            "TokenHub request exceeded its total time limit"
                        ) from exc
                    self._sleep(delay)
                    continue
                raise Hy3APIError(f"TokenHub request failed: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise Hy3APIError("TokenHub returned invalid JSON") from exc
        raise Hy3APIError("TokenHub retry loop exhausted")

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(20.0, (2**attempt) + random.random())
