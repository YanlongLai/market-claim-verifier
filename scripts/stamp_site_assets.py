#!/usr/bin/env python3
"""Stamp ?v=<content hash> onto site CSS/JS links.

The dappgo.com Cloudflare zone gives CSS/JS a 4-hour browser cache, so an
unversioned styles.css or script.js can outlive the HTML that uses it.
Run after editing any of these assets; tests fail when a stamp is stale.
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["docs/site/index.html", "docs/zh/index.html", "docs/explorer/index.html", "docs/explorer/index.zh.html"]
LINK = re.compile(r'(?P<attr>href|src)="(?P<name>/?(?:[\w.-]+/)*[\w.-]+\.(?:css|js))(?:\?v=[0-9a-f]+)?"')


def version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def stamped(page: Path) -> str:
    html = page.read_text()

    def replace(match: re.Match) -> str:
        name = match["name"]
        asset = ROOT / "docs/site" / name.lstrip("/") if name.startswith("/") else page.parent / name
        return f'{match["attr"]}="{name}?v={version(asset)}"'

    return LINK.sub(replace, html)


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for relative in PAGES:
        page = ROOT / relative
        html = stamped(page)
        if html != page.read_text():
            stale.append(relative)
            if not check:
                page.write_text(html)
    if check and stale:
        print("Stale asset versions (run scripts/stamp_site_assets.py):", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
