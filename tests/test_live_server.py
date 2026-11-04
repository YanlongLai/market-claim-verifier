"""Self-hosted HTTP/SQLite adapter tests: fake transports, no network sockets."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
import json
import os
import time
from types import SimpleNamespace

from aiohttp import StreamReader
from aiohttp.test_utils import make_mocked_request
import httpx
import pytest

from server.live import server
from test_live_check import APPLE, TRACE, fixture_sec

TOKEN = "offline-origin-token-marker"
PASSWORD = "offline-password-marker"
NOW = 1793635200


def settings(tmp_path, **options):
    return server.Settings(tmp_path, "offline-api-key-marker", PASSWORD, TOKEN, **options)


def no_network(request):
    pytest.fail("unexpected outbound I/O")


@asynccontextmanager
async def running(config, transport=no_network, clock=lambda: NOW):
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport), trust_env=False) as client:
        app = server.create_app(config, client=client, clock=clock)
        app.on_startup.freeze()
        await app.startup()
        app.freeze()
        try:
            yield app, app[server.SERVICES]
        finally:
            await app.cleanup()


async def request(app, path="/api/check", *, method="POST", body=None, raw=None, token=TOKEN, ip="192.0.2.1", headers=None):
    fields = {"X-Live-Origin-Token": token, "Content-Type": "application/json", **(headers or {})}
    if token is None:
        fields.pop("X-Live-Origin-Token")
    if ip is not None:
        fields["X-Live-Client-IP"] = ip
    payload = StreamReader(SimpleNamespace(_reading_paused=False), 4096)
    if raw is None:
        raw = json.dumps(body if body is not None else {"text": APPLE["claim"], "password": PASSWORD}).encode()
    payload.feed_data(raw)
    payload.feed_eof()
    req = make_mocked_request(method, path, headers=fields, payload=payload, app=app)
    return await app._handle(req)


def data(response):
    return json.loads(response.text)


def state(services):
    return json.loads(services.ledger.db.execute("SELECT body FROM ledger WHERE id = 1").fetchone()[0])


def test_replay_through_real_http_adapter_preserves_python_verdict_cost_and_privacy(tmp_path, capsys, caplog):
    async def run():
        responses = iter(TRACE["requests"])
        async def transport(req):
            assert req.extensions["timeout"] == dict.fromkeys(("connect", "read", "write", "pool"), 22)
            if req.url.host == "inference.baseten.co":
                assert req.headers["Authorization"] == "Bearer offline-api-key-marker"
                payload = json.loads(req.content)
                assert payload["model"] == "meta-models/muse-spark-open-1026"
                assert "password" not in payload and PASSWORD not in req.content.decode()
                assert "X-Live-Origin-Token" not in req.headers
                return httpx.Response(200, json=next(responses)["raw_response"])
            assert req.url.host in {"www.sec.gov", "data.sec.gov"}
            assert req.headers["User-Agent"] == server.SEC_AGENT
            assert "Authorization" not in req.headers
            return httpx.Response(200, text=await fixture_sec(str(req.url)))
        async with running(settings(tmp_path), transport) as (app, services):
            response = await request(app)
            result = data(response)
            assert response.status == 200 and response.headers["Cache-Control"] == "no-store"
            assert result["verdict"] == "supported"
            assert result["claims"][0]["actual_value"] == 109417000000
            assert result["cost_usd"] == pytest.approx(TRACE["cost_usd"])
            assert (await services.gate("budget", {}))["daily_spent_usd"] == pytest.approx(TRACE["cost_usd"], abs=3e-9)
            stored = json.dumps(state(services))
            # Public history now retains the original and corrected draft;
            # spending state must still contain no post or credentials.
            assert APPLE["claim"] not in stored
            assert result["corrections"]["original_text"] == APPLE["claim"]
            assert result["corrections"]["edits"] == []
            for private in (PASSWORD, TOKEN, services.settings.api_key, "192.0.2.1", "reasoning_content"):
                assert private not in stored
                assert private not in response.text
            assert services.ledger.db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert services.ledger.db.execute("PRAGMA synchronous").fetchone()[0] == 2
    asyncio.run(run())
    assert not capsys.readouterr().out and not caplog.text


def test_budget_math_daily_stop_and_utc_rollover(tmp_path):
    async def run():
        now = [NOW]
        async with running(settings(tmp_path), clock=lambda: now[0]) as (app, services):
            await services.gate("reserve", {"id": "a", "amount": .59})
            response = await request(app, "/api/budget", method="GET")
            assert response.status == 200
            assert data(response)["daily_remaining_usd"] == 2.41
            assert response.headers["Cache-Control"].endswith("s-maxage=5, must-revalidate")
            await services.gate("settle", {"id": "a", "amount": .02})
            await services.gate("settle", {"id": "a", "amount": .02})
            assert (await services.gate("budget", {}))["daily_remaining_usd"] == 2.98
            await services.gate("reserve", {"id": "b", "amount": 2.98})
            response = await request(app)
            assert response.status == 429 and data(response)["error"] == "budget_exhausted"
            assert data(response)["budget"]["daily_remaining_usd"] == 0
            now[0] += 86400
            assert (await services.gate("budget", {}))["daily_remaining_usd"] == 3
            assert state(services)["lifetime_nanos"] == 3_000_000_000
    asyncio.run(run())


def test_twenty_dollar_lifetime_stop_survives_restart_prune_and_reset_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_RESET_ID", "must-be-ignored")
    async def run():
        now = [NOW]
        config = settings(tmp_path)
        async with running(config, clock=lambda: now[0]) as (_, services):
            for day in range(7):
                now[0] = NOW + day * 86400
                await services.gate("reserve", {"id": str(day), "amount": 3 if day < 6 else 2})
            assert state(services)["lifetime_nanos"] == 20_000_000_000
        now[0] += 10 * 86400
        async with running(config, clock=lambda: now[0]) as (app, services):
            await services.prune()
            assert state(services)["days"] == state(services)["holds"] == {}
            assert state(services)["lifetime_nanos"] == 20_000_000_000
            response = await request(app)
            assert response.status == 503 and data(response)["error"] == "total_budget_exhausted"
            assert data(await request(app, "/api/budget", method="GET"))["status"] == "total_budget_exhausted"
    asyncio.run(run())


@pytest.mark.parametrize("daily,total,amount,count,accepted", [("3", "20", .03, 250, 100), ("100", "20", .3, 100, 66)])
def test_parallel_reservations_and_restart_never_exceed_either_budget(tmp_path, daily, total, amount, count, accepted):
    async def run():
        config = settings(tmp_path, daily_budget=daily, total_budget=total)
        async with running(config) as (_, services):
            async def reserve(i):
                await asyncio.sleep(0)
                try:
                    await services.gate("reserve", {"id": str(i), "amount": amount})
                    return True
                except server.LiveError as error:
                    assert error.code in {"budget_exhausted", "total_budget_exhausted"}
                    return False
            assert sum(await asyncio.gather(*(reserve(i) for i in range(count)))) == accepted
            saved = state(services)
            assert saved["lifetime_nanos"] <= int(float(total) * 1e9)
            assert sum(r["amount_nanos"] for r in saved["days"].values()) <= int(float(daily) * 1e9)
        async with running(config) as (_, services):
            assert state(services) == saved
            assert len(state(services)["holds"]) == accepted
    asyncio.run(run())


def test_transaction_rolls_back_failed_transition(tmp_path, monkeypatch):
    async def run():
        async with running(settings(tmp_path)) as (_, services):
            await services.gate("reserve", {"id": "saved", "amount": .1})
            saved = state(services)
            def broken(state, *args, **kwargs):
                state["lifetime_nanos"] = 0
                raise ValueError("synthetic failure")
            monkeypatch.setattr(server, "transition", broken)
            with pytest.raises(ValueError):
                await services.gate("reserve", {"id": "failed", "amount": 1})
            assert state(services) == saved and not services.ledger.db.in_transaction
    asyncio.run(run())


def test_402_unreadable_body_stops_future_calls_and_persists(tmp_path, capsys, caplog):
    class BrokenBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            pytest.fail("402 body must never be read")
            yield b""
    async def run():
        calls = []
        def transport(req):
            calls.append(req)
            return httpx.Response(402, stream=BrokenBody())
        config = settings(tmp_path)
        async with running(config, transport) as (app, services):
            response = await request(app)
            assert response.status == 503 and data(response)["error"] == "credit_exhausted"
            assert data(response)["cost_is_bound"] is True
            assert state(services)["lifetime_nanos"] > 0
        async with running(config, transport) as (app, services):
            assert data(await request(app))["error"] == "credit_exhausted"
            assert data(await request(app, "/api/budget", method="GET"))["status"] == "credit_exhausted"
        assert len(calls) == 1
    asyncio.run(run())
    assert not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize("status,body,expected", [(403, "insufficient credits private-account-detail", "credit_exhausted"),
    (429, "quota exhausted private-account-detail", "credit_exhausted"), (403, "invalid key private-account-detail", "provider_error"),
    (429, "rate limit private-account-detail", "provider_error")])
def test_baseten_error_shapes_are_redacted_without_false_credit_stops(tmp_path, status, body, expected):
    async def run():
        async with running(settings(tmp_path), lambda _: httpx.Response(status, text=body)) as (app, services):
            response = await request(app)
            assert response.status == 503 and data(response)["error"] == expected
            assert "private-account-detail" not in response.text
            assert bool(state(services).get("credit_exhausted")) == (expected == "credit_exhausted")
    asyncio.run(run())


@pytest.mark.parametrize("attempted,configured,expected", [(None, PASSWORD, 401), ("wrong", PASSWORD, 401), (PASSWORD, "", 503)])
def test_missing_wrong_or_unconfigured_password_never_reserves(tmp_path, attempted, configured, expected):
    async def run():
        async with running(replace(settings(tmp_path), password=configured)) as (app, services):
            response = await request(app, body={"text": APPLE["claim"], "password": attempted})
            assert response.status == expected
            assert not {"holds", "days", "lifetime_nanos", "rates"} & state(services).keys()
    asyncio.run(run())


def test_origin_auth_covers_health_budget_unknown_routes_and_uses_fixed_size_comparison(tmp_path, monkeypatch):
    real_compare, comparisons = server.hmac.compare_digest, []
    def compare(left, right):
        comparisons.append((left, right))
        assert isinstance(left, bytes) and len(left) == len(right) == 32
        return real_compare(left, right)
    monkeypatch.setattr(server.hmac, "compare_digest", compare)
    async def run():
        async with running(settings(tmp_path)) as (app, services):
            for path in ("/api/check", "/api/check-example", "/api/budget", "/healthz", "/unknown"):
                for token, expected in ((None, 401), ("wrong", 403)):
                    response = await request(app, path, method="GET", token=token)
                    assert response.status == expected and data(response)["error"] == "origin_rejected"
            assert services.ledger.db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 0
            assert data(await request(app, "/healthz", method="GET")) == {"ok": True}
            assert (await request(app, "/unknown", method="GET")).status == 404
            assert (await request(app, "/api/check", method="GET")).status == 404
    asyncio.run(run())
    assert len(comparisons) == 13


def test_client_ip_only_comes_from_origin_header_and_auth_lockout_survives_restart(tmp_path):
    async def run():
        config = settings(tmp_path)
        async with running(config) as (app, _):
            response = await request(app, ip=None, headers={"CF-Connecting-IP": "192.0.2.1", "X-Forwarded-For": "192.0.2.1"})
            assert response.status == 503
            for _ in range(5):
                assert (await request(app, body={"text": APPLE["claim"], "password": "wrong"})).status == 401
        async with running(config) as (app, _):
            response = await request(app)
            assert response.status == 429 and data(response)["error"] == "auth_rate_limited"
    asyncio.run(run())


@pytest.mark.parametrize("raw", [b"{", b"[]", b"null", b"\xff", b'{}' + b' ' * 4095,
    json.dumps({"text": "x" * 601, "password": PASSWORD}).encode()])
def test_malformed_or_oversized_bodies_are_400_without_outbound_io(tmp_path, raw):
    async def run():
        async with running(settings(tmp_path)) as (app, _):
            response = await request(app, raw=raw)
            assert response.status == 400 and data(response)["error"] == "invalid_input"
    asyncio.run(run())


def test_out_of_scope_and_missing_key_fail_closed(tmp_path):
    async def run():
        for config, text, status in [(settings(tmp_path), "Bitcoin is up", 422),
                                     (replace(settings(tmp_path), api_key=""), APPLE["claim"], 503)]:
            async with running(config) as (app, services):
                assert (await request(app, body={"text": text, "password": PASSWORD})).status == status
                assert not state(services).get("holds")
    asyncio.run(run())


def test_sec_allowlist_redirect_rejection_and_six_hour_memory_disk_cache(tmp_path):
    async def run():
        now, calls = [time.time()], []
        def transport(req):
            calls.append(str(req.url))
            if req.url.path == "/redirect":
                return httpx.Response(302, headers={"Location": "https://evil.example/private"})
            if req.url.path == "/html":
                return httpx.Response(200, text="<html>not JSON</html>")
            return httpx.Response(200, json={"ok": True})
        config = settings(tmp_path)
        url = "https://www.sec.gov/files/company_tickers.json"
        async with running(config, transport, clock=lambda: now[0]) as (_, services):
            for bad in ("https://evil.example/x", "http://www.sec.gov/x", "https://www.sec.gov:443/x", "https://www.sec.gov@evil.example/x"):
                with pytest.raises(server.LiveError, match="sec_unavailable"):
                    await services.sec(bad)
            assert calls == []
            assert await services.sec(url) == await services.sec(url)
            assert len(calls) == 1
            for path in ("redirect", "html"):
                with pytest.raises(server.LiveError, match="sec_unavailable"):
                    await services.sec("https://data.sec.gov/" + path)
            assert len(list(services.cache_dir.glob("*.json"))) == 1
        async with running(config, transport, clock=lambda: now[0]) as (_, services):
            assert json.loads(await services.sec(url)) == {"ok": True}
            assert len(calls) == 3  # Disk cache survived restart.
            now[0] += server.TTL + 1
            await services.prune()
            assert not services.cache and not list(services.cache_dir.glob("*.json"))
            await services.sec(url)
            assert len(calls) == 4
    asyncio.run(run())


def test_overall_timeout_keeps_reservation_and_returns_same_504_shape(tmp_path, monkeypatch):
    timeout = asyncio.timeout
    monkeypatch.setattr(server.asyncio, "timeout", lambda seconds: timeout(.01 if seconds == 55 else seconds))
    async def transport(req):
        await asyncio.Event().wait()
    async def run():
        async with running(settings(tmp_path), transport) as (app, services):
            response = await request(app)
            assert response.status == 504 and data(response)["error"] == "timeout"
            assert data(response)["cost_is_bound"] is True
            assert not next(iter(state(services)["holds"].values()))["settled"]
    asyncio.run(run())


def test_env_and_file_secrets_have_defaults_without_reading_host_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "environ", {})
    assert server.Settings.from_env() == server.Settings()
    for name in ("BASETEN_API_KEY", "LIVE_CHECK_PASSWORD", "LIVE_ORIGIN_TOKEN", "META_MODEL_API_KEY", "FIREWORKS_API_KEY"):
        path = tmp_path / name
        path.write_text("file-marker\n")
        monkeypatch.setenv(name + "_FILE", str(path))
    config = server.Settings.from_env()
    assert config.api_key == config.password == config.origin_token == config.meta_api_key == config.fireworks_api_key == "file-marker"
    monkeypatch.setenv("LIVE_CHECK_PASSWORD", "")
    assert server.Settings.from_env().password == ""
    monkeypatch.setenv("LIVE_ORIGIN_TOKEN_FILE", str(tmp_path / "missing"))
    with pytest.raises(OSError):
        server.Settings.from_env()
