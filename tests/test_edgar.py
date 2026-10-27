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


def synthetic_client(tmp_path: Path, facts: dict) -> EdgarClient:
    tmp_path.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / "company_tickers.json", tmp_path / "company_tickers.json")
    (tmp_path / "companyfacts-CIK0001326801.json").write_text(
        json.dumps({"entityName": "Synthetic Meta", "facts": facts}),
        encoding="utf-8",
    )
    return EdgarClient(tmp_path)


def test_quarter_selection_rejects_ytd(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)

    q2 = client.lookup_fact("META", "revenue", "2025Q2")
    q3 = client.lookup_fact("META", "revenue", "2025Q3")

    assert q2["start"] == "2025-04-01"
    assert q2["end"] == "2025-06-30"
    assert q2["value"] == 47_516_000_000
    assert q2["duration_days"] == 91
    assert q2["period_type"] == "quarter"
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


def test_statement_form_preferred_over_proxy(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "net_income", "FY2024")

    assert result["form"] == "10-K"
    assert result["form_fallback"] is False
    assert result["period_type"] == "annual"
    assert result["duration_days"] == 366


def test_non_statement_form_is_explicit_fallback(tmp_path: Path) -> None:
    client = synthetic_client(
        tmp_path,
        {
            "us-gaap": {
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2024-01-01",
                                "end": "2024-12-31",
                                "val": 10,
                                "accn": "0000000-24-000001",
                                "form": "PRE 14C",
                                "filed": "2025-01-01",
                            }
                        ]
                    }
                }
            }
        },
    )

    result = client.lookup_fact("META", "net_income", "FY2024")

    assert result["form"] == "PRE 14C"
    assert result["form_fallback"] is True


def test_q4_is_derived_for_additive_flow(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "revenue", "2025Q4")

    assert result["derived"] is True
    assert result["period_type"] == "quarter"
    assert result["derivation"] == "FY2025 - 9M YTD"
    assert result["value"] == result["components"][0]["value"] - result["components"][1]["value"]


def test_latest_flow_prefers_newest_derived_quarter(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "capex", "latest")

    assert result["derived"] is True
    assert result["start"] == "2026-07-01"
    assert result["end"] == "2026-09-30"
    assert result["duration_days"] == 92
    assert result["period_type"] == "quarter"
    assert result["value"] == 83_055_000_000 - 49_113_000_000


def test_ytd_is_derived_for_requested_quarter(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "capex", "2025Q2")

    assert result["derived"] is True
    assert result["value"] == 16_538_000_000
    assert result["start"] == "2025-04-01"
    assert result["end"] == "2025-06-30"
    assert [component["period_type"] for component in result["components"]] == [
        "ytd",
        "quarter",
    ]


def test_non_additive_q4_returns_structured_error(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "eps_diluted", "2024Q4")

    assert result["error"] == "not_additive_cannot_derive"


def test_non_calendar_fiscal_dates_use_frame_or_end_date(tmp_path: Path) -> None:
    client = synthetic_client(
        tmp_path,
        {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "start": "2024-07-01",
                                "end": "2024-09-30",
                                "val": 20,
                                "accn": "0000000-24-000001",
                                "form": "10-Q",
                                "filed": "2024-11-01",
                                "frame": "CY2024Q3",
                            },
                            {
                                "start": "2024-07-01",
                                "end": "2024-12-31",
                                "val": 45,
                                "accn": "0000000-25-000001",
                                "form": "10-Q",
                                "filed": "2025-02-01",
                                "frame": "CY2024Q4",
                            },
                            {
                                "start": "2024-07-01",
                                "end": "2025-03-31",
                                "val": 70,
                                "accn": "0000000-25-000002",
                                "form": "10-Q",
                                "filed": "2025-05-01",
                                "frame": "CY2025Q1",
                            },
                            {
                                "start": "2024-07-01",
                                "end": "2025-06-30",
                                "val": 100,
                                "accn": "0000000-25-000003",
                                "form": "10-K",
                                "filed": "2025-08-01",
                                "fy": 2025,
                                "fp": "FY",
                            },
                        ]
                    }
                }
            }
        },
    )

    result = client.lookup_fact("META", "revenue", "2025Q1")

    assert result["derived"] is True
    assert result["value"] == 25
    assert result["start"] == "2025-01-01"
    assert result["end"] == "2025-03-31"
    assert result["period_type"] == "quarter"


def test_instant_fact_has_instant_period_type(tmp_path: Path) -> None:
    client = fixture_client(tmp_path)
    result = client.lookup_fact("META", "cash", "latest")

    assert result["start"] is None
    assert result["duration_days"] is None
    assert result["period_type"] == "instant"


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
