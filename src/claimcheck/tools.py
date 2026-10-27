"""Strict model tool definitions and an evidence-numbered dispatcher."""

from __future__ import annotations

import copy
import re
from typing import Any

from .edgar import METRICS, EdgarClient


PERIOD_PATTERN = r"^(latest|FY\d{4}|\d{4}Q[1-4])$"
BASE_PERIOD_PATTERN = r"^(FY\d{4}|\d{4}Q[1-4])$"


LOOKUP_FACT_TOOL = {
    "type": "function",
    "name": "lookup_fact",
    "description": (
        "Look up one SEC EDGAR XBRL fact for a ticker, metric, and quarter or "
        "fiscal year. Successful results include duration_days and "
        "period_type (quarter, ytd, annual, or instant). Additive flows may "
        "return derived=true with derivation and components; never treat a "
        "ytd result as a quarter or recompute a derived result."
    ),
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

# Responses API function definitions do not carry a result schema, so keep the
# output contract next to the input definition for callers, tests, and prompt
# authors.  Error objects may contain ``error`` instead of these fact fields.
LOOKUP_FACT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "evidence_id": {"type": "string"},
        "value": {"type": ["number", "null"]},
        "start": {"type": ["string", "null"]},
        "end": {"type": ["string", "null"]},
        "duration_days": {"type": ["integer", "null"]},
        "period_type": {
            "type": "string",
            "enum": ["quarter", "ytd", "annual", "instant"],
        },
        "form_fallback": {"type": "boolean"},
        "derived": {"type": "boolean"},
        "derivation": {"type": "string"},
        "components": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": ["number", "null"]},
                    "start": {"type": ["string", "null"]},
                    "end": {"type": ["string", "null"]},
                    "accn": {"type": "string"},
                    "form": {"type": ["string", "null"]},
                    "filed": {"type": ["string", "null"]},
                    "duration_days": {"type": ["integer", "null"]},
                    "period_type": {
                        "type": "string",
                        "enum": ["quarter", "ytd", "annual", "instant"],
                    },
                },
                "required": [
                    "value",
                    "start",
                    "end",
                    "accn",
                    "form",
                    "filed",
                    "duration_days",
                    "period_type",
                ],
            },
        },
    },
}

COMPUTE_CHANGE_TOOL = {
    "type": "function",
    "name": "compute_change",
    "description": (
        "Compute the absolute and year-over-year change for one SEC EDGAR XBRL "
        "metric. The period and base_period must be the same kind of period; "
        "when base_period is omitted, null, empty, \"null\", or \"none\", use "
        "the same quarter or fiscal year one year earlier. The result includes "
        "both cited lookup facts and a percentage change in percent points."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "metric": {"type": "string", "enum": list(METRICS)},
            "period": {"type": "string", "pattern": PERIOD_PATTERN},
            "base_period": {
                "type": ["string", "null"],
                "pattern": BASE_PERIOD_PATTERN,
            },
        },
        "required": ["ticker", "metric", "period", "base_period"],
        "additionalProperties": False,
    },
    "strict": True,
}

HISTORY_RANK_TOOL = {
    "type": "function",
    "name": "history_rank",
    "description": (
        "Compare one quarter or fiscal-year fact with every available comparable "
        "period of the same period_type. Quarters include derived Q4 values when "
        "available; annual periods are compared only with annual periods. Return "
        "the rank, record flags, prior high/low, and the comparison window."
    ),
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

HISTORY_RANK_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "metric": {"type": "string"},
        "period": {"type": "string"},
        "period_type": {
            "type": "string",
            "enum": ["quarter", "annual", "ytd", "instant"],
        },
        "value": {"type": ["number", "null"]},
        "rank": {"type": ["integer", "null"]},
        "count": {"type": ["integer", "null"]},
        "is_highest": {"type": "boolean"},
        "is_lowest": {"type": "boolean"},
        "previous_high": {"type": ["object", "null"]},
        "previous_low": {"type": ["object", "null"]},
        "periods_considered": {"type": "object"},
        "periods": {"type": "array"},
        "comparable_periods": {"type": "array"},
        "error": {"type": "string"},
        "message": {"type": "string"},
        "evidence_id": {"type": "string"},
    },
    "required": [
        "ticker",
        "metric",
        "period",
        "period_type",
        "value",
        "rank",
        "count",
        "is_highest",
        "is_lowest",
        "previous_high",
        "previous_low",
        "periods_considered",
        "periods",
        "evidence_id",
    ],
    "additionalProperties": True,
}

