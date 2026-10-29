"""Meta Muse function-calling loop and deterministic evidence checks."""

from __future__ import annotations

import copy
import json
import math
import os
import re
import time
from collections.abc import Mapping
from typing import Any

from .budget import Ledger
from .checks import CLAIM_TYPES, COMPARATORS, evaluate_verdict
from .edgar import EdgarClient
from .providers import ParsedResponse, ProviderAdapter, get_provider
from .tools import TOOL_DEFINITIONS, ToolRunner
from .trace import TraceRecorder
from .release_tools import RELEASE_INSTRUCTIONS
from .period_context import missing_period_reason
from .retries import exception_status, retry_info, wait_for_retry


VERDICTS = ("supported", "contradicted", "insufficient_evidence")
MAX_TOOL_OUTPUT_TOKENS = 4_000
MAX_FINAL_OUTPUT_TOKENS = 3_000
MAX_OUTPUT_TOKENS_ENV = "CLAIMCHECK_MAX_OUTPUT_TOKENS"
REASONING_EFFORT_ENV = "CLAIMCHECK_REASONING_EFFORT"

SUB_CLAIM_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "stated_text": {"type": "string"},
        "claim_type": {"type": "string", "enum": list(CLAIM_TYPES)},
        "comparator": {"type": "string", "enum": list(COMPARATORS)},
        "stated_value": {"type": ["number", "null"]},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "interpretations": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "evidence id like E3 — never free text",
            },
        },
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "note": {"type": "string"},
        "model_found_value": {"type": ["number", "null"]},
    },
    "required": [
        "text",
        "stated_text",
        "claim_type",
        "comparator",
        "stated_value",
        "evidence_ids",
        "interpretations",
        "verdict",
        "note",
        "model_found_value",
    ],
    "additionalProperties": False,
}

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "summary": {"type": "string"},
        "sub_claims": {"type": "array", "items": SUB_CLAIM_SCHEMA},
    },
    "required": ["verdict", "summary", "sub_claims"],
    "additionalProperties": False,
}


