"""Frozen public-session rechecks; no new model, SEC, OCR or ASR execution."""
import asyncio
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_verdict
from claimcheck.edgar import EdgarClient
from claimcheck.tools import ToolRunner
from claimcheck.trace import TraceRecorder
from test_live_check import APPLE, FIXTURES, TRACE, Gate, LiveRun, finish


FIXTURE = Path(__file__).parent / "fixtures/live-determinism/session-20261104T021100641318Z.json"
FIXTURE_SHA256 = "a4deb207015512ae3d4e9020636b2ae626e8ff24bfd29121bfa47bd1e864ad3e"


def no_network(*_):
    pytest.fail("replay must use only frozen evidence")


def session_replay():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256
    recorded = json.loads(raw)["result"]
    runner = ToolRunner(EdgarClient(cache_dir=FIXTURES, fetcher=no_network))
    runner.evidence = {fact["evidence_id"]: copy.deepcopy(fact) for fact in recorded["evidence"]}
    call = None
    for event in recorded["events"]:
        if event["kind"] == "tool_call":
            call = event
        elif event["kind"] == "tool_result":
            assert call["name"] == event["name"]
            runner.calls.append({"name": call["name"], "arguments": copy.deepcopy(call["arguments"]),
                                 "result": copy.deepcopy(event["result"])})
            runner.evidence_kind[event["result"]["evidence_id"]] = event["name"]
    # The public envelope retains checks, not the model's raw final JSON. Reuse
    # its proposals and the verbatim stated literals to restore numeric precision.
    literals = ["$143.1 billion", "$60.9 billion", "more than double", "$416.2 billion", ""]
    subs = [{"text": check["text"], "claim_type": check["claim_type"],
             "stated_value": check["stated_value"], "comparator": check["comparator"],
             "evidence_ids": list(check["evidence_ids"]), "interpretations": [],
             "stated_text": literal, "verdict": "supported", "model_found_value": None,
             "note": "Reconstructed proposal from the retained public check."}
            for check, literal in zip(recorded["claims"], literals)]
    final = {"verdict": recorded["model_verdict"], "summary": recorded["summary"], "sub_claims": subs}
    return recorded, runner, final


@pytest.mark.parametrize("binding", ["recorded_ambiguous", "missing", "claim_fields"])
def test_recorded_session_rebinds_apple_quarter_and_corrects_the_draft(binding):
    recorded, runner, final = session_replay()
    before = copy.deepcopy(recorded)
    apple = recorded["claims"][3]
    assert (recorded["verdict"], apple["program_verdict"], apple["actual_value"]) == (
        "insufficient_evidence", "unchecked", None)
    assert apple["evidence_ids"] == ["E6", "E7"]
    if binding != "recorded_ambiguous":
        final["sub_claims"][3]["evidence_ids"] = []
    if binding == "claim_fields":
        final["sub_claims"][3].update(ticker="AAPL", metric="revenue", period="FY2025Q4")
        runner.calls = []  # Complete report/fact identities need no fallback.
    result = finish(recorded["corrections"]["original_text"], final, runner)
    assert result["verdict"] == "contradicted"
    apple = result["claims"][3]
    assert apple["program_verdict"] == "contradicted"
    assert apple["actual_value"] == 102466000000
    assert apple["evidence_ids"] == ["E6"]
    assert apple["evidence_binding"]["source"] == (
        "claim_fields" if binding == "claim_fields" else "tool_call_arguments")
    assert apple["evidence_binding"]["match"] == {
        "ticker": "AAPL", "metric": "revenue", "period": "FY2025Q4"}
    edit, = result["corrections"]["edits"]
    assert (edit["original"], edit["replacement"]) == ("$416.2 billion", "$102.5 billion")
    assert edit["evidence_ids"] == ["E6"]
    assert all(check["program_verdict"] == "supported" for check in result["claims"][:3])
    assert result["claims"][4]["program_verdict"] == "unchecked"
    assert "evidence_binding" not in result["claims"][4]
    assert recorded == before  # The historical failure is never rewritten.


@pytest.mark.parametrize("candidate_count", [0, 2])
def test_no_unique_fact_stays_unchecked_with_ambiguous_evidence(candidate_count):
    recorded, runner, final = session_replay()
    sub = final["sub_claims"][3]
    sub["evidence_ids"] = []
    if candidate_count == 0:
        runner.evidence.pop("E6")  # The annual fact must not rescue the quarter.
    else:
        runner.evidence["E9"] = {**runner.evidence["E6"], "evidence_id": "E9", "value": 103000000000}
        runner.calls.append({"name": "lookup_fact",
                             "arguments": {"ticker": "AAPL", "metric": "revenue", "period": "FY2025Q4"},
                             "result": runner.evidence["E9"]})
    result = finish(recorded["corrections"]["original_text"], final, runner)
    apple = result["claims"][3]
    assert result["verdict"] == "insufficient_evidence"
    assert (apple["program_verdict"], apple["actual_value"], apple["reason"]) == (
        "unchecked", None, "ambiguous_evidence")
    assert len(apple["evidence_binding"]["candidate_ids"]) == candidate_count
    assert apple["evidence_binding"]["evidence_ids"] == []
    assert result["corrections"]["edits"] == []


