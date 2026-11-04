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
OUT = ROOT / 'demo/assets/terminal-v4-r5'
FOOTERS = {'comparison': 'Saved eval · Oct 27 · no live calls',
           'threads': 'Saved Threads run · Nov 3',
           'media': 'Frozen media run · Oct 30'}
COLS, ROWS, FONT_PX, KEY_FONT_PX = 52, 12, 56, 96
KEY_ROW, FOOTER_ROW = 10, 12
DURATIONS = {'beat4': 16, 'beat7': 24}


@dataclass
class Block:
    title: str
    lines: list[str]
    seconds: float
    group: str

    @property
    def footer(self):
        return FOOTERS['comparison' if self.group == 'comparison' else
                       'media' if self.group in ('image', 'audio') else 'threads']

    def validate(self):
        # One headline, up to six table rows, and the single fixed footer.
        if not 1 <= len(self.lines) <= 6:
            raise ValueError(f'Terminal block overflows: {self.title}')
        if any(len(line) > COLS - 4 for line in [self.title, *self.lines, self.footer]):
            raise ValueError(f'Terminal line overflows: {self.title}')
        if len(self.lines[-1]) > 30:
            raise ValueError(f'96px key line overflows: {self.title}')


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
    ], 4, 'comparison')
    yield Block('SEC tools + Python verdict', [
        '357 claims · corrected gold · includes dev',
        f"{single['correct']}/{single['n']} → {agent['correct']}/{agent['n']} correct",
        f"{100 * single['correct'] / single['n']:.1f}% → {100 * agent['correct'] / agent['n']:.1f}%",
    ], 5, 'comparison')
    yield Block('Held-out text claims', [
        'Baseten · Muse Spark Open · corrected gold',
        'Failures count as wrong',
        f"{agent['test_correct']}/{agent['test_n']} held-out · {100 * agent['test_correct'] / agent['test_n']:.1f}%",
    ], 7, 'comparison')


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
        'CoreWeave annual revenue · 3 of 5 claims',
        f'FY2023 {values[0]}',
    ], 1, 'post')
    yield Block(f'Extracted claims · 3 of {report["proposed_count"]}', [
        f'FY{p} revenue · {v}' for p, v in zip(periods, values)
    ], 1.5, 'claims')
    trace = read(folder + '/' + claims[0]['trace_path'], sources)
    tools = []
    for call in trace['tool_calls'][:2]:
        tools.append(call['name'])
        tools.append(', '.join(f'{k}={v}' for k, v in call['arguments'].items()))
    yield Block('SEC tool calls · CRWV FY2023', [*tools, 'CRWV · FY2023'], 1.5, 'tools')
    verdicts = [f"FY{p} · {c['verdict'].upper()} · {v} → {money(k['actual_value'])}"
                for p, v, c, k in zip(periods, values, claims, checks)]
    yield Block('Program verdicts · 3-claim excerpt', verdicts[1:] + ['FY2023 · CONTRADICTED',
        f'{values[0]} → {money(checks[0]["actual_value"])}'], 2, 'verdicts')

    scale = read('demo/data/scale-v4.json', sources)
    cohort = scale['cohorts'][scale['selected_cohort']]
    median = cohort['median_wall_seconds']
    hours = round(scale['projection']['sequential_hours_at_median'])
    # Fully typed by 6.78 s, before the spoken scale clause at 8.6 s. Keep it
    # through both the latency and projection sentences; the cut stays at 148 s.
    yield Block('Scale · at the saved median', [
        f"{cohort['items']} saved Threads posts · Baseten/post",
        'Sequential projection · not a measured batch',
        f'median {median:.1f} s/post',
        f'1,000 posts ≈ {hours} h · 1 worker',
    ], 12, 'scale')

    rows = [read(path, sources) for path in cohort['sources'][:6]]
    assert sum(r['status'] != 'completed' for r in rows) == 1
    rows.sort(key=lambda r: r['status'] != 'completed')
    labels = {'insufficient_evidence': 'INSUFFICIENT', None: 'UNCHECKED',
              'supported': 'SUPPORTED', 'contradicted': 'CONTRADICTED'}
    table = []
    for row in rows:
        failed = row['status'] != 'completed'
        table.append(f"{row['id']:<4} {'FAILED' if failed else labels[row['verdict']]:<12} {row['wall_seconds']:>4.1f} s")
    yield Block('Batch · completed except FAILED', table, 3, 'batch')

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
            f"{claim['ticker']} {period} revenue · {claim['verdict'].upper()}",
            money(value),
        ], 1.5, call_name)


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
            print(f'\033[{4 + index};3H{line}', end='')
        print(f'\033[{FOOTER_ROW};3H\033[1;37m{block.footer}\033[0m', end='', flush=True)
        # Key line is always written last, character by character, in bold gold.
        key = block.lines[-1]
        print(f'\033[{KEY_ROW};3H\033[1;33m', end='', flush=True)
        for index, char in enumerate(key):
            deadline = start + offset + .18 + .6 * (index + 1) / len(key)
            time.sleep(max(0, deadline - time.monotonic()))
            print(char, end='', flush=True)
        print('\033[0m', end='', flush=True)
        offset += block.seconds
        time.sleep(max(0, start + offset - time.monotonic()))
    # Keep the final hold in the cast; agg uses the timestamp of this event.
    print('\033[?25l', end='', flush=True)


