"""Progress and abuse regressions: fake clock/transports, no paid work."""
import asyncio
import json
from uuid import uuid4

import pytest

from workers.live.src.gate import transition
from server.live.progress import MAX_BUFFERS, ProgressBuffer, member_id
from test_live_server import APPLE, PASSWORD, data, request, running, server, settings, state


def gate(state, action, now=1000, **data):
    return transition(state, action, data, now=now, budget="3", password_secret=PASSWORD)


def test_progress_ttl_cursor_bound_and_allowlist_redact_all_sensitive_fields():
    now = [1000]
    buffer = ProgressBuffer(lambda: now[0])
    run_id = str(uuid4())
    assert buffer.create(run_id)
    assert not buffer.create(run_id)
    assert buffer.read(str(uuid4())) is None
    for index in range(210):
        buffer.event(run_id, index / 10, "tool_call", {
            "name": "lookup_fact", "password": PASSWORD, "text": "private input", "ip": "192.0.2.1",
            "arguments": {"ticker": "AMZN", "metric": "revenue", "period": "2023Q3", "text": "private input"}}, (PASSWORD, "AMZN"))
    value = buffer.read(run_id)
    assert len(value["lines"]) == 200 and value["next"] == 210 and value["done"] is False
    assert value["lines"][0]["t_s"] == 1
    assert len(buffer.read(run_id, 208)["lines"]) == 2
    assert buffer.read(run_id, 210)["lines"] == []
    encoded = json.dumps(value)
    assert all(secret not in encoded for secret in (PASSWORD, "private input", "192.0.2.1", "AMZN"))
    assert "lookup_fact" in encoded and "revenue" in encoded
    buffer.finish(run_id)
    buffer.event(run_id, 30, "error", {"code": "timeout"})
    assert buffer.read(run_id)["next"] == 210 and buffer.read(run_id)["done"]
    now[0] += 299
    assert buffer.read(run_id)
    now[0] += 1
    assert buffer.read(run_id) is None
    for _ in range(MAX_BUFFERS):
        assert buffer.create(str(uuid4()))
    assert not buffer.create(str(uuid4()))


def test_lockout_uses_rolling_fifteen_minutes_and_lasts_thirty():
    saved = {}
    # Expire only the first attempt, not the later failures in its old window.
    for at in (1000, 1800, 1850, 1899):
        assert gate(saved, "authenticate", now=at, ip="one", password="wrong")[1] == 401
    assert gate(saved, "authenticate", now=1900, ip="one", password="wrong")[1] == 401
    assert gate(saved, "authenticate", now=1901, ip="one", password="wrong") == ({"error": "locked", "retry_after": 1800}, 429)
    assert gate(saved, "authenticate", now=3700, ip="one", password=PASSWORD)[1] == 429
    assert gate(saved, "authenticate", now=3701, ip="one", password=PASSWORD)[1] == 200
    assert not saved.get("holds")


def test_global_twenty_and_ip_five_are_atomic_and_rejected_runs_do_not_count():
    saved = {}
    for index in range(20):
        assert gate(saved, "rate", ip=f"ip-{index // 5}")[1] == 200
    assert gate(saved, "rate", ip="new") == ({"error": "busy"}, 429)
    assert gate(saved, "rate", ip="ip-0")[0]["error"] == "rate_limited"
    assert len(saved["site_runs"]) == 20
    assert all(raw not in json.dumps(saved) for raw in ("ip-0", "new"))
    assert gate(saved, "rate", now=1600, ip="new")[1] == 200


def test_burst_rolling_window_and_fixed_ten_minute_block_survive_serialization():
    saved = {}
    for index in range(30):
        assert gate(saved, "burst", now=1000 + index, ip="one")[1] == 200
    assert gate(saved, "burst", now=1030, ip="one") == ({"error": "slow_down"}, 429)
    saved = json.loads(json.dumps(saved))
    assert gate(saved, "burst", now=1629, ip="one")[1] == 429
    assert gate(saved, "burst", now=1031, ip="two")[1] == 200
    assert gate(saved, "burst", now=1630, ip="one")[1] == 200
    assert not saved.get("holds") and not saved["site_runs"]


