"""Keep crawlable translations, metadata and published evaluation counts aligned."""

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://hackathon.dappgo.com"
PAGES = {
    "docs/site/index.html": ("/", "en", "WebApplication"),
    "docs/zh/index.html": ("/zh/", "zh-Hant", "WebApplication"),
    "docs/explorer/index.html": ("/explorer/", "en", "Dataset"),
    "docs/explorer/index.zh.html": ("/explorer/index.zh.html", "zh-Hant", "Dataset"),
}


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.meta, self.links, self.schemas = {}, [], []
        self.title, self.lang, self.data = "", "", None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs["lang"]
        if tag == "meta":
            self.meta[attrs.get("name", attrs.get("property"))] = attrs.get("content")
        if tag == "link":
            self.links.append(attrs)
        if tag == "title":
            self.data = "title"
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.data = "jsonld"
        assert not any(name.startswith("on") for name in attrs), "Inline event handler"

    def handle_data(self, value):
        if self.data == "title":
            self.title += value
        if self.data == "jsonld":
            self.schemas.append(json.loads(value))

    def handle_endtag(self, tag):
        if tag in {"title", "script"}:
            self.data = None


def test_static_chinese_page_cannot_drift_from_template_or_copy():
    result = subprocess.run([sys.executable, "scripts/build_zh_page.py", "--check"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    source = (ROOT / "docs/zh/index.html").read_text()
    for text in ("貼上一則財經貼文。", "運作方式", "每個答案都連到申報文件。"):
        assert text in source
    assert 'src="/script.js?v=' in source
    assert 'href="/explorer/index.zh.html"' in source


def test_all_pages_have_consistent_canonical_metadata_and_valid_schema():
    for relative, (path, language, schema_type) in PAGES.items():
        source = (ROOT / relative).read_text()
        page = Page(source)
        assert page.lang == language
        assert page.meta["og:title"] == page.meta["twitter:title"] == page.title
        assert page.meta["og:description"] == page.meta["twitter:description"] == page.meta["description"]
        assert page.meta["og:url"] == ORIGIN + path
        assert page.meta["og:locale"] == ("en_US" if language == "en" else "zh_TW")
        assert "claude:viewport-fit-sides" not in page.meta
        assert [link["href"] for link in page.links if link.get("rel") == "canonical"] == [ORIGIN + path]
        group = "/explorer/" if schema_type == "Dataset" else "/"
        zh = "/explorer/index.zh.html" if schema_type == "Dataset" else "/zh/"
        assert {link["hreflang"]: link["href"] for link in page.links if link.get("rel") == "alternate"} == {
            "en": ORIGIN + group, "zh-Hant": ORIGIN + zh, "x-default": ORIGIN + group,
        }
        assert len(page.schemas) == 1
        schema = page.schemas[0]
        assert schema["@context"] == "https://schema.org" and schema["@type"] == schema_type
        assert schema["url"] == ORIGIN + path
        assert schema["description"] == page.meta["description"]
        if schema_type == "WebApplication":
            assert schema["operatingSystem"] == "Web" and schema["isAccessibleForFree"] is True
            assert schema["publisher"] == {"@type": "Organization", "name": "DappGo", "url": "https://dappgo.com"}


def test_metadata_numbers_match_the_published_full_evaluation():
    site = json.loads((ROOT / "docs/site/data/site.json").read_text())
    explorer = json.loads((ROOT / "docs/explorer/data.json").read_text())
    count = len(explorer["claims"])
    verdicts = sum(len(claim["results"]) for claim in explorer["claims"])
    assert site["eval"]["claim_count"] == count == 357
    assert site["eval"]["result_count"] == verdicts == 2142
    systems = {system["id"]: system for system in site["systems"]}
    with_sec = f'{100 * systems["agent@baseten"]["accuracy"]:.1f}%'
    without_sec = f'{100 * systems["single_shot@baseten"]["accuracy"]:.1f}%'
    for relative, (_, _, schema_type) in PAGES.items():
        page = Page((ROOT / relative).read_text())
        assert str(count) in page.meta["description"]
        if schema_type == "WebApplication":
            assert with_sec in page.meta["description"] and without_sec in page.meta["description"]
        else:
            assert f"{verdicts:,}" in page.meta["description"]
            assert [item["value"] for item in page.schemas[0]["variableMeasured"]] == [count, verdicts]
    assert 140 <= len(Page((ROOT / "docs/site/index.html").read_text()).meta["description"]) <= 155


def test_sitemap_contains_every_canonical_and_reciprocal_alternates():
    tree = ElementTree.parse(ROOT / "docs/sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
    entries = tree.findall("s:url", ns)
    assert {entry.findtext("s:loc", namespaces=ns) for entry in entries} == {ORIGIN + p[0] for p in PAGES.values()}
    for entry in entries:
        assert entry.findtext("s:lastmod", namespaces=ns)
        assert {link.attrib["hreflang"] for link in entry.findall("x:link", ns)} == {"en", "zh-Hant", "x-default"}
