#!/usr/bin/env python3
"""Build the small data snapshot used by the reader-facing site.

The landing page only needs a few evaluation values and three real post reports.
Keeping the extraction here means the page never has to copy a claim, span,
verdict, filing value, or URL by hand.
Use --offline to reuse matching filing excerpts from the existing site snapshot.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Also support direct invocation from a checkout without an installed package.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from claimcheck.post import with_report_gaps

try:
    from .build_explorer_data import posthoc_snapshot
    from .filing_excerpts import SECFilingFetcher, claim_excerpts, group_excerpt_records
except ImportError:  # Running this file directly from the docs/scripts directory.
    from build_explorer_data import posthoc_snapshot
    from filing_excerpts import SECFilingFetcher, claim_excerpts, group_excerpt_records


EXPLORER_PATH = ROOT / "docs" / "explorer" / "data.json"
SUMMARY_PATH = ROOT / "docs" / "evidence" / "eval-v2-2026-10-27" / "summary.json"
OUTPUT_PATH = ROOT / "docs" / "site" / "data" / "site.json"
BUILD_SUMMARY_PATH = ROOT / "docs" / "site" / "BUILD_SUMMARY.md"
FILING_CACHE_PATH = ROOT / ".cache" / "filings"
STAMP_FILING_FIXTURES = ROOT / "tests/fixtures/sec-filings"

EXAMPLE_REPORTS = {
    "en": ROOT / "docs" / "evidence" / "posts-2026-10-28" / "bigtech-thread-baseten" / "report.json",
    "zh": ROOT / "docs" / "evidence" / "posts-2026-10-28" / "tw-social-post-meta" / "report.json",
}

EXAMPLE_IDS = {
    "en": "bigtech-thread-baseten",
    "zh": "tw-social-post-meta",
}

# Compact, faithful display copy. Identity, verdicts and links are read from the
# reports below, rather than copied into the animation or its translations.
STAMP_SELECTIONS = (
    ("demo-thread-baseten", 1, "Q3 2023 revenue: $143.1B.", "2023 年第 3 季營收 1,431 億美元。"),
    ("demo-thread-baseten", 3, "Fiscal Q4 2025 alone: $416.2B revenue.", "僅 2025 財年第 4 季，營收就達 4,162 億美元。"),
    ("demo-thread-baseten", 4, "At 30x sales, NVDA is still cheap.", "NVDA 股價是營收的 30 倍，仍然便宜。"),
    ("demo-thread-baseten", 2, "FY2024 revenue: $60.9B, more than double.", "2024 財年營收 609 億美元，是前一年的兩倍多。"),
    ("bigtech-thread-baseten", 3, "Full-year 2025 revenue grew 3%.", "2025 全年營收成長 3%。"),
    ("tw-social-post-meta", 1, "FY2024 revenue: $245.1B, up 16%.", None),
    ("bigtech-thread-baseten", 5, "Revenue will cross $500B by 2027.", "到 2027 年，營收將突破 5,000 億美元。"),
    ("bigtech-thread-baseten", 4, "Fiscal 2024 revenue: $391.0B.", "2024 財年營收 3,910 億美元。"),
    ("tw-social-post-meta", 3, "2024 revenue exceeded $50B.", None),
)

# These are explicitly fictional example posts; their checks remain report data.
STAMP_POST_DATES = {
    "demo-thread-baseten": "2025-11-03",
    "bigtech-thread-baseten": "2026-02-03",
    "tw-social-post-meta": "2025-02-24",
    "market-recap-repost": "2025-02-25",
    "banana-news-article": "2023-10-27",
}

STAMP_PERSONAS = {
    "demo-thread-baseten": {
        "id": "retail-owl", "name": {"en": "Ticker Owl", "zh": "Ticker Owl"},
        "byline": {"en": "@tickerowl", "zh": "@tickerowl"}, "followers": 18400,
        "follower_label": {"en": "18.4K followers", "zh": "1.84 萬 追蹤"},
    },
    "bigtech-thread-baseten": {
        "id": "chart-raccoon", "name": {"en": "Chart Coon", "zh": "Chart Coon"},
        "byline": {"en": "@chartcoon", "zh": "@chartcoon"}, "followers": 52100,
        "follower_label": {"en": "52.1K followers", "zh": "5.21 萬 追蹤"},
    },
    "tw-social-post-meta": {
        "id": "lazy-cat", "name": {"en": "US Stocks in 1 Minute", "zh": "美股懶人包"},
        "byline": {"en": "美股懶人包", "zh": "US Stocks in 1 Minute"}, "followers": 43000,
        "follower_label": {"en": "43K followers", "zh": "4.3 萬 追蹤"},
    },
    "market-recap-repost": {
        "id": "repost-bird", "name": {"en": "Market Recap", "zh": "Market Recap"},
        "byline": {"en": "Market Recap", "zh": "Market Recap"}, "followers": 210000,
        "follower_label": {"en": "210K followers", "zh": "21 萬 追蹤"},
    },
    "banana-news-article": {
        "id": "banana-news", "name": {"en": "Banana News Flash", "zh": "香蕉新聞快報"},
        "byline": {"en": "香蕉新聞快報", "zh": "Banana News Flash"}, "followers": 96000,
        "follower_label": {"en": "96K followers", "zh": "9.6 萬 追蹤"},
    },
}

SYSTEM_ORDER = [
    "agent@baseten",
    "agent@fireworks",
    "agent@meta",
    "single_shot@meta",
    "single_shot@baseten",
    "single_shot@fireworks",
]

PROVIDER_ORDER = ("meta", "baseten", "fireworks")

SYSTEM_META = {
    "agent@baseten": {"mode": "agent", "provider": "Baseten", "short": "Agent · Baseten"},
    "agent@fireworks": {"mode": "agent", "provider": "Fireworks", "short": "Agent · Fireworks"},
    "agent@meta": {"mode": "agent", "provider": "Meta API", "short": "Agent · Meta API"},
    "single_shot@meta": {"mode": "single-shot", "provider": "Meta API", "short": "Single-shot · Meta API"},
    "single_shot@baseten": {"mode": "single-shot", "provider": "Baseten", "short": "Single-shot · Baseten"},
    "single_shot@fireworks": {"mode": "single-shot", "provider": "Fireworks", "short": "Single-shot · Fireworks"},
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def display_value(value: Any, unit: str | None) -> str | None:
    """Make a compact display string without changing the stored raw value."""
    if not is_number(value):
        return None
    amount = float(value)
    if unit == "USD":
        sign = "-" if amount < 0 else ""
        absolute = abs(amount)
        if absolute >= 1_000_000_000:
            return f"{sign}${absolute / 1_000_000_000:,.3f}B"
        if absolute >= 1_000_000:
            return f"{sign}${absolute / 1_000_000:,.3f}M"
        return f"{sign}${absolute:,.0f}"
    if unit in {"percent", "%"}:
        return f"{amount:,.3f}%"
    return f"{amount:,.3f}"


def round_points(value: float) -> int:
    return int(round(value * 100))


def system_snapshot(system_id: str, stats: dict[str, Any]) -> dict[str, Any]:
    overall = stats["confidence_intervals"][system_id]["overall"]
    totals = stats["system_totals"][system_id]
    meta = SYSTEM_META[system_id]
    return {
        "id": system_id,
        **meta,
        "n": overall["n"],
        "correct": overall["correct"],
        "accuracy": overall["accuracy"],
        "accuracy_ci": {
            "lower": overall["accuracy_ci"]["lower"],
            "upper": overall["accuracy_ci"]["upper"],
        },
        "false_supported": overall["false_supported"],
        "false_supported_denominator": overall["harmful_gold"],
        "cost_mean": totals["cost_usd"]["mean"],
        "latency_mean_s": totals["latency_ms"]["mean"] / 1000,
    }


def evidence_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "ticker",
        "entity",
        "metric",
        "concept",
        "value",
        "unit",
        "start",
        "end",
        "form",
        "filed",
        "accn",
        "frame",
        "fiscal_year",
        "fiscal_period",
        "period",
        "filing_url",
        "id",
        "role",
        "tier",
    )
    snapshot = {key: item.get(key) for key in fields if key in item}
    if is_number(item.get("value")):
        snapshot["display_value"] = display_value(item["value"], item.get("unit"))
    return snapshot


def program_check_snapshot(check: dict[str, Any]) -> dict[str, Any]:
    """Keep only the check fields the modal needs for its conclusion line."""

    fields = (
        "text",
        "stated_value_used",
        "actual_value",
        "comparator",
        "program_verdict",
        "evidence_ids",
    )
    return {key: check.get(key) for key in fields if key in check}


def first_form(evidence: list[dict[str, Any]]) -> str | None:
    for item in evidence:
        if item.get("form"):
            return item["form"]
    return None


def first_filed(evidence: list[dict[str, Any]]) -> str | None:
    for item in evidence:
        if item.get("filed"):
            return item["filed"]
    return None


def first_url(evidence: list[dict[str, Any]]) -> str | None:
    for item in evidence:
        if item.get("filing_url"):
            return item["filing_url"]
    return None


def stamp_gap_snapshot(claim: dict[str, Any]) -> dict[str, Any]:
    """Use the most severe assessed check, keeping its values and units together."""

    fields = ("severity", "score", "gap", "gap_kind", "direction_wrong", "gap_relation", "filed_value_display", "stated_value_display")
    empty = dict.fromkeys(fields)
    if claim.get("status") != "verified" or claim.get("verdict") not in {"supported", "contradicted"}:
        return empty
    checks = [check for check in claim.get("program_checks") or [] if check.get("gap") is not None]
    if not checks:
        return empty
    severity_order = {name: index for index, name in enumerate(("exact", "minor", "moderate", "major", "severe"))}
    check = max(checks, key=lambda item: (severity_order[item["gap"]["severity"]], -item["gap"]["score"]))
    assessment = check["gap"]
    unit = "percent" if assessment["gap_kind"] == "points" else next(
        (item.get("unit") for item in claim.get("evidence") or [] if item.get("id") in (check.get("evidence_ids") or [])),
        None,
    )
    return {
        **assessment,
        "gap_relation": "shortfall" if check.get("comparator") in {"gt", "gte"} else "off",
        "filed_value_display": display_value(check.get("actual_value"), unit),
        "stated_value_display": display_value(check.get("stated_value_used"), unit),
    }


def stamp_period(period: str | None) -> dict[str, str] | None:
    if not period:
        return None
    match = re.fullmatch(r"(FY)?(\d{4})(?:Q([1-4]))?", period)
    if not match:
        return {"en": period, "zh": period}
    fiscal, year, quarter = match.groups()
    return {
        "en": f"{'Fiscal ' if fiscal else ''}{'Q' + quarter + ' ' if quarter else ''}{year}",
        "zh": f"{year} {'財年' if fiscal else '年'}{'第 ' + quarter + ' 季' if quarter else ''}",
    }


def stamp_source_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    return {key: evidence.get(key) for key in (
        "ticker", "entity", "concept", "value", "unit", "start", "end", "form", "filed", "accn", "filing_url",
    )}


def stamp_excerpt(
    evidence: dict[str, Any], fetcher: SECFilingFetcher,
) -> dict[str, Any]:
    """Re-extract the first-filing row, never reuse a later saved excerpt."""
    source = stamp_source_evidence(evidence)
    record = claim_excerpts({"status": "verified", "evidence": [evidence]}, fetcher)[0]
    passage = record.get("excerpt")
    if not passage:
        raise ValueError(f"Stamp passage missing for {evidence.get('ticker')}: {record.get('reason')}")
    result = {
        "type": passage["type"], "form": evidence["form"], "filed": evidence["filed"],
        "company": evidence["entity"], "section_title": passage.get("section_title"),
        "source_evidence": source, "primary_url": record["primary_url"],
        "inline_url": record.get("inline_url"), "fact": passage["fact"],
    }
    if passage["type"] == "table":
        cells = passage["row"]["cells"]
        labels = [cell["text"] for cell in cells if cell.get("is_row_label")]
        headers = list(dict.fromkeys(
            cell["text"] for row in passage["headers"] for cell in row["cells"]
            if cell.get("covers_fact") and cell.get("text")
        ))
        result.update(row_label=" ".join(labels), period_header=" · ".join(headers), value=passage["fact"]["raw_value"])
    else:
        text = passage["text"]
        if len(text) > 220:
            # Preserve a verbatim, fact-centred fragment rather than inventing a sentence.
            start = max(0, passage["fact_range"]["start"] - 80)
            text = text[start:start + 220]
        result.update(text=text, value=passage["fact"]["raw_value"])
    return result


def stamp_derivation(
    evidence: dict[str, Any], cached_site: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve the Q4 source components from the existing SEC companyfacts cache."""
    for card in cached_site.get("stamp_cards", []):
        excerpt = card.get("excerpt") or {}
        derivation = excerpt.get("derivation") or {}
        if derivation.get("derived_from") == stamp_source_evidence(evidence):
            annual, nine = derivation["full_year"], derivation["nine_months"]
            if annual["value"] - nine["value"] == evidence["value"] and annual["end"] == evidence["end"]:
                # Keep component metadata scoped to the source fact, rather than
                # inheriting the derived quarter's period or fiscal-period tag.
                derivation = {**derivation, "full_year": stamp_source_evidence(annual), "nine_months": stamp_source_evidence(nine)}
                return derivation["full_year"], derivation
    companies = {item["ticker"]: item for item in read_json(ROOT / ".cache/company_tickers.json").values()}
    company = companies[evidence["ticker"]]
    facts = read_json(ROOT / f".cache/companyfacts-CIK{company['cik_str']:010d}.json")
    values = facts["facts"]["us-gaap"][evidence["concept"]]["units"][evidence["unit"]]
    annuals = [item for item in values if item.get("end") == evidence["end"] and item.get("form") == "10-K"
               and (int(item["end"][:4]) - int(item.get("start", item["end"])[:4]) >= 1)]
    for annual in sorted(annuals, key=lambda item: item["filed"]):
        nine_months = [item for item in values if item.get("start") == annual.get("start")
                      and item.get("end", "") < evidence["start"] and item.get("form") == "10-Q"
                      and annual["val"] - item["val"] == evidence["value"]]
        if not nine_months:
            continue
        nine = min(nine_months, key=lambda item: item["filed"])
        def component(item):
            return {**stamp_source_evidence(evidence), "value": item["val"], "start": item["start"], "end": item["end"],
                    "form": item["form"], "filed": item["filed"], "accn": item["accn"],
                    "filing_url": f"https://www.sec.gov/Archives/edgar/data/{company['cik_str']}/{item['accn'].replace('-', '')}/"}
        return component(annual), {"full_year": component(annual), "nine_months": component(nine),
                                  "derived_from": stamp_source_evidence(evidence),
                                  "result": evidence["value"], "label": {"en": "Full year", "zh": "全年"},
                                  "text": {"en": f"Q4 = full year − nine months = ${evidence['value'] / 1e9:.1f}B",
                                           "zh": f"第 4 季 = 全年 − 前九個月 = ${evidence['value'] / 1e9:.1f}B"}}
    raise ValueError(f"No SEC full-year/nine-month components for {evidence['ticker']} {evidence['period']}")


