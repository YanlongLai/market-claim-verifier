from __future__ import annotations

import copy
import json
import math
import shutil
import wave
from array import array
from pathlib import Path
from types import SimpleNamespace

import pytest

from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.edgar import EdgarClient
from claimcheck.ingest import _InputLedger, attach_locations, channel_stages, ingest_file, prepare_text
from claimcheck.ingest_media import ASR_MODEL, IngestError, decode, transcribe
from claimcheck.ingest_text import normalize_numbers, original_offset
from claimcheck.release_fetch import ReleaseClient
from claimcheck.cli import main

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "tests/fixtures/multimodal"
EVIDENCE = ROOT / "docs/evidence/multimodal-2026-10-29"


def offline_clients(tmp_path):
    cache = tmp_path / "corpus"
    shutil.copytree(ROOT / "tests/fixtures/sec-offline", cache)
    shutil.copytree(ROOT / "tests/fixtures/releases/releases", cache / "releases")

    def missing(url):
        raise AssertionError("unrecorded SEC access")

    return EdgarClient(cache_dir=cache, fetcher=missing), ReleaseClient(cache, fetcher=missing)


class ReplayMeta:
    def __init__(self, requests):
        self.requests = copy.deepcopy(requests)
        self.responses = self
        self.chat = SimpleNamespace(completions=self)
        self.calls = 0

    def create(self, **payload):
        expected = self.requests.pop(0)
        self.calls += 1
        assert payload["model"] == expected["request"]["model"]
        assert payload["model"] in {"muse-spark-1.3", "meta-models/muse-spark-open-1026"}
        # Legacy extraction output replay under the current prompt tests the
        # deterministic downstream checks, not what a new model would extract.
        from claimcheck.post import EXTRACTION_PROMPT
        extraction = str(expected['request'].get('instructions', '')).startswith('You extract financial claims')
        assert payload.get("instructions") == (EXTRACTION_PROMPT if extraction else expected["request"].get("instructions"))
        if "image_sha256" in json.dumps(expected["request"]):
            assert payload["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,")
        elif "input" in payload:
            assert payload["input"] == expected["request"]["input"]
        else:
            assert payload["messages"] == expected["request"]["messages"]
        if expected.get('status') == 'error':
            exc = RuntimeError(expected['raw_response']['message'])
            exc.status_code = expected['retry']['http_status']
            raise exc
        return expected.get("raw_response", expected.get("response"))


@pytest.mark.parametrize("run,file", [("text", "post.txt"), ("screenshot", "example-post.png")])
def test_actual_text_and_vision_responses_replay_through_sec_and_program(tmp_path, run, file):
    saved = json.loads((EVIDENCE / run / "ingest.json").read_text())
    channel = saved["channels"][0]
    requests = []
    if channel.get("media_call"):
        requests.append(json.loads((EVIDENCE / run / channel["media_call"]).read_text()))
    traces = EVIDENCE / run / "checks" / channel["id"]
    requests += json.loads((EVIDENCE / run / channel["extraction_trace"]).read_text())["requests"]
    for claim in channel["claims"]:
        if claim.get("trace_path"):
            requests += json.loads((traces / claim["trace_path"]).read_text())["requests"]
    replay = ReplayMeta(requests)
    edgar, release = offline_clients(tmp_path)
    result = ingest_file(MEDIA / file, client=replay, vision_client=replay, edgar=edgar,
        release_client=release, ledger=Ledger(tmp_path / "ledger", budget_usd=5), model="muse-spark-1.3",
        provider="meta", out_dir=tmp_path / "out", max_output_tokens=4000)
    assert result["status"] == "completed"
    assert not replay.requests
    assert [s["status"] for s in result["stages"]] == ["reached"] * 5 + ["not_applicable"]
    claims = result["channels"][0]["claims"]
    assert [c["verdict"] for c in claims] == ["supported", "contradicted"]
    assert result["cost_usd"] == pytest.approx(saved["cost_usd"])
    for claim in claims:
        assert claim["evidence"] and all(e["tier"] in {"L1", "L2", "L3", "L4"} for e in claim["evidence"])
        for location in claim["source_locations"]:
            a, b = location["raw_span"]
            assert result["channels"][0]["raw_text"][a:b] == location["heard_or_read_quote"]


