"""Resolve relative claim periods from dated, eligible SEC evidence, never the clock."""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from .edgar import EdgarClient
from .issuer import identify_issuer

RELATIVE = re.compile(r"\b(?:(?:last|latest|most recent)\s+(?:fiscal\s+|calendar\s+)?quarter|this\s+(?:fiscal\s+|calendar\s+)?year|(?:first|second|third|fourth)[ -]quarter|Q[1-4])\b", re.I)


def dated_client(edgar: EdgarClient, published_at: str) -> EdgarClient:
    cutoff = date.fromisoformat(published_at[:10]).isoformat()
    if edgar.policy.as_of:
        cutoff = min(cutoff, edgar.policy.as_of)
    client = EdgarClient(edgar.cache_dir, fetcher=edgar.fetcher, user_agent=edgar.user_agent,
                         timeout=edgar.timeout, as_of=cutoff)
    client._document_cache = edgar._document_cache
    return client


def resolve_relative_period(claim: str, edgar: EdgarClient, published_at: str | None,
                            release_client: Any = None) -> tuple[str, dict | None]:
    phrase = RELATIVE.search(claim)
    if not phrase or (re.search(r"\b20\d{2}\b", claim) and not re.search(r"\bthis\s+(?:fiscal\s+|calendar\s+)?year\b", claim, re.I)):
        return claim, None
    record: dict = {"original_claim": claim, "published_at": published_at, "phrase": phrase[0]}
    def fail(reason):
        return claim, {**record, "error": "insufficient_evidence", "reason": reason}
    if not published_at:
        return fail("missing_period: relative period requires item publication date")
    try:
        source_date = date.fromisoformat(published_at[:10])
        eligible = dated_client(edgar, published_at)
        company = identify_issuer(eligible, claim)
        if company.get("error"):
            return fail(company["error"] + ": " + company["reason"])
        ticker = company["ticker"]
        record.update(ticker=ticker, cik=company["cik"], cutoff=eligible.policy.as_of)
        # Use complete statement periods, not whichever value happens to match
        # the claim. Revenue is the period index, not the asserted metric.
        labels = eligible.list_periods(ticker, "revenue")
        candidates = []
        for label in labels if isinstance(labels, list) else []:
            fact = eligible.lookup_fact(ticker, "revenue", label)
            if fact.get("error") or fact.get("period_type") not in {"quarter", "annual"}:
                continue
            filed = fact.get("filed") or fact.get("provenance", {}).get("latest_filed")
            if not filed or filed > eligible.policy.as_of:
                continue
            candidates.append({"period": label, "end": fact["end"], "filed": filed,
                               "period_type": fact["period_type"], "source_sha256": fact.get("source_sha256"),
                               "filing_url": fact.get("filing_url")})
        # A just-furnished quarterly report may precede companyfacts. Its
        # stated reporting quarter and SEC filing date are also period evidence.
        if release_client is not None:
            from .release import _scope
            from .release_text import parse_html
            for filing in release_client.filings(company["cik"], f"FY{source_date.year}")[:32]:
                if not eligible.policy.admits(filing.get("filingDate")):
                    continue
                for exhibit in release_client.exhibits(company["cik"], filing):
                    label, end = _scope(parse_html(exhibit["raw"]))
                    if label and end and "Q" in label:
                        candidates.append({"period": label, "end": end, "filed": exhibit["filed"],
                                           "period_type": "quarter", "source_sha256": exhibit["sha256"],
                                           "filing_url": exhibit["exhibit_url"]})
        annual = "year" in phrase[0].lower()
        wanted = "annual" if annual else "quarter"
        candidates = [c for c in candidates if c["period_type"] == wanted and c["end"] <= source_date.isoformat()]
        record["candidates"] = candidates
        if annual:
            # 'This year' must not silently become last year's annual report.
            target_year = source_date.year
            if eligible.fiscal_equals_calendar(ticker) is not True:
                if not re.search(r"fiscal|calendar", phrase[0], re.I):
                    return fail("multiple plausible fiscal/calendar meanings for this year; an explicit basis and completed filed period are required")
                if "fiscal" in phrase[0].lower():
                    from .fiscal import fiscal_label, fiscal_year_ends
                    doc, _ = eligible._facts_document(company["cik"])
                    label = fiscal_label(source_date, fiscal_year_ends(doc))
                    if label is None:
                        return fail("issuer fiscal calendar unavailable for this fiscal year")
                    target_year = label[0]
            candidates = [c for c in candidates if c["period"].removeprefix("FY") == str(target_year)]
        ordinal = re.search(r"first|second|third|fourth|Q[1-4]", phrase[0], re.I)
        if ordinal:
            q = ordinal[0][-1] if ordinal[0].upper().startswith("Q") else str(["first", "second", "third", "fourth"].index(ordinal[0].lower()) + 1)
            candidates = [c for c in candidates if c["period"].endswith("Q" + q)]
            if not re.search(r"fiscal|calendar", claim, re.I) and eligible.fiscal_equals_calendar(ticker) is not True:
                latest_by_basis = {}
                for c in candidates:
                    basis = c["period"].startswith("FY")
                    if c["end"] > latest_by_basis.get(basis, {}).get("end", ""):
                        latest_by_basis[basis] = c
                if len({c["end"] for c in latest_by_basis.values()}) > 1:
                    return fail("multiple plausible periods: fiscal and calendar quarter differ; explicit basis required")
        if re.search(r"\bcalendar\b", claim, re.I):
            if eligible.fiscal_equals_calendar(ticker) is True:
                pass
            else:
                candidates = [c for c in candidates if not c["period"].startswith("FY")]
        elif re.search(r"\bfiscal\b", claim, re.I):
            candidates = [c for c in candidates if c["period"].startswith("FY")]
        if not candidates:
            return fail("no eligible filed period for relative phrase; this-year YTD, monthly and forecast periods cannot be substituted with a prior annual period")
        newest = max(c["end"] for c in candidates)
        choices = [c for c in candidates if c["end"] == newest]
        # Equivalent calendar/fiscal labels for the same dates are one period.
        chosen = sorted(choices, key=lambda c: (not c["period"].startswith("FY"), c["filed"]))[0]
        label = chosen["period"]
        if re.search(r"\bcalendar\b", claim, re.I) and eligible.fiscal_equals_calendar(ticker) is True:
            label = label.removeprefix("FY")
        label_text = ("fiscal " if label.startswith("FY") else "calendar ") + (f"Q{label[-1]} {label.removeprefix('FY')[:4]}" if "Q" in label else f"year {label.removeprefix('FY')}")
        resolved = claim[:phrase.start()] + label_text + claim[phrase.end():]
        note = f"period resolved from post date {source_date} → {label}, filed {chosen['filed']}"
        return resolved, {**record, **chosen, "period": label, "resolved_claim": resolved, "reason": note}
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        return fail(f"dated period resolution unavailable: {type(exc).__name__}: {exc}")