def first_reported_fact(evidence: dict[str, Any], companyfacts: dict[str, Any]) -> dict[str, Any]:
    """First SEC filing of this exact concept, unit and duration (not a later repeat)."""
    concept = evidence["concept"].removeprefix("us-gaap:")
    values = companyfacts.get("facts", {}).get("us-gaap", {}).get(concept, {}).get("units", {}).get(evidence["unit"], [])
    matching = [item for item in values if item.get("start") == evidence.get("start")
                and item.get("end") == evidence.get("end") and item.get("filed")]
    if not matching:
        raise ValueError(f"No SEC first-filing date for {evidence['ticker']} {concept} {evidence.get('start')}–{evidence.get('end')}")
    first = min(matching, key=lambda item: (date.fromisoformat(item["filed"]), item["accn"]))
    cik = int(companyfacts["cik"])
    return {
        "ticker": evidence["ticker"], "cik": cik, "concept": concept, "unit": evidence["unit"],
        "start": evidence.get("start"), "end": evidence["end"],
        "first_filed": first["filed"], "form": first["form"], "accn": first["accn"],
        "first_reported_value": first["val"],
        "companyfacts_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
    }


def stamp_date_basis(
    evidence: list[dict[str, Any]], fetcher: SECFilingFetcher, cached_site: dict[str, Any],
) -> dict[str, Any]:
    """Include growth comparisons and both components of a derived quarter."""
    facts = {}
    for item in evidence:
        components = [item]
        if item.get("derived"):
            _, derivation = stamp_derivation(item, cached_site)
            components = [derivation["full_year"], derivation["nine_months"]]
        for component in components:
            key = tuple(component.get(field) for field in ("ticker", "concept", "unit", "start", "end"))
            if key in facts:
                continue
            source_url = urlparse(component.get("filing_url") or "")
            match = re.match(r"/Archives/edgar/data/(\d+)/", source_url.path)
            if source_url.hostname != "www.sec.gov" or not match:
                raise ValueError(f"No SEC company identity for date validation: {key}")
            cik = int(match[1])
            # Offline builds revalidate dates against committed, hash-checked
            # SEC snapshots rather than depending on the author's ignored cache.
            seed_dir = ROOT / "tests/fixtures/sec-offline" if fetcher.offline else ROOT / ".cache"
            data = fetcher.load_companyfacts(cik, seed_cache=seed_dir / f"companyfacts-CIK{cik:010d}.json")
            fact = first_reported_fact(component, data)
            if fact["first_reported_value"] != component["value"]:
                raise ValueError(f"First-filing value differs from recorded evidence for {component['ticker']}")
            facts[key] = fact
    return {
        "method": "sec-companyfacts-first-filed",
        "not_before": max((fact["first_filed"] for fact in facts.values()), default=None),
        "facts": list(facts.values()),
    }


