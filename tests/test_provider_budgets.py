"""Provider caps, legacy migration and paid-call attribution with fake I/O only."""
import asyncio
from datetime import datetime, timezone
import json

import pytest

from server.live.server import Settings, SpendGate
from test_live_check import APPLE
from test_live_examples import config as example_config, transport_for
from test_live_providers_history import provider_settings, replay_transport
from test_live_server import NOW, PASSWORD, TOKEN, data, request, running, settings
from workers.live.src.gate import NANOS, PROVIDERS, prune, transition
from workers.live.src.live import LiveError


def op(state, action="budget", payload=None, *, now=86399, caps=None, daily="90", total="60"):
    return transition(state, action, payload or {}, now=now, budget=daily, total_budget=total,
                      provider_budgets=caps)


def test_defaults_api_shape_and_compatibility_sums():
    state = {}
    assert op(state, "reserve", {"provider": "meta", "id": "m", "amount": .5})[1] == 200
    budget, status = op(state)
    assert status == 200 and budget["status"] == "ready"
    assert set(budget["providers"]) == set(PROVIDERS)
    assert budget["providers"]["meta"] == {
        "daily_limit": 30, "daily_spent": .5, "daily_remaining": 29.5,
        "lifetime_limit": 20, "lifetime_spent": .5, "lifetime_remaining": 19.5, "status": "ready"}
    assert budget["providers"]["baseten"]["lifetime_spent"] == 0
    for field in ("daily_limit", "daily_spent", "daily_remaining",
                  "lifetime_limit", "lifetime_spent", "lifetime_remaining"):
        assert budget[field + "_usd"] == sum(row[field] for row in budget["providers"].values())
    assert not any(key in json.dumps(budget) for key in ("holds", "salt", "provider_migration", "amount_nanos"))


def test_http_budget_exposes_each_configured_cap_without_password_or_provider_keys(tmp_path):
    async def run():
        config = Settings(
            data_dir=tmp_path, origin_token=TOKEN, daily_budget="80", total_budget="90",
            baseten_daily_budget="10", baseten_lifetime_budget="15", meta_daily_budget="40", meta_lifetime_budget="50",
            fireworks_daily_budget="30", fireworks_lifetime_budget="25")
        async with running(config) as (app, services):
            await services.gate("reserve", {"provider": "meta", "id": "m", "amount": .25})
            response = await request(app, "/api/budget", method="GET")
            budget = data(response)
            assert response.status == 200 and "s-maxage=5" in response.headers["Cache-Control"]
            assert budget["providers"]["meta"] == {
                "daily_limit": 40, "daily_spent": .25, "daily_remaining": 39.75,
                "lifetime_limit": 50, "lifetime_spent": .25, "lifetime_remaining": 49.75, "status": "ready"}
            assert budget["providers"]["baseten"]["daily_limit"] == 10
            assert budget["providers"]["fireworks"]["lifetime_limit"] == 25
            assert budget["daily_limit_usd"] == 80 and budget["lifetime_limit_usd"] == 90
            assert not any(key in json.dumps(budget) for key in ("password", "api_key", "holds", "salt", "amount_nanos"))
    asyncio.run(run())


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("stop", ["daily", "lifetime", "credit"])
def test_one_provider_stops_without_borrowing_or_pausing_the_others(provider, stop):
    state = {}
    caps = {provider: ("0" if stop == "daily" else "30", "0" if stop == "lifetime" else "20")}
    if stop == "credit":
        op(state, "credit_exhausted", {"provider": provider})
    result, status = op(state, "reserve", {"provider": provider, "id": "blocked", "amount": .1}, caps=caps)
    assert status == (429 if stop == "daily" else 503)
    expected = {"daily": "budget_exhausted", "lifetime": "total_budget_exhausted", "credit": "credit_exhausted"}[stop]
    assert result["error"] == expected and not state["holds"]
    budget, _ = op(state, caps=caps)
    assert budget["status"] == "ready" and budget["providers"][provider]["status"] == expected
    for other in set(PROVIDERS) - {provider}:
        assert op(state, "reserve", {"provider": other, "id": other, "amount": .1}, caps=caps)[1] == 200
    assert state["providers"][provider]["lifetime_nanos"] == 0
    assert state["lifetime_nanos"] == 200_000_000


