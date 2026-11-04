"""Packaged example route: real ingest/core, injected Meta/SEC transports only."""
import asyncio
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import threading
import wave

import httpx
import pytest

from claimcheck import ingest_media
from scripts.build_examples import post_pdf
from server.live import server
from test_live_server import PASSWORD, TOKEN, data, request, running, settings, state
from test_live_check import APPLE, TRACE, fixture_sec

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "docs/examples/post.png"


def config(tmp_path, kind="text", **options):
    folder = tmp_path / "examples"
    folder.mkdir(parents=True, exist_ok=True)
    content = {"text": APPLE["claim"].encode(), "pdf": post_pdf(APPLE["claim"]),
               "image": IMAGE.read_bytes(), "audio": b"offline audio fixture", "video": b"offline video fixture"}[kind]
    filename = server.EXAMPLES[kind]
    (folder / filename).write_bytes(content)
    (folder / "manifest.json").write_text(json.dumps([{"id": kind, "kind": kind, "status": "ready", "file": filename,
        "size_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}]))
    return replace(settings(tmp_path), examples_dir=folder, meta_api_key="offline-meta-key", **options)


async def example_request(app, kind="text", password=PASSWORD, **more):
    return await request(app, "/api/check-example", body={"example_id": kind, "password": password}, **more)


def transport_for(calls, *, ocr_text=APPLE["claim"], usage=True, media_status=200):
    responses = iter(TRACE["requests"])

    async def transport(req):
        calls.append(req)
        if req.url.host == "api.meta.ai":
            assert req.headers["Authorization"] == "Bearer offline-meta-key"
            assert PASSWORD not in req.content.decode(errors="replace")
            if media_status != 200:
                return httpx.Response(media_status, json={"error": "offline failure"})
            if req.url.path.endswith("/asr/transcribe"):
                assert b"muse-voice-transcribe-1.0" in req.content
                assert b"RIFF" in req.content and b"DIARIZATION" in req.content
                return httpx.Response(200, json={"turns": [{"transcript": APPLE["claim"], "startMs": 0, "endMs": 900}]})
            payload = json.loads(req.content)
            assert payload["model"] == "muse-spark-1.3"
            assert payload["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,")
            return httpx.Response(200, json={"status": "completed", "output_text": ocr_text,
                **({"usage": {"input_tokens": 100, "output_tokens": 50}} if usage else {})})
        if req.url.host == "inference.baseten.co":
            return httpx.Response(200, json=next(responses)["raw_response"])
        assert req.url.host in {"www.sec.gov", "data.sec.gov"}
        return httpx.Response(200, text=await fixture_sec(str(req.url)))
    return transport


@pytest.mark.parametrize("kind", ["text", "pdf", "image"])
def test_example_uses_existing_decoder_and_program_verdict_with_cost_in_shared_ledger(tmp_path, kind, caplog, capsys):
    async def run():
        calls = []
        async with running(config(tmp_path, kind), transport_for(calls)) as (app, services):
            response = await example_request(app, kind)
            result = data(response)
            assert response.status == 200, result
            assert result["verdict"] == "supported"
            assert " ".join(result["input"]["text_read"].split()) == APPLE["claim"]
            assert result["input"]["kind"] == result["input"]["example_id"] == kind
            assert " ".join(result["corrections"]["original_text"].split()) == APPLE["claim"]
            prep = result["input"]["preprocessing"]
            assert prep["latency_ms"] >= 0
            assert prep["provider"] == ("meta" if kind == "image" else "local")
            assert prep["cost_usd"] == pytest.approx(.0003375 if kind == "image" else 0)
            assert result["cost_usd"] == pytest.approx(TRACE["cost_usd"] + prep["cost_usd"])
            budget = await services.gate("budget", {})
            assert budget["daily_spent_usd"] == pytest.approx(result["cost_usd"], abs=4e-9)
            assert all(hold["settled"] for hold in state(services)["holds"].values())
            for private in (PASSWORD, TOKEN, "offline-meta-key", "offline-api-key-marker", "reasoning_content"):
                assert private not in response.text and private not in json.dumps(state(services))
            assert response.headers["Cache-Control"] == "no-store"
    asyncio.run(run())
    assert not caplog.text and not capsys.readouterr().out


@pytest.mark.parametrize("kind,ocr_count", [("audio", 0), ("video", 3)])
def test_audio_and_video_use_meta_asr_and_all_three_frames_before_the_same_pipeline(tmp_path, monkeypatch, kind, ocr_count):
    original_decode = ingest_media.decode

    def decode(path, folder):
        folder.mkdir(parents=True, exist_ok=True)
        audio = folder / "audio.wav"
        with wave.open(str(audio), "wb") as wav:
            wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\0\0" * 24000)
        channels = [{"id": "audio", "kind": "transcript", "decoded": True, "duration_s": 1, "audio": str(audio)}]
        if kind == "video":
            for i in range(1, 4):
                channels.append({"id": f"frame-{i}", "kind": "frame", "decoded": True, "sample_ms": i * 200, "image": str(IMAGE)})
        return kind, channels

    monkeypatch.setattr(ingest_media, "decode", decode)

    async def run():
        calls = []
        async with running(config(tmp_path, kind), transport_for(calls)) as (app, services):
            response = await example_request(app, kind)
            result = data(response)
            assert response.status == 200, result
            assert result["verdict"] == "supported"
            assert sum(req.url.path == "/v1/responses" for req in calls) == ocr_count
            assert sum(req.url.path == "/v1/asr/transcribe" for req in calls) == 1
            assert result["input"]["text_read"].count(APPLE["claim"]) == ocr_count + 1
            assert result["input"]["preprocessing"]["cost_usd"] == pytest.approx(.00005 + ocr_count * .0003375)
            assert all(row["settled"] for row in state(services)["holds"].values())
    asyncio.run(run())
    monkeypatch.setattr(ingest_media, "decode", original_decode)


def test_example_auth_limits_unknown_id_packaged_hash_and_body_limit_precede_paid_io(tmp_path):
    async def run():
        async with running(config(tmp_path)) as (app, services):
            assert (await example_request(app, token=None)).status == 401
            assert (await example_request(app, password="wrong")).status == 401
            for example_id in ("../post.txt", "unknown", [], None):
                response = await example_request(app, example_id)
                assert response.status == 400 and data(response)["error"] == "unknown_example"
            assert (await example_request(app, raw=b" " * 1025)).status == 400
            assert (await request(app, "/api/check-example", body={"example_id": "text", "password": PASSWORD, "file": "post.txt"})).status == 400
            (services.settings.examples_dir / "post.txt").write_text("tampered")
            response = await example_request(app)
            assert response.status == 503 and data(response)["error"] == "example_unavailable"
            assert not state(services).get("holds") and not state(services).get("rates")
    asyncio.run(run())


def test_examples_share_auth_rate_and_budget_stops_with_pasted_checks(tmp_path):
    async def run():
        async with running(config(tmp_path, "image")) as (app, services):
            for _ in range(5):
                await services.gate("rate", {"ip": "192.0.2.1"})
            assert data(await example_request(app, "image"))["error"] == "rate_limited"
            assert not state(services).get("holds")
        async with running(config(tmp_path / "budget", "image", daily_budget="0")) as (app, services):
            response = await example_request(app, "image")
            assert response.status == 429 and data(response)["error"] == "budget_exhausted"
            assert not state(services).get("holds")
    asyncio.run(run())


@pytest.mark.parametrize("status,code", [(402, "credit_exhausted"), (503, "preprocessing_failed")])
def test_preprocessing_failure_keeps_one_hold_and_does_not_retry(tmp_path, status, code):
    async def run():
        calls = []
        async with running(config(tmp_path, "image"), transport_for(calls, media_status=status)) as (app, services):
            response = await example_request(app, "image")
            result = data(response)
            assert response.status == 503 and result["error"] == code
            assert len(calls) == 1
            assert result["input"]["preprocessing"]["cost_usd"] > 0 and result["cost_is_bound"]
            assert not next(iter(state(services)["holds"].values()))["settled"]
            if status == 402:
                assert (await services.gate("budget", {}))["providers"]["meta"]["status"] == "credit_exhausted"
    asyncio.run(run())


def test_missing_meta_key_and_pending_assets_do_not_spend(tmp_path):
    async def run():
        async with running(replace(config(tmp_path, "image"), meta_api_key="")) as (app, services):
            assert data(await example_request(app, "image"))["error"] == "unavailable"
            assert not state(services).get("holds")
        folder = ROOT / "docs/examples"
        async with running(replace(settings(tmp_path), examples_dir=folder)) as (app, services):
            # This committed build deliberately has no synthesized narration.
            if not (folder / "post.mp3").exists():
                assert data(await example_request(app, "audio"))["error"] == "example_unavailable"
    asyncio.run(run())


def test_media_timeout_is_60_seconds_cancels_io_keeps_hold_and_seals_bridge(tmp_path, monkeypatch):
    timeout = asyncio.timeout
    limits, calls, contexts = [], [], []
    def short(seconds):
        limits.append(seconds)
        context = timeout(None if seconds == 60 else seconds)
        if seconds == 60:
            contexts.append(context)
        return context
    monkeypatch.setattr(server.asyncio, "timeout", short)
    async def transport(req):
        calls.append(req)
        contexts[0].reschedule(asyncio.get_running_loop().time() + .01)
        await asyncio.Event().wait()
    async def run():
        async with running(config(tmp_path, "image"), transport) as (app, services):
            response = await example_request(app, "image")
            result = data(response)
            assert response.status == 504 and result["error"] == "timeout"
            assert result["input"]["kind"] == "image" and result["cost_is_bound"]
            assert not next(iter(state(services)["holds"].values()))["settled"]
            await asyncio.sleep(.02)
            assert len(calls) == 1
    asyncio.run(run())
    # Body/auth parsing has its own short deadline; media execution keeps the
    # separate 60-second deadline and cancellation bridge.
    assert 60 in limits


def test_missing_ocr_usage_retains_bound_in_total_and_preprocessing_cost(tmp_path):
    async def run():
        calls = []
        async with running(config(tmp_path, "image"), transport_for(calls, usage=False)) as (app, services):
            result = data(await example_request(app, "image"))
            assert result["verdict"] == "supported" and result["cost_is_bound"]
            assert result["input"]["preprocessing"]["cost_usd"] > .01
            assert (await services.gate("budget", {}))["daily_spent_usd"] == pytest.approx(result["cost_usd"], abs=4e-9)
    asyncio.run(run())


def test_meta_transport_timeout_returns_504_and_retains_its_preprocessing_hold(tmp_path):
    async def transport(req):
        raise httpx.ReadTimeout("offline timeout marker", request=req)
    async def run():
        async with running(config(tmp_path, "image"), transport) as (app, services):
            response = await example_request(app, "image")
            result = data(response)
            assert response.status == 504 and result["error"] == "timeout"
            assert result["cost_is_bound"] and result["input"]["preprocessing"]["cost_usd"] > 0
            assert not next(iter(state(services)["holds"].values()))["settled"]
            assert "offline timeout marker" not in response.text
    asyncio.run(run())


def test_timeout_while_decoding_never_starts_a_late_paid_call(tmp_path, monkeypatch):
    timeout = asyncio.timeout
    contexts = []
    def delayed_timeout(seconds):
        context = timeout(None if seconds == 60 else seconds)
        if seconds == 60:
            contexts.append(context)
        return context
    monkeypatch.setattr(server.asyncio, "timeout", delayed_timeout)
    release, finished = threading.Event(), threading.Event()
    loops = []

    def slow_decode(path, folder):
        loops[0].call_soon_threadsafe(contexts[0].reschedule, loops[0].time() + .01)
        release.wait(1)
        finished.set()
        return "image", [{"id": "image", "kind": "ocr", "decoded": True, "image": str(IMAGE)}]
    monkeypatch.setattr(ingest_media, "decode", slow_decode)

    async def run():
        loops.append(asyncio.get_running_loop())
        async with running(config(tmp_path, "image")) as (app, services):
            response = await example_request(app, "image")
            assert response.status == 504
            release.set()
            assert await asyncio.to_thread(finished.wait, 1)
            await asyncio.sleep(.02)
            assert not state(services).get("holds")
    asyncio.run(run())
