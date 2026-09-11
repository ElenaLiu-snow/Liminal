"""Provider-neutral JSON model interface and DeepSeek HTTP adapter.

Only safe request metadata is returned to callers. API keys and model reasoning
content are never placed in receipts or logs.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol

from .pipeline import canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env.local"


class ProviderError(RuntimeError):
    """Raised when a model provider cannot return a usable JSON object."""


@dataclass(frozen=True)
class JsonModelResponse:
    payload: dict[str, Any]
    receipt: dict[str, Any]


class JsonModelClient(Protocol):
    def complete_json(self, prompt: str, *, stage: str) -> JsonModelResponse:
        """Return one JSON object plus non-sensitive request metadata."""


def load_env_file(path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """Read a small dotenv-style file without mutating process environment."""

    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ProviderError(f"invalid environment entry at {path.name}:{line_number}")
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not name or not name.replace("_", "").isalnum():
            raise ProviderError(f"invalid environment name at {path.name}:{line_number}")
        values[name] = value
    return values


def _positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ProviderError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ProviderError(f"{name} must be positive")
    return parsed


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-pro"
    timeout_seconds: int = 180
    max_tokens: int = 8192
    max_attempts: int = 3
    thinking: str = "disabled"
    reasoning_effort: str = "high"

    @classmethod
    def from_env(cls, path: Path = DEFAULT_ENV_PATH) -> "DeepSeekConfig":
        file_values = load_env_file(path)
        if path.is_file() and path.stat().st_mode & 0o077:
            raise ProviderError(
                f"{path.name} permissions are too broad; set them to 600 before use"
            )

        def setting(name: str, default: str = "") -> str:
            return os.environ.get(name, file_values.get(name, default)).strip()

        api_key = setting("DEEPSEEK_API_KEY")
        if not api_key:
            raise ProviderError(
                f"DEEPSEEK_API_KEY is missing; configure it in {path.name} or the process environment"
            )
        base_url = setting("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        if not base_url.startswith("https://"):
            raise ProviderError("DEEPSEEK_BASE_URL must use HTTPS")
        model = setting("DEEPSEEK_MODEL", "deepseek-v4-pro")
        if not model:
            raise ProviderError("DEEPSEEK_MODEL must be non-empty")
        thinking = setting("DEEPSEEK_THINKING", "disabled")
        if thinking not in {"enabled", "disabled"}:
            raise ProviderError("DEEPSEEK_THINKING must be enabled or disabled")
        reasoning_effort = setting("DEEPSEEK_REASONING_EFFORT", "high")
        if reasoning_effort not in {"low", "high", "max"}:
            raise ProviderError("DEEPSEEK_REASONING_EFFORT must be low, high, or max")
        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=_positive_int(
                setting("DEEPSEEK_TIMEOUT_SECONDS", "180"),
                "DEEPSEEK_TIMEOUT_SECONDS",
            ),
            max_tokens=_positive_int(
                setting("DEEPSEEK_MAX_TOKENS", "8192"), "DEEPSEEK_MAX_TOKENS"
            ),
            max_attempts=_positive_int(
                setting("DEEPSEEK_MAX_ATTEMPTS", "3"), "DEEPSEEK_MAX_ATTEMPTS"
            ),
            thinking=thinking,
            reasoning_effort=reasoning_effort,
        )


class DeepSeekClient:
    """Minimal standard-library client for DeepSeek's OpenAI-compatible API."""

    provider_name = "deepseek"

    def __init__(self, config: DeepSeekConfig) -> None:
        self.config = config

    @property
    def endpoint(self) -> str:
        return f"{self.config.base_url}/chat/completions"

    def _request_payload(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "response_format": {"type": "json_object"},
            "max_tokens": self.config.max_tokens,
            "thinking": {"type": self.config.thinking},
        }
        if self.config.thinking == "enabled":
            payload["reasoning_effort"] = self.config.reasoning_effort
        return payload

    def _post_json(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Liminal-v2-alpha/1",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _safe_provider_message(body: bytes) -> str:
        try:
            parsed = json.loads(body.decode("utf-8", errors="replace"))
            message = parsed.get("error", {}).get("message", "")
            if isinstance(message, str) and message:
                return message[:300]
        except (json.JSONDecodeError, AttributeError):
            pass
        return "provider returned an unreadable error response"

    def complete_json(self, prompt: str, *, stage: str) -> JsonModelResponse:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ProviderError("model prompt must be a non-empty string")
        if not isinstance(stage, str) or not stage.strip():
            raise ProviderError("model stage must be a non-empty string")

        request_payload = self._request_payload(prompt)
        last_error = "unknown provider error"
        attempts_used = 0
        for attempt in range(1, self.config.max_attempts + 1):
            attempts_used = attempt
            try:
                response = self._post_json(request_payload)
                choices = response.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise ProviderError("provider response contains no choices")
                choice = choices[0]
                content = choice.get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    usage = response.get("usage", {})
                    completion_tokens = (
                        usage.get("completion_tokens")
                        if isinstance(usage, Mapping)
                        else None
                    )
                    raise ProviderError(
                        "provider returned empty JSON content "
                        f"(finish_reason={choice.get('finish_reason')!r}, "
                        f"completion_tokens={completion_tokens!r})"
                    )
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise ProviderError("provider content is not valid JSON") from exc
                if not isinstance(parsed, dict):
                    raise ProviderError("provider JSON content must be an object")
                usage = response.get("usage")
                safe_usage = {
                    key: value
                    for key, value in usage.items()
                    if isinstance(key, str) and isinstance(value, (int, float))
                } if isinstance(usage, Mapping) else {}
                receipt = {
                    "provider": self.provider_name,
                    "stage": stage,
                    "requested_model": self.config.model,
                    "served_model": response.get("model"),
                    "response_id": response.get("id"),
                    "created": response.get("created"),
                    "finish_reason": choice.get("finish_reason"),
                    "attempts": attempt,
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "output_sha256": hashlib.sha256(
                        canonical_json(parsed).encode("utf-8")
                    ).hexdigest(),
                    "usage": safe_usage,
                }
                return JsonModelResponse(payload=parsed, receipt=receipt)
            except urllib.error.HTTPError as exc:
                message = self._safe_provider_message(exc.read())
                message = message.replace(self.config.api_key, "[REDACTED]")
                last_error = f"HTTP {exc.code}: {message}"
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable:
                    break
            except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                last_error = f"network error: {type(exc).__name__}"
            except (json.JSONDecodeError, ProviderError) as exc:
                last_error = str(exc)
            if attempt < self.config.max_attempts:
                time.sleep(min(2 ** (attempt - 1), 4))
        raise ProviderError(
            f"DeepSeek stage {stage!r} failed after {attempts_used} attempt(s): {last_error}"
        )