def test_progress_endpoint_while_post_in_flight_then_done_expiry_and_redaction(tmp_path, monkeypatch):
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        now = [1000]
        async def bounded(self, claim):
            self.log("model", step=1, phase="running")
            self.log("tool_call", name="lookup_fact", arguments={"ticker": "AMZN", "metric": "revenue", "period": "2023Q3", "text": claim})
            entered.set()
            await release.wait()
            self.log("model", step=1, phase="completed", cost_usd=.01)
            self.log("tool_result", result={"evidence_id": "E1", "value": 143100000000, "unit": "USD", "form": "10-Q"})
            self.log("program_check", check={"text": claim})
            self.log("verdict", verdict="supported", cost_usd=.01)
            return self.envelope(verdict="supported")
        monkeypatch.setattr(server.LiveRun, "bounded", bounded)
        async with running(settings(tmp_path), clock=lambda: now[0]) as (app, services):
            run_id = str(uuid4())
            path = f"/api/progress/{run_id}"
            assert (await request(app, path, method="GET")).status == 404
            bad = await request(app, body={"text": APPLE["claim"], "password": "wrong", "client_run_id": run_id})
            assert bad.status == 401 and not services.progress.runs
            post = asyncio.create_task(request(app, body={"text": APPLE["claim"], "password": PASSWORD, "client_run_id": run_id}))
            await entered.wait()
            snapshot = data(await request(app, path + "?after=0", method="GET"))
            assert set(snapshot) == {"lines", "done", "next"}
            assert snapshot["done"] is False and len(snapshot["lines"]) == 3
            assert set(snapshot["lines"][0]) == {"t_s", "text"}
            release.set()
            assert (await post).status == 200
            snapshot2 = data(await request(app, path + f'?after={snapshot["next"]}', method="GET"))
            assert snapshot2["done"] and len(snapshot2["lines"]) == 4
            assert "duration=" in snapshot2["lines"][-1]["text"]
            encoded = json.dumps([snapshot, snapshot2])
            assert all(private not in encoded for private in (PASSWORD, APPLE["claim"], "192.0.2.1"))
            assert services.in_flight == 0
            assert (await request(app, body={"text": APPLE["claim"], "password": PASSWORD, "client_run_id": run_id})).status == 400
            for suffix in ("?after=-1", "?after=1&after=2", "?unknown=1"):
                assert (await request(app, path + suffix, method="GET")).status == 400
            now[0] += 300
            assert (await request(app, path, method="GET")).status == 404
    asyncio.run(run())


def test_concurrency_no_queue_release_on_failure_and_compare_member_counts(tmp_path, monkeypatch):
    async def run():
        release = asyncio.Event()
        async def bounded(self, claim):
            await release.wait()
            raise server.LiveError("provider_error")
        monkeypatch.setattr(server.LiveRun, "bounded", bounded)
        async with running(settings(tmp_path)) as (app, services):
            one = asyncio.create_task(request(app, ip="192.0.2.1"))
            two = asyncio.create_task(request(app, ip="192.0.2.2"))
            while services.in_flight < 2:
                await asyncio.sleep(0)
            rejected = await request(app, ip="192.0.2.3")
            assert rejected.status == 429 and data(rejected)["error"] == "busy"
            assert len(state(services)["site_runs"]) == 2
            release.set()
            assert all(response.status == 503 for response in await asyncio.gather(one, two))
            assert services.in_flight == 0
            services.settings = settings(tmp_path, meta_api_key="offline-meta", fireworks_api_key="offline-fireworks")
            run_id = str(uuid4())
            compared = await request(app, "/api/compare", ip="192.0.2.4", body={"text": APPLE["claim"], "password": PASSWORD,
                "providers": ["baseten", "meta", "fireworks"], "client_run_id": run_id})
            assert len(data(compared)["runs"]) == 3
            assert len(state(services)["site_runs"]) == 5
            assert all(services.progress.read(member_id(run_id, index))["done"] for index in range(3))
    asyncio.run(run())


@pytest.mark.parametrize("path,method", [("/api/budget", "GET"), ("/api/history", "GET"),
    ("/api/progress/" + str(uuid4()), "GET"), ("/api/unknown", "POST"), ("/api/check", "POST")])
def test_all_api_routes_burst_block_before_auth_or_paid_work(tmp_path, path, method):
    async def run():
        now = [1000]
        async with running(settings(tmp_path), clock=lambda: now[0]) as (app, services):
            for _ in range(30):
                assert (await request(app, "/api/budget", method="GET")).status == 200
            response = await request(app, path, method=method)
            assert response.status == 429 and data(response) == {"error": "slow_down"}
            assert not state(services)["holds"]
            assert (await request(app, "/api/budget", method="GET", ip="192.0.2.2")).status == 200
            now[0] += 600
            assert (await request(app, "/api/budget", method="GET")).status == 200
    asyncio.run(run())


def test_cancellation_releases_concurrency_and_finishes_buffer(tmp_path, monkeypatch):
    async def run():
        entered = asyncio.Event()
        async def bounded(self, claim):
            entered.set()
            await asyncio.Event().wait()
        monkeypatch.setattr(server.LiveRun, "bounded", bounded)
        async with running(settings(tmp_path)) as (app, services):
            run_id = str(uuid4())
            post = asyncio.create_task(request(app, body={"text": APPLE["claim"], "password": PASSWORD, "client_run_id": run_id}))
            await entered.wait()
            assert services.in_flight == 1
            post.cancel()
            with pytest.raises(asyncio.CancelledError):
                await post
            assert services.in_flight == 0
            assert services.progress.read(run_id)["done"]
            assert "timeout" in services.progress.read(run_id)["lines"][-1]["text"]
    asyncio.run(run())


def test_history_summary_reads_legacy_errors_locally_without_detail_requests(tmp_path):
    async def run():
        config = settings(tmp_path)
        # A real failed origin attempt records its existing envelope; no API key.
        config = server.Settings(data_dir=tmp_path, password=PASSWORD, origin_token=config.origin_token)
        async with running(config) as (app, services):
            assert (await request(app)).status == 503
            body, envelope = services.ledger.db.execute("SELECT body, envelope FROM history").fetchone()
            assert "error" not in json.loads(body)
            assert json.loads(envelope)["error"] == "unavailable"
        async with running(config) as (app, _):
            rows = data(await request(app, "/api/history", method="GET"))["rows"]
            assert len(rows) == 1 and rows[0]["error"] == "unavailable"
    asyncio.run(run())
