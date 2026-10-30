"""v007 evidence compiler. CLI preparation reads recorded files only; no media generation.

Host build.py uses the same compiler after locked-clone narration is measured.
The approved v006 timeline/data stay in motion/; this revision lives in motion/v3/.
"""
from __future__ import annotations

import argparse
import array
from bisect import bisect_left
import json
import math
from pathlib import Path
import re
import sys
import wave

import yaml

from motion_cues import cue_document, detect_silences, map_sentences
from motion_data import product_data
from motion_timing import narration_start, next_beat, presentation_timing, video_beats
from pipeline import BuildError, file_hash, read_json

ROOT = Path(__file__).resolve().parents[1]
STORY = 'demo/storyboard-v3.yaml'
L4 = 'docs/evidence/eval-l4-2026-10-29'
MM = 'docs/evidence/multimodal-2026-10-30'
RECALL = 'docs/evidence/multimodal-2026-10-30b'
OUT = 'demo/motion/v3'


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def hover_source(repo: Path) -> str:
    """Adapt verbatim site clock/pose/spotlight expressions, without its DOM/playback.

    Slice boundaries deliberately fail closed if the site's implementation changes.
    The small wrapper supplies the original DOM targets as plain state objects.
    No eval, browser, copied asset files, or changes to the website are needed.
    """
    source = (repo / 'docs/site/script.js').read_text()
    def between(start, end):
        return source.split(start, 1)[1].split(end, 1)[0]
    constants = 'const CHECKABLE =' + between('const CHECKABLE =', 'const checkable =')
    policies = 'const checkable =' + between('const checkable =', 'let elapsed =')
    # policies contains the real loop-duration setup, clamp/easing and facing map.
    phase = 'function phaseAt(' + between('function phaseAt(', 'function paintRobot(')
    robot = between('function paintRobot(age, card) {', 'if (!geometry) return { x: 0, y: 0 };')
    geometry = 'const emptyBox =' + between('const emptyBox =', 'function setBox(')
    cone = 'function conePoints(' + between('function conePoints(', 'function paintSpotlight(')
    lighting = between('function paintSpotlight(age, item, visor) {', 'const poolCenter = center(row);')
    # Page measurement, localization and DOM painting are excluded.
    return ('// Generated from docs/site/script.js; run demo/motion_v3.py to refresh.\n'
            f'// Site SHA-256: {file_hash(repo / "docs/site/script.js")}\n'
            '(function(root) {\n"use strict";\n'
            + geometry + cone + 'function state(age, card, elapsed=age, targets=null) {\n'
            'const cards=[card], poses=Object.fromEntries(["idle","inspect","reach","present",'
            '"point","think","stamp","stamp-down","approve","concern","shrug"]'
            '.map(name=>[name,{style:{}}]));\n'
            'const robot={style:{},dataset:{}};\n' + constants + policies + phase + robot +
            '\nconst item={light:targets||{post:emptyBox,row:emptyBox,compare:emptyBox,search:[emptyBox]}}, motion={matches:false};\n' + lighting +
            '\nreturn {phase:phaseAt(age,canCheck),pose,previous,blend,bob,dip,lean,'
            'transform:robot.style.transform,thruster:robot.dataset.thruster,'
            'visor:POSE_VISORS[pose],nozzle:POSE_ANCHORS[pose].nozzle,canvas:POSE_CANVAS,'
            'facing:facing[pose],postAlpha,filingAlpha,yearAlpha,shade:compareIn*lift,'
            'finding,comparing,locked:age>=FIND_LOCK,row,filingTarget};\n}\n'
            'const api={state,conePoints}; if(typeof module==="object"&&module.exports)module.exports=api;'
            'else root.HoverSource=api;\n})(globalThis);\n')


