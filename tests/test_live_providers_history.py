"""W1 contract tests using retained transcripts, temporary SQLite and fake I/O."""
import asyncio
import copy
from dataclasses import replace
import json

import httpx
import pytest

from claimcheck.budget import Ledger
from claimcheck.providers import get_provider
from server.live import server
from test_live_check import APPLE, TRACE, fixture_sec
from test_live_examples import config as example_config, transport_for
from test_live_server import NOW, PASSWORD, TOKEN, data, request, running, settings, state
from workers.live.src.live import INSTRUCTIONS, MAX_OUTPUT, TOOLS, reservation_for, usage_cost


def provider_settings(tmp_path, **options):
    return replace(settings(tmp_path), meta_api_key="meta-marker", fireworks_api_key="fireworks-marker", **options)


def meta_response(chat, index=0):
    message = chat["choices"][0]["message"]
    usage = chat["usage"]
    return {"id": f"response-{index}", "status": "completed", "output": [
        {"type": "function_call", "call_id": call["id"], **call["function"]}
        for call in (message.get("tool_calls") or [])], "output_text": message.get("content") or "",
        "usage": {"input_tokens": usage["prompt_tokens"], "output_tokens": usage["completion_tokens"],
                  "input_tokens_details": usage.get("prompt_tokens_details", {})}}


def replay_transport(calls, *, pause=False):
    positions = {}

    async def transport(req):
        if req.url.host in {"www.sec.gov", "data.sec.gov"}:
            return httpx.Response(200, text=await fixture_sec(str(req.url)))
        provider = {"inference.baseten.co": "baseten", "api.fireworks.ai": "fireworks", "api.meta.ai": "meta"}[req.url.host]
        adapter = get_provider(provider)
        assert str(req.url) == adapter.base_url + ("/responses" if provider == "meta" else "/chat/completions")
        assert req.headers["Authorization"] == "Bearer " + {
            "baseten": "offline-api-key-marker", "fireworks": "fireworks-marker", "meta": "meta-marker"}[provider]
        payload = json.loads(req.content)
        assert payload["model"] == adapter.default_model
        assert payload["temperature"] == 0 and payload["top_p"] == 1
        assert payload["max_tokens" if adapter.chat_completions else "max_output_tokens"] == MAX_OUTPUT
        assert PASSWORD not in req.content.decode() and TOKEN not in req.content.decode()
        tools = payload.get("tools", [])
        assert {tool.get("name", tool.get("function", {}).get("name")) for tool in tools} <= {
            "lookup_fact", "list_periods", "compute_change", "history_rank"}
        if provider == "meta":
            assert "previous_response_id" not in payload
            assert "untrusted" in payload["instructions"]
            assert all(item.get("type") != "reasoning" for item in payload["input"])
        calls.append(provider)
        if pause:
            await asyncio.sleep(0)
        index = positions.get(provider, 0)
        positions[provider] = index + 1
        raw = copy.deepcopy(TRACE["requests"][index]["raw_response"])
        return httpx.Response(200, json=meta_response(raw, index) if provider == "meta" else raw)
    return transport


@pytest.mark.parametrize("provider", ["baseten", "fireworks", "meta"])
def test_fixed_provider_adapter_routing_receipt_prices_and_independent_keys(tmp_path, provider):
    async def run():
        calls = []
        config = provider_settings(tmp_path)
        if provider != "baseten":
            config = replace(config, api_key="")
        async with running(config, replay_transport(calls)) as (app, services):
            response = await request(app, body={"text": APPLE["claim"], "password": PASSWORD, "provider": provider})
            result = data(response)
            assert response.status == 200, result
            assert result["verdict"] == "supported" and calls == [provider] * 3
            receipt = result["receipt"]
            assert set(receipt) == {"provider", "model", "latency_ms", "cost_usd", "preprocessing"}
            assert receipt["provider"] == result["provider"] == provider
            assert receipt["model"] == result["model"] == get_provider(provider).default_model
            assert receipt["preprocessing"] is None
            assert receipt["cost_usd"] == pytest.approx(TRACE["cost_usd"])
            assert receipt["latency_ms"] == result["latency_ms"]
            assert result["input"] == {"kind": "text", "text_read": APPLE["claim"]}
            assert (await services.gate("budget", {}))["daily_spent_usd"] == pytest.approx(receipt["cost_usd"], abs=4e-9)
    asyncio.run(run())


