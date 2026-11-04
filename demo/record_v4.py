#!/usr/bin/env python3
"""Record one live check and its result on committed main, with no automatic retry.

Host: PLAYWRIGHT_MODULE=/path/to/playwright LIVE_CHECK_PASSWORD_FILE=/private/file
      uv run --project demo python demo/record_v4.py --port 8765
No screenshots, HAR, browser trace, storage export or request-body logs are made.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import threading

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo/cache/live-takes/v4"
STORYBOARD = ROOT / "demo/storyboard-v4.yaml"
FFMPEG = Path("/opt/homebrew/bin/ffmpeg")
FFPROBE = Path("/opt/homebrew/bin/ffprobe")
ORIGIN = "https://hackathon.dappgo.com"
BEATS = {"v406": ("beat6", 58.0), "v409": ("beat9", 14.0)}


class RecordingError(RuntimeError):
    pass


def digest(path):
    with Path(path).open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def live_copy_supported(result):
    """Narration refers to the receipt without promising a price or latency."""
    cost, latency = result.get("cost_usd"), result.get("latency_ms")
    return (type(cost) in (float, int) and math.isfinite(cost) and cost >= 0
            and type(latency) in (float, int) and math.isfinite(latency) and latency > 0
            and not result.get("cost_is_bound"))


def live_cue_events(scene, receipt):
    """Resolve exact onsets from this take's reveal phases, never model latency."""
    phases = {t["phase"]: t["at_s"] for t in receipt["timings"]}
    # Older takes remain usable for source previews. Host gates require r5.
    phases.setdefault("verdict_reveal", phases.get("verdict_hold"))
    phases.setdefault("draft_reveal", phases.get("corrected_draft_hold"))
    events = []
    for spec in scene["cue_events"]:
        phase = spec.get("receipt_phase")
        at = phases[phase] + spec.get("offset_s", 0) if phase else 0
        if type(at) not in (float, int) or not math.isfinite(at) or not 0 <= at < scene["target_s"]:
            raise RecordingError("Live narration cue falls outside the locked scene")
        events.append({**spec, "at_scene_s": at})
    return events


def check_choreography(receipt):
    proof = receipt.get("choreography", {})
    events = receipt.get("result", {}).get("events", [])
    calls = [i for i,e in enumerate(events) if e["kind"] == "tool_call"]
    shown = proof.get("trace_steps_shown", [])
    derivation=proof.get('apple_derivation',{})
    readability=receipt.get('readability',{})
    if (receipt.get("capture_version") != 5 or not proof.get("trace_details_open")
            or not proof.get("apple_inspect_open") or not proof.get("program_verdict_shown")
            or [s["index"] for s in shown if s["kind"] == "tool_call" and s.get("visible")] != calls
            or not calls or not 0 < proof.get("after_click_s", math.inf) <= 56
            or not 0 < proof.get("beat6_actions_end_s", math.inf) <= 56
            or any(s.get('hold_ms',0)<700 for s in shown)
            or not any(s['kind']=='verdict' and s.get('visible') for s in shown)
            or derivation.get('hold_ms',0)<2000
            or derivation.get('annual',0)-derivation.get('nine_months',0)!=derivation.get('quarter')
            or readability.get('playback_body_px',0)<20
            or abs(readability.get('column_center_x',0)-960)>4
            or receipt.get("zoom") != 1.6):
        raise RecordingError("r5 requires an open trace, all visible tool calls, program verdict and Apple inspector; re-record on host")


