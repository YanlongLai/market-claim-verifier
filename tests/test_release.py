from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_sub_claim
from claimcheck.edgar import EdgarClient
from claimcheck.post import _evidence_rows, screen_claims
from claimcheck.release import _scope, extract_candidates, requires_release
from claimcheck.release_fetch import ReleaseClient, ReleaseError
from claimcheck.release_report import render_release_quote
from claimcheck.release_text import parse_html
from claimcheck.tools import ToolRunner

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/releases"
SOURCES = {s["ticker"]: s for s in json.loads((FIXTURES / "manifest.json").read_text())}
CLAIMS = [json.loads(line) for line in (ROOT / "eval/l4/claims.jsonl").read_text().splitlines()]


def offline_client():
    def missing(url):
        raise ReleaseError("not in recorded corpus")
    return ReleaseClient(FIXTURES, fetcher=missing)


class RecordedEdgar:
    cache_dir = FIXTURES
    user_agent = "DappGo market-claim-verifier admin@dappgo.com"
    timeout = 20.0
    filing_value = None
    filing_type = "quarter"
    filing_end = None

    def resolve_ticker(self, ticker):
        source = SOURCES[ticker]
        return {"ticker": ticker, "cik": source["cik"], "entity": {"AAPL": "Apple Inc.", "AMZN": "AMAZON COM INC"}.get(ticker, ticker)}

    def fiscal_equals_calendar(self, ticker):
        return ticker in {"META", "AMD", "INTC", "AMZN"}

    def lookup_fact(self, ticker, metric, period):
        if metric != "revenue" or ticker not in {"AAPL", "AMZN"}:
            return {"error": "fact_not_found"}
        return {"ticker": ticker, "metric": metric, "value": self.filing_value if self.filing_value is not None else {"AAPL": 94036e6, "AMZN": 167702e6}[ticker],
                "unit": "USD", "period_type": self.filing_type,
                "end": self.filing_end or {"AAPL": "2025-06-28", "AMZN": "2025-06-30"}[ticker],
                "provenance": {"tier": "L2", "strength": "medium", "forms": ["10-Q"]}}


def selected(case, edgar=None):
    runner = ToolRunner(edgar or RecordedEdgar(), release_client=offline_client())
    found = runner.dispatch("find_earnings_release", {"ticker": case["ticker"], "metric": case["metric"], "period": case["period"], "claim_kind": case["kind"]})
    candidates = found.get("candidates") or []
    ids = []
    if candidates:
        c = candidates[0]
        quote = runner.dispatch("quote_release", {"candidate_id": c["candidate_id"], "start": c["start"], "end": c["end"]})
        assert not quote.get("error"), quote
        ids = [quote["evidence_id"]]
    sub = {"text": case["claim"], "original_claim": case["claim"], "stated_text": case["claim"],
           "claim_type": case["kind"], "comparator": "eq", "evidence_ids": ids,
           "stated_value": 777, "model_found_value": 777, "verdict": "supported"}
    return runner, found, sub


@pytest.mark.parametrize("case", CLAIMS, ids=lambda c: c["id"])
def test_registered_examples_are_reproducible_without_models(case):
    runner, _, sub = selected(case)
    check = evaluate_sub_claim(sub, runner)
    assert check["program_verdict"] == case["gold_verdict"], check
    if check["program_verdict"] in {"supported", "contradicted"}:
        quote = check["release_evidence"]
        raw, _ = runner.release_service.client.read(quote["exhibit_url"])
        doc = parse_html(raw)
        assert doc.text[quote["start"]:quote["end"]] == quote["quote"]
        assert check["evidence_strength"] == "medium" and not quote["provenance"]["audited"]


