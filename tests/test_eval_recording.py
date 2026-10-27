from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claimcheck.evaluate import report_evaluation, run_evaluation
from claimcheck.prompts import prompt_files_in_sync, prompt_registry, prompt_versions_for


class RecordingResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "status": "completed",
            "output_text": json.dumps(
                {"verdict": "supported", "summary": "recorded", "sub_claims": []}
            ),
            "usage": {
                "input_tokens": 101,
                "output_tokens": 23,
                "input_tokens_details": {"cached_tokens": 7},
                "output_tokens_details": {"reasoning_tokens": 5},
            },
        }


class RecordingClient:
    def __init__(self) -> None:
        self.responses = RecordingResponses()


def _claim() -> dict[str, str]:
    return {
        "id": "C01",
        "split": "dev",
        "category": "exact_value_true",
        "claim": "Meta revenue was $47.5B.",
        "gold_verdict": "supported",
    }


def test_single_shot_trace_and_result_record_everything(tmp_path: Path) -> None:
    client = RecordingClient()
    out = tmp_path / "eval"
    run_evaluation(
        [_claim()],
        systems=("single_shot",),
        out_dir=out,
        client=client,
        budget_usd=1.0,
        split="dev",
    )

    result = json.loads((out / "C01--single_shot.json").read_text(encoding="utf-8"))
    assert result["trace_path"].startswith("traces/")
    assert result["prompt_versions"] == prompt_versions_for("single_shot")
    assert result["tokens"] == {"input": 101, "cached": 7, "output": 23, "reasoning": 5}
    assert result["model_calls"] == 1
    assert result["tool_calls"] == 0
    assert result["started_at"].endswith("Z")
    assert result["finished_at"].endswith("Z")

    trace = json.loads((out / result["trace_path"]).read_text(encoding="utf-8"))
    request = trace["requests"][0]
    assert set(request) == {
        "request",
        "reservation",
        "raw_response",
        "usage",
        "cost",
        "latency_ms",
        "status",
    }
    assert set(request["request"]) >= {"instructions", "input", "text"}
    assert request["raw_response"]["output_text"]
    assert trace["tokens"] == result["tokens"]


def test_manifest_records_versions_hashes_and_ledger(tmp_path: Path) -> None:
    claims_path = tmp_path / "claims.jsonl"
    claims_path.write_text(json.dumps(_claim()) + "\n", encoding="utf-8")
    out = tmp_path / "eval"
    run_evaluation(
        [_claim()],
        systems=("single_shot",),
        out_dir=out,
        client=RecordingClient(),
        budget_usd=1.0,
        split="dev",
        claims_path=claims_path,
        cli_args=["eval", "run", "--split", "dev"],
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"].startswith("eval-")
    assert manifest["finished_at"].endswith("Z")
    assert manifest["wall_clock_s"] >= 0
    assert manifest["git_commit"]
    assert isinstance(manifest["git_dirty"], bool)
    assert manifest["python_version"]
    assert manifest["openai_version"]
    assert manifest["split"] == "dev"
    assert manifest["cli_args"] == ["eval", "run", "--split", "dev"]
    assert manifest["ledger_spend_after_usd"] >= manifest["ledger_spend_before_usd"]
    assert manifest["claims_jsonl_sha256"]
    assert set(manifest["prompt_registry"]) == set(prompt_registry())
    for entry in manifest["prompt_registry"].values():
        assert entry["text"]
        assert len(entry["sha256"]) == 64


def test_prompt_export_is_in_sync() -> None:
    in_sync, problems = prompt_files_in_sync()
    assert in_sync, problems


def test_report_contains_audit_sections(tmp_path: Path) -> None:
    claims_path = tmp_path / "claims.jsonl"
    claims_path.write_text(json.dumps(_claim()) + "\n", encoding="utf-8")
    out = tmp_path / "eval"
    run_evaluation(
        [_claim()],
        systems=("single_shot",),
        out_dir=out,
        client=RecordingClient(),
        budget_usd=1.0,
        split="dev",
        claims_path=claims_path,
    )
    report_evaluation(out, claims_path=claims_path)
    report = (out / "REPORT.md").read_text(encoding="utf-8")
    for section in (
        "Run window:",
        "Wall clock:",
        "Per-system totals",
        "Provider comparison",
        "Prompt versions",
        "Single Shot correct?",
        "tokens (i/c/o/r)",
        "Agent errors",
        "accuracy",
        "false-supported rate",
        "insufficient rate",
    ):
        assert section in report
