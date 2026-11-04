"""Repository prose is English by default, with separate Traditional Chinese files.

No Git executable or third-party parser is needed, including in the offline copy.
Code, URLs, paths, tickers and explicit product/model identifiers are not prose.
"""
from __future__ import annotations

from html.parser import HTMLParser
from html import unescape
import hashlib
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {'.md', '.html', '.txt', '.srt'}
SKIP = {'.git', '.venv', '.venv-workers', '.cache', '.pytest_cache', '__pycache__',
        'node_modules', 'python_modules', '.wrangler'}
# Unified, compatibility and supplementary Han, kana, Hangul and Bopomofo.
CJK = re.compile('[\u2e80-\u2fff\u3040-\u30ff\u3100-\u312f\u31a0-\u31bf'
                 '\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af'
                 '\uf900-\ufaff\U00020000-\U000323af]')
# Proper names and technical identifiers may be used in Chinese prose. This is
# a finite vocabulary, not an exception for quotations or arbitrary short text.
IDENTIFIERS = set('''AI API ASR AAPL AMZN AWS Baseten Bootstrap Bopomofo Breeze
CI CIK CLI CMoney CSS Claude Coca Cola CrowdStrike DappGo EDGAR EBITDA EPS ETF
Apple Amazon Alphabet Intel Adobe IP ID HTTP CFO WER SM Entertainment Cloud
A B C D E Open eSpeak n p ms s
FFmpeg FY GAAP GIF Google H264 HTML IBM IFRS JPEG JSON JSONL KO KRW L1 L2 L3 L4
LINE Latin MIT MP3 MP4 MSFT Markdown McNemar Meta Microsoft Model Muse NVDA
Noto Nvidia OCR PDF PNG Pages Palantir Playwright Python Q1 Q2 Q3 Q4 Reels
SEC SHA Spark TC TSLA Tesla Threads Token TXT Twitter US USD US GAAP Voice
Transcribe WAV WebP Wilson X XBRL XLSX YAML YoY YouTube Fireworks Node
Contributor Standard VTT FFprobe ffprobe uv UTF UTC WebM MOV MKV FLAC M4A
AIFF AAC OGG SVG FFNN FTNN ETFs OpenAI Codex English GitHub'''.split())
PHRASES = ('Meta Model API', 'Muse Spark', 'Muse Voice Transcribe', 'IBM Plex',
           'Noto Sans TC', 'Market Claim Verifier', 'Coca-Cola')


def prose_files():
    """Walk the repository without following ignored environment symlinks."""
    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.is_symlink() or path.name in SKIP:
                continue
            if path.relative_to(ROOT).as_posix() in {'demo/cache', 'demo/out'}:
                continue
            if path.is_dir():
                yield from visit(path)
            elif path.suffix.lower() in SUFFIXES:
                yield path
    yield from visit(ROOT)


def is_chinese(path):
    relative = path.relative_to(ROOT)
    return '.zh-TW.' in path.name or '.zh.' in path.name or 'zh' in relative.parts


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'code', 'pre'}:
            self.hidden += 1
        if not self.hidden:
            meta = dict(attrs)
            human_meta = (meta.get('name') in {'description', 'twitter:title', 'twitter:description', 'twitter:image:alt'}
                          or meta.get('property') in {'og:title', 'og:description', 'og:image:alt', 'og:site_name'})
            self.parts.extend(value for key, value in attrs
                              if (key in {'alt', 'title', 'aria-label', 'placeholder'}
                                  or key == 'content' and human_meta)
                              and value and not value.startswith(('http', '#')))

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'code', 'pre'}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def chinese_prose(text, html=False):
    if html:
        parser = VisibleHTML()
        parser.feed(text)
        text = '\n'.join(parser.parts)
    else:
        text = re.sub(r'^(```|~~~).*?^\1[^\n]*$', '', text, flags=re.M | re.S)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
        # Inline code is permitted, but multiword natural-language quotations
        # belong in the English source rather than being hidden as code.
        text = re.sub(r'`[^`\n]+`', '', text)
        text = re.sub(r'!?\[([^]\n]*)\]\([^\s)]*(?:\s+"[^"]*")?\)', r'\1', text)
        text = re.sub(r'\]\([^)]*\)', ']', text)
        text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'https?://[^\s<>）)]+', '', text)
    text = re.sub(r'\b[\w.-]+(?:/|\\)[\w./#?%=&-]*', '', text)
    text = re.sub(r'\b[\w.-]+\.(?:md|html|jsonl?|txt|srt|py|js|mjs|png|webp|svg|gif|log)\b', '', text)
    text = re.sub(r'\b[0-9a-f]{7,64}\b', '', text)
    # Model names, IDs, tickers and units containing digits/underscores.
    text = re.sub(r'\b[A-Za-z0-9]+(?:[_@.-][A-Za-z0-9]+)+\b', '', text)
    text = re.sub(r'\b(?:[A-Za-z]+\d+[A-Za-z\d]*|\d+[A-Za-z]+)\b', '', text)
    for phrase in PHRASES:
        text = text.replace(phrase, '')
    return text


