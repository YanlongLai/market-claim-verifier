"""Offline password/lockout regressions through the shipped Worker and SQLite DO."""
import asyncio
import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from test_live_budget import Request, adapter, durable  # noqa: F401
from test_live_check import TRACE, fixture_sec
from gate import password_matches, transition

PASSWORD = "offline-only-密碼-credential-marker"
CLAIM = "Apple fiscal Q3 2026 revenue was $109.4 billion."


def auth(state, value=None, *, ip="192.0.2.1", now=1000, secret=PASSWORD):
    return transition(state, "authenticate", {"ip": ip, "password": value}, now=now,
                      budget="invalid", total_budget="invalid", password_secret=secret)


def test_constant_time_path_always_compares_sha256_digests(monkeypatch):
    import gate
    calls = []
    real_compare = gate.hmac.compare_digest

    def compare(left, right):
        calls.append((left, right))
        assert isinstance(left, bytes) and isinstance(right, bytes)
        assert len(left) == len(right) == 32
        return real_compare(left, right)

    monkeypatch.setattr(gate.hmac, "compare_digest", compare)
    for attempted in [None, {}, False, "", "a", "x" * 3000, PASSWORD[:-1], PASSWORD]:
        assert password_matches(attempted, PASSWORD) is (attempted == PASSWORD)
    assert len(calls) == 8
    assert all(expected == hashlib.sha256(PASSWORD.encode()).digest() for _, expected in calls)


def test_authentication_never_touches_spending_or_request_rate_and_never_resets_failures_on_success():
    state = {"lifetime_nanos": 123, "days": {"saved": {"amount": .1}}, "holds": {"saved": {}},
             "rates": {"saved": {"count": 3}}, "credit_exhausted": True}
    original = copy.deepcopy(state)
    assert auth(state, "wrong")[1] == 401
    assert auth(state, PASSWORD)[1] == 200
    assert next(iter(state["auth_failures"].values()))["count"] == 1
    assert all(state[key] == value for key, value in original.items())
    assert "192.0.2.1" not in json.dumps(state)


def test_failure_window_lockout_and_other_ip_success_do_not_extend_lockout():
    state = {}
    for offset in range(5):
        assert auth(state, "wrong", now=1000 + offset)[1] == (401 if offset < 4 else 429)
    assert auth(state, PASSWORD, now=1005) == ({"error": "locked", "retry_after": 1799}, 429)
    assert auth(state, PASSWORD, now=1006, ip="192.0.2.2")[1] == 200
    assert auth(state, "wrong", now=2803)[1] == 429
    assert auth(state, PASSWORD, now=2804)[1] == 200
    assert state["auth_failures"] == {}
    assert auth(state, "wrong", now=3000)[1] == 401
    assert auth(state, "wrong", now=3900)[1] == 401
    assert next(iter(state["auth_failures"].values()))["count"] == 1


def worker(adapter, call):
    actions = []

    class Namespace:
        def idFromName(self, name):
            assert name == "baseten-live-global-v1"
            return name

        def get(self, _):
            async def fetch(req):
                data = json.loads(req.body)
                actions.append(data["action"])
                return await call(**data)
            return SimpleNamespace(fetch=fetch)

    return adapter.Default(env=SimpleNamespace(SPEND_GATE=Namespace(), BASETEN_API_KEY="offline-dummy")), actions


def request(password=None, ip="192.0.2.1", **extra):
    return Request("https://live.internal/api/check", {
        "method": "POST", "headers": {"X-Live-Client-IP": ip},
        "body": json.dumps({"text": CLAIM, "password": password, **extra})})


@pytest.mark.parametrize("secret", [None, ""])
def test_unset_secret_fails_closed_before_budget_or_network_and_budget_is_public(adapter, secret, capsys, caplog):
    async def run():
        gate, call, _ = durable(adapter, password=secret)
        if secret is None:
            del gate.env.LIVE_CHECK_PASSWORD
        app, actions = worker(adapter, call)
        response = await app.fetch(request(PASSWORD))
        assert response.status == 503
        assert (await response.json())["error"] == "unavailable"
        assert actions == ["authenticate"]
        assert gate.load() == {}
        del app.env.BASETEN_API_KEY
        public = await app.fetch(Request("https://live.internal/api/budget"))
        assert public.status == 200
        assert PASSWORD not in response.body + public.body + json.dumps(gate.load())
    asyncio.run(run())
    assert PASSWORD not in capsys.readouterr().out + caplog.text


