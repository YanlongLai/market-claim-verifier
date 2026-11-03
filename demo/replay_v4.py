#!/usr/bin/env python3
"""Real-shell PTY replays of saved evidence. No inference or SEC access."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import shlex
import shutil
import struct
import subprocess
import sys
import termios
import time

ROOT = Path(__file__).resolve().parent.parent
EVAL = 'docs/evidence/eval-v2-2026-10-27'
FAIR = 'docs/evidence/fair-multimodal-v1'
THREADS = 'docs/evidence/real-world-2026-11-02/threads'
OUT = ROOT / 'demo/assets/terminal-v4'
FOOTER = 'Replay of saved run · recorded 2026-10-27 · no live calls'
COLS, ROWS, FONT_PX = 74, 20, 40
DURATIONS = {'beat4': 16, 'beat7': 24}


@dataclass
class Block:
    title: str
    lines: list[str]
    seconds: float
    group: str

    def validate(self):
        # One headline, up to six table rows, and the single fixed footer.
        if not 1 <= len(self.lines) <= 6:
            raise ValueError(f'Terminal block overflows: {self.title}')
        if any(len(line) > COLS - 4 for line in [self.title, *self.lines, FOOTER]):
            raise ValueError(f'Terminal line overflows: {self.title}')


def read(path, sources):
    raw = (ROOT / path).read_bytes()
    sources[path] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def money(value):
    """Site-style dollar/B/M units, retaining quoted precision (e.g. $2.29B)."""
    if value is None:
        return 'unavailable'
    value = Decimal(str(value))
    sign = '-' if value < 0 else ''
    value = abs(value)
    for divisor, suffix in [(Decimal('1e9'), 'B'), (Decimal('1e6'), 'M')]:
        if value >= divisor:
            number = format((value / divisor).quantize(Decimal('.001'), rounding=ROUND_HALF_UP), 'f').rstrip('0').rstrip('.')
            return f'{sign}${number}{suffix}'
    return f'{sign}${value.quantize(Decimal(1), rounding=ROUND_HALF_UP):,}'


def comparison(sources):
    path = 'eval/v2/claims-v2-corrected.jsonl'
    raw = (ROOT / path).read_bytes()
    sources[path] = hashlib.sha256(raw).hexdigest()
    gold = {r['id']: r for r in map(json.loads, raw.splitlines())}
    stats = {}
    for method in ('single_shot', 'agent'):
        rows = [read(p.relative_to(ROOT).as_posix(), sources)
                for p in sorted((ROOT / EVAL).glob(f'*--{method}@baseten.json'))]
        assert len(rows) == 357
        good = lambda r: r['status'] == 'completed' and r['verdict'] == gold[r['id']]['gold_verdict']
        test = [r for r in rows if r['split'] == 'test']
        stats[method] = dict(correct=sum(map(good, rows)), n=len(rows),
                            test_correct=sum(map(good, test)), test_n=len(test))
    single, agent = stats['single_shot'], stats['agent']
    yield Block('Same model · no tools', [
        'Baseten · Muse Spark Open',
        '357 claims · corrected gold · includes dev',
        f"{single['correct']}/{single['n']} correct · {100 * single['correct'] / single['n']:.1f}%",
    ], 8, 'comparison')
    yield Block('SEC tools + Python verdict', [
        f"{single['correct']}/{single['n']} no tools → {agent['correct']}/{agent['n']} with tools",
        f"357 incl. dev · corrected gold · {100 * single['correct'] / single['n']:.1f}% → {100 * agent['correct'] / agent['n']:.1f}%",
        f"{agent['test_correct']}/{agent['test_n']} held-out · {100 * agent['test_correct'] / agent['test_n']:.1f}%",
    ], 8, 'comparison')


def scale_pages(sources):
    folder = f'{THREADS}/baseten/post/T03'
    report = read(folder + '/report.json', sources)
    read(folder + '/result.json', sources)
    # Show three of the five claims, explicitly labelled as an excerpt.
    claims = report['claims'][1:4]
    checks = [c['program_checks'][0] for c in claims]
    periods = ['2023', '2024', '2025']
    values = [money(c['stated_value_used']) for c in checks]
    yield Block('One post · T03 excerpt', [
        'CoreWeave annual revenue',
        ' · '.join(f'{p} {v}' for p, v in zip(periods, values)),
    ], 1.5, 'post')
    yield Block(f'Extracted claims · 3 of {report["proposed_count"]}', [
        f'CRWV · FY{p} revenue · {v}' for p, v in zip(periods, values)
    ], 2.5, 'claims')
    trace = read(folder + '/' + claims[0]['trace_path'], sources)
    tools = []
    for call in trace['tool_calls'][:2]:
        args = ', '.join(f'{k}={v}' for k, v in call['arguments'].items())
        tools.append(f'{call["name"]}({args})')
    yield Block('SEC tool calls · CRWV FY2023', tools, 2.5, 'tools')
    verdicts = [f"FY{p} · {c['verdict'].upper()} · {v} → {money(k['actual_value'])}"
                for p, v, c, k in zip(periods, values, claims, checks)]
    yield Block('Program verdicts · 3-claim excerpt', verdicts[1:] + verdicts[:1], 3.5, 'verdicts')

    scale = read('demo/data/scale-v4.json', sources)
    cohort = scale['cohorts'][scale['selected_cohort']]
    rows = [read(path, sources) for path in cohort['sources'][:6]]
    assert sum(r['status'] != 'completed' for r in rows) == 1
    rows.sort(key=lambda r: r['status'] != 'completed')
    labels = {'insufficient_evidence': 'INSUFFICIENT', None: 'UNCHECKED',
              'supported': 'SUPPORTED', 'contradicted': 'CONTRADICTED'}
    table = []
    for row in rows:
        failed = row['status'] != 'completed'
        table.append(f"{row['id']:<5} {'FAILED' if failed else 'completed':<10} "
                     f"{'post CLI error' if failed else labels[row['verdict']]:<15} {row['wall_seconds']:>5.1f} s")
    yield Block('Batch · ID / status / verdict / seconds', table, 5, 'batch')

    for name, title, call_name, period in [
        ('META-webp', 'OCR · frozen synthetic screenshot', 'image', 'FY2026 Q3'),
        ('MSFT-wav', 'ASR · frozen synthetic audio', 'audio', 'FY2027 Q1'),
    ]:
        ingest = read(f'{FAIR}/test/baseten/low/{name}/ingest.json', sources)
        call = read(f'{FAIR}/prepared/{name}/calls/{call_name}.json', sources)
        read(f'{FAIR}/prepared/{name}/prepared.json', sources)
        channel = ingest['channels'][0]
        read(FAIR + '/' + channel['text_record'], sources)
        claim = channel['claims'][0]
        if claim.get('trace_path'):
            trace_folder = Path(FAIR) / Path(channel['text_record']).parent
            read((trace_folder / claim['trace_path']).as_posix(), sources)
        value = claim['program_checks'][0]['stated_value_used']
        yield Block(title, [
            call['model'],
            f"{claim['ticker']} {period} revenue · {money(value)} → {claim['verdict'].upper()}",
        ], 3, call_name)

    median = cohort['median_wall_seconds']
    hours = round(scale['projection']['sequential_hours_at_median'])
    yield Block('Scale · at the saved median', [
        f"{cohort['items']} saved Threads posts · Baseten/post",
        f'median {median:.1f} s/post · 1,000 posts ≈ {hours} h, one worker',
    ], 3, 'scale')


def pages(kind, sources):
    content = list(comparison(sources) if kind == 'beat4' else scale_pages(sources))
    for block in content:
        block.validate()
    assert sum(b.seconds for b in content) == DURATIONS[kind]
    return content


def play(kind):
    # Explicit saved-trace playback; the product CLI is never imported.
    content = pages(kind, {})
    start = time.monotonic()
    offset = 0
    for block in content:
        print('\033[2J\033[H\033[?25l', end='')
        print(f'\033[2;3H\033[1;37m{block.title}\033[0m', end='')
        for index, line in enumerate(block.lines[:-1]):
            print(f'\033[{5 + index * 2};3H{line}', end='')
        print(f'\033[{ROWS};3H\033[2;90m{FOOTER}\033[0m', end='', flush=True)
        # Key line is always written last, character by character, in bold gold.
        key = block.lines[-1]
        print(f'\033[{5 + (len(block.lines) - 1) * 2};3H\033[1;33m', end='', flush=True)
        for index, char in enumerate(key):
            deadline = start + offset + .18 + .6 * (index + 1) / len(key)
            time.sleep(max(0, deadline - time.monotonic()))
            print(char, end='', flush=True)
        print('\033[0m', end='', flush=True)
        offset += block.seconds
        time.sleep(max(0, start + offset - time.monotonic()))
    # Keep the final hold in the cast; agg uses the timestamp of this event.
    print('\033[?25l', end='', flush=True)


def record(kind, agg, archive=None):
    OUT.mkdir(parents=True, exist_ok=True)
    cast = OUT / f'{kind}.cast'
    previous = None
    if cast.exists():
        if not archive or not re.fullmatch(r'[A-Za-z0-9_-]+', archive):
            raise SystemExit('Existing take retained. Pass --archive NAME to move it before recording.')
        previous = OUT / 'takes' / archive
        previous.mkdir(parents=True, exist_ok=True)
        files = [OUT / f'{kind}.{ext}' for ext in ('cast', 'gif', 'json', 'mp4')]
        if any((previous / p.name).exists() for p in files):
            raise SystemExit('Archive already contains this take; choose a new name.')
        for path in files:
            if path.exists():
                shutil.move(str(path), previous / path.name)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', ROWS, COLS, 1920, 1080))
    argv = [sys.executable, str(Path(__file__).resolve()), 'play', kind]
    shell = ['/bin/zsh', '-f', '-c', 'exec ' + shlex.join(argv)]
    env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('TOKEN', 'SECRET', 'API_KEY', 'PASSWORD'))}
    env.update(TERM='xterm-256color', COLUMNS=str(COLS), LINES=str(ROWS), PYTHONUNBUFFERED='1')
    start = time.monotonic()
    first_output = None
    with cast.open('w') as output:
        output.write(json.dumps(dict(version=2, width=COLS, height=ROWS,
            title='v4 ' + kind + ' | SAVED EVIDENCE REPLAY',
            env={'TERM': 'xterm-256color', 'SHELL': '/bin/zsh'})) + '\n')
        child = subprocess.Popen(shell, cwd=ROOT, env=env, stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)
        while True:
            ready, _, _ = select.select([master], [], [], .2)
            if ready:
                try:
                    raw = os.read(master, 65536)
                except OSError:
                    break
                if not raw:
                    break
                now = time.monotonic()
                if first_output is None:
                    first_output = now
                output.write(json.dumps([now - first_output, 'o', raw.decode('utf-8')]) + '\n')
            elif child.poll() is not None:
                break
    os.close(master)
    code = child.wait()
    sources = {}
    content = pages(kind, sources)
    receipt = dict(kind=kind, command=shell, recording='real zsh subprocess attached to a PTY, asciicast v2',
        exit_code=code, cols=COLS, rows=ROWS, font_px=FONT_PX, font='Menlo', theme='github-dark',
        resolution=[1920, 1080], duration_s=DURATIONS[kind], max_visible_lines=8,
        startup_seconds_excluded=first_output-start if first_output is not None else None,
        footer=FOOTER, footer_row=ROWS, key_typed_last=True,
        blocks=[dict(title=b.title, lines=b.lines, duration_s=b.seconds, group=b.group) for b in content],
        speed='editorial playback; never a runtime measurement', sources=sources,
        replay_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limits=['Original evaluation: corrected gold; full 357 includes dev; failures count as wrong.',
                'Footer date identifies the original evaluation. Threads/media dates are in the source records.',
                'Beat 7 shows three of five T03 claims and six of 78 batch rows, including one failure.',
                'Media examples are frozen synthetic fixtures with cached text verification; OCR/ASR is not retested.',
                '1,000-post duration is a sequential projection at the median, not a measured batch.'],
        previous_take=previous.relative_to(ROOT).as_posix() if previous else None,
        cast_sha256=hashlib.sha256(cast.read_bytes()).hexdigest(), status='cast-recorded')
    target = OUT / f'{kind}.json'
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    if code:
        raise SystemExit(f'Real replay process failed ({code}); partial take retained.')
    if agg:
        gif = OUT / f'{kind}.gif'
        command = [agg, '--font-family', 'Menlo', '--font-size', str(FONT_PX), '--line-height', '1.2',
                   '--theme', 'github-dark', '--idle-time-limit', '100', '--last-frame-duration', '0', str(cast), str(gif)]
        subprocess.run(command, check=True)
        dims = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(gif)]))['streams'][0]
        if dims['width'] > 1920 or dims['height'] > 1080:
            raise SystemExit('Terminal exceeds 1920×1080; preserve this take and adjust the grid.')
        mp4 = OUT / f'{kind}.mp4'
        encode = ['ffmpeg', '-v', 'error', '-y', '-i', str(gif), '-vf',
                  f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0d1117,tpad=stop_mode=clone:stop_duration={DURATIONS[kind]},fps=30',
                  '-t', str(receipt['duration_s']), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', str(mp4)]
        subprocess.run(encode, check=True)
        receipt.update(status='rendered-real-terminal-recording', render_command=command, encode_command=encode,
            mp4_sha256=hashlib.sha256(mp4.read_bytes()).hexdigest(), gif_sha256=hashlib.sha256(gif.read_bytes()).hexdigest(),
            terminal_raster=[dims['width'], dims['height']])
        target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    print(target.relative_to(ROOT))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command', choices=['play', 'record', 'check'])
    cli.add_argument('kind', choices=['beat4', 'beat7'])
    cli.add_argument('--agg', help='Existing agg executable; never installs a package')
    cli.add_argument('--archive', help='Retain the previous take under takes/NAME before recording')
    args = cli.parse_args()
    if args.command == 'play':
        play(args.kind)
    elif args.command == 'record':
        record(args.kind, args.agg, args.archive)
    else:
        sources = {}
        result = pages(args.kind, sources)
        print(f'PASS {args.kind}: {len(result)} blocks, ≤8 visible lines, {len(sources)} saved sources')