def unexpected_latin(text, html=False):
    return sorted({word for word in re.findall(r'[A-Za-z]+', chinese_prose(text, html))
                   if word not in IDENTIFIERS})


def test_repository_language_purity():
    failures = []
    for path in prose_files():
        text = path.read_text(encoding='utf-8')
        name = str(path.relative_to(ROOT))
        if is_chinese(path):
            words = unexpected_latin(text, path.suffix == '.html')
            if words:
                failures.append(f'{name}: Latin prose: {", ".join(words[:25])}')
        else:
            rendered = unescape(text) if path.suffix == '.html' else text
            hits = [str(i) for i, line in enumerate(rendered.splitlines(), 1) if CJK.search(line)]
            if hits:
                failures.append(f'{name}: CJK at lines {", ".join(hits[:20])}')
    assert not failures, '\n' + '\n'.join(failures)


@pytest.mark.parametrize('sample', ['Hello world', 'This is an English sentence.',
                                   '這一段 contains English prose。',
                                   '[English prose](https://example.com)',
                                   '<p title="Hello world">中文</p>'])
def test_detects_english_prose_in_chinese(sample):
    assert unexpected_latin(sample, sample.startswith('<'))


def test_identifiers_urls_and_code_are_allowed():
    assert not unexpected_latin('使用 Meta Model API 查核 NVDA；Python 與 SEC。'
                                '\n`lookup_fact` [來源](https://example.com/a)'
                                '\n```sh\nuv run python -m claimcheck\n```')
    assert CJK.search('繁體中文')
    assert CJK.search('\U00020000')
    assert CJK.search('ひらがな')
    assert CJK.search('한글')


def test_language_migration_retains_original_sources_and_input_bytes():
    directory = ROOT / 'docs/evidence/readme-v3-2026-11-04'
    archive = json.loads((directory / 'original-language-sources.json').read_text())
    originals = {row['path']: row for row in archive['files']}
    for row in originals.values():
        assert hashlib.sha256(row['text'].encode('utf-8')).hexdigest() == row['sha256']
    mappings = json.loads((directory / 'input-translations.json').read_text())['translations']
    for row in mappings:
        assert hashlib.sha256((ROOT / row['original_path']).read_bytes()).hexdigest() == originals[row['path']]['sha256']
    path = 'examples/posts/tw-social-post.txt'
    assert hashlib.sha256((ROOT / 'examples/posts/tw-social-post.zh-TW.txt').read_bytes()).hexdigest() == originals[path]['sha256']


def test_documentation_update_keeps_recorded_financial_evidence_unchanged():
    directory = ROOT / 'docs/evidence/readme-v3-2026-11-04'
    hashes = json.loads((directory / 'protected-records.json').read_text())
    hashes.update(json.loads((directory / 'locked-demo-outputs.json').read_text()))
    for relative, expected in hashes.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
