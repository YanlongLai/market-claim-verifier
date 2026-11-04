"""README v3: separate languages, shared headline facts and traceable evidence."""
import html
from html.parser import HTMLParser
import json
import re
import subprocess
from pathlib import Path

import pytest

from test_site_stamps_runtime import run_check
from test_language_purity import unexpected_latin

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ("README.md", "README.zh-TW.md", "JUDGES.md", "JUDGES.zh-TW.md", "llms.txt",
            "docs/llms.txt", "docs/site/index.html", "docs/zh/index.html", "docs/site/script.js")
CANONICAL = ("$0.01", "$0.02", "90.2%", "240/266", "1/139", "8,000", "23", "600")


@pytest.mark.parametrize("relative", SURFACES)
def test_public_summaries_reject_old_number_variants(relative):
    source = (ROOT / relative).read_text()
    assert not re.findall(r"\$0\.020\b|0\.0099\d*|6–20 (?:s|秒)", source)
    # v3 explicitly includes historical all-claim results in a labelled table.
    if relative not in {"README.md", "README.zh-TW.md"}:
        assert "90.5%" not in source


@pytest.mark.parametrize("relative", SURFACES[:-1])
def test_public_summaries_use_the_canonical_number_set_in_their_language(relative):
    source = html.unescape((ROOT / relative).read_text())
    assert all(value in source for value in CANONICAL), relative
    assert re.search(r"6 (?:s|秒)", source), relative
    assert re.search(r"10 (?:s|秒)", source), relative