def test_missing_report_fields_use_only_unique_lookup_arguments_for_the_named_ticker():
    _, runner, final = session_replay()
    sub = final["sub_claims"][3]
    sub.update(text="Apple reported $416.2 billion.", evidence_ids=[])
    # With no report metric/period, the two Apple lookups remain ambiguous.
    checks, _ = evaluate_verdict([sub], runner)
    assert checks[0]["reason"] == "ambiguous_evidence"
    runner.evidence.pop("E7")
    checks, verdict = evaluate_verdict([sub], runner)
    assert verdict == "contradicted"
    assert checks[0]["evidence_binding"]["source"] == "tool_call_arguments"
    assert checks[0]["evidence_ids"] == ["E6"]
    runner.calls = []
    checks, _ = evaluate_verdict([sub], runner)
    assert checks[0]["reason"] == "ambiguous_evidence"


@pytest.mark.parametrize("overrides", [
    {"ticker": "MSFT", "metric": "revenue", "period": "FY2025Q4"},
    {"ticker": "AAPL", "metric": "net_income", "period": "FY2025Q4"},
    {"ticker": "AAPL", "metric": "revenue", "period": "2025Q4"},
    {"text": "Apple revenue in Q4 2025 was $416.2 billion."},
    {"text": "Apple revenue in 2025 was $416.2 billion."},
    {"text": "Apple and NVIDIA revenue was $416.2 billion."},
])
def test_binding_never_crosses_issuer_metric_or_period_scope(overrides):
    _, runner, final = session_replay()
    sub = {**final["sub_claims"][3], "evidence_ids": [], **overrides}
    checks, verdict = evaluate_verdict([sub], runner)
    assert verdict == "insufficient_evidence"
    assert checks[0]["program_verdict"] == "unchecked"
    assert checks[0]["reason"] == "ambiguous_evidence"


def test_lookup_arguments_can_restore_missing_fact_metadata_but_cannot_override_it():
    _, runner, final = session_replay()
    sub = {**final["sub_claims"][3], "evidence_ids": [],
           "ticker": "AAPL", "metric": "revenue", "period": "FY2025Q4"}
    for field in ("ticker", "metric", "period"):
        runner.evidence["E6"].pop(field)
    checks, verdict = evaluate_verdict([sub], runner)
    assert verdict == "contradicted" and checks[0]["evidence_ids"] == ["E6"]
    assert checks[0]["evidence_binding"]["source"] == "tool_call_arguments"
    runner.evidence["E6"]["ticker"] = "MSFT"
    checks, verdict = evaluate_verdict([sub], runner)
    assert verdict == "insufficient_evidence" and checks[0]["reason"] == "ambiguous_evidence"


def test_live_replay_records_program_binding_before_the_rechecked_claim():
    recorded, runner, final = session_replay()

    async def run():
        gate = Gate()
        async def model(payload):
            assert payload["temperature"] == 0 and payload["top_p"] == 1
            assert gate.actions[-1] == "reserve"
            return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(final)}}],
                    "usage": {"prompt_tokens": 1000, "completion_tokens": 1000}}
        live = LiveRun(model, no_network, gate)
        live.runner = runner
        result = await live.bounded(recorded["corrections"]["original_text"])
        assert result["verdict"] == "contradicted"
        event, = [e for e in result["events"] if e["kind"] == "program_binding"]
        assert event["role"] == "program" and event["claim_index"] == 3
        assert event["source"] == "tool_call_arguments" and event["evidence_ids"] == ["E6"]
        following = result["events"][result["events"].index(event) + 1]
        assert following["kind"] == "program_check" and following["check"]["actual_value"] == 102466000000
        assert result["corrections"]["edits"][0]["replacement"] == "$102.5 billion"
    asyncio.run(run())


def test_shared_cli_records_the_program_binding_in_its_trace(tmp_path):
    responses = [copy.deepcopy(request["raw_response"]) for request in TRACE["requests"]]
    message = responses[-1]["choices"][0]["message"]
    final = json.loads(message["content"])
    final["sub_claims"][0]["evidence_ids"] = []
    message["content"] = json.dumps(final)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: responses.pop(0))))
    recorder = TraceRecorder(APPLE["claim"], TRACE["model"], provider="baseten")
    result = verify_claim(APPLE["claim"], client, EdgarClient(cache_dir=FIXTURES, fetcher=no_network),
                          Ledger(tmp_path / "ledger", budget_usd=1, provider="baseten"), TRACE["model"],
                          provider="baseten", trace=recorder)
    assert result["verdict"] == "supported"
    event, = recorder.as_dict()["program_events"]
    assert event["kind"] == "program_binding" and event["role"] == "program"
    assert event["source"] == "tool_call_arguments" and event["evidence_ids"] == ["E1"]
