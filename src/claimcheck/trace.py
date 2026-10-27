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


def _number(value: Any) -> int:
    """Return a non-negative integer token count from SDK or test-double data."""

    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, number)


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def usage_tokens(usage: Any) -> dict[str, int]:
    """Normalize SDK usage into the four evaluation accounting buckets."""

    if isinstance(usage, Mapping) and any(key in usage for key in ("input", "cached", "output", "reasoning")):
        return {
            "input": _number(usage.get("input")),
            "cached": min(_number(usage.get("input")), _number(usage.get("cached"))),
            "output": _number(usage.get("output")),
            "reasoning": _number(usage.get("reasoning")),
        }
    input_tokens = _number(_get(usage, "input_tokens"))
    input_details = _get(usage, "input_tokens_details")
    cached_tokens = min(input_tokens, _number(_get(input_details, "cached_tokens", 0)))
    output_tokens = _number(_get(usage, "output_tokens"))
    output_details = _get(usage, "output_tokens_details")
    reasoning_tokens = _number(
        _get(
            output_details,
            "reasoning_tokens",
            _get(usage, "reasoning_tokens", 0),
        )
    )
    return {
        "input": input_tokens,
        "cached": cached_tokens,
        "output": output_tokens,
        "reasoning": reasoning_tokens,
    }


class TraceRecorder:
    """Collect one verification trace in memory before writing it once."""

    def __init__(
        self,
        claim: str,
        model: str,
        *,
        provider: str = "meta",
        secrets: Iterable[str] = (),
    ) -> None:
        self.claim = claim
        self.model = model
        self.provider = provider
        self.secrets = tuple(secrets)
        self.requests: list[dict[str, Any]] = []
        self.tool_calls: list[dict[str, Any]] = []
        self.final_verdict: dict[str, Any] | None = None
        self.program_checks: list[dict[str, Any]] = []
        self.incomplete_turns: list[dict[str, Any]] = []
        self.previous_response_fallback = False

    def record_request(
        self,
        *,
        payload: Any,
        response: Any,
        reservation: Any,
        usage: Any,
        cost: float,
        latency_ms: float,
        status: str = "completed",
        raw_usage: Any = None,
        normalized_usage: Any = None,
        finish_reason: str | None = None,
        rate_limit_headers: Mapping[str, Any] | None = None,
        previous_response_fallback: bool = False,
    ) -> None:
        entry: dict[str, Any] = {
            "request": redact(model_dump(payload), self.secrets),
            "reservation": redact(model_dump(reservation), self.secrets),
            "raw_response": redact(model_dump(response), self.secrets),
            "usage": redact(model_dump(usage), self.secrets),
            "cost": cost,
            "latency_ms": round(latency_ms, 3),
            "status": status,
        }
        if raw_usage is not None:
            entry["raw_usage"] = redact(model_dump(raw_usage), self.secrets)
        if normalized_usage is not None:
            entry["normalized_usage"] = redact(model_dump(normalized_usage), self.secrets)
        if finish_reason is not None:
            entry["finish_reason"] = finish_reason
        if rate_limit_headers is not None:
            entry["rate_limit_headers"] = redact(model_dump(rate_limit_headers), self.secrets)
        if previous_response_fallback:
            entry["previous_response_fallback"] = True
        self.requests.append(entry)

    def mark_previous_response_fallback(self) -> None:
        self.previous_response_fallback = True

    def record_incomplete_turn(
        self,
        *,
        turn: int,
        attempt: int,
        phase: str,
        status: str,
        reason: Any,
        max_output_tokens: int,
    ) -> None:
        self.incomplete_turns.append(
            {
                "turn": turn,
                "attempt": attempt,
                "phase": phase,
                "status": status,
                "reason": reason,
                "max_output_tokens": max_output_tokens,
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

    @property
    def total_cost(self) -> float:
        return sum(float(item.get("cost", 0.0)) for item in self.requests)

    @property
    def total_latency_ms(self) -> float:
        return sum(float(item.get("latency_ms", 0.0)) for item in self.requests)

    @property
    def total_tokens(self) -> dict[str, int]:
        totals = {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
        for item in self.requests:
            for key, value in usage_tokens(item.get("usage")).items():
                totals[key] += value
        return totals

    @property
    def model_calls(self) -> int:
        return len(self.requests)

    @property
    def tool_call_count(self) -> int:
        return len(self.tool_calls)

    def summary(self) -> dict[str, Any]:
        return {
            "cost_usd": self.total_cost,
            "latency_ms": self.total_latency_ms,
            "tokens": self.total_tokens,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_call_count,
        }

    def as_dict(self) -> dict[str, Any]:
        total_cost = self.total_cost
        total_latency_ms = self.total_latency_ms
        return {
            "claim": self.claim,
            "model": self.model,
            "provider": self.provider,
            "requests": self.requests,
            "tool_calls": self.tool_calls,
            "usage": [item.get("usage") for item in self.requests],
            "tokens": self.total_tokens,
            "model_calls": self.model_calls,
            "cost": total_cost,
            "cost_usd": total_cost,
            "latency_ms": total_latency_ms,
            "tool_call_count": self.tool_call_count,
            "incomplete_turns": self.incomplete_turns,
            "previous_response_fallback": self.previous_response_fallback,
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
