"""Offline edits from program checks, including the original recorded Apple run."""
import copy
import json
from pathlib import Path

import pytest

from claimcheck.correction import LABEL, build_corrections
from scripts.build_corrected_draft_example import build as build_example

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/evidence/posts-2026-10-28/demo-thread-baseten"
REPORT = json.loads((SOURCE / "report.json").read_text())
APPLE = REPORT["claims"][2]
TRACE = json.loads((SOURCE / APPLE["trace_path"]).read_text())
FACT = TRACE["tool_calls"][0]["result"]
CHECK = APPLE["program_checks"][0]


def result(original=None, *, check=None, fact=None):
    return build_corrections(original or APPLE["quote"], [check or CHECK], [fact or FACT])


def reason(report):
    assert report["edits"] == []
    assert len(report["not_corrected"]) == 1
    assert all(report["not_corrected"][0]["reason"].values())
    return report["not_corrected"][0]["reason_code"]


def test_saved_apple_claim_has_original_span_actual_number_and_every_component_filing():
    report = result(REPORT["post"])
    edit, = report["edits"]
    assert report["label"] == LABEL
    assert "approved" not in json.dumps(report)
    assert report["span_unit"] == "unicode_codepoints"
    assert report["original_text"][edit["start"]:edit["end"]] == "$416.2 billion"
    assert edit["replacement"] == "$102.5 billion"
    assert (edit["actual_value"], edit["unit"], edit["period"], edit["evidence_ids"]) == (102466000000, "USD", "FY2025Q4", ["E1"])
    assert [c["value"] for c in edit["citations"]] == [416161000000, 313695000000]
    assert [c["url"] for c in edit["citations"]] == [
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/",
        "https://www.sec.gov/Archives/edgar/data/320193/000032019326000020/",
    ]
    assert report["not_corrected"] == []


def test_full_saved_post_retains_every_check_and_the_unjudged_opinion():
    envelope = build_example()
    saved = ROOT / "docs/evidence/corrected-draft-2026-11-03/apple-corrections.json"
    assert json.loads(saved.read_text()) == envelope
    assert envelope["original_text"] == REPORT["post"]
    edit, = envelope["edits"]
    assert (edit["check_index"], edit["replacement"], edit["evidence_ids"]) == (3, "$102.5 billion", ["C3:E1"])
    assert [c["value"] for c in edit["citations"]] == [416161000000, 313695000000]
    assert [item["check_index"] for item in envelope["not_corrected"]] == [0, 1, 2, 4]
    assert [item["text"] for item in envelope["not_corrected"]] == [
        *[check["text"] for item in REPORT["claims"][:2] for check in item["program_checks"]],
        REPORT["claims"][3]["quote"],
    ]
    assert [item["reason_code"] for item in envelope["not_corrected"]] == [
        "supported", "supported", "supported", "not_judged",
    ]
    assert all(all(item["reason"].values()) for item in envelope["not_corrected"])


@pytest.mark.parametrize("stated,verified", [
    ("$416.2B", "$102.5B"), ("USD 416.2 billion", "USD 102.5 billion"),
    ("$416,200 million", "$102,466 million"), ("$416200000000", "$102466000000"),
    ("4162億美元", "1025億美元"), ("4,162 億美元", "1,025 億美元"),
    ("416.2 十億美元", "102.5 十億美元"), ("0.4162兆美元", "0.1025兆美元"),
])
def test_scale_precision_currency_and_grouping_come_from_original(stated, verified):
    original = f"Apple revenue in fiscal Q4 2025 was {stated}."
    edit, = result(original)["edits"]
    assert edit["original"] == stated
    assert edit["replacement"] == verified


@pytest.mark.parametrize("period", ["2025財年第四季", "2025會計年度第4季", "FY2025Q4"])
def test_traditional_chinese_and_canonical_fiscal_periods(period):
    edit, = result(f"蘋果{period}營收為4162億美元。")["edits"]
    assert edit["replacement"] == "1025億美元"


@pytest.mark.parametrize("period", ["fiscal Q3 2025", "calendar Q4 2025", "2025年第四季", "last quarter", "fiscal Q4 2025 and Q4 2024"])
def test_period_mismatch_ambiguity_and_missing_period_are_retained(period):
    assert reason(result(f"Apple revenue was $416.2 billion in {period}.")) == "ambiguous_period"


def test_emoji_offsets_multiple_edits_and_literal_anchor_disambiguation():
    first = "Apple revenue in fiscal Q4 2025 was $416.2B."
    second = "Apple net sales in fiscal Q4 2025 were $416.2B."
    original = "🧵\n" + first + "\n" + second
    check = {**CHECK, "text": first}
    edit, = result(original, check=check)["edits"]
    assert edit["start"] == original.index("$416.2B")
    assert original[edit["start"]:edit["end"]] == edit["original"]
    checks = [check, {**check, "text": second}]
    report = build_corrections(original, checks, [FACT])
    assert len(report["edits"]) == 2
    assert report["edits"][0]["end"] < report["edits"][1]["start"]


