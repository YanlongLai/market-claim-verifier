"""Snapshot the published DappGo feed; never export its text to evidence files.

Raw news text is restricted to an explicitly selected ignored .cache directory.
The public receipt has only hashes, URLs, timestamps and aggregate counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BASE = "https://news.dappgo.com"
SEED = "dappgo-news-2026-11-02-v1"
FINANCIAL = re.compile(
    r"\b(revenue|revenues|sales|eps|earnings per share|net (?:income|profit|loss)|"
    r"gross (?:margin|profit)|operating (?:income|profit|margin)|guidance|outlook|"
    r"earnings growth|profit growth)\b|營收|每股盈餘|每股獲利|淨利|毛利率|財測|獲利成長", re.I)
NUMBER = re.compile(r"\d")
SECONDARY_FINANCIAL = re.compile(
    r"\b(profit|profits|margin|margins|earnings|growth)\b|EPS|淨損|毛利|年增|年減|獲利|盈餘", re.I)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def pointer_url(market: str, pointer: dict) -> str:
    """Match dappgo-news-app/src/news.ts pointerUrls, with full byte validation later."""
    if market not in {"us", "tw"} or not isinstance(pointer, dict):
        raise ValueError("invalid market/pointer")
    full_hash = str(pointer.get("hash", "")).strip()
    path = str(pointer.get("data_url_v2", "")).strip()
    match = re.fullmatch(r"dashboard/data-([a-f0-9]{12,64})\.json", path)
    if not re.fullmatch(r"[a-f0-9]{64}", full_hash) or not match or not full_hash.startswith(match[1]):
        raise ValueError("invalid immutable same-market pointer")
    return f"{BASE}/api/markets/{market}/{path}"


def validate_payload(raw: bytes, pointer: dict) -> dict:
    # The publisher's logical data hash is not a hash of the delivered bytes.
    # Keep a separate byte SHA-256; never claim the two hashes are equivalent.
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("ticker_data"), dict) or not data["ticker_data"]:
        raise ValueError("payload has no ticker data")
    if not any(re.fullmatch(r"[A-Z0-9.\-]{1,12}", symbol) and isinstance(value, dict)
               for symbol, value in data["ticker_data"].items()):
        raise ValueError("payload has no valid ticker data")
    if data.get("data_hash") != pointer["hash"].strip():
        raise ValueError("payload data_hash does not match pointer")
    return data


def stories(market: str, payload: dict) -> list[dict]:
    """Flatten/deduplicate URLs without changing any source assertions (cache only)."""
    by_url = {}
    for ticker, company in sorted(payload["ticker_data"].items()):
        if not re.fullmatch(r"[A-Z0-9.\-]{1,12}", ticker) or not isinstance(company, dict):
            continue
        for item in company.get("news", []):
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).hostname:
                continue
            if url in by_url:
                by_url[url]["tickers"].append(ticker)
                continue
            text = " ".join(str(item.get(k) or "") for k in (
                "title", "title_en", "title_zh", "summary", "summary_en", "summary_zh"))
            raw = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            by_url[url] = {
                "market": market, "url": url, "tickers": [ticker], "ticker": ticker,
                "outlet": str(item.get("source") or item.get("provider") or urlsplit(url).hostname),
                "published_at": item.get("published_at_utc") or item.get("date"),
                "story_sha256": digest(raw), "company": company.get("name", ticker),
                "financial_candidate": bool(FINANCIAL.search(text) and NUMBER.search(text)),
                "raw": item,
            }
    return list(by_url.values())


def sample(items: list[dict], target: int, *, seed: str = SEED) -> list[dict]:
    """Seeded round-robin strata; stable under input permutation, no gold inputs."""
    if target < 0:
        raise ValueError("negative sample size")
    rank = lambda value: digest((seed + "\0" + value).encode())
    groups = defaultdict(list)
    for item in items:
        groups[(item["market"], item["outlet"], item["ticker"])].append(item)
    keys = sorted(groups, key=lambda key: rank(json.dumps(key)))
    queues = [deque(sorted(groups[key], key=lambda item: rank(item["url"]))) for key in keys]
    selected = []
    while len(selected) < target and any(queues):
        for queue in queues:
            if queue and len(selected) < target:
                selected.append(queue.popleft())
    return selected


def screening_inventory(items: list[dict]) -> tuple[list[dict], list[dict]]:
    first = sample([item for item in items if item["financial_candidate"]], len(items))
    second = []
    for item in items:
        if item["financial_candidate"]:
            continue
        text = " ".join(str(item["raw"].get(key) or "") for key in ("title", "title_en", "summary", "summary_en"))
        if NUMBER.search(text) and SECONDARY_FINANCIAL.search(text):
            second.append(item)
    return first, second


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"Accept": "application/json", "User-Agent": "DappGo evaluation snapshot"}), timeout=30) as response:
        return response.read()


def collect(cache: Path, receipt: Path) -> dict:
    if cache.name != ".cache":
        raise ValueError("raw payload directory must be named .cache")
    if receipt.exists() or any((cache / f"{m}-pointer.json").exists() for m in ("us", "tw")):
        raise FileExistsError("collection already exists; use a new cache/receipt for another attempt")
    cache.mkdir(parents=True, exist_ok=True)
    # This directory may live outside the source tree because its .cache is a read-only symlink.
    if not (cache.parent / ".gitignore").exists():
        (cache.parent / ".gitignore").write_text(".cache/\n")
    inventory, snapshots = [], []
    for market in ("us", "tw"):
        url = f"{BASE}/api/markets/{market}/dashboard/latest.json"
        record = {"market": market, "pointer_url": url, "fetch_started_at": now()}
        try:
            pointer_raw = fetch(url)
            (cache / f"{market}-pointer.json").write_bytes(pointer_raw)
            pointer = json.loads(pointer_raw)
            payload_url = pointer_url(market, pointer)
            record.update(pointer_sha256=digest(pointer_raw), pointer=pointer, payload_url=payload_url)
            raw = fetch(payload_url)
            (cache / f"{market}-payload.json").write_bytes(raw)
            record.update(payload_sha256=digest(raw), payload_bytes=len(raw))
            payload = validate_payload(raw, pointer)
            rows = stories(market, payload)
            inventory.extend(rows)
            record.update(status="collected", pointer_sha256=digest(pointer_raw), pointer=pointer,
                          payload_url=payload_url, payload_sha256=digest(raw), payload_bytes=len(raw),
                          unique_stories=len(rows), ticker_count=len(payload["ticker_data"]),
                          financial_candidates=sum(row["financial_candidate"] for row in rows),
                          validation="same-market immutable path/hash-prefix; logical data_hash matches pointer; separate byte SHA-256")
        except Exception as exc:
            record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        record["fetch_finished_at"] = now()
        snapshots.append(record)
    (cache / "inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    result = {"snapshots": snapshots, "seed": SEED, "total_unique_stories": len(inventory)}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.cache, args.receipt), indent=2))
