#!/usr/bin/env python3
"""Record one live check and its result on committed main, with no automatic retry.

Host: PLAYWRIGHT_MODULE=/path/to/playwright LIVE_CHECK_PASSWORD_FILE=/private/file
      uv run --project demo python demo/record_v5.py --port 8765
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
OUT = ROOT / "demo/cache/live-takes/v5"
STORYBOARD = ROOT / "demo/storyboard-v5.yaml"
FFMPEG = Path("/opt/homebrew/bin/ffmpeg")
FFPROBE = Path("/opt/homebrew/bin/ffprobe")
ORIGIN = "https://hackathon.dappgo.com"
BEATS = {"v505": ("beat6", 58.0), "v508": ("beat9", 16.0)}
CAPTURE_VERSION = 9
LIVE_PHASES = ('live_workspace_reveal','use_apple_example','check_against_sec','verdict_reveal','draft_reveal',
               'evidence_reveal','tool_call_2_reveal','tool_call_4_reveal','program_verdict_reveal','hover_receipt')


class RecordingError(RuntimeError):
    pass


def apple_filing_citations(result):
    """Project the actual E3 components and correction links, never invented sources."""
    fact=next((e for e in result.get('evidence',[]) if e.get('evidence_id')=='E3'
               and e.get('ticker')=='AAPL' and e.get('derived')),None)
    edit=next((e for e in result.get('corrections',{}).get('edits',[])
               if e.get('original')=='$416.2 billion' and e.get('replacement')=='$102.5 billion'
               and 'E3' in e.get('evidence_ids',[])),None)
    if not fact or not edit:
        raise RecordingError('Apple E3 derived fact and cited correction required')
    citations=[]
    for form,kind in (('10-K','annual'),('10-Q','ytd')):
        component=next((c for c in fact.get('components',[]) if c.get('form')==form and c.get('period_type')==kind),None)
        citation=next((c for c in edit.get('citations',[]) if c.get('evidence_id')=='E3' and c.get('form')==form),None)
        if (not component or not citation or not citation.get('url','').startswith('https://www.sec.gov/Archives/')
            or any(component.get(k)!=citation.get(k) for k in ('accn','value','start','end','period_type'))):
            raise RecordingError('Apple SEC citation must match its E3 component form and period')
        end=datetime.strptime(component['end'],'%Y-%m-%d')
        label=f"fiscal {fact['fiscal_year']} annual" if kind=='annual' else f"nine months to {end.day} {('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')[end.month-1]} {end.year}"
        citations.append(dict(evidence_id='E3',form=form,period_label=label,**{k:citation[k] for k in ('url','accn','start','end')}))
    return citations


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
    events = []
    for spec in scene["cue_events"]:
        phase = spec.get("receipt_phase")
        if phase not in phases or spec.get('offset_s',0)!=0:
            raise RecordingError('Every live cue must start exactly at its recorded picture phase')
        at = phases[phase]
        if type(at) not in (float, int) or not math.isfinite(at) or not 0 <= at < scene["target_s"]:
            raise RecordingError("Live narration cue falls outside the locked scene")
        events.append({**spec, "at_scene_s": at})
    return events


def check_choreography(receipt):
    proof=receipt.get('choreography',{});result=receipt.get('result',{})
    calls=[i for i,e in enumerate(result.get('events',[])) if e.get('kind')=='tool_call']
    shown=proof.get('trace_steps_shown',[]);derived=proof.get('apple_derivation',{})
    geometry=receipt.get('geometry_checks',[]);language=receipt.get('language_checks',[])
    ending=receipt.get('ending_frame',{})
    check_startup_cover(receipt)
    if (receipt.get('capture_version')!=CAPTURE_VERSION or receipt.get('zoom')!=1.95
        or not proof.get('trace_details_open')
        or not proof.get('program_verdict_shown') or len(calls)!=4
        or [s['index'] for s in shown if s['kind']=='tool_call' and s.get('visible')]!=calls
        or any(s.get('hold_ms',0)<700 for s in shown)
        or not 0<proof.get('beat6_actions_end_s',math.inf)<=57.5
        or not 0<proof.get('after_click_s',math.inf)<=56
        or round(derived.get('annual',0)/1e9,1)!=416.2 or round(derived.get('nine_months',0)/1e9,1)!=313.7
        or round(derived.get('quarter',0)/1e9,1)!=102.5
        or derived.get('annual',0)-derived.get('nine_months',0)!=derived.get('quarter')
        or receipt.get('live_checks')!=1 or not geometry or not language
        or not ending.get('visible_together') or ending.get('both_links',0)<2):
        raise RecordingError('v5 requires four tools, open trace/Apple inspector, native ending, geometry and English DOM proof')
    for g in geometry:
        if (not all(type(g.get(k)) in (int,float) and math.isfinite(g[k]) for k in ('source_width','left_margin','right_margin','horizontal_overflow'))
            or g.get('source_width',0)<1500 or min(g.get('left_margin',0),g.get('right_margin',0))<60
            or abs(g['left_margin']-g['right_margin'])>4 or g.get('horizontal_overflow',math.inf)>1 or g.get('zoom')!=1.95):
            raise RecordingError('v5 workspace must span >=1500 px with equal >=60 px margins')
    if any(c.get('text_nodes',1) or c.get('attributes',1) or c.get('language_switches',1) for c in language):
        raise RecordingError('v5 capture DOM contains non-English glyphs or a language switch')
    phases={t['phase'] for t in receipt['timings']}
    if not set(LIVE_PHASES)<=phases:
        raise RecordingError('v5 live overlay phases are incomplete')
    check_named_elements(receipt)


def check_startup_cover(receipt):
    """Only a pre-content cover released after a passing audit can enter the film."""
    cover=receipt.get('startup_cover',{});geometry=receipt.get('geometry_checks',[])
    index=cover.get('release_geometry_index');released=cover.get('released_at_s')
    rect=cover.get('workspace_rect',{})
    calibration=('source_start_s','first_native_frame_s','source_cover_release_s','video_clock_offset_s')
    if (receipt.get('capture_version')!=CAPTURE_VERSION or not cover.get('injected_before_content')
        or cover.get('colour')!='#f7f5ef' or not cover.get('cover_present') or not cover.get('cover_opaque') or not cover.get('layout_installed')
        or cover.get('zoom')!=1.95 or type(index) is not int or not 0<=index<len(geometry)
        or type(released) not in (int,float) or not math.isfinite(released)
        or not geometry[index].get('at_s',math.inf)<=released or abs(released)>.75
        or not cover.get('workspace_framed_before_release') or not cover.get('decoded_workspace_start')
        or not 60<=rect.get('left',-1)<rect.get('right',0)<=1860 or not 80<=rect.get('top',-1)<rect.get('bottom',0)<=548
        or not all(type(cover.get(k)) in (int,float) and math.isfinite(cover[k]) for k in calibration)):
        raise RecordingError('v9 audited startup cover, card band and decoded workspace start required; re-record on the host')
    if (abs(cover['source_start_s']-cover['first_native_frame_s']-.1)>1e-7
        or abs(cover['video_clock_offset_s']-cover['first_native_frame_s']+cover['source_cover_release_s'])>1e-7
        or abs(released+.1)>1e-7):
        raise RecordingError('Decoded cover edge must calibrate the page/video clocks before cue placement')


def check_named_elements(receipt):
    phases={t['phase']:t['at_s'] for t in receipt['timings']}
    expected=set(LIVE_PHASES)|{p for p in phases if p.startswith('tool_call_') and p.endswith('_reveal')}|{'agent_trace_expand','program_verdict_reveal'}
    checks=receipt.get('named_element_checks',[])
    if {c.get('phase') for c in checks}!=expected or len(checks)!=len(expected):
        raise RecordingError('Named element rectangles required at every live cue onset and trace step')
    for check in checks:
        if check.get('at_s')!=phases[check['phase']] or not check.get('elements') or check.get('visible_until_s',-1)<=check['at_s']:
            raise RecordingError('Named element rectangles must use the exact recorded phase onset')
        for r in check['elements']:
            if (not all(type(r.get(k)) in (int,float) and math.isfinite(r[k]) for k in ('left','right','top','bottom'))
                or not 60<=r['left']<r['right']<=1860 or not 0<=r['top']<r['bottom']<=766):
                raise RecordingError('Named live element must be fully visible above the chapter lane')
            band=check.get('overlay_band')
            if band not in ('top','bottom') or (band=='top' and r['top']<270) or (band=='bottom' and r['bottom']>548):
                raise RecordingError('Opaque overlay band intersects the named native element')
        audit=check.get('card_edge_audit',{})
        band={'left':80,'right':1840,'top':558,'bottom':790} if check['overlay_band']=='bottom' else {'left':80,'right':1840,'top':24,'bottom':250}
        if audit.get('status')!='pass' or audit.get('band')!=band or not audit.get('lines') or not isinstance(audit.get('controls'),list):
            raise RecordingError('Native text line and control audit required at every card cue onset')
        for r in [*audit['lines'],*audit['controls']]:
            if (not all(type(r.get(k)) in (int,float) and math.isfinite(r[k]) for k in ('left','right','top','bottom'))
                or r['left']>=r['right'] or r['top']>=r['bottom']):
                raise RecordingError('Invalid native text line rectangle')
            edges=(band['top'],) if check['overlay_band']=='bottom' else (band['top'],band['bottom'])
            if r['left']<band['right'] and r['right']>band['left'] and any(r['top']<y<r['bottom'] for y in edges):
                raise RecordingError('Native text line or control crosses the card edge at cue onset')
        if check['phase']=='verdict_reveal':
            charge=audit.get('input_charge',{});heading=audit.get('corrected_heading',{})
            if (not charge or charge.get('bottom',math.inf)>0 or not heading
                or not (heading.get('top',-1)>=558 or 0<=heading.get('top',-1)<heading.get('bottom',math.inf)<=558)):
                raise RecordingError('Verdict must exclude input reading charge and show or mask the whole corrected heading')
    ending=receipt.get('ending_frame',{}).get('named_elements',[])
    if len(ending)!=3 or any(not 60<=r.get('left',0)<r.get('right',0)<=1860 or not 80<=r.get('top',0)<r.get('bottom',0)<=586 for r in ending):
        raise RecordingError('Ending draft and citation rectangles required for overlay review')


def probe(path):
    completed = subprocess.run(
        [str(FFPROBE), "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path)],
        capture_output=True, check=True, text=True)
    data = json.loads(completed.stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    return {"duration_s": float(data["format"]["duration"]),
            "width": video["width"], "height": video["height"], "fps": video["r_frame_rate"]}


def workspace_start(frames, released_at_s, *, width=96, height=54, fps=30):
    """Find three decoded non-paper workspace frames after the covered startup.

    The cover is held until Try is framed. The first varied frames can therefore
    only be the native workspace. Never use the page clock alone as a video trim.
    Pure paper, white and black encoder-start frames all fail the variation test.
    """
    size=width*height;run=0
    for i in range(len(frames)//size):
        frame=frames[i*size:(i+1)*size]
        dark=sum(p<210 for p in frame)/size
        run=run+1 if .005<dark<.9 and max(frame)-min(frame)>60 else 0
        if run>=3:
            start=(i+1)/fps
            if abs(start-released_at_s)>.75:raise RecordingError('Decoded workspace start differs from cover clock; retain attempt for review')
            return start
    raise RecordingError('No stable native workspace after the startup cover; retain attempt')


def select_workspace_start(raw,session):
    released=session['startup_cover']['released_at_s']
    frames=subprocess.run([str(FFMPEG),'-nostdin','-v','error','-i',str(raw),'-t',str(released+2),
        '-vf','fps=30,scale=96:54','-pix_fmt','gray','-f','rawvideo','-'],capture_output=True,check=True).stdout
    return workspace_start(frames,released)


def workspace_clock(session,start):
    """Normalize audit clocks to the continuous MP4 selection; retain raw receipt."""
    import copy
    selected=copy.deepcopy(session)
    released=session['startup_cover']['released_at_s']
    # The decoded cover -> workspace edge calibrates Playwright's page clock to
    # the actual video clock. Merely subtracting the trim would retain any encoder
    # startup offset in every subsequent picture/speech binding.
    first_native=start-3/30
    video_offset=first_native-released
    shift=start-video_offset
    for collection in ('timings','geometry_checks','language_checks','named_element_checks'):
        for item in selected[collection]:
            item['at_s']-=shift
            if 'visible_until_s' in item:item['visible_until_s']-=shift
            if item.get('phase')=='live_workspace_reveal':item['at_s']=0.
    selected['startup_cover']['released_at_s']-=shift
    selected['startup_cover'].update(decoded_workspace_start=True,source_start_s=start,first_native_frame_s=first_native,
        source_cover_release_s=released,video_clock_offset_s=video_offset,
        selection='Three decoded native workspace frames; cover edge calibrates page/video clocks; no paper/hero/stamp frames')
    selected['beat6_actions_end_s']-=shift
    return selected


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
                raise RecordingError(f"{scene['id']}: live take missing; run demo/record_v5.py on the host")
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
        if digest(root / recording["receipt"]) != recording.get("receipt_sha256"):
            raise RecordingError("Live receipt changed since storyboard wiring")
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
        if scene['id'] == 'v505' and scene.get('cue_events') != live_cue_events(scene, receipt):
            raise RecordingError("v505: cue times differ from the wired receipt")
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
    with tempfile.TemporaryDirectory(prefix="v5-site-") as temporary:
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
    spec = importlib.util.spec_from_file_location("v5_preview", ROOT / "scripts/serve_site.py")
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
        scene["renderer"] = "live-site" if scene["id"] == "v505" else "result-site"
        scene["recording"] = {"asset": receipt["mp4"]["path"],
                              "receipt": receipt_path.relative_to(ROOT).as_posix(), "offset_s": 0.0,
                              "timings":receipt["timings"],"receipt_sha256":digest(receipt_path),
                              "capture_version":receipt["capture_version"]}
        if scene['id'] == 'v505':
            scene['cue_events'] = live_cue_events(scene, receipt)
        scene["on_screen"] = "Live product · corrected draft + SEC filing" if scene["id"] == "v508" else "Live product · SEC evidence · agent trace · measured receipt"
        scene["director_notes"] = "One continuous workspace selection after the decoded startup cover; raw WebM retained uncut. Locked scene duration."
    check_recordings(story)
    (OUT / f"storyboard-before-{stamp}.yaml").write_text(original)
    temporary = STORYBOARD.with_suffix(".yaml.tmp")
    temporary.write_text("# Director v5: exact cuts; real site assets have retained receipts.\n" +
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
        print("PASS both v5 live takes exist, match receipts, and cover their exact scenes")
        return
    if not os.environ.get("PLAYWRIGHT_MODULE"):
        raise RecordingError("Set PLAYWRIGHT_MODULE to an existing Playwright package directory")
    if not FFMPEG.is_file() or not FFPROBE.is_file():
        raise RecordingError("Homebrew ffmpeg and ffprobe are required")
    environment = dict(os.environ)
    for key in ("DEBUG", "PWDEBUG", "NODE_OPTIONS", "NODE_DEBUG"):
        environment.pop(key, None)
    worker = ROOT / "demo/record_v5.mjs"
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
        start=select_workspace_start(raw,session)
        session=workspace_clock(session,start)
        span = session["beat9_span_s"]
        if span < 16 or media["duration_s"] < span + 58:
            raise RecordingError("Recording is too short; no scene was wired")
        beat9 = OUT / f"beat9-{stamp}.webm"
        convert(raw, beat9, start=media["duration_s"] - span, webm=True)
        receipts = {}
        for scene_id, (beat, minimum) in BEATS.items():
            webm = OUT / f"{beat}-{stamp}.webm"
            mp4 = webm.with_suffix(".mp4")
            convert(webm, mp4,start=start if scene_id=='v505' else None)
            supported = live_copy_supported(session["result"])
            receipt = {**run, "status": "ready" if supported else "needs-director-review", "scene_id": scene_id, "scene_duration_s": minimum,
                       "locked_live_copy_supported": supported,
                       "capture_version": CAPTURE_VERSION,
                       "viewport": [1920, 1080], "deviceScaleFactor": 1, "zoom": 1.95,
                       "result": session["result"], "timings": session["timings"],
                       "presentation": session["presentation"],
                       "readability": session["readability"],
                       "geometry_checks": session["geometry_checks"], "language_checks": session["language_checks"],
                       "startup_cover": session["startup_cover"], "named_element_checks": session["named_element_checks"],
                       "live_checks": session["live_checks"], "ending_frame": session["ending_frame"],
                       "choreography": {k: session[k] for k in ("trace_details_open", "trace_steps_shown", "tool_calls_shown",
                           "program_verdict_shown", "apple_inspect_open", "apple_derivation", "after_click_s", "beat6_actions_end_s")},
                       "source_session": worker_path.relative_to(ROOT).as_posix(),
                       "native_ui": session["native_ui"], "trim": "continuous workspace selection after decoded cover release; raw source retained uncut"}
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
