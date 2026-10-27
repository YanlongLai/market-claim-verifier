"""Strict model tool definitions and an evidence-numbered dispatcher."""

from __future__ import annotations

import copy
import re
from typing import Any

from .edgar import METRICS, EdgarClient


PERIOD_PATTERN = r"^(latest|FY\d{4}|\d{4}Q[1-4])$"


LOOKUP_FACT_TOOL = {
    "type": "function",
    "name": "lookup_fact",
    "description": "Look up one SEC EDGAR XBRL fact for a ticker, metric, and quarter or fiscal year.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "metric": {"type": "string", "enum": list(METRICS)},
            "period": {"type": "string", "pattern": PERIOD_PATTERN},
        },
        "required": ["ticker", "metric", "period"],
        "additionalProperties": False,
    },
    "strict": True,
}

LIST_PERIODS_TOOL = {
    "type": "function",
    "name": "list_periods",
    "description": "List the recent directly available SEC EDGAR quarter and fiscal-year periods for a ticker and metric.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "metric": {"type": "string", "enum": list(METRICS)},
        },
        "required": ["ticker", "metric"],
        "additionalProperties": False,
    },
    "strict": True,
}

TOOL_DEFINITIONS = [LOOKUP_FACT_TOOL, LIST_PERIODS_TOOL]
# Public aliases for callers that prefer schema terminology.
LOOKUP_FACT_SCHEMA = LOOKUP_FACT_TOOL
LIST_PERIODS_SCHEMA = LIST_PERIODS_TOOL
TOOL_SCHEMAS = {"lookup_fact": LOOKUP_FACT_TOOL, "list_periods": LIST_PERIODS_TOOL}


class ToolValidationError(ValueError):
    """Raised internally for a malformed model tool call."""


def _validate_lookup(args: Any) -> dict[str, str]:
    if not isinstance(args, dict):
        raise ToolValidationError("arguments must be an object")
    required = {"ticker", "metric", "period"}
    if set(args) != required:
        missing = sorted(required - set(args))
        extra = sorted(set(args) - required)
        detail = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"additional={extra}")
        raise ToolValidationError("invalid arguments: " + ", ".join(detail))
    if not all(isinstance(args[key], str) for key in required):
        raise ToolValidationError("ticker, metric, and period must be strings")
    ticker = args["ticker"].strip()
    metric = args["metric"].strip().lower()
    period = args["period"].strip().upper()
    if not ticker:
        raise ToolValidationError("ticker must not be empty")
    if metric not in METRICS:
        raise ToolValidationError(f"unknown metric: {metric}")
    if period != "LATEST" and not re.fullmatch(r"(?:FY\d{4}|\d{4}Q[1-4])", period):
        raise ToolValidationError(f"invalid period: {period}")
    return {"ticker": ticker, "metric": metric, "period": period}


def _validate_list(args: Any) -> dict[str, str]:
    if not isinstance(args, dict):
        raise ToolValidationError("arguments must be an object")
    required = {"ticker", "metric"}
    if set(args) != required:
        missing = sorted(required - set(args))
        extra = sorted(set(args) - required)
        detail = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"additional={extra}")
        raise ToolValidationError("invalid arguments: " + ", ".join(detail))
    if not isinstance(args["ticker"], str) or not isinstance(args["metric"], str):
        raise ToolValidationError("ticker and metric must be strings")
    ticker = args["ticker"].strip()
    metric = args["metric"].strip().lower()
    if not ticker:
        raise ToolValidationError("ticker must not be empty")
    if metric not in METRICS:
        raise ToolValidationError(f"unknown metric: {metric}")
    return {"ticker": ticker, "metric": metric}


class ToolRunner:
    """Dispatch tools and assign stable evidence IDs for one verification run."""

    def __init__(self, edgar: EdgarClient) -> None:
        self.edgar = edgar
        self._next_evidence = 1
        self.evidence: dict[str, dict[str, Any]] = {}
        self.calls: list[dict[str, Any]] = []

    def _number_result(self, result: Any) -> dict[str, Any]:
        if isinstance(result, dict):
            numbered = copy.deepcopy(result)
        else:
            numbered = {"value": result}
        evidence_id = f"E{self._next_evidence}"
        self._next_evidence += 1
        numbered["evidence_id"] = evidence_id
        self.evidence[evidence_id] = numbered
        return numbered

    def dispatch(self, name: str, args: Any) -> dict[str, Any]:
        """Validate and dispatch one tool call, returning an evidence object."""

        try:
            if name == "lookup_fact":
                valid = _validate_lookup(args)
                result = self.edgar.lookup_fact(**valid)
            elif name == "list_periods":
                valid = _validate_list(args)
                result = self.edgar.list_periods(**valid)
            else:
                raise ToolValidationError(f"unknown tool: {name}")
        except ToolValidationError as exc:
            result = {"error": "invalid_tool_call", "message": str(exc)}
        except Exception as exc:  # tool errors are evidence, not a model crash
            result = {"error": "tool_error", "message": str(exc)}

        numbered = self._number_result(result)
        self.calls.append({"name": name, "arguments": args, "result": numbered})
        return numbered


def dispatch(
    name: str,
    args: Any,
    edgar: EdgarClient | None = None,
    runner: ToolRunner | None = None,
) -> dict[str, Any]:
    """Convenience wrapper used by callers that need a single dispatch.

    A caller with no injected client gets the normal cache-backed client, which
    keeps the public ``dispatch(name, args)`` form useful in a CLI or REPL.
    Agent runs pass a shared ``ToolRunner`` so evidence IDs remain run-local.
    """

    active_runner = runner or ToolRunner(edgar or EdgarClient())
    return active_runner.dispatch(name, args)
