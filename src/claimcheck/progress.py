"""Allowlisted, single-line progress summaries. Never serialize input or reasoning."""
from __future__ import annotations

import json
import math
import re
import time

from .tools import METRICS
from .trace import redact


def _token(value, pattern):
    return value if isinstance(value, str) and re.fullmatch(pattern, value) else None


def safe_fields(kind, fields):
    """Project arbitrary events onto finite names, validated labels and numbers."""
    out = {}
    for key in ("provider", "model", "kind", "phase", "name", "verdict", "code", "role", "unit", "form"):
        value = fields.get(key)
        allowed = {
            "provider": {"baseten", "fireworks", "meta"},
            "model": {"meta-models/muse-spark-open-1026", "accounts/fireworks/models/muse-spark-open",
                      "muse-spark-1.3", "muse-wonder-1.0"},
            "kind": {"text", "image", "pdf", "audio", "video"},
            "phase": {"running", "completed", "extraction", "verification", "dry_run"},
            "name": {"lookup_fact", "list_periods", "compute_change", "history_rank", "period_resolution"},
            "verdict": {"supported", "contradicted", "insufficient_evidence"},
            "role": {"program", "model"},
            "unit": {"USD", "USD/shares", "shares", "percent", "%", "pure"},
            "form": {"10-K", "10-Q", "10-K/A", "10-Q/A", "20-F", "40-F", "6-K", "8-K"},
        }.get(key)
        if allowed is not None and isinstance(value, str) and value in allowed:
            out[key] = value
    # Error messages/bodies are deliberately excluded, including tool errors.
    if kind == "error":
        from_codes = {"unavailable", "timeout", "provider_error", "credit_exhausted", "budget_exhausted",
                      "total_budget_exhausted", "rate_limited", "invalid_model_output", "incomplete_model",
                      "tool_limit", "out_of_scope", "sec_unavailable", "preprocessing_failed",
                      "example_unavailable", "invalid_input", "unknown_example", "unknown_provider",
                      "unauthorized", "auth_rate_limited", "not_found", "failed"}
        if isinstance(fields.get("code"), str) and fields["code"] in from_codes:
            out["code"] = fields["code"]
    for key in ("chars", "step", "claims", "claim_index", "status", "count",
                "supported", "contradicted", "insufficient_evidence"):
        value = fields.get(key)
        if type(value) is int and 0 <= value < 1_000_000:
            out[key] = value
    for key in ("cost_usd", "value", "pct_change", "abs_change"):
        value = fields.get(key)
        if type(value) in (int, float) and math.isfinite(value):
            out[key] = value
    if type(fields.get("cost_is_bound")) is bool:
        out["cost_is_bound"] = fields["cost_is_bound"]
    source = fields.get("arguments") if kind == "tool_call" else fields.get("result")
    if isinstance(source, dict):
        for key, pattern in (("ticker", r"[A-Z][A-Z0-9.-]{0,9}"),
                             ("period", r"latest|(?:FY)?[12][0-9]{3}(?:Q[1-4])?"),
                             ("base_period", r"(?:FY)?[12][0-9]{3}(?:Q[1-4])?"),
                             ("evidence_id", r"[ECP][1-9][0-9]{0,5}")):
            if value := _token(source.get(key), pattern):
                out[key] = value
        if isinstance(source.get("metric"), str) and source["metric"] in METRICS:
            out["metric"] = source["metric"]
        if kind == "tool_result":
            out.update(safe_fields("result", {k: source[k] for k in
                       ("value", "pct_change", "abs_change", "unit", "form") if k in source}))
    return out


def format_event(prefix, elapsed, kind, fields, *, secrets=()):
    kind = kind if kind in {"start", "model", "tool_call", "tool_result", "program_check",
                            "program_binding", "verdict", "error", "preprocessing", "claim", "receipt"} else "event"
    values = safe_fields(kind, fields)
    parts = [prefix, f"+{elapsed:.2f}s", f"event={kind}"]
    for key, value in values.items():
        if key == "cost_usd":
            parts.append(f"cost=${value:.4f}")
        else:
            encoded = str(value).lower() if isinstance(value, bool) else str(value)
            parts.append(f"{key}={encoded if re.fullmatch(r'[A-Za-z0-9_./%+-]+', encoded) else json.dumps(encoded)}")
    return redact(" ".join(parts), secrets)


class CLIProgress:
    def __init__(self, *, secrets=(), clock=time.monotonic):
        self.clock, self.start, self.secrets = clock, clock(), secrets

    def __call__(self, kind, fields):
        import sys
        print(format_event("cli", self.clock() - self.start, kind, fields, secrets=self.secrets),
              file=sys.stderr, flush=True)