@pytest.mark.parametrize("provider", [None, "", "unknown", "Meta", 1, [], {}, "__proto__"])
def test_unknown_provider_is_rejected_without_spending_or_history(tmp_path, provider):
    async def run():
        async with running(provider_settings(tmp_path)) as (app, services):
            response = await request(app, body={"text": APPLE["claim"], "password": PASSWORD, "provider": provider})
            assert response.status == 400 and data(response)["error"] == "unknown_provider"
            assert "receipt" in data(response) and "input" in data(response)
            assert not state(services).get("holds")
            assert data(await request(app, "/api/history", method="GET")) == {"rows": []}
    asyncio.run(run())


@pytest.mark.parametrize("provider", ["baseten", "fireworks", "meta"])
def test_reservation_and_usage_match_existing_provider_ledger_and_invalid_usage_keeps_hold(provider):
    adapter = get_provider(provider)
    payload = adapter.initial_request(APPLE["claim"], adapter.default_model, max_output_tokens=MAX_OUTPUT, reasoning_effort=None)
    ledger = Ledger(persist=False, provider=provider)
    reservation = ledger.estimate(payload, model=adapter.default_model, max_output_tokens=MAX_OUTPUT)
    assert reservation_for(payload, provider)["amount"] >= reservation.amount
    raw = {"input_tokens": 1500, "output_tokens": 100, "input_tokens_details": {"cached_tokens": 1000}} if provider == "meta" else {
        "prompt_tokens": 1500, "completion_tokens": 100, "prompt_tokens_details": {"cached_tokens": 1000}}
    assert usage_cost(payload, raw, provider) == ledger.reconcile(reservation, raw)
    for bad in (None, {}, {**raw, next(iter(raw)): True}, {**raw, next(iter(raw)): -1}):
        assert usage_cost(payload, bad, provider) is None


def test_example_receipt_separates_meta_preprocessing_from_selected_verifier(tmp_path):
    async def run():
        calls = []
        config = replace(example_config(tmp_path, "image"), fireworks_api_key="fireworks-marker", api_key="")
        legacy = transport_for(calls)
        async def transport(req):
            if req.url.host == "api.fireworks.ai":
                assert req.headers["Authorization"] == "Bearer fireworks-marker"
                # The recorded chat responses have the common adapter format.
                request_copy = httpx.Request("POST", "https://inference.baseten.co/v1/chat/completions", content=req.content)
                return await legacy(request_copy)
            return await legacy(req)
        async with running(config, transport) as (app, services):
            response = await request(app, "/api/check-example", body={"example_id": "image", "password": PASSWORD, "provider": "fireworks"})
            result = data(response)
            assert response.status == 200, result
            receipt = result["receipt"]
            assert receipt["provider"] == "fireworks"
            assert receipt["preprocessing"] == {k: result["input"]["preprocessing"][k] for k in ("model", "latency_ms", "cost_usd")}
            assert receipt["preprocessing"]["cost_usd"] == pytest.approx(.0003375)
            assert receipt["cost_usd"] == pytest.approx(TRACE["cost_usd"])
            assert result["cost_usd"] == pytest.approx(receipt["cost_usd"] + receipt["preprocessing"]["cost_usd"])
            assert result["latency_ms"] == pytest.approx(receipt["latency_ms"] + receipt["preprocessing"]["latency_ms"], abs=.001)
            assert (await services.gate("budget", {}))["daily_spent_usd"] == pytest.approx(result["cost_usd"], abs=4e-9)
    asyncio.run(run())