def test_span_selection_and_numbers_are_revalidated():
    runner, found, sub = selected(CLAIMS[0])
    c = found["candidates"][0]
    bad = runner.dispatch("quote_release", {"candidate_id": c["candidate_id"], "start": c["start"] + 1, "end": c["end"]})
    assert bad.get("error")
    runner.evidence[sub["evidence_ids"][0]]["low"] = 1
    check = evaluate_sub_claim(sub, runner)
    assert check["actual_range"] == [47.5e9, 50.5e9]
    assert check["program_verdict"] == "supported"
    sub["evidence_ids"] = [found["evidence_id"]]
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "insufficient_evidence"


def test_original_claim_beats_model_rewrite_and_model_numbers():
    runner, _, sub = selected(CLAIMS[1])
    sub.update(text=CLAIMS[0]["claim"], stated_value=47.5e9, model_found_value=47.5e9)
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "contradicted"
    sub["stated_text"] = "invented quote"
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "insufficient_evidence"


@pytest.mark.parametrize("claim", ["AAPL expects revenue of $94.036 billion for FY2025Q3.", "AAPL reported adjusted EPS of $1.57 for FY2025Q3."])
def test_model_cannot_relabel_guidance_or_non_gaap_as_a_gaap_value(claim):
    runner = ToolRunner(RecordedEdgar(), release_client=offline_client())
    fact = runner.dispatch("lookup_fact", {"ticker": "AAPL", "metric": "revenue", "period": "FY2025Q3"})
    sub = {"text": claim, "original_claim": claim, "stated_text": claim, "claim_type": "value", "evidence_ids": [fact["evidence_id"]], "verdict": "supported"}
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "insufficient_evidence"


def test_target_issuer_name_does_not_route_reported_gaap_results_to_guidance():
    claim = "Target reported revenue of $1.0 billion for FY2025Q2."
    assert not requires_release(claim)
    assert requires_release("Target expects revenue of $1.0 billion for FY2025Q3.")
    assert requires_release("AAPL has a revenue target of $1 billion for FY2025Q4.")
    assert _scope(parse_html("<h1>Target Reports First Quarter Fiscal 2025 Results</h1>"))[0] == "FY2025Q1"
    runner = ToolRunner(RecordedEdgar())
    fact = runner._number_result({"value": 1e9, "unit": "USD", "ticker": "TGT", "metric": "revenue", "period": "FY2025Q2"}, "lookup_fact")
    sub = {"text": claim, "original_claim": claim, "stated_text": "$1.0 billion", "claim_type": "value", "comparator": "eq", "evidence_ids": [fact["evidence_id"]], "verdict": "supported"}
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "supported"


@pytest.mark.parametrize("change", ["ticker", "period", "metric", "unit"])
def test_cannot_cite_other_issuer_period_metric_or_units(change):
    runner, _, sub = selected(CLAIMS[0])
    original = sub["original_claim"]
    altered = original.replace({"ticker": "META", "period": "FY2025Q3", "metric": "revenue", "unit": "$47.5 billion to $50.5 billion"}[change],
                               {"ticker": "AAPL", "period": "FY2024Q3", "metric": "operating income", "unit": "47.5% to 50.5%"}[change])
    sub.update(original_claim=altered, text=altered, stated_text=altered)
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "insufficient_evidence"


def test_filing_value_wins_and_mismatch_is_flagged():
    edgar = RecordedEdgar()
    edgar.filing_value = 99.036e9
    runner, _, sub = selected(CLAIMS[4], edgar)
    check = evaluate_sub_claim(sub, runner)
    assert check["program_verdict"] == "contradicted" and check["actual_value"] == 99.036e9
    assert check["flags"] == ["release_vs_filing_mismatch"] and check["authoritative_tier"] == "L2"
    assert check["evidence_ids"][-1].startswith("P")


