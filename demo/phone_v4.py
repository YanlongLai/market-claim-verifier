#!/usr/bin/env python3
"""Rebuild the portrait saved-post SVG directly from the retained report."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parent.parent
SOURCE = 'docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json'
ASSET = 'demo/assets/saved-post-v4.svg'


def svg(root=ROOT):
    raw = (root / SOURCE).read_bytes()
    post = json.loads(raw)['post']
    provenance = dict(source=SOURCE, source_sha256=hashlib.sha256(raw).hexdigest(),
                      post_sha256=hashlib.sha256(post.encode()).hexdigest(),
                      label='saved post · 28 Oct 2026', repost_counter='motion-system element; excluded from still')
    lines = []
    y = 370
    for paragraph in post.strip().split('\n\n'):
        for line in textwrap.wrap(paragraph, width=30, break_long_words=False, break_on_hyphens=False):
            lines.append(f'    <text x="134" y="{y}" font-size="56">{escape(line)}</text>')
            y += 72
        y += 32
    if y > 1800:
        raise ValueError('Saved post exceeds phone safe area')
    return '\n'.join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920" role="img" aria-labelledby="title desc">',
        '  <title id="title">Saved finance post inside a phone outline</title>',
        '  <desc id="desc">Full saved post, verbatim. saved post · 28 Oct 2026. Repost animation is separate.</desc>',
        f'  <metadata>{escape(json.dumps(provenance, ensure_ascii=False, sort_keys=True))}</metadata>',
        '  <rect width="1080" height="1920" fill="#111a20"/>',
        '  <rect id="phone-outline" x="56" y="40" width="968" height="1840" rx="112" fill="#f7f5ef" stroke="#718e94" stroke-width="12"/>',
        '  <rect x="382" y="86" width="316" height="38" rx="19" fill="#15252b"/>',
        '  <g font-family="Arial, sans-serif" fill="#15252b">',
        '    <text x="134" y="236" font-size="56" fill="#465e68">saved post · 28 Oct 2026</text>',
        '    <path d="M134 282H946" stroke="#c6cfcb" stroke-width="2"/>',
        *lines,
        '  </g>',
        '  <rect x="378" y="1816" width="324" height="8" rx="4" fill="#718e94"/>',
        '</svg>', '',
    ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--png', action='store_true', help='Also rasterize with macOS AppKit and installed Swift')
    args = parser.parse_args()
    output = svg()
    if args.check:
        if (ROOT / ASSET).read_text() != output:
            raise SystemExit(f'{ASSET} is stale; run demo/phone_v4.py')
    else:
        (ROOT / ASSET).write_text(output)
        if args.png:
            subprocess.run(['swift', '-module-cache-path', str(Path(tempfile.gettempdir())/'v4-phone-swift-cache'),
                            str(ROOT/'demo/phone_v4.swift'), str(ROOT/ASSET),
                            str((ROOT/ASSET).with_suffix('.png'))], check=True)
    print('PASS saved-post v4: 1080×1920, verbatim post, ≥56 px, no baked-in repost count')