def row_font(block, row):
    # These are literal rows from the PTY, enlarged without retyping their values.
    if row == KEY_ROW or (block.group == 'scale' and row == 6) or (block.group == 'comparison' and row == 5
            and '/' in block.lines[1]):
        return KEY_FONT_PX
    return FONT_PX


class TerminalScreen:
    """Strict interpreter for the clear/position/SGR subset emitted by play()."""
    def __init__(self):
        self.grid = {}
        self.row, self.col, self.style = 1, 1, (0,)
        self.pending = ''

    def feed(self, text):
        text, self.pending = self.pending + text, ''
        while text:
            if text.startswith('\033'):
                match = re.match(r'\033\[([0-9;?]*)([A-Za-z])', text)
                if not match:
                    if re.fullmatch(r'\033(?:\[[0-9;?]*)?', text):
                        self.pending = text
                        return
                    raise ValueError('Unsupported terminal control sequence')
                args, command = match.groups()
                if command == 'J' and args == '2': self.grid.clear()
                elif command == 'H': self.row, self.col = map(int, (args or '1;1').split(';'))
                elif command == 'm': self.style = tuple(map(int, args.split(';')))
                elif (args, command) != ('?25', 'l'): raise ValueError('Unexpected terminal control')
                text = text[match.end():]
            else:
                char, text = text[0], text[1:]
                if not 1 <= self.row <= ROWS or not 1 <= self.col <= COLS:
                    raise ValueError('PTY output outside declared grid')
                self.grid[self.row, self.col] = (char, self.style)
                self.col += 1

    def lines(self):
        return {r: ''.join(self.grid.get((r,c), (' ',()))[0] for c in range(3,COLS+1)).rstrip()
                for r in range(1,ROWS+1)}


