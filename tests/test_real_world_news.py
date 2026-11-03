"""Offline collector/sampler regressions using exclusively synthetic news text."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("news_collect", ROOT / "scripts/real_world/collect.py")
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)
FIXTURE = json.loads((ROOT / "tests/fixtures/real-world-news/synthetic.json").read_text())


def test_pointer_restricts_hash_path_and_market():
    pointer = FIXTURE["pointer"]
    assert collect.pointer_url("tw", pointer).startswith("https://news.dappgo.com/api/markets/tw/dashboard/")
    for path in ("../us/dashboard/data-aaaaaaaaaaaa.json", "https://evil.test/data-aaaaaaaaaaaa.json",
                 "dashboard/data-bbbbbbbbbbbb.json", "dashboard/data-aaaaaaaaaaa.json",
                 "dashboard/data-aaaaaaaaaaaa.json?redirect=evil"):
        with pytest.raises(ValueError):
            collect.pointer_url("us", {**pointer, "data_url_v2": path})
    with pytest.raises(ValueError):
        collect.pointer_url("other", pointer)


def test_logical_hash_and_byte_hash_are_distinct_and_schema_is_checked():
    raw = json.dumps(FIXTURE["payload"]).encode()
    assert collect.digest(raw) != FIXTURE["pointer"]["hash"]
    assert collect.validate_payload(raw, FIXTURE["pointer"])["ticker_data"]
    for payload in ({}, {"ticker_data": {}}, {**FIXTURE["payload"], "data_hash": "b" * 64},
                    {**FIXTURE["payload"], "ticker_data": {"../bad": {}}}):
        with pytest.raises(ValueError):
            collect.validate_payload(json.dumps(payload).encode(), FIXTURE["pointer"])


def test_url_deduplication_and_numeric_screen_do_not_create_extra_stories():
    rows = collect.stories("us", FIXTURE["payload"])
    assert len(rows) == 4
    by_url = {row["url"]: row for row in rows}
    assert by_url["https://example.test/revenue"]["tickers"] == ["ALSO", "FAKE"]
    assert not by_url["https://example.test/price"]["financial_candidate"]
    first, second = collect.screening_inventory(rows)
    assert any(row["url"].endswith("revenue") for row in first)
    assert any(row["url"].endswith("eps") for row in second)


def test_sampling_is_seeded_stratified_and_permutation_invariant():
    rows = [{"market": "us", "outlet": outlet, "ticker": "SYN", "url": f"https://example.test/{outlet}/{n}"}
            for outlet in ("a", "b") for n in range(9)]
    selected = collect.sample(rows, 5)
    assert selected == collect.sample(list(reversed(rows)), 5)
    assert len({row["outlet"] for row in selected[:2]}) == 2
    assert selected != collect.sample(rows, 5, seed="another-frozen-seed")
    assert len(collect.sample(rows, 100)) == len(rows)


def test_collector_retains_hashes_without_publishing_feed_text(tmp_path, monkeypatch):
    raw_pointer = json.dumps(FIXTURE["pointer"]).encode()
    raw_payload = json.dumps(FIXTURE["payload"]).encode()
    monkeypatch.setattr(collect, "fetch", lambda url: raw_pointer if url.endswith("latest.json") else raw_payload)
    receipt = tmp_path / "evidence/collection.json"
    cache = tmp_path / ".cache"
    collect.collect(cache, receipt)
    text = receipt.read_text()
    assert "Synthetic revenue" not in text
    assert collect.digest(raw_payload) in text
    assert (cache / "us-payload.json").read_bytes() == raw_payload
    with pytest.raises(FileExistsError):
        collect.collect(cache, receipt)
