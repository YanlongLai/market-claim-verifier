"""Deterministic, claim-aware checks for model-produced sub-claims."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from .numbers import ParsedNumber, infer_comparator, parse_stated_number
from .release import RELEASE_KINDS, claim_number, claim_periods, infer_metric, requires_release


CLAIM_TYPES = (
    "value",
    "change_pct",
    "change_abs",
    "record_high",
    "record_low",
    "first_time_above",
    "other",
    *RELEASE_KINDS,
)
COMPARATORS = ("eq", "approx", "gt", "gte", "lt", "lte")
PROGRAM_VERDICTS = ("supported", "contradicted", "unchecked", "insufficient_evidence")

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


def gap_assessment(
    stated: float | None,
    actual: float | None,
    comparator: str,
    tolerance: float | None,
    claim_type: str,
) -> dict[str, Any] | None:
    """Measure numeric accuracy without changing the program verdict.

    Relative gaps are fractions; percent-change gaps are percentage points.
    Major starts at 10% or 5 pp, and Severe starts above 50% or 20 pp.
    An undefined relative gap against zero has no assessment.
    """

    if (
        not all(_is_number(value) for value in (stated, actual, tolerance))
        or tolerance < 0
        or comparator not in COMPARATORS
        or claim_type not in CLAIM_TYPES
        or claim_type == "other"
    ):
        return None

    if comparator in {"gt", "gte"}:
        difference = max(0.0, stated - actual)
    elif comparator in {"lt", "lte"}:
        difference = max(0.0, actual - stated)
    else:
        difference = abs(stated - actual)

    points = claim_type == "change_pct"
    gap_kind = "points" if points else "relative"
    if difference <= tolerance:
        return {
            "gap_kind": gap_kind,
            "gap": 0.0,
            "direction_wrong": False,
            "severity": "exact",
            "score": 100.0,
        }

    if not points and actual == 0:
        return None
    gap = difference if points else difference / abs(actual)
    if not math.isfinite(gap):
        return None
    direction_wrong = points and (stated < 0 < actual or actual < 0 < stated)
    minor, major, severe = (1.0, 5.0, 20.0) if points else (0.02, 0.10, 0.50)
    if gap > severe:
        severity = "severe"
    elif gap >= major or direction_wrong:
        severity = "major"
    elif gap >= minor:
        severity = "moderate"
    else:
        severity = "minor"
    score = max(0.0, 100 - (4 if points else 200) * gap - (30 if direction_wrong else 0))
    return {
        "gap_kind": gap_kind,
        "gap": gap,
        "direction_wrong": direction_wrong,
        "severity": severity,
        "score": score,
    }


def program_check_gap(check: Mapping[str, Any]) -> dict[str, Any] | None:
    """Assess only a program check with an established numeric verdict."""

    if check.get("program_verdict") not in {"supported", "contradicted"}:
        return None
    return gap_assessment(
        check.get("stated_value_used"),
        check.get("actual_value"),
        str(check.get("comparator") or ""),
        check.get("tolerance"),
        str(check.get("claim_type") or ""),
    )


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


def _period_basis(evidence: Mapping[str, Any] | None) -> str | None:
    if evidence is None:
        return None
    basis = str(evidence.get("period_basis") or "").strip().lower()
    if basis in {"calendar", "fiscal"}:
        return basis
    period = str(evidence.get("period") or "").strip().upper()
    if re.fullmatch(r"FY\d{4}(?:Q[1-4])?", period):
        return "fiscal"
    if re.fullmatch(r"\d{4}Q[1-4]", period):
        return "calendar"
    return None


def _period_type(evidence: Mapping[str, Any] | None) -> str | None:
    if evidence is None:
        return None
    value = str(evidence.get("period_type") or "").strip().lower()
    if value in {"quarter", "annual", "ytd", "instant"}:
        return value
    period = str(evidence.get("period") or "").strip().upper()
    if re.fullmatch(r"(?:FY)?\d{4}Q[1-4]", period):
        return "quarter"
    if re.fullmatch(r"FY\d{4}", period):
        return "annual"
    start = evidence.get("start")
    end = evidence.get("end")
    if isinstance(start, str) and isinstance(end, str):
        try:
            duration = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
        except ValueError:
            duration = None
        if duration is not None:
            if 80 <= duration <= 100:
                return "quarter"
            if 300 <= duration <= 380:
                return "annual"
    return None


def _claim_text(sub_claim: Mapping[str, Any]) -> str:
    return " ".join(
        str(sub_claim.get(field) or "")
        for field in (
            "stated_text",
            "text",
            "original_claim",
            "claim",
            "claim_text",
            "_original_claim",
        )
    )


def _original_claim_text(sub_claim: Mapping[str, Any]) -> str:
    return next(
        (
            str(sub_claim.get(field))
            for field in ("original_claim", "claim", "claim_text", "_original_claim")
            if sub_claim.get(field)
        ),
        "",
    )


def _period_scope(sub_claim: Mapping[str, Any]) -> str | None:
    text = (_original_claim_text(sub_claim) or _claim_text(sub_claim)).lower()
    if re.search(
        r"\bfiscal\b|\bfy\b|\bfy\s*(?:20\d{2}|\d{2})(?:\s*q[1-4])?\b",
        text,
    ):
        return "fiscal"
    if re.search(
        r"\bcalendar\b|\bcy\b|\bcy\s*(?:20\d{2}|\d{2})(?:\s*q[1-4])?\b",
        text,
    ):
        return "calendar"
    return None


def _mentions_quarter(sub_claim: Mapping[str, Any]) -> bool:
    text = _claim_text(sub_claim).lower()
    return bool(
        re.search(
            r"\bq[1-4]\b|\b(?:first|second|third|fourth)[ -]quarter\b",
            text,
        )
    )


_MONTH_NAME_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
    re.IGNORECASE,
)
_UNLABELED_QUARTER_PATTERNS = (
    re.compile(r"\bq(?P<quarter>[1-4])\s*(?:of\s*)?(?P<year>20\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(?P<year>20\d{2})\s*q(?P<quarter>[1-4])\b", re.IGNORECASE),
    re.compile(
        r"\b(?P<ordinal>first|second|third|fourth)[ -]+quarter"
        r"(?:\s+of)?\s+(?P<year>20\d{2})\b",
        re.IGNORECASE,
    ),
)


def _unlabeled_quarter(sub_claim: Mapping[str, Any]) -> str | None:
    """Return the calendar-style label for an unlabeled quarter mention."""

    text = _claim_text(sub_claim)
    qualifier_text = _original_claim_text(sub_claim) or text
    qualifier_claim = {"text": qualifier_text}
    if (
        not text
        or _period_scope(qualifier_claim) is not None
        or _MONTH_NAME_RE.search(qualifier_text)
    ):
        return None
    ordinal_to_quarter = {
        "first": "1",
        "second": "2",
        "third": "3",
        "fourth": "4",
    }
    for pattern in _UNLABELED_QUARTER_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        quarter = match.groupdict().get("quarter")
        if quarter is None:
            ordinal = match.groupdict().get("ordinal")
            quarter = ordinal_to_quarter.get(str(ordinal).lower())
        year = match.groupdict().get("year")
        if quarter is not None and year is not None:
            return f"{year}Q{quarter}"
    return None


def _numeric_result(evidence: Mapping[str, Any] | None) -> bool:
    """Return whether an evidence object has a usable numeric result."""

    return bool(
        evidence is not None
        and "error" not in evidence
        and (
            _is_number(evidence.get("value"))
            or _is_number(evidence.get("pct_change"))
            or _is_number(evidence.get("abs_change"))
        )
    )


def _numeric_result_ids(value: Any, runner: Any) -> list[str]:
    return [
        evidence_id
        for evidence_id in _normalise_evidence_ids(value)
        if _numeric_result(_evidence(runner, evidence_id))
    ]


def _period_reading_key(evidence: Mapping[str, Any] | None) -> str | None:
    if evidence is None:
        return None
    period = _context_value(evidence.get("period"), "period")
    if period is None:
        period = _period_from_fact_context(
            _context_value(evidence.get("start"), "start"),
            _context_value(evidence.get("end"), "end"),
            _context_value(evidence.get("frame"), "frame"),
        )
    if period is None:
        return None
    return period


def _distinct_period_readings(
    evidence_ids: Sequence[str], runner: Any
) -> set[str]:
    return {
        reading
        for evidence_id in evidence_ids
        if (reading := _period_reading_key(_evidence(runner, evidence_id))) is not None
    }


def _select_period_interpretations(
    sub_claim: Mapping[str, Any],
    candidates: Sequence[str],
    runner: Any,
    *,
    explicit: bool,
) -> list[str]:
    """Apply the fiscal/calendar compatibility filters to numeric candidates."""

    selected = _unique_ids(candidates)
    if not selected:
        return []

    if not explicit:
        bases = {
            basis
            for evidence_id in selected
            if (basis := _period_basis(_evidence(runner, evidence_id))) is not None
        }
        if len(bases) < 2 or not _mentions_quarter(sub_claim):
            return []

    if _mentions_quarter(sub_claim):
        quarter_candidates = [
            evidence_id
            for evidence_id in selected
            if _period_type(_evidence(runner, evidence_id)) == "quarter"
        ]
        if quarter_candidates:
            selected = quarter_candidates
            claim_type = str(sub_claim.get("claim_type") or "")
            if claim_type in {"change_pct", "change_abs"}:
                compute_candidates = [
                    evidence_id
                    for evidence_id in selected
                    if _runner_evidence_kind(
                        runner, evidence_id, _evidence(runner, evidence_id) or {}
                    )
                    == "compute_change"
                ]
                if compute_candidates:
                    selected = compute_candidates

    scope = _period_scope(sub_claim)
    if scope is not None:
        scoped = [
            evidence_id
            for evidence_id in selected
            if _period_basis(_evidence(runner, evidence_id)) == scope
        ]
        # A legacy trace may not have period_basis on a derived fiscal
        # quarter. Keep its quarter evidence rather than treating an annual
        # FY fact as the fiscal-quarter interpretation.
        if scoped:
            selected = scoped
        elif explicit:
            selected = []

    selected = _unique_ids(selected)
    if len(_distinct_period_readings(selected, runner)) < 2:
        return []
    return selected


def _resolve_interpretation_ids(
    sub_claim: Mapping[str, Any],
    evidence_ids: Sequence[str],
    runner: Any,
    *,
    single_deduplicated: bool = False,
) -> tuple[list[str], bool]:
    """Resolve safe period citations and report dropped model entries.

    Older traces predate the ``interpretations`` field and often cite a
    calendar quarter plus a fiscal fact in ``evidence_ids``. If explicit
    interpretations are absent or unusable, retain that compatibility path,
    but only with numeric evidence that exists in this run.
    """

    raw_value = sub_claim.get("interpretations")
    raw_entries = _normalise_evidence_ids(raw_value)
    valid_explicit = _unique_ids(_numeric_result_ids(raw_entries, runner))
    invalid = (
        (raw_value is not None and not isinstance(raw_value, list) and bool(raw_value))
        or any(
            not _numeric_result(_evidence(runner, evidence_id))
            for evidence_id in raw_entries
        )
    )

    if single_deduplicated and len(valid_explicit) == 1:
        return valid_explicit, invalid

    if len(_distinct_period_readings(valid_explicit, runner)) >= 2:
        selected = _select_period_interpretations(
            sub_claim,
            valid_explicit,
            runner,
            explicit=True,
        )
        if selected:
            return selected, invalid

    # If explicit interpretations were dropped or did not provide two
    # distinct readings, evaluate the cited evidence using the pre-existing
    # evidence_ids compatibility behavior. Invalid/non-numeric results cannot
    # become interpretation children.
    fallback_candidates = _numeric_result_ids(evidence_ids, runner)
    selected = _select_period_interpretations(
        sub_claim,
        fallback_candidates,
        runner,
        explicit=False,
    )
    return selected, invalid


def _interpretation_ids(
    sub_claim: Mapping[str, Any], evidence_ids: Sequence[str], runner: Any
) -> list[str]:
    """Resolve safe explicit or legacy period-interpretation citations."""

    return _resolve_interpretation_ids(sub_claim, evidence_ids, runner)[0]


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


def _period_evidence_nodes(value: Any) -> list[Mapping[str, Any]]:
    """Return a fact result and any nested facts that carry period context."""

    found: list[Mapping[str, Any]] = []
    visited: set[int] = set()

    def visit(node: Any) -> None:
        if not isinstance(node, Mapping) or id(node) in visited:
            return
        visited.add(id(node))
        found.append(node)
        for key in ("current_fact", "base_fact", "current", "base", "components"):
            child = node.get(key)
            if isinstance(child, list):
                for item in child:
                    visit(item)
            else:
                visit(child)

    visit(value)
    return found


def _period_context(node: Mapping[str, Any]) -> dict[str, Any]:
    period = _period_reading_key(node)
    if period is None:
        fiscal_year = node.get("fiscal_year", node.get("fy"))
        fiscal_period = str(node.get("fiscal_period", node.get("fp")) or "").upper()
        try:
            fiscal_year_int = int(fiscal_year)
        except (TypeError, ValueError):
            fiscal_year_int = None
        if fiscal_year_int is not None and fiscal_period in {"Q1", "Q2", "Q3", "Q4"}:
            period = f"FY{fiscal_year_int:04d}{fiscal_period}"
    period_basis = _period_basis(node)
    if period_basis is None and period is not None:
        period_basis = "fiscal" if period.startswith("FY") else "calendar"
    return {
        "ticker": _context_value(node.get("ticker"), "ticker"),
        "metric": _context_value(node.get("metric"), "metric"),
        "period": period,
        "period_basis": period_basis,
        "fiscal_equals_calendar": node.get("fiscal_equals_calendar"),
        "base_period": _context_value(node.get("base_period"), "period"),
    }


def _period_contexts(
    evidence_ids: Sequence[str], runner: Any
) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for evidence_id in _unique_ids(evidence_ids):
        for node in _period_evidence_nodes(_evidence(runner, evidence_id)):
            context = _period_context(node)
            if context["ticker"] is None or context["metric"] is None:
                continue
            if context["period"] is None and context["period_basis"] is None:
                continue
            contexts.append(context)
    return contexts


def _bool_flag(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return None


def _period_target_label(target: str, basis: str) -> str:
    return f"FY{target}" if basis == "fiscal" else target


def _prior_period_label(period: str) -> str | None:
    match = re.fullmatch(r"(?:FY)?(\d{4})Q([1-4])", period.upper())
    if match is None:
        return None
    year, quarter = int(match.group(1)), match.group(2)
    prefix = "FY" if period.upper().startswith("FY") else ""
    return f"{prefix}{year - 1:04d}Q{quarter}"


def _program_dispatch(
    runner: Any, name: str, arguments: Mapping[str, Any]
) -> Mapping[str, Any] | None:
    """Run or reuse a program-side tool call and return its numbered result."""

    calls = getattr(runner, "calls", None)
    if isinstance(calls, list):
        for call in calls:
            if (
                isinstance(call, Mapping)
                and call.get("role") == "program"
                and call.get("name") == name
                and call.get("arguments") == dict(arguments)
                and isinstance(call.get("result"), Mapping)
            ):
                return call["result"]

    dispatch_program = getattr(runner, "dispatch_program", None)
    if callable(dispatch_program):
        result = dispatch_program(name, dict(arguments))
        return result if isinstance(result, Mapping) else None

    # Keep the checker usable with a lightweight runner supplied by an offline
    # replay test.  A real ToolRunner takes the branch above; this fallback
    # registers the same P-numbered evidence shape when only an EdgarClient is
    # attached to the runner.
    if name != "lookup_fact":
        return None
    edgar = getattr(runner, "edgar", None)
    lookup_fact = getattr(edgar, "lookup_fact", None)
    evidence = getattr(runner, "evidence", None)
    evidence_kind = getattr(runner, "evidence_kind", None)
    if not callable(lookup_fact) or not isinstance(evidence, dict):
        return None
    try:
        raw_result = lookup_fact(**dict(arguments))
    except Exception as exc:  # pragma: no cover - defensive adapter path
        raw_result = {"error": "tool_error", "message": str(exc)}
    result = dict(raw_result) if isinstance(raw_result, Mapping) else {"value": raw_result}
    existing_ids = [
        int(match.group(1))
        for evidence_id in evidence
        if (match := re.fullmatch(r"P(\d+)", str(evidence_id))) is not None
    ]
    evidence_id = f"P{max(existing_ids, default=0) + 1}"
    result["evidence_id"] = evidence_id
    evidence[evidence_id] = result
    if isinstance(evidence_kind, dict):
        evidence_kind[evidence_id] = name
    if isinstance(calls, list):
        calls.append(
            {
                "name": name,
                "arguments": dict(arguments),
                "result": result,
                "role": "program",
            }
        )
    return result


def _maybe_program_period_interpretation(
    sub_claim: Mapping[str, Any],
    evidence_ids: Sequence[str],
    interpretation_ids: Sequence[str],
    runner: Any,
) -> tuple[list[str], bool]:
    """Fetch a missing fiscal/calendar reading for an unlabeled quarter."""

    claim_type = str(sub_claim.get("claim_type") or "")
    if claim_type not in {"value", "change_pct", "change_abs"}:
        return [], False
    target = _unlabeled_quarter(sub_claim)
    if target is None:
        return [], False
    if len(_distinct_period_readings(interpretation_ids, runner)) >= 2:
        return [], False

    source_ids = _unique_ids([*evidence_ids, *interpretation_ids])
    contexts = _period_contexts(source_ids, runner)
    if not contexts:
        return [], False
    target_labels = {target, f"FY{target}"}
    matching_contexts = [
        context for context in contexts if context.get("period") in target_labels
    ]
    source_contexts = matching_contexts or contexts
    issuer_flags = [
        flag
        for context in source_contexts
        if (flag := _bool_flag(context.get("fiscal_equals_calendar"))) is not None
    ]
    if not issuer_flags:
        fiscal_equals_calendar = getattr(
            getattr(runner, "edgar", None), "fiscal_equals_calendar", None
        )
        if callable(fiscal_equals_calendar):
            try:
                flag = _bool_flag(fiscal_equals_calendar(source_contexts[0]["ticker"]))
            except Exception:  # pragma: no cover - provider adapter fallback
                flag = None
            if flag is not None:
                issuer_flags.append(flag)
    if not issuer_flags or any(flag is True for flag in issuer_flags):
        return [], False
    if not any(flag is False for flag in issuer_flags):
        return [], False

    bases = {
        str(context["period_basis"])
        for context in source_contexts
        if context.get("period_basis") in {"calendar", "fiscal"}
    }
    if len(bases) >= 2:
        return [], False
    if bases == {"fiscal"}:
        missing_basis = "calendar"
    elif bases == {"calendar"}:
        missing_basis = "fiscal"
    else:
        return [], False

    source_compute_id = next(
        (
            evidence_id
            for evidence_id in source_ids
            if _runner_evidence_kind(runner, evidence_id, _evidence(runner, evidence_id) or {})
            == "compute_change"
        ),
        None,
    )
    source_context = next(
        context
        for context in source_contexts
        if context.get("ticker") and context.get("metric")
    )
    ticker = str(source_context["ticker"])
    metric = str(source_context["metric"])
    period = _period_target_label(target, missing_basis)
    if source_compute_id is not None and claim_type in {"change_pct", "change_abs"}:
        source = _evidence(runner, source_compute_id) or {}
        prior_target = _prior_period_label(target)
        base_period = (
            _period_target_label(prior_target, missing_basis)
            if prior_target is not None
            else _context_value(source.get("base_period"), "period")
        )
        if base_period is None:
            return [], False
        result = _program_dispatch(
            runner,
            "compute_change",
            {
                "ticker": ticker,
                "metric": metric,
                "period": period,
                "base_period": base_period,
            },
        )
    else:
        result = _program_dispatch(
            runner,
            "lookup_fact",
            {"ticker": ticker, "metric": metric, "period": period},
        )
    if result is None or not _numeric_result(result):
        return [], False
    result_basis = _period_basis(result)
    if result_basis != missing_basis:
        return [], False
    evidence_id = result.get("evidence_id")
    if evidence_id is None:
        return [], False
    return [str(evidence_id)], True


_EVIDENCE_STRENGTH_ORDER = {"low": 0, "medium": 1, "high": 2}


def _provenance_nodes(value: Any) -> list[Mapping[str, Any]]:
    """Collect compact provenance nodes from a tool result and its components."""

    found: list[Mapping[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            provenance = node.get("provenance")
            if isinstance(provenance, Mapping):
                found.append(provenance)
                # A history result contains provenance for every comparison
                # row.  The evidence for the claim is its requested period,
                # represented by the result-level node; do not downgrade it
                # because an unrelated historical row was restated.
                return
            for key in ("current_fact", "base_fact", "current", "base", "components"):
                child = node.get(key)
                if child is not None:
                    visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return found


def _evidence_quality(
    evidence_ids: Sequence[str], runner: Any
) -> tuple[str, list[Mapping[str, Any]]]:
    nodes: list[Mapping[str, Any]] = []
    for evidence_id in _unique_ids(evidence_ids):
        nodes.extend(_provenance_nodes(_evidence(runner, evidence_id)))
    if not nodes:
        return "low", []
    strength = min(
        (str(node.get("strength") or "low") for node in nodes),
        key=lambda value: _EVIDENCE_STRENGTH_ORDER.get(value, 0),
    )
    return strength if strength in _EVIDENCE_STRENGTH_ORDER else "low", nodes


def _evidence_summary(nodes: Sequence[Mapping[str, Any]]) -> str:
    if not nodes:
        return "Evidence: unavailable"
    parts: list[str] = []
    for node in nodes:
        tier = str(node.get("tier") or "L2")
        forms = [str(form) for form in node.get("forms", []) if form]
        if tier == "L1":
            label = "audited 10-K"
        elif tier == "L3":
            component_tiers = "/".join(
                str(value) for value in node.get("component_tiers", []) if value
            )
            label = f"derived L3{f' ({component_tiers} components)' if component_tiers else ''}"
        elif node.get("form_fallback"):
            label = "form fallback"
            if forms:
                label += f" ({', '.join(forms)})"
        elif forms and forms != ["10-Q"]:
            label = f"reviewed 10-Q ({', '.join(forms)})"
        else:
            label = "reviewed 10-Q"
        confirmations = node.get("confirmations")
        if isinstance(confirmations, int) and confirmations > 0:
            label += f", confirmed in {confirmations} filing{'s' if confirmations != 1 else ''}"
        label += ", restated" if node.get("restated") else ", not restated"
        if label not in parts:
            parts.append(label)
    return "Evidence: " + "; ".join(parts)


def _with_evidence_quality(
    result: Mapping[str, Any], evidence_ids: Sequence[str], runner: Any
) -> dict[str, Any]:
    """Attach program-owned evidence strength and restatement flags."""

    value = dict(result)
    value["gap"] = program_check_gap(value)
    strength, nodes = _evidence_quality(evidence_ids, runner)
    value["evidence_strength"] = strength
    value["evidence_summary"] = _evidence_summary(nodes)
    only_restatement = bool(nodes) and all(bool(node.get("restated")) for node in nodes)
    restated_evidence = bool(
        only_restatement
        and value.get("program_verdict") in {"supported", "contradicted"}
    )
    value["restated_evidence"] = restated_evidence
    if restated_evidence:
        flags = value.get("flags")
        flags = list(flags) if isinstance(flags, list) else []
        if "restated_evidence" not in flags:
            flags.append("restated_evidence")
        value["flags"] = flags
    return value


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


def _lookup_fact_identity(evidence: Mapping[str, Any] | None) -> tuple[Any, ...] | None:
    """Return the identity of a numeric lookup fact, ignoring filing metadata."""

    if evidence is None or "error" in evidence:
        return None
    required = ("concept", "start", "end", "value")
    if not all(key in evidence for key in required) or not _is_number(evidence["value"]):
        return None
    return (
        "lookup_fact",
        evidence.get("ticker"),
        evidence.get("metric"),
        evidence["concept"],
        evidence["start"],
        evidence["end"],
        float(evidence["value"]),
    )


def _compute_change_identity(evidence: Mapping[str, Any] | None) -> tuple[Any, ...] | None:
    """Return the identity of a compute result from its current/base facts."""

    if evidence is None or "error" in evidence:
        return None
    current = next(
        (
            value
            for field in ("current_fact", "current")
            if isinstance(value := evidence.get(field), Mapping)
        ),
        None,
    )
    base = next(
        (
            value
            for field in ("base_fact", "base")
            if isinstance(value := evidence.get(field), Mapping)
        ),
        None,
    )
    current_identity = _lookup_fact_identity(current)
    base_identity = _lookup_fact_identity(base)
    if current_identity is None or base_identity is None:
        return None
    return ("compute_change", current_identity, base_identity)


def _history_rank_identity(evidence: Mapping[str, Any] | None) -> tuple[Any, ...] | None:
    """Return the comparable-period window used by a history result."""

    if evidence is None or "error" in evidence:
        return None
    rows = evidence.get("periods")
    if not isinstance(rows, list):
        rows = evidence.get("comparable_periods")
    if isinstance(rows, list):
        window = tuple(
            (
                row.get("end", row.get("end_date")),
                row.get("value"),
                row.get("period_type"),
                (
                    re.sub(r"^FY(\d{4})Q", r"\1Q", str(row.get("period")))
                    if row.get("period") is not None
                    else None
                ),
            )
            for row in rows
            if isinstance(row, Mapping)
        )
    else:
        window = ()
    if not window:
        periods_considered = evidence.get("periods_considered")
        if not isinstance(periods_considered, Mapping):
            return None
        window = (
            (
                re.sub(
                    r"^FY(\d{4})Q", r"\1Q", str(periods_considered.get("first"))
                ),
                re.sub(
                    r"^FY(\d{4})Q", r"\1Q", str(periods_considered.get("last"))
                ),
            ),
        )
    return (
        "history_rank",
        evidence.get("ticker"),
        evidence.get("metric"),
        window,
    )


def _evidence_identity(
    evidence_id: str, runner: Any
) -> tuple[Any, ...] | None:
    evidence = _evidence(runner, evidence_id)
    if evidence is None:
        return None
    kind = _runner_evidence_kind(runner, evidence_id, evidence)
    if kind == "lookup_fact":
        return _lookup_fact_identity(evidence)
    if kind == "compute_change":
        return _compute_change_identity(evidence)
    if kind == "history_rank":
        return _history_rank_identity(evidence)
    return None


def _deduplicate_evidence_ids(
    evidence_ids: Sequence[str], runner: Any
) -> tuple[list[str], list[list[str]]]:
    """Collapse citations that resolve to the same underlying evidence.

    The first citation remains authoritative.  The returned groups include that
    citation and every citation collapsed into it so callers can retain a
    complete audit trail.
    """

    selected: list[str] = []
    seen: dict[tuple[Any, ...], int] = {}
    groups: list[list[str]] = []
    for evidence_id in _normalise_evidence_ids(list(evidence_ids)):
        identity = _evidence_identity(evidence_id, runner)
        if identity is None:
            if evidence_id not in selected:
                selected.append(evidence_id)
            continue
        group_index = seen.get(identity)
        if group_index is None:
            seen[identity] = len(groups)
            groups.append([evidence_id])
            selected.append(evidence_id)
        else:
            groups[group_index].append(evidence_id)
    return selected, [group for group in groups if len(group) > 1]


def _same_fact(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """Compare the identifying fact fields used by duplicate evidence."""

    left_identity = _lookup_fact_identity(left)
    right_identity = _lookup_fact_identity(right)
    if left_identity is None or right_identity is None:
        return False
    return left_identity == right_identity


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


def _interpretation_reason(
    evidence_ids: Sequence[str], child_checks: Sequence[Mapping[str, Any]]
) -> str:
    parts: list[str] = []
    for evidence_id, child in zip(evidence_ids, child_checks):
        actual = child.get("actual_value")
        actual_text = "none" if actual is None else f"{float(actual):g}"
        parts.append(
            f"{evidence_id} actual {actual_text} -> {child.get('program_verdict')}"
        )
    return "; ".join(parts)


def _evaluate_period_interpretations(
    sub_claim: Mapping[str, Any],
    runner: Any,
    related_sub_claims: Sequence[Mapping[str, Any]] | None,
    evidence_ids: list[str],
    interpretation_ids: list[str],
    invalid_interpretations: bool,
    deduplicated_evidence: list[str],
    program_added_interpretation: bool = False,
    program_evidence_ids: Sequence[str] = (),
) -> dict[str, Any]:
    child_claims = []
    for evidence_id in interpretation_ids:
        child = dict(sub_claim)
        child["evidence_ids"] = [evidence_id]
        child["interpretations"] = []
        child_claims.append(child)
    child_checks = [
        evaluate_sub_claim(
            child,
            runner,
            related_sub_claims,
            _allow_interpretations=False,
        )
        for child in child_claims
    ]
    if not child_checks:
        # This is only reachable when an explicit interpretation list was
        # incompatible with an explicit fiscal/calendar qualifier.  The
        # ordinary checker reports the missing evidence cleanly.
        fallback = dict(sub_claim)
        fallback["interpretations"] = []
        result = evaluate_sub_claim(
            fallback,
            runner,
            related_sub_claims,
            _allow_interpretations=False,
        )
        result["evidence_ids"] = evidence_ids
        result["interpretations"] = []
        result["invalid_interpretations"] = invalid_interpretations
        result["deduplicated_evidence"] = deduplicated_evidence
        result["program_added_interpretation"] = program_added_interpretation
        result["program_evidence_ids"] = list(program_evidence_ids)
        if invalid_interpretations:
            result["reason"] = f"invalid_interpretations; {result.get('reason', '')}"
        return _with_evidence_quality(result, evidence_ids, runner)

    child_verdicts = [str(child.get("program_verdict")) for child in child_checks]
    if all(value == "supported" for value in child_verdicts):
        program_verdict = "supported"
    elif all(value == "contradicted" for value in child_verdicts):
        program_verdict = "contradicted"
    else:
        program_verdict = "unchecked"

    period_ambiguous = (
        program_verdict == "unchecked"
        and "supported" in child_verdicts
        and "contradicted" in child_verdicts
    )
    first = dict(child_checks[0])
    model_verdict = sub_claim.get("verdict")
    values = [child.get("actual_value") for child in child_checks]
    detail = _interpretation_reason(interpretation_ids, child_checks)
    if program_verdict == "unchecked":
        reason = f"period_ambiguous; interpretations: {detail}"
    else:
        reason = f"period interpretations all {program_verdict}: {detail}"
    if invalid_interpretations:
        reason = f"invalid_interpretations; {reason}"
    if first.get("comparator_corrected"):
        reason = f"comparator_corrected; {reason}"

    first.update(
        {
            "evidence_ids": evidence_ids,
            "interpretations": interpretation_ids,
            "interpretation_results": [
                {
                    "evidence_id": evidence_id,
                    "program_verdict": child.get("program_verdict"),
                    "actual_value": child.get("actual_value"),
                    "reason": child.get("reason"),
                }
                for evidence_id, child in zip(interpretation_ids, child_checks)
            ],
            "interpretation_values": values,
            "evidence_valid": all(child.get("evidence_valid") for child in child_checks),
            "program_verdict": program_verdict,
            "actual_value": values[0] if len(values) == 1 else None,
            "tolerance": first.get("tolerance") if len(values) == 1 else None,
            "reason": reason,
            "period_ambiguous": period_ambiguous,
            "invalid_interpretations": invalid_interpretations,
            "deduplicated_evidence": deduplicated_evidence,
            "program_added_interpretation": program_added_interpretation,
            "program_evidence_ids": list(program_evidence_ids),
            "disagreement": (
                program_verdict != "unchecked" and model_verdict != program_verdict
            ),
        }
    )
    return _with_evidence_quality(first, evidence_ids, runner)


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
    *,
    _allow_interpretations: bool = True,
) -> dict[str, Any]:
    """Evaluate one normalized model sub-claim against cited evidence."""

    original = str(sub_claim.get("original_claim") or sub_claim.get("text") or "")
    if sub_claim.get("claim_type") == "reported_in_release" and not requires_release(original):
        # A failed release search is not a quote and must not hide a cited
        # authoritative GAAP fact. Re-enter the normal value checker, retaining
        # its issuer/metric/unit/period validation and original user wording.
        kinds = getattr(runner, "evidence_kind", {})
        cited = _normalise_evidence_ids(sub_claim.get("evidence_ids"))
        metric = infer_metric(original)
        stated = claim_number(original, metric) if metric else None
        literal = str(sub_claim.get('stated_text') or '')
        parsed = parse_stated_number(literal)
        level_matches = (stated and stated['low'] == stated['high'] and literal and literal in original
                         and parsed and math.isclose(parsed.value, stated['low'], rel_tol=1e-12, abs_tol=1e-10))
        periods = claim_periods(original)
        from .release_checks import _issuer_matches
        facts = [eid for eid in cited if kinds.get(eid) == "lookup_fact"
                 and isinstance(runner.evidence.get(eid), Mapping)
                 and not runner.evidence[eid].get("error")
                 and (runner.evidence[eid].get("provenance") or {}).get("tier") in {"L1", "L2"}
                 and level_matches and stated['unit'] == runner.evidence[eid].get('unit')
                 and metric == runner.evidence[eid].get('metric')
                 and _issuer_matches(original, runner.evidence[eid])
                 and periods == {runner.evidence[eid].get('period')}]
        if facts and not any(kinds.get(eid) == "quote_release" for eid in cited):
            result = evaluate_sub_claim(
                {**sub_claim, "claim_type": "value", "evidence_ids": facts,
                 "interpretations": [eid for eid in sub_claim.get("interpretations", []) if eid in facts]},
                runner, related_sub_claims, _allow_interpretations=_allow_interpretations)
            result["reported_release_xbrl_fallback"] = True
            return result

    if requires_release(str(sub_claim.get("original_claim") or sub_claim.get("text") or "")) or sub_claim.get("claim_type") in RELEASE_KINDS or any(
        getattr(runner, "evidence_kind", {}).get(str(eid)) in {"find_earnings_release", "quote_release"}
        for eid in sub_claim.get("evidence_ids", [])
    ):
        from .release_checks import evaluate_release_claim
        return evaluate_release_claim(sub_claim, runner)

    raw_evidence_ids = _normalise_evidence_ids(sub_claim.get("evidence_ids"))
    evidence_ids, evidence_groups = _deduplicate_evidence_ids(raw_evidence_ids, runner)
    raw_interpretation_ids = _normalise_evidence_ids(sub_claim.get("interpretations"))
    interpretation_source_ids, interpretation_groups = _deduplicate_evidence_ids(
        raw_interpretation_ids, runner
    )
    deduplicated_evidence = _unique_ids(
        [evidence_id for group in [*evidence_groups, *interpretation_groups] for evidence_id in group]
    )
    interpretation_ids, invalid_interpretations = (
        _resolve_interpretation_ids(
            {**sub_claim, "interpretations": interpretation_source_ids},
            evidence_ids,
            runner,
            single_deduplicated=bool(interpretation_groups),
        )
        if _allow_interpretations
        else ([], False)
    )
    claim_type = str(sub_claim.get("claim_type") or "")
    model_comparator = sub_claim.get("comparator")
    model_comparator_text = (
        str(model_comparator) if model_comparator is not None else ""
    )
    original_claim = next(
        (
            str(sub_claim.get(field))
            for field in ("original_claim", "claim", "claim_text")
            if sub_claim.get(field)
        ),
        "",
    )
    comparator = infer_comparator(
        sub_claim.get("stated_text"),
        sub_claim.get("text"),
        original_claim,
    )
    comparator_corrected = model_comparator_text != comparator
    if comparator_corrected:
        flags_for_comparator = ["comparator_corrected"]
    else:
        flags_for_comparator = []

    program_evidence_ids: list[str] = []
    program_added_interpretation = False
    if _allow_interpretations:
        program_evidence_ids, program_added_interpretation = (
            _maybe_program_period_interpretation(
                sub_claim,
                evidence_ids,
                interpretation_ids,
                runner,
            )
        )
        if program_added_interpretation:
            raw_evidence_ids = _unique_ids([*raw_evidence_ids, *program_evidence_ids])
            raw_interpretation_ids = _unique_ids(
                [*raw_interpretation_ids, *program_evidence_ids]
            )
            evidence_ids, evidence_groups = _deduplicate_evidence_ids(
                raw_evidence_ids, runner
            )
            interpretation_source_ids, interpretation_groups = _deduplicate_evidence_ids(
                raw_interpretation_ids, runner
            )
            deduplicated_evidence = _unique_ids(
                [
                    evidence_id
                    for group in [*evidence_groups, *interpretation_groups]
                    for evidence_id in group
                ]
            )
            interpretation_ids, invalid_interpretations = _resolve_interpretation_ids(
                {**sub_claim, "interpretations": interpretation_source_ids},
                evidence_ids,
                runner,
                single_deduplicated=bool(interpretation_groups),
            )

    if interpretation_ids:
        return _evaluate_period_interpretations(
            sub_claim,
            runner,
            related_sub_claims,
            evidence_ids,
            interpretation_ids,
            invalid_interpretations,
            deduplicated_evidence,
            program_added_interpretation,
            program_evidence_ids,
        )

    if claim_type in {"record_high", "record_low"}:
        stated, precision, flags = _record_number_and_precision(sub_claim)
    elif claim_type == "other":
        stated_value = sub_claim.get("stated_value")
        stated = float(stated_value) if _is_number(stated_value) else None
        precision = None
        flags = []
    else:
        stated, precision, flags = _number_and_precision(sub_claim)
    flags.extend(flags_for_comparator)
    if claim_type in {"change_pct", "change_abs"}:
        stated = _apply_change_direction(sub_claim, stated, flags)
    if invalid_interpretations:
        flags.append("invalid_interpretations")

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
                    return _with_evidence_quality({
                        "text": str(sub_claim.get("text") or ""),
                        "claim_type": claim_type,
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
                        "comparator": comparator,
                        "model_comparator": model_comparator_text,
                        "comparator_corrected": comparator_corrected,
                        "interpretations": [],
                        "period_ambiguous": False,
                        "program_added_interpretation": program_added_interpretation,
                        "program_evidence_ids": list(program_evidence_ids),
                        "invalid_interpretations": invalid_interpretations,
                        "deduplicated_evidence": deduplicated_evidence,
                    }, evidence_ids, runner)
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
        "model_comparator": model_comparator_text,
        "comparator_corrected": comparator_corrected,
    }
    if flags:
        flag_reason = ", ".join(flags)
        if reason != flag_reason and not reason.startswith(f"{flag_reason};"):
            reason = f"{flag_reason}; {reason}"

    return _with_evidence_quality({
        "text": str(sub_claim.get("text") or ""),
        "claim_type": claim_type,
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
        "comparator": comparator,
        "interpretations": [],
        "period_ambiguous": False,
        "program_added_interpretation": program_added_interpretation,
        "program_evidence_ids": list(program_evidence_ids),
        "invalid_interpretations": invalid_interpretations,
        "deduplicated_evidence": deduplicated_evidence,
        **flag_fields,
    }, evidence_ids, runner)


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
    "gap_assessment",
    "program_check_gap",
    "evaluate_sub_claim",
    "evaluate_verdict",
    "overall_program_verdict",
]