@pytest.mark.parametrize("run,file", [
    ("audio-two-voices", "two-voices.wav"),
])
def test_actual_asr_and_video_responses_replay_without_codecs(monkeypatch, tmp_path, run, file):
    saved = json.loads((EVIDENCE / run / "ingest.json").read_text())
    requests, speech_responses = [], []
    for channel in saved["channels"]:
        if channel.get("media_call"):
            record = json.loads((EVIDENCE / run / channel["media_call"]).read_text())
            if channel["kind"] == "transcript":
                speech_responses.append(record["response"])
            else:
                requests.append(record)
        if channel.get("extraction_trace"):
            requests += json.loads((EVIDENCE / run / channel["extraction_trace"]).read_text())["requests"]
        for claim in channel.get("claims", []):
            if claim.get("trace_path"):
                requests += json.loads((EVIDENCE / run / "checks" / channel["id"] / claim["trace_path"]).read_text())["requests"]

    def recorded_decode(path, media_dir):
        # Replay the saved decoded channels. Codec integration is checked below
        # when ffmpeg is present; ASR/model/tool replay needs no codec binaries.
        channels = []
        for original in saved["channels"]:
            channel = {k: copy.deepcopy(v) for k, v in original.items() if k in {
                "id", "kind", "decoded", "duration_s", "sample_ms", "image_info", "audio_sha256"}}
            if original["kind"] == "transcript":
                channel["audio"] = str(MEDIA / ("two-voices.wav" if file == "two-voices.wav" else "release-reading.wav"))
            else:
                channel["image"] = str(EVIDENCE / run / original["image"])
            channels.append(channel)
        return saved["input"]["kind"], channels

    class SpeechHTTP:
        def post(self, url, **kwargs):
            request = json.loads(kwargs["files"]["request"][1])
            assert request == {"model": ASR_MODEL, "audioEncoding": "WAV", "mode": "DIARIZATION", "languageBias": ["English"]}
            assert kwargs["files"]["audio"][1].read(4) == b"RIFF"
            response = speech_responses.pop(0)
            return SimpleNamespace(status_code=200, json=lambda: response)

    monkeypatch.setattr("claimcheck.ingest.decode", recorded_decode)
    # Recorded paths must be below the report directory for portable output.
    # Copy only replay artifacts into that directory, then use its relative paths.
    original_decode = recorded_decode
    def local_decode(path, media_dir):
        media_dir.mkdir(parents=True)
        kind, channels = original_decode(path, media_dir)
        for channel in channels:
            key = "audio" if "audio" in channel else "image"
            source = Path(channel[key])
            dest = media_dir / (channel["id"] + source.suffix)
            shutil.copyfile(source, dest)
            channel[key] = str(dest)
        return kind, channels
    monkeypatch.setattr("claimcheck.ingest.decode", local_decode)
    replay = ReplayMeta(requests)
    edgar, release = offline_clients(tmp_path)
    result = ingest_file(MEDIA / file, client=replay, vision_client=replay, asr_http=SpeechHTTP(), meta_api_key="fake-key",
        edgar=edgar, release_client=release, ledger=Ledger(tmp_path / "ledger", budget_usd=5), model=saved["model"],
        provider=saved["provider"], out_dir=tmp_path / "out", max_output_tokens=8000)
    assert result["status"] == "completed" and not replay.requests and not speech_responses
    assert [s["status"] for s in result["stages"]] == [s["status"] for s in saved["stages"]]
    assert result["cost_usd"] == pytest.approx(saved["cost_usd"])
    for channel, recorded in zip(result["channels"], saved["channels"]):
        assert channel["raw_text"] == recorded["raw_text"]
        assert [(c["status"], c.get("verdict")) for c in channel["claims"]] == [(c["status"], c.get("verdict")) for c in recorded["claims"]]
        assert [c["source_locations"] for c in channel["claims"]] == [c["source_locations"] for c in recorded["claims"]]
    if run == "audio-two-voices":
        assert {s["speaker"] for s in result["channels"][0]["segments"]} == {"A"}  # observed diarization miss