def test_compare_runs_in_requested_order_and_checks_budget_before_every_member(tmp_path):
    async def run():
        calls, budget_checks = [], []
        async with running(provider_settings(tmp_path), replay_transport(calls, pause=True)) as (app, services):
            original = services.gate
            async def gate(action, params):
                if action == "budget":
                    budget_checks.append(list(calls))
                return await original(action, params)
            services.gate = gate
            response = await request(app, "/api/compare", body={"text": APPLE["claim"], "password": PASSWORD,
                                                              "providers": ["fireworks", "meta", "baseten"]})
            result = data(response)
            assert response.status == 200
            assert [run["receipt"]["provider"] for run in result["runs"]] == ["fireworks", "meta", "baseten"]
            assert all(run["verdict"] == "supported" for run in result["runs"])
            assert calls == ["fireworks"] * 3 + ["meta"] * 3 + ["baseten"] * 3
            assert budget_checks == [[], ["fireworks"] * 3, ["fireworks"] * 3 + ["meta"] * 3]
            rows = data(await request(app, "/api/history", method="GET"))["rows"]
            assert [row["provider"] for row in rows] == ["baseten", "meta", "fireworks"]
    asyncio.run(run())


def test_compare_reuses_one_packaged_story_input_with_selected_adapters(tmp_path):
    async def run():
        config = replace(example_config(tmp_path, "pdf"), meta_api_key="meta-marker", fireworks_api_key="fireworks-marker")
        manifest = json.loads((config.examples_dir / "manifest.json").read_text())
        manifest[0]["id"] = "b-pdf"
        (config.examples_dir / "manifest.json").write_text(json.dumps(manifest))
        calls = []
        async with running(config, replay_transport(calls)) as (app, services):
            response = await request(app, "/api/compare", body={"example_id": "b-pdf", "password": PASSWORD,
                                                              "providers": ["fireworks", "meta"]})
            runs = data(response)["runs"]
            assert response.status == 200 and calls == ["fireworks"] * 3 + ["meta"] * 3
            assert [run["receipt"]["provider"] for run in runs] == ["fireworks", "meta"]
            for result in runs:
                assert result["input"]["example_id"] == "b-pdf" and result["input"]["story"] == "b"
                assert " ".join(result["input"]["text_read"].split()) == APPLE["claim"]
                assert result["receipt"]["preprocessing"]["model"] == "native-pdf"
                assert result["receipt"]["preprocessing"]["cost_usd"] == 0
            assert len((await services.ledger.history())["rows"]) == 2
    asyncio.run(run())


@pytest.mark.parametrize("body", [
    {"text": "Apple FY2025 revenue $416.2B", "providers": ["meta"]},
    {"text": "Apple FY2025 revenue $416.2B", "providers": ["meta", "meta"]},
    {"text": "Apple FY2025 revenue $416.2B", "providers": ["meta", "unknown"]},
    {"text": "Apple FY2025 revenue $416.2B", "providers": ["meta", {}]},
    {"text": "Apple FY2025 revenue $416.2B", "providers": ["meta", "baseten"], "model": "custom"},
    {"text": "Apple FY2025 revenue $416.2B", "example_id": "a-text", "providers": ["meta", "baseten"]},
])
def test_origin_compare_rejects_invalid_members_or_extra_fields_without_history_or_spend(tmp_path, body):
    async def run():
        async with running(provider_settings(tmp_path)) as (app, services):
            response = await request(app, "/api/compare", body={**body, "password": PASSWORD})
            assert response.status == 400
            assert not state(services).get("holds")
            assert await services.ledger.history() == {"rows": []}
    asyncio.run(run())


def test_compare_retains_every_member_after_global_reservation_failure(tmp_path):
    async def run():
        calls = []
        holds = []
        for name in ("baseten", "fireworks"):
            adapter = get_provider(name)
            payload = adapter.initial_request(APPLE["claim"], adapter.default_model, max_output_tokens=MAX_OUTPUT, reasoning_effort=None)
            payload["messages"][0]["content"] = INSTRUCTIONS
            payload.update(tools=TOOLS, parallel_tool_calls=False, temperature=0, top_p=1)
            holds.append(reservation_for(payload, name)["amount"])
        def transport(req):
            calls.append(req.url.host)
            raw = copy.deepcopy(TRACE["requests"][-1]["raw_response"])
            raw["usage"] = {"prompt_tokens": 1000, "completion_tokens": 100}
            return httpx.Response(200, json=raw)
        async with running(provider_settings(tmp_path, daily_budget=str(max(holds) + .000000001)), transport) as (app, services):
            response = await request(app, "/api/compare", body={"text": APPLE["claim"], "password": PASSWORD,
                                                              "providers": ["baseten", "fireworks", "meta"]})
            result = data(response)
            assert response.status == 200, result
            assert len(result["runs"]) == 3
            assert result["runs"][1]["error"] == "budget_exhausted"
            assert result["runs"][1]["receipt"]["cost_usd"] == 0
            assert calls == ["inference.baseten.co"]
            assert len(data(await request(app, "/api/history", method="GET"))["rows"]) == 3
            assert all(row["settled"] for row in state(services)["holds"].values())
    asyncio.run(run())


