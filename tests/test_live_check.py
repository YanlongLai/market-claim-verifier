"""Offline runner, source identity, recorded replay, and public spend guard tests."""
import asyncio
import copy
import json
from pathlib import Path
import sys

import pytest

from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_verdict
from claimcheck.edgar import EdgarClient
from claimcheck.providers import BASETEN_DEFAULT_MODEL, BASETEN_PRICING
from claimcheck.tools import ToolRunner

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workers/live/src"))
from live import LiveError, LiveRun, finish, reservation_for, usage_cost, validate_text  # noqa: E402
from gate import transition  # noqa: E402
from scripts.build_live_demo import build as build_demo  # noqa: E402
from scripts.build_live_worker import build as build_worker  # noqa: E402

EVIDENCE = ROOT / "docs/evidence/eval-v2-2026-10-27"
FIXTURES = ROOT / "tests/fixtures/sec-offline"
APPLE = json.loads((EVIDENCE / "R06--agent@baseten.json").read_text())
TRACE = json.loads((EVIDENCE / APPLE["trace_path"]).read_text())


class Gate:
    def __init__(self, budget="3"):
        self.state, self.budget, self.actions = {}, budget, []

    async def __call__(self, action, data):
        self.actions.append(action)
        result, status = transition(self.state, action, data, now=1793635200, budget=self.budget)
        if status != 200:
            raise LiveError(result["error"], status)
        return result


def fixture_sec(url):
    filename = url.rsplit("/", 1)[-1]
    if filename.startswith("CIK"):
        filename = "companyfacts-" + filename
    return asyncio.sleep(0, result=(FIXTURES / filename).read_text())


def replay_model(gate, *, modify=None):
    responses = [copy.deepcopy(r["raw_response"]) for r in TRACE["requests"]]
    async def call(payload):
        assert gate.actions[-1] == "reserve", "no model I/O before the durable reservation"
        assert payload["model"] == "meta-models/muse-spark-open-1026"
        result = responses.pop(0)
        if modify:
            modify(result)
        return result
    return call


def test_worker_bundles_every_core_module_byte_for_byte(tmp_path):
    hashes = build_worker(tmp_path / "claimcheck")
    assert {p.name for p in (ROOT / "src/claimcheck").glob("*.py")} == set(hashes)
    for name in hashes:
        assert (tmp_path / "claimcheck" / name).read_bytes() == (ROOT / "src/claimcheck" / name).read_bytes()
    # Cloudflare receives the same checks, tool dispatcher and price ledger.
    assert {"checks.py", "numbers.py", "tools.py", "edgar.py", "budget.py"} <= set(hashes)


def test_recorded_demo_is_reproducible_and_does_not_publish_reasoning():
    demo = build_demo()
    assert json.loads((ROOT / "docs/site/data/live-demo.json").read_text()) == demo
    assert demo["cost_usd"] == TRACE["cost_usd"]
    assert demo["latency_ms"] == TRACE["latency_ms"]
    assert demo["started_at"] == APPLE["started_at"]
    assert all(event["timestamp"] is None for event in demo["events"])
    assert "reasoning_content" not in json.dumps(demo)
    assert len([e for e in demo["events"] if e["kind"] == "model"]) == 3


def test_real_baseten_responses_replay_through_live_runner_without_network():
    async def run():
        gate = Gate()
        live = LiveRun(replay_model(gate), fixture_sec, gate)
        result = await live.bounded(APPLE["claim"])
        assert result["verdict"] == "supported"
        assert result["claims"][0]["actual_value"] == 109417000000
        assert result["claims"][0]["tolerance"] == 50000000
        assert result["evidence"][0]["period"] == "FY2026Q3"
        assert result["cost_usd"] == pytest.approx(TRACE["cost_usd"])
        assert result["cost_is_bound"] is False
        assert gate.actions == ["reserve", "settle"] * 3
        assert "reasoning_content" not in json.dumps(result)
        assert [e["kind"] for e in result["events"]] == [
            "model", "tool_call", "tool_result", "model", "model", "program_check", "verdict"]
    asyncio.run(run())


