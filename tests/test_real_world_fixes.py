"""Offline regressions on seen real-world inputs and explicit synthetic edge cases."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_sub_claim, evaluate_verdict
from claimcheck.dated_period import resolve_relative_period
from claimcheck.edgar import EdgarClient
from claimcheck.financial import margin, segment_fact
from claimcheck.issuer import bind_issuer
from claimcheck.numbers import parse_stated_number
from claimcheck.release import extract_candidates
from claimcheck.release_fetch import ReleaseClient, _rows
from claimcheck.release_text import parse_html
from claimcheck.tools import ToolRunner

ROOT = Path(__file__).resolve().parents[1]
RECORDED = ROOT / "docs/evidence/real-world-2026-11-02"


def client(tmp_path, *, ticker="META", cik="0001326801", name="Meta Platforms Inc", rows=None, extra=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "company_tickers.json").write_text(json.dumps({"0": {"ticker": ticker, "cik_str": int(cik), "title": name}}))
    if rows is None:
        rows = [
            dict(start="2025-01-01", end="2025-12-31", filed="2026-02-01", form="10-K", fy=2025, fp="FY", val=400),
            dict(start="2026-04-01", end="2026-06-30", filed="2026-07-25", form="10-Q", fy=2026, fp="Q2", val=100),
            dict(start="2026-07-01", end="2026-09-30", filed="2026-10-24", form="10-Q", fy=2026, fp="Q3", val=120),
            dict(start="2026-07-01", end="2026-09-30", filed="2026-11-10", form="10-Q/A", fy=2026, fp="Q3", val=125)]
    for r in rows:
        r.setdefault("accn", "0001326801-26-000001")
    facts = {"us-gaap": {"Revenues": {"units": {"USD": rows}}}}
    for key, value in (extra or {}).items():
        facts["us-gaap"][key] = {"units": {"USD": value}}
    (tmp_path / f"companyfacts-CIK{cik}.json").write_text(json.dumps({"entityName": name, "facts": facts}))
    def no_network(url):
        raise AssertionError("Unexpected retrieval: " + url)
    return EdgarClient(tmp_path, fetcher=no_network)


@pytest.mark.parametrize("phrase", ["last quarter", "latest quarter", "third quarter", "Q3"])
def test_relative_uses_filing_cutoff_not_clock_or_matching_value(tmp_path, phrase):
    edgar = client(tmp_path)
    claim, evidence = resolve_relative_period(f"Meta revenue was $120 {phrase}.", edgar, "2026-10-29")
    assert "fiscal Q3 2026" in claim
    assert evidence["filed"] == "2026-10-24"
    assert evidence["source_sha256"]
    assert "period resolved from post date 2026-10-29" in evidence["reason"]
    claim, evidence = resolve_relative_period("Meta revenue last quarter was $120.", edgar, "2026-10-20")
    assert evidence["period"] == "FY2026Q2"  # Q3 existed but was not yet filed


def test_relative_needs_date_and_this_year_does_not_become_prior_fy(tmp_path):
    edgar = client(tmp_path)
    assert resolve_relative_period("Meta revenue last quarter was $120.", edgar, None)[1]["error"]
    assert resolve_relative_period("Meta revenue this year was $400.", edgar, "2026-10-29")[1]["error"]
    _, ev = resolve_relative_period("Meta revenue this year was $400.", edgar, "2025-12-30")
    assert ev["error"]


def test_fiscal_calendar_ambiguity_fails_closed(tmp_path):
    rows = [dict(start="2024-10-01", end="2025-09-30", filed="2025-11-01", form="10-K", fy=2025, fp="FY", val=400),
            dict(start="2026-04-01", end="2026-06-30", filed="2026-07-25", form="10-Q", fy=2026, fp="Q3", val=100),
            dict(start="2026-07-01", end="2026-09-30", filed="2026-10-24", form="10-K", fy=2026, fp="Q4", val=120)]
    edgar = client(tmp_path, ticker="AAPL", cik="0000320193", name="Apple Inc", rows=rows)
    _, ev = resolve_relative_period("Apple revenue third quarter was $100.", edgar, "2026-10-29")
    assert ev["error"] and "multiple plausible periods" in ev["reason"]
    _, ev = resolve_relative_period("Apple revenue last fiscal quarter was $120.", edgar, "2026-10-29")
    assert ev["period"] == "FY2026Q4"


def test_recorded_hon_precision_cannot_bind_honeywell_even_via_post_rewrite(tmp_path):
    case = next(json.loads(l) for l in (RECORDED / "claims.jsonl").read_text().splitlines() if json.loads(l)["id"] == "RW046")
    edgar = client(tmp_path, ticker="HON", cik="0000773840", name="Honeywell International Inc")
    runner = ToolRunner(edgar, claim_text=case["claim"])
    for name, args in [("lookup_fact", dict(ticker="HON", metric="revenue", period="FY2026Q3")),
                       ("compute_change", dict(ticker="HON", metric="revenue", period="FY2026Q3", base_period="FY2025Q3")),
                       ("find_earnings_release", dict(ticker="HON", metric="revenue", period="FY2026Q3", claim_kind="reported_in_release"))]:
        assert runner.dispatch(name, args)["error"] == "issuer not in SEC coverage"
    assert bind_issuer(edgar, "HON revenue", "HON")["error"]
    assert bind_issuer(edgar, "Honeywell revenue", "HON")["issuer_bound"]
    assert bind_issuer(edgar, "Honeywell revenue", "HON", country="TW")["error"]


def test_supplied_exchange_country_must_agree_with_sec(tmp_path):
    edgar = client(tmp_path)
    (tmp_path / "company_tickers_exchange.json").write_text(json.dumps({"fields": ["cik", "ticker", "exchange"], "data": [[1326801, "META", "Nasdaq"]]}))
    (tmp_path / "submissions-CIK0001326801.json").write_text(json.dumps({"addresses": {"business": {"stateOrCountry": "CA", "stateOrCountryDescription": "CA"}}}))
    assert bind_issuer(edgar, "Meta revenue", "META", country="US", exchange="Nasdaq")["issuer_bound"]
    assert bind_issuer(edgar, "Meta revenue", "META", country="Canada")["error"]
    assert bind_issuer(edgar, "Meta revenue", "META", exchange="NYSE")["error"]


def test_generic_quote_inherits_only_a_unique_named_source_heading(tmp_path):
    from claimcheck.issuer import quote_issuer_context
    edgar = client(tmp_path)
    assert quote_issuer_context(edgar, "its revenue was $120", "Meta reports results. Its revenue was $120")[1]["cik"] == "0001326801"
    assert quote_issuer_context(edgar, "Hon Precision revenue was $120", "Meta reports results. Hon Precision revenue was $120")[1] is None
    assert quote_issuer_context(edgar, "its revenue was $120", "Hon Precision reports results, followed by Meta.")[1] is None


@pytest.mark.parametrize("metric,concept,value", [("net_margin", "NetIncomeLoss", 24), ("operating_margin", "OperatingIncomeLoss", 36), ("gross_margin", "GrossProfit", 60)])
def test_margins_use_matching_filed_inputs_and_formula(tmp_path, metric, concept, value):
    row = dict(start="2026-07-01", end="2026-09-30", filed="2026-10-24", form="10-Q", fy=2026, fp="Q3", val=value)
    edgar = client(tmp_path, extra={concept: [row]})
    result = margin(edgar, "META", metric, "FY2026Q3")
    # This undated request uses the later amended revenue (125).
    assert result["value"] == value / 125 * 100
    assert len(result["components"]) == 2 and result["formula"].endswith("/ revenue * 100")
    assert all(c["filed"] and c["source_sha256"] for c in result["components"])
    row["end"] = "2026-06-30"
    other = client(tmp_path / "mismatch", extra={concept: [row]})
    assert margin(other, "META", metric, "FY2026Q3")["error"]


def test_yoy_formula_records_both_inputs_and_zero_base(tmp_path):
    rows = [dict(start="2025-07-01", end="2025-09-30", filed="2025-10-24", form="10-Q", fy=2025, fp="Q3", val=100),
            dict(start="2026-07-01", end="2026-09-30", filed="2026-10-24", form="10-Q", fy=2026, fp="Q3", val=120)]
    runner = ToolRunner(client(tmp_path, rows=rows))
    ev = runner.dispatch("compute_change", dict(ticker="META", metric="revenue", period="FY2026Q3", base_period="FY2025Q3"))
    assert ev["pct_change"] == 20 and ev["inputs"] == {"current": 120, "base": 100}
    assert "abs(base)" in ev["formula"] and ev["base_fact"]["source_sha256"]
    rows[0]["val"] = 0
    runner = ToolRunner(client(tmp_path / "zero", rows=rows))
    assert runner.dispatch("compute_change", dict(ticker="META", metric="revenue", period="FY2026Q3", base_period="FY2025Q3"))["error"] == "zero_base_value"


def test_segment_xbrl_never_uses_consolidated_or_other_segment(tmp_path):
    row = dict(start="2026-07-01", end="2026-09-30", filed="2026-10-24", form="10-Q", fy=2026, fp="Q3", val=100,
               dimensions={"srt:StatementBusinessSegmentsAxis": "amzn:AmazonWebServicesMember"})
    edgar = client(tmp_path, ticker="AMZN", cik="0001018724", name="Amazon.com Inc", rows=[row])
    result = segment_fact(edgar, "AMZN", "aws_revenue", "2026Q3")
    assert result["value"] == 100 and result["segment_dimensions"]
    row["dimensions"] = {"srt:StatementBusinessSegmentsAxis": "amzn:NorthAmericaMember"}
    other = client(tmp_path / "other", ticker="AMZN", cik="0001018724", name="Amazon.com Inc", rows=[row])
    assert segment_fact(other, "AMZN", "aws_revenue", "2026Q3")["error"]


def primary_runner(tmp_path, case_id):
    case = next(json.loads(l) for l in (RECORDED / "claims.jsonl").read_text().splitlines() if json.loads(l)["id"] == case_id)
    gold = next(json.loads(l) for l in (RECORDED / "gold.jsonl").read_text().splitlines() if json.loads(l)["id"] == case_id)
    source = gold["source"]
    ticker, cik = source["ticker"], source.get("cik", "0001306965")
    entity = {"UNH": "UnitedHealth Group Inc", "ARCC": "Ares Capital Corp", "SHEL": "Shell plc", "SBUX": "Starbucks Corp"}[ticker]
    edgar = client(tmp_path / "edgar", ticker=ticker, cik=cik, name=entity)
    content = gzip.decompress((RECORDED / "sources" / source["gzip_file"]).read_bytes())
    assert hashlib.sha256(content).hexdigest() == source["sha256"]
    form = source["form"].split()[0]
    accession = source.get("accession", "0001628280-26-068044")
    index = source.get("index_url", source["exhibit_url"].rsplit("/", 1)[0] + "/" + accession + "-index.html")
    ex = source["form"].split()[-1]
    def fetch(url):
        if url.startswith("https://data.sec.gov/submissions/"):
            return {"filings": {"recent": {"form": [form], "filingDate": [source["filed"]], "accessionNumber": [accession], "items": ["2.02"]}}}
        if url == index:
            return f'<table><tr><td>EX-{ex}</td><td><a href="{source["exhibit_url"]}">release</a></td></tr></table>'
        if url == source["exhibit_url"]:
            return content
        raise AssertionError(url)
    releases = ReleaseClient(tmp_path / "release", fetcher=fetch)
    return case, gold, ToolRunner(edgar, release_client=releases, claim_text=case["claim"])


@pytest.mark.parametrize("case_id,metric,kind", [("RW006", "adjusted_eps", "guidance"), ("RW026", "investment_income", "reported_in_release"),
                                              ("RW050", "net_income", "reported_in_release"), ("RW052", "us_comparable_sales_growth", "reported_in_release")])
def test_four_recorded_sec_positives_without_relaxing_evidence(tmp_path, case_id, metric, kind):
    case, gold, runner = primary_runner(tmp_path, case_id)
    period = gold["period"]
    found = runner.dispatch("find_earnings_release", dict(ticker=gold["source"]["ticker"], metric=metric, period=period, claim_kind=kind))
    assert len(found.get("candidates", [])) == 1, found
    c = found["candidates"][0]
    ev = runner.dispatch("quote_release", dict(candidate_id=c["candidate_id"], start=c["start"], end=c["end"]))
    sub = dict(text=case["claim"], original_claim=case["claim"], stated_text=case["claim"], claim_type=kind, evidence_ids=[ev["evidence_id"]])
    result = evaluate_sub_claim(sub, runner)
    assert result["program_verdict"] == "supported", result
    assert result["release_evidence"]["span_verified"] and result["release_evidence"]["provenance"]["tier"] == "L4"
    # A tampered amount/metric/period cannot reuse the correct release quote.
    bad = {**sub, "original_claim": case["claim"].replace("2026", "2024"), "text": case["claim"].replace("2026", "2024"), "stated_text": case["claim"].replace("2026", "2024")}
    assert evaluate_sub_claim(bad, runner)["program_verdict"] == "insufficient_evidence"


def test_6k_discovery_and_us_scope_controls():
    rows = _rows({"form": ["6-K", "8-K", "8-K"], "items": ["", "2.02", "5.07"]})
    assert [r["form"] for r in rows] == ["6-K", "8-K"]
    doc = parse_html('<h2>Q4 Fiscal Year 2026 Highlights</h2><p>Global comparable coffeehouse sales increased 7.2%; North America comparable coffeehouse sales increased 7.9%.</p>')
    assert not extract_candidates(doc, "us_comparable_sales_growth", "reported_in_release", "FY2026Q4")


def test_segment_release_fallback_retains_table_unit_and_header(tmp_path):
    edgar = client(tmp_path / "edgar", ticker="AMZN", cik="0001018724", name="Amazon.com Inc")
    html = '<h1>Third quarter 2026 results</h1><p>in millions</p><table><tr><th></th><th>Q3 2026</th><th>Q3 2025</th></tr><tr><td>AWS revenue</td><td>30,000</td><td>25,000</td></tr><tr><td>Consolidated revenue</td><td>150,000</td><td>130,000</td></tr></table>'
    base = 'https://www.sec.gov/Archives/edgar/data/1018724/000101872426000001/'
    accession = '0001018724-26-000001'
    def fetch(url):
        if 'submissions' in url:
            return {"form": ["8-K"], "items": ["2.02"], "accessionNumber": [accession], "filingDate": ["2026-10-28"]}
        if url.endswith('-index.html'):
            return '<table><tr><td>EX-99.1</td><td><a href="release.htm">release</a></td></tr></table>'
        if url == base + 'release.htm':
            return html
        raise AssertionError(url)
    runner = ToolRunner(edgar, release_client=ReleaseClient(tmp_path / 'releases', fetcher=fetch), claim_text='Amazon AWS revenue')
    ev = runner.dispatch('lookup_fact', dict(ticker='AMZN', metric='aws_revenue', period='FY2026Q3'))
    assert ev['value'] == 30000e6 and ev['provenance']['tier'] == 'L4'
    assert ev['release_evidence']['span_verified'] and ev['context_spans']
    assert runner.dispatch('lookup_fact', dict(ticker='AMZN', metric='data_center_revenue', period='FY2026Q3')).get('error')


def test_meta_finalization_includes_pending_outputs_at_turn_limit(tmp_path):
    from test_agent import ScriptedClient, FakeResponse, FakeCall, supported_final
    responses = [FakeResponse('pending', output=[FakeCall('lookup_fact', json.dumps(dict(ticker='META', metric='revenue', period='FY2026Q3')), 'call-last')]),
                 FakeResponse('final', output_text=json.dumps(supported_final()))]
    transport = ScriptedClient(responses)
    verify_claim('Meta fiscal Q3 2026 revenue was $120.', transport, client(tmp_path / 'edgar'),
                 Ledger(tmp_path / 'ledger.jsonl', budget_usd=1), 'muse-spark-1.3', max_turns=1)
    assert transport.responses.calls[1]['previous_response_id'] == 'pending'
    outputs = [x for x in transport.responses.calls[1]['input'] if x.get('type') == 'function_call_output']
    assert len(outputs) == 1 and outputs[0]['call_id'] == 'call-last'


def test_margin_cannot_cite_consolidated_revenue_as_a_percentage(tmp_path):
    runner = ToolRunner(client(tmp_path))
    ev = runner.dispatch('lookup_fact', dict(ticker='META', metric='revenue', period='FY2026Q3'))
    check = evaluate_sub_claim(dict(text='Meta fiscal Q3 2026 net margin was 20%', claim_type='value', stated_text='20%', evidence_ids=[ev['evidence_id']]), runner)
    assert check['program_verdict'] == 'insufficient_evidence' and 'components' in check['reason']


def test_recheck_accepts_frozen_threads_and_news_schema_and_shared_cap(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('fixcheck_runner', ROOT / 'scripts/real_world/fixcheck.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, identifier in [('news', 'RW001'), ('threads', 'TH001')]:
        path = tmp_path / (name + '.jsonl')
        path.write_text(json.dumps(dict(id=identifier, claim='Meta revenue last quarter was $120', published_at='2026-10-29T12:00:00Z')) + '\n')
        assert module.cases_from(path)[0]['id'] == identifier
    assert module.CAP == 5 and set(module.MODELS) == {'meta', 'baseten', 'fireworks'}
    from claimcheck.budget import BudgetExceeded
    shared = tmp_path / 'ledger.jsonl'
    # Unknown usage remains reserved and consumes the later set's same cap.
    news = Ledger(shared, budget_usd=5, provider='meta')
    news.reserve({'input': 'news'}, model=module.MODELS['meta'], max_output_tokens=900000, provider='meta')
    threads = Ledger(shared, budget_usd=5, provider='meta')
    with pytest.raises(BudgetExceeded):
        threads.reserve({'input': 'threads'}, model=module.MODELS['meta'], max_output_tokens=900000, provider='meta')


def test_recorded_guidance_revisions_use_latest_eligible_filing_not_old_outlook(tmp_path):
    import tarfile
    with tarfile.open(RECORDED / 'runtime-cache-baseten.tar.gz') as tar:
        tar.extractall(tmp_path, filter='data')
    def missing(url):
        raise AssertionError('outside frozen source cache')
    edgar = EdgarClient(tmp_path, as_of='2026-11-02', fetcher=missing)
    runner = ToolRunner(edgar, release_client=ReleaseClient(tmp_path, fetcher=missing), claim_text='UnitedHealth 2026 adjusted EPS outlook')
    found = runner.dispatch('find_earnings_release', dict(ticker='UNH', metric='adjusted_eps', period='FY2026', claim_kind='guidance'))
    assert {c['filed'] for c in found['candidates']} == {'2026-10-13'}
    assert {c['low'] for c in found['superseded_guidance']} == {19.5, 18.25, 17.75}
    c = found['candidates'][0]
    quote = runner.dispatch('quote_release', dict(candidate_id=c['candidate_id'], start=c['start'], end=c['end']))
    claim = 'UnitedHealth raised its 2026 adjusted EPS outlook to at least $20.50.'
    check = evaluate_sub_claim(dict(text=claim, original_claim=claim, stated_text='at least $20.50', claim_type='guidance', evidence_ids=[quote['evidence_id']]), runner)
    assert check['program_verdict'] == 'supported' and check['comparator'] == 'gte'


def test_segment_growth_cannot_assume_revenue_or_use_consolidated_sales(tmp_path):
    edgar = client(tmp_path, ticker='AMZN', cik='0001018724', name='Amazon.com Inc')
    runner = ToolRunner(edgar, claim_text='AWS grew by 39% last quarter.')
    assert runner.dispatch('lookup_fact', dict(ticker='AMZN', metric='aws_revenue', period='FY2026Q3'))['error'] == 'segment metric unspecified'
    runner = ToolRunner(edgar, claim_text='Amazon AWS revenue was $30 billion in fiscal Q3 2026.')
    assert runner.dispatch('lookup_fact', dict(ticker='AMZN', metric='revenue', period='FY2026Q3'))['error'] == 'segment scope requires segment facts'


@pytest.mark.parametrize("literal,value", [("1.2億", 120e6), ("12000萬", 120e6), ("1.2 billion", 1200e6), ("120 million", 120e6)])
def test_chinese_scales(literal, value):
    assert parse_stated_number(literal).value == value


@pytest.mark.parametrize("stated", ["$1.2 billion", "$12 billion", "$120 billion", "$12 million"])
def test_unit_note_does_not_change_contradiction(tmp_path, stated):
    rows = [dict(start="2026-07-01", end="2026-09-30", filed="2026-10-24", form="10-Q", fy=2026, fp="Q3", val=120e6)]
    runner = ToolRunner(client(tmp_path, rows=rows))
    ev = runner.dispatch("lookup_fact", dict(ticker="META", metric="revenue", period="FY2026Q3"))
    sub = dict(text=f"Meta fiscal Q3 2026 revenue was {stated}", claim_type="value", stated_text=stated, comparator="eq", evidence_ids=[ev["evidence_id"]])
    checks, verdict = evaluate_verdict([sub], runner)
    assert verdict == "contradicted" and "likely unit/translation error" in checks[0]["reason"]