class Prose(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip, self.text, self.ids, self.headings = 0, [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style"}: self.skip += 1
        if attrs.get("id"): self.ids.append(attrs["id"])
        if tag == "section" and attrs.get("id"): self.headings.append(attrs["id"])
        for key in ("alt", "aria-label", "title"):
            if attrs.get(key): self.text.append(attrs[key])

    def handle_endtag(self, tag):
        if tag in {"script", "style"}: self.skip -= 1

    def handle_data(self, value):
        if not self.skip and value.strip(): self.text.append(value.strip())


def markdown_prose(source):
    source = re.sub(r"```.*?```|<!--.*?-->", "", source, flags=re.S)
    source = re.sub(r"`[^`]*`", "", source)
    source = re.sub(r"\]\([^)]*\)", "]", source)
    return re.sub(r"<[^>]*>", "", source)


@pytest.mark.parametrize("relative", ("docs/site/index.html", "README.md", "JUDGES.md", "llms.txt", "docs/llms.txt"))
def test_english_presentation_contains_no_chinese(relative):
    assert not re.search(r"[\u3400-\u9fff]", (ROOT / relative).read_text()), relative


@pytest.mark.parametrize("viewport", (375, 1440))
@pytest.mark.parametrize("reduced", (False, True))
def test_english_stamp_scene_contains_no_chinese_in_any_text_node_or_label(viewport, reduced):
    # Exercise the shipped data and renderer, including hidden/static cards,
    # bylines, repost attribution, media labels, captions and accessible names.
    # Do not strip tokens or limit this to prose elements.
    run_check(r"""
function check(node) {
  assert.ok(!/[\u3400-\u9fff]/u.test(node.textContent), node.textContent);
  for (const key of ['alt', 'aria-label', 'title']) {
    const value = node.getAttribute(key) || '';
    assert.ok(!/[\u3400-\u9fff]/u.test(value), `${key}: ${value}`);
  }
  node.children.forEach(check);
}
for (let index = 0; index < cards.length; index++) {
  for (const age of [.1, 1.8, 2.95, 4.1, 4.94]) {
    seek(api.timing.starts[index] + age);
    check(scene);
  }
}
""", viewport=viewport, reduced=reduced, language="en", page="docs/site/index.html")


@pytest.mark.parametrize("relative", ("docs/zh/index.html", "README.zh-TW.md", "JUDGES.zh-TW.md"))
def test_chinese_presentation_contains_no_english_prose(relative):
    source = (ROOT / relative).read_text()
    assert not unexpected_latin(source, relative.endswith(".html")), relative


def load_copy():
    return json.loads(subprocess.run(["node", "-e", "process.stdout.write(JSON.stringify(require('./docs/site/script.js')))"],
                                    cwd=ROOT, check=True, text=True, capture_output=True).stdout)


@pytest.mark.parametrize("language", ("en", "zh"))
def test_six_facts_have_one_title_compact_copy_and_the_shared_evidence(language):
    copy = load_copy()[language]["facts"]
    page = (ROOT / ("docs/site/index.html" if language == "en" else "docs/zh/index.html")).read_text()
    articles = re.findall(r'<article class="fact-section".*?</article>', page, re.S)
    assert len(articles) == 6
    for i, article in enumerate(articles, 1):
        for key in (f"question{i}", f"detail{i}", f"summary{i}", "label", "source"):
            assert article.count(f'data-i18n="facts.{key}"') == 1
            assert f'>{html.escape(copy[key], quote=False)}<' in article
        target = re.search(r'/blob/main/(docs/evidence/[^"#]+)', article)[1]
        assert (ROOT / target.split("#")[0]).is_file()
        assert 'lang="en"' not in article and 'lang="zh-Hant"' not in article
        assert '<table' not in article and '<th' not in article
        assert article.count('<h3') == 1 and article.count('<p') == 2
        assert 'class="fact-line"' in article and 'class="fact-reference"> · <a' in article


def test_complete_mirrors_have_the_same_sections_and_unique_ids():
    expected = ["top", "stamp-scene", "how", "live-check", "facts", "evidence", "limits"]
    for relative in ("docs/site/index.html", "docs/zh/index.html"):
        parser = Prose(); parser.feed((ROOT / relative).read_text())
        assert parser.headings == expected
        assert len(parser.ids) == len(set(parser.ids))


def test_readmes_follow_v3_length_and_mirror_section_structure():
    outlines = []
    for relative in ("README.md", "README.zh-TW.md"):
        lines = (ROOT / relative).read_text().splitlines()
        assert 250 <= len(lines) <= 320
        assert "readme-robot.gif" in lines[2]
        assert re.search(r'!\[[^\]]+\]\(docs/site/img/readme-robot.gif\)', lines[2])
        assert lines[4].startswith("**")
        assert any(line.startswith("## ") for line in lines[:12])
        outlines.append([len(re.match(r'#+', line)[0]) for line in lines if line.startswith('#')])
        assert '<!-- readme-shot:try-story-a -->' in lines
        assert '<!-- readme-shot:corrected-draft -->' in lines
    assert outlines[0] == outlines[1]
    for relative in ("JUDGES.md", "JUDGES.zh-TW.md"):
        assert len((ROOT / relative).read_text().splitlines()) <= 120


def test_readme_accuracy_tables_match_completed_saved_results():
    claims = json.loads((ROOT / 'docs/explorer/data.json').read_text())['claims']
    for relative in ('README.md', 'README.zh-TW.md'):
        text = (ROOT / relative).read_text().replace('（', '(').replace('）', ')')
        text = re.sub(r'\s+', '', text)
        for provider in ('baseten', 'fireworks', 'meta'):
            for method in ('agent', 'single_shot'):
                system = f'{method}@{provider}'
                for subset in (claims, [c for c in claims if c['split'] == 'test']):
                    correct = sum(c['results'][system]['status'] == 'completed'
                                  and c['results'][system]['verdict'] == c['gold'] for c in subset)
                    assert f'{100 * correct / len(subset):.1f}%({correct}/{len(subset)})' in text


def test_budget_configuration_and_public_meter_use_10_daily_60_lifetime():
    yaml = (ROOT / "deploy/k8s/live-check.yaml").read_text()
    toml = (ROOT / "workers/live/wrangler.toml").read_text()
    assert re.search(r'name: DAILY_BUDGET_USD\s+value: "10"', yaml)
    assert re.search(r'name: TOTAL_BUDGET_USD\s+value: "60"', yaml)
    assert 'DAILY_BUDGET_USD = "10"' in toml and 'TOTAL_BUDGET_USD = "60"' in toml
    for relative in ("docs/site/index.html", "docs/zh/index.html"):
        assert 'id="live-budget-meter" max="10"' in (ROOT / relative).read_text()
