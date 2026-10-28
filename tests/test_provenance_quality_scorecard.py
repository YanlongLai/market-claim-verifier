from __future__ import annotations

import json
import shutil
from pathlib import Path

from claimcheck.checks import evaluate_verdict
from claimcheck.data_quality import build_data_quality_report
from claimcheck.edgar import EdgarClient
from claimcheck.evaluate import compute_source_scorecard, wilson_interval
from claimcheck.tools import ToolRunner


FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_client(tmp_path: Path) -> EdgarClient:
    shutil.copyfile(FIXTURES / "company_tickers.json", tmp_path / "company_tickers.json")
    shutil.copyfile(
        FIXTURES / "companyfacts-META-trimmed.json",
        tmp_path / "companyfacts-CIK0001326801.json",
    )
    return EdgarClient(tmp_path)


def test_fact_provenance_tiers_confirmations_and_derived_components(tmp_path: Path) -> None:
    client = _fixture_client(tmp_path)

    quarterly = client.lookup_fact("META", "revenue", "2025Q2")
    annual = client.lookup_fact("META", "net_income", "FY2024")
    derived = client.lookup_fact("META", "revenue", "2025Q4")

    assert quarterly["provenance"]["tier"] == "L2"
    assert quarterly["provenance"]["confirmations"] == 2
    assert quarterly["provenance"]["forms"] == ["10-Q"]
    assert annual["provenance"]["tier"] == "L1"
    assert annual["provenance"]["audited"] is True
    assert annual["provenance"]["strength"] == "high"
    assert derived["provenance"]["tier"] == "L3"
    assert derived["provenance"]["component_tiers"] == ["L1", "L2"]
    assert all("provenance" in component for component in derived["components"])
    change = ToolRunner(client).dispatch(
        "compute_change",
        {"ticker": "META", "metric": "revenue", "period": "2025Q2", "base_period": "2024Q2"},
    )
    assert change["current_fact"]["provenance"]
    assert change["base_fact"]["provenance"]
    history = client.history_rank("META", "revenue", "2025Q2")
    assert history["provenance"]["tier"] == "L2"


def test_restated_provenance_keeps_values_seen_and_low_strength(tmp_path: Path) -> None:
    shutil.copyfile(FIXTURES / "company_tickers.json", tmp_path / "company_tickers.json")
    facts = {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {
                    "USD": [
                        {
                            "start": "2024-01-01",
                            "end": "2024-03-31",
                            "val": 100,
                            "accn": "0000000-24-000001",
                            "form": "10-Q",
                            "filed": "2024-05-01",
                        },
                        {
                            "start": "2024-01-01",
                            "end": "2024-03-31",
                            "val": 110,
                            "accn": "0000000-24-000002",
                            "form": "10-Q/A",
                            "filed": "2024-08-01",
                        },
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        {
                            "start": "2024-01-01",
                            "end": "2024-03-31",
                            "val": 50,
                            "accn": "0000000-24-000003",
                            "form": "8-K",
                            "filed": "2024-05-02",
                        }
                    ]
                }
            },
        }
    }
    (tmp_path / "companyfacts-CIK0001326801.json").write_text(
        json.dumps({"cik": 1326801, "entityName": "Synthetic Meta", "facts": facts}),
        encoding="utf-8",
    )
    result = EdgarClient(tmp_path).lookup_fact("META", "revenue", "2024Q1")
    provenance = result["provenance"]
    assert provenance["restated"] is True
    assert provenance["amended"] is True
    assert provenance["strength"] == "low"
    assert {item["value"] for item in provenance["values_seen"]} == {100, 110}
    fallback = EdgarClient(tmp_path).lookup_fact("META", "net_income", "2024Q1")
    assert fallback["provenance"]["form_fallback"] is True
    assert fallback["provenance"]["strength"] == "low"