def probe(path):
    completed = subprocess.run(
        [str(FFPROBE), "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path)],
        capture_output=True, check=True, text=True)
    data = json.loads(completed.stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    return {"duration_s": float(data["format"]["duration"]),
            "width": video["width"], "height": video["height"], "fps": video["r_frame_rate"]}


def check_recordings(story, root=ROOT, *, required=True):
    """Storyboard gate: pending footage is allowed only for source-only previews.

    With required=True, wired takes must exist, match their receipts and cover
    the scene. Source previews remain rebuildable without ignored cache/media.
    Host review/keyframe/render preparation always requires both takes.
    """
    records = {}
    for scene in story["scenes"]:
        if scene["id"] not in BEATS:
            continue
        recording = scene.get("recording")
        if not recording:
            if required:
                raise RecordingError(f"{scene['id']}: live take missing; run demo/record_v4.py on the host")
            if not scene.get("placeholder"):
                raise RecordingError(f"{scene['id']}: neither a retained live take nor an explicit pending placeholder")
            continue
        if scene.get("placeholder") or recording.get("offset_s") != 0:
            raise RecordingError(f"{scene['id']}: live take must replace the placeholder and start uncut")
        if not required:
            continue
        for key in ("asset", "receipt"):
            path = (root / recording[key]).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise RecordingError(f"{scene['id']}: {key} does not exist within the project")
        receipt = json.loads((root / recording["receipt"]).read_text())
        if receipt.get("status") != "ready" or receipt.get("scene_id") != scene["id"]:
            raise RecordingError(f"{scene['id']}: receipt is not an accepted live recording")
        result = receipt.get("result", {})
        if (result.get("mode") != "live" or result.get("provider") != "baseten"
                or result.get("model") != "meta-models/muse-spark-open-1026"):
            raise RecordingError(f"{scene['id']}: real Baseten Muse result required")
        if not live_copy_supported(result):
            raise RecordingError(f"{scene['id']}: measured cost/time receipt missing or bounded")
        check_choreography(receipt)
        if scene['id'] == 'v406' and scene.get('cue_events') != live_cue_events(scene, receipt):
            raise RecordingError("v406: cue times differ from the wired receipt")
        for kind in ("webm", "mp4"):
            artifact = receipt[kind]
            path = (root / artifact["path"]).resolve()
            if (not path.is_relative_to(root.resolve()) or not path.is_file()
                    or digest(path) != artifact["sha256"]):
                raise RecordingError(f"{scene['id']}: {kind} missing or changed since recording")
            media = probe(path)
            if (not math.isfinite(media["duration_s"]) or media["duration_s"] < scene["target_s"]
                    or (media["width"], media["height"]) != (1920, 1080)):
                raise RecordingError(f"{scene['id']}: {kind} is shorter than the scene or is not 1920×1080")
            if kind == "mp4" and media["fps"] != "30/1":
                raise RecordingError(f"{scene['id']}: MP4 must be 30 fps")
        if receipt["mp4"]["path"] != recording["asset"]:
            raise RecordingError(f"{scene['id']}: storyboard asset differs from the receipt")
        records[scene["id"]] = receipt
    if required and set(records) != set(BEATS):
        raise RecordingError("Both live scenes are required")
    return records


@contextmanager
def site_snapshot(ref):
    """Read committed main into a disposable directory; never merge over local work."""
    commit = subprocess.check_output(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
                                     cwd=ROOT, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="v4-site-") as temporary:
        directory = Path(temporary)
        archive = directory / "site.tar"
        with archive.open("wb") as file:
            subprocess.run(["git", "archive", "--format=tar", commit, "docs"],
                           cwd=ROOT, stdout=file, check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(directory, filter="data")
        docs = directory / "docs"
        html = (docs / "site/index.html").read_text()
        if 'id="live-password"' not in html or 'id="live-result"' not in html:
            raise RecordingError("The selected site commit lacks the merged live-check / corrected-draft UI")
        sources = {f"docs/site/{name}": digest(docs / "site" / name)
                   for name in ("index.html", "script.js", "styles.css", "data/live-demo-post.json")}
        yield docs, {"ref": ref, "commit": commit, "docs_archive_sha256": digest(archive), "sources": sources}


@contextmanager
def serve(docs, port):
    spec = importlib.util.spec_from_file_location("v4_preview", ROOT / "scripts/serve_site.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.ThreadingHTTPServer(("127.0.0.1", port), module.Handler)
    server.docs_root, server.proxy_api = docs, ORIGIN
    server.max_checks, server.check_count, server.check_lock = 1, 0, threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def convert(source, target, *, start=None, webm=False):
    command = [str(FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "error", "-n"]
    if start is not None:
        command += ["-ss", f"{start:.6f}"]
    command += ["-i", str(source), "-an", "-vf", "scale=1920:1080,fps=30"]
    command += (["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "24"] if webm else
                ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    subprocess.run([*command, str(target)], capture_output=True, check=True)


def wire_storyboard(receipts, stamp):
    original = STORYBOARD.read_text()
    story = yaml.safe_load(original)
    for scene in story["scenes"]:
        if scene["id"] not in receipts:
            continue
        receipt_path = receipts[scene["id"]]
        receipt = json.loads(receipt_path.read_text())
        scene.pop("placeholder", None)
        scene["renderer"] = "live-site" if scene["id"] == "v406" else "result-site"
        scene["recording"] = {"asset": receipt["mp4"]["path"],
                              "receipt": receipt_path.relative_to(ROOT).as_posix(), "offset_s": 0.0,
                              "timings":receipt["timings"],"receipt_sha256":digest(receipt_path),
                              "capture_version":receipt["capture_version"]}
        if scene['id'] == 'v406':
            scene['cue_events'] = live_cue_events(scene, receipt)
        scene["on_screen"] = "Live product · corrected draft + SEC filing" if scene["id"] == "v409" else "Live product · SEC evidence · agent trace · measured receipt"
        scene["director_notes"] = "Real product recording; uncut source. Locked scene duration; first scene-length seconds used."
    check_recordings(story)
    (OUT / f"storyboard-before-{stamp}.yaml").write_text(original)
    temporary = STORYBOARD.with_suffix(".yaml.tmp")
    temporary.write_text("# Director v4 r3: exact cuts; real site assets have retained receipts.\n" +
                         yaml.safe_dump(story, sort_keys=False, allow_unicode=True, width=105))
    temporary.replace(STORYBOARD)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--site-ref", default="main", help="Committed site source (default: merged main)")
    parser.add_argument("--check", action="store_true", help="Require existing, sufficiently long storyboard takes; no network")
    parser.add_argument("--preflight", action="store_true", help="Check host browser/media prerequisites; no API requests")
    args = parser.parse_args()
    if args.check:
        check_recordings(yaml.safe_load(STORYBOARD.read_text()))
        print("PASS both v4 live takes exist, match receipts, and cover their exact scenes")
        return
    if not os.environ.get("PLAYWRIGHT_MODULE"):
        raise RecordingError("Set PLAYWRIGHT_MODULE to an existing Playwright package directory")
    if not FFMPEG.is_file() or not FFPROBE.is_file():
        raise RecordingError("Homebrew ffmpeg and ffprobe are required")
    environment = dict(os.environ)
    for key in ("DEBUG", "PWDEBUG", "NODE_OPTIONS", "NODE_DEBUG"):
        environment.pop(key, None)
    worker = ROOT / "demo/record_v4.mjs"
    if args.preflight:
        result = subprocess.run(["node", str(worker), "--preflight"], env=environment, capture_output=True)
        if result.returncode:
            raise RecordingError("Host preflight failed: check Playwright / Chromium availability; no live call attempted")
        print("PASS host Chromium, Playwright, ffmpeg and ffprobe; no live call attempted")
        return
    password_file = environment.get("LIVE_CHECK_PASSWORD_FILE")
    if not password_file or not Path(password_file).is_file():
        raise RecordingError("Set LIVE_CHECK_PASSWORD_FILE to an existing private password file; do not pass the password itself")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    OUT.mkdir(parents=True, exist_ok=True)
    run_path = OUT / f"run-{stamp}.json"
    config_path = OUT / f"config-{stamp}.json"
    run = {"status": "started", "timestamp": stamp, "live_check_limit": 1,
           "retry_policy": "one request; no automatic retries; failed/partial runs retained",
           "storyboard_sha256_before": digest(STORYBOARD),
           "implementation": {p.relative_to(ROOT).as_posix(): digest(p)
                              for p in (Path(__file__).resolve(), worker, ROOT / "scripts/serve_site.py")}}
    save(run_path, run)
    try:
        with site_snapshot(args.site_ref) as (docs, source), serve(docs, args.port) as url:
            run.update(site_source=source, page_url=url)
            save(run_path, run)
            worker_path = OUT / f"session-{stamp}.json"
            save(config_path, {"page_url": url, "out": str(OUT), "stamp": stamp,
                               "receipt": str(worker_path)})
            print(f"Recording {url} from {source['commit'][:12]}; at most one paid check, no retry.", flush=True)
            result = subprocess.run(["node", str(worker), str(config_path)], env=environment, capture_output=True)
            if result.returncode or not worker_path.is_file():
                raise RecordingError("Capture did not complete; inspect the retained session receipt's failure_stage on the host")
            session = json.loads(worker_path.read_text())
            if session.get("status") != "captured":
                raise RecordingError("Capture did not pass the live-result / choreography gate; attempt retained")
        raw = OUT / f"beat6-{stamp}.webm"
        media = probe(raw)
        span = session["beat9_span_s"]
        if span < 16 or media["duration_s"] < span + 50:
            raise RecordingError("Recording is too short; no scene was wired")
        beat9 = OUT / f"beat9-{stamp}.webm"
        convert(raw, beat9, start=media["duration_s"] - span, webm=True)
        receipts = {}
        for scene_id, (beat, minimum) in BEATS.items():
            webm = OUT / f"{beat}-{stamp}.webm"
            mp4 = webm.with_suffix(".mp4")
            convert(webm, mp4)
            supported = live_copy_supported(session["result"])
            receipt = {**run, "status": "ready" if supported else "needs-director-review", "scene_id": scene_id, "scene_duration_s": minimum,
                       "locked_live_copy_supported": supported,
                       "capture_version": 5,
                       "viewport": [1920, 1080], "deviceScaleFactor": 1, "zoom": 1.6,
                       "result": session["result"], "timings": session["timings"],
                       "presentation": session["presentation"],
                       "readability": session["readability"],
                       "choreography": {k: session[k] for k in ("trace_details_open", "trace_steps_shown", "tool_calls_shown",
                           "program_verdict_shown", "apple_inspect_open", "apple_derivation", "after_click_s", "beat6_actions_end_s")},
                       "source_session": worker_path.relative_to(ROOT).as_posix(),
                       "native_ui": session["native_ui"], "trim": "first scene-duration seconds; source retained uncut"}
            for kind, path in (("webm", webm), ("mp4", mp4)):
                receipt[kind] = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), **probe(path)}
            receipt_path = webm.with_suffix(".json")
            save(receipt_path, receipt)
            receipts[scene_id] = receipt_path
        wire_storyboard(receipts, stamp)
        run.update(status="ready", receipts={k: p.relative_to(ROOT).as_posix() for k, p in receipts.items()},
                   storyboard_sha256_after=digest(STORYBOARD))
        print("Saved beat6/beat9 WebM, 1920×1080 30 fps MP4, redacted receipts; storyboard assets wired.")
    except Exception:
        run.update(status="failed", failure="Retained partial attempt; no automatic retry; storyboard wiring requires both validated takes")
        raise
    finally:
        save(run_path, run)


if __name__ == "__main__":
    try:
        main()
    except RecordingError as error:
        # These messages are authored locally and never contain request data.
        print(str(error))
        raise SystemExit(1)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        # Avoid subprocess/Playwright diagnostics that could echo fill() arguments.
        print("Recorder stopped. Check prerequisites / retained run and session receipts. No automatic retry.")
        raise SystemExit(1)