def validate_stamp_post_date(post_date: str, date_basis: dict[str, Any], *, today: date | None = None) -> None:
    """Fail the build for a future example or one preceding any checked figure."""
    try:
        posted = date.fromisoformat(post_date)
        if posted.isoformat() != post_date:
            raise ValueError("Expected YYYY-MM-DD")
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid example post date: {post_date!r}") from error
    earliest = max((fact["first_filed"] for fact in date_basis["facts"]), default=None)
    if date_basis["not_before"] != earliest:
        raise ValueError("Post date_basis does not match its SEC first-filing dates")
    if earliest and posted < date.fromisoformat(earliest):
        raise ValueError(f"Example post date {post_date} precedes SEC first-filing date {earliest}")
    if posted > (today or date.today()):
        raise ValueError(f"Example post date {post_date} is after today")


def first_filing_source(evidence: dict[str, Any], date_basis: dict[str, Any]) -> dict[str, Any]:
    """Retarget the unchanged fact to the accession that first reported it."""
    fields = ("ticker", "concept", "unit", "start", "end")
    fact = next(fact for fact in date_basis["facts"] if all(fact[key] == evidence[key] for key in fields))
    if fact["first_reported_value"] != evidence["value"]:
        raise ValueError(f"First-filing value differs from recorded evidence for {evidence['ticker']}")
    return {**stamp_source_evidence(evidence), "form": fact["form"], "filed": fact["first_filed"],
            "accn": fact["accn"],
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{fact['cik']}/{fact['accn'].replace('-', '')}/"}


def validate_stamp_filing(card: dict[str, Any]) -> None:
    """The paper's actual filing, stamp and value must agree with its date basis."""
    excerpt = card.get("excerpt")
    if excerpt is None:
        return
    source = excerpt["source_evidence"]
    first = first_filing_source(source, card["date_basis"])
    if any(source[key] != first[key] for key in ("filed", "form", "accn", "filing_url")):
        raise ValueError(f"Stamp excerpt is not the first filing: {card['id']}")
    if (excerpt["filed"], excerpt["form"]) != (source["filed"], source["form"]):
        raise ValueError(f"Displayed filing does not match its excerpt: {card['id']}")
    if date.fromisoformat(excerpt["filed"]) > date.fromisoformat(card["post_date"]):
        raise ValueError(f"Displayed filing date follows post date: {card['id']}")
    if excerpt["fact"]["full_value"] != source["value"]:
        raise ValueError(f"Displayed filing value differs from recorded evidence: {card['id']}")


def stamp_persona(persona_id: str) -> dict[str, Any]:
    persona = STAMP_PERSONAS[persona_id]
    return {**persona, "fictional": True, "avatar": f"img/personas/{persona['id']}-256.webp"}


def stamp_thread_position(post: str, quote: str) -> str | None:
    """Use the saved post's numbered entries, not the number of extracted claims."""
    entries = list(re.finditer(r"(?m)^(\d+)/", post))
    offset = post.find(quote)
    preceding = [entry for entry in entries if entry.start() <= offset]
    return f"{preceding[-1][1]}/{entries[-1][1]}" if preceding else None


def stamp_cards(filing_fetcher: SECFilingFetcher | None = None, cached_site: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Select real claims in a mixed order, including across the loop boundary."""
    reports = {
        report_id: with_report_gaps(read_json(path), path.parent)
        for report_id in dict.fromkeys(selection[0] for selection in STAMP_SELECTIONS)
        for path in [ROOT / "docs/evidence/posts-2026-10-28" / report_id / "report.json"]
    }
    cards = []
    cached_site = cached_site if cached_site is not None else read_json(OUTPUT_PATH)
    fetcher = SECFilingFetcher(FILING_CACHE_PATH, offline=True, fixture_dir=STAMP_FILING_FIXTURES)
    company_names = {item["ticker"]: item["entity"] for report in reports.values() for claim in report["claims"]
                     for item in claim.get("evidence", []) if item.get("entity")}
    for report_id, index, english, chinese in STAMP_SELECTIONS:
        report_path = Path("docs/evidence/posts-2026-10-28") / report_id / "report.json"
        claim = next(item for item in reports[report_id]["claims"] if item["index"] == index)
        evidence = claim.get("evidence") or []
        checkable = claim.get("status") == "verified" and claim.get("verdict") in ("supported", "contradicted")
        forms = list(dict.fromkeys(item["form"] for item in evidence if item.get("form") in ("10-Q", "10-K")))
        date_basis = stamp_date_basis(evidence if checkable else [], fetcher, cached_site)
        excerpt = None
        if checkable:
            source = evidence[0]
            derivation = None
            if source.get("derived"):
                source, derivation = stamp_derivation(source, cached_site)
            source = first_filing_source(source, date_basis)
            excerpt = stamp_excerpt(source, fetcher)
            if derivation:
                excerpt["derivation"] = {**derivation,
                    **{key: first_filing_source(derivation[key], date_basis) for key in ("full_year", "nine_months")}}
        post_date = STAMP_POST_DATES[report_id]
        validate_stamp_post_date(post_date, date_basis)
        company = evidence[0]["entity"] if evidence else company_names[claim["ticker"]]
        period = stamp_period(evidence[0].get("period")) if evidence else (
            {"en": match[0], "zh": match[0] + " 年"} if claim["kind"] == "forecast" and (match := re.search(r"20\d{2}", claim["quote"])) else None
        )
        cards.append({
            "id": f"{report_id}-{index}",
            "check_id": f"{report_id}-{index}",
            "source_report": report_path.as_posix(),
            "claim_index": claim["index"],
            "ticker": claim["ticker"],
            "company": company,
            "persona": stamp_persona(report_id),
            "post_date": post_date,
            "date_basis": date_basis,
            "period": period,
            "quote": claim["quote"],
            "kind": claim["kind"],
            "status": claim["status"],
            "verdict": claim.get("verdict"),
            "summary": claim.get("summary"),
            "text": {"en": english, "zh": chinese if chinese is not None else claim["quote"]},
            "source_kind": "social" if report_id == "tw-social-post-meta" else "thread",
            "input_kind": "text",
            "thread_index": stamp_thread_position(reports[report_id]["post"], claim["quote"]),
            # Illustrative activity belongs to the fictional post, never to a
            # real account or the recorded check. The UI labels it as example.
            "example_activity": {"reply": 12, "repost": 24, "like": 180, "views": 2400},
            "filing_url": excerpt["primary_url"] if excerpt else first_url(evidence),
            "evidence_label": f"SEC {' / '.join(forms) if forms else '10-Q / 10-K'}" if checkable and evidence else None,
            "excerpt": excerpt,
            **stamp_gap_snapshot(claim),
        })
    by_id = {card["id"]: card for card in cards}
    amazon = by_id["demo-thread-baseten-1"]
    coca_cola = by_id["tw-social-post-meta-3"]
    cards.extend([
        {**amazon, "id": "banana-news-article", "same_claim_as": amazon["id"],
         "persona": stamp_persona("banana-news-article"), "source_kind": "article",
         "post_date": STAMP_POST_DATES["banana-news-article"],
         "thread_index": None,
         "article": {"lead": {"en": amazon["quote"], "zh": amazon["text"]["zh"]},
                     "illustrations": ["img/polish/article-revenue.webp", "img/polish/article-ledger.webp"]},
         "text": {"en": "Amazon reports $143.1B in Q3 2023 revenue.", "zh": "亞馬遜 2023 年第 3 季營收達 1,431 億美元。"}},
        {**coca_cola, "id": "market-recap-repost", "same_claim_as": coca_cola["id"],
         "persona": stamp_persona("market-recap-repost"), "source_kind": "repost",
         "post_date": STAMP_POST_DATES["market-recap-repost"], "reposted_from": "美股懶人包"},
    ])
    for card in cards:
        validate_stamp_post_date(card["post_date"], card["date_basis"])
        validate_stamp_filing(card)
    if len(cards) > 11 or any(card["verdict"] == following["verdict"] for card, following in zip(cards, cards[1:] + cards[:1])):
        raise ValueError("Stamp loop must have at most 11 cards and alternate verdicts, including wraparound")
    return cards


def source_snapshot(claim: dict[str, Any]) -> dict[str, Any] | None:
    evidence = claim.get("evidence") or []
    for item in evidence:
        if is_number(item.get("value")):
            return {
                "kind": "direct",
                "value": item.get("value"),
                "unit": item.get("unit"),
                "display_value": display_value(item.get("value"), item.get("unit")),
                "form": item.get("form"),
                "filed": item.get("filed"),
                "filing_url": item.get("filing_url"),
                "period": item.get("period"),
            }

    checks = claim.get("program_checks") or []
    if any(is_number(check.get("actual_value")) for check in checks):
        return {
            "kind": "derived",
            "summary": claim.get("summary"),
            "form": first_form(evidence),
            "filed": first_filed(evidence),
            "filing_url": first_url(evidence),
        }
    return None


def claim_snapshot(
    claim: dict[str, Any], filing_fetcher: SECFilingFetcher | None,
    cached_claim: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = claim.get("evidence") or []
    snapshot = {
        "index": claim.get("index"),
        "quote": claim.get("quote"),
        "span": claim.get("span"),
        "claim": claim.get("claim"),
        "ticker": claim.get("ticker"),
        "kind": claim.get("kind"),
        "status": claim.get("status"),
        "verdict": claim.get("verdict"),
        "summary": claim.get("summary"),
        "program_checks": [
            program_check_snapshot(check) for check in (claim.get("program_checks") or [])
        ],
        "source": source_snapshot(claim),
        "evidence": [evidence_snapshot(item) for item in evidence],
    }
    if filing_fetcher is None:
        if cached_claim is None or "excerpts" not in cached_claim or any(
            cached_claim.get(key) != value for key, value in snapshot.items()
        ):
            raise ValueError(f"--offline requires matching stored filing excerpts for claim {claim.get('index')}")
        excerpts = cached_claim["excerpts"]
    else:
        excerpts = claim_excerpts(claim, filing_fetcher)
    snapshot.update({"excerpts": excerpts, "modal_blocks": group_excerpt_records(evidence, excerpts)})
    return snapshot


def excerpt_summary(claims: list[dict[str, Any]]) -> dict[str, Any]:
    claim_results = []
    matched_components = 0
    unmatched_components = 0
    for claim in claims:
        if claim.get("status") != "verified":
            continue
        excerpts = claim.get("excerpts") or []
        matched = sum(1 for item in excerpts if item.get("excerpt") is not None)
        unmatched = len(excerpts) - matched
        matched_components += matched
        unmatched_components += unmatched
        claim_results.append(
            {
                "index": claim.get("index"),
                "claim": claim.get("claim"),
                "matched": matched,
                "unmatched": unmatched,
                "reasons": [item.get("reason") for item in excerpts if item.get("reason")],
            }
        )
    return {
        "verified_claims": len(claim_results),
        "matched_claims": sum(1 for item in claim_results if item["matched"]),
        "partial_claims": sum(1 for item in claim_results if item["matched"] and item["unmatched"]),
        "unmatched_claims": sum(1 for item in claim_results if not item["matched"]),
        "matched_components": matched_components,
        "unmatched_components": unmatched_components,
        "claims": claim_results,
    }


def example_snapshot(
    example_id: str, report: dict[str, Any], filing_fetcher: SECFilingFetcher | None,
    cached_example: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cached_claims = {claim["index"]: claim for claim in (cached_example or {}).get("claims", [])}
    claims = [claim_snapshot(claim, filing_fetcher, cached_claims.get(claim.get("index"))) for claim in report.get("claims", [])]
    return {
        "id": example_id,
        "post": report.get("post", ""),
        "provider": report.get("provider"),
        "model": report.get("model"),
        "proposed_count": report.get("proposed_count"),
        "counts": report.get("counts", {}),
        "verdicts": report.get("verdicts", {}),
        "claims": claims,
        "filing_excerpt_summary": excerpt_summary(claims),
    }


def write_build_summary(examples: dict[str, dict[str, Any]], cards: list[dict[str, Any]]) -> None:
    lines = [
        "# Site build summary",
        "",
        "- The bilingual site reads both example `report.json` files directly and writes the checked claims, SEC facts, filing excerpts, and original-filing links to `docs/site/data/site.json`.",
        "- SEC downloads use the required User-Agent, are limited to five requests per second, and are cached under `.cache/filings/`.",
        "",
        "## Filing excerpt results",
        "",
    ]
    for language, example in examples.items():
        summary = example["filing_excerpt_summary"]
        lines.append(
            f"### {language}: {example['id']} — {summary['matched_components']} matched, {summary['unmatched_components']} unmatched component facts"
        )
        lines.append("")
        for item in summary["claims"]:
            lines.append(
                f"- Claim {item['index']}: {item['claim']} — {item['matched']} matched, {item['unmatched']} unmatched."
            )
            claim = next(
                (candidate for candidate in example["claims"] if candidate.get("index") == item["index"]),
                None,
            )
            if claim:
                excerpts_by_index = {
                    record.get("evidence_index"): record for record in claim.get("excerpts") or []
                }
                for block in claim.get("modal_blocks") or []:
                    labels = []
                    highlights = []
                    for evidence_index in block.get("evidence_indices") or []:
                        evidence = (claim.get("evidence") or [])[evidence_index]
                        label = evidence.get("id") or "Evidence"
                        if evidence.get("role") == "current":
                            label += " this period"
                        elif evidence.get("role") == "comparison":
                            label += " comparison"
                        labels.append(label)
                        record = excerpts_by_index.get(evidence_index) or {}
                        fact = (record.get("excerpt") or {}).get("fact") or {}
                        highlight = str(fact.get("raw_value") or fact.get("full_value") or "not available")
                        if highlight not in highlights:
                            highlights.append(highlight)
                    lines.append(
                        f"  - Modal block after dedupe: {' · '.join(labels)} — highlighted value: {', '.join(highlights)}."
                    )
            for reason in item["reasons"]:
                lines.append(f"  - Reason: {reason}")
        lines.append("")

    lines.extend([
        "## On-screen filing chronology",
        "",
        "Each checkable card uses the first filing of its unchanged fact. Complete, lossless iXBRL documents are committed under `tests/fixtures/sec-filings/`; offline builds re-extract the rows and validate dates and values. All 11 component facts match their recorded values; no later comparative-column fallback is needed. Saved report/modal provenance is preserved separately.",
        "",
        "| Card | Post date | Displayed filing | First-filed basis (accession) |",
        "| --- | --- | --- | --- |",
    ])
    for card in cards:
        excerpt = card.get("excerpt")
        displayed = f"{excerpt['form']}, {excerpt['filed']}" if excerpt else "No filing — opinion / forecast"
        basis = "; ".join(f"{fact['first_filed']} ({fact['accn']})" for fact in card["date_basis"]["facts"]) or "Not checked"
        lines.append(f"| {card['id']} ({card['ticker']}) | {card['post_date']} | {displayed} | {basis} |")
    lines.append("")

    lines.extend(
        [
            "## Files changed",
            "",
            "- `docs/site/index.html`",
            "- `docs/site/script.js`",
            "- `docs/site/styles.css`",
            "- `docs/site/data/site.json`",
            "- `docs/scripts/build_site.py`",
            "- `docs/scripts/filing_excerpts.py`",
            "- `tests/test_filing_excerpts.py`",
            "- `docs/site/BUILD_SUMMARY.md`",
            "",
        ]
    )
    BUILD_SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def family_snapshot(stats: dict[str, Any], family: str) -> dict[str, Any]:
    selected = {}
    for system_id in ("agent@meta", "agent@baseten", "agent@fireworks"):
        family_stats = stats["confidence_intervals"][system_id]["family"][family]
        selected[system_id] = {
            "correct": family_stats["correct"],
            "n": family_stats["n"],
            "accuracy": family_stats["accuracy"],
        }
    return {"id": family, "systems": selected}


def paired_snapshot(stats: dict[str, Any]) -> dict[str, Any]:
    pairs = {
        "meta": "agent@meta_vs_single_shot@meta",
        "baseten": "agent@baseten_vs_single_shot@baseten",
        "fireworks": "agent@fireworks_vs_single_shot@fireworks",
    }
    paired = {}
    for provider, pair_id in pairs.items():
        comparison = stats["paired_comparisons"][pair_id]
        paired[provider] = {
            "points": round_points(comparison["accuracy_difference"]),
            "mcnemar_exact_p": comparison["mcnemar_exact_p"],
            "n": comparison["n"],
        }
    return paired


def chart_snapshot(systems: dict[str, dict[str, Any]], paired: dict[str, Any]) -> list[dict[str, Any]]:
    chart = []
    for provider in PROVIDER_ORDER:
        without = systems[f"single_shot@{provider}"]
        with_checks = systems[f"agent@{provider}"]
        chart.append(
            {
                "id": provider,
                "provider": with_checks["provider"],
                "without": {
                    "accuracy": without["accuracy"],
                    "percent": round_points(without["accuracy"]),
                },
                "with_checks": {
                    "accuracy": with_checks["accuracy"],
                    "percent": round_points(with_checks["accuracy"]),
                },
                "change_points": paired[provider]["points"],
            }
        )
    return chart


def research_snapshot(systems: dict[str, dict[str, Any]], paired: dict[str, Any], families: list[dict[str, Any]]) -> dict[str, Any]:
    confidence_intervals = {}
    cost_latency = {}
    for provider in PROVIDER_ORDER:
        without = systems[f"single_shot@{provider}"]
        with_checks = systems[f"agent@{provider}"]
        confidence_intervals[provider] = {
            "without": without["accuracy_ci"],
            "with_checks": with_checks["accuracy_ci"],
        }
        cost_latency[provider] = {
            "without": {
                "cost_mean": without["cost_mean"],
                "latency_mean_s": without["latency_mean_s"],
            },
            "with_checks": {
                "cost_mean": with_checks["cost_mean"],
                "latency_mean_s": with_checks["latency_mean_s"],
            },
        }
    return {
        "confidence_intervals": confidence_intervals,
        "paired": paired,
        "cost_latency": cost_latency,
        "families": families,
        "gold_corrections": [
            "Amazon's 12-month 10-Q value was trailing-twelve-month data, not a fiscal year.",
            "Apple's 52/53-week quarter ending 2023-07-01 belongs to calendar Q2, not Q3.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Reuse matching stored filing excerpts without fetching SEC filings")
    args = parser.parse_args()
    explorer = read_json(EXPLORER_PATH)
    stats = explorer["stats"]
    summary = read_json(SUMMARY_PATH) if SUMMARY_PATH.exists() else {}

    systems = {system_id: system_snapshot(system_id, stats) for system_id in SYSTEM_ORDER}
    paired = paired_snapshot(stats)
    families = [
        family_snapshot(stats, "record_first"),
        family_snapshot(stats, "yoy"),
        family_snapshot(stats, "period_trap"),
    ]

    cached_site = read_json(OUTPUT_PATH) if OUTPUT_PATH.exists() else {}
    cached_examples = cached_site.get("examples", {}) if args.offline else {}
    filing_fetcher = None if args.offline else SECFilingFetcher(FILING_CACHE_PATH)
    examples = {
        language: example_snapshot(EXAMPLE_IDS[language], read_json(report_path), filing_fetcher, cached_examples.get(language))
        for language, report_path in EXAMPLE_REPORTS.items()
    }

    cards = stamp_cards(filing_fetcher, cached_site)
    output = {
        "eval": {
            "claim_count": len(explorer["claims"]),
            "result_count": summary.get("result_count", len(explorer["claims"]) * len(SYSTEM_ORDER)),
            "generated_at": summary.get("generated_at", ""),
            "run": explorer.get("run"),
        },
        "systems": list(systems.values()),
        "chart": chart_snapshot(systems, paired),
        "posthoc_rerun": posthoc_snapshot(explorer["claims"], ROOT / explorer["posthoc_rerun"]["run"]),
        "paired": paired,
        "families": families,
        "research": research_snapshot(systems, paired, families),
        "examples": examples,
        "stamp_cards": cards,
        "filing_excerpts": {
            "cache_dir": ".cache/filings",
            "examples": {language: example["filing_excerpt_summary"] for language, example in examples.items()},
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    write_build_summary(examples, cards)


if __name__ == "__main__":
    main()