def test_self_made_fixture_hashes_and_non_silent_pcm():
    manifest = json.loads((MEDIA / "manifest.json").read_text())
    import hashlib
    for filename, info in manifest["files"].items():
        raw = (MEDIA / filename).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == info["sha256"]
        assert len(raw) == info["bytes"]
    for filename in ("release-reading.wav", "two-voices.wav"):
        with wave.open(str(MEDIA / filename)) as wav:
            assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 24000)
            samples = array("h", wav.readframes(wav.getnframes()))
            assert max(abs(s) for s in samples) > 1000
            if filename == "release-reading.wav":
                assert 30 <= len(samples) / 24000 <= 60


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="optional ffmpeg/ffprobe codec integration")
def test_local_decoder_keeps_silent_video_frames_and_audio_separate(tmp_path):
    kind, channels = decode(MEDIA / "slides-silent.mp4", tmp_path / "video")
    assert kind == "video" and len(channels) == 4
    assert channels[0]["error"] == "video has no audio track" and not channels[0]["decoded"]
    assert all(c["decoded"] for c in channels[1:])
    assert [c["sample_ms"] for c in channels[1:]] == sorted(c["sample_ms"] for c in channels[1:])
    kind, channels = decode(MEDIA / "release-reading.wav", tmp_path / "audio")
    assert kind == "audio" and channels[0]["decoded"] and 30 <= channels[0]["duration_s"] <= 60


@pytest.mark.parametrize("raw,expected", [
    ("ninety four point zero billion and one point six seven dollars", "94.0 billion and 1.67 dollars"),
    ("fortytwo and twelve percent", "42 and 12 percent"),
    ("two thousand twenty five third quarter", "2025 Q3"),
    ("minus one point zero five", "-1.05"),
    ("Total: 94,036 million. Net: 23,434.", "Total: 94036 million. Net: 23434."),
    ("low to mid single digits", "low to mid single digits"),
    ("fourteen fiftyfive", "fourteen fiftyfive"),  # Unsupported year-style speech is preserved.
])
def test_normalization_preserves_source_and_precision(raw, expected):
    normalized, edits = normalize_numbers(raw)
    assert normalized == expected
    for edit in edits:
        a, b = edit["normalized_span"]
        x, y = edit["raw_span"]
        assert normalized[a:b] == edit["normalized"]
        assert raw[x:y] == edit["heard_or_read"]
        assert original_offset(a, edits) == x
        assert original_offset(b, edits, end=True) == y


def test_repeated_heard_claim_keeps_both_turns_without_inventing_names():
    text = "Apple EPS was one point six seven in fiscal 2025 third quarter."
    channel = {"id": "audio", "kind": "transcript", "decoded": True, "segments": [
        {"id": "turn-1", "text": text, "start_ms": 0, "end_ms": 5000, "speaker": "A"},
        {"id": "turn-2", "text": text, "start_ms": 6000, "end_ms": 11000, "speaker": "B"}]}
    prepare_text(channel)
    quote = "Apple EPS was 1.67 in fiscal 2025 Q3."
    claims = [{"quote": quote, "span": [0, len(quote)], "kind": "reported_fact", "status": "to_verify"}]
    attach_locations(channel, claims)
    assert len(claims[0]["source_locations"]) == 2
    assert [s["speaker"] for loc in claims[0]["source_locations"] for s in loc["sources"]] == ["A", "B"]
    channel["claims"] = claims
    assert channel_stages(channel)[5]["status"] == "reached"
    del channel["segments"][1]["speaker"]
    attach_locations(channel, claims)
    assert channel_stages(channel)[5]["status"] == "not_reached"