@pytest.mark.parametrize("case", [CLAIMS[4], CLAIMS[5], CLAIMS[30]], ids=lambda c: c["id"])
def test_real_recorded_xbrl_cross_check(case):
    edgar = EdgarClient(FIXTURES / "xbrl", fetcher=lambda u: pytest.fail("offline"))
    runner, _, sub = selected(case, edgar)
    check = evaluate_sub_claim(sub, runner)
    assert check["program_verdict"] == case["gold_verdict"]
    assert check["filing_cross_check"]["provenance"]["tier"] == "L2"
    assert check["authoritative_tier"] == "L2" and not check["flags"]


def test_segment_and_non_gaap_revenue_claims_cannot_use_consolidated_gaap_totals():
    for qualifier in ("AWS segment", "non-GAAP", "constant currency"):
        runner, _, sub = selected(CLAIMS[30])
        claim = sub["original_claim"].replace("revenue", qualifier + " revenue")
        sub.update(original_claim=claim, stated_text=claim, text=claim)
        assert evaluate_sub_claim(sub, runner)["program_verdict"] == "insufficient_evidence"


def test_point_in_a_guidance_range_is_not_supported_as_the_stated_range():
    runner, _, sub = selected(CLAIMS[0])
    claim = "META expects revenue of $49.0 billion for FY2025Q3."
    sub.update(original_claim=claim, stated_text=claim, text=claim)
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == "insufficient_evidence"


def test_non_usd_claim_cannot_match_a_usd_per_share_amount():
    runner, _, sub = selected(CLAIMS[26])
    claim = sub["original_claim"].replace("$5.31", "€5.31")
    sub.update(original_claim=claim, stated_text=claim, text=claim)
    assert evaluate_sub_claim(sub, runner)["reason"] == "unsupported_release_currency"


@pytest.mark.parametrize("replacement,verdict", [("−$5.31", "contradicted"), ("($5.31", "insufficient_evidence")])
def test_negative_or_malformed_claims_never_reuse_a_positive_value(replacement, verdict):
    runner, _, sub = selected(CLAIMS[26])
    claim = sub["original_claim"].replace("$5.31", replacement)
    sub.update(original_claim=claim, stated_text=claim, text=claim)
    assert evaluate_sub_claim(sub, runner)["program_verdict"] == verdict


@pytest.mark.parametrize("field,value", [("filing_type", "ytd"), ("filing_end", "2025-09-30")])
def test_wrong_filing_period_does_not_override_release(field, value):
    edgar = RecordedEdgar()
    edgar.filing_value = 99.036e9
    setattr(edgar, field, value)
    runner, _, sub = selected(CLAIMS[4], edgar)
    check = evaluate_sub_claim(sub, runner)
    assert check["program_verdict"] == "supported" and not check["flags"]


def test_conflicting_candidates_cannot_be_hidden_by_selecting_one():
    runner, _, sub = selected(CLAIMS[0])
    service = runner.release_service
    service.candidates["conflicting"] = {**next(iter(service.candidates.values())), "low": 1}
    assert evaluate_sub_claim(sub, runner)["reason"] == "ambiguous_or_revised_release_values"


def test_strict_tool_rejects_extra_numbers_urls_and_boolean_offsets():
    runner = ToolRunner(RecordedEdgar(), release_client=offline_client())
    for args in [dict(candidate_id="fake", start=True, end=4), dict(candidate_id="fake", start=0, end=4, value=1), dict(candidate_id="fake", start=0, end=4, url="https://evil.example")]:
        assert runner.dispatch("quote_release", args).get("error")


def test_fiscal_calendar_alias_only_with_xbrl_calendar_proof():
    source = SOURCES["AAPL"]
    raw, _ = offline_client().read(source["exhibit_url"])
    doc = parse_html(raw)
    assert extract_candidates(doc, "revenue", "reported_in_release", "2025Q3", calendar=False) == []
    assert extract_candidates(doc, "revenue", "reported_in_release", "FY2025Q3")