COMPUTE_CHANGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "metric": {"type": "string"},
        "period": {"type": "string"},
        "base_period": {"type": "string"},
        "current_fact": {"$ref": "#/$defs/fact"},
        "base_fact": {"$ref": "#/$defs/fact"},
        "current": {"$ref": "#/$defs/fact"},
        "base": {"$ref": "#/$defs/fact"},
        "abs_change": {"type": ["number", "null"]},
        "pct_change": {"type": ["number", "null"]},
        "error": {"type": "string"},
        "message": {"type": "string"},
        "available_periods": {"type": "array", "items": {"type": "string"}},
        "evidence_id": {"type": "string"},
    },
    "required": [
        "ticker",
        "metric",
        "period",
        "base_period",
        "current_fact",
        "base_fact",
        "abs_change",
        "pct_change",
        "evidence_id",
    ],
    "additionalProperties": True,
    "$defs": {"fact": LOOKUP_FACT_OUTPUT_SCHEMA},
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

TOOL_DEFINITIONS = [
    LOOKUP_FACT_TOOL,
    LIST_PERIODS_TOOL,
    COMPUTE_CHANGE_TOOL,
    HISTORY_RANK_TOOL,
]
# Public aliases for callers that prefer schema terminology.
LOOKUP_FACT_SCHEMA = LOOKUP_FACT_TOOL
LIST_PERIODS_SCHEMA = LIST_PERIODS_TOOL
COMPUTE_CHANGE_SCHEMA = COMPUTE_CHANGE_TOOL
HISTORY_RANK_SCHEMA = HISTORY_RANK_TOOL
TOOL_SCHEMAS = {
    "lookup_fact": LOOKUP_FACT_TOOL,
    "list_periods": LIST_PERIODS_TOOL,
    "compute_change": COMPUTE_CHANGE_TOOL,
    "history_rank": HISTORY_RANK_TOOL,
}
TOOL_OUTPUT_SCHEMAS = {
    "lookup_fact": LOOKUP_FACT_OUTPUT_SCHEMA,
    "compute_change": COMPUTE_CHANGE_OUTPUT_SCHEMA,
    "history_rank": HISTORY_RANK_OUTPUT_SCHEMA,
}


class ToolValidationError(ValueError):
    """Raised internally for a malformed model tool call."""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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


def _validate_compute(args: Any) -> dict[str, str | None]:
    if not isinstance(args, dict):
        raise ToolValidationError("arguments must be an object")
    required = {"ticker", "metric", "period"}
    allowed = required | {"base_period"}
    if not required.issubset(args) or not set(args).issubset(allowed):
        missing = sorted(required - set(args))
        extra = sorted(set(args) - allowed)
        detail = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"additional={extra}")
        raise ToolValidationError("invalid arguments: " + ", ".join(detail))
    if not all(isinstance(args[key], str) for key in ("ticker", "metric", "period")):
        raise ToolValidationError("ticker, metric, and period must be strings")
    raw_base = args.get("base_period")
    if raw_base is not None and not isinstance(raw_base, str):
        raise ToolValidationError("base_period must be a string or null")

    ticker = args["ticker"].strip()
    metric = args["metric"].strip().lower()
    period = args["period"].strip().upper()
    if not ticker:
        raise ToolValidationError("ticker must not be empty")
    if metric not in METRICS:
        raise ToolValidationError(f"unknown metric: {metric}")
    if period != "LATEST" and not re.fullmatch(r"(?:FY\d{4}|\d{4}Q[1-4])", period):
        raise ToolValidationError(f"invalid period: {period}")

    base_text = raw_base.strip() if isinstance(raw_base, str) else ""
    base_period = base_text.upper()
    if base_period.lower() in {"", "null", "none"}:
        base_period = None
    if base_period is not None and not re.fullmatch(
        r"(?:FY\d{4}|\d{4}Q[1-4])", base_period
    ):
        raise ToolValidationError(f"invalid base_period: {base_period}")
    if base_period is None:
        base_period = _prior_year_period(period)
        if base_period is None:
            raise ToolValidationError(
                "base_period is required when period is latest"
            )
    if _period_kind(period) != _period_kind(base_period):
        raise ToolValidationError(
            "period and base_period must be the same kind: both fiscal years or both quarters"
        )
    return {
        "ticker": ticker,
        "metric": metric,
        "period": period,
        "base_period": base_period,
    }


