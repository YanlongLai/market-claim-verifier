"""Strict model tool definitions and an evidence-numbered dispatcher."""

from __future__ import annotations

import copy
import re
from datetime import date
from typing import Any

from .edgar import METRICS, EdgarClient
from .release import ReleaseService
from .release_tools import RELEASE_TOOLS, dispatch_release


PERIOD_PATTERN = r"^(latest|FY\d{4}(?:Q[1-4])?|\d{4}Q[1-4])$"
BASE_PERIOD_PATTERN = r"^(FY\d{4}(?:Q[1-4])?|\d{4}Q[1-4])$"


PROVENANCE_SCHEMA = {
    "type": "object",
    "properties": {
        "tier": {"type": "string", "enum": ["L1", "L2", "L3", "L4"]},
        "component_tiers": {"type": "array", "items": {"type": "string"}},
        "component_strengths": {"type": "array", "items": {"type": "string"}},
        "audited": {"type": "boolean"},
        "confirmations": {"type": "integer", "minimum": 0},
        "forms": {"type": "array", "items": {"type": "string"}},
        "first_filed": {"type": ["string", "null"]},
        "latest_filed": {"type": ["string", "null"]},
        "restated": {"type": "boolean"},
        "values_seen": {"type": "array"},
        "amended": {"type": "boolean"},
        "form_fallback": {"type": "boolean"},
        "strength": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": [
        "tier",
        "audited",
        "confirmations",
        "forms",
        "first_filed",
        "latest_filed",
        "restated",
        "amended",
        "strength",
    ],
    "additionalProperties": True,
}