@pytest.mark.parametrize("value,expected", [(109400000000, "supported"), (200000000000, "contradicted"), (None, "insufficient_evidence")])
def test_three_outcomes_are_decided_by_python_not_model(value, expected):
    runner = ToolRunner(EdgarClient(cache_dir=FIXTURES, fetcher=lambda _: pytest.fail("network")))
    tool = TRACE["tool_calls"][0]
    runner.dispatch(tool["name"], tool["arguments"])
    final = copy.deepcopy(TRACE["final_verdict"])
    sub = final["sub_claims"][0]
    # The proposed model verdict remains supported in all three cases.
    if value is None:
        sub["claim_type"], sub["evidence_ids"] = "other", []
    else:
        sub["stated_text"] = f"${value / 1e9:.1f} billion"
        sub["text"] = f"Apple fiscal Q3 2026 revenue was {sub['stated_text']}"
        sub["stated_value"] = value
    assert finish(sub["text"], final, runner)["verdict"] == expected


def test_all_357_v2_baseten_tool_transcripts_use_the_cli_evaluator():
    count = 0
    for path in sorted(EVIDENCE.glob("*--agent@baseten.json")):
        record = json.loads(path.read_text())
        if record["status"] != "completed":
            continue
        trace = json.loads((EVIDENCE / record["trace_path"]).read_text())
        final = trace["final_verdict"]
        def runner():
            r = ToolRunner(EdgarClient(cache_dir=FIXTURES, fetcher=lambda _: pytest.fail("network")))
            for tool in trace["tool_calls"]:
                result = tool.get("result", {})
                if result.get("evidence_id"):
                    r.evidence[result["evidence_id"]] = copy.deepcopy(result)
                    r.evidence_kind[result["evidence_id"]] = tool["name"]
            r._next_program_evidence = 1000  # avoid collisions with recorded P IDs
            return r
        cli_checks, cli_verdict = evaluate_verdict(
            [{**s, "original_claim": record["claim"]} for s in final["sub_claims"]], runner())
        result = finish(record["claim"], final, runner())
        assert result["verdict"] == cli_verdict, path.name
        assert result["claims"] == cli_checks, path.name
        count += 1
    assert count == 357


@pytest.mark.parametrize("text", ["", "   ", "x" * 601, None, 42])
def test_invalid_input_is_refused(text):
    with pytest.raises(LiveError, match="invalid_input"):
        validate_text(text)


@pytest.mark.parametrize("text", ["Bitcoin was up 2%", "台積電營收", "TWSE index grew 2%"])
def test_scope_is_explicit_before_a_model_call(text):
    with pytest.raises(LiveError, match="out_of_scope"):
        validate_text(text)


def test_budget_pricing_and_missing_usage_follow_cli_with_a_larger_public_hold():
    for text in ("Apple revenue " * 20, "蘋果營收" * 100):
        payload = {"model": BASETEN_DEFAULT_MODEL, "messages": [{"role": "user", "content": text}], "max_tokens": 2000}
        hold = reservation_for(payload)
        cli = Ledger(persist=False, provider="baseten").estimate(payload, model=BASETEN_DEFAULT_MODEL, max_output_tokens=2000)
        assert hold["cli_estimate"] == cli.amount
        assert hold["estimated_input_tokens"] == cli.estimated_input_tokens
        assert hold["amount"] >= cli.amount
        assert hold["amount"] == hold["input_ceiling"] * BASETEN_PRICING["input"] + 2000 * BASETEN_PRICING["output"]
        usage = {"prompt_tokens": 1200, "completion_tokens": 400, "prompt_tokens_details": {"cached_tokens": 1000}}
        assert usage_cost(payload, usage) == Ledger(persist=False, provider="baseten").reconcile(cli, usage)
        for bad in (None, {}, {"prompt_tokens": -1, "completion_tokens": 0}):
            assert usage_cost(payload, bad) is None


def test_concurrent_requests_cannot_overspend_and_refunds_are_idempotent():
    async def run():
        gate = Gate("0.10")
        async def reserve(i):
            await asyncio.sleep(0)
            try:
                await gate("reserve", {"id": str(i), "amount": .03})
                return True
            except LiveError:
                return False
        assert sum(await asyncio.gather(*(reserve(i) for i in range(30)))) == 3
        before = next(iter(gate.state["days"].values()))["amount"]
        await gate("settle", {"id": "0", "amount": .01})
        await gate("settle", {"id": "0", "amount": .01})
        assert next(iter(gate.state["days"].values()))["amount"] == pytest.approx(before - .02)
        await gate("settle", {"id": "1", "amount": None})
        assert next(iter(gate.state["days"].values()))["amount"] == pytest.approx(before - .02)
    asyncio.run(run())


