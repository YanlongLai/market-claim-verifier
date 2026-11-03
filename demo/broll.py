"""Host-only extraction of approved B-roll; no inference, TTS, browser or film render.

Run `python demo/broll.py extract` before host keyframes. `check` needs no FFmpeg.
The committed JS describes frame addresses; decoded PNGs stay in demo/cache/.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image

from motion_timing import narration_start, next_beat, video_beats
from pipeline import BuildError, file_hash, read_json

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'demo/prompts/broll/manifest.json'
DATA = 'demo/motion/v3/broll-data.js'
# Desired reductions of silent holds; real cut positions still use detected beats.
HOLD_TRIMS = dict(zip(
    ['v301-disclosure', 'v302-apple', 'v303-extract', 'v304-hover', 'v305-proof', 'v306-program',
     'v307-l4', 'v308-screenshot', 'v309-audio', 'v310-results', 'v311-limits', 'v312-cta'],
    [0, 3, 2, 2, 2, 2, 1, .5, .5, 1, 0, 0]))


def proposed_timeline(timing: dict, scenes: list[dict], beats: list[float]) -> dict:
    """Read measured voice lengths; propose shorter holds plus an unfilled slot.

    This deliberately returns a proposal, never edits a storyboard or host timing.
    No voice is synthesized or accelerated, and the placeholder contains no claims.
    """
    if [s['id'] for s in timing['shots']] != list(HOLD_TRIMS):
        raise BuildError('Expected the twelve v3 scenes in order.')
    shots, start = [], 0.0
    for old, scene in zip(timing['shots'], scenes, strict=True):
        if old['id'] != scene['id']:
            raise BuildError('Measured timings and storyboard scenes disagree.')
        if scene['id'] == 'v312-cta':
            end = next_beat(beats, start + 11)
            shots.append(dict(id='v311b-real-world', start=start, end=end, duration_s=round(end-start, 4),
                              status='PLACEHOLDER — DappGo News + Threads results; evidence and picture pending',
                              narration=None))
            start = end
        voice_s = old.get('voice_s')
        if type(voice_s) not in (int, float) or not math.isfinite(voice_s) or voice_s <= 0:
            raise BuildError('Retiming needs host-measured cached narration, not preview durations.')
        voice_start = narration_start(scene, start, beats)
        voice_end = round(voice_start + voice_s, 9)
        target = start + old['end'] - old['start'] - HOLD_TRIMS[scene['id']]
        end = next_beat(beats, max(target, voice_end + .3))
        shots.append(dict(id=scene['id'], start=start, end=end, voice_start=voice_start,
                          voice_s=voice_s, voice_end=voice_end, hold_s=round(end-voice_end, 4),
                          old_duration_s=round(old['end']-old['start'], 4),
                          duration_s=round(end-start, 4)))
        start = end
    reserve = next(s for s in shots if s['id'] == 'v311b-real-world')
    if start > min(180, timing['duration']) or not 10 <= reserve['duration_s'] <= 12:
        raise BuildError('Proposed holds/placeholder exceed the film budget; review on the host.')
    return dict(revision='v010', status='PROPOSAL — Owner gate 1 pending', duration=start,
                baseline_duration=timing['duration'], narration_changes=[], shots=shots)


def records(repo: Path) -> dict:
    data = read_json(repo / RECORD)
    retained = math.floor(data['source_frames'] - data['trim_tail_s'] * data['fps'])
    if retained != data['retained_frames'] or retained <= 0:
        raise BuildError('B-roll trim must discard complete tail frames.')
    for clip in data['clips']:
        receipt = read_json(repo / clip['receipt'])
        prompts = read_json(repo / 'demo/prompts/broll' / clip['prompt_file'])
        expected = prompts['common'] + ' ' + prompts['shots'][clip['prompt_key']]['prompt']
        if (file_hash(repo / clip['receipt']) != clip['receipt_sha256'] or
                file_hash(repo / clip['source']) != clip['source_sha256'] or
                receipt['status'] != 'success' or receipt['params'] != clip['params'] or
                receipt['model'] != clip['model'] or
                receipt['output']['sha256'] != clip['source_sha256'] or
                clip['params']['prompt'] != expected or
                clip['params']['negative'] != prompts['negative']):
            raise BuildError(f"{clip['id']}: source, receipt or saved prompt changed.")
        params, output = clip['params'], receipt['output']
        if (params['frames'] != data['source_frames'] or output['frame_count'] != data['source_frames'] or
                params['fps'] != data['fps'] or output['fps'] != data['fps'] or
                params['size'] != data['size'] or output['size'] != data['size']):
            raise BuildError(f"{clip['id']}: source dimensions/rate changed.")
        for item in clip['inputs'].values():
            path = repo / 'docs/site/img/auditor/H' / Path(item['path']).name
            if file_hash(path) != item['sha256']:
                raise BuildError(f"{clip['id']}: reference image changed.")
    return data


def runtime_data(data: dict) -> str:
    sources = {c['id']: c for c in data['clips']}
    clips = []
    for clip in data['clips']:
        asset_id = data.get('placement_replacements', {}).get(clip['id'], clip['id'])
        if asset_id not in sources:
            raise BuildError(f"{clip['id']}: replacement must reuse an approved source.")
        source = sources[asset_id]
        clips.append(dict(id=clip['id'], asset_id=asset_id,
                          source_sha256=source['source_sha256'],
                          receipt_sha256=source['receipt_sha256'], **clip['placement']))
    value = dict(fps=data['fps'], frame_count=data['retained_frames'], size=data['size'],
                 trim_tail_s=data['trim_tail_s'], background=data['background'], panel=data['panel'],
                 base='../../cache/broll-480/',
                 clips=clips)
    return ('// Generated from demo/prompts/broll/manifest.json by demo/broll.py; no media decoded.\n'
            'window.BROLL_DATA = ' + json.dumps(value, ensure_ascii=False, indent=2) + ';\n')


def frame_files(folder: Path, count: int) -> list[Path]:
    return [folder / f'frame-{i:04d}.png' for i in range(count)]


def validate_frames(folder: Path, data: dict) -> list[dict]:
    paths = frame_files(folder, data['retained_frames'])
    if set(folder.glob('frame-*.png')) != set(paths):
        raise BuildError(f'{folder}: expected exactly {len(paths)} PNGs. Run demo/broll.py extract.')
    hashes = []
    for path in paths:
        with Image.open(path) as image:
            if image.format != 'PNG' or list(image.size) != data['size']:
                raise BuildError(f'{path}: expected native 480 square PNG.')
            image.load()
        hashes.append(dict(file=path.name, sha256=file_hash(path)))
    return hashes


def extraction_command(ffmpeg: str, source: Path, target: Path, count: int) -> list[str]:
    # trim by source index: no resampling, scaling, duplicated frames or partial tail frame.
    return [ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-i', str(source),
            '-map', '0:v:0', '-an', '-vf', f'trim=start_frame=0:end_frame={count},setpts=PTS-STARTPTS',
            '-fps_mode', 'passthrough', '-start_number', '0', str(target / 'frame-%04d.png')]


def extract(repo: Path, data: dict, ffmpeg: str) -> None:
    cache = repo / 'demo/cache/broll-480'
    cache.mkdir(parents=True, exist_ok=True)
    for clip in data['clips']:
        destination = cache / clip['id']
        receipt_path = destination / 'extraction.json'
        if receipt_path.is_file():
            try:
                previous = read_json(receipt_path)
                reusable = (previous.get('source_sha256') == clip['source_sha256'] and
                            previous.get('manifest_sha256') == file_hash(repo / RECORD) and
                            previous.get('frames') == validate_frames(destination, data))
            except (BuildError, OSError, ValueError):
                reusable = False  # Interrupted or damaged derived cache: decode afresh.
            if reusable:
                print(f"cached {clip['id']}: {data['retained_frames']} frames")
                continue
        with tempfile.TemporaryDirectory(prefix=clip['id']+'-', dir=cache) as temp:
            folder = Path(temp)
            command = extraction_command(ffmpeg, repo / clip['source'], folder, data['retained_frames'])
            subprocess.run(command, check=True)
            hashes = validate_frames(folder, data)
            receipt = dict(source_sha256=clip['source_sha256'], manifest_sha256=file_hash(repo / RECORD),
                           fps=data['fps'], duration_s=data['retained_frames']/data['fps'],
                           discarded_tail_s=(data['source_frames']-data['retained_frames'])/data['fps'],
                           command=command, ffmpeg=subprocess.check_output([ffmpeg, '-version'], text=True).splitlines()[0],
                           frames=hashes)
            (folder/'extraction.json').write_text(json.dumps(receipt, indent=2)+'\n')
            if destination.exists():
                shutil.rmtree(destination)
            folder.rename(destination)
        print(f"extracted {clip['id']}: {data['retained_frames']} native PNGs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'data', 'extract', 'plan'])
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--timing', type=Path, help='plan: host-measured v3 timing.json (read only)')
    parser.add_argument('--out', type=Path, help='plan: proposed timeline JSON (use demo/out/)')
    args = parser.parse_args()
    if args.command == 'plan':
        if not args.timing or not args.out:
            parser.error('plan requires --timing and --out')
        import yaml
        story = yaml.safe_load((ROOT/'demo/storyboard-v3.yaml').read_text())
        _, beats = video_beats(read_json(ROOT/story['music']['beats']))
        proposal = proposed_timeline(read_json(args.timing), story['scenes'], beats)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(proposal, indent=2, ensure_ascii=False)+'\n')
        print(f"Proposed {proposal['duration']:.4f} s, including real-world placeholder; Owner gate 1 pending.")
        return
    data = records(ROOT)
    js = runtime_data(data)
    if args.command == 'data':
        (ROOT/DATA).write_text(js)
    elif not (ROOT/DATA).is_file() or (ROOT/DATA).read_text() != js:
        raise BuildError('Stale B-roll addresses. Run python demo/broll.py data.')
    if args.command == 'extract':
        extract(ROOT, data, args.ffmpeg)
    print(f'B-roll {args.command}: five approved sources; 45/49 frames, 2.8125 s each.')


if __name__ == '__main__':
    try:
        main()
    except (BuildError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
