#!/usr/bin/env python3
"""Extract every whole-second frame from the two local v4 terminal MP4s."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'demo/out/v4-terminal-review'


def extract():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    clips = []
    for kind, duration, start in [('beat4', 16, 40), ('beat7', 24, 122)]:
        path = ROOT / f'demo/assets/terminal-v4/{kind}.mp4'
        stream = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_streams', '-of', 'json', str(path),
        ]))['streams'][0]
        assert [stream['width'], stream['height']] == [1920, 1080]
        assert stream['r_frame_rate'] == '30/1'
        assert float(stream['duration']) == duration, (kind, stream['duration'])
        assert int(stream['nb_frames']) == duration * 30
        # Select source frames 0,30,60…; timestamps are exact, not half-second fps samples.
        command = ['ffmpeg', '-v', 'error', '-y', '-i', str(path), '-vf', 'select=not(mod(n\\,30))',
                   '-fps_mode', 'vfr', '-start_number', '0', str(OUT / f'{kind}-%02ds.png')]
        subprocess.run(command, check=True)
        clips.append(dict(clip=kind, source=path.relative_to(ROOT).as_posix(),
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          duration_s=duration, frames=int(stream['nb_frames']), extract_command=command))
        for second in range(duration):
            png = OUT / f'{kind}-{second:02d}s.png'
            frames.append(dict(file=png.name, clip=kind, clip_second=second, timeline_second=start+second,
                               sha256=hashlib.sha256(png.read_bytes()).hexdigest()))
    manifest = dict(resolution=[1920, 1080], sample_fps=1, clips=clips, frames=frames)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUT / 'README.md').write_text(
        '# v4 round 2 terminal review\n\n'
        '40 PNGs at exact whole-second source timestamps (1 fps), 1920×1080. '
        'Clip 4 is 16.000 s / 480 frames; clip 7 is 24.000 s / 720 frames. '
        'The final highlighted figures are held through each clip’s final frame.\n\n'
        'Regenerate from the repository root with `python3 demo/terminal_review_v4.py`. '
        '[Hashes and timestamps](manifest.json).\n\n' +
        '\n'.join(f'- [{f["file"]}]({f["file"]}) · film {f["timeline_second"]} s' for f in frames) + '\n')
    print('\n'.join(str(OUT.relative_to(ROOT) / f['file']) for f in frames))
    print('PASS terminal review: 40 PNGs at 1 fps; 16.000 s / 24.000 s, 30 fps, 1920×1080')


if __name__ == '__main__':
    extract()
