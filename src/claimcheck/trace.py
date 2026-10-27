"""Trace recording with secret-safe model request/response serialization."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "secret",
    "password",
    "access_token",
    "refresh_token",
)
_TOKEN_SHAPE = re.compile(r"\b(?:sk|meta|hf)_[A-Za-z0-9_-]{12,}\b")


def model_dump(value: Any) -> Any:
    """Use the SDK's ``model_dump`` when present, with safe fallbacks."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): model_dump(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [model_dump(item) for item in value]
    dumper = getattr(value, "model_dump", None)
    if callable(dumper):
        try:
            return model_dump(dumper())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return model_dump(vars(value))
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def redact(value: Any, secrets: Iterable[str] = ()) -> Any:
    """Redact sensitive fields and exact known secrets recursively."""

    secret_values = [secret for secret in secrets if secret]
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
                result[str(key)] = "[REDACTED]"
            else:
                result[str(key)] = redact(item, secret_values)
        return result
    if isinstance(value, list):
        return [redact(item, secret_values) for item in value]
    if isinstance(value, str):
        cleaned = value
        for secret in secret_values:
            cleaned = cleaned.replace(secret, "[REDACTED]")
        return _TOKEN_SHAPE.sub("[REDACTED]", cleaned)
    return value


class TraceRecorder:
    """Collect one verification trace in memory before writing it once."""

    def __init__(
        self,
        claim: str,
        model: str,
        *,
        secrets: Iterable[str] = (),
    ) -> None:
        self.claim = claim
        self.model = model
        self.secrets = tuple(secrets)
        self.requests: list[dict[str, Any]] = []
        self.tool_calls: list[dict[str, Any]] = []
        self.final_verdict: dict[str, Any] | None = None
        self.program_checks: list[dict[str, Any]] = []

    def record_request(
        self,
        *,
        payload: Any,
        response: Any,
        reservation: Any,
        usage: Any,
        cost: float,
        latency_ms: float,
    ) -> None:
        self.requests.append(
            {
                "request": redact(model_dump(payload), self.secrets),
                "reservation": redact(model_dump(reservation), self.secrets),
                "raw_response": redact(model_dump(response), self.secrets),
                "usage": redact(model_dump(usage), self.secrets),
                "cost": cost,
                "latency_ms": round(latency_ms, 3),
            }
        )

    def record_tool_call(
        self, *, name: str, arguments: Any, call_id: str | None, result: Any
    ) -> None:
        self.tool_calls.append(
            {
                "name": name,
                "arguments": redact(model_dump(arguments), self.secrets),
                "call_id": call_id,
                "result": redact(model_dump(result), self.secrets),
            }
        )

    def finish(self, verdict: dict[str, Any]) -> None:
        self.final_verdict = redact(model_dump(verdict), self.secrets)
        self.program_checks = list(verdict.get("program_checks", []))

    def as_dict(self) -> dict[str, Any]:
        total_cost = sum(float(item.get("cost", 0.0)) for item in self.requests)
        return {
            "claim": self.claim,
            "model": self.model,
            "requests": self.requests,
            "tool_calls": self.tool_calls,
            "usage": [item.get("usage") for item in self.requests],
            "cost": total_cost,
            "final_verdict": self.final_verdict,
            "program_checks": self.program_checks,
        }


def write_trace(
    runs_dir: str | Path,
    trace: TraceRecorder | Mapping[str, Any],
) -> Path:
    """Write a UTC timestamped trace and return its path."""

    path_dir = Path(runs_dir)
    path_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    filename = now.strftime("%Y%m%dT%H%M%SZ") + f"-{uuid.uuid4().hex[:8]}.json"
    path = path_dir / filename
    value = trace.as_dict() if isinstance(trace, TraceRecorder) else dict(trace)
    path.write_text(
        json.dumps(redact(value), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return path
