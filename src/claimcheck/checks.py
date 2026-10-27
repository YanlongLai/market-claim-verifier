"""Deterministic, claim-aware checks for model-produced sub-claims."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .numbers import ParsedNumber, parse_stated_number


CLAIM_TYPES = ("value", "change_pct", "change_abs")
COMPARATORS = ("eq", "approx", "gt", "gte", "lt", "lte")
PROGRAM_VERDICTS = ("supported", "contradicted", "unchecked")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _relative_difference(left: float, right: float) -> float:
    denominator = max(abs(right), 1e-12)
    return abs(left - right) / denominator


def _runner_evidence_kind(runner: Any, evidence_id: str, result: Mapping[str, Any]) -> str | None:
    kinds = getattr(runner, "evidence_kind", {})
    if isinstance(kinds, Mapping) and evidence_id in kinds:
        return str(kinds[evidence_id])
    if "pct_change" in result or "abs_change" in result or "current_fact" in result:
        return "compute_change"
    if isinstance(result.get("value"), (int, float)) and not isinstance(result.get("value"), bool):
        return "lookup_fact"
    return None


def _normalise_evidence_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _number_and_precision(sub_claim: Mapping[str, Any]) -> tuple[float | None, float | None, list[str]]:
    stated_value = sub_claim.get("stated_value")
    model_value = float(stated_value) if _is_number(stated_value) else None
    parsed: ParsedNumber | None = parse_stated_number(sub_claim.get("stated_text", ""))
    flags: list[str] = []

    if parsed is None:
        if model_value is None:
            flags.append("stated_text_unparsed")
            return None, None, flags
        flags.append("stated_text_unparsed")
        return model_value, abs(model_value) * 0.005, flags

    parsed_value, precision = parsed
    if model_value is None or _relative_difference(abs(parsed_value), abs(model_value)) > 0.005:
        # Preserve a model-supplied sign while taking the magnitude from the
        # literal text.  The parser intentionally does not infer signs from
        # words such as "loss".
        sign = -1.0 if model_value is not None and model_value < 0 else 1.0
        flags.append("stated_value_corrected")
        return sign * parsed_value, precision, flags
    return model_value, precision, flags


def _value_evidence(
    evidence_ids: list[str], runner: Any
) -> tuple[float | None, bool, str]:
    if len(evidence_ids) != 1:
        return None, False, "ambiguous_evidence"
    evidence_id = evidence_ids[0]
    evidence = getattr(runner, "evidence", {}).get(evidence_id)
    if not isinstance(evidence, Mapping):
        return None, False, "ambiguous_evidence"
    kind = _runner_evidence_kind(runner, evidence_id, evidence)
    if kind not in {"lookup_fact", "compute_change"}:
        return None, False, "ambiguous_evidence"
    if "error" in evidence or not _is_number(evidence.get("value")):
        return None, False, "missing_evidence"
    return float(evidence["value"]), True, ""


def _change_evidence(
    evidence_ids: list[str], claim_type: str, runner: Any
) -> tuple[float | None, bool, str]:
    if len(evidence_ids) != 1:
        return None, False, "ambiguous_evidence"
    evidence_id = evidence_ids[0]
    evidence = getattr(runner, "evidence", {}).get(evidence_id)
    if not isinstance(evidence, Mapping):
        return None, False, "ambiguous_evidence"
    if _runner_evidence_kind(runner, evidence_id, evidence) != "compute_change":
        return None, False, "ambiguous_evidence"
    if "error" in evidence:
        return None, False, "missing_evidence"
    field = "pct_change" if claim_type == "change_pct" else "abs_change"
    if not _is_number(evidence.get(field)):
        return None, False, "missing_evidence"
    return float(evidence[field]), True, ""


def _tolerance(claim_type: str, comparator: str, stated: float, precision: float) -> float:
    if comparator in {"gt", "lt"}:
        return 0.0
    if comparator in {"gte", "lte", "eq"}:
        return precision
    if claim_type == "change_pct":
        return max(2 * precision, 1.0)
    return max(2 * precision, 0.025 * abs(stated))


def _compare(actual: float, stated: float, comparator: str, tolerance: float) -> bool:
    if comparator in {"eq", "approx"}:
        return abs(actual - stated) <= tolerance
    if comparator == "gt":
        return actual > stated
    if comparator == "lt":
        return actual < stated
    if comparator == "gte":
        return actual >= stated - tolerance
    if comparator == "lte":
        return actual <= stated + tolerance
    return False


def evaluate_sub_claim(sub_claim: Mapping[str, Any], runner: Any) -> dict[str, Any]:
    """Evaluate one normalized model sub-claim against cited evidence."""

    evidence_ids = _normalise_evidence_ids(sub_claim.get("evidence_ids"))
    claim_type = sub_claim.get("claim_type")
    comparator = sub_claim.get("comparator")
    stated, precision, flags = _number_and_precision(sub_claim)
    actual: float | None = None
    evidence_valid = False
    reason = ""

    if claim_type not in CLAIM_TYPES:
        reason = "invalid_claim_type"
    elif comparator not in COMPARATORS:
        reason = "invalid_comparator"
    elif stated is None or precision is None:
        reason = "stated_text_unparsed"
    elif claim_type == "value":
        actual, evidence_valid, reason = _value_evidence(evidence_ids, runner)
    else:
        actual, evidence_valid, reason = _change_evidence(evidence_ids, claim_type, runner)

    tolerance: float | None = None
    program_verdict = "unchecked"
    if reason == "" and actual is not None and stated is not None and precision is not None:
        tolerance = _tolerance(claim_type, comparator, stated, precision)
        if _compare(actual, stated, comparator, tolerance):
            program_verdict = "supported"
            reason = (
                f"actual {actual:g} is consistent with stated {stated:g} "
                f"using {comparator} tolerance {tolerance:g}"
            )
        else:
            program_verdict = "contradicted"
            reason = (
                f"actual {actual:g} is not consistent with stated {stated:g} "
                f"using {comparator} tolerance {tolerance:g}"
            )
    elif not reason:
        reason = "missing_evidence"

    model_verdict = sub_claim.get("verdict")
    disagreement = (
        program_verdict != "unchecked" and model_verdict != program_verdict
    )
    flag_fields = {
        "stated_value_corrected": "stated_value_corrected" in flags,
        "stated_text_unparsed": "stated_text_unparsed" in flags,
    }
    if flags:
        reason = f"{', '.join(flags)}; {reason}"

    return {
        "text": str(sub_claim.get("text") or ""),
        "stated_value": stated,
        "evidence_ids": evidence_ids,
        "evidence_valid": evidence_valid,
        "program_verdict": program_verdict,
        "actual_value": actual,
        "tolerance": tolerance,
        "reason": reason,
        "disagreement": disagreement,
        "precision": precision,
        "stated_value_used": stated,
        **flag_fields,
    }


def overall_program_verdict(checks: Sequence[Mapping[str, Any]]) -> str:
    """Apply the claim-level aggregation rule to sub-claim checks."""

    program_verdicts = [check.get("program_verdict") for check in checks]
    if any(value == "contradicted" for value in program_verdicts):
        return "contradicted"
    if program_verdicts and all(value == "supported" for value in program_verdicts):
        return "supported"
    return "insufficient_evidence"


def evaluate_verdict(
    sub_claims: Sequence[Mapping[str, Any]], runner: Any
) -> tuple[list[dict[str, Any]], str]:
    """Evaluate all sub-claims and return checks plus the program verdict."""

    checks = [evaluate_sub_claim(sub_claim, runner) for sub_claim in sub_claims]
    return checks, overall_program_verdict(checks)


__all__ = [
    "CLAIM_TYPES",
    "COMPARATORS",
    "PROGRAM_VERDICTS",
    "evaluate_sub_claim",
    "evaluate_verdict",
    "overall_program_verdict",
]
