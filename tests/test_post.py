from __future__ import annotations

import json

from claimcheck.post import locate_quote, numbers_preserved, parse_extraction, render_html, screen_claims

POST = (
    "Amazon crushed it: revenue hit $143.1 billion in calendar Q3 2023!\n"
    "Analysts expect $180 billion next year. NVDA is wildly overvalued at 50x sales.\n"
    "台積電第三季營收 7,597 億元。"
)


def test_quote_must_be_exact_span_tolerating_whitespace_only() -> None:
    assert locate_quote(POST, "revenue hit $143.1 billion in calendar Q3 2023") is not None
    assert locate_quote(POST, "revenue  hit $143.1\nbillion in calendar Q3 2023") is not None
    assert locate_quote(POST, "revenue reached $143.1 billion in calendar Q3 2023") is None


def test_numbers_preserved_allows_unit_rescaling_but_not_new_numbers() -> None:
    assert numbers_preserved("TSMC third-quarter revenue was NT$759.7 billion.", "台積電第三季營收 7,597 億元")[0]
    ok, missing = numbers_preserved("Amazon revenue was $143.1 billion in Q3 2023.", "revenue hit $143.1 billion last quarter")
    assert not ok and missing == ["3", "2023"]
    assert not numbers_preserved("Amazon revenue was $144.1 billion.", "revenue hit $143.1 billion")[0]


def test_screen_routes_facts_forecasts_opinions_and_rejects_inventions() -> None:
    proposed = [
        {"quote": "revenue hit $143.1 billion in calendar Q3 2023", "claim": "Amazon revenue was $143.1 billion in calendar Q3 2023.", "ticker": "AMZN", "kind": "reported_fact"},
        {"quote": "Analysts expect $180 billion next year.", "claim": "Analysts expect Amazon revenue of $180 billion next year.", "ticker": "AMZN", "kind": "forecast"},
        {"quote": "NVDA is wildly overvalued at 50x sales.", "claim": "NVIDIA trades at 50x sales.", "ticker": "NVDA", "kind": "opinion"},
        {"quote": "revenue hit $143.1 billion last quarter", "claim": "Amazon revenue was $143.1 billion in Q3 2023.", "ticker": "AMZN", "kind": "reported_fact"},
        {"quote": "revenue hit $143.1 billion in calendar Q3 2023", "claim": "Amazon revenue was $150 billion in calendar Q3 2023.", "ticker": "AMZN", "kind": "reported_fact"},
        {"quote": "revenue hit $143.1 billion in calendar Q3 2023", "claim": "amazon revenue was $143.1 billion in calendar Q3 2023.", "ticker": "AMZN", "kind": "reported_fact"},
    ]
    screened = screen_claims(POST, proposed)
    assert [item["status"] for item in screened] == ["to_verify", "not_checked", "not_checked", "rejected", "rejected"]
    assert screened[0]["span"] == [POST.index("revenue hit"), POST.index("revenue hit") + len(proposed[0]["quote"])]
    assert screened[3]["screen_reason"] == "quote is not an exact span of the post"
    assert "150" in screened[4]["screen_reason"]


def test_parse_extraction_accepts_fenced_json_and_render_marks_spans() -> None:
    raw = "```json\n" + json.dumps({"claims": [{"quote": "revenue hit $143.1 billion in calendar Q3 2023", "claim": "Amazon revenue was $143.1 billion in calendar Q3 2023.", "kind": "reported_fact"}]}) + "\n```"
    claims = screen_claims(POST, parse_extraction(raw))
    claims[0].update(status="verified", verdict="supported", program_checks=[], evidence=[])
    page = render_html({
        "post": POST, "provider": "baseten", "model": "m", "claims": claims, "cost_usd": 0.01, "wall_clock_s": 1.0,
        "counts": {"verified": 1, "not_checked": 0, "rejected": 0},
        "verdicts": {"supported": 1, "contradicted": 0, "insufficient_evidence": 0},
    })
    assert 'class="span s-supported"' in page and 'href="#c1"' in page


def test_period_numbers_may_come_from_the_headline_but_must_exist_in_the_post() -> None:
    post = "Apple Q4 2025 earnings:\nRevenue rose 8% to $102.5B."
    assert numbers_preserved("Apple revenue rose 8% to $102.5B in fiscal Q4 2025.", "Revenue rose 8% to $102.5B.", post)[0]
    ok, missing = numbers_preserved("Apple revenue rose 8% to $102.5B in fiscal Q4 2024.", "Revenue rose 8% to $102.5B.", post)
    assert not ok and missing == ["2024"]


def test_growth_multiplier_words_parse_as_percent_growth() -> None:
    from claimcheck.numbers import infer_comparator, parse_stated_number

    assert infer_comparator("more than double", "NVIDIA revenue was more than double the year before") == "gt"
    assert parse_stated_number("more than double").value == 100.0
    doubled = parse_stated_number("doubled")
    assert doubled.value == 100.0 and doubled.precision == 7.5  # roughly 85-115% growth under approx
    assert infer_comparator("doubled", "Meta net income doubled") == "approx"
    assert parse_stated_number("tripled").value == 200.0
    assert parse_stated_number("up 100%").precision == 0.5


def test_literal_hundred_million_is_rescaled_before_verification() -> None:
    from claimcheck.post import normalize_scale_words

    assert normalize_scale_words("Coca-Cola revenue exceeded 500 hundred million US dollars.") == "Coca-Cola revenue exceeded 50 billion US dollars."
    assert normalize_scale_words("revenue was 2,451 hundred million") == "revenue was 245.1 billion"
    post = "可口可樂 2024 年營收突破 500 億美元。"
    item = {"quote": "可口可樂 2024 年營收突破 500 億美元", "claim": "Coca-Cola's 2024 revenue exceeded 500 hundred million US dollars.", "kind": "reported_fact"}
    assert screen_claims(post, [item])[0]["claim"] == "Coca-Cola's 2024 revenue exceeded 50 billion US dollars."


def test_change_evidence_keeps_both_filed_facts() -> None:
    from claimcheck.post import _evidence_rows

    fact = lambda value, end, accn: {"ticker": "TSLA", "concept": "Revenues", "value": value, "start": end[:4] + "-01-01", "end": end, "form": "10-K", "accn": accn, "provenance": {"tier": "L1"}}
    trace = {"tool_calls": [{"name": "compute_change", "result": {
        "evidence_id": "E3", "pct_change": -2.93,
        "current": fact(94827000000, "2025-12-31", "A-26"), "base": fact(97690000000, "2024-12-31", "A-26"),
    }}]}
    rows = _evidence_rows(trace, {"E3"})
    assert [(row["id"], row["role"], row["value"]) for row in rows] == [("E3", "current", 94827000000), ("E3", "comparison", 97690000000)]
    assert all(row["accn"] == "A-26" and row["tier"] == "L1" for row in rows)