def test_data_quality_tiny_snapshot_detects_mismatch_drop_and_restatement(tmp_path: Path) -> None:
    (tmp_path / "company_tickers.json").write_text(
        json.dumps({"0": {"cik_str": 1, "ticker": "TST", "title": "Test"}}),
        encoding="utf-8",
    )
    revenue = [
        {"start": "2024-01-01", "end": "2024-03-31", "val": 10_000_000, "accn": "R1", "form": "10-Q", "filed": "2024-05-01", "fy": 2024, "fp": "Q1"},
        {"start": "2024-01-01", "end": "2024-03-31", "val": 11_000_000, "accn": "R2", "form": "10-Q/A", "filed": "2024-08-01", "fy": 2024, "fp": "Q1"},
        {"start": "2024-04-01", "end": "2024-06-30", "val": 20_000_000, "accn": "R3", "form": "10-Q", "filed": "2024-08-01", "fy": 2024, "fp": "Q2"},
        {"start": "2024-07-01", "end": "2024-09-30", "val": 30_000_000, "accn": "R4", "form": "10-Q", "filed": "2024-11-01", "fy": 2024, "fp": "Q3"},
        {"start": "2024-10-01", "end": "2024-12-31", "val": 40_000_000, "accn": "R5", "form": "10-Q", "filed": "2025-02-01", "fy": 2024, "fp": "Q4"},
        {"start": "2024-01-01", "end": "2024-12-31", "val": 90_000_000, "accn": "R6", "form": "10-K", "filed": "2025-02-01", "fy": 2024, "fp": "FY"},
    ]
    net_income = [
        {"start": "2024-01-01", "end": "2024-03-31", "val": 10_000_000, "accn": "N1", "form": "10-Q", "filed": "2024-05-01", "fy": 2024, "fp": "Q1"},
        {"start": "2024-01-01", "end": "2024-06-30", "val": 20_000_000, "accn": "N2", "form": "10-Q", "filed": "2024-08-01", "fy": 2024, "fp": "Q2"},
        {"start": "2024-01-01", "end": "2024-09-30", "val": 15_000_000, "accn": "N3", "form": "10-Q", "filed": "2024-11-01", "fy": 2024, "fp": "Q3"},
    ]
    facts = {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": revenue}},
            "NetIncomeLoss": {"units": {"USD": net_income}},
        }
    }
    (tmp_path / "companyfacts-CIK0000000001.json").write_text(
        json.dumps({"cik": 1, "entityName": "Test", "facts": facts}),
        encoding="utf-8",
    )
    capex = [
        {"start": "2024-01-01", "end": "2024-03-31", "val": 5_000_000, "accn": "C1", "form": "10-Q", "filed": "2024-05-01", "fy": 2024, "fp": "Q1"},
        {"start": "2024-01-01", "end": "2024-06-30", "val": 12_000_000, "accn": "C2", "form": "10-Q", "filed": "2024-08-01", "fy": 2024, "fp": "Q2"},
        {"start": "2024-01-01", "end": "2024-09-30", "val": 9_000_000, "accn": "C3", "form": "10-Q", "filed": "2024-11-01", "fy": 2024, "fp": "Q3"},
    ]
    facts["us-gaap"]["PaymentsToAcquirePropertyPlantAndEquipment"] = {"units": {"USD": capex}}
    (tmp_path / "companyfacts-CIK0000000001.json").write_text(
        json.dumps({"cik": 1, "entityName": "Test", "facts": facts}),
        encoding="utf-8",
    )
    report = build_data_quality_report(tmp_path)
    metrics = report["issuers"][0]["metrics"]
    assert metrics["revenue"]["annual_sum_vs_annual"]["anomalies"]
    # Income can fall year-to-date after a loss quarter, so only non-decreasing metrics are checked.
    assert not metrics["net_income"]["ytd_monotonicity"]["anomalies"]
    assert metrics["capex"]["ytd_monotonicity"]["anomalies"]
    assert metrics["revenue"]["restatements"]["count"] == 1
    assert metrics["revenue"]["restatements"]["material"] == 1
    assert "R1" in metrics["revenue"]["restatements"]["examples"][0]["accessions"]


def test_evidence_summary_strength_and_restatement_flag() -> None:
    class Runner:
        evidence = {
            "E1": {
                "value": 100,
                "ticker": "META",
                "metric": "revenue",
                "concept": "Revenue",
                "start": "2024-01-01",
                "end": "2024-03-31",
                "period": "2024Q1",
                "period_type": "quarter",
                "provenance": {
                    "tier": "L1",
                    "audited": True,
                    "confirmations": 3,
                    "forms": ["10-K"],
                    "first_filed": "2024-01-01",
                    "latest_filed": "2025-01-01",
                    "restated": True,
                    "values_seen": [{"value": 99, "accn": ["A1"]}, {"value": 100, "accn": ["A2"]}],
                    "amended": False,
                    "strength": "low",
                },
            }
        }
        evidence_kind = {"E1": "lookup_fact"}

    sub_claim = {
        "text": "Revenue was $100",
        "stated_text": "$100",
        "claim_type": "value",
        "comparator": "eq",
        "stated_value": 100,
        "evidence_ids": ["E1"],
        "interpretations": [],
        "verdict": "supported",
        "note": "",
        "model_found_value": 100,
    }
    checks, verdict = evaluate_verdict([sub_claim], Runner())
    assert verdict == "supported"
    assert checks[0]["evidence_strength"] == "low"
    assert checks[0]["evidence_summary"] == "Evidence: audited 10-K, confirmed in 3 filings, restated"
    assert checks[0]["restated_evidence"] is True
    assert "restated_evidence" in checks[0]["flags"]


