"""Deterministic, claim-aware checks for model-produced sub-claims."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from .numbers import ParsedNumber, parse_stated_number


CLAIM_TYPES = (
    "value",
    "change_pct",
    "change_abs",
    "record_high",
    "record_low",
    "first_time_above",
    "other",
)
COMPARATORS = ("eq", "approx", "gt", "gte", "lt", "lte")
PROGRAM_VERDICTS = ("supported", "contradicted", "unchecked")

_NEGATIVE_DIRECTION_WORDS = (
    "fell",
    "fall",
    "declined",
    "decline",
    "down",
    "dropped",
    "drop",
    "decreased",
    "decrease",
    "shrank",
    "lower",
    "slid",
    "slumped",
    "contracted",
    "loss of",
)
_POSITIVE_DIRECTION_WORDS = (
    "rose",
    "up",
    "grew",
    "growth",
    "increased",
    "gained",
    "jumped",
    "higher",
    "surged",
    "climbed",
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _relative_difference(left: float, right: float) -> float:
    denominator = max(abs(right), 1e-12)
    return abs(left - right) / denominator


def _runner_evidence_kind(runner: Any, evidence_id: str, result: Mapping[str, Any]) -> str | None:
    kinds = getattr(runner, "evidence_kind", {})
    if isinstance(kinds, Mapping) and evidence_id in kinds:
        return str(kinds[evidence_id])
    if "rank" in result or "is_highest" in result or "periods_considered" in result:
        return "history_rank"
    if "pct_change" in result or "abs_change" in result or "current_fact" in result:
        return "compute_change"
    if _is_number(result.get("value")):
        return "lookup_fact"
    return None


def _normalise_evidence_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _unique_ids(evidence_ids: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(evidence_ids))


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
        # literal text. Change-direction words are applied separately below.
        sign = -1.0 if model_value is not None and model_value < 0 else 1.0
        flags.append("stated_value_corrected")
        return sign * parsed_value, precision, flags
    return model_value, precision, flags


def _direction(sub_claim: Mapping[str, Any]) -> int | None:
    text = " ".join(
        str(sub_claim.get(field) or "") for field in ("stated_text", "text")
    ).lower()
    negative = any(
        re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", text)
        for word in _NEGATIVE_DIRECTION_WORDS
    )
    positive = any(
        re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", text)
        for word in _POSITIVE_DIRECTION_WORDS
    )
    if negative and not positive:
        return -1
    if positive and not negative:
        return 1
    return None


def _apply_change_direction(
    sub_claim: Mapping[str, Any],
    stated: float | None,
    flags: list[str],
) -> float | None:
    if stated is None:
        return None
    direction = _direction(sub_claim)
    if direction is None:
        return stated
    directed = direction * abs(stated)
    if stated != 0 and math.copysign(1.0, stated) != math.copysign(1.0, directed):
        flags.append("stated_sign_corrected")
    return directed


def _evidence(runner: Any, evidence_id: str) -> Mapping[str, Any] | None:
    value = getattr(runner, "evidence", {}).get(evidence_id)
    return value if isinstance(value, Mapping) else None


def _has_numeric_value(evidence: Mapping[str, Any] | None) -> bool:
    return bool(
        evidence is not None
        and "error" not in evidence
        and _is_number(evidence.get("value"))
    )


def _component_ids(compute: Mapping[str, Any]) -> set[str]:
    component_ids: set[str] = set()
    for field in ("current_fact", "base_fact", "current", "base"):
        value = compute.get(field)
        if isinstance(value, Mapping) and value.get("evidence_id") is not None:
            component_ids.add(str(value["evidence_id"]))
    return component_ids


def _same_fact(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """Compare the identifying fact fields used by duplicate evidence."""

    keys = ("concept", "start", "end", "accn", "value")
    if not _is_number(left.get("value")) or not _is_number(right.get("value")):
        return False
    available = [key for key in keys if key in left and key in right]
    return bool(available) and all(left.get(key) == right.get(key) for key in available)


def _numeric_citation(evidence_ids: Sequence[str], runner: Any) -> bool:
    for evidence_id in evidence_ids:
        evidence = _evidence(runner, evidence_id)
        if evidence is None or "error" in evidence:
            continue
        if _has_numeric_value(evidence) or any(
            _is_number(evidence.get(field)) for field in ("pct_change", "abs_change")
        ):
            return True
    return False


def _context_value(value: Any, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if field == "metric":
        return text.lower()
    return text.upper()


def _period_from_fact_context(
    start: str | None, end: str | None, frame: str | None
) -> str | None:
    frame_match = re.fullmatch(r"CY(?P<year>\d{4})(?P<quarter>Q[1-4])(?:I)?", frame or "")
    if frame_match is not None:
        return f"{frame_match.group('year')}{frame_match.group('quarter')}"
    if end is None:
        return None
    try:
        end_date = date.fromisoformat(end)
    except ValueError:
        return None
    if start is not None:
        try:
            duration = (end_date - date.fromisoformat(start)).days + 1
        except ValueError:
            duration = None
        if duration is not None and 300 <= duration <= 380:
            return f"FY{end_date.year}"
    return f"{end_date.year}Q{((end_date.month - 1) // 3) + 1}"


def _period_start(period: str | None) -> str | None:
    if period is None:
        return None
    if match := re.fullmatch(r"FY(\d{4})", period):
        return f"{match.group(1)}-01-01"
    if match := re.fullmatch(r"(\d{4})Q([1-4])", period):
        month = (int(match.group(2)) - 1) * 3 + 1
        return f"{match.group(1)}-{month:02d}-01"
    return None


def _add_context(
    contexts: set[tuple[str, ...]],
    ticker: str | None,
    metric: str | None,
    period: str | None,
    start: str | None,
    end: str | None,
    frame: str | None = None,
) -> None:
    if ticker is None or metric is None:
        return
    if period is not None:
        contexts.add(("period", ticker, metric, period))
    if start is not None and end is not None:
        contexts.add(("dates", ticker, metric, start, end))
    resolved_period = _period_from_fact_context(start, end, frame)
    if resolved_period is not None:
        contexts.add(("period", ticker, metric, resolved_period))


def _evidence_contexts(value: Mapping[str, Any] | None) -> set[tuple[str, ...]]:
    """Return period and date identities present in an evidence object.

    Recorded lookup results from older traces may omit ``period`` while still
    carrying SEC dates/frame.  History results carry the target period and can
    expose its target row, so both forms resolve to a shared identity.
    """

    if value is None:
        return set()
    contexts: set[tuple[str, ...]] = set()
    ticker = _context_value(value.get("ticker"), "ticker")
    metric = _context_value(value.get("metric"), "metric")
    period = _context_value(value.get("period"), "period")
    start = _context_value(value.get("start"), "start")
    end = _context_value(value.get("end"), "end")
    frame = _context_value(value.get("frame"), "frame")
    _add_context(contexts, ticker, metric, period, start, end, frame)

    # history_rank's target row in older traces has period/value and may have
    # only an end date.  Reconstruct the calendar-quarter/year start when
    # possible so it can match an older lookup_fact result by SEC dates.
    if period is not None:
        for field in ("periods", "comparable_periods"):
            rows = value.get(field)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                row_period = _context_value(row.get("period"), "period")
                if row_period != period:
                    continue
                row_start = _context_value(row.get("start"), "start") or _period_start(
                    row_period
                )
                row_end = _context_value(row.get("end"), "end") or end
                _add_context(
                    contexts,
                    ticker,
                    metric,
                    row_period,
                    row_start,
                    row_end,
                    _context_value(row.get("frame"), "frame"),
                )
                break
    for field in ("current_fact", "base_fact", "current", "base"):
        nested = value.get(field)
        if isinstance(nested, Mapping):
            contexts.update(_evidence_contexts(nested))
    return contexts


def _same_fact_context(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return bool(_evidence_contexts(left) & _evidence_contexts(right))


def _history_periods(history: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for field in ("periods", "comparable_periods"):
        value = history.get(field)
        if not isinstance(value, list):
            continue
        periods = [
            item
            for item in value
            if isinstance(item, Mapping)
            and isinstance(item.get("period"), str)
            and _is_number(item.get("value"))
        ]
        if periods:
            return periods
    return []


def _history_period_key(period: str) -> tuple[int, int] | None:
    match = re.fullmatch(
        r"(?:FY(?P<fy>\d{4})|(?P<year>\d{4})Q(?P<quarter>[1-4]))",
        period.upper(),
    )
    if match is None:
        return None
    if match.group("fy"):
        return int(match.group("fy")), 4
    return int(match.group("year")), int(match.group("quarter"))


def _history_item_end(item: Mapping[str, Any]) -> str | None:
    for field in ("end", "end_date"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _history_window(
    history: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, list[Mapping[str, Any]]]:
    """Return the claimed period and only comparable periods before it."""

    periods = _history_periods(history)
    target_period = str(history.get("period") or "").strip().upper()
    target_index = next(
        (
            index
            for index, item in enumerate(periods)
            if str(item["period"]).strip().upper() == target_period
        ),
        None,
    )
    if target_index is None:
        return None, []

    target = periods[target_index]
    target_end = _history_item_end(target) or _history_item_end(history)
    target_key = _history_period_key(target_period)
    earlier: list[Mapping[str, Any]] = []
    for index, item in enumerate(periods):
        item_period = str(item["period"]).strip().upper()
        if index == target_index or item_period == target_period:
            continue
        item_end = _history_item_end(item)
        if item_end is not None and target_end is not None:
            before = item_end < target_end
        else:
            item_key = _history_period_key(item_period)
            if item_key is not None and target_key is not None:
                before = item_key < target_key
            else:
                # history_rank documents ``periods`` as chronological.  This
                # fallback keeps older recorded evidence usable when it lacks
                # explicit SEC end dates.
                before = index < target_index
        if before:
            earlier.append(item)
    return target, earlier


def _first_time_threshold(
    sub_claim: Mapping[str, Any],
    history: Mapping[str, Any],
    evidence_ids: Sequence[str],
    runner: Any,
    related_sub_claims: Sequence[Mapping[str, Any]] | None,
) -> tuple[float | None, float | None, list[str]]:
    """Resolve a first-time threshold from a sibling claim or model value."""

    current_ids = set(evidence_ids)
    for candidate in related_sub_claims or ():
        if candidate is sub_claim:
            continue
        candidate_ids = set(_normalise_evidence_ids(candidate.get("evidence_ids")))
        if not candidate_ids:
            continue
        same_citation = bool(current_ids & candidate_ids)
        same_context = any(
            _same_fact_context(history, evidence)
            for candidate_id in candidate_ids
            if (evidence := _evidence(runner, candidate_id)) is not None
        )
        if not same_citation and not same_context:
            continue
        parsed = parse_stated_number(candidate.get("stated_text", ""))
        if parsed is not None:
            return parsed.value, parsed.precision, []

    stated_value = sub_claim.get("stated_value")
    if _is_number(stated_value):
        model_value = float(stated_value)
        return model_value, abs(model_value) * 0.005, ["threshold_from_model"]
    return None, None, []


def _value_evidence(
    evidence_ids: list[str], runner: Any
) -> tuple[float | None, bool, str]:
    ids = _unique_ids(evidence_ids)
    if not ids:
        return None, False, "no_evidence"

    records = {evidence_id: _evidence(runner, evidence_id) for evidence_id in ids}
    lookup_ids = [
        evidence_id
        for evidence_id, evidence in records.items()
        if evidence is not None
        and _runner_evidence_kind(runner, evidence_id, evidence) == "lookup_fact"
        and _has_numeric_value(evidence)
    ]
    compute_ids = [
        evidence_id
        for evidence_id, evidence in records.items()
        if evidence is not None
        and _runner_evidence_kind(runner, evidence_id, evidence) == "compute_change"
    ]

    # One lookup fact is sufficient on its own. A compute_change citation may
    # repeat that fact, but only when it is the same current/base component.
    if len(lookup_ids) == 1 and len(compute_ids) == 0 and len(ids) == 1:
        return float(records[lookup_ids[0]]["value"]), True, ""
    if len(lookup_ids) == 1 and len(compute_ids) == 1:
        compute = records[compute_ids[0]]
        assert compute is not None
        component_facts = [
            value
            for field in ("current_fact", "base_fact", "current", "base")
            if isinstance(value := compute.get(field), Mapping)
        ]
        lookup = records[lookup_ids[0]]
        assert lookup is not None
        allowed = {lookup_ids[0], compute_ids[0]} | _component_ids(compute)
        if set(ids) <= allowed and any(
            _same_fact(lookup, component) for component in component_facts
        ):
            return float(lookup["value"]), True, ""

    if not _numeric_citation(ids, runner):
        return None, False, "no_evidence"
    return None, False, "ambiguous_evidence"


def _change_evidence(
    evidence_ids: list[str], claim_type: str, runner: Any
) -> tuple[float | None, bool, str]:
    ids = _unique_ids(evidence_ids)
    if not ids:
        return None, False, "no_evidence"

    records = {evidence_id: _evidence(runner, evidence_id) for evidence_id in ids}
    compute_ids = [
        evidence_id
        for evidence_id, evidence in records.items()
        if evidence is not None
        and _runner_evidence_kind(runner, evidence_id, evidence) == "compute_change"
    ]
    field = "pct_change" if claim_type == "change_pct" else "abs_change"
    if len(compute_ids) == 1:
        compute_id = compute_ids[0]
        compute = records[compute_id]
        assert compute is not None
        # Component lookup facts belonging to this compute_change are allowed
        # citations and do not make the change claim ambiguous.
        if not set(ids) <= ({compute_id} | _component_ids(compute)):
            return None, False, (
                "no_evidence" if not _numeric_citation(ids, runner) else "ambiguous_evidence"
            )
        if "error" in compute or not _is_number(compute.get(field)):
            return None, False, "no_evidence"
        return float(compute[field]), True, ""
    if len(compute_ids) > 1:
        return None, False, (
            "no_evidence" if not _numeric_citation(ids, runner) else "ambiguous_evidence"
        )
    if not _numeric_citation(ids, runner):
        return None, False, "no_evidence"
    return None, False, "ambiguous_evidence"


def _history_evidence(
    evidence_ids: list[str], runner: Any
) -> tuple[Mapping[str, Any] | None, bool, str]:
    ids = _unique_ids(evidence_ids)
    history_ids = [
        evidence_id
        for evidence_id in ids
        if (evidence := _evidence(runner, evidence_id)) is not None
        and "error" not in evidence
        and _runner_evidence_kind(runner, evidence_id, evidence) == "history_rank"
    ]
    if len(history_ids) != 1:
        return None, False, (
            "no_evidence" if not _numeric_citation(ids, runner) else "ambiguous_evidence"
        )

    history_id = history_ids[0]
    history = _evidence(runner, history_id)
    assert history is not None
    for evidence_id in ids:
        if evidence_id == history_id:
            continue
        evidence = _evidence(runner, evidence_id)
        if (
            evidence is None
            or _runner_evidence_kind(runner, evidence_id, evidence) != "lookup_fact"
            or not _same_fact_context(history, evidence)
        ):
            return None, False, (
                "no_evidence"
                if not _numeric_citation(ids, runner)
                else "ambiguous_evidence"
            )
    return history, True, ""


def _tolerance(claim_type: str, comparator: str, stated: float, precision: float) -> float:
    if comparator in {"gt", "lt"}:
        base = 0.0
    elif comparator in {"gte", "lte", "eq"}:
        base = precision
    elif claim_type == "change_pct":
        base = max(2 * precision, 1.0)
    else:
        base = max(2 * precision, 0.025 * abs(stated))
    if claim_type == "value":
        base = min(base, 0.10 * abs(stated))
    return base


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


def _record_number_and_precision(sub_claim: Mapping[str, Any]) -> tuple[float, float, list[str]]:
    stated_value = sub_claim.get("stated_value")
    if _is_number(stated_value):
        return float(stated_value), 0.0, []
    return 1.0, 0.0, []


def _history_reason(prefix: str, history: Mapping[str, Any]) -> str:
    window = history.get("periods_considered")
    return f"{prefix} over periods_considered={window}"


def evaluate_sub_claim(
    sub_claim: Mapping[str, Any],
    runner: Any,
    related_sub_claims: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate one normalized model sub-claim against cited evidence."""

    evidence_ids = _normalise_evidence_ids(sub_claim.get("evidence_ids"))
    claim_type = str(sub_claim.get("claim_type") or "")
    comparator = sub_claim.get("comparator")
    if claim_type in {"record_high", "record_low"}:
        stated, precision, flags = _record_number_and_precision(sub_claim)
    elif claim_type == "other":
        stated_value = sub_claim.get("stated_value")
        stated = float(stated_value) if _is_number(stated_value) else None
        precision = None
        flags = []
    else:
        stated, precision, flags = _number_and_precision(sub_claim)
    if claim_type in {"change_pct", "change_abs"}:
        stated = _apply_change_direction(sub_claim, stated, flags)

    actual: float | None = None
    evidence_valid = False
    reason = ""
    history: Mapping[str, Any] | None = None

    if claim_type not in CLAIM_TYPES:
        reason = "invalid_claim_type"
    elif comparator not in COMPARATORS:
        reason = "invalid_comparator"
    elif claim_type == "other":
        reason = "unchecked_other_claim"
    elif claim_type in {"record_high", "record_low", "first_time_above"}:
        history, evidence_valid, reason = _history_evidence(evidence_ids, runner)
        if evidence_valid and history is not None:
            target, earlier = _history_window(history)
            if target is None:
                evidence_valid = False
                reason = "no_evidence"
            elif claim_type == "record_high":
                target_value = float(target["value"])
                actual = 1.0 if all(
                    float(item["value"]) <= target_value
                    for item in [*earlier, target]
                ) else 0.0
                reason = ""
            elif claim_type == "record_low":
                target_value = float(target["value"])
                actual = 1.0 if all(
                    float(item["value"]) >= target_value
                    for item in [*earlier, target]
                ) else 0.0
                reason = ""
            else:
                if "stated_text_unparsed" in flags:
                    threshold, threshold_precision, threshold_flags = _first_time_threshold(
                        sub_claim,
                        history,
                        evidence_ids,
                        runner,
                        related_sub_claims,
                    )
                    if threshold is not None:
                        stated = threshold
                        precision = threshold_precision
                        flags = [
                            flag for flag in flags if flag != "stated_text_unparsed"
                        ]
                        flags.extend(threshold_flags)

                threshold = stated
                current_value = float(target["value"])
                above = [
                    item
                    for item in earlier
                    if threshold is not None and float(item["value"]) > threshold
                ]
                actual = current_value
                if threshold is None:
                    evidence_valid = False
                    reason = "stated_text_unparsed"
                else:
                    is_first = current_value > threshold and not above
                    reason = _history_reason(
                        "first_time_above is "
                        + ("true" if is_first else "false"),
                        history,
                    )
                    if above:
                        reason += f"; earlier_periods_above={above}"
                    if not is_first:
                        reason += f"; threshold={threshold:g}"
                    if flags:
                        reason = f"{', '.join(flags)}; {reason}"
                    model_verdict = sub_claim.get("verdict")
                    program_verdict = "supported" if is_first else "contradicted"
                    return {
                        "text": str(sub_claim.get("text") or ""),
                        "stated_value": stated,
                        "evidence_ids": evidence_ids,
                        "evidence_valid": evidence_valid,
                        "program_verdict": program_verdict,
                        "actual_value": actual,
                        "tolerance": 0.0,
                        "reason": reason,
                        "disagreement": model_verdict != program_verdict,
                        "precision": precision,
                        "stated_value_used": stated,
                        "stated_value_corrected": "stated_value_corrected" in flags,
                        "stated_text_unparsed": "stated_text_unparsed" in flags,
                        "stated_sign_corrected": "stated_sign_corrected" in flags,
                        "threshold_from_model": "threshold_from_model" in flags,
                    }
    elif stated is None or precision is None:
        reason = "stated_text_unparsed"
    elif claim_type == "value":
        actual, evidence_valid, reason = _value_evidence(evidence_ids, runner)
    else:
        actual, evidence_valid, reason = _change_evidence(evidence_ids, claim_type, runner)

    tolerance: float | None = None
    program_verdict = "unchecked"
    if (
        reason == ""
        and actual is not None
        and stated is not None
        and precision is not None
    ):
        if claim_type in {"record_high", "record_low"}:
            tolerance = 0.0
            is_record = actual == 1.0
            program_verdict = "supported" if is_record else "contradicted"
            reason = _history_reason(
                f"{claim_type} is " + ("true" if is_record else "false"),
                history or {},
            )
        else:
            tolerance = _tolerance(claim_type, str(comparator), stated, precision)
            if _compare(actual, stated, str(comparator), tolerance):
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
        reason = "no_evidence"

    model_verdict = sub_claim.get("verdict")
    disagreement = program_verdict != "unchecked" and model_verdict != program_verdict
    flag_fields = {
        "stated_value_corrected": "stated_value_corrected" in flags,
        "stated_text_unparsed": "stated_text_unparsed" in flags,
        "stated_sign_corrected": "stated_sign_corrected" in flags,
        "threshold_from_model": "threshold_from_model" in flags,
    }
    if flags:
        flag_reason = ", ".join(flags)
        if reason != flag_reason and not reason.startswith(f"{flag_reason};"):
            reason = f"{flag_reason}; {reason}"

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

    checks = [
        evaluate_sub_claim(sub_claim, runner, sub_claims)
        for sub_claim in sub_claims
    ]
    return checks, overall_program_verdict(checks)


__all__ = [
    "CLAIM_TYPES",
    "COMPARATORS",
    "PROGRAM_VERDICTS",
    "evaluate_sub_claim",
    "evaluate_verdict",
    "overall_program_verdict",
]