SYSTEM_INSTRUCTIONS = """You verify financial claims against SEC EDGAR facts.
Decompose the claim into every atomic factual assertion. Every factual assertion
in the user's claim must become a sub-claim, including a value, a change, a
record, and a first-time assertion in the same sentence. Assertions that the
tools cannot check must still become a sub-claim with claim_type other; the
program will leave those unchecked. Use lookup_fact for a value,
compute_change for YoY or other period-to-period growth, history_rank for
record/first-time assertions, and list_periods only to understand missing data.
Never use memory for numbers. A quarter must have period_type=quarter and
duration_days around 80-100, not period_type=ytd. If a result has derived=true,
use its derivation and components as evidence and do not calculate that fact
again. For compute_change, cite its own evidence ID; its two nested component
fact IDs may also be cited and are ignored by the verifier.

Each final sub_claim must contain exactly these model fields:
text, stated_text, claim_type (value, change_pct, change_abs, record_high,
record_low, first_time_above, or other), comparator (eq, approx, gt, gte, lt,
or lte), stated_value in base units (USD, USD/share, percentage points, or 1
for a record boolean), evidence_ids, interpretations, verdict, note, and
model_found_value. interpretations is required and may be empty. Every non-empty
item must be an evidence id like E3 — never free text.
Copy stated_text verbatim from the claim, including words such as "about",
"up", or "fell" (for example, "about $1.4 billion", "up 22%", or
"fell 10%"). For a change_pct, stated_value is 22 for 22%, not 0.22; the
verifier applies the sign implied by direction words such as fell/down or
rose/up. model_found_value is the number read from the cited evidence in the
same units, or null when it is missing.

Comparator wording is deterministic: a plain numeric statement with no hedge
or inequality phrase is eq; about/around/roughly/approximately/nearly/almost,
close to, some, or ~ means approx; topped/exceeded/above/more than/over/
surpassed/beat means gt; at least/no less than means gte; below/under/less
than/short of means lt; at most/no more than/up to means lte. The program
records and may correct the model comparator from these words. "up" and
"fell" describe change direction, not approximation.

For a quarter claim at a non-calendar-fiscal issuer, use period_basis from
the tool results. If the claim says neither fiscal nor calendar, look up both
the calendar label (for example 2025Q4) and the fiscal label (for example
FY2025Q4), cite both IDs in evidence_ids, and put those two IDs in
interpretations. Keep interpretations empty unless both fiscal and calendar
readings were looked up. If the claim says fiscal, cite only the fiscal
reading; if it says calendar, cite only the calendar reading. When a lookup or
compute result has fiscal_equals_calendar=true, the issuer's fiscal year is the
calendar year: fiscal and calendar labels refer to the same underlying facts,
so look up and cite only one reading even when the claim has no
fiscal/calendar qualifier.

Examples:
1. "Tesla net income was about $1.4 billion": lookup_fact; stated_text
   "about $1.4 billion", claim_type value, comparator approx, stated_value
   1400000000.
2. "Alphabet revenue exceeded $100 billion": lookup_fact; stated_text
   "exceeded $100 billion", claim_type value, comparator gt, stated_value
   100000000000.
3. "Meta revenue was up 22% YoY": compute_change(META, revenue, 2025Q2,
   null); stated_text "up 22%", claim_type change_pct, comparator eq,
   stated_value 22, and cite the compute_change evidence ID.
4. "Tesla revenue fell 10% YoY": compute_change(TSLA, revenue, 2025Q3,
   null); stated_text "fell 10%", claim_type change_pct, comparator eq,
   stated_value -10, and cite the compute_change evidence ID.
5. "Alphabet Q3 2025 revenue was a record high": history_rank(GOOGL,
   revenue, 2025Q3); claim_type record_high, comparator eq, stated_value 1,
   and cite the history_rank evidence ID.
6. "Alphabet Q3 2025 revenue topped $100 billion for the first time": create
   two sub-claims: value gt 100000000000 and first_time_above with stated_value
   100000000000, both citing the relevant evidence; the latter is supported
   only when this period is above the threshold and no earlier comparable
   period is above it.
7. If a requested fact is unavailable, leave model_found_value null, cite any
   relevant evidence, and set that sub-claim to insufficient_evidence. Say
   insufficient_evidence when data is missing or evidence is ambiguous."""

AGENT_FINAL_VERDICT_PROMPT = (
    "Return the final structured verdict now. Include every atomic factual "
    "assertion as a sub-claim, including assertions that need claim_type other "
    "when the tools cannot check them. Copy stated_text verbatim from the claim; "
    "include claim_type, comparator, stated_value in base units, evidence_ids, "
    "interpretations (an array, possibly empty; non-empty items are evidence "
    "ids like E3, never free text), verdict, model_found_value, "
    "and a concise note."
)

SYSTEM_INSTRUCTIONS += RELEASE_INSTRUCTIONS