LOOKUP_FACT_TOOL = {
    "type": "function",
    "name": "lookup_fact",
    "description": (
        "Look up one SEC EDGAR XBRL fact for a ticker, metric, and calendar "
        "quarter, fiscal quarter (FY2025Q4), or fiscal year. Successful results "
        "include period (the normalized requested label, or the resolved label "
        "for latest), period_basis (calendar or fiscal), fiscal_equals_calendar, "
        "duration_days, and period_type (quarter, ytd, annual, or "
        "instant). Additive flows may "
        "return derived=true with derivation and components; never treat a "
        "ytd result as a quarter or recompute a derived result. When "
        "fiscal_equals_calendar is true, fiscal and calendar labels identify "
        "the same fact; do not look up both readings. Every fact includes compact "
        "provenance: L1 audited 10-K, L2 reviewed 10-Q, or L3 program-derived, "
        "with confirmations, restatement, amendment, and evidence strength."
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
        "period": {"type": "string"},
        "period_basis": {"type": "string", "enum": ["calendar", "fiscal"]},
        "fiscal_equals_calendar": {"type": "boolean"},
        "value": {"type": ["number", "null"]},
        "start": {"type": ["string", "null"]},
        "end": {"type": ["string", "null"]},
        "duration_days": {"type": ["integer", "null"]},
        "period_type": {
            "type": "string",
            "enum": ["quarter", "ytd", "annual", "instant"],
        },
        "provenance": PROVENANCE_SCHEMA,
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
                    "provenance": PROVENANCE_SCHEMA,
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
        "both cited lookup facts, fiscal_equals_calendar, their fact-level "
        "provenance, and a percentage change in percent points."
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
        "the rank, record flags through the requested period, prior high/low, "
        "and the comparison window with period end dates. The requested period "
        "also includes compact fact provenance and evidence strength."
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
        "period_basis": {"type": "string", "enum": ["calendar", "fiscal"]},
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
        "provenance": PROVENANCE_SCHEMA,
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
        "period_basis",
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
        "period_basis": {"type": "string", "enum": ["calendar", "fiscal"]},
        "fiscal_equals_calendar": {"type": "boolean"},
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
        "period_basis",
        "fiscal_equals_calendar",
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
    *RELEASE_TOOLS,
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
    **{tool["name"]: tool for tool in RELEASE_TOOLS},
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


def _resolved_fact_period(result: dict[str, Any]) -> str | None:
    """Infer the normalized period label for a ``latest`` fact result."""

    fiscal_year = result.get("fiscal_year", result.get("fy"))
    fiscal_period = str(result.get("fiscal_period", result.get("fp")) or "").upper()
    try:
        fiscal_year_int = int(fiscal_year)
    except (TypeError, ValueError):
        fiscal_year_int = None
    if fiscal_year_int is not None and fiscal_period in {"Q1", "Q2", "Q3", "Q4"}:
        return f"FY{fiscal_year_int:04d}{fiscal_period}"
    if fiscal_year_int is not None and fiscal_period == "FY":
        return f"FY{fiscal_year_int:04d}"

    frame = str(result.get("frame") or "").strip().upper()
    match = re.fullmatch(r"CY(?P<year>\d{4})(?P<quarter>Q[1-4])(?:I)?", frame)
    if match is not None:
        return f"{match.group('year')}{match.group('quarter')}"
    annual_match = re.fullmatch(r"CY(?P<year>\d{4})", frame)
    if annual_match is not None:
        return f"FY{annual_match.group('year')}"

    end_text = result.get("end")
    if not isinstance(end_text, str):
        return None
    try:
        end = date.fromisoformat(end_text)
    except ValueError:
        return None

    if result.get("period_type") == "annual":
        return f"FY{end.year}"
    start_text = result.get("start")
    if isinstance(start_text, str):
        try:
            duration = (end - date.fromisoformat(start_text)).days + 1
        except ValueError:
            duration = None
        if duration is not None and 300 <= duration <= 380:
            return f"FY{end.year}"

    # A quarter label is also the useful identity for an instant fact when
    # EDGAR does not provide a CY...I frame.
    return f"{end.year}Q{((end.month - 1) // 3) + 1}"


def _period_basis_for_label(period: str) -> str:
    return (
        "fiscal"
        if re.fullmatch(r"FY\d{4}(?:Q[1-4])?", str(period).strip().upper())
        else "calendar"
    )


def _add_lookup_period(result: Any, requested_period: str) -> Any:
    """Attach the requested/resolved identity to numeric lookup evidence."""

    if not isinstance(result, dict):
        return result
    period = requested_period
    if requested_period == "LATEST":
        period = _resolved_fact_period(result) or str(result.get("period") or "LATEST")
    period = period.strip().upper()
    basis = str(result.get("period_basis") or "").strip().lower()
    if basis not in {"calendar", "fiscal"}:
        basis = _period_basis_for_label(period)
    enriched = {
        **result,
        "period": period,
        "period_basis": basis,
    }
    if "fiscal_equals_calendar" in result:
        enriched["fiscal_equals_calendar"] = bool(result["fiscal_equals_calendar"])
    return enriched


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
    if period != "LATEST" and not re.fullmatch(
        r"(?:FY\d{4}(?:Q[1-4])?|\d{4}Q[1-4])", period
    ):
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
    if period != "LATEST" and not re.fullmatch(
        r"(?:FY\d{4}(?:Q[1-4])?|\d{4}Q[1-4])", period
    ):
        raise ToolValidationError(f"invalid period: {period}")

    base_text = raw_base.strip() if isinstance(raw_base, str) else ""
    base_period = base_text.upper()
    if base_period.lower() in {"", "null", "none"}:
        base_period = None
    if base_period is not None and not re.fullmatch(
        r"(?:FY\d{4}(?:Q[1-4])?|\d{4}Q[1-4])", base_period
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
        r"(?:FY\d{4}(?:Q[1-4])?|\d{4}Q[1-4])", period
    ):
        raise ToolValidationError(f"invalid period: {period}")
    return {"ticker": ticker, "metric": metric, "period": period}


def _period_kind(period: str) -> str:
    if re.fullmatch(r"FY\d{4}Q[1-4]", period):
        return "fiscal_quarter"
    if period.startswith("FY"):
        return "annual"
    if re.fullmatch(r"\d{4}Q[1-4]", period):
        return "calendar_quarter"
    return "latest"


def _prior_year_period(period: str) -> str | None:
    if match := re.fullmatch(r"FY(\d{4})Q([1-4])", period):
        return f"FY{int(match.group(1)) - 1:04d}Q{match.group(2)}"
    if match := re.fullmatch(r"FY(\d{4})", period):
        return f"FY{int(match.group(1)) - 1:04d}"
    if match := re.fullmatch(r"(\d{4})Q([1-4])", period):
        return f"{int(match.group(1)) - 1:04d}Q{match.group(2)}"
    return None


class ToolRunner:
    """Dispatch tools and assign stable evidence IDs for one verification run."""

    def __init__(self, edgar: EdgarClient, release_client: Any = None) -> None:
        self.edgar = edgar
        self._release_client = release_client
        self.release_service: ReleaseService | None = None
        self._next_evidence = 1
        self._next_program_evidence = 1
        self.evidence: dict[str, dict[str, Any]] = {}
        self.evidence_kind: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []

    def _number_result(
        self,
        result: Any,
        kind: str | None = None,
        *,
        prefix: str = "E",
    ) -> dict[str, Any]:
        if isinstance(result, dict):
            numbered = copy.deepcopy(result)
        else:
            numbered = {"value": result}
        if prefix == "P":
            evidence_id = f"P{self._next_program_evidence}"
            self._next_program_evidence += 1
        else:
            evidence_id = f"E{self._next_evidence}"
            self._next_evidence += 1
        numbered["evidence_id"] = evidence_id
        self.evidence[evidence_id] = numbered
        if kind is not None:
            self.evidence_kind[evidence_id] = kind
        return numbered

    def _compute_change(
        self,
        valid: dict[str, str | None],
        *,
        program: bool = False,
    ) -> dict[str, Any]:
        dispatch_lookup = self.dispatch_program if program else self.dispatch
        current = dispatch_lookup(
            "lookup_fact",
            {
                "ticker": valid["ticker"],
                "metric": valid["metric"],
                "period": valid["period"],
            },
        )
        base = dispatch_lookup(
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
            "period_basis": _period_basis_for_label(valid["period"]),
            "current_fact": current,
            "base_fact": base,
            # Short aliases make the relationship obvious to callers inspecting
            # a tool result while the *_fact names stay unambiguous in schemas.
            "current": current,
            "base": base,
            "abs_change": None,
            "pct_change": None,
        }
        fiscal_flags = [
            value
            for value in (
                current.get("fiscal_equals_calendar"),
                base.get("fiscal_equals_calendar"),
            )
            if isinstance(value, bool)
        ]
        if fiscal_flags:
            result["fiscal_equals_calendar"] = any(fiscal_flags)
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

    def _dispatch_result(
        self, name: str, args: Any, *, program: bool = False
    ) -> dict[str, Any]:
        try:
            if name in {"find_earnings_release", "quote_release"}:
                if self.release_service is None:
                    self.release_service = ReleaseService(self.edgar, self._release_client)
                result = dispatch_release(self.release_service, name, args)
            elif name == "lookup_fact":
                valid = _validate_lookup(args)
                result = _add_lookup_period(
                    self.edgar.lookup_fact(**valid), valid["period"]
                )
            elif name == "list_periods":
                valid = _validate_list(args)
                result = self.edgar.list_periods(**valid)
            elif name == "compute_change":
                valid = _validate_compute(args)
                result = self._compute_change(valid, program=program)
            elif name == "history_rank":
                valid = _validate_history(args)
                result = self.edgar.history_rank(**valid)
            else:
                raise ToolValidationError(f"unknown tool: {name}")
        except ToolValidationError as exc:
            result = {"error": "invalid_tool_call", "message": str(exc)}
        except Exception as exc:  # tool errors are evidence, not a model crash
            result = {"error": "tool_error", "message": str(exc)}

        return result

    def _dispatch_and_record(
        self,
        name: str,
        args: Any,
        *,
        role: str | None = None,
    ) -> dict[str, Any]:
        result = self._dispatch_result(name, args, program=role == "program")
        prefix = "P" if role == "program" else "E"
        numbered = self._number_result(result, name, prefix=prefix)
        call = {"name": name, "arguments": args, "result": numbered}
        if role is not None:
            call["role"] = role
        self.calls.append(call)
        return numbered

    def dispatch(self, name: str, args: Any) -> dict[str, Any]:
        """Validate and dispatch one model tool call, returning evidence."""

        return self._dispatch_and_record(name, args)

    def dispatch_program(self, name: str, args: Any) -> dict[str, Any]:
        """Dispatch a deterministic program-side lookup with a ``P`` evidence ID."""

        return self._dispatch_and_record(name, args, role="program")


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