def render_cast(cast, destination, blocks, duration):
    """Rasterize the actual saved PTY events; no product call or inferred text."""
    from PIL import Image, ImageDraw, ImageFont
    font_path = Path('/System/Library/Fonts/Menlo.ttc')
    if not font_path.is_file():
        raise SystemExit('Menlo is required for the retained terminal typography')
    fonts = {s: ImageFont.truetype(str(font_path), s) for s in (FONT_PX, KEY_FONT_PX)}
    events = [e for e in map(json.loads, cast.read_text().splitlines()[1:]) if e[1] == 'o']
    screen, cursor = TerminalScreen(), 0
    command = ['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24',
               '-video_size','1920x1080','-framerate','30','-i','pipe:0','-an',
               '-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(destination)]
    log = destination.with_suffix('.render.log')
    with log.open('wb') as errors:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
        try:
            for frame in range(duration * 30):
                t = frame / 30
                while cursor < len(events) and events[cursor][0] <= t:
                    screen.feed(events[cursor][2]); cursor += 1
                title = screen.lines().get(2)
                block = next((b for b in blocks if b.title == title), blocks[0])
                image = Image.new('RGB',(1920,1080),'#0d1117'); draw = ImageDraw.Draw(image)
                for row,line in screen.lines().items():
                    if not line: continue
                    size = row_font(block,row)
                    y = 64 if row == 2 else 800 if row == FOOTER_ROW else 640 if row == KEY_ROW else 220+(row-4)*80
                    if draw.textlength(line, font=fonts[size]) > 1760:
                        raise ValueError(f'{size}px terminal line exceeds safe width: {line}')
                    draw.text((80,y),line,font=fonts[size],fill='#e5b968' if size == KEY_FONT_PX else '#f0f6fc')
                child.stdin.write(image.tobytes())
        finally:
            child.stdin.close()
            code = child.wait()
    if code: raise SystemExit(f'Terminal raster failed; retained {log}')
    return dict(renderer='literal asciicast ANSI rows, Pillow + FFmpeg', command=command,
                label_font_px=FONT_PX,principal_font_px=KEY_FONT_PX,
                font_sha256=hashlib.sha256(font_path.read_bytes()).hexdigest(),
                footer_top_px=800,footer_bottom_limit_px=880,caption_zone_top_px=880,
                mp4_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())


def record(kind, render=False, archive=None):
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
        footers=FOOTERS, footer_row=FOOTER_ROW, key_row=KEY_ROW, key_typed_last=True,
        blocks=[dict(title=b.title, lines=b.lines, duration_s=b.seconds, group=b.group,footer=b.footer,
                     row_fonts={str(row):row_font(b,row) for row in (2,*range(4,4+len(b.lines)-1),KEY_ROW,FOOTER_ROW)}) for b in content],
        speed='editorial playback; never a runtime measurement', sources=sources,
        replay_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limits=['Original evaluation: corrected gold; full 357 includes dev; failures count as wrong.',
                'Footers distinguish the Oct 27 eval, Nov 3 saved Threads run and Oct 30 frozen media run.',
                'Beat 7 shows three of five T03 claims and six of 78 batch rows, including one failure.',
                'Media examples are frozen synthetic fixtures with cached text verification; OCR/ASR is not retested.',
                '1,000-post duration is a sequential projection at the median, not a measured batch.'],
        previous_take=previous.relative_to(ROOT).as_posix() if previous else None,
        cast_sha256=hashlib.sha256(cast.read_bytes()).hexdigest(), status='cast-recorded')
    target = OUT / f'{kind}.json'
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    if code:
        raise SystemExit(f'Real replay process failed ({code}); partial take retained.')
    if render:
        mp4 = OUT / f'{kind}.mp4'
        receipt.update(render_cast(cast,mp4,content,DURATIONS[kind]),status='rendered-real-terminal-recording')
        target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    print(target.relative_to(ROOT))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command', choices=['play', 'record', 'check'])
    cli.add_argument('kind', choices=['beat4', 'beat7'])
    cli.add_argument('--render', action='store_true', help='Render actual PTY rows at 56px labels / 96px principal lines')
    cli.add_argument('--archive', help='Retain the previous take under takes/NAME before recording')
    args = cli.parse_args()
    if args.command == 'play':
        play(args.kind)
    elif args.command == 'record':
        record(args.kind, args.render, args.archive)
    else:
        sources = {}
        result = pages(args.kind, sources)
        print(f'PASS {args.kind}: {len(result)} blocks, ≤8 visible lines, {len(sources)} saved sources')