def waveform(path: Path, bins=64) -> list[float]:
    """Measured peaks of the committed synthetic PCM; no playback or synthesis."""
    with wave.open(str(path)) as audio:
        if audio.getsampwidth() != 2:
            raise BuildError('Expected committed 16-bit synthetic WAV.')
        samples = array.array('h', audio.readframes(audio.getnframes()))
    if sys.byteorder != 'little':
        samples.byteswap()
    step = math.ceil(len(samples) / bins)
    return [round(max(map(abs, samples[i:i+step]), default=0) / 32768, 6)
            for i in range(0, len(samples), step)]


def evidence_data(repo: Path) -> dict:
    product = product_data(repo)
    disclosure = re.search(r'^> (.+)$', (repo / 'demo/JUDGE_INTRO.md').read_text(), re.M)
    if not disclosure:
        raise BuildError('Complete JUDGE_INTRO disclosure is missing.')
    site = read_json(repo / 'docs/site/data/site.json')
    results = {r['id']: r for r in map(json.loads, (repo / L4 / 'results.jsonl').read_text().splitlines())}
    releases = []
    for identifier in ('L4-01', 'L4-27'):
        row = results[identifier]
        trace_path = f'{L4}/{row["trace"]}'
        trace = read_json(repo / trace_path)
        card = next(c for c in site['stamp_cards'] if c.get('claim_id') == identifier)
        if row['predicted'] != 'supported' or trace['final_verdict']['verdict'] != 'supported':
            raise BuildError(f'{identifier}: recorded release verdict changed.')
        original = trace['program_checks'][0]['release_evidence']
        for field in ('quote', 'period', 'value', 'low', 'high', 'claim_kind', 'metric'):
            if card['excerpt']['source_evidence'].get(field) != original.get(field):
                raise BuildError(f'{identifier}: site excerpt differs from its raw trace ({field}).')
        releases.append(dict(id=identifier, claim=row['claim'], kind=row['kind'],
                             verdict=row['predicted'], excerpt=card['excerpt'],
                             source=trace_path, checks=trace['program_checks']))
    inputs = {}
    for kind, channel in [('screenshot', 'image'), ('audio', 'audio'), ('text', 'text')]:
        # 30b reran the text control only; retain the original screenshot/audio runs.
        folder = f'{RECALL if kind == "text" else MM}/{kind}'
        source = f'{folder}/checks/{channel}/report.json'
        report = read_json(repo / source)
        candidates = [(claim, check) for claim in report['claims'] for check in claim['program_checks']
                      if re.search(r'\bEPS\b|earnings per share', check.get('text', ''), re.I)
                      and '$1.67' in check.get('text', '')]
        if len(candidates) != 1:
            raise BuildError(f'{kind}: deliberate EPS check is ambiguous.')
        claim, check = candidates[0]
        if check['program_verdict'] != 'contradicted' or claim['verdict'] != 'contradicted':
            raise BuildError(f'{kind}: retained EPS verdict changed.')
        if (check['stated_value_used'], check['actual_value']) != (1.67, 1.57):
            raise BuildError(f'{kind}: retained EPS values changed.')
        ingest_source = f'{folder}/ingest.json'
        trace_source = f'{folder}/checks/{channel}/{claim["trace_path"]}'
        ingest = read_json(repo / ingest_source)
        period = re.search(r'fiscal (Q[1-4]) (\d{4})', check['text'])
        if not period:
            raise BuildError(f'{kind}: EPS check lost its fiscal period.')
        inputs[kind] = dict(source=source, ingest_source=ingest_source, trace_source=trace_source,
                            evidence=claim['evidence'], quote=claim['quote'], check=check,
                            verdict=claim['verdict'], input=ingest['input'],
                            segments=ingest['channels'][0]['segments'],
                            period_label=f'FY{period[2]} {period[1]}')
        if kind=='audio':
            fragment='quarterly diluted earnings per share of 1.67 dollars'
            if fragment not in claim['quote']:
                raise BuildError('Synthetic audio exact EPS clause changed.')
            inputs[kind]['display_quote']=fragment
    comparison_source = f'{RECALL}/before-after.json'
    comparison = read_json(repo / comparison_source)
    coverage = {}
    for label, run, channel in [('live', 'long-call-r2', 'audio'),
                                ('frozen_asr', 'long-call-frozen', 'text')]:
        after = comparison['runs'][run]['after']
        counts = after['channels'][channel]['recall']
        source = f'{RECALL}/{run}/ingest.json'
        ingest = read_json(repo / source)
        if (after['status'] != ingest['status'] or after['status'] != 'completed'
                or not 0 <= counts['accepted'] == counts['program_checked'] <= counts['expected']
                or counts['expected'] <= 0):
            raise BuildError(f'{run}: recorded guarded/program-checked coverage is inconsistent.')
        coverage[label] = dict(source=source, comparison_source=comparison_source, channel=channel,
                               guarded=counts['accepted'], program_checked=counts['program_checked'],
                               expected=counts['expected'], status=after['status'])
        if label == 'live':
            limitation = next((line for line in ingest['limitations']
                               if 'speaker labels are not names or roles' in line), None)
            if not limitation:
                raise BuildError('Long-call speaker-label limitation is missing.')
            speaker_identity = dict(verified=False, source=source, limitation=limitation)
    fixture = repo / 'tests/fixtures/multimodal/example-post.png'
    audio = repo / 'tests/fixtures/multimodal/release-reading.wav'
    for kind, path in [('screenshot', fixture), ('audio', audio)]:
        if inputs[kind]['input']['sha256'] != file_hash(path):
            raise BuildError(f'{kind}: fixture differs from the recorded input.')
    summary = read_json(repo / 'docs/evidence/eval-v2-2026-10-27/summary.json')
    scores = []
    for provider, label in [('meta', 'Meta API'), ('baseten', 'Baseten'), ('fireworks', 'Fireworks')]:
        values = []
        for system in ('single_shot', 'agent'):
            splits = summary['metrics'][f'{system}@{provider}'].values()
            n = sum(s['n_claims'] for s in splits)
            correct = sum(s['correct'] for s in splits)
            if n != product['claim_count']:
                raise BuildError('Original v2 counts disagree.')
            values.append(dict(correct=correct, total=n, percent=round(100*correct/n, 1)))
        scores.append(dict(provider=provider, label=label, alone=values[0], checked=values[1]))
    source_paths = {f'{L4}/results.jsonl', f'{L4}/REPORT.md', f'{MM}/REPORT.md', f'{RECALL}/REPORT.md',
                    comparison_source, *(r['source'] for r in coverage.values()),
                    'demo/JUDGE_INTRO.md', 'docs/site/script.js',
                    'docs/site/img/auditor/H/manifest.json', 'tests/fixtures/multimodal/generation.json',
                    'tests/fixtures/multimodal/example-post.png', 'tests/fixtures/multimodal/release-reading.wav',
                    *(r['source'] for r in releases), *(r['source'] for r in inputs.values()),
                    *(r['ingest_source'] for r in inputs.values()),
                    *(r['trace_source'] for r in inputs.values())}
    source_paths.update(p.relative_to(repo).as_posix() for p in (repo/'docs/site/img/auditor/H').glob('*.webp'))
    source_paths.update('docs/site/img/'+p for p in ('stamp-paper.webp', 'fx/beam-pool.webp', 'fx/lens-flare.webp'))
    return dict(base=product, disclosure=disclosure[1], releases=releases, inputs=inputs, scores=scores,
                recall=dict(source=comparison_source, report_source=f'{RECALL}/REPORT.md',
                            policy=comparison['policy'], coverage=coverage,
                            speaker_identity=speaker_identity),
                apple_check=read_json(repo/'demo/data/demo-thread.json')['claims'][2]['program_checks'][0],
                apple_evidence_ids=[e['id'] for e in read_json(repo/'demo/data/demo-thread.json')['claims'][2]['evidence']],
                waveform=waveform(audio),
                provenance={**product['provenance'], **{p:file_hash(repo/p) for p in sorted(source_paths)}})