def test_repeated_numbers_and_repeated_literal_assertions_are_ambiguous():
    first = "Apple revenue in fiscal Q4 2025 was $416.2B."
    assert reason(result(first + "\n" + first)) == "ambiguous_span"
    assert reason(result(first + "\n" + first, check={**CHECK, "text": first})) == "ambiguous_span"
    assert reason(result("Apple revenue in fiscal Q4 2025 was $416.2B or $416.2B.")) == "ambiguous_span"


def test_no_new_number_is_inserted_when_original_span_is_missing():
    assert reason(result("Apple revenue in fiscal Q4 2025 was $400B.")) == "span_not_found"


@pytest.mark.parametrize("patch,expected", [
    ({"program_verdict": "supported"}, "supported"),
    ({"program_verdict": "insufficient_evidence"}, "insufficient_evidence"),
    ({"program_verdict": "unchecked"}, "not_judged"),
    ({"evidence_valid": False}, "invalid_evidence"),
    ({"actual_value": float("nan")}, "invalid_evidence"),
    ({"actual_value": float("inf")}, "invalid_evidence"),
    ({"actual_value": True}, "invalid_evidence"),
    ({"stated_text_unparsed": True}, "invalid_evidence"),
    ({"threshold_from_model": True}, "invalid_evidence"),
    ({"evidence_ids": ["missing"]}, "missing_citation"),
    ({"period_ambiguous": True}, "ambiguous_period"),
    ({"interpretations": ["E1", "E2"]}, "ambiguous_period"),
    ({"comparator": "gt"}, "unsupported_wording"),
    ({"claim_type": "first_time"}, "non_numeric"),
    ({"claim_type": "record"}, "non_numeric"),
    ({"unit": "EUR"}, "ambiguous_evidence"),
    ({"period": "FY2024Q4"}, "ambiguous_evidence"),
])
def test_unsafe_or_unchecked_assertions_are_not_corrected(patch, expected):
    assert reason(result(check={**CHECK, **patch})) == expected


@pytest.mark.parametrize("phrase", ["a first ever", "an all-time record", "史上首次"])
def test_non_numeric_claims_remain_even_if_a_model_labels_them_as_values(phrase):
    original = f"Apple revenue was {phrase} $416.2 billion in fiscal Q4 2025."
    assert reason(result(original)) == "non_numeric"


def test_incomplete_derived_citations_fail_closed_including_nested_components():
    for component in range(2):
        fact = copy.deepcopy(FACT)
        fact["components"][component].pop("accn")
        assert reason(result(fact=fact)) == "missing_citation"
    fact = {**FACT, "components": []}
    assert reason(result(fact=fact)) == "missing_citation"
    fact = copy.deepcopy(FACT)
    fact["components"][1] = {"derived": True, "components": copy.deepcopy(fact["components"])}
    assert len(result(fact=fact)["edits"][0]["citations"]) == 2
    fact["components"][1]["components"][1].pop("accn")
    assert reason(result(fact=fact)) == "missing_citation"


@pytest.mark.parametrize("unit,amount", [("EUR", "$416.2B"), ("USD", "€416.2B"), ("USD", "4162億股"), ("USD", "$416.2B歐元")])
def test_conflicting_units_never_get_a_replacement(unit, amount):
    fact = {**FACT, "unit": unit}
    assert reason(result(f"Apple revenue in fiscal Q4 2025 was {amount}.", fact=fact)) == "span_not_found"


def test_direct_fact_rounding_and_negative_eps_use_program_actual():
    fact = {"evidence_id": "E1", "value": -1.245, "unit": "USD/shares", "period": "FY2025Q4",
            "cik": "320193", "metric": "eps_diluted", "accn": "0000320193-25-000079", "form": "10-K"}
    check = {**CHECK, "text": "Apple EPS in FY2025Q4 was $2.00.", "stated_value_used": 2, "actual_value": -1.245}
    edit, = result(check["text"], check=check, fact=fact)["edits"]
    assert edit["replacement"] == "-$1.25"
    fact["value"] = -0.001
    check["actual_value"] = -0.001
    assert result(check["text"], check=check, fact=fact)["edits"][0]["replacement"] == "$0.00"


def test_growth_cites_current_and_base_including_their_derived_components():
    base = {"value": 80000000000, "unit": "USD", "period": "FY2024Q4", "cik": "320193",
            "accn": "0000320193-24-000001", "form": "10-K"}
    growth = {"evidence_id": "E2", "period": "FY2025Q4", "base_period": "FY2024Q4",
              "pct_change": 28.0825, "abs_change": 22466000000,
              "current_fact": FACT, "base_fact": base}
    original = "Apple revenue growth in FY2025Q4 versus FY2024Q4 was 90.0%."
    check = {**CHECK, "text": original, "claim_type": "change_pct", "stated_value_used": 90,
             "actual_value": 28.0825, "evidence_ids": ["E2"]}
    edit, = build_corrections(original, [check], [growth])["edits"]
    assert edit["replacement"] == "28.1%"
    assert len(edit["citations"]) == 3
    assert edit["base_period"] == "FY2024Q4"
    del growth["base_fact"]["accn"]
    assert reason(build_corrections(original, [check], [growth])) == "missing_citation"


