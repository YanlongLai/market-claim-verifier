"""SEC Item 2.02 discovery and content-addressed earnings exhibit snapshots.

Only SEC filing-index EX-99.1 / EX-99.2 HTML links are accepted. A release is
furnished, unaudited evidence; this module makes no numeric assertions.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

from .sec_transport import USER_AGENT, sec_get


class ReleaseError(RuntimeError):
    pass


class _Index(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[str, list[str]]] = []
        self.parts: list[str] = []
        self.links: list[str] = []
        self.in_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.in_row, self.parts, self.links = True, [], []
        if tag == "a" and self.in_row:
            self.links.extend(v for k, v in attrs if k == "href" and v)

    def handle_data(self, data: str) -> None:
        if self.in_row:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_row:
            self.rows.append((" ".join(self.parts), self.links))
            self.in_row = False


def exhibit_links(raw: bytes, index_url: str) -> list[tuple[str, str]]:
    parser = _Index()
    parser.feed(raw.decode("utf-8", errors="replace"))
    found: list[tuple[str, str]] = []
    base_path = urlsplit(index_url).path.rsplit("/", 1)[0] + "/"
    for text, links in parser.rows:
        match = re.search(r"\bEX-99\.(1|2)\b", text, re.I)
        if not match:
            continue
        for href in links:
            url = urljoin(index_url, href)
            parts = urlsplit(url)
            if (parts.scheme == "https" and parts.hostname == "www.sec.gov"
                    and parts.path.startswith(base_path)
                    and re.search(r"\.html?$", parts.path, re.I)
                    and not parts.query and not parts.fragment):
                item = (f"99.{match[1]}", url)
                if item not in found:
                    found.append(item)
    return sorted(found)  # release before optional text slides


def _rows(document: dict[str, Any]) -> list[dict[str, str]]:
    table = document.get("filings", {}).get("recent", document)
    forms = table.get("form", [])
    return [{key: str(values[i]) for key, values in table.items()
             if isinstance(values, list) and i < len(values)}
            for i in range(len(forms)) if forms[i] == "8-K"
            and "2.02" in re.findall(r"\d+\.\d+", str(table.get("items", [""] * len(forms))[i]))]


def period_window(period: str) -> tuple[date, date]:
    """Wide discovery window, never used to assert a number's period.

    Fiscal calendars can end in any month. Text/column matching, below this
    transport layer, must still establish the exact fiscal/calendar period.
    """
    match = re.fullmatch(r"(?:FY)?(20\d{2})(?:Q[1-4])?", period.upper())
    if not match:
        raise ReleaseError("an explicit FYyyyy[Qn] or yyyyQn period is required")
    year = int(match[1])
    return date(year - 1, 1, 1), date(year + 1, 5, 1)


class ReleaseClient:
    def __init__(self, cache_dir: str | Path, *, fetcher: Callable[[str], Any] | None = None,
                 user_agent: str = USER_AGENT, timeout: float = 20.0) -> None:
        self.cache_dir = Path(cache_dir) / "releases"
        self.fetcher = fetcher or (lambda url: sec_get(url, user_agent=user_agent, timeout=timeout))
        self.loaded: dict[str, dict[str, Any]] = {}

    def read(self, url: str) -> tuple[bytes, dict[str, Any]]:
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in {"data.sec.gov", "www.sec.gov"}:
            raise ReleaseError("only SEC HTTPS documents are permitted")
        name = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / name
        meta_path = self.cache_dir / (name + ".meta.json")
        if path.is_file() and meta_path.is_file():
            raw, meta = path.read_bytes(), json.loads(meta_path.read_text())
            if meta.get("sha256") != hashlib.sha256(raw).hexdigest() or meta.get("url") != url:
                raise ReleaseError("release cache integrity failure")
        else:
            result = self.fetcher(url)
            raw = result if isinstance(result, bytes) else result.encode() if isinstance(result, str) else json.dumps(result).encode()
            meta = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(),
                    "fetched_at": datetime.now(timezone.utc).isoformat()}
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        self.loaded[url] = meta
        return raw, dict(meta)

    def filings(self, cik: str, period: str) -> list[dict[str, str]]:
        start, end = period_window(period)
        url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
        raw, _ = self.read(url)
        doc = json.loads(raw)
        rows = _rows(doc)
        # Recent is not complete for older requested periods. Follow only
        # SEC-listed historical shards whose declared date range overlaps.
        for shard in doc.get("filings", {}).get("files", []):
            if (str(shard.get("filingTo", "")) >= start.isoformat()
                    and str(shard.get("filingFrom", "9999")) <= end.isoformat()
                    and re.fullmatch(r"CIK\d+-submissions-\d+\.json", str(shard.get("name", "")))):
                archive, _ = self.read("https://data.sec.gov/submissions/" + shard["name"])
                rows.extend(_rows(json.loads(archive)))
        unique = {row["accessionNumber"]: row for row in rows
                  if start.isoformat() <= row.get("filingDate", "") <= end.isoformat()
                  and re.fullmatch(r"\d{10}-\d{2}-\d{6}", row.get("accessionNumber", ""))}
        return sorted(unique.values(), key=lambda row: row["filingDate"], reverse=True)

    def exhibits(self, cik: str, filing: dict[str, str]) -> list[dict[str, Any]]:
        accession = filing["accessionNumber"]
        base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"
        index_url = f"{base}/{accession}-index.html"
        raw, index_meta = self.read(index_url)
        exhibits = []
        for exhibit, url in exhibit_links(raw, index_url):
            content, meta = self.read(url)
            # No PDF/OCR, binary slide decks, or inline-only links masquerading as HTML.
            if not re.search(rb"<(?:html|body|div|p|table)\b", content[:20000], re.I):
                continue
            exhibits.append({"cik": f"{int(cik):010d}", "accession": accession,
                             "filed": filing["filingDate"], "exhibit": exhibit,
                             "form": f"8-K Ex {exhibit}", "exhibit_url": url,
                             "sha256": meta["sha256"], "index_url": index_url,
                             "index_sha256": index_meta["sha256"], "raw": content})
        return exhibits