def test_nano_rounding_atomic_rejection_settlement_binding_and_midnight():
    state = {}
    caps = {"meta": (".3000000009", "1")}
    for i in range(3):
        assert op(state, "reserve", {"provider": "meta", "id": str(i), "amount": .1}, caps=caps)[1] == 200
    assert op(state, "reserve", {"provider": "meta", "id": "extra", "amount": 1e-10}, caps=caps)[1] == 429
    assert state["lifetime_nanos"] == 300_000_000
    assert op(state, "settle", {"id": "0", "provider": "baseten", "amount": 0}, caps=caps)[1] == 503
    assert not state["holds"]["0"]["settled"]
    for _ in range(2):
        assert op(state, "settle", {"id": "0", "provider": "meta", "amount": .02}, now=86401, caps=caps)[1] == 200
    budget, _ = op(state, now=86401, caps=caps)
    assert budget["providers"]["meta"]["daily_remaining"] == .3
    assert budget["providers"]["meta"]["lifetime_spent"] == .22
    assert state["providers"]["meta"]["days"]["1970-01-01"]["amount_nanos"] == 220_000_000
    assert op(state, "settle", {"id": "1", "provider": "meta", "amount": None}, now=86401, caps=caps)[1] == 200
    prune(state, 400000)
    assert state["providers"]["meta"]["lifetime_nanos"] == 220_000_000


def test_provider_lifetime_latch_survives_refund_pruning_and_cap_increase():
    state = {}
    caps = {"fireworks": ("30", ".5")}
    op(state, "reserve", {"provider": "fireworks", "id": "f", "amount": .5}, caps=caps)
    op(state, "settle", {"provider": "fireworks", "id": "f", "amount": .01}, caps=caps)
    prune(state, 400000)
    budget, _ = op(state, now=400000, caps={"fireworks": ("100", "100")})
    assert budget["providers"]["fireworks"]["lifetime_spent"] == .01
    assert budget["providers"]["fireworks"]["status"] == "total_budget_exhausted"
    assert budget["status"] == "ready" and budget["global"]["status"] == "ready"


def test_provider_daily_reservation_shortfall_is_visible_until_utc_midnight():
    state = {}
    caps = {"meta": (".05", "20")}
    op(state, "reserve", {"provider": "meta", "id": "m", "amount": .03}, caps=caps)
    result, status = op(state, "reserve", {"provider": "meta", "id": "extra", "amount": .03}, caps=caps)
    assert status == 429 and result["budget"]["providers"]["meta"]["status"] == "budget_exhausted"
    assert op(state, caps=caps)[0]["providers"]["meta"]["daily_spent"] == .03
    assert op(state, caps=caps)[0]["providers"]["meta"]["daily_remaining"] == .02
    assert op(state, caps=caps)[0]["providers"]["baseten"]["status"] == "ready"
    assert op(state, now=86400, caps=caps)[0]["providers"]["meta"]["status"] == "ready"
    assert op(state, now=86400, caps=caps)[0]["providers"]["meta"]["lifetime_spent"] == .03


@pytest.mark.parametrize("daily,total,error", [(".3", "60", "budget_exhausted"), ("90", ".3", "total_budget_exhausted")])
def test_sum_guard_is_atomic_across_different_providers(daily, total, error):
    state = {}
    for provider in ("meta", "baseten"):
        assert op(state, "reserve", {"provider": provider, "id": provider, "amount": .15}, daily=daily, total=total)[1] == 200
    result, _ = op(state, "reserve", {"provider": "fireworks", "id": "f", "amount": .01}, daily=daily, total=total)
    assert result["error"] == error
    assert state["lifetime_nanos"] == 300_000_000
    assert state["providers"]["fireworks"]["lifetime_nanos"] == 0
    assert "f" not in state["holds"]


def test_usage_over_the_reserved_bound_pauses_only_the_affected_provider():
    state = {}
    op(state, "reserve", {"provider": "meta", "id": "m", "amount": .1})
    op(state, "settle", {"provider": "meta", "id": "m", "amount": .2})
    budget, _ = op(state)
    assert budget["providers"]["meta"]["status"] == "total_budget_exhausted"
    assert budget["providers"]["meta"]["daily_spent"] == .2
    assert budget["global"]["daily_spent"] == .2
    assert budget["providers"]["baseten"]["status"] == budget["status"] == "ready"