def test_budget_failure_prevents_model_and_failed_model_keeps_hold():
    async def run():
        async def never(_):
            pytest.fail("paid model must not be reached")
        gate = Gate("0")
        with pytest.raises(LiveError, match="budget_exhausted"):
            await LiveRun(never, never, gate).bounded(APPLE["claim"])
        gate = Gate()
        async def broken(_):
            raise LiveError("provider_error")
        live = LiveRun(broken, never, gate)
        with pytest.raises(LiveError, match="provider_error"):
            await live.bounded(APPLE["claim"])
        assert len(gate.state["holds"]) == 1
        assert live.envelope()["cost_is_bound"] is True
        assert next(iter(gate.state["days"].values()))["amount"] > 0
    asyncio.run(run())


def test_missing_period_uses_cli_abstention_without_model_or_sec_io():
    async def run():
        async def never(*args):
            pytest.fail("missing period must not call a model or SEC")
        result = await LiveRun(never, never, never).bounded("Apple revenue reached $109.4 billion")
        assert result["verdict"] == "insufficient_evidence"
        assert result["cost_usd"] == 0
        assert "missing_period" in result["claims"][0]["flags"]
    asyncio.run(run())


def test_failure_after_lookup_keeps_partial_sec_evidence_and_cost():
    async def run():
        gate = Gate()
        first = copy.deepcopy(TRACE["requests"][0]["raw_response"])
        calls = 0
        async def model(_):
            nonlocal calls
            calls += 1
            if calls == 1:
                return first
            raise LiveError("provider_error")
        live = LiveRun(model, fixture_sec, gate)
        with pytest.raises(LiveError, match="provider_error"):
            await live.bounded(APPLE["claim"])
        partial = live.envelope()
        assert partial["evidence"][0]["value"] == 109417000000
        assert partial["cost_is_bound"] is True
        assert partial["cost_usd"] > TRACE["requests"][0]["cost"]
        assert "verdict" not in partial
    asyncio.run(run())


def test_rate_limit_privacy_expiry_daily_reset_and_invalid_config():
    state = {}
    def op(action, data, t=1000, cap="3"):
        return transition(state, action, data, now=t, budget=cap)
    for _ in range(5):
        assert op("rate", {"ip": "192.0.2.1"})[1] == 200
    assert op("rate", {"ip": "192.0.2.1"})[1] == 429
    assert "192.0.2.1" not in json.dumps(state)
    assert op("rate", {"ip": "192.0.2.1"}, 1601)[1] == 200
    assert op("reserve", {"id": "a", "amount": 3})[1] == 200
    assert op("reserve", {"id": "b", "amount": .001})[1] == 429
    assert op("reserve", {"id": "c", "amount": 3}, 87400)[1] == 200
    assert op("reserve", {"id": "d", "amount": .001}, cap="NaN")[1] == 503
    assert op("reserve", {"id": "d", "amount": .001}, cap="-1")[1] == 503
    # No user text, IP addresses, provider keys or model bodies enter the ledger.
    assert set(state) <= {"rates", "days", "holds", "salt", "salt_day"}


def test_gate_uses_integer_money_and_rate_windows_span_utc_midnight():
    state = {}
    for i in range(5):
        assert transition(state, "rate", {"ip": "192.0.2.1"}, now=86399, budget="3")[1] == 200
    assert transition(state, "rate", {"ip": "192.0.2.1"}, now=86401, budget="3")[1] == 429
    state = {}
    for i in range(3):
        assert transition(state, "reserve", {"id": str(i), "amount": .1}, now=1000, budget=".3")[1] == 200
    assert next(iter(state["days"].values()))["amount_nanos"] == 300_000_000
    assert transition(state, "reserve", {"id": "over", "amount": .0000000001}, now=1000, budget=".3")[1] == 429