def _validate_history(args: Any) -> dict[str, str]:
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
    if period != "LATEST" and not re.fullmatch(
        r"(?:FY\d{4}|\d{4}Q[1-4])", period
    ):
        raise ToolValidationError(f"invalid period: {period}")
    return {"ticker": ticker, "metric": metric, "period": period}


def _period_kind(period: str) -> str:
    if period.startswith("FY"):
        return "annual"
    if re.fullmatch(r"\d{4}Q[1-4]", period):
        return "quarter"
    return "latest"


def _prior_year_period(period: str) -> str | None:
    if match := re.fullmatch(r"FY(\d{4})", period):
        return f"FY{int(match.group(1)) - 1:04d}"
    if match := re.fullmatch(r"(\d{4})Q([1-4])", period):
        return f"{int(match.group(1)) - 1:04d}Q{match.group(2)}"
    return None


class ToolRunner:
    """Dispatch tools and assign stable evidence IDs for one verification run."""

    def __init__(self, edgar: EdgarClient) -> None:
        self.edgar = edgar
        self._next_evidence = 1
        self.evidence: dict[str, dict[str, Any]] = {}
        self.evidence_kind: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []

    def _number_result(self, result: Any, kind: str | None = None) -> dict[str, Any]:
        if isinstance(result, dict):
            numbered = copy.deepcopy(result)
        else:
            numbered = {"value": result}
        evidence_id = f"E{self._next_evidence}"
        self._next_evidence += 1
        numbered["evidence_id"] = evidence_id
        self.evidence[evidence_id] = numbered
        if kind is not None:
            self.evidence_kind[evidence_id] = kind
        return numbered

    def _compute_change(self, valid: dict[str, str | None]) -> dict[str, Any]:
        current = self.dispatch(
            "lookup_fact",
            {
                "ticker": valid["ticker"],
                "metric": valid["metric"],
                "period": valid["period"],
            },
        )
        base = self.dispatch(
            "lookup_fact",
            {
                "ticker": valid["ticker"],
                "metric": valid["metric"],
                "period": valid["base_period"],
            },
        )
        result: dict[str, Any] = {
            "ticker": valid["ticker"],
            "metric": valid["metric"],
            "period": valid["period"],
            "base_period": valid["base_period"],
            "current_fact": current,
            "base_fact": base,
            # Short aliases make the relationship obvious to callers inspecting
            # a tool result while the *_fact names stay unambiguous in schemas.
            "current": current,
            "base": base,
            "abs_change": None,
            "pct_change": None,
        }
        failed = current if "error" in current else base if "error" in base else None
        if failed is not None:
            result.update(
                {
                    "error": failed.get("error", "fact_not_found"),
                    "message": failed.get(
                        "message", "One of the requested facts could not be found."
                    ),
                }
            )
            if isinstance(failed.get("available_periods"), list):
                result["available_periods"] = failed["available_periods"]
            return result

        current_value = current.get("value")
        base_value = base.get("value")
        if not _is_number(current_value) or not _is_number(base_value):
            result.update(
                {
                    "error": "non_numeric_fact",
                    "message": "Both requested facts must have numeric values.",
                }
            )
            return result
        if float(base_value) == 0:
            result.update(
                {
                    "error": "zero_base_value",
                    "message": "Cannot compute percentage change from a zero base value.",
                }
            )
            return result
        abs_change = current_value - base_value
        pct_change = abs_change / abs(base_value) * 100
        result["abs_change"] = abs_change
        result["pct_change"] = pct_change
        return result

    def dispatch(self, name: str, args: Any) -> dict[str, Any]:
        """Validate and dispatch one tool call, returning an evidence object."""

        try:
            if name == "lookup_fact":
                valid = _validate_lookup(args)
                result = self.edgar.lookup_fact(**valid)
            elif name == "list_periods":
                valid = _validate_list(args)
                result = self.edgar.list_periods(**valid)
            elif name == "compute_change":
                valid = _validate_compute(args)
                result = self._compute_change(valid)
            elif name == "history_rank":
                valid = _validate_history(args)
                result = self.edgar.history_rank(**valid)
            else:
                raise ToolValidationError(f"unknown tool: {name}")
        except ToolValidationError as exc:
            result = {"error": "invalid_tool_call", "message": str(exc)}
        except Exception as exc:  # tool errors are evidence, not a model crash
            result = {"error": "tool_error", "message": str(exc)}

        numbered = self._number_result(result, name)
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
