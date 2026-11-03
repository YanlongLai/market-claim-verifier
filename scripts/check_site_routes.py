#!/usr/bin/env python3
"""Crawl local href/src links against the actual Pages output (never SPA fallback)."""

import posixpath
import re
from collections import deque
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from serve_site import ROOT, output_path

ORIGIN = "https://hackathon.dappgo.com"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        meta = dict(attrs)
        if tag == "meta" and meta.get("property", meta.get("name")) in {"og:image", "twitter:image"}:
            self.links.append(meta["content"])
        for key, value in attrs:
            if value and key in {"href", "src", "poster"}:
                self.links.append(value)
            if value and key == "srcset":
                self.links.extend(part.strip().split()[0] for part in value.split(","))


def crawl():
    queue = deque([("/", "entry"), ("/zh/", "entry"), ("/explorer/", "entry"),
                   ("/explorer/index.zh.html", "entry"), ("/llms.txt", "entry")])
    visited = set()
    missing = []
    external = set()
    while queue:
        url, referrer = queue.popleft()
        parsed = urlsplit(urljoin(ORIGIN + "/", url))
        if parsed.netloc != urlsplit(ORIGIN).netloc:
            external.add(f"{parsed.scheme}://{parsed.netloc}")
            continue
        path = posixpath.normpath(parsed.path)
        if parsed.path.endswith("/") and path != "/":
            path += "/"
        if path in visited:
            continue
        visited.add(path)
        file = output_path(path)
        if file.is_dir():
            file /= "index.html"
        if not file.is_file():
            missing.append((path, referrer))
            print(f"MISSING {path} (from {referrer})")
            continue
        print(f"OK {path} -> docs/{file.relative_to(ROOT)}")
        links = []
        if file.suffix == ".html":
            parser = Links()
            parser.feed(file.read_text())
            links += parser.links
        if file.suffix in {".html", ".css"}:
            links += re.findall(r"url\(\s*[\"']?([^\s\)\"']+)", file.read_text())
        if file.suffix == ".md" or file.name == "llms.txt":
            links += re.findall(r"!?\[[^\]]*\]\(([^\s)]+)", file.read_text())
        if file.suffix == ".js":
            links += re.findall(r"fetch\([\"']([^\"']+)", file.read_text())
        for link in links:
            if link.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
                continue
            queue.append((urljoin(ORIGIN + path, unescape(link)), path))
    print(f"CHECKED {len(visited)} local paths; {len(missing)} missing; no fallback used")
    print("EXTERNAL link origins (not fetched): " + ", ".join(sorted(external)))
    return bool(missing)


if __name__ == "__main__":
    raise SystemExit(crawl())