def test_source_scorecard_uses_wilson_ci_and_suppresses_small_domains() -> None:
    claims = [
        {
            "id": str(index),
            "source_tier": "primary",
            "source_domain": "example.com" if index < 20 else "small.example",
            "gold_verdict": "supported" if index < 10 else "contradicted",
        }
        for index in range(21)
    ]
    results = [
        {
            "id": str(index),
            "system": "agent@meta",
            "status": "completed",
            "verdict": "supported" if index < 10 else "contradicted",
            "evidence_strength": "high",
        }
        for index in range(21)
    ]
    scorecard = compute_source_scorecard(claims, results, systems=("agent@meta",))
    assert scorecard["source_reliability"]["by_tier"]["primary"]["n"] == 21
    assert scorecard["source_reliability"]["by_domain"]["example.com"]["n"] == 20
    assert "small.example" in scorecard["source_reliability"]["suppressed_domains"]
    assert scorecard["system_accuracy_by_source_tier"]["agent@meta"]["primary"]["accuracy"] == 1.0
    assert scorecard["evidence_strength"]["by_agent_system"]["agent@meta"]["distribution"]["high"]["accuracy"] == 1.0
    ci = scorecard["source_reliability"]["by_tier"]["primary"]["wilson_95_ci"]["supported"]
    assert (ci["lower"], ci["upper"]) == wilson_interval(10, 21)


def test_registry_and_data_quality_figure_are_registered() -> None:
    registry = Path("sources/registry.yaml").read_text(encoding="utf-8")
    assert "sec-edgar-companyfacts" in registry
    assert "primary:" in registry and "major_press:" in registry
    assert 'fair_access_rate_limit: "10 req/s"' in registry
    figures = json.loads(Path("docs/figures/figures.json").read_text(encoding="utf-8"))
    entry = next(item for item in figures["figures"] if item["id"] == "data-quality")
    assert entry["generator"] == "make_data_quality"
    assert Path("docs/figures/data-quality.svg").is_file()


def test_fiscal_labels_come_from_period_dates_not_filing_metadata() -> None:
    from claimcheck.fiscal import fiscal_label, normalize_fiscal_labels

    # Oracle-like May year-end; the later filing tags its own quarter with the wrong fiscal year.
    document = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"start": "2024-06-01", "end": "2025-05-31", "val": 57, "form": "10-K", "fy": 2025, "fp": "FY"},
                            {"start": "2025-06-01", "end": "2026-05-31", "val": 67, "form": "10-K", "fy": 2026, "fp": "FY"},
                            {"start": "2026-06-01", "end": "2026-08-31", "val": 19, "form": "10-Q", "fy": 2026, "fp": "Q1"},
                        ]
                    }
                }
            }
        }
    }
    normalize_fiscal_labels(document)
    quarter = document["facts"]["us-gaap"]["Revenues"]["units"]["USD"][2]
    assert (quarter["fy"], quarter["fp"]) == (2027, "Q1")
    assert (quarter["filing_fy"], quarter["filing_fp"]) == (2026, "Q1")
    # A 52/53-week year ending in the first days of January belongs to the prior calendar year (J&J).
    from datetime import date

    ends = [date(2010, 1, 3), date(2011, 1, 2)]
    assert fiscal_label(date(2011, 1, 2), ends) == (2010, 4)
    assert fiscal_label(date(2010, 4, 4), ends) == (2010, 1)


def test_quarter_tagged_with_annual_amount_is_excluded(tmp_path: Path) -> None:
    (tmp_path / "company_tickers.json").write_text(
        json.dumps({"0": {"cik_str": 1341439, "ticker": "ORCL", "title": "Oracle"}}),
        encoding="utf-8",
    )
    revenue = [
        {"start": "2017-06-01", "end": "2018-05-31", "val": 39_383, "accn": "K", "form": "10-K", "filed": "2018-06-21", "fy": 2018, "fp": "FY"},
        {"start": "2017-06-01", "end": "2018-02-28", "val": 28_369, "accn": "Q3", "form": "10-Q", "filed": "2018-03-12", "fy": 2018, "fp": "Q3"},
        # Real Oracle FY2020 10-K tagging error: the FY2018 annual amount on a three-month period.
        {"start": "2018-03-01", "end": "2018-05-31", "val": 39_383, "accn": "BAD", "form": "10-K", "filed": "2020-06-22", "fy": 2020, "fp": "FY"},
    ]
    (tmp_path / "companyfacts-CIK0001341439.json").write_text(
        json.dumps({"cik": 1341439, "entityName": "Oracle", "facts": {"us-gaap": {"Revenues": {"units": {"USD": revenue}}}}}),
        encoding="utf-8",
    )
    result = EdgarClient(tmp_path).lookup_fact("ORCL", "revenue", "FY2018Q4")
    assert result["value"] == 39_383 - 28_369
    assert result["derived"] is True
    assert [item["accn"] for item in result["excluded_facts"]] == ["BAD"]