def _validate_output_tokens(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("max_output_tokens must be a positive integer")
    try:
        output_tokens = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_output_tokens must be a positive integer") from exc
    if output_tokens <= 0:
        raise ValueError("max_output_tokens must be a positive integer")
    return output_tokens


def _configured_max_output_tokens(value: int | None = None) -> int | None:
    if value is not None:
        return _validate_output_tokens(value)
    raw = os.environ.get(MAX_OUTPUT_TOKENS_ENV)
    if raw is None or not raw.strip():
        return None
    return _validate_output_tokens(raw)


def _configured_reasoning_effort(value: str | None = None) -> str | None:
    if value is not None:
        return value or None
    return os.environ.get(REASONING_EFFORT_ENV) or None


def _request_payload(
    payload: dict[str, Any],
    *,
    reasoning_effort: str | None,
) -> dict[str, Any]:
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    return payload


def initial_request(
    claim: str,
    model: str,
    *,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    provider: str | ProviderAdapter = "meta",
) -> dict[str, Any]:
    active_provider = get_provider(provider)
    if active_provider.name != "meta":
        configured_max = _configured_max_output_tokens(max_output_tokens)
        return active_provider.initial_request(
            claim,
            model,
            max_output_tokens=configured_max or MAX_TOOL_OUTPUT_TOKENS,
            reasoning_effort=_configured_reasoning_effort(reasoning_effort),
        )
    configured_max = _configured_max_output_tokens(max_output_tokens)
    payload = {
        "model": model,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": [{"role": "user", "content": claim}],
        "tools": TOOL_DEFINITIONS,
        "parallel_tool_calls": True,
        "max_output_tokens": configured_max or MAX_TOOL_OUTPUT_TOKENS,
    }
    return _request_payload(
        payload,
        reasoning_effort=_configured_reasoning_effort(reasoning_effort),
    )


def verdict_text_format() -> dict[str, Any]:
    """Isolated so the final structured-output request is easy to change."""

    return {
        "format": {
            "type": "json_schema",
            "name": "verdict",
            "schema": VERDICT_SCHEMA,
            "strict": True,
        }
    }


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _response_status(response: Any) -> str:
    if isinstance(response, ParsedResponse):
        return response.status
    status = _get(response, "status")
    return str(status) if status is not None else "completed"


def _incomplete_reason(response: Any) -> Any:
    if isinstance(response, ParsedResponse):
        return response.incomplete_reason
    details = _get(response, "incomplete_details")
    return _get(details, "reason") if details is not None else None


def _usage_dict(response: Any) -> dict[str, Any] | None:
    usage = _get(response, "usage")
    if usage is None:
        return None
    details = _get(usage, "input_tokens_details")
    cached = _get(details, "cached_tokens", 0) if details is not None else 0
    output_details = _get(usage, "output_tokens_details")
    reasoning = _get(output_details, "reasoning_tokens", 0) if output_details is not None else 0
    if reasoning is None:
        reasoning = _get(usage, "reasoning_tokens", 0)
    return {
        "input_tokens": _get(usage, "input_tokens"),
        "output_tokens": _get(usage, "output_tokens"),
        "input_tokens_details": {"cached_tokens": cached or 0},
        "output_tokens_details": {"reasoning_tokens": reasoning or 0},
    }


def _function_calls(response: Any) -> list[Any]:
    output = _get(response, "output", []) or []
    if not isinstance(output, list):
        output = [output]
    calls = []
    for item in output:
        if _get(item, "type") == "function_call":
            calls.append(item)
    return calls


def _call_id(call: Any) -> str | None:
    value = _get(call, "call_id") or _get(call, "id")
    return str(value) if value is not None else None


def _call_arguments(call: Any) -> Any:
    raw = _get(call, "arguments", {})
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _call_name(call: Any) -> str:
    return str(_get(call, "name") or "")


def _response_text(response: Any) -> str:
    if isinstance(response, ParsedResponse):
        return response.text
    output_text = _get(response, "output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    output = _get(response, "output", []) or []
    if not isinstance(output, list):
        output = [output]
    chunks: list[str] = []
    for item in output:
        if _get(item, "type") not in {None, "message"}:
            continue
        content = _get(item, "content", []) or []
        if not isinstance(content, list):
            content = [content]
        for part in content:
            text = _get(part, "text")
            if isinstance(text, str):
                chunks.append(text)
    return "".join(chunks)


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return value
    return None


def _normalize_verdict(raw_text: str) -> dict[str, Any]:
    try:
        raw = json.loads(raw_text)
    except (TypeError, json.JSONDecodeError):
        return {
            "verdict": "insufficient_evidence",
            "summary": "The model did not return valid structured verdict JSON.",
            "sub_claims": [],
            "model_output_invalid": True,
        }
    if not isinstance(raw, dict):
        return {
            "verdict": "insufficient_evidence",
            "summary": "The model verdict was not a JSON object.",
            "sub_claims": [],
            "model_output_invalid": True,
        }
    verdict = raw.get("verdict")
    if verdict not in VERDICTS:
        verdict = "insufficient_evidence"
    sub_claims: list[dict[str, Any]] = []
    raw_subclaims = raw.get("sub_claims", [])
    if isinstance(raw_subclaims, list):
        for item in raw_subclaims:
            if not isinstance(item, dict):
                continue
            sub_verdict = item.get("verdict")
            if sub_verdict not in VERDICTS:
                sub_verdict = "insufficient_evidence"
            ids = item.get("evidence_ids", [])
            if not isinstance(ids, list):
                ids = []
            sub_claims.append(
                {
                    "text": str(item.get("text") or ""),
                    "stated_text": str(item.get("stated_text") or ""),
                    "claim_type": str(item.get("claim_type") or ""),
                    "comparator": str(item.get("comparator") or ""),
                    "stated_value": _number(item.get("stated_value")),
                    "verdict": sub_verdict,
                    "evidence_ids": [str(evidence_id) for evidence_id in ids],
                    "interpretations": [
                        str(evidence_id)
                        for evidence_id in item.get("interpretations", [])
                    ]
                    if isinstance(item.get("interpretations", []), list)
                    else [],
                    "model_found_value": _number(item.get("model_found_value")),
                    "note": str(item.get("note") or ""),
                }
            )
    return {
        "verdict": verdict,
        "summary": str(raw.get("summary") or ""),
        "sub_claims": sub_claims,
    }


def _schema_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _valid_verdict_schema(value: Any) -> bool:
    """Validate the existing verdict schema without adding a dependency."""

    if not isinstance(value, dict):
        return False
    if set(value) != {"verdict", "summary", "sub_claims"}:
        return False
    if value.get("verdict") not in VERDICTS or not isinstance(value.get("summary"), str):
        return False
    sub_claims = value.get("sub_claims")
    if not isinstance(sub_claims, list):
        return False
    required = {
        "text",
        "stated_text",
        "claim_type",
        "comparator",
        "stated_value",
        "evidence_ids",
        "interpretations",
        "verdict",
        "note",
        "model_found_value",
    }
    for sub_claim in sub_claims:
        if not isinstance(sub_claim, dict) or set(sub_claim) != required:
            return False
        if not isinstance(sub_claim.get("text"), str) or not isinstance(sub_claim.get("stated_text"), str):
            return False
        if sub_claim.get("claim_type") not in CLAIM_TYPES or sub_claim.get("comparator") not in COMPARATORS:
            return False
        stated_value = sub_claim.get("stated_value")
        found_value = sub_claim.get("model_found_value")
        if stated_value is not None and not _schema_number(stated_value):
            return False
        if found_value is not None and not _schema_number(found_value):
            return False
        if not isinstance(sub_claim.get("evidence_ids"), list) or any(
            not isinstance(item, str) for item in sub_claim["evidence_ids"]
        ):
            return False
        if not isinstance(sub_claim.get("interpretations"), list) or any(
            not isinstance(item, str) for item in sub_claim["interpretations"]
        ):
            return False
        if sub_claim.get("verdict") not in VERDICTS or not isinstance(sub_claim.get("note"), str):
            return False
    return True


def _strip_json_fences(raw_text: str) -> str:
    text = str(raw_text or "").strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text


def _parse_strict_verdict(raw_text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(_strip_json_fences(raw_text))
    except (TypeError, json.JSONDecodeError):
        return None
    # Traces produced before the period-interpretation field remain replayable;
    # the published schema is strict and normalized output always contains it.
    if isinstance(value, dict) and isinstance(value.get("sub_claims"), list):
        for sub_claim in value["sub_claims"]:
            if isinstance(sub_claim, dict) and "interpretations" not in sub_claim:
                sub_claim["interpretations"] = []
    if not _valid_verdict_schema(value):
        return None
    return _normalize_verdict(json.dumps(value, ensure_ascii=False))


def _invalid_model_json_result(recorder: TraceRecorder) -> dict[str, Any]:
    result = {
        "verdict": "insufficient_evidence",
        "summary": "The model did not return valid verdict JSON after one repair request.",
        "sub_claims": [],
        "program_checks": [],
        "model_output_invalid": True,
        "invalid_model_json": True,
        "flags": ["invalid_model_json"],
        "evidence_strength": "low",
        "evidence_summary": "Evidence: unavailable",
    }
    recorder.finish(result)
    return result


def _already_structured_verdict(response: Any) -> bool:
    """Accept a fake/provider response that already returned final JSON.

    The normal path still makes the dedicated final request.  This small
    compatibility branch makes the loop tolerant of providers/test doubles
    that return the structured verdict immediately after tool outputs.
    """

    try:
        value = json.loads(_response_text(response))
    except (TypeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and value.get("verdict") in VERDICTS
        and isinstance(value.get("summary"), str)
        and isinstance(value.get("sub_claims"), list)
    )


def _exception_status_code(exc: BaseException) -> int | None:
    for value in (
        getattr(exc, "status_code", None),
        getattr(exc, "status", None),
        _get(getattr(exc, "response", None), "status_code"),
        _get(getattr(exc, "response", None), "status"),
    ):
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            continue
    return None


def _is_previous_response_not_found_error(
    exc: BaseException, payload: Mapping[str, Any]
) -> bool:
    """Recognize the Meta response-chain expiration/not-found error."""

    if "previous_response_id" not in payload:
        return False
    message = str(exc).lower()
    status_code = _exception_status_code(exc)
    not_found = (
        ("response" in message and "not found" in message)
        or (
            "reasoning item" in message
            and ("not found" in message or "expired" in message)
        )
        or (
            "expired" in message
            and ("response" in message or "reasoning item" in message)
        )
        or ("previous_response_id" in message and "not" in message)
    )
    if not not_found:
        return False
    # Meta normally returns HTTP 400, but test doubles and SDK wrappers may
    # expose only the error text.  Text matching is enough for an explicit
    # previous-response expiration; an unrelated HTTP 400 is never retried.
    return (
        status_code in {400, 404}
        or "previous_response_id" in message
        or "referenced response" in message
        or "previous response" in message
    )


def _request_with_retry(
    *,
    client: Any,
    ledger: Ledger,
    recorder: TraceRecorder,
    payload: dict[str, Any],
    model: str,
    provider: ProviderAdapter | str = "meta",
    max_output_tokens: int,
    previous_context: Any,
    turn: int,
    phase: str,
    retry_incomplete: bool = True,
    fallback_payload: dict[str, Any] | None = None,
    fallback_previous_context: Any = None,
) -> tuple[Any, bool]:
    """Make one request, retrying expiration and max-token failures safely."""

    active_provider = get_provider(provider)
    attempts = 2 if retry_incomplete else 1
    active_payload = payload
    active_context = previous_context
    fallback_used = False
    transient_attempt = 1
    for attempt in range(attempts):
        request_limit = max_output_tokens * (2 if attempt else 1)
        retry_after_incomplete = False
        while True:
            using_fallback = fallback_used
            request_payload = {**active_payload}
            if active_provider.chat_completions:
                request_payload.pop("max_output_tokens", None)
                request_payload["max_tokens"] = request_limit
            else:
                request_payload["max_output_tokens"] = request_limit
            reservation = ledger.reserve(
                request_payload,
                model=model,
                max_output_tokens=request_limit,
                previous_context=(
                    fallback_previous_context if using_fallback else active_context
                ),
                provider=active_provider.name,
            )
            started = time.perf_counter()
            try:
                response = active_provider.call(client, request_payload)
            except Exception as exc:
                latency_ms = (time.perf_counter() - started) * 1000
                retry = retry_info(exception_status(exc), transient_attempt)
                recorder.record_request(
                    payload=request_payload,
                    response={
                        "error": type(exc).__name__,
                        "message": str(exc),
                    },
                    reservation=reservation,
                    usage=None,
                    cost=reservation.amount,
                    latency_ms=latency_ms,
                    status="error",
                    previous_response_fallback=using_fallback,
                    retry=retry,
                )
                if wait_for_retry(retry):
                    transient_attempt += 1
                    continue
                if (
                    not using_fallback
                    and not fallback_used
                    and fallback_payload is not None
                    and active_provider.name == "meta"
                    and _is_previous_response_not_found_error(exc, request_payload)
                ):
                    fallback_used = True
                    recorder.mark_previous_response_fallback()
                    active_payload = fallback_payload
                    active_context = fallback_previous_context
                    continue
                raise
            latency_ms = (time.perf_counter() - started) * 1000
            usage = response.usage
            cost = ledger.reconcile(reservation, usage)
            status = response.status
            recorder.record_request(
                payload=request_payload,
                response=response.raw_response,
                reservation=reservation,
                usage=response.normalized_usage if active_provider.chat_completions else usage,
                cost=cost,
                latency_ms=latency_ms,
                status=status,
                raw_usage=response.raw_usage if active_provider.chat_completions else None,
                normalized_usage=response.normalized_usage if active_provider.chat_completions else None,
                finish_reason=response.finish_reason,
                rate_limit_headers=response.rate_limit_headers if active_provider.chat_completions else None,
                previous_response_fallback=using_fallback,
            )
            if status == "completed":
                return response, True

            reason = response.incomplete_reason
            recorder.record_incomplete_turn(
                turn=turn,
                attempt=attempt + 1,
                phase=phase,
                status=status,
                reason=reason,
                max_output_tokens=request_limit,
            )
            retry_after_incomplete = (
                attempt == 0
                and status == "incomplete"
                and reason == "max_output_tokens"
                and retry_incomplete
            )
            break
        if retry_after_incomplete:
            continue
        return response, False

    raise AssertionError("request retry loop did not return")


def _incomplete_response_result(
    recorder: TraceRecorder,
    response: Any,
) -> dict[str, Any]:
    status = _response_status(response)
    reason = _incomplete_reason(response)
    if status == "incomplete":
        summary = "The model response was incomplete; no verdict was accepted."
    else:
        summary = f"The model response had non-completed status {status!r}; no verdict was accepted."
    if reason:
        summary += f" Reason: {reason}."
    result = {
        "verdict": "insufficient_evidence",
        "summary": summary,
        "sub_claims": [],
        "program_checks": [],
        "incomplete_response": True,
    }
    recorder.finish(result)
    return result


def verify_claim(
    claim: str,
    client: Any,
    edgar: EdgarClient,
    ledger: Ledger,
    model: str,
    max_turns: int = 6,
    *,
    trace: TraceRecorder | None = None,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    provider: str | ProviderAdapter = "meta",
    release_client: Any = None,
) -> dict[str, Any]:
    """Run the model/tool loop, then apply program checks to its verdict."""

    active_provider = get_provider(provider)
    recorder = trace or TraceRecorder(claim, model, provider=active_provider.name)
    recorder.provider = active_provider.name
    reason = missing_period_reason(claim)
    if reason:
        check = {"text": claim, "claim_type": "unresolved_period", "program_verdict": "insufficient_evidence",
                 "reason": reason, "evidence_ids": [], "flags": ["missing_period"], "evidence_strength": "low"}
        result = {"verdict": "insufficient_evidence", "summary": reason, "sub_claims": [],
                  "program_checks": [check], "flags": ["missing_period"], "evidence_strength": "low"}
        recorder.finish(result)
        return result
    runner = ToolRunner(edgar, release_client=release_client)
    configured_max = _configured_max_output_tokens(max_output_tokens)
    tool_output_tokens = configured_max or MAX_TOOL_OUTPUT_TOKENS
    final_output_tokens = configured_max or MAX_FINAL_OUTPUT_TOKENS
    configured_reasoning_effort = _configured_reasoning_effort(reasoning_effort)
    response: ParsedResponse | None = None
    current_payload = active_provider.initial_request(
        claim,
        model,
        max_output_tokens=tool_output_tokens,
        reasoning_effort=configured_reasoning_effort,
    )
    previous_context: Any = None
    meta_history: list[dict[str, Any]] = [
        copy.deepcopy(item)
        for item in current_payload.get("input", [])
        if isinstance(item, dict)
    ] if active_provider.name == "meta" else []
    fallback_payload: dict[str, Any] | None = None
    turns = 0

    while turns < max(1, max_turns):
        response, completed = _request_with_retry(
            client=client,
            ledger=ledger,
            recorder=recorder,
            payload=current_payload,
            model=model,
            provider=active_provider,
            max_output_tokens=tool_output_tokens,
            previous_context=previous_context,
            turn=turns + 1,
            phase="tool",
            fallback_payload=fallback_payload,
            fallback_previous_context=None,
        )
        if not completed:
            return _incomplete_response_result(recorder, response)
        turns += 1
        if active_provider.name == "meta" and response.output_items:
            meta_history.extend(copy.deepcopy(response.output_items))
        calls = response.tool_calls
        if not calls:
            break

        tool_results: list[dict[str, Any]] = []
        for call in calls:
            name = call.name
            try:
                args = json.loads(call.arguments)
            except (TypeError, json.JSONDecodeError):
                args = call.arguments
            result = runner.dispatch(name, args)
            call_id = call.call_id
            recorder.record_tool_call(name=name, arguments=args, call_id=call_id, result=result)
            tool_results.append(
                {
                    "call_id": call_id,
                    "name": name,
                    "arguments": args,
                    "result": result,
                }
            )
        previous_context = None
        tool_input_items = [
            {
                "type": "function_call_output",
                "call_id": item["call_id"],
                "output": json.dumps(
                    item["result"], ensure_ascii=False, separators=(",", ":")
                ),
            }
            for item in tool_results
        ]
        if active_provider.name == "meta":
            meta_history.extend(copy.deepcopy(tool_input_items))
            previous_context = {
                "response_id": response.response_id,
                "tool_outputs": tool_input_items,
            }
        current_payload = active_provider.continuation_request(
            current_payload,
            response,
            tool_results,
            model=model,
            max_output_tokens=tool_output_tokens,
            reasoning_effort=configured_reasoning_effort,
        )
        if active_provider.name == "meta":
            fallback_payload = active_provider.fallback_request(
                current_payload,
                meta_history,
                model=model,
                max_output_tokens=tool_output_tokens,
                reasoning_effort=configured_reasoning_effort,
            )

    if response is None:
        result = {
            "verdict": "insufficient_evidence",
            "summary": "No model response was produced.",
            "sub_claims": [],
            "program_checks": [],
        }
        recorder.finish(result)
        return result

    if active_provider.name == "meta" and _already_structured_verdict(response):
        # Some OpenAI-compatible test doubles/providers complete the verdict on
        # the tool-output continuation itself.  Do not spend a redundant call.
        final_response = response
    else:
        final_payload = active_provider.final_request(
            current_payload,
            response,
            model=model,
            max_output_tokens=final_output_tokens,
            reasoning_effort=configured_reasoning_effort,
        )
        final_fallback_payload: dict[str, Any] | None = None
        if active_provider.name == "meta":
            final_input = [
                copy.deepcopy(item)
                for item in final_payload.get("input", [])
                if isinstance(item, dict)
            ]
            final_fallback_payload = active_provider.fallback_request(
                final_payload,
                [*meta_history, *final_input],
                model=model,
                max_output_tokens=final_output_tokens,
                reasoning_effort=configured_reasoning_effort,
            )
        final_response, completed = _request_with_retry(
            client=client,
            ledger=ledger,
            recorder=recorder,
            payload=final_payload,
            model=model,
            provider=active_provider,
            max_output_tokens=final_output_tokens,
            previous_context=previous_context,
            turn=turns + 1,
            phase="final",
            fallback_payload=final_fallback_payload,
            fallback_previous_context=None,
        )
        if not completed:
            return _incomplete_response_result(recorder, final_response)

    if active_provider.chat_completions:
        verdict = _parse_strict_verdict(_response_text(final_response))
        if verdict is None:
            repair_payload = active_provider.repair_request(
                current_payload,
                final_response,
                model=model,
                max_output_tokens=final_output_tokens,
                reasoning_effort=configured_reasoning_effort,
            )
            repaired_response, repair_completed = _request_with_retry(
                client=client,
                ledger=ledger,
                recorder=recorder,
                payload=repair_payload,
                model=model,
                provider=active_provider,
                max_output_tokens=final_output_tokens,
                previous_context=None,
                turn=turns + 2,
                phase="final_repair",
                retry_incomplete=False,
            )
            if not repair_completed:
                return _invalid_model_json_result(recorder)
            verdict = _parse_strict_verdict(_response_text(repaired_response))
            if verdict is None:
                return _invalid_model_json_result(recorder)
            final_response = repaired_response
    else:
        verdict = _normalize_verdict(_response_text(final_response))
    model_verdict = verdict["verdict"]
    check_sub_claims = [
        {**sub_claim, "original_claim": claim}
        for sub_claim in verdict["sub_claims"]
    ]
    checks, program_verdict = evaluate_verdict(check_sub_claims, runner)
    for call in runner.calls:
        if call.get("role") != "program":
            continue
        recorder.record_tool_call(
            name=str(call.get("name") or ""),
            arguments=call.get("arguments"),
            call_id=None,
            result=call.get("result"),
            role="program",
        )
    for sub_claim, check in zip(verdict["sub_claims"], checks):
        sub_claim.update(check)
    verdict["model_verdict"] = model_verdict
    verdict["verdict"] = program_verdict
    verdict["program_checks"] = checks
    strength_order = {"low": 0, "medium": 1, "high": 2}
    strengths = [
        str(check.get("evidence_strength"))
        for check in checks
        if str(check.get("evidence_strength")) in strength_order
    ]
    verdict["evidence_strength"] = (
        min(strengths, key=lambda value: strength_order[value]) if strengths else "low"
    )
    summaries = list(
        dict.fromkeys(
            str(check.get("evidence_summary"))
            for check in checks
            if check.get("evidence_summary")
            and str(check.get("evidence_summary")) != "Evidence: unavailable"
        )
    )
    verdict["evidence_summary"] = (
        "Evidence: " + "; ".join(summary.removeprefix("Evidence: ") for summary in summaries)
        if summaries
        else "Evidence: unavailable"
    )
    if any(check.get("restated_evidence") for check in checks):
        flags = verdict.get("flags")
        flags = list(flags) if isinstance(flags, list) else []
        if "restated_evidence" not in flags:
            flags.append("restated_evidence")
        verdict["flags"] = flags
    if any("release_vs_filing_mismatch" in check.get("flags", []) for check in checks):
        verdict["flags"] = list(dict.fromkeys([*verdict.get("flags", []), "release_vs_filing_mismatch"]))
    verdict["model_program_disagreement"] = (
        model_verdict != program_verdict
        or any(check.get("disagreement") for check in checks)
    )
    recorder.finish(verdict)
    return verdict
