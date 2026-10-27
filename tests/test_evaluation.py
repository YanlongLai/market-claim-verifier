from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from claimcheck.evaluate import (
    compute_metrics,
    load_claims,
    report_evaluation,
    run_evaluation,
    single_shot_request,
)


def verdict_payload(verdict: str = "supported") -> dict[str, Any]:
    return {
        "verdict": verdict,
        "summary": "fake verdict",
        "sub_claims": [],
    }


class FakeResponses:
    def __init__(self, verdict: str = "supported") -> None:
        self.calls: list[dict[str, Any]] = []
        self.verdict = verdict

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "status": "completed",
            "output_text": json.dumps(verdict_payload(self.verdict)),
            "usage": {
                "input_tokens": 100,
                "output_tokens": 20,
                "input_tokens_details": {"cached_tokens": 0},
            },
        }


class FakeClient:
    def __init__(self, verdict: str = "supported") -> None:
        self.responses = FakeResponses(verdict)


def one_claim() -> list[dict[str, Any]]:
    return [
        {
            "id": "C01",
            "split": "dev",
            "category": "exact_value_true",
            "claim": "Meta revenue was $47.5B.",
            "gold_verdict": "supported",
        }
    ]


def test_dataset_validation_has_30_items_and_required_mix() -> None:
    claims = load_claims()
    assert len(claims) == 30
    assert [claim["id"] for claim in claims] == [f"C{number:02d}" for number in range(1, 31)]
    assert sum(claim["split"] == "dev" for claim in claims) == 20
    assert sum(claim["split"] == "test" for claim in claims) == 10
    assert {claim["gold_verdict"] for claim in claims} == {
        "supported",
        "contradicted",
        "insufficient_evidence",
    }


def test_single_shot_request_has_no_tools() -> None:
    request = single_shot_request("Meta revenue was $47.5B.", "muse-spark-1.3", today="2026-10-27")
    assert "tools" not in request
    assert "parallel_tool_calls" not in request
    assert request["text"]["format"]["name"] == "verdict"
    assert "2026-10-27" in request["instructions"]


def test_single_shot_run_uses_one_no_tool_call(tmp_path: Path) -> None:
    client = FakeClient()
    out = tmp_path / "eval"
    run_evaluation(
        one_claim(),
        systems=("single_shot",),
        out_dir=out,
        client=client,
        budget_usd=1.0,
    )
    assert len(client.responses.calls) == 1
    assert "tools" not in client.responses.calls[0]
    result = json.loads((out / "C01--single_shot.json").read_text())
    assert result["status"] == "completed"
    assert result["verdict"] == "supported"


def test_resume_skips_completed_pair(tmp_path: Path) -> None:
    out = tmp_path / "eval"
    first = FakeClient()
    first_manifest = run_evaluation(
        one_claim(),
        systems=("single_shot",),
        out_dir=out,
        client=first,
        budget_usd=1.0,
    )
    assert first_manifest["executed_pairs"] == 1

    second = FakeClient()
    second_manifest = run_evaluation(
        one_claim(),
        systems=("single_shot",),
        out_dir=out,
        client=second,
        budget_usd=1.0,
    )
    assert second.responses.calls == []
    assert second_manifest["skipped_pairs"] == 1
    assert second_manifest["executed_pairs"] == 0


def test_budget_stop_is_recorded_without_call(tmp_path: Path) -> None:
    client = FakeClient()
    out = tmp_path / "eval"
    manifest = run_evaluation(
        one_claim(),
        systems=("single_shot",),
        out_dir=out,
        client=client,
        budget_usd=0.0,
    )
    assert client.responses.calls == []
    assert manifest["budget_stop"]["id"] == "C01"
    result = json.loads((out / "C01--single_shot.json").read_text())
    assert result["status"] == "budget_stopped"
    assert result["error"]["category"] == "budget_refused"


def test_metrics_math_hand_computed_example() -> None:
    claims = [
        {"id": "A", "split": "dev", "gold_verdict": "supported"},
        {"id": "B", "split": "dev", "gold_verdict": "contradicted"},
        {"id": "C", "split": "dev", "gold_verdict": "insufficient_evidence"},
        {"id": "D", "split": "dev", "gold_verdict": "supported"},
    ]
    results = [
        {"id": "A", "split": "dev", "system": "agent", "status": "completed", "verdict": "supported", "latency_ms": 10, "cost_usd": 0.1},
        {"id": "B", "split": "dev", "system": "agent", "status": "completed", "verdict": "supported", "latency_ms": 20, "cost_usd": 0.2},
        {"id": "C", "split": "dev", "system": "agent", "status": "completed", "verdict": "insufficient_evidence", "latency_ms": 30, "cost_usd": 0.3},
    ]
    metrics = compute_metrics(claims, results, system="agent", split="dev")
    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["false_supported_rate"] == pytest.approx(0.5)
    assert metrics["insufficient_rate"] == pytest.approx(0.25)
    assert metrics["per_gold_class"]["supported"]["recall"] == pytest.approx(0.5)
    assert metrics["per_gold_class"]["contradicted"]["precision"] == 0.0
    assert metrics["latency_ms"]["p50"] == pytest.approx(20.0)
    assert metrics["cost_usd"]["total"] == pytest.approx(0.6)


def test_report_writes_summary_and_markdown(tmp_path: Path) -> None:
    claims_path = tmp_path / "claims.jsonl"
    claims_path.write_text(
        "\n".join(json.dumps(item) for item in one_claim()) + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "eval"
    run_evaluation(
        one_claim(),
        systems=("single_shot",),
        out_dir=out,
        client=FakeClient(),
        budget_usd=1.0,
    )
    summary = report_evaluation(out, claims_path=claims_path)
    assert summary["result_count"] == 1
    assert (out / "summary.json").is_file()
    report = (out / "REPORT.md").read_text()
    assert "Per-claim results" in report
    assert "No significance claims" in report
