"""Offline budget and actual Worker/SQLite adapter tests; no provider requests."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workers/live/src"))
from gate import prune, transition  # noqa: E402
from live import LiveError, provider_credit_exhausted  # noqa: E402


def op(state, action="budget", data=None, now=86399, daily="3", total="20"):
    return transition(state, action, data or {}, now=now, budget=daily, total_budget=total)


def test_public_remaining_counts_holds_and_reconciliation_not_private_data():
    state = {}
    assert op(state, "reserve", {"id": "a", "amount": .59})[1] == 200
    budget, status = op(state)
    assert status == 200
    assert budget["day"] == "1970-01-01"
    assert budget["resets_at"] == "1970-01-02T00:00:00Z"
    assert budget["status"] == "ready"
    assert budget["global"] == {"daily_limit": 3.0, "daily_spent": .59, "daily_remaining": 2.41,
                                "lifetime_limit": 20.0, "lifetime_spent": .59, "lifetime_remaining": 19.41,
                                "status": "ready"}
    assert budget["daily_limit_usd"] == 90
    assert budget["daily_remaining_usd"] == 89.41
    op(state, "settle", {"id": "a", "amount": .02})
    op(state, "settle", {"id": "a", "amount": .02})
    assert op(state)[0]["global"]["daily_remaining"] == 2.98
    assert state["lifetime_nanos"] == 20_000_000
    op(state, "reserve", {"id": "unknown-usage", "amount": .1})
    op(state, "settle", {"id": "unknown-usage", "amount": None})
    assert op(state)[0]["global"]["daily_remaining"] == 2.88


def test_utc_midnight_and_late_reconciliation_touch_original_day_only():
    state = {}
    op(state, "reserve", {"id": "yesterday", "amount": 3})
    assert op(state)[0]["status"] == "budget_exhausted"
    assert op(state, now=86400)[0]["global"]["daily_remaining"] == 3
    assert op(state, now=86400)[0]["resets_at"] == "1970-01-03T00:00:00Z"
    op(state, "reserve", {"id": "today", "amount": .5}, now=86400)
    op(state, "settle", {"id": "yesterday", "amount": .1}, now=86401)
    assert op(state, now=86401)[0]["global"]["daily_remaining"] == 2.5
    assert state["lifetime_nanos"] == 600_000_000
    # Idle cleanup does not forgive unsettled spending in the lifetime counter.
    prune(state, 400000)
    assert state["lifetime_nanos"] == 600_000_000


def test_lifetime_cap_survives_midnight_refund_idle_and_limit_increase():
    state = {}
    op(state, "reserve", {"id": "a", "amount": 3}, total="4")
    assert op(state, "reserve", {"id": "b", "amount": 1}, now=86400, total="4")[1] == 200
    op(state, "settle", {"id": "b", "amount": .01}, now=86401, total="4")
    assert state["lifetime_nanos"] == 3_010_000_000
    prune(state, 400000)
    budget, _ = op(state, now=400000, total="100")
    assert budget["global"]["daily_remaining"] == 3
    assert budget["status"] == "total_budget_exhausted"
    assert op(state, "reserve", {"id": "c", "amount": .01}, now=400000, total="100")[1] == 503


def test_insufficient_lifetime_reservation_latches_and_legacy_days_are_adopted():
    state = {"days": {"1970-01-01": {"amount": .9, "expires": 400000}}}
    result, status = op(state, "reserve", {"id": "a", "amount": .11}, total="1")
    assert status == 503 and result["error"] == "total_budget_exhausted"
    assert state["lifetime_nanos"] == 900_000_000
    assert result["budget"]["status"] == "total_budget_exhausted"


def test_default_twenty_dollar_lifetime_limit_includes_days_pruned_by_alarms():
    state = {}
    for day in range(6):
        assert op(state, "reserve", {"id": str(day), "amount": 3}, now=day * 86400)[1] == 200
    assert op(state, "reserve", {"id": "last", "amount": 2}, now=6 * 86400)[1] == 200
    assert state["lifetime_nanos"] == 20_000_000_000
    assert op(state, now=40 * 86400)[0]["status"] == "total_budget_exhausted"


def test_admin_deployment_reset_is_once_only_and_keeps_pending_holds_and_daily_spend():
    state = {}
    op(state, "reserve", {"id": "settled", "amount": .5})
    op(state, "settle", {"id": "settled", "amount": .1})
    op(state, "reserve", {"id": "inflight", "amount": .5})
    op(state, "credit_exhausted")
    assert op(state, "budget", {"reset_id": "public-cannot-reset"})[0]["status"] == "credit_exhausted"
    def reset(action="budget", data=None):
        return transition(state, action, data or {}, now=86399, budget="3", reset_id="admin-2026-11-02")
    assert reset()[0]["status"] == "ready"
    assert state["lifetime_nanos"] == 500_000_000
    assert reset()[0]["global"]["daily_remaining"] == 2.4
    reset("reserve", {"id": "after-reset", "amount": .1})
    reset("settle", {"id": "inflight", "amount": .2})
    assert reset()[0]["global"]["daily_remaining"] == 2.6
    assert state["lifetime_nanos"] == 300_000_000
    reset("credit_exhausted")
    assert reset()[0]["status"] == "credit_exhausted"  # same ID never resets twice


@pytest.mark.parametrize("cap", ["NaN", "Infinity", "-1", "oops"])
def test_invalid_total_config_fails_closed(cap):
    assert op({}, "reserve", {"id": "a", "amount": .01}, total=cap)[1] == 503


@pytest.mark.parametrize("status,body,paused", [
    (402, "", True), (402, "unreadable billing body", True),
    (403, '{"error":{"code":"insufficient_quota"}}', True),
    (429, '{"error":"You exceeded your current quota"}', True),
    (429, '{"error":{"message":"Account credits have been exhausted"}}', True),
    (403, '{"error":"Payment required"}', True),
    (403, '{"error":"Your spending limit has been reached"}', True),
    (429, '{"error":"Monthly budget exceeded"}', True),
    (403, '{"error":"Invalid API key"}', False),
    (429, '{"error":"Rate limit exceeded; requests per minute"}', False),
    (429, '{"error":"No capacity available"}', False),
    (529, '{"error":"Capacity exhausted"}', False),
    (500, '{"error":"Quota exceeded"}', False),
])
def test_baseten_status_and_exhaustion_wording(status, body, paused):
    assert provider_credit_exhausted(status, body) is paused


class Response:
    def __init__(self, body, status=200, headers=None):
        self.body, self.status, self.headers = body, status, headers or {}
        self.ok = 200 <= status < 300

    async def text(self):
        return self.body

    async def json(self):
        return json.loads(self.body)


class Request:
    def __init__(self, url, options=None):
        options = options or {}
        self.url, self.method = url, options.get("method", "GET")
        self.headers, self.body = options.get("headers", {}), options.get("body", "")

    async def text(self):
        return self.body

    async def json(self):
        return json.loads(self.body)


@pytest.fixture
def adapter(monkeypatch):
    """Load the shipped Cloudflare adapter with SQLite and JS transport doubles."""
    class Base:
        def __init__(self, ctx=None, env=None):
            self.ctx, self.env = ctx, env

    js = ModuleType("js")
    js.AbortSignal = SimpleNamespace(timeout=lambda _: None)
    js.Object = SimpleNamespace(fromEntries=lambda v: v)
    js.Request, js.Response = SimpleNamespace(new=Request), SimpleNamespace(new=Response)
    js.caches, js.fetch = SimpleNamespace(), lambda *a, **k: pytest.fail("network")
    ffi = ModuleType("pyodide.ffi")
    ffi.to_js = lambda v, **_: v
    workers = ModuleType("workers")
    workers.DurableObject, workers.WorkerEntrypoint, workers.Response = Base, Base, Response
    for key, value in {"js": js, "pyodide.ffi": ffi, "workers": workers}.items():
        monkeypatch.setitem(sys.modules, key, value)
    spec = importlib.util.spec_from_file_location("live_budget_worker", ROOT / "workers/live/src/entry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.time, "time", lambda: 86399)
    return module


class Storage:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:")
        self.sql = self
        self.alarms = []

    def exec(self, query, *params):
        cursor = self.connection.execute(query, params)
        rows = cursor.fetchall()
        return SimpleNamespace(toArray=lambda: [SimpleNamespace(body=row[0]) for row in rows])

    async def setAlarm(self, when):
        self.alarms.append(when)
        await asyncio.sleep(0)  # concurrent fetches may run after the write


def durable(adapter, daily="3", total="20", storage=None, password="offline-password", provider_env=None):
    storage = storage or Storage()
    gate = adapter.SpendGate(SimpleNamespace(storage=storage), SimpleNamespace(
        DAILY_BUDGET_USD=daily, TOTAL_BUDGET_USD=total, LIVE_CHECK_PASSWORD=password, **(provider_env or {})))
    async def call(action, data=None):
        return await gate.fetch(Request("https://gate.internal/", {"method": "POST", "body": json.dumps({"action": action, "data": data or {}})}))
    return gate, call, storage


def test_durable_adapter_reads_provider_env_caps_and_keeps_other_providers_available(adapter):
    async def run():
        gate, call, _ = durable(adapter, provider_env={"META_DAILY_BUDGET_USD": ".05", "BASETEN_LIFETIME_BUDGET_USD": ".05"})
        for provider in ("meta", "baseten"):
            assert (await call("reserve", {"provider": provider, "id": provider, "amount": .03})).status == 200
            assert (await call("reserve", {"provider": provider, "id": provider + "-extra", "amount": .03})).status == (429 if provider == "meta" else 503)
        budget = await (await call("budget")).json()
        assert budget["providers"]["meta"]["daily_limit"] == .05
        assert budget["providers"]["meta"]["status"] == "budget_exhausted"
        assert budget["providers"]["baseten"]["lifetime_limit"] == .05
        assert budget["providers"]["fireworks"]["status"] == budget["status"] == "ready"
        assert gate.load()["lifetime_nanos"] == 60_000_000
    asyncio.run(run())


@pytest.mark.parametrize("daily,total", [(".1", "20"), ("3", ".1")])
def test_concurrent_actual_durable_sqlite_reservations_never_exceed_either_cap(adapter, daily, total):
    async def run():
        gate, call, _ = durable(adapter, daily, total)
        responses = await asyncio.gather(*(call("reserve", {"id": str(i), "amount": .03}) for i in range(50)))
        assert sum(r.status == 200 for r in responses) == 3
        assert gate.load()["lifetime_nanos"] == 90_000_000
        assert next(iter(gate.load()["days"].values()))["amount_nanos"] == 90_000_000
        budget = await (await call("budget")).json()
        assert budget["global"]["daily_remaining"] == pytest.approx(float(daily) - .09)
    asyncio.run(run())


@pytest.mark.parametrize("stop", ["daily", "lifetime", "credit"])
def test_actual_worker_refuses_before_model_and_budget_get_needs_no_key(adapter, stop):
    async def run():
        _, call, _ = durable(adapter, daily="0" if stop == "daily" else "3", total="0" if stop == "lifetime" else "20")
        if stop == "credit":
            await call("credit_exhausted")
        class Namespace:
            def idFromName(self, name):
                assert name == "baseten-live-global-v1"
                return name
            def get(self, _):
                return SimpleNamespace(fetch=lambda req: call(**json.loads(req.body)))
        worker = adapter.Default(env=SimpleNamespace(SPEND_GATE=Namespace(), BASETEN_API_KEY="offline-dummy"))
        response = await worker.fetch(Request("https://live.internal/api/check", {
            "method": "POST", "headers": {"X-Live-Client-IP": "192.0.2.1"},
            "body": json.dumps({"text": "Apple fiscal Q3 2026 revenue was $109.4 billion.", "password": "offline-password"})}))
        assert response.status == (429 if stop == "daily" else 503)
        assert (await response.json())["error"] == {"daily": "budget_exhausted", "lifetime": "total_budget_exhausted", "credit": "credit_exhausted"}[stop]
        del worker.env.BASETEN_API_KEY
        budget = await worker.fetch(Request("https://live.internal/api/budget"))
        assert budget.status == 200
        assert "s-maxage=5" in budget.headers["Cache-Control"]
    asyncio.run(run())


@pytest.mark.parametrize("status,body,paused", [(402, "billing", True), (429, "quota exhausted", True), (403, "insufficient credits", True), (429, "rate limit exceeded", False), (403, "invalid API key", False)])
def test_provider_response_sets_durable_pause_then_blocks_next_run_and_survives_alarm(adapter, monkeypatch, status, body, paused):
    async def run():
        gate, call, storage = durable(adapter)
        worker = adapter.Services(SimpleNamespace(BASETEN_API_KEY="offline-dummy"))
        async def internal(action, data):
            response = await call(action, data)
            value = await response.json()
            if not response.ok:
                raise LiveError(value["error"], response.status)
            return value
        worker.gate = internal
        calls = []
        async def outbound(*args, **kwargs):
            calls.append(args[0])
            return Response(body, status)
        monkeypatch.setattr(adapter, "outbound", outbound)
        from live import LiveRun
        claim = "Apple fiscal Q3 2026 revenue was $109.4 billion."
        with pytest.raises(LiveError, match="credit_exhausted" if paused else "provider_error"):
            await LiveRun(worker.model, lambda _: pytest.fail("SEC"), internal).bounded(claim)
        assert len(calls) == 1
        assert gate.load()["providers"]["baseten"].get("credit_exhausted", False) is paused
        assert gate.load()["lifetime_nanos"] > 0  # rejected call keeps its hold
        if paused:
            monkeypatch.setattr(adapter.time, "time", lambda: 400000)
            await gate.alarm()
            restarted, after_restart, _ = durable(adapter, storage=storage)
            assert restarted.load()["providers"]["baseten"]["credit_exhausted"] is True
            assert (await (await after_restart("budget")).json())["providers"]["baseten"]["status"] == "credit_exhausted"
            with pytest.raises(LiveError, match="credit_exhausted"):
                await LiveRun(worker.model, lambda _: pytest.fail("SEC"), internal).bounded(claim)
            assert len(calls) == 1
    asyncio.run(run())