def test_sqlite_migration_preserves_history_global_totals_and_legacy_hold_refunds(tmp_path):
    async def run():
        config = settings(tmp_path, daily_budget="90", total_budget="100")
        gate = SpendGate(config, lambda: NOW)
        day = datetime.fromtimestamp(NOW, timezone.utc).strftime("%Y-%m-%d")
        legacy = {"lifetime_nanos": 12 * NANOS,
                  "days": {day: {"amount": 2, "expires": NOW + 172800}},
                  "holds": {"old": {"day": day, "amount": .5, "settled": False, "expires": NOW + 172800}}}
        gate.db.execute("INSERT INTO ledger VALUES (1, ?)", (json.dumps(legacy),))
        gate.db.execute("INSERT INTO history VALUES ('kept', ?, ?, ?)", (NOW, '{"old":"row"}', '{}'))
        original_history = gate.db.execute("SELECT * FROM history").fetchall()
        budget = await gate.update("budget", {})
        assert budget["global"]["lifetime_spent"] == 12
        assert all(row["lifetime_spent"] == 12 and row["daily_spent"] == 2 for row in budget["providers"].values())
        assert gate.db.execute("SELECT * FROM history").fetchall() == original_history
        await gate.update("settle", {"id": "old", "amount": .2})
        await gate.update("settle", {"id": "old", "amount": .2})
        await gate.update("reserve", {"id": "new", "provider": "meta", "amount": .1})
        await gate.update("settle", {"id": "new", "provider": "meta", "amount": .03})
        gate.close()
        restarted = SpendGate(config, lambda: NOW)
        try:
            saved = json.loads(restarted.db.execute("SELECT body FROM ledger").fetchone()[0])
            assert saved["provider_migration"] == {"version": 2, "legacy_lifetime_nanos": 12 * NANOS,
                                                    "allocation": "conservative_all_providers"}
            budget = await restarted.update("budget", {})
            assert budget["global"]["lifetime_spent"] == budget["providers"]["meta"]["lifetime_spent"] == 11.73
            assert budget["providers"]["baseten"]["lifetime_spent"] == 11.7
            assert restarted.db.execute("SELECT * FROM history").fetchall() == original_history
        finally:
            restarted.close()
    asyncio.run(run())


def test_legacy_days_are_adopted_before_idle_pruning_and_stops_are_preserved():
    state = {"days": {"1970-01-01": {"amount": .9, "expires": 1}}, "credit_exhausted": True}
    prune(state, 400000)
    assert state["lifetime_nanos"] == 900_000_000 and not state["days"]
    assert all(p["lifetime_nanos"] == 900_000_000 and p["credit_exhausted"] for p in state["providers"].values())


@pytest.mark.parametrize("cap", ["NaN", "Infinity", "-1", "bad"])
def test_invalid_provider_cap_fails_closed(cap):
    state = {}
    assert op(state, "reserve", {"id": "bad", "provider": "meta", "amount": .01}, caps={"meta": (cap, "20")})[1] == 503
    assert not state["holds"] and not state["lifetime_nanos"]


def test_settings_load_all_six_caps_and_defaults(monkeypatch):
    # Exercise only cap settings, even under verify's nonexistent key-file guard.
    for name in ("BASETEN_API_KEY", "FIREWORKS_API_KEY", "META_MODEL_API_KEY", "LIVE_CHECK_PASSWORD", "LIVE_ORIGIN_TOKEN"):
        monkeypatch.setenv(name, "")
    for provider in PROVIDERS:
        for period, default in (("daily", "30"), ("lifetime", "20")):
            monkeypatch.delenv(f"{provider.upper()}_{period.upper()}_BUDGET_USD", raising=False)
    assert Settings.from_env().provider_budgets == {p: ("30", "20") for p in PROVIDERS}
    for i, provider in enumerate(PROVIDERS):
        monkeypatch.setenv(provider.upper() + "_DAILY_BUDGET_USD", str(i + 1))
        monkeypatch.setenv(provider.upper() + "_LIFETIME_BUDGET_USD", str(i + 10))
    assert Settings.from_env().provider_budgets == {p: (str(i + 1), str(i + 10)) for i, p in enumerate(PROVIDERS)}


