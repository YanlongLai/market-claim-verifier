"""Filed component calculations and explicitly scoped XBRL segment facts."""
from __future__ import annotations

import math
import re
from typing import Any
from datetime import date

from .edgar import (_SelectedFact, _FactGroup, _matches_period, _derived_provenance,
                    _with_period_metadata)

MARGINS = {"net_margin": "net_income", "operating_margin": "operating_income", "gross_margin": "gross_profit"}
# Exact taxonomy members/concepts; no substring matching against a segment name.
SEGMENTS = {
    "aws_revenue": {"0001018724": {"AmazonWebServicesMember", "AmazonWebServicesSegmentMember", "AmazonWebServicesSegmentNetSales"}},
    "google_cloud_revenue": {"0001652044": {"GoogleCloudMember", "GoogleCloudRevenue"}},
    "data_center_revenue": {
        "0001045810": {"DataCenterMember", "DataCenterRevenue"},
        "0000002488": {"DataCenterMember", "DataCenterSegmentMember", "DataCenterRevenue"}},
}
EXTRA_METRICS = tuple(MARGINS) + tuple(SEGMENTS)


def margin(edgar: Any, ticker: str, metric: str, period: str) -> dict:
    numerator = edgar.lookup_fact(ticker, MARGINS[metric], period)
    denominator = edgar.lookup_fact(ticker, "revenue", period)
    result = {"ticker": ticker, "metric": metric, "period": period, "unit": "percent",
              "derived": True, "components": [numerator, denominator],
              "formula": f"{MARGINS[metric]} / revenue * 100",
              "derivation": f"{MARGINS[metric]} / revenue * 100"}
    if numerator.get("error") or denominator.get("error"):
        return {**result, "error": "filed margin components unavailable", "reason": "both filed numerator and revenue required"}
    if any(numerator.get(k) != denominator.get(k) for k in ("cik", "start", "end", "period_type", "unit")) or numerator.get("unit") != "USD":
        return {**result, "error": "margin component issuer, dates, units or duration mismatch"}
    a, b = numerator.get("value"), denominator.get("value")
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (a, b)) or b <= 0:
        return {**result, "error": "margin denominator must be positive; both inputs finite"}
    return {**numerator, **result, "value": a / b * 100,
            "inputs": {MARGINS[metric]: a, "revenue": b},
            "provenance": _derived_provenance(c["provenance"] for c in (numerator, denominator))}


def segment_fact(edgar: Any, ticker: str, metric: str, period: str) -> dict:
    company = edgar.resolve_ticker(ticker)
    allowed = SEGMENTS[metric].get(company.get("cik"), set())
    missing = {**company, "metric": metric, "period": period, "error": "segment revenue unavailable",
               "reason": "no exact XBRL segment fact; earnings-release table required"}
    if not allowed or period.upper() == "LATEST":
        return missing
    document, digest = edgar._facts_document(company["cik"])
    matches = []
    for namespace, concepts in document.get("facts", {}).items():
        for concept, data in concepts.items():
            for row in data.get("units", {}).get("USD", []):
                dimensions = row.get("dimensions", row.get("segment", {}))
                if isinstance(dimensions, dict):
                    members = {str(v).split(":")[-1] for v in dimensions.values()}
                else:
                    members = set()
                exact_concept = concept in allowed
                if not exact_concept and not (concept in {"Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"} and members & allowed):
                    continue
                # Extra dimensions (geography/product combinations) are not totals.
                fiscal = re.fullmatch(r"FY(\d{4})Q([1-4])", period.upper())
                matches_period = (str(row.get("fy")) == fiscal[1] and str(row.get("fp")) == "Q" + fiscal[2]
                                  and row.get("start") and 80 <= (date.fromisoformat(row["end"]) - date.fromisoformat(row["start"])).days <= 100) if fiscal else _matches_period(row, period.upper())
                if members - allowed or not matches_period:
                    continue
                group = _FactGroup(f"{namespace}:{concept}", "USD", (row,), 0)
                fact = edgar._direct_result(company, document, digest, metric, _SelectedFact(group, row, False))
                fact["segment_dimensions"] = dimensions
                matches.append(fact)
    if not matches:
        return missing
    latest = max(str(c.get("filed", "")) for c in matches)
    matches = [c for c in matches if str(c.get("filed", "")) == latest]
    if len({(c.get("value"), c.get("start"), c.get("end")) for c in matches}) != 1:
        return {**missing, "error": "ambiguous XBRL segment values"}
    return _with_period_metadata(matches[0], period.upper())
