"""Meta Muse function-calling loop and deterministic evidence checks."""

from __future__ import annotations

import json
import math
import time
from collections.abc import Mapping
from typing import Any

from .budget import Ledger
from .edgar import EdgarClient
from .tools import TOOL_DEFINITIONS, ToolRunner
from .trace import TraceRecorder


VERDICTS = ("supported", "contradicted", "insufficient_evidence")
MAX_TOOL_OUTPUT_TOKENS = 1_200
MAX_FINAL_OUTPUT_TOKENS = 1_200

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "summary": {"type": "string"},
        "sub_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "verdict": {"type": "string", "enum": list(VERDICTS)},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "expected_value": {"type": ["number", "null"]},
                    "found_value": {"type": ["number", "null"]},
                    "note": {"type": "string"},
                },
                "required": [
                    "text",
                    "verdict",
                    "evidence_ids",
                    "expected_value",
                    "found_value",
                    "note",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["verdict", "summary", "sub_claims"],
    "additionalProperties": False,
}


SYSTEM_INSTRUCTIONS = """You verify financial claims against SEC EDGAR facts.
Decompose the claim into atomic numeric sub-claims. Use the lookup_fact and
list_periods tools for every number; never use memory for numbers. A quarter
must have period_type=quarter and duration_days around 80-100, not
period_type=ytd. If a result has derived=true, use its derivation and
components as the evidence and do not calculate it again. Prefer the evidence
IDs returned by tools, and say insufficient_evidence when data is missing."""


def initial_request(claim: str, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": [{"role": "user", "content": claim}],
        "tools": TOOL_DEFINITIONS,
        "parallel_tool_calls": True,
        "max_output_tokens": MAX_TOOL_OUTPUT_TOKENS,
    }


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


def _usage_dict(response: Any) -> dict[str, Any] | None:
    usage = _get(response, "usage")
    if usage is None:
        return None
    details = _get(usage, "input_tokens_details")
    cached = _get(details, "cached_tokens", 0) if details is not None else 0
    return {
        "input_tokens": _get(usage, "input_tokens"),
        "output_tokens": _get(usage, "output_tokens"),
        "input_tokens_details": {"cached_tokens": cached or 0},
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
                    "verdict": sub_verdict,
                    "evidence_ids": [str(evidence_id) for evidence_id in ids],
                    "expected_value": _number(item.get("expected_value")),
                    "found_value": _number(item.get("found_value")),
                    "note": str(item.get("note") or ""),
                }
            )
    return {
        "verdict": verdict,
        "summary": str(raw.get("summary") or ""),
        "sub_claims": sub_claims,
    }


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


def _round_sig(value: float, digits: int = 3) -> float:
    if value == 0:
        return 0.0
    return round(value, digits - int(math.floor(math.log10(abs(value)))) - 1)


def _scaled_difference(left: float, right: float) -> float:
    if left == right:
        return 0.0
    scales = (1.0, 1e3, 1e6, 1e9, 1e-3, 1e-6, 1e-9)
    best = float("inf")
    for scale in scales:
        candidate = left * scale
        denominator = max(abs(candidate), abs(right), 1e-12)
        best = min(best, abs(candidate - right) / denominator)
    return best


def _matches_tool_value(found: float, tool_value: Any) -> bool:
    if not isinstance(tool_value, (int, float)) or isinstance(tool_value, bool):
        return False
    found_float = float(found)
    tool_float = float(tool_value)
    if _scaled_difference(found_float, tool_float) <= 1e-9:
        return True
    for scale in (1.0, 1e3, 1e6, 1e9, 1e-3, 1e-6, 1e-9):
        if _round_sig(found_float * scale) == _round_sig(tool_float):
            return True
    return False


def _program_checks(verdict: dict[str, Any], runner: ToolRunner) -> tuple[list[dict[str, Any]], bool, bool]:
    checks: list[dict[str, Any]] = []
    invalid_evidence = False
    mismatch = False
    for sub_claim in verdict["sub_claims"]:
        evidence_ids = sub_claim["evidence_ids"]
        evidence_results = [runner.evidence.get(evidence_id) for evidence_id in evidence_ids]
        ids_exist = bool(evidence_ids) and all(result is not None for result in evidence_results)
        numeric_results = [
            result
            for result in evidence_results
            if isinstance(result, dict) and isinstance(result.get("value"), (int, float))
        ]
        found_value = sub_claim["found_value"]
        found_matches = (
            found_value is not None
            and bool(evidence_results)
            and all(
                isinstance(result, dict)
                and isinstance(result.get("value"), (int, float))
                and _matches_tool_value(float(found_value), result["value"])
                for result in evidence_results
            )
        )
        evidence_valid = ids_exist and (
            found_matches if numeric_results or found_value is not None else True
        )
        if not evidence_valid:
            invalid_evidence = True

        expected = sub_claim["expected_value"]
        program_check = "unchecked"
        relative_diff: float | None = None
        if expected is not None and found_value is not None:
            relative_diff = _scaled_difference(float(expected), float(found_value))
            program_check = "match" if relative_diff <= 0.015 else "mismatch"
            if program_check == "mismatch":
                mismatch = True
        sub_claim["program_check"] = program_check
        checks.append(
            {
                "text": sub_claim["text"],
                "evidence_valid": evidence_valid,
                "evidence_ids": evidence_ids,
                "program_check": program_check,
                "relative_diff": relative_diff,
            }
        )
    return checks, invalid_evidence, mismatch


