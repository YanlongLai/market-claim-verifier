"""Ephemeral, capability-ID logs projected from the structured event stream."""
from __future__ import annotations

import re
import time

from claimcheck.progress import safe_fields
from claimcheck.trace import redact

RUN_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
TTL = 300
MAX_LINES = 200
MAX_BUFFERS = 1000


def member_id(run_id, index):
    """Compare members use adjacent low nibbles; UUID version/variant stay v4."""
    return run_id[:-1] + format((int(run_id[-1], 16) + index) % 16, "x")


def terminal_text(kind, fields):
    values = safe_fields(kind, fields)
    if kind == "program_check":
        return "program_check  count=1"
    if kind not in {"start", "preprocessing", "model", "tool_call", "tool_result", "verdict", "error"}:
        return None
    parts = [kind]
    order = {
        "start": ("provider", "model", "kind"),
        "preprocessing": ("phase", "kind", "cost_usd"),
        "model": ("step", "phase", "cost_usd"),
        "tool_call": ("name", "ticker", "metric", "base_period", "period"),
        "tool_result": ("name", "ticker", "metric", "period", "evidence_id", "value", "pct_change", "abs_change", "unit", "form"),
        "verdict": ("verdict", "claims", "cost_usd"),
        "error": ("code", "provider_status", "cost_usd"),
    }
    for key in order[kind]:
        if key not in values:
            continue
        value = values[key]
        if key == "cost_usd":
            parts.append(f"${value:.5f}")
        elif key == "evidence_id":
            parts.append("→ " + value)
        elif key in {"step", "claims", "base_period", "pct_change", "abs_change", "provider_status"}:
            parts.append(f"{key}={value}")
        else:
            parts.append(str(value))
    return "  ".join(parts)


class ProgressBuffer:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.runs = {}

    def prune(self):
        now = self.clock()
        self.runs = {key: row for key, row in self.runs.items() if row["expires"] > now}

    def create(self, run_id):
        self.prune()
        if run_id in self.runs or len(self.runs) >= MAX_BUFFERS:
            return False
        self.runs[run_id] = {"expires": self.clock() + TTL, "lines": [], "next": 0, "done": False}
        return True

    def event(self, run_id, elapsed, kind, fields, secrets=()):
        self.prune()
        row = self.runs.get(run_id)
        if not row or row["done"]:
            return
        text = terminal_text(kind, fields)
        if text is None:
            return
        if kind == "verdict":
            text += f"  duration={elapsed:.1f}s"
        # The same secret redactor protects the pod and public terminal.
        row["lines"].append({"t_s": round(max(0, elapsed), 3), "text": redact(text, secrets)[:512]})
        row["next"] += 1
        del row["lines"][:-MAX_LINES]

    def finish(self, run_id):
        if run_id in self.runs:
            self.runs[run_id]["done"] = True

    def read(self, run_id, after=0):
        self.prune()
        row = self.runs.get(run_id)
        if row is None:
            return None
        base = row["next"] - len(row["lines"])
        return {"lines": row["lines"][max(0, after - base):], "done": row["done"], "next": row["next"]}