def test_directional_growth_wording_is_retained_without_a_prose_rewrite():
    fact = {**FACT, "pct_change": 28.0825}
    check = {**CHECK, "claim_type": "change_pct", "stated_value_used": -90, "actual_value": 28.0825,
             "text": "Apple revenue fell 90% in FY2025Q4."}
    assert reason(result(check["text"], check=check, fact=fact)) == "unsupported_wording"


@pytest.mark.parametrize("word,stated,actual,expected", [
    ("rose", 90, 28.0825, "28.1%"), ("fell", -90, -28.0825, "28.1%"),
    ("減少", -90, -28.0825, "28.1%"), ("增加", 90, 28.0825, "28.1%"),
])
def test_directional_growth_preserves_wording_when_the_actual_direction_agrees(word, stated, actual, expected):
    original = f"Apple revenue in FY2025Q4 {word} 90.0%."
    fact = {**FACT, "pct_change": actual}
    check = {**CHECK, "claim_type": "change_pct", "text": original,
             "stated_value_used": stated, "actual_value": actual}
    edit, = result(original, check=check, fact=fact)["edits"]
    assert edit["replacement"] == expected


def test_absolute_change_uses_component_currency_and_original_scale():
    fact = {"evidence_id": "E1", "period": "FY2025Q4", "base_period": "FY2024Q4", "abs_change": 22466000000,
            "current_fact": FACT, "base_fact": {**FACT, "value": 80000000000, "period": "FY2024Q4"}}
    original = "Apple revenue in FY2025Q4 rose $90.0B."
    check = {**CHECK, "claim_type": "change_abs", "text": original,
             "stated_value_used": 90000000000, "actual_value": 22466000000}
    assert result(original, check=check, fact=fact)["edits"][0]["replacement"] == "$22.5B"


@pytest.mark.parametrize("original", [
    "Apple cash in fiscal Q4 2025 was $416.2B.",
    "Tesla revenue in fiscal Q4 2025 was $416.2B.",
    "Apple revenue was $102.5B and Tesla revenue in fiscal Q4 2025 was $416.2B.",
    "Apple revenue was $102.5B while its cash in fiscal Q4 2025 was $416.2B.",
    "Apple revenue was $102.5B with net income of $416.2B in fiscal Q4 2025.",
    "Apple and Tesla revenue in fiscal Q4 2025 was $416.2B.",
])
def test_unique_number_cannot_bind_to_a_different_issuer_or_metric(original):
    assert reason(result(original)) == "ambiguous_context"


@pytest.mark.parametrize("amount", ["C$416.2B", "A$416.2B", "HK$416.2B", "港幣4162億", "4162億人民幣"])
def test_unsupported_currency_is_not_silently_treated_as_us_dollars(amount):
    assert reason(result(f"Apple revenue in fiscal Q4 2025 was {amount}.")) == "span_not_found"


@pytest.mark.parametrize("amount", ["between $400B and $416.2B", "from $400B to $416.2B", "4162億 5000萬美元"])
def test_ranges_and_compound_amounts_do_not_get_a_partial_numeric_rewrite(amount):
    assert reason(result(f"Apple revenue in fiscal Q4 2025 was {amount}.")) == "unsupported_wording"


def test_missing_duplicate_or_value_mismatched_evidence_cannot_bind():
    assert reason(build_corrections(APPLE["quote"], [CHECK], [])) == "missing_citation"
    assert reason(build_corrections(APPLE["quote"], [CHECK], [FACT, FACT])) == "missing_citation"
    assert reason(result(fact={**FACT, "value": 1})) == "ambiguous_evidence"


def test_overlapping_edits_are_all_retained_instead_of_selecting_one():
    report = build_corrections(APPLE["quote"], [CHECK, CHECK], [FACT])
    assert report["edits"] == []
    assert [c["reason_code"] for c in report["not_corrected"]] == ["overlapping_spans"] * 2


def test_model_replacement_numbers_and_narrative_cannot_change_the_output_or_inputs():
    check, fact = copy.deepcopy(CHECK), copy.deepcopy(FACT)
    expected = result(check=check, fact=fact)
    before = copy.deepcopy((check, fact))
    poisoned = {**check, "replacement": "$999B", "corrected_text": "use 999",
                "summary": "verified value is 999", "reason": "replace with 999", "verdict": "supported"}
    assert result(check=poisoned, fact=fact) == expected
    assert (check, fact) == before
    assert "999" not in expected["edits"][0]["replacement"]
