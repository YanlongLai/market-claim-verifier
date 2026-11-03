#!/usr/bin/env python3
"""Build /zh/ from the English HTML and the production COPY dictionary.

Node imports the complete script's DOM-free export, rather than extracting a
JavaScript object with a regex. Only translated spans/attributes are replaced;
the English layout stays the template. Run after stamping CSS/JS, or use --check.
"""

import argparse
import html
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://hackathon.dappgo.com"
TARGET = ROOT / "docs/zh/index.html"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def load_copy():
    result = subprocess.run(
        ["node", "-e", "const copy = require(process.argv[1]); "
         "const data = require(process.argv[2]); "
         "for (const lang of Object.values(copy)) lang.results.caption = lang.results.caption(data.eval.claim_count); "
         "process.stdout.write(JSON.stringify(copy));",
         str(ROOT / "docs/site/script.js"), str(ROOT / "docs/site/data/site.json")],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def attribute(tag, name, value):
    pattern = rf'(\b{re.escape(name)}=")[^"]*"'
    replaced, count = re.subn(pattern, lambda m: m[1] + html.escape(value, quote=True) + '"', tag)
    if count != 1:
        raise ValueError(f"Expected one {name} in {tag}")
    return replaced


class Translate(HTMLParser):
    def __init__(self, source, copy):
        super().__init__(convert_charrefs=False)
        self.source, self.copy = source, copy
        self.lines = [0]
        for match in re.finditer("\n", source):
            self.lines.append(match.end())
        self.stack, self.edits = [], []

    def position(self):
        row, column = self.getpos()
        return self.lines[row - 1] + column

    def value(self, path):
        value = self.copy
        for part in path.split("."):
            value = value[part]
        if not isinstance(value, str):
            raise ValueError(f"Static translation is not a string: {path}")
        return value

    def handle_starttag(self, tag, attrs):
        meta = dict(attrs)
        start = self.position()
        raw = self.get_starttag_text()
        translated = raw
        if tag == "html":
            translated = attribute(translated, "lang", "zh-Hant")
        if "data-i18n-aria" in meta:
            translated = attribute(translated, "aria-label", self.value(meta["data-i18n-aria"]))
        for name in ("href", "src", "poster"):
            value = meta.get(name, "")
            if value and not value.startswith(("/", "#", "?")) and not urlsplit(value).scheme:
                translated = attribute(translated, name, urlsplit(urljoin(ORIGIN + "/", value)).path +
                                         ("?" + urlsplit(value).query if urlsplit(value).query else "") +
                                         ("#" + urlsplit(value).fragment if urlsplit(value).fragment else ""))
        if tag == "link" and meta.get("rel") == "canonical":
            translated = attribute(translated, "href", ORIGIN + "/zh/")
        key = meta.get("property", meta.get("name"))
        content = {
            "description": self.copy["metaDescription"],
            "og:title": self.copy["metaTitle"], "twitter:title": self.copy["metaTitle"],
            "og:description": self.copy["metaDescription"], "twitter:description": self.copy["metaDescription"],
            "og:image:alt": self.copy["metaImageAlt"], "twitter:image:alt": self.copy["metaImageAlt"],
            "og:url": ORIGIN + "/zh/", "og:locale": "zh_TW", "og:locale:alternate": "en_US",
        }
        if tag == "meta" and key in content:
            translated = attribute(translated, "content", content[key])
        if meta.get("data-language"):
            active = meta["data-language"] == "zh"
            translated = attribute(translated, "class", "language-button" + (" is-active" if active else ""))
            translated = translated.replace(' aria-current="page"', "")
            if active:
                translated = translated[:-1] + ' aria-current="page">'
        if meta.get("data-example"):
            active = meta["data-example"] == "zh"
            translated = attribute(translated, "class", "example-button" + (" is-active" if active else ""))
            translated = attribute(translated, "aria-selected", str(active).lower())
        if meta.get("data-i18n") == "footer.explorer":
            translated = attribute(translated, "href", "/explorer/index.zh.html")
        if translated != raw:
            self.edits.append((start, start + len(raw), translated))
        if tag not in VOID:
            self.stack.append((tag, start + len(raw), meta))

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError(f"Unexpected closing tag: {tag}")
        _, start, meta = self.stack.pop()
        end = self.position()
        value = None
        if "data-i18n" in meta:
            value = html.escape(self.value(meta["data-i18n"]), quote=False)
        elif tag == "title":
            value = html.escape(self.copy["metaTitle"], quote=False)
        elif tag == "script" and meta.get("type") == "application/ld+json":
            data = json.loads(self.source[start:end])
            data.update(url=ORIGIN + "/zh/", description=self.copy["metaDescription"], inLanguage="zh-Hant")
            value = "\n" + json.dumps(data, ensure_ascii=False, indent=4) + "\n    "
        if value is not None:
            self.edits.append((start, end, value))


def render(copy=None):
    source = (ROOT / "docs/site/index.html").read_text()
    parser = Translate(source, (copy or load_copy())["zh"])
    parser.feed(source)
    parser.close()
    if parser.stack:
        raise ValueError("Unclosed HTML elements")
    end = len(source)
    for start, stop, replacement in sorted(parser.edits, reverse=True):
        if stop > end:
            raise ValueError("Overlapping translated elements")
        source = source[:start] + replacement + source[stop:]
        end = start
    return source.replace("<!doctype html>", "<!doctype html>\n<!-- Generated by scripts/build_zh_page.py; edit docs/site/index.html and its COPY dictionary. -->", 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not TARGET.is_file() or TARGET.read_text() != expected:
            print("Stale /zh/ page: run python3 scripts/build_zh_page.py")
            return 1
        print("PASS static /zh/ matches English HTML and production COPY")
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