def test_sqlite_concurrent_reservations_never_borrow_another_provider_budget(tmp_path):
    async def run():
        config = settings(tmp_path, daily_budget="90", total_budget="100", meta_daily_budget=".1", baseten_lifetime_budget=".1")
        gate = SpendGate(config, lambda: NOW)
        async def reserve(provider, i):
            try:
                await gate.update("reserve", {"provider": provider, "id": provider + str(i), "amount": .03})
                return True
            except LiveError:
                return False
        try:
            accepted = await asyncio.gather(*(reserve(p, i) for p in ("meta", "baseten") for i in range(30)))
            assert sum(accepted) == 6
            budget = await gate.update("budget", {})
            assert budget["global"]["lifetime_spent"] == .18
            assert budget["providers"]["meta"]["daily_spent"] == .09
            assert budget["providers"]["baseten"]["lifetime_spent"] == .09
            assert budget["providers"]["fireworks"]["daily_spent"] == 0
        finally:
            gate.close()
    asyncio.run(run())


@pytest.mark.parametrize("stop", ["daily", "lifetime", "credit", "reservation"])
def test_compare_skips_an_exhausted_member_and_runs_later_providers(tmp_path, stop):
    async def run():
        options = {}
        if stop == "daily":
            options["baseten_daily_budget"] = "0"
        elif stop in {"lifetime", "reservation"}:
            options["baseten_lifetime_budget"] = "0" if stop == "lifetime" else ".00001"
        calls = []
        async with running(provider_settings(tmp_path, **options), replay_transport(calls)) as (app, services):
            if stop == "credit":
                await services.gate("credit_exhausted", {"provider": "baseten"})
            response = await request(app, "/api/compare", body={"text": APPLE["claim"], "password": PASSWORD,
                                                               "providers": ["baseten", "meta", "fireworks"]})
            runs = data(response)["runs"]
            assert response.status == 200 and len(runs) == 3
            assert runs[0]["error"] in {"budget_exhausted", "total_budget_exhausted", "credit_exhausted"}
            assert runs[0]["receipt"]["cost_usd"] == 0
            assert all(run["verdict"] == "supported" for run in runs[1:])
            assert calls == ["meta"] * 3 + ["fireworks"] * 3
            assert len((await services.ledger.history())["rows"]) == 3
            budget = data(await request(app, "/api/budget", method="GET"))
            assert budget["status"] == "ready" and budget["providers"]["baseten"]["lifetime_spent"] == 0
    asyncio.run(run())


def test_provider_credit_error_during_compare_does_not_stop_later_members(tmp_path):
    async def run():
        calls = []
        replay = replay_transport(calls)
        async def transport(req):
            if req.url.host == "inference.baseten.co":
                import httpx
                calls.append("baseten")
                return httpx.Response(402)
            return await replay(req)
        async with running(provider_settings(tmp_path), transport) as (app, services):
            response = await request(app, "/api/compare", body={"text": APPLE["claim"], "password": PASSWORD,
                                                               "providers": ["baseten", "meta"]})
            runs = data(response)["runs"]
            assert runs[0]["error"] == "credit_exhausted" and runs[1]["verdict"] == "supported"
            budget = await services.gate("budget", {})
            assert budget["providers"]["baseten"]["status"] == "credit_exhausted"
            assert budget["providers"]["meta"]["status"] == budget["status"] == "ready"
    asyncio.run(run())


def test_media_cost_charges_meta_and_exhausted_meta_prevents_preprocessing(tmp_path):
    async def run():
        calls = []
        config = example_config(tmp_path, "image")
        async with running(config, transport_for(calls)) as (app, services):
            response = await request(app, "/api/check-example", body={"example_id": "image", "password": PASSWORD})
            result = data(response)
            assert result["verdict"] == "supported"
            budget = await services.gate("budget", {})
            assert budget["providers"]["meta"]["lifetime_spent"] == pytest.approx(result["receipt"]["preprocessing"]["cost_usd"], abs=3e-9)
            assert budget["providers"]["baseten"]["lifetime_spent"] == pytest.approx(result["receipt"]["cost_usd"], abs=3e-9)
            assert budget["providers"]["fireworks"]["lifetime_spent"] == 0
            before = list(calls)
            await services.gate("credit_exhausted", {"provider": "meta"})
            blocked = await request(app, "/api/check-example", body={"example_id": "image", "password": PASSWORD})
            assert data(blocked)["error"] == "credit_exhausted" and calls == before
    asyncio.run(run())