def hover_anchors(shot: dict, events: dict, beats: list[float]) -> list[tuple[float, int]]:
    """Spend the lead on reading/reaching/searching; lock on the spoken find cue.

    Reserve distinct detected beats inside each window. Sparse grids may move a
    pose from its preferred beat, but never reorder poses or move spoken events.
    """
    error = 'Hover narration cues leave no beat for its pose sequence; review the host timings.'

    def between(start, end, count=1, targets=None):
        available = [b for b in beats if start < b < end]
        if len(available) < count:
            raise BuildError(error)
        targets = targets or [start+(end-start)*(i+1)/(count+1) for i in range(count)]
        chosen, previous = [], -1
        for i, target in enumerate(targets):
            index = min(max(previous+1, bisect_left(available, target)), len(available)-count+i)
            chosen.append(available[index])
            previous = index
        return chosen

    voice_start = shot.get('voice_start', shot['start'])
    if voice_start > shot['start']:
        read, reach, find = between(shot['start'], voice_start, 3)
        lock = events['find']
    else:
        read, reach = between(shot['start'], events['find'], 2)
        find = events['find']
        lock, = between(find, events['compare'])
    strike_index = beats.index(events['strike'])
    windup, = between(events['compare'], events['strike'],
                      targets=[beats[max(0, strike_index-2)]])
    react, = between(events['strike'], shot['end'],
                     targets=[beats[min(len(beats)-1, strike_index+2)]])
    anchors = [(shot['start'], 0), (read, 700), (reach, 1500), (find, 2300), (lock, 2900),
               (events['compare'], 3700), (windup, 4500), (events['strike'], 4800),
               (react, 5300), (shot['end'], 6400)]
    if any(b[0] <= a[0] for a, b in zip(anchors, anchors[1:])):
        raise BuildError(error)
    return anchors


