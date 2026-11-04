"""Keep the public summary concise and distinct from historical evidence."""

import html
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUIDE_URL = "https://github.com/YanlongLai/market-claim-verifier/blob/main/docs/evidence/REVIEW_GUIDE.md"
SURFACES = (
    "README.md", "README.zh-TW.md", "JUDGES.md", "llms.txt",
    "docs/llms.txt", "docs/site/index.html", "docs/zh/index.html",
    "docs/site/script.js",
)
CANONICAL = (
    "$0.01 per live check", "$0.02 per claim", "6–20 s live", "10 s median",
    "90.2% (240/266)", "1/139", "≈8,000 companies", "23 tested",
    "≤600 characters",
)


@pytest.mark.parametrize("relative", SURFACES)
def test_public_summaries_reject_old_number_variants(relative):
    # Scan the full HTML, including JSON-LD, meta, OG and Twitter descriptions.
    # Historical evidence pages retain the measurements and full-set scores.
    source = (ROOT / relative).read_text()
    forbidden = re.findall(r"\$0\.020\b|0\.0099\d*|90\.5%", source)
    assert not forbidden, (relative, forbidden)
    assert not re.search(r"(?<![\d.])6 s live|即時(?:查核需時)? 6 秒|240/266\s*[（(]90\.2%", source)


@pytest.mark.parametrize("relative", (
    "README.md", "JUDGES.md", "llms.txt", "docs/llms.txt",
    "docs/site/index.html", "docs/zh/index.html",
))
def test_public_summaries_use_the_canonical_number_set(relative):
    source = html.unescape((ROOT / relative).read_text())
    assert all(value in source for value in CANONICAL), relative


def fact_table(source):
    return re.search(r"\| Question \| Answer \|\n.*?(?=\n\n)", source, re.S)[0]


def test_facts_are_short_bilingual_and_identical_across_surfaces():
    table = fact_table((ROOT / "README.md").read_text())
    rows = [line.split("|")[1:-1] for line in table.splitlines()[2:]]
    assert len(rows) == 8 and all(len(row) == 2 for row in rows)
    for relative in ("JUDGES.md", "README.zh-TW.md"):
        assert fact_table((ROOT / relative).read_text()) == table
    copy = json.loads(subprocess.run(
        ["node", "-e", "process.stdout.write(JSON.stringify(require('./docs/site/script.js')))"],
        cwd=ROOT, check=True, text=True, capture_output=True,
    ).stdout)
    for relative in ("docs/site/index.html", "docs/zh/index.html"):
        source = (ROOT / relative).read_text()
        body = re.search(r'<table class="facts-table">.*?</table>', source, re.S)[0]
        assert len(re.findall(r'<th scope="col"', body)) == 2
        answers = re.findall(r'<span class="fact-answer" lang="([^"]+)">(.*?)</span>', body)
        assert len(answers) == 16
        for index, (_, answer) in enumerate(rows, 1):
            en, zh = answer.strip().split("<br>")
            assert len(en) <= 110 and len(zh) <= 45
            assert answers[(index - 1) * 2:index * 2] == [
                ("en", html.escape(en)), ("zh-Hant", html.escape(zh)),
            ]
            assert copy["en"]["facts"][f"answer{index}"] == en
            assert copy["zh"]["facts"][f"answer{index}"] == zh
        assert source.count(f'href="{GUIDE_URL}#facts-in-detail"') == 1


def test_readme_first_screen_keeps_four_short_facts_in_twelve_lines():
    source = (ROOT / "README.md").read_text().splitlines()
    assert source[12:15] == ["", "## Facts", ""]
    assert all(0 < len(line) <= 70 and "·" not in line for line in source[5:9])
    assert all(line.count("·") <= 2 for line in source[:12])


def test_legacy_bookmarks_have_one_visible_reference_and_no_link_list():
    judges = (ROOT / "JUDGES.md").read_text()
    assert "<details>" not in judges
    anchor_line, = [line for line in judges.splitlines() if line.startswith('<a id="60-second-path"')]
    assert len(re.findall(r'<a id="[^"]+"></a>', anchor_line)) == 16
    assert 'Earlier anchors → [REVIEW_GUIDE.md](docs/evidence/REVIEW_GUIDE.md).' in judges
    for relative in ("docs/site/index.html", "docs/zh/index.html"):
        source = (ROOT / relative).read_text()
        assert '<details class="earlier-sections">' not in source
        assert 'id="how" hidden></a>' in source
        assert f'Earlier anchors → <a href="{GUIDE_URL}">REVIEW_GUIDE.md</a>' in source
        assert 'id="corrected-draft"' not in source
        assert 'data-i18n="draft.rule"' not in source
        assert 'data-i18n="live.lede"' not in source