@pytest.mark.parametrize("attempted", [None, "", "wrong-marker", False, {}, PASSWORD[:-1]])
def test_missing_or_wrong_password_is_401_without_budget_reservation_or_model(adapter, attempted, capsys, caplog):
    async def run():
        gate, call, _ = durable(adapter, daily="0", total="0", password=PASSWORD)
        app, actions = worker(adapter, call)
        # Even a paid endpoint with no provider key must authenticate first.
        del app.env.BASETEN_API_KEY
        response = await app.fetch(request(attempted))
        assert response.status == 401
        assert await response.json() == {"error": "unauthorized", "demo": "data/live-demo.json"}
        assert response.headers["Cache-Control"] == "no-store"
        assert actions == ["authenticate"]
        state = gate.load()
        assert set(state) == {"auth_failures", "salt"}
        assert next(iter(state["auth_failures"].values()))["count"] == 1
        assert PASSWORD not in response.body + json.dumps(state)
        assert "wrong-marker" not in response.body + json.dumps(state)
    asyncio.run(run())
    captured = capsys.readouterr()
    assert not captured.out and not captured.err and not caplog.text


def test_concurrent_failures_lock_across_sqlite_restart_then_alarm_expires_them(adapter, monkeypatch):
    async def run():
        gate, call, storage = durable(adapter, password=PASSWORD)
        app, actions = worker(adapter, call)
        responses = await asyncio.gather(*(app.fetch(request("wrong-marker")) for _ in range(20)))
        assert sum(r.status == 401 for r in responses) == 4
        assert sum(r.status == 429 for r in responses) == 16
        assert set(actions) == {"authenticate"}
        assert storage.alarms[-1] == (86399 + 1800) * 1000
        restarted, again, _ = durable(adapter, storage=storage, password=PASSWORD)
        app, actions = worker(adapter, again)
        assert (await app.fetch(request(PASSWORD))).status == 429
        assert actions == ["authenticate"]
        state = restarted.load()
        assert set(state) == {"auth_failures", "salt"}
        serialized = json.dumps(state)
        assert all(value not in serialized for value in [PASSWORD, "wrong-marker", "192.0.2.1",
                                                        hashlib.sha256(PASSWORD.encode()).hexdigest()])
        monkeypatch.setattr(adapter.time, "time", lambda: 86399 + 1800)
        await restarted.alarm()
        assert restarted.load()["auth_failures"] == {}
        assert (await (await again("authenticate", {"ip": "192.0.2.1", "password": PASSWORD})).json()) == {"ok": True}
    asyncio.run(run())


def test_authenticated_success_replays_original_model_trace_without_password_leaks(adapter, monkeypatch, capsys, caplog):
    async def run():
        gate, call, _ = durable(adapter, password=PASSWORD)
        app, actions = worker(adapter, call)
        responses = [copy.deepcopy(item["raw_response"]) for item in TRACE["requests"]]
        payloads = []

        async def model(_self, payload):
            assert actions[-1] == "reserve"
            payloads.append(payload)
            return responses.pop(0)

        async def sec(_self, url):
            return await fixture_sec(url)

        monkeypatch.setattr(adapter.Services, "model", model)
        monkeypatch.setattr(adapter.Services, "sec", sec)
        response = await app.fetch(request(PASSWORD))
        result = await response.json()
        assert response.status == 200
        assert result["verdict"] == "supported" and result["mode"] == "live"
        assert result["claims"][0]["evidence_ids"] == ["E1"]
        assert actions[:3] == ["authenticate", "budget", "rate"]
        assert actions.count("reserve") == actions.count("settle") == len(payloads) == 3
        assert gate.load()["lifetime_nanos"] > 0
        assert not responses
        assert PASSWORD not in response.body + json.dumps(gate.load()) + json.dumps(payloads)
        assert not any(hasattr(adapter.Default, name) for name in ("model", "sec", "gate"))
    asyncio.run(run())
    captured = capsys.readouterr()
    assert not captured.out and not captured.err and not caplog.text