def keyframes(timing: dict, anchors: list) -> list[dict]:
    frames = []
    poses = dict((age, t) for t, age in anchors)
    hover = next(s for s in timing['shots'] if s['id']=='v304-hover')
    search_end = hover.get('voice_start', hover['start'])
    if search_end <= hover['start']:
        search_end = poses[2900]
    hover_times = [(poses[2300]+search_end)/2,
                   poses[3700]+min(.3, (poses[4500]-poses[3700])/2),
                   poses[4800]+min(.3, (poses[5300]-poses[4800])/2)]
    for shot in timing['shots']:
        times = (hover_times if shot['id']=='v304-hover' else
                 [shot['start']+(shot['end']-shot['start'])*f for f in (.08, .5, .92)])
        frames.extend(dict(shot=shot['id'], t=round(t, 6), position=label)
                      for t, label in zip(times, ('opening', 'middle', 'end')))
    return frames


def compile_data(repo: Path, story: dict, *, voices=None, analyze=None) -> dict:
    grid = read_json(repo / story['music']['beats'])
    offset, beats = video_beats(grid)
    if story['site_url'] != 'https://hackathon.dappgo.com/' or story['music']['music_offset_s'] != offset:
        raise BuildError('v007 requires the new CTA and the first measured music beat.')
    scenes = story['scenes']
    if voices:
        timing = presentation_timing(scenes, {s['id']:v['voice_s'] for s,v in zip(scenes, voices)}, beats)
        timing['voice_keys'] = {s['id']:v['key'] for s,v in zip(scenes, voices)}
    else:
        # Snap absolute target boundaries, avoiding cumulative rounding drift.
        ends = [next_beat(beats, float(s['target_end_s'])) for s in scenes]
        timing = dict(source='beat-snapped target preview; narration unmeasured', duration=ends[-1],
                      shots=[dict(id=s['id'], start=0 if i==0 else ends[i-1], end=ends[i])
                             for i,s in enumerate(scenes)])
    if not 170 <= timing['duration'] <= min(180, story['max_total_s']):
        raise BuildError('v007 must fit 170–180 s. Review the script/holds on the host; never accelerate speech.')
    timing.update(version=2, revision='v007', music_offset_s=offset,
                  voice_rule='first detected beat >= scene start + narration_lead_s (default 0)',
                  cut_rule='first detected beat >= max(absolute target end, narration end + 0.3 s)')
    local, analysis = {}, {}
    for i, (scene, shot) in enumerate(zip(scenes, timing['shots'])):
        shot['voice_start'] = narration_start(scene, shot['start'], beats)
        duration = voices[i]['voice_s'] if voices else shot['end']-shot['voice_start']-.6
        silences = analyze(scene, voices[i]) if voices and analyze else []
        local[scene['id']] = map_sentences(scene['narration'], duration, silences)
        analysis[scene['id']] = dict(source='measured locked-clone audio' if voices else 'target preview only',
                                    voice_start=shot['voice_start'])
    cues = cue_document(scenes, timing, local, analysis, beats)
    # The site's original robot clock is warped between these detected beat anchors.
    hover = next(s for s in timing['shots'] if s['id']=='v304-hover')
    events = {e['event']:e['t'] for e in cues['_events'][hover['id']]}
    anchors = hover_anchors(hover, events, beats)
    qr = read_json(repo/'demo/motion/qr.json')
    if qr['url'] != story['site_url']:
        raise BuildError('QR URL differs from the v007 storyboard.')
    evidence = evidence_data(repo)
    evidence['provenance'][STORY] = file_hash(repo/STORY)
    return dict(revision='v007', scenes=scenes, timing=timing, cues=cues,
                beats=dict(beats_s=beats, music_offset_s=offset, source_sha256=file_hash(repo/story['music']['beats'])),
                product=evidence, qr=qr, hover_anchors=anchors, keyframes=keyframes(timing, anchors))


