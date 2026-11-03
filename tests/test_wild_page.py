"""Shipped-page contracts and offline execution; visual QA runs separately."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit

import pytest

from docs.scripts import build_wild as wild
from test_wild_builder import evidence, write_json  # shared filesystem fixture

PAGE = wild.ROOT / "docs/wild"


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": "document", "attrs": {}, "children": []}
        self.stack = [self.root]
        self.nodes = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": []}
        self.stack[-1]["children"].append(node)
        self.nodes.append(node)
        if tag not in {"meta", "link", "br", "hr", "img", "input", "source", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]["tag"] == tag:
                self.stack = self.stack[:index]
                return

    def handle_data(self, data):
        self.stack[-1]["children"].append(data)


def test_csp_and_every_automatic_resource_are_same_origin():
    doc = Document((PAGE / "index.html").read_text())
    csp = next(n["attrs"]["content"] for n in doc.nodes if n["attrs"].get("http-equiv") == "Content-Security-Policy")
    assert "default-src 'none'" in csp
    for directive in ("script-src 'self'", "style-src 'self'", "connect-src 'self'", "base-uri 'none'", "object-src 'none'"):
        assert directive in csp
    assert "unsafe-inline" not in csp
    for node in doc.nodes:
        attrs = node["attrs"]
        assert not any(k.startswith("on") or k == "style" for k in attrs)
        if node["tag"] in {"script", "link", "img", "iframe", "source", "video", "audio"}:
            for key in ("href", "src", "poster"):
                if key in attrs:
                    value = attrs[key]
                    assert not urlsplit(value).scheme and not value.startswith(("/", "//"))
                    assert (PAGE / value).is_file()
    css = (PAGE / "styles.css").read_text()
    assert not re.search(r"@import|url\(", css)
    script = (PAGE / "script.js").read_text()
    assert "innerHTML" not in script and "eval(" not in script
    assert script.count("win.fetch(") == 1


def test_phone_layout_and_accessible_fallback_contract():
    doc = Document((PAGE / "index.html").read_text())
    ids = [n["attrs"]["id"] for n in doc.nodes if "id" in n["attrs"]]
    assert len(ids) == len(set(ids))
    assert len([n for n in doc.nodes if n["tag"] == "h1"]) == 1
    assert any(n["tag"] == "noscript" for n in doc.nodes)
    assert any(n["attrs"].get("class") == "skip-link" for n in doc.nodes)
    assert any(n["attrs"].get("aria-live") == "polite" for n in doc.nodes)
    for node in doc.nodes:
        if node["tag"] == "a" and node["attrs"].get("href", "").startswith("#"):
            assert node["attrs"]["href"][1:] in ids
    css = (PAGE / "styles.css").read_text()
    phone = css.split("@media (max-width: 600px)")[1].split("@media")[0]
    assert ".comparison { grid-template-columns: 1fr;" in phone
    assert ".source-detail, .before-after { grid-template-columns: 1fr;" in phone
    assert "min-width: 0" in phone
    assert "repeat(2, 1fr)" in phone
    assert "min-height: 44px" in css
    assert "overflow-x: hidden" not in css  # Don't conceal layout failures.
    assert "prefers-reduced-motion: no-preference" in css
    assert ":focus-visible" in css


@pytest.mark.skipif(shutil.which("node") is None, reason="Node 22+ required")
@pytest.mark.parametrize("config", [{}, {"language": "zh", "dark": True}, {"storageBlocked": True}, {"unavailable": True}, {"url": "https://example.test/wild/"}])
def test_production_page_runtime_without_network(evidence, config):
    data = wild.build(evidence)
    payload = {"dom": Document((PAGE / "index.html").read_text()).root, "data": data, **config}
    result = subprocess.run(["node", str(wild.ROOT / "tests/wild_runtime.mjs")], input=json.dumps(payload), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("report", [False, True])
def test_page_runtime_renders_optional_bilingual_fixcheck(evidence, report):
    path = evidence / wild.FIXCHECK
    write_json(path / "case.json", {"status": "completed"})
    write_json(path / "summary.json", {"kind": "posthoc_fixcheck", "comparisons": [{"id": "T33", "description": {"en": "Fixture correction", "zh": "測試修正"}, "before": {"en": "Before fixture", "zh": "修正前測試"}, "after": {"en": "After fixture", "zh": "修正後測試"}, "evidence_path": (wild.FIXCHECK / "case.json").as_posix()}]})
    if report:
        (path / "summary.json").unlink()
        (path / "REPORT.md").write_text("# Post-hoc fix recheck\n\n| Case | Before | After |\n|---|---|---|\n| T33 | supported | contradicted |\n")
    test_production_page_runtime_without_network(evidence, {})
