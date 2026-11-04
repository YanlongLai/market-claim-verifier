"""Offline proxy privacy, single-request limit and live-asset gates (no browser/API)."""
from email.message import Message
import importlib.util
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
import threading

import pytest
import yaml

import record_v4 as recorder

spec = importlib.util.spec_from_file_location("preview_v4_tests", recorder.ROOT / "scripts/serve_site.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def handler(tmp_path, *, method="POST", path="/api/check", origin="http://127.0.0.1:8765"):
    instance = preview.Handler.__new__(preview.Handler)
    instance.command, instance.path = method, path
    instance.server = SimpleNamespace(docs_root=tmp_path, proxy_api=recorder.ORIGIN,
                                     server_port=8765, check_lock=threading.Lock(), check_count=0, max_checks=1)
    instance.headers = Message()
    body = b'{"text":"Apple","password":"private-test-secret"}'
    for key, value in {"Content-Type": "application/json", "Content-Length": str(len(body)),
                       "Origin": origin, "Cookie": "private-cookie", "Authorization": "private-token"}.items():
        instance.headers[key] = value
    instance.rfile, instance.wfile = BytesIO(body), BytesIO()
    instance.errors, instance.response_headers, instance.statuses = [], {}, []
    instance.send_error = lambda code, *args: instance.errors.append(code)
    instance.send_response = instance.statuses.append
    instance.send_header = instance.response_headers.__setitem__
    instance.end_headers = lambda: None
    return instance


class Response(BytesIO):
    code = 200
    headers = {"Content-Type": "application/json"}


def test_proxy_sends_only_expected_headers_and_never_logs_body(tmp_path, monkeypatch, capsys):
    instance = handler(tmp_path)
    calls = []
    def open_request(request, *, timeout):
        calls.append(request)
        assert timeout == 40
        return Response(b'{"verdict":"contradicted"}')
    monkeypatch.setattr(preview, "build_opener", lambda *args: SimpleNamespace(open=open_request))
    assert instance.proxy_request()
    request = calls[0]
    assert request.full_url == "https://hackathon.dappgo.com/api/check"
    headers=dict(request.header_items())
    assert headers.pop('User-agent').endswith(' live-check-preview')
    assert headers == {"Origin": recorder.ORIGIN, "Content-type": "application/json", "Accept": "application/json"}
    assert b'"password":"private-test-secret"' in request.data
    assert instance.statuses == [200] and instance.wfile.getvalue() == b'{"verdict":"contradicted"}'
    instance.log_message("%s", request.data)
    assert capsys.readouterr() == ("", "")
    assert instance.proxy_request() and instance.errors == [429]
    assert len(calls) == 1  # No automatic retry, including after partial attempts.


@pytest.mark.parametrize("method,path,origin,code", [
    ("GET", "/api/check", "http://127.0.0.1:8765", 405),
    ("POST", "/api/budget", "http://127.0.0.1:8765", 405),
    ("POST", "/api/check?password=bad", "http://127.0.0.1:8765", 405),
    ("POST", "/api/check", "https://untrusted.example", 403),
])
def test_proxy_rejects_other_methods_origins_and_query_credentials(tmp_path, monkeypatch, method, path, origin, code):
    instance = handler(tmp_path, method=method, path=path, origin=origin)
    monkeypatch.setattr(preview, "build_opener", lambda *_: pytest.fail("must not contact upstream"))
    assert instance.proxy_request() and instance.errors == [code]


def test_budget_is_forwarded_without_a_body_and_preserves_upstream_status(tmp_path, monkeypatch):
    instance = handler(tmp_path, method="GET", path="/api/budget")
    def open_request(request, **_kwargs):
        assert request.data is None and request.method == "GET"
        raise preview.HTTPError(request.full_url, 429, "limited", {"Content-Type": "application/json"},
                                BytesIO(b'{"error":"rate_limited"}'))
    monkeypatch.setattr(preview, "build_opener", lambda *_: SimpleNamespace(open=open_request))
    instance.proxy_request()
    assert instance.statuses == [429]
    assert instance.response_headers["Cache-Control"] == "no-store"
    assert instance.wfile.getvalue() == b'{"error":"rate_limited"}'


def test_static_preview_and_redirects_cannot_forward_credentials(tmp_path):
    assert preview.output_path("/styles.css", tmp_path) == tmp_path / "site/styles.css"
    assert preview.output_path("/evidence/", tmp_path) == tmp_path / "evidence/index.html"
    with pytest.raises(ValueError):
        preview.output_path("/%2e%2e/private", tmp_path)
    for invalid in ("https://user:password@example.com", "http://example.com", "https://example.com/api"):
        with pytest.raises(Exception):
            preview.proxy_origin(invalid)
    assert preview.NoRedirect().redirect_request(None, None, None, None, None, None) is None


def make_takes(tmp_path, monkeypatch):
    story = {"scenes": []}
    lengths={s['id']:s['target_s'] for s in yaml.safe_load(recorder.STORYBOARD.read_text())['scenes']}
    for scene_id, (beat, _) in recorder.BEATS.items():
        seconds=lengths[scene_id]
        receipt = {"status": "ready", "scene_id": scene_id,
                   "capture_version":5,"zoom":1.6,
                   "readability":{"playback_body_px":20.16,"column_center_x":960},
                   "timings":[{"phase":"verdict_reveal","at_s":22.08978275},
                              {"phase":"draft_reveal","at_s":25.017312916}],
                   "choreography":{"trace_details_open":True,"apple_inspect_open":True,
                       "program_verdict_shown":True,"after_click_s":45,"beat6_actions_end_s":50,
                       "apple_derivation":{"annual":416161000000,"nine_months":313695000000,
                           "quarter":102466000000,"hold_ms":2000},
                       "trace_steps_shown":[{"index":0,"kind":"tool_call","visible":True,"hold_ms":700},
                                            {"index":1,"kind":"verdict","visible":True,"hold_ms":700}]},
                   "result": {"mode": "live", "provider": "baseten", "model": "meta-models/muse-spark-open-1026",
                              "cost_usd": .02, "latency_ms": 20000,
                              "events":[{"kind":"tool_call"},{"kind":"verdict"}]}}
        for kind in ("webm", "mp4"):
            path = tmp_path / f"{beat}.{kind}"
            path.write_bytes(f"synthetic {kind} fixture".encode())
            receipt[kind] = {"path": path.name, "sha256": recorder.digest(path)}
        receipt_path = tmp_path / f"{beat}.json"
        recorder.save(receipt_path, receipt)
        original=next(s for s in yaml.safe_load(recorder.STORYBOARD.read_text())['scenes'] if s['id']==scene_id)
        story["scenes"].append({"id": scene_id, "target_s": seconds,"cue_events":original['cue_events'],
                                "recording": {"asset": f"{beat}.mp4", "receipt": receipt_path.name, "offset_s": 0}})
    monkeypatch.setattr(recorder, "probe", lambda path: {"duration_s": lengths['v406' if 'beat6' in str(path) else 'v409'],
                                                       "width": 1920, "height": 1080, "fps": "30/1"})
    return story


def test_both_recordings_must_exist_match_hashes_and_cover_the_scene(tmp_path, monkeypatch):
    story = make_takes(tmp_path, monkeypatch)
    assert set(recorder.check_recordings(story, tmp_path)) == {"v406", "v409"}
    (tmp_path / "beat9.mp4").unlink()
    with pytest.raises(recorder.RecordingError, match="asset does not exist"):
        recorder.check_recordings(story, tmp_path)


def test_too_short_changed_or_non_live_takes_are_rejected(tmp_path, monkeypatch):
    story = make_takes(tmp_path, monkeypatch)
    monkeypatch.setattr(recorder, "probe", lambda _: {"duration_s": story['scenes'][0]['target_s']-.01, "width": 1920, "height": 1080, "fps": "30/1"})
    with pytest.raises(recorder.RecordingError, match="shorter"):
        recorder.check_recordings(story, tmp_path)
    story = make_takes(tmp_path, monkeypatch)
    (tmp_path / "beat6.webm").write_bytes(b"changed")
    with pytest.raises(recorder.RecordingError, match="missing or changed"):
        recorder.check_recordings(story, tmp_path)
    story = make_takes(tmp_path, monkeypatch)
    path = tmp_path / "beat6.json"
    receipt = json.loads(path.read_text()); receipt["result"]["mode"] = "recorded"; recorder.save(path, receipt)
    with pytest.raises(recorder.RecordingError, match="real Baseten"):
        recorder.check_recordings(story, tmp_path)


def test_missing_live_takes_block_host_preparation_but_allow_explicit_source_preview():
    story = {"scenes": [{"id": scene, "placeholder": True} for scene in recorder.BEATS]}
    assert recorder.check_recordings(story, required=False) == {}
    with pytest.raises(recorder.RecordingError, match="live take missing"):
        recorder.check_recordings(story)


def test_source_preview_stays_rebuildable_without_ignored_host_cache(tmp_path):
    story={"scenes":[{"id":scene,"target_s":seconds,
                       "recording":{"asset":f"demo/cache/live-takes/v4/{beat}-timestamp.mp4",
                                    "receipt":f"demo/cache/live-takes/v4/{beat}-timestamp.json", "offset_s":0}}
                      for scene,(beat,seconds) in recorder.BEATS.items()]}
    assert recorder.check_recordings(story,tmp_path,required=False)=={}
    with pytest.raises(recorder.RecordingError,match="asset does not exist"):
        recorder.check_recordings(story,tmp_path)


def test_numeric_free_copy_accepts_genuine_measurements_without_price_or_speed_targets():
    assert recorder.live_copy_supported({"cost_usd": .02, "latency_ms": 20000})
    assert recorder.live_copy_supported({"cost_usd": .01, "latency_ms": 10900})
    assert recorder.live_copy_supported({"cost_usd": .062084, "latency_ms": 38400})
    assert recorder.live_copy_supported({"cost_usd": .01, "latency_ms": 6000})
    for result in ({"cost_usd": -1, "latency_ms": 20000},
                   {"cost_usd": .01, "latency_ms": 0},
                   {"cost_usd": float('nan'), "latency_ms": 20000},
                   {"cost_usd": .02, "latency_ms": 20000, "cost_is_bound": True}):
        assert not recorder.live_copy_supported(result)


@pytest.mark.parametrize('patch',[
    {'trace_details_open':False},{'apple_inspect_open':False},{'program_verdict_shown':False},
    {'trace_steps_shown':[]},{'after_click_s':56.01},{'beat6_actions_end_s':56.01},
])
def test_closed_or_incomplete_trace_and_overlong_choreography_are_rejected(tmp_path,monkeypatch,patch):
    make_takes(tmp_path,monkeypatch)
    receipt=json.loads((tmp_path/'beat6.json').read_text())
    recorder.check_choreography(receipt)
    receipt['choreography'].update(patch)
    with pytest.raises(recorder.RecordingError,match='r5 requires'):
        recorder.check_choreography(receipt)


def test_cue_positions_follow_receipt_reveals_instead_of_model_latency():
    scene=yaml.safe_load(recorder.STORYBOARD.read_text())['scenes'][5]
    receipt={'timings':[{'phase':'verdict_reveal','at_s':19},{'phase':'draft_reveal','at_s':24}]}
    assert [e['at_scene_s'] for e in recorder.live_cue_events(scene,receipt)]==[0,18,21,24]


def test_wiring_uses_timestamped_assets_and_preserves_all_narration_and_cuts(tmp_path, monkeypatch):
    story_path = tmp_path / "storyboard.yaml"
    original = yaml.safe_load(recorder.STORYBOARD.read_text())
    story_path.write_text(yaml.safe_dump(original))
    monkeypatch.setattr(recorder, "STORYBOARD", story_path)
    monkeypatch.setattr(recorder, "ROOT", tmp_path)
    monkeypatch.setattr(recorder, "OUT", tmp_path)
    story = make_takes(tmp_path, monkeypatch)
    paths = {scene["id"]: tmp_path / scene["recording"]["receipt"] for scene in story["scenes"]}
    # check_recordings defaults to the real root; bind it explicitly for this fixture.
    check = recorder.check_recordings
    monkeypatch.setattr(recorder, "check_recordings", lambda s: check(s, tmp_path))
    recorder.wire_storyboard(paths, "test-stamp")
    updated = yaml.safe_load(story_path.read_text())
    for before, after in zip(original["scenes"], updated["scenes"]):
        for key in ("narration", "subtitle_cues", "target_s", "target_start_s", "target_end_s"):
            assert before[key] == after[key]
    assert not any(s.get("placeholder") for s in updated["scenes"])
    assert (tmp_path / "storyboard-before-test-stamp.yaml").is_file()