def artifacts(repo: Path, story: dict, data: dict) -> dict[str, str]:
    narration = '\n\n'.join(s['narration'] for s in story['scenes'])+'\n'
    return {f'{OUT}/data.js': '// Generated by demo/motion_v3.py; no network or inference.\nwindow.MOTION_DATA = '+
                              json_text(data).rstrip().replace('</', '<\\/')+';\n',
            f'{OUT}/timing.json': json_text(data['timing']),
            f'{OUT}/keyframes.json': json_text(data['keyframes']),
            f'{OUT}/hover-source.js': hover_source(repo),
            'demo/NARRATION-v007.txt': narration}


def prepare(builder, *, require_voice=False):
    voices = None
    try:
        voices = [builder.require_voice(s) for s in builder.scenes]
    except BuildError:
        if require_voice:
            raise
    def analyze(scene, voice):
        path = Path(voice['artifacts']['audio']['path'])
        return detect_silences(path, voice['voice_s'], builder.demo/'cache/cues'/f'{scene["id"]}-{file_hash(path)}.log')
    data = compile_data(builder.repo, builder.story, voices=voices, analyze=analyze)
    for relative, content in artifacts(builder.repo, builder.story, data).items():
        destination = builder.repo/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)
    for name, value in [('beats',data['beats']), ('cues',data['cues'])]:
        (builder.demo/'motion/v3'/f'{name}.json').write_text(json_text(value))
    return data['timing']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    story = yaml.safe_load((ROOT/STORY).read_text())
    data = compile_data(ROOT, story)
    stale = []
    for relative, content in artifacts(ROOT, story, data).items():
        destination = ROOT/relative
        if args.check:
            if not destination.is_file() or destination.read_text() != content:
                stale.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
    if stale:
        raise BuildError('Stale v007 preview artifacts: '+', '.join(stale))
    print(f'v007 {"checked" if args.check else "prepared"}: {len(data["scenes"])} scenes, '
          f'{data["timing"]["duration"]:.4f} s; target preview only, no voice/browser/media generated.')


if __name__=='__main__':
    main()