def verify_claim(
    claim: str,
    client: Any,
    edgar: EdgarClient,
    ledger: Ledger,
    model: str,
    max_turns: int = 6,
    *,
    trace: TraceRecorder | None = None,
) -> dict[str, Any]:
    """Run the model/tool loop, then apply program checks to its verdict."""

    recorder = trace or TraceRecorder(claim, model)
    runner = ToolRunner(edgar)
    response: Any = None
    response_id: str | None = None
    current_payload = initial_request(claim, model)
    previous_context: Any = None
    turns = 0

    while turns < max(1, max_turns):
        reservation = ledger.reserve(
            current_payload,
            model=model,
            max_output_tokens=MAX_TOOL_OUTPUT_TOKENS,
            previous_context=previous_context,
        )
        started = time.perf_counter()
        response = client.responses.create(**current_payload)
        latency_ms = (time.perf_counter() - started) * 1000
        usage = _usage_dict(response)
        cost = ledger.reconcile(reservation, usage)
        recorder.record_request(
            payload=current_payload,
            response=response,
            reservation=reservation,
            usage=usage,
            cost=cost,
            latency_ms=latency_ms,
        )
        turns += 1
        response_id = _get(response, "id") or response_id
        calls = _function_calls(response)
        if not calls:
            break

        outputs: list[dict[str, Any]] = []
        for call in calls:
            name = _call_name(call)
            args = _call_arguments(call)
            result = runner.dispatch(name, args)
            call_id = _call_id(call)
            recorder.record_tool_call(name=name, arguments=args, call_id=call_id, result=result)
            outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False, separators=(",", ":")),
                }
            )
        previous_context = {"response_id": response_id, "tool_outputs": outputs}
        current_payload = {
            "model": model,
            "previous_response_id": response_id,
            "input": outputs,
            "tools": TOOL_DEFINITIONS,
            "parallel_tool_calls": True,
            "max_output_tokens": MAX_TOOL_OUTPUT_TOKENS,
        }

    if response is None:
        result = {
            "verdict": "insufficient_evidence",
            "summary": "No model response was produced.",
            "sub_claims": [],
            "program_checks": [],
        }
        recorder.finish(result)
        return result

    if _already_structured_verdict(response):
        # Some OpenAI-compatible test doubles/providers complete the verdict on
        # the tool-output continuation itself.  Do not spend a redundant call.
        final_response = response
    else:
        final_payload = {
            "model": model,
            "previous_response_id": response_id,
            "input": [
                {
                    "role": "user",
                    "content": "Return the final structured verdict now. Include every atomic numeric sub-claim, its evidence IDs, expected value, found value, and a concise note.",
                }
            ],
            "text": verdict_text_format(),
            "max_output_tokens": MAX_FINAL_OUTPUT_TOKENS,
        }
        final_reservation = ledger.reserve(
            final_payload,
            model=model,
            max_output_tokens=MAX_FINAL_OUTPUT_TOKENS,
            previous_context=previous_context,
        )
        started = time.perf_counter()
        final_response = client.responses.create(**final_payload)
        latency_ms = (time.perf_counter() - started) * 1000
        final_usage = _usage_dict(final_response)
        final_cost = ledger.reconcile(final_reservation, final_usage)
        recorder.record_request(
            payload=final_payload,
            response=final_response,
            reservation=final_reservation,
            usage=final_usage,
            cost=final_cost,
            latency_ms=latency_ms,
        )

    verdict = _normalize_verdict(_response_text(final_response))
    checks, invalid_evidence, mismatch = _program_checks(verdict, runner)
    verdict["program_checks"] = checks
    unchecked = any(
        check.get("program_check") == "unchecked" for check in checks
    )
    checked_programs = [
        check for check in checks if check.get("program_check") != "unchecked"
    ]
    all_checked_subclaims_match = bool(checked_programs) and all(
        check.get("program_check") == "match" and check.get("evidence_valid")
        for check in checked_programs
    )
    disagreement = (
        verdict["verdict"] == "supported"
        and (invalid_evidence or mismatch or unchecked or not verdict["sub_claims"])
    ) or (
        verdict["verdict"] == "contradicted" and all_checked_subclaims_match
    )
    if disagreement:
        verdict["verdict"] = "insufficient_evidence"
        verdict["model_program_disagreement"] = True
        if all_checked_subclaims_match:
            suffix = " Program checks matched every checked sub-claim, so the contradicted verdict was not accepted."
        else:
            suffix = " Program checks did not validate the model's supported verdict."
        verdict["summary"] = (verdict["summary"] + suffix).strip()
    else:
        verdict["model_program_disagreement"] = False
    recorder.finish(verdict)
    return verdict
