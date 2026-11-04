"""Presentation v2: separate languages, shared facts and traceable evidence."""
import html
from html.parser import HTMLParser
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ("README.md", "README.zh-TW.md", "JUDGES.md", "JUDGES.zh-TW.md", "llms.txt",
            "docs/llms.txt", "docs/site/index.html", "docs/zh/index.html", "docs/site/script.js")
CANONICAL = ("$0.01 per live check", "$0.02 per claim", "6–20 s live", "10 s median",
             "90.2% (240/266)", "1/139", "≈8,000 companies", "23 tested", "≤600 characters")
ZH_NUMBERS = ("$0.01", "$0.02", "6–20 秒", "10 秒", "90.2% (240/266)", "1/139", "8,000 家", "23 家", "≤600 字元")


@pytest.mark.parametrize("relative", SURFACES)
def test_public_summaries_reject_old_number_variants(relative):
    source = (ROOT / relative).read_text()
    assert not re.findall(r"\$0\.020\b|0\.0099\d*|90\.5%", source)
    assert not re.search(r"(?<![\d.])6 s live|即時(?:查核需時)? 6 秒|240/266\s*[（(]90\.2%", source)


@pytest.mark.parametrize("relative", SURFACES[:-1])
def test_public_summaries_use_the_canonical_number_set_in_their_language(relative):
    source = html.unescape((ROOT / relative).read_text())
    values = ZH_NUMBERS if "zh" in relative else CANONICAL
    assert all(value in source for value in values), relative


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


@pytest.mark.parametrize("relative", ("docs/zh/index.html", "README.zh-TW.md", "JUDGES.zh-TW.md"))
def test_chinese_presentation_contains_no_english_prose(relative):
    source = (ROOT / relative).read_text()
    if relative.endswith(".html"):
        parser = Prose(); parser.feed(source); source = "\n".join(parser.text)
    else:
        source = markdown_prose(source)
    # Exact model identifiers and numeric suffixes are data, not UI prose.
    for model in ("meta-models/muse-spark-open-1026", "accounts/fireworks/models/muse-spark-open", "muse-spark-1.3"):
        source = source.replace(model, "")
    source = re.sub(r"\$[\d,.]+[BM]?", "", source)
    assert not re.search(r"[A-Za-z]{2,}", source), (relative, source)


def load_copy():
    return json.loads(subprocess.run(["node", "-e", "process.stdout.write(JSON.stringify(require('./docs/site/script.js')))"],
                                    cwd=ROOT, check=True, text=True, capture_output=True).stdout)


@pytest.mark.parametrize("language", ("en", "zh"))
def test_six_fact_answers_and_evidence_match_site_readme_and_judge_guide(language):
    copy = load_copy()[language]["facts"]
    suffix = "" if language == "en" else ".zh-TW"
    readme, judges = [(ROOT / f"{name}{suffix}.md").read_text() for name in ("README", "JUDGES")]
    header = "| Fact | Answer |" if language == "en" else "| 項目 | 答案 |"
    pattern = re.escape(header) + r"\n.*?(?=\n\n)"
    table = re.search(pattern, readme, re.S)[0]
    assert re.search(pattern, judges, re.S)[0] == table
    rows = table.splitlines()[2:]
    assert len(rows) == 6
    page = (ROOT / ("docs/site/index.html" if language == "en" else "docs/zh/index.html")).read_text()
    articles = re.findall(r'<article class="fact-section".*?</article>', page, re.S)
    assert len(articles) == 6
    for i, (row, article) in enumerate(zip(rows, articles), 1):
        answer = copy[f"answer{i}"]
        assert answer in row
        assert f'data-i18n="facts.answer{i}">{html.escape(answer, quote=False)}</span>' in article
        target = re.search(r'\]\((docs/evidence/[^)]+)\)', row)[1]
        assert (ROOT / target.split("#")[0]).is_file()
        assert f'/blob/main/{target}"' in article
        assert 'lang="en"' not in article and 'lang="zh-Hant"' not in article
        assert article.count('<tr>') == 1


def test_complete_mirrors_have_the_same_sections_and_unique_ids():
    expected = ["top", "stamp-scene", "how", "live-check", "facts", "evidence", "limits"]
    for relative in ("docs/site/index.html", "docs/zh/index.html"):
        parser = Prose(); parser.feed((ROOT / relative).read_text())
        assert parser.headings == expected
        assert len(parser.ids) == len(set(parser.ids))


def test_readmes_open_with_the_robot_and_stay_within_180_lines():
    for relative in ("README.md", "README.zh-TW.md"):
        lines = (ROOT / relative).read_text().splitlines()
        assert len(lines) <= 180
        assert "readme-robot.gif" in lines[2]
        assert lines[5].startswith("**")
        assert any(line.startswith("## ") for line in lines[:12])


def test_budget_configuration_and_public_meter_use_10_daily_60_lifetime():
    yaml = (ROOT / "deploy/k8s/live-check.yaml").read_text()
    toml = (ROOT / "workers/live/wrangler.toml").read_text()
    assert re.search(r'name: DAILY_BUDGET_USD\s+value: "10"', yaml)
    assert re.search(r'name: TOTAL_BUDGET_USD\s+value: "60"', yaml)
    assert 'DAILY_BUDGET_USD = "10"' in toml and 'TOTAL_BUDGET_USD = "60"' in toml
    for relative in ("docs/site/index.html", "docs/zh/index.html"):
        assert 'id="live-budget-meter" max="10"' in (ROOT / relative).read_text()