@pytest.mark.parametrize("stop", ["daily", "lifetime", "credit"])
def test_compare_global_stop_labels_every_member_without_paid_calls(tmp_path, stop):
    async def run():
        config = provider_settings(tmp_path, **({"daily_budget": "0"} if stop == "daily" else {"total_budget": "0"} if stop == "lifetime" else {}))
        async with running(config) as (app, services):
            if stop == "credit":
                await services.gate("credit_exhausted", {})
            response = await request(app, "/api/compare", body={"text": APPLE["claim"], "password": PASSWORD,
                                                              "providers": ["baseten", "meta"]})
            runs = data(response)["runs"]
            assert len(runs) == 2 and all(run["error"] == runs[0]["error"] for run in runs) and runs[0]["error"] in {"budget_exhausted", "total_budget_exhausted", "credit_exhausted"}
            assert not state(services).get("holds")
    asyncio.run(run())


def test_history_masks_metadata_survives_restart_and_roundtrips_hostile_input_as_data(tmp_path, caplog, capsys):
    text = '\"><script>alert(1)</script> Apple revenue was $109.4B in fiscal Q3 2026; DROP TABLE history; --'
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
    async def run():
        config = provider_settings(tmp_path)
        async with running(config, replay_transport([])) as (app, services):
            assert (await request(app, body={"text": text, "password": "wrong"})).status == 401
            assert data(await request(app, "/api/history", method="GET")) == {"rows": []}
            response = await request(app, body={"text": text, "password": PASSWORD}, headers={"User-Agent": ua})
            assert response.status == 200
            row, = data(await request(app, "/api/history?limit=1", method="GET"))["rows"]
            assert row["input_text"] == text and row["browser"] == "Edge" and row["device"] == "Windows / desktop"
            assert row["ip_masked"].startswith("192.0.*.*#") and len(row["ip_masked"].split("#")[1]) == 8
            detail = await request(app, "/api/history/" + row["id"], method="GET")
            assert detail.headers["Cache-Control"] == "no-store"
            assert data(detail) == {**row, "envelope": data(response)}
            dumped = " ".join(str(x) for x in services.ledger.db.iterdump())
            for private in (ua, "192.0.2.1", PASSWORD, TOKEN, "reasoning_content", "meta-marker", "fireworks-marker"):
                assert private not in dumped
                assert private not in detail.text
            marker = row["ip_masked"]
            record_id = row["id"]
        async with running(config) as (app, services):
            assert data(await request(app, "/api/history/" + record_id, method="GET"))["input_text"] == text
            assert server.masked_ip("192.0.2.1", services.ledger.history_salt) == marker
    asyncio.run(run())
    assert not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize("path", ["?limit=0", "?limit=51", "?limit=-1", "?limit=1.0", "?limit=1&limit=2", "?private=1", "/../history", "/bad-id", "/" + "a" * 32 + "?limit=1"])
def test_history_limits_and_id_validation_do_not_query_arbitrary_data(tmp_path, path):
    async def run():
        async with running(settings(tmp_path)) as (app, _):
            response = await request(app, "/api/history" + path, method="GET")
            assert response.status in {400, 404}
    asyncio.run(run())


