"""Program-owned L4 verdicts; the model chooses a cached span, never a number."""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

from .numbers import infer_comparator, parse_stated_number
from .release import RELEASE_KINDS, _OUTLOOK, claim_number, claim_periods, infer_metric


def _issuer_matches(text: str, evidence: Mapping[str, Any]) -> bool:
    if re.search(r"\b" + re.escape(evidence["ticker"]) + r"\b", text, re.I):
        return True
    entity = re.sub(r"\b(?:INCORPORATED|INC|CORPORATION|CORP|LTD|LIMITED|CLASS|COM|PLC)\b|[.,]", " ", evidence["entity"], flags=re.I)
    entity = re.sub(r"\s+", " ", entity).strip()
    return len(entity) >= 3 and bool(re.search(r"\b" + re.escape(entity) + r"\b", text, re.I))


def _equal(left: float, right: float, tolerance: float = 0.0) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=tolerance + 1e-10)


def evaluate_release_claim(sub: Mapping[str, Any], runner: Any) -> dict[str, Any]:
    ids = list(dict.fromkeys(str(i) for i in sub.get("evidence_ids", []) if isinstance(i, str)))
    result: dict[str, Any] = {
        "text": str(sub.get("text") or ""), "evidence_ids": ids,
        "evidence_valid": False, "program_verdict": "insufficient_evidence",
        "actual_value": None, "actual_range": None, "stated_value": None,
        "stated_value_used": None, "stated_range": None, "tolerance": None,
        "reason": "no_verified_release_quote", "disagreement": False,
        "evidence_strength": "low", "evidence_summary": "Evidence: unavailable",
        "flags": [], "interpretations": [], "period_ambiguous": False,
    }

    def finish(reason: str) -> dict[str, Any]:
        result["reason"] = reason
        result["disagreement"] = sub.get("verdict") != result["program_verdict"]
        return result

    original = str(sub.get("original_claim") or sub.get("claim") or sub.get("text") or "")
    if re.search(r"[€£¥]|\b(?:EUR|GBP|CAD|CNY|JPY|TWD|Canadian dollars|euros|sterling)\b|NT\$", original, re.I):
        return finish("unsupported_release_currency")
    stated = str(sub.get("stated_text") or "")
    if not stated or stated not in original:
        return finish("stated_text_not_in_original_claim")
    metric = infer_metric(original)
    if metric is None:
        return finish("unsupported_release_metric")
    if metric == "revenue" and re.search(r"\b(?:segment|aws|north america|international|digital media|digital experience|iphone|services|data center|gaming|constant currency|organic|pro forma|non[ -]gaap|adjusted)\b", original, re.I):
        return finish("release_revenue_scope_not_consolidated_gaap")
    periods = claim_periods(original)
    # The original user's period takes precedence over a rewritten sub-claim.
    # Multiple periods require an exact atomic quote to establish the scope.
    atomic = original
    if len(periods) > 1:
        proposed = str(sub.get("text") or "")
        if proposed and proposed in original and len(claim_periods(proposed)) == 1:
            atomic, periods = proposed, claim_periods(proposed)
            metric = infer_metric(proposed)
        else:
            return finish("ambiguous_release_claim_period")
    if len(periods) != 1 or metric is None:
        return finish("explicit_release_claim_period_required")
    period = next(iter(periods))
    claimed = claim_number(atomic, metric)
    if claimed is None:
        return finish("release_claim_number_unparsed_or_verbal")
    if infer_comparator(stated, atomic) not in {"eq", "approx"}:
        return finish("release_inequality_not_supported")
    kind = "guidance" if _OUTLOOK.search(atomic) else "non_gaap" if metric.startswith("adjusted_") or metric == "free_cash_flow" else "reported_in_release"
    service = getattr(runner, "release_service", None)
    quotes = []
    for eid in ids:
        evidence = runner.evidence.get(eid)
        if not isinstance(evidence, Mapping) or runner.evidence_kind.get(eid) != "quote_release" or not service:
            continue
        try:
            verified = service.quote(evidence["candidate_id"], evidence["start"], evidence["end"])
        except (KeyError, ValueError, RuntimeError, TypeError):
            continue
        if verified["metric"] != metric or verified["claim_kind"] != kind:
            continue
        if not _issuer_matches(atomic, verified):
            continue
        if period != verified["period"] and not (verified["calendar_equals_fiscal"] and period.removeprefix("FY") == verified["period"].removeprefix("FY")):
            continue
        if verified["unit"] != claimed["unit"]:
            continue
        quotes.append(verified)
    if not quotes:
        return finish("release_quote_issuer_metric_kind_unit_or_period_mismatch")
    values = {(q["low"], q["high"]) for q in quotes}
    # A model cannot hide a conflicting number returned by the same search.
    all_values = {(q["low"], q["high"]) for q in service.candidates.values()
                  if q["ticker"] == quotes[0]["ticker"] and q["metric"] == metric
                  and q["claim_kind"] == kind and q["period"] == quotes[0]["period"]}
    if len(values) != 1 or len(all_values) != 1:
        return finish("ambiguous_or_revised_release_values")
    quote = quotes[0]
    actual_low, actual_high = quote["low"], quote["high"]
    result.update(evidence_valid=True, evidence_strength="medium",
                  evidence_summary=f"Evidence: furnished, unaudited {quote['form']} (L4), filed {quote['filed']}",
                  release_evidence=quote, stated_range=[claimed["low"], claimed["high"]],
                  stated_value=claimed["low"] if claimed["low"] == claimed["high"] else None,
                  stated_value_used=claimed["low"] if claimed["low"] == claimed["high"] else None,
                  comparator="eq", actual_range=[actual_low, actual_high])

    if kind == "reported_in_release":
        filing = runner.dispatch_program("lookup_fact", {"ticker": quote["ticker"], "metric": metric, "period": period})
        result["filing_cross_check"] = filing
        provenance = filing.get("provenance", {})
        value = filing.get("value")
        # A wrong-date, YTD, different-unit, or fallback form does not outrank
        # this release, even if its result superficially has a number.
        if (not filing.get("error") and type(value) in {int, float} and math.isfinite(value)
                and provenance.get("tier") in {"L1", "L2"} and not provenance.get("form_fallback")
                and filing.get("period") == period and filing.get("unit") == quote["unit"]
                and filing.get("period_type") == quote["period_type"]
                and (not quote.get("period_end") or filing.get("end") == quote["period_end"])):
            result["evidence_ids"].append(filing["evidence_id"])
            if not _equal(actual_low, value):
                result["flags"].append("release_vs_filing_mismatch")
            actual_low = actual_high = float(value)
            result["actual_range"] = [actual_low, actual_high]
            result["authoritative_tier"] = provenance["tier"]
            if provenance.get("strength") == "low":
                result["evidence_strength"] = "low"
            result["evidence_summary"] += f"; authoritative XBRL {provenance['tier']}"
    c_lo, c_hi = claimed["low"], claimed["high"]
    if c_lo != c_hi:
        matches = _equal(c_lo, actual_low) and _equal(c_hi, actual_high)
        result["tolerance"] = 0.0
    else:
        # A point inside a range is not the same assertion as that range. An
        # explicit +/- center is a stated issuer point and is comparable.
        if actual_low != actual_high:
            if quote["center"] is None:
                return finish("point_claim_requires_release_point_or_explicit_center")
            actual_low = quote["center"]
        precision = parse_stated_number(claimed["literal"])
        tolerance = precision.precision / 2 if precision else 0.0
        result["tolerance"] = tolerance
        result["actual_value"] = actual_low
        matches = _equal(c_lo, actual_low, tolerance)
    result["program_verdict"] = "supported" if matches else "contradicted"
    return finish("release_numeric_period_label_match" if matches else "release_numeric_contradiction")