def test_scope_excludes_other_inputs_and_retains_failed_reservations(tmp_path):
    shared = Ledger(tmp_path / "ledger", budget_usd=1)
    first, second = _InputLedger(shared), _InputLedger(shared)
    a = first.reserve({}, model="muse-spark-1.3", max_output_tokens=100, provider="meta")
    b = second.reserve_audio(1.1)
    first.reconcile(a, {"input_tokens": 10, "output_tokens": 10})
    assert first.spent_total == pytest.approx(.000055)
    assert second.spent_total == pytest.approx(.0001)
    assert shared.spent_total == pytest.approx(first.spent_total + second.spent_total)


@pytest.mark.parametrize("duration", [0, -1, 601, math.nan, math.inf])
def test_bad_asr_duration_is_rejected_before_upload(tmp_path, duration):
    with pytest.raises(ValueError):
        Ledger(tmp_path / "ledger").reserve_audio(duration)
    assert not (tmp_path / "ledger").exists()


def test_zero_budget_stops_before_model_and_still_records_decoded_input(tmp_path):
    class NeverCall:
        @property
        def responses(self):
            raise AssertionError("model called without reservation")
    result = ingest_file(MEDIA / "post.txt", client=NeverCall(), edgar=None,
        ledger=Ledger(tmp_path / "ledger", budget_usd=0), model="muse-spark-1.3", provider="meta", out_dir=tmp_path / "out")
    assert [s["status"] for s in result["stages"]][:3] == ["reached", "reached", "not_reached"]
    assert result["cost_usd"] == 0 and result["channels"][0]["error"]
    assert (tmp_path / "out/ingest.json").is_file()


def test_unaccepted_model_is_refused_without_call(tmp_path):
    with pytest.raises(IngestError, match="only.*Meta"):
        ingest_file(MEDIA / "post.txt", client=None, edgar=None, ledger=Ledger(tmp_path / "ledger"),
                    model="some-other-model", provider="meta", out_dir=tmp_path / "out")


def test_invalid_and_overlong_inputs_record_a_stop_without_upload(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"not an image")
    kwargs = dict(client=None, edgar=None, ledger=Ledger(tmp_path / "ledger"), model="muse-spark-1.3", provider="meta")
    result = ingest_file(path, out_dir=tmp_path / "broken", **kwargs)
    assert result["status"] == "failed" and result["stages"][0]["status"] == "not_reached"
    path = tmp_path / "large.txt"
    path.write_text("x" * 6001)
    result = ingest_file(path, out_dir=tmp_path / "large", **kwargs)
    assert result["stages"][1]["status"] == "reached" and result["stages"][2]["status"] == "not_reached"
    assert "client unavailable" in result["channels"][0]["error"]


def test_asr_http_failure_keeps_charge_and_never_records_auth(tmp_path):
    wav = tmp_path / "clip.wav"
    wav.write_bytes(b"RIFF test")
    secret = "test-secret-do-not-record"
    class HTTP:
        def post(self, url, **kwargs):
            assert kwargs["headers"]["Authorization"] == "Bearer " + secret
            return SimpleNamespace(status_code=401)
    ledger = Ledger(tmp_path / "ledger", budget_usd=1)
    with pytest.raises(IngestError, match="401"):
        transcribe({"audio": str(wav), "duration_s": 30.2}, http=HTTP(), api_key=secret,
                   ledger=ledger, record=tmp_path / "call.json")
    saved = json.loads((tmp_path / "call.json").read_text())
    assert saved["request"]["model"] == ASR_MODEL
    assert saved["cost_usd"] == pytest.approx(31 * .18 / 3600) == ledger.spent_total
    assert secret not in (tmp_path / "call.json").read_text()


def test_untimed_transcript_is_usable_text_without_fabricated_attribution(tmp_path):
    wav = tmp_path / "clip.wav"
    wav.write_bytes(b"RIFF test")
    response = {"transcript": "Apple EPS was one point six seven.", "turns": []}
    http = SimpleNamespace(post=lambda *a, **kw: SimpleNamespace(status_code=200, json=lambda: response))
    segments, _ = transcribe({"audio": str(wav), "duration_s": 10}, http=http, api_key="test-key",
                            ledger=Ledger(tmp_path / "ledger"), record=tmp_path / "asr.json")
    assert segments == [{"id": "untimed-transcript", "text": response["transcript"]}]


