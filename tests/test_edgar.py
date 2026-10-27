from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from claimcheck.edgar import EdgarClient


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_client(tmp_path: Path) -> EdgarClient:
    tmp_path.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / "company_tickers.json", tmp_path / "company_tickers.json")
    shutil.copyfile(
        FIXTURES / "companyfacts-META-trimmed.json",
        tmp_path / "companyfacts-CIK0001326801.json",
    )
    return EdgarClient(tmp_path)


def test_quarter_selection_rejects_ytd(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)

    q2 = client.lookup_fact("META", "revenue", "2025Q2")
    q3 = client.lookup_fact("META", "revenue", "2025Q3")

    assert q2["start"] == "2025-04-01"
    assert q2["end"] == "2025-06-30"
    assert q2["value"] == 47_516_000_000
    assert q3["start"] == "2025-07-01"
    assert q3["end"] == "2025-09-30"


def test_concept_fallback_uses_legacy_revenues(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "revenue", "2018Q2")

    assert result["concept"] == "Revenues"
    assert result["value"] == 13_231_000_000


def test_latest_filed_comparative_wins(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "revenue", "2024Q2")

    assert result["filed"] == "2025-07-31"
    assert result["accn"] == "0001628280-25-036791"


def test_q4_is_not_silently_computed(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "revenue", "2025Q4")

    assert result["error"] == "q4_not_directly_available"
    assert "FY2025" in result["available_periods"]


def test_unknown_ticker_is_structured(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("NOPE", "revenue", "2025Q2")

    assert result["error"] == "unknown_ticker"
    assert result["available_periods"] == []


def test_fetch_cache_records_hash_and_timestamp(tmp_path: Path) -> None:
    ticker_body = (FIXTURES / "company_tickers.json").read_bytes()
    facts_body = (FIXTURES / "companyfacts-META-trimmed.json").read_bytes()

    def fetcher(url: str) -> bytes:
        return ticker_body if url.endswith("company_tickers.json") else facts_body

    cache = EdgarClient(tmp_path, fetcher=fetcher)
    result = cache.lookup_fact("META", "revenue", "2025Q2")
    assert result["value"] == 47_516_000_000

    metadata_path = tmp_path / "companyfacts-CIK0001326801.json.meta.json"
    metadata = json.loads(metadata_path.read_text())
    assert metadata["fetched_at"]
    assert metadata["sha256"] == hashlib.sha256(facts_body).hexdigest()
