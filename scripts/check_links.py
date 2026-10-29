#!/usr/bin/env python3
"""Check Markdown/llms.txt file links and anchors; optionally check HTTP links.

Local checks need only the Python standard library and never use the network.
Code examples are excluded. HTTP 401/403/429 and transport failures are reported
as unverified, rather than silently treated as working links.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from html import unescape
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", ".cache", ".pytest_cache", "__pycache__", "node_modules"}


def documents(root: Path) -> list[Path]:
    found = []
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not (Path(folder) / d).is_symlink())
        for name in sorted(files):
            path = Path(folder) / name
            if not path.is_symlink() and (path.suffix.lower() in {".md", ".markdown"} or path == root / "llms.txt"):
                found.append(path)
    return found


def prose(text: str, *, inline_code: bool = True) -> str:
    """Blank code while keeping offsets/line numbers intact."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append("\n" if line.endswith("\n") else "")
        elif fence is not None or line.startswith("    ") or line.startswith("\t"):
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(line)
    content = "".join(lines)
    return re.sub(r"(`+).*?\1", lambda m: " " * len(m[0]), content) if inline_code else content


def links(text: str) -> list[tuple[str, int]]:
    content = prose(text)
    found = []

    def add(url: str, start: int) -> None:
        found.append((unescape(url.strip("<>")), content.count("\n", 0, start) + 1))

    # Find destinations after ](, including balanced parentheses in filenames.
    for match in re.finditer(r"\]\(\s*", content):
        start = match.end()
        if content[start:start + 1] == "<":
            end = content.find(">", start + 1)
            if end != -1:
                add(content[start + 1:end], match.start())
            continue
        depth = 0
        end = start
        while end < len(content):
            char = content[end]
            if char == "\\":
                end += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            end += 1
        if end > start:
            add(content[start:end], match.start())
    for match in re.finditer(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", content, re.MULTILINE):
        add(match[1], match.start())
    for match in re.finditer(r"\b(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", content, re.IGNORECASE):
        add(match[1], match.start())
    for match in re.finditer(r"<(https?://[^<>\s]+)>", content):
        add(match[1], match.start())
    # GitHub also renders bare HTTP URLs as links.
    for match in re.finditer(r"https?://[^\s<>\"']+", content):
        url = match[0].rstrip(".,;:!?]")
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        add(url, match.start())
    return sorted(set(found), key=lambda item: (item[1], item[0]))


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    ids = set(re.findall(r"\b(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", text))
    if path.suffix.lower() not in {".md", ".markdown"}:
        return ids
    used = set()
    # GitHub heading slugs, including suffixes on repeated headings.
    clean = prose(text, inline_code=False)
    for match in re.finditer(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", clean, re.MULTILINE):
        title = re.sub(r"<[^>]*>", "", unescape(match[1])).replace("`", "").lower()
        title = re.sub(r"!?(?:\[([^\]]*)\])\([^)]*\)", r"\1", title)
        slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        candidate, suffix = slug, 0
        while candidate in used:
            suffix += 1
            candidate = f"{slug}-{suffix}"
        used.add(candidate)
    return ids | used


def undefined_references(text: str) -> list[tuple[str, int]]:
    content = prose(text)
    normalize = lambda label: " ".join(label.lower().split())
    definitions = {normalize(match[1]) for match in re.finditer(r"^ {0,3}\[([^\]]+)\]:", content, re.MULTILINE)}
    missing = []
    for match in re.finditer(r"\[([^\]\n]+)\]\[([^\]\n]*)\]", content):
        label = match[2] or match[1]
        if normalize(label) not in definitions:
            missing.append((label, content.count("\n", 0, match.start()) + 1))
    return missing


def http_status(url: str) -> tuple[str, str]:
    request = Request(url, headers={"User-Agent": "market-claim-verifier-link-check/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            return "ok", str(response.status)
    except HTTPError as error:
        if error.code in {401, 403, 429} or error.code >= 500:
            return "unverified", f"HTTP {error.code}"
        return "broken", f"HTTP {error.code}"
    except (URLError, TimeoutError, OSError, ValueError) as error:
        return "unverified", str(error.reason if isinstance(error, URLError) else error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--external", action="store_true", help="Also GET unique HTTP(S) destinations (requires network)")
    args = parser.parse_args()
    root = args.root.resolve()
    files = documents(root)
    failures = []
    external: dict[str, str] = {}
    local_count = 0
    cache: dict[Path, set[str]] = {}
    for source in files:
        content = source.read_text(encoding="utf-8")
        for label, line in undefined_references(content):
            failures.append(f"{source.relative_to(root)}:{line}: undefined link reference [{label}]")
        for target, line in links(content):
            location = f"{source.relative_to(root)}:{line}"
            url = urlsplit(target)
            if url.scheme in {"http", "https"}:
                external.setdefault(urlunsplit(url._replace(fragment="")), location)
                continue
            if url.scheme in {"mailto", "tel", "data"}:
                continue
            if url.scheme:
                failures.append(f"{location}: unsupported link scheme: {target}")
                continue
            local_count += 1
            path = (source.parent / unquote(url.path)).resolve() if url.path else source
            if not path.is_relative_to(root):
                failures.append(f"{location}: file link leaves the repository: {target}")
                continue
            if not path.exists():
                failures.append(f"{location}: missing {target}")
                continue
            fragment = unquote(url.fragment)
            if fragment and path.is_file():
                if re.fullmatch(r"L\d+(?:-L\d+)?", fragment):
                    last = int(fragment.split("L")[-1])
                    valid = 1 <= last <= len(path.read_text(encoding="utf-8").splitlines())
                else:
                    if path not in cache:
                        cache[path] = anchors(path)
                    valid = fragment in cache[path]
                if not valid:
                    failures.append(f"{location}: missing anchor {target}")
    print(f"Markdown: {len(files)} files; {local_count} local links/anchors; {len(external)} unique HTTP(S) links")
    for failure in failures:
        print(f"FAIL {failure}")
    if args.external:
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(http_status, external))
        counts = {kind: sum(status[0] == kind for status in statuses) for kind in ("ok", "broken", "unverified")}
        for (url, location), (kind, detail) in zip(external.items(), statuses):
            if kind != "ok":
                print(f"{kind.upper()} {location}: {url} ({detail})")
            if kind == "broken":
                failures.append(url)
        print("HTTP: " + "; ".join(f"{count} {kind}" for kind, count in counts.items()))
    else:
        print("HTTP links not fetched (offline); use --external for a separate network check")
    if failures:
        return 1
    print("PASS Markdown links and anchors" if not args.external else "PASS local links; no confirmed broken HTTP links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
