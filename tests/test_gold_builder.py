from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_gold_builder():
    path = ROOT / "eval" / "build_gold.py"
    spec = importlib.util.spec_from_file_location("standalone_build_gold", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_gold_builder_works_on_tiny_raw_fixture(tmp_path: Path) -> None:
    builder = load_gold_builder()
    cache = tmp_path / "cache"
    cache.mkdir()
    shutil.copyfile(ROOT / "tests/fixtures/company_tickers.json", cache / "company_tickers.json")
    shutil.copyfile(
        ROOT / "tests/fixtures/companyfacts-META-trimmed.json",
        cache / "companyfacts-CIK0001326801.json",
    )
    claims = {
        "claims": [
            {
                "id": "T01",
                "split": "dev",
                "category": "exact_value_true",
                "claim": "Meta's Q1 2022 revenue was $27.9 billion.",
                "spec": {
                    "kind": "value",
                    "ticker": "META",
                    "metric": "revenue",
                    "period": "2022Q1",
                    "stated": 27.9,
                    "scale": "billion",
                    "precision": 0.1,
                    "comparator": "eq",
                },
                "gold_verdict": "supported",
                "gold_note": "",
            }
        ]
    }
    claims_path = tmp_path / "claims.yaml"
    claims_path.write_text(json.dumps(claims), encoding="utf-8")
    result = builder.build_dataset(
        claims_path,
        cache_dir=cache,
        jsonl_path=tmp_path / "claims.jsonl",
        facts_path=tmp_path / "gold_facts.json",
        review_path=tmp_path / "GOLD_REVIEW.md",
        strict=False,
    )
    assert result["disagreements"] == []
    generated = json.loads((tmp_path / "gold_facts.json").read_text())
    fact = generated["claims"][0]["facts"][0]
    assert fact["value"] == 27908000000
    assert fact["concept"] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert fact["accn"]
    assert len(fact["source_sha256"]) == 64
    assert "T01" in (tmp_path / "GOLD_REVIEW.md").read_text()


def test_fiscal_quarter_spec_resolves_sec_fy_fp_fields(tmp_path: Path) -> None:
    builder = load_gold_builder()
    cache = tmp_path / "cache"
    cache.mkdir()
    shutil.copyfile(ROOT / "tests/fixtures/company_tickers.json", cache / "company_tickers.json")
    shutil.copyfile(
        ROOT / "tests/fixtures/companyfacts-META-trimmed.json",
        cache / "companyfacts-CIK0001326801.json",
    )
    ticker_map = builder._load_ticker_map(cache)
    snapshot = builder.load_snapshot(cache, "META", ticker_map)

    result = builder.evaluate_spec(
        {
            "kind": "value",
            "ticker": "META",
            "metric": "revenue",
            "period": "FY2022Q1",
            "stated": 27.9,
            "scale": "billion",
            "precision": 0.1,
            "comparator": "eq",
        },
        {"META": snapshot},
    )

    assert result["truth"] is True
    assert result["facts"][0]["start"] == "2022-01-01"
    assert result["facts"][0]["end"] == "2022-03-31"


def test_dataset_split_is_stratified() -> None:
    builder = load_gold_builder()
    claims = builder.load_claims()
    by_category: dict[str, list[dict[str, object]]] = {}
    for claim in claims:
        by_category.setdefault(str(claim["category"]), []).append(claim)

    assert all(
        len(items) < 2 or {str(item["split"]) for item in items} == {"dev", "test"}
        for items in by_category.values()
    )
    builder.validate_claims(claims)