def test_capped_claims_do_not_claim_all_program_verdicts():
    channel = {"id": "text", "kind": "text", "decoded": True, "raw_text": "some text", "claims": [
        {"kind": "reported_fact", "status": "verified", "program_checks": [{"program_verdict": "supported"}]},
        {"kind": "reported_fact", "status": "not_checked", "screen_reason": "over claim limit"}]}
    assert channel_stages(channel)[2]["status"] == "reached"
    assert channel_stages(channel)[4]["status"] == "partial"


def test_extraction_and_sources_survive_a_later_provider_failure(tmp_path):
    quote = "Apple reported diluted EPS of $1.67 for fiscal Q3 2025."
    class FailAfterExtraction:
        responses = None
        def __init__(self):
            self.responses = self
            self.calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls > 1:
                raise RuntimeError("provider error with test-private-key")
            return {"id": "extract", "status": "completed", "output_text": json.dumps({"claims": [
                {"quote": quote, "claim": quote, "kind": "reported_fact", "ticker": "AAPL"}]}),
                "usage": {"input_tokens": 10, "output_tokens": 50}}
    result = ingest_file(MEDIA / "post.txt", client=FailAfterExtraction(), edgar=object(),
        ledger=Ledger(tmp_path / "ledger", budget_usd=1), model="muse-spark-1.3", provider="meta",
        out_dir=tmp_path / "out", secrets=["test-private-key"])
    assert result["stages"][2]["status"] == "reached" and result["stages"][4]["status"] == "not_reached"
    assert result["channels"][0]["claims"][0]["source_locations"]
    assert result["cost_usd"] > .0002  # failed agent reservation remains accounted for
    for path in (tmp_path / "out").rglob("*"):
        if path.suffix in {".html", ".json"}:
            assert "test-private-key" not in path.read_text()


def test_absent_ffmpeg_is_an_explicit_input_failure(monkeypatch, tmp_path):
    path = tmp_path / "clip.wav"
    path.write_bytes(b"RIFF test")
    monkeypatch.setattr("claimcheck.ingest_media.shutil.which", lambda _: None)
    result = ingest_file(path, client=None, edgar=None, ledger=Ledger(tmp_path / "ledger"),
                        model="muse-spark-1.3", provider="meta", out_dir=tmp_path / "out")
    assert result["stages"][0]["status"] == "not_reached"
    assert "ffprobe" in result["errors"][0]
    assert result["stages"][5]["status"] == "not_reached"


def test_module_cli_records_missing_input_and_rejects_nonfinite_budget(monkeypatch, tmp_path, capsys):
    for key in ("MODEL_API_KEY", "BASETEN_API_KEY", "FIREWORKS_API_KEY", "CLAIMCHECK_PROVIDER", "CLAIMCHECK_MODEL"):
        monkeypatch.delenv(key, raising=False)
    for key in ("MODEL_API_KEY_FILE", "BASETEN_API_KEY_FILE", "FIREWORKS_API_KEY_FILE"):
        monkeypatch.setenv(key, str(tmp_path / "no-key"))
    monkeypatch.setenv("CLAIMCHECK_RUNS_DIR", str(tmp_path / "runs"))
    output = tmp_path / "out"
    assert main(["ingest", str(tmp_path / "missing.wav"), "--out", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
    saved = json.loads((output / "ingest.json").read_text())
    assert saved["stages"][5]["status"] == "not_reached"
    assert main(["ingest", str(MEDIA / "post.txt"), "--budget", "nan"]) == 2
    assert "finite" in capsys.readouterr().err


def test_asr_uses_meta_budget_even_when_text_is_baseten(tmp_path):
    ledger = Ledger(tmp_path / "ledger", provider="baseten", budget_usd=10, provider_budgets={"meta": 0})
    with pytest.raises(BudgetExceeded):
        ledger.reserve_audio(30)
    assert ledger.spent_total == 0
