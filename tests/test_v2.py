from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

from claimcheck.budget import Ledger
from claimcheck.evaluate import (
    mcnemar_exact_pvalue,
    paired_bootstrap_ci,
    run_evaluation,
    wilson_interval,
)


ROOT = Path(__file__).parents[1]
OFFLINE_CACHE = ROOT / "tests" / "fixtures" / "sec-offline"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_generator_same_seed_is_byte_stable(tmp_path: Path) -> None:
    generator = load_module("v2_generator_test", ROOT / "eval/v2/generate.py")
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    generator.generate_claims(seed=7, target=160, cache_dir=OFFLINE_CACHE, output=first, log_path=tmp_path / "first.log")
    generator.generate_claims(seed=7, target=160, cache_dir=OFFLINE_CACHE, output=second, log_path=tmp_path / "second.log")
    assert first.read_bytes() == second.read_bytes()
    rows = [json.loads(line) for line in first.read_text().splitlines()]
    assert len(rows) == 160
    assert {row["family"] for row in rows} == set(generator.FAMILIES)
    assert all(sum(row["family"] == family for row in rows) >= 12 for family in generator.FAMILIES)


def _spec_parts(spec: dict[str, Any]) -> list[dict[str, Any]]:
    parts = [spec]
    for part in spec.get("parts", []):
        if isinstance(part, dict):
            parts.extend(_spec_parts(part))
    return parts


def test_v2_period_and_metric_constraints(tmp_path: Path) -> None:
    generator = load_module("v2_generator_constraints_test", ROOT / "eval/v2/generate.py")
    output = tmp_path / "claims.jsonl"
    generator.generate_claims(seed=11, target=160, cache_dir=OFFLINE_CACHE, output=output, log_path=tmp_path / "generate.log")
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    non_calendar = {"MSFT", "AAPL", "NVDA", "ORCL", "NKE", "CSCO", "ADBE", "COST", "WMT", "V", "CRM"}
    month = r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b"
    for row in rows:
        assert not re.search(r"\b20\d{2}-\d{2}-\d{2}\b", row["claim"])
        if row["family"] == "ambiguous_period":
            continue
        for spec in _spec_parts(row["spec"]):
            if spec.get("period") is None:
                continue
            assert spec.get("period_basis") in {"calendar", "fiscal", "month_named"}
            if spec.get("ticker") not in non_calendar:
                continue
            text = row["claim"].casefold()
            basis = spec["period_basis"]
            if basis == "fiscal":
                assert "fiscal" in text or re.search(r"\bfy\s*20\d{2}", text) or "full-year" in text or "year ended" in text
            elif basis == "calendar":
                assert "calendar" in text or re.search(month, text)
            else:
                assert "quarter ended" in text or re.search(month, text)

    assert all(
        row["spec"].get("metric") != "eps_diluted"
        for row in rows
        if row["family"] == "unit_trap"
    )
    assert all(
        row["spec"].get("metric") in generator.RECORD_METRICS
        for row in rows
        if row["family"] == "record_first"
    )


def test_ambiguous_period_gold_checks_both_readings() -> None:
    gold = load_module("v2_gold_ambiguity_test", ROOT / "eval/build_gold.py")
    cache = OFFLINE_CACHE
    ticker_map = gold._load_ticker_map(cache)
    snapshots = {
        ticker: gold.load_snapshot(cache, ticker, ticker_map)
        for ticker in ("NVDA", "MSFT")
    }
    for ticker, period, stated in (("NVDA", "FY2024Q2", 13.5), ("MSFT", "FY2024Q2", 62.0)):
        result = gold.evaluate_spec(
            {
                "kind": "ambiguous_period",
                "ticker": ticker,
                "metric": "revenue",
                "period": period,
                "period_basis": "fiscal",
                "stated": stated,
                "scale": "billion",
                "precision": 0.1,
                "comparator": "eq",
            },
            snapshots,
        )
        assert result["truth"] is None
        assert "fiscal" in result["note"] and "calendar" in result["note"]
        assert "reports" in result["note"]


