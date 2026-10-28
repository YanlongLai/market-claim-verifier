"""Period-based fiscal labels for SEC companyfacts.

SEC companyfacts ``fy``/``fp`` describe the *filing* a fact came from, not the period the fact covers. Comparative
values carry the later filing's labels, and some filings carry a fiscal-year focus that differs from the issuer's own
naming (e.g. Oracle's quarter ended 2026-08-31 is "fiscal 2027 Q1" but is tagged ``fy=2026``). This module recomputes
both labels from the period dates and the issuer's fiscal year-end, taken from its annual (10-K) periods. Fiscal years
are named by the calendar year in which they end (a year ending in the first days of January counts as the
previous calendar year), which is the convention of every issuer in the snapshot.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any, Iterable, Mapping

ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}
# 52/53-week fiscal years end on a weekday near a fixed date, so period ends can sit a few days after the nominal
# year-end of the previous fiscal year.
SLACK = timedelta(days=7)


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _iter_facts(document: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    for taxonomy in (document.get("facts") or {}).values():
        if not isinstance(taxonomy, Mapping):
            continue
        for concept in taxonomy.values():
            units = concept.get("units") if isinstance(concept, Mapping) else None
            if not isinstance(units, Mapping):
                continue
            for facts in units.values():
                for fact in facts or []:
                    if isinstance(fact, dict):
                        yield fact


def fiscal_year_ends(document: Mapping[str, Any]) -> list[date]:
    """Distinct fiscal year-end dates from annual filings, oldest first.

    Annual filings also carry 12-month amounts that are not fiscal years (trailing periods, pro forma tables), so only
    ends in the issuer's dominant year-end month are kept.
    """

    ends: set[date] = set()
    for fact in _iter_facts(document):
        if str(fact.get("form") or "").upper() not in ANNUAL_FORMS:
            continue
        start, end = _date(fact.get("start")), _date(fact.get("end"))
        if start is None or end is None or not 350 <= (end - start).days <= 380:
            continue
        ends.add(end)
    if not ends:
        return []
    months = Counter((end - SLACK).month for end in ends)
    year_end_month = months.most_common(1)[0][0]
    merged: list[date] = []
    for end in sorted(end for end in ends if (end - SLACK).month == year_end_month):
        # Collapse ends within the slack window (restated or differently tagged copies of the same fiscal year).
        if merged and end - merged[-1] <= SLACK:
            merged[-1] = end
        else:
            merged.append(end)
    return merged


def _shift_years(anchor: date, years: int) -> date:
    try:
        return anchor.replace(year=anchor.year + years)
    except ValueError:  # Feb 29
        return anchor.replace(year=anchor.year + years, day=28)


def fiscal_label(end: date, year_ends: list[date]) -> tuple[int, int] | None:
    """Return (fiscal_year, quarter 1-4) for a period ending on ``end``."""

    if not year_ends:
        return None
    fiscal_end = next((candidate for candidate in year_ends if end <= candidate + SLACK), None)
    if fiscal_end is None:
        years = 1
        while _shift_years(year_ends[-1], years) + SLACK < end:
            years += 1
        fiscal_end = _shift_years(year_ends[-1], years)
    elif fiscal_end == year_ends[0]:
        while end <= _shift_years(fiscal_end, -1) + SLACK:
            fiscal_end = _shift_years(fiscal_end, -1)
    previous = next((candidate for candidate in reversed(year_ends) if candidate < fiscal_end - SLACK), None)
    if previous is None or (fiscal_end - previous).days > 380:
        previous = _shift_years(fiscal_end, -1)
    quarter = round((end - previous).days / ((fiscal_end - previous).days / 4))
    # A year ending in the first days of January belongs to the previous calendar year's fiscal year (J&J, AMD).
    return (fiscal_end - SLACK).year, min(max(quarter, 1), 4)


def normalize_fiscal_labels(document: dict[str, Any]) -> dict[str, Any]:
    """Rewrite ``fy``/``fp`` on every fact from its own period; keep the filing labels as ``filing_fy``/``filing_fp``."""

    if document.get("_fiscal_labels_normalized"):
        return document
    year_ends = fiscal_year_ends(document)
    if not year_ends:
        return document
    for fact in _iter_facts(document):
        end = _date(fact.get("end"))
        label = fiscal_label(end, year_ends) if end is not None else None
        if label is None:
            continue
        fact.setdefault("filing_fy", fact.get("fy"))
        fact.setdefault("filing_fp", fact.get("fp"))
        start = _date(fact.get("start"))
        fiscal_year, quarter = label
        fact["fy"] = fiscal_year
        if start is not None and 350 <= (end - start).days <= 380:
            # Trailing-twelve-month amounts in 10-Qs (Amazon) are not fiscal years.
            fact["fp"] = "FY" if quarter == 4 else "TTM"
        elif start is None and quarter == 4:
            fact["fp"] = "FY"  # year-end balance sheet, as annual filings tag it
        else:
            fact["fp"] = f"Q{quarter}"
    document["_fiscal_labels_normalized"] = True
    return document
