#!/usr/bin/env python3
"""Generate the complete Traditional Chinese mirror from the shared page structure.

Each prose element has a key in the production COPY dictionary. A parsed tree
emits one locale per element; bilingual answer spans are rejected. This keeps
all seven sections, the form, stepper, chart and no-script fallbacks in parity.
Run after stamping CSS/JS, or use --check. No network or model calls.
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
    pattern = rf'((?<![\w-]){re.escape(name)}=")[^"]*"'
    replaced, count = re.subn(pattern, lambda m: m[1] + html.escape(value, quote=True) + '"', tag)
    if count != 1:
        raise ValueError(f"Expected one {name} in {tag}")
    return replaced


class LocalizedPage(HTMLParser):
    """Parse the semantic template, then render its structure in one language."""

    def __init__(self, copy):
        super().__init__(convert_charrefs=False)
        self.copy = copy
        self.root = {"children": []}
        self.stack = [self.root]

    def value(self, path):
        value = self.copy
        for part in path.split("."):
            value = value[part]
        if not isinstance(value, str):
            raise ValueError(f"Static translation is not a string: {path}")
        return value

    def handle_starttag(self, tag, attrs):
        meta = dict(attrs)
        if tag == "span" and meta.get("lang"):
            raise ValueError("Use a single localized element, not mixed-language spans")
        node = {"tag": tag, "meta": meta, "raw": self.get_starttag_text(), "children": []}
        self.stack[-1]["children"].append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1]["tag"] != tag:
            raise ValueError(f"Unexpected closing tag: {tag}")
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1]["children"].append(data)

    def handle_entityref(self, name):
        self.handle_data("&" + name + ";")

    def handle_charref(self, name):
        self.handle_data("&#" + name + ";")

    def handle_decl(self, decl):
        self.handle_data("<!" + decl + ">")

    def handle_comment(self, data):
        self.handle_data("<!--" + data + "-->")

    def opening(self, tag, meta, raw):
        translated = raw
        if tag == "html":
            translated = attribute(translated, "lang", "zh-Hant")
        if "data-i18n-aria" in meta:
            translated = attribute(translated, "aria-label", self.value(meta["data-i18n-aria"]))
        if "data-i18n-alt" in meta:
            translated = attribute(translated, "alt", self.value(meta["data-i18n-alt"]))
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
        return translated

    def emit(self, node):
        if isinstance(node, str):
            return node
        if "tag" not in node:
            return "".join(self.emit(child) for child in node["children"])
        tag, meta = node["tag"], node["meta"]
        opening = self.opening(tag, meta, node["raw"])
        if tag in VOID:
            return opening
        contents = "".join(self.emit(child) for child in node["children"])
        if "data-i18n" in meta:
            contents = html.escape(self.value(meta["data-i18n"]), quote=False)
        elif tag == "title":
            contents = html.escape(self.copy["metaTitle"], quote=False)
        elif tag == "script" and meta.get("type") == "application/ld+json":
            data = json.loads(contents)
            data.update(name=self.copy["brand"], url=ORIGIN + "/zh/",
                        description=self.copy["metaDescription"], inLanguage="zh-Hant")
            contents = "\n" + json.dumps(data, ensure_ascii=False, indent=4) + "\n    "
        return opening + contents + "</" + tag + ">"


def render(copy=None):
    source = (ROOT / "docs/site/index.html").read_text()
    parser = LocalizedPage((copy or load_copy())["zh"])
    parser.feed(source)
    parser.close()
    if len(parser.stack) != 1:
        raise ValueError("Unclosed HTML elements")
    output = parser.emit(parser.root)
    return output.replace("<!doctype html>", "<!doctype html>\n<!-- Generated by scripts/build_zh_page.py from the shared semantic structure and localized COPY. -->", 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not TARGET.is_file() or TARGET.read_text() != expected:
            print("Stale /zh/ page: run python3 scripts/build_zh_page.py")
            return 1
        print("PASS complete /zh/ structure matches the shared template and localized COPY")
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