def test_paraphrase_constraint_checker_accepts_synonyms_and_rejects_missing_fields() -> None:
    paraphrase = load_module("v2_paraphrase_test", ROOT / "eval/v2/paraphrase.py")
    original = "Apple's Q3 2025 revenue rose 8% year over year to $47.5B."
    accepted = "Apple reported $47,500 million of revenue in the third quarter of 2025, up 8% year over year."
    rejected = "Apple reported revenue in the third quarter of 2025."
    spec = {"ticker": "AAPL", "period": "FY2025Q3"}
    assert paraphrase.check_paraphrase_constraints(original, accepted, spec=spec)["accepted"]
    result = paraphrase.check_paraphrase_constraints(original, rejected, spec=spec)
    assert not result["accepted"]
    assert any("number" in reason for reason in result["reasons"])
    period_result = paraphrase.check_paraphrase_constraints(
        "Apple's calendar Q3 2025 revenue rose 8% year over year to $47.5B.",
        "Apple reported $47.5B of revenue in Q3 2025, up 8% year over year.",
        spec=spec,
    )
    assert not period_result["accepted"]
    assert any("period semantics: calendar" in reason for reason in period_result["reasons"])


def test_real_yaml_validation_and_statistics() -> None:
    builder = load_module("v2_build_test", ROOT / "eval/v2/build.py")
    rows = builder._real_claims(ROOT / "eval/v2/real.yaml")
    builder.validate_real_claims(rows)
    with pytest.raises(builder.BuildError):
        builder.validate_real_claims([{**rows[0], "claim": " ".join(["word"] * 26)}])
    assert wilson_interval(5, 10) == pytest.approx((0.2365930905, 0.7634069095))
    assert mcnemar_exact_pvalue({"b": 3, "c": 1}) == pytest.approx(0.625)
    assert paired_bootstrap_ci([True, False, True], [False, False, True], n_resamples=1000, seed=11) == paired_bootstrap_ci([True, False, True], [False, False, True], n_resamples=1000, seed=11)


class _FakeResponses:
    def create(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "completed",
            "output_text": json.dumps({"verdict": "supported", "summary": "ok", "sub_claims": []}),
            "usage": {"input_tokens": 100, "output_tokens": 20},
        }


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponses()


def test_concurrent_budget_reservations_never_exceed_cap(tmp_path: Path) -> None:
    claims = [
        {
            "id": f"T{i:03d}", "split": "dev", "category": "value", "claim": "x",
            "gold_verdict": "supported",
        }
        for i in range(32)
    ]
    out = tmp_path / "eval"
    run_evaluation(
        claims,
        systems=("single_shot",),
        out_dir=out,
        client=_FakeClient(),
        budget_usd=0.03,
        concurrency=8,
    )
    ledger = Ledger(out / "ledger.jsonl", budget_usd=0.03)
    assert ledger.spent_total <= 0.03 + 1e-12
    assert len(list(out.glob("T*--single_shot.json"))) == 32



def test_paraphrase_rejects_model_commentary() -> None:
    paraphrase = load_module("v2_paraphrase_commentary_test", ROOT / "eval/v2/paraphrase.py")

    original = "In full-year 2025, Tesla saw revenue increase 3% from a year earlier."
    spec = {"kind": "growth", "ticker": "TSLA", "metric": "revenue", "period": "FY2025", "direction": "up", "stated": 3}
    commentary = (
        "That claim is not accurate - Tesla's revenue did not increase 3% in full-year 2025.\n\n"
        "An accurate headline would be: Tesla's full-year 2025 revenue fell about 3%."
    )
    result = paraphrase.check_paraphrase_constraints(original, commentary, spec=spec)
    assert not result["accepted"]
    assert "not a single line" in result["reasons"]
    assert any(reason.startswith("commentary instead of paraphrase") for reason in result["reasons"])
    good = paraphrase.check_paraphrase_constraints(original, "Tesla full-year 2025 revenue increases 3% from a year earlier", spec=spec)
    assert good["accepted"], good["reasons"]