def test_history_14_day_retention_and_5000_row_limit_share_existing_periodic_prune(tmp_path):
    async def run():
        now = [NOW]
        async with running(settings(tmp_path), clock=lambda: now[0]) as (app, services):
            db = services.ledger.db
            db.executemany("INSERT INTO history(id, created_at, body, envelope) VALUES (?, ?, ?, ?)",
                [(f"{i:032x}", NOW + i / 10000, "{}", "{}") for i in range(5002)])
            await services.prune()
            assert db.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 5000
            assert db.execute("SELECT id FROM history ORDER BY created_at LIMIT 1").fetchone()[0] == f"{2:032x}"
            now[0] += server.HISTORY_TTL + 1
            assert data(await request(app, "/api/history", method="GET")) == {"rows": []}
            assert (await request(app, "/api/history/" + f"{5001:032x}", method="GET")).status == 404
            await services.prune()
            assert db.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 0
    asyncio.run(run())


def test_long_partial_history_envelope_is_bounded_and_marked_without_losing_receipt(tmp_path):
    async def run():
        async with running(settings(tmp_path)) as (_, services):
            run = server.LiveRun(services.model, services.sec, services.gate)
            run.input_info["text_read"] = "hostile " + "字" * 599
            run.events = [{"kind": "tool_result", "result": "x" * 100_000}]
            result = run.envelope(error="provider_error")
            record_id = await services.ledger.record(result, "2001:db8:abcd:1234::1", "iPad Version/17 Safari/123")
            row = await services.ledger.history(record_id=record_id)
            assert row["envelope"]["history_truncated"] is True
            assert row["envelope"]["receipt"] == result["receipt"]
            assert len(row["input_text"]) == 600
            assert row["ip_masked"].startswith("2001:0db8:*#")
            assert row["browser"] == "Safari" and row["device"] == "iPadOS / tablet"
            assert services.ledger.db.execute("SELECT length(CAST(envelope AS BLOB)) FROM history").fetchone()[0] <= 65536
    asyncio.run(run())


def test_history_keeps_original_correction_count_when_large_unicode_result_needs_truncation(tmp_path):
    async def run():
        async with running(settings(tmp_path)) as (_, services):
            run = server.LiveRun(services.model, services.sec, services.gate)
            run.input_info["text_read"] = "字" * 12000
            result = run.envelope(verdict="contradicted", corrections={"original_text": "字" * 12000,
                                                                     "edits": [{"replacement": "1"}]})
            record_id = await services.ledger.record(result, None, "")
            row = await services.ledger.history(record_id=record_id)
            assert row["corrections_count"] == 1 and row["ip_masked"] == "unknown"
            assert row["envelope"]["history_truncated"] is True
            assert "corrections" not in row["envelope"]
            assert row["envelope"]["input"]["text_read"] == row["input_text"] == "字" * 600
            assert row["envelope"]["receipt"] == result["receipt"]
            assert services.ledger.db.execute("SELECT length(CAST(envelope AS BLOB)) FROM history").fetchone()[0] <= 65536
    asyncio.run(run())


@pytest.mark.parametrize("ua,device,browser", [
    ("iPhone CriOS/100 Mobile/1 Safari/123", "iOS / mobile", "Chrome"),
    ("Android Mobile EdgA/120", "Android / mobile", "Edge"),
    ("Android SamsungBrowser/12 Chrome/90", "Android / tablet", "Samsung Internet"),
    ("Macintosh Version/17 Safari/1", "macOS / desktop", "Safari"),
    ("X11; CrOS Chrome/100", "ChromeOS / desktop", "Chrome"),
    ("X11; Linux Firefox/120", "Linux / desktop", "Firefox"),
    ("<script>raw hostile UA</script>", "Unknown / unknown", "Other")])
def test_small_deterministic_ua_parser(ua, device, browser):
    assert server.parse_user_agent(ua) == (device, browser)


def test_three_story_example_ids_are_packaged_hash_checked_and_path_safe(tmp_path):
    config = example_config(tmp_path)
    folder = config.examples_dir
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest[0]["id"] = "b-text"
    manifest[0]["story"] = "b"
    (folder / "manifest.json").write_text(json.dumps(manifest))
    assert server.load_example(folder, "b-text") == (folder / "post.txt", "text")
    manifest[0]["file"] = "../outside.txt"
    (folder / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(server.LiveError, match="example_unavailable"):
        server.load_example(folder, "b-text")