def test_post_routes_only_issuer_guidance_and_retains_release_provenance():
    claim = CLAIMS[0]["claim"]
    screened = screen_claims(claim, [{"quote": claim, "claim": claim, "ticker": "META", "kind": "issuer_guidance"}])
    assert screened[0]["status"] == "to_verify"
    runner, _, sub = selected(CLAIMS[0])
    rows = _evidence_rows({"tool_calls": runner.calls}, set(sub["evidence_ids"]))
    ev = rows[0]
    assert ev["form"] == "8-K Ex 99.1" and ev["tier"] == "L4"
    assert ev["sha256"] and ev["accession"] and ev["filed"] and ev["quote"]
    page = render_release_quote(ev)
    assert "<mark>" in page and "47.5-50.5 billion" in page and "data-start=" in page


def test_insufficient_outlook_keeps_the_inspected_primary_source_in_reports():
    runner, found, sub = selected(CLAIMS[6])
    assert not found["candidates"]
    rows = _evidence_rows({"tool_calls": runner.calls}, {found["evidence_id"]})
    assert rows and rows[0]["role"] == "searched"
    assert rows[0]["filing_url"] == SOURCES["AAPL"]["exhibit_url"]
    assert rows[0]["accession"] == SOURCES["AAPL"]["accession"]


def test_parallel_gaap_non_gaap_points_are_not_treated_as_a_guidance_range():
    doc = parse_html('<h1>Second Quarter Fiscal 2025 Results</h1><h2>Third quarter fiscal 2025 outlook</h2><p>GAAP and non-GAAP diluted earnings per share are expected to be $2.00 and $3.00, respectively.</p>')
    assert extract_candidates(doc, "adjusted_eps", "guidance", "FY2025Q3") == []


def test_gold_builder_is_independent_and_byte_reproducible(tmp_path):
    path = ROOT / "eval/l4/build_gold.py"
    spec = importlib.util.spec_from_file_location("independent_l4_gold", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("annotations.json", "build_gold.py"):
        shutil.copyfile(ROOT / "eval/l4" / name, tmp_path / name)
    module.HERE = tmp_path
    module.build()
    for name in ("claims.jsonl", "gold_facts.json", "MANIFEST.json"):
        assert (tmp_path / name).read_bytes() == (ROOT / "eval/l4" / name).read_bytes()
    assert "from claimcheck" not in path.read_text() and "import claimcheck" not in path.read_text()


def test_agent_uses_find_and_quote_and_program_rejects_model_number(tmp_path):
    case = CLAIMS[0]
    class Responses:
        turn = 0

        def create(self, **kwargs):
            self.turn += 1
            output, text = [], ""
            if self.turn == 1:
                output = [dict(type="function_call", name="find_earnings_release", arguments=json.dumps(dict(ticker="META", metric="revenue", period="FY2025Q3", claim_kind="guidance")), call_id="find")]
            elif self.turn == 2:
                result = json.loads(next(i["output"] for i in kwargs["input"] if i.get("type") == "function_call_output"))
                c = result["candidates"][0]
                output = [dict(type="function_call", name="quote_release", arguments=json.dumps({k: c[k] for k in ("candidate_id", "start", "end")}), call_id="quote")]
            elif self.turn == 4:
                text = json.dumps(dict(verdict="contradicted", summary="Model number is intentionally wrong.", sub_claims=[dict(text=case["claim"], stated_text="$47.5 billion to $50.5 billion", claim_type="guidance", comparator="eq", stated_value=777, evidence_ids=["E2"], interpretations=[], verdict="contradicted", model_found_value=777, note="test")]))
            return SimpleNamespace(id=f"r{self.turn}", output=output, output_text=text, usage=dict(input_tokens=50, output_tokens=50), status="completed")
    response = verify_claim(case["claim"], SimpleNamespace(responses=Responses()), RecordedEdgar(), Ledger(tmp_path / "ledger", budget_usd=1), "muse-spark-1.3", release_client=offline_client())
    assert response["verdict"] == "supported" and response["model_program_disagreement"]
    assert response["program_checks"][0]["actual_range"] == [47.5e9, 50.5e9]
