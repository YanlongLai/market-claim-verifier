from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from claimcheck.agent import SUB_CLAIM_SCHEMA, VERDICT_SCHEMA, verify_claim
from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_sub_claim, evaluate_verdict
from claimcheck.edgar import EdgarClient
from claimcheck.numbers import infer_comparator
from claimcheck.trace import TraceRecorder
from claimcheck.tools import ToolRunner


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("stated_text", "sub_claim_text", "expected"),
    [
        ("$1.3 billion", "Tesla's Q3 2025 net income was $1.3 billion.", "eq"),
        ("$281.6 billion", "Microsoft closed fiscal 2025 with $281.6 billion.", "eq"),
        ("$47.4 billion", "Meta's Q2 2025 revenue was $47.4 billion.", "eq"),
        ("$10 billion", "revenue was around $10 billion.", "approx"),
        ("about $1.4 billion", "Tesla net income was about $1.4 billion.", "approx"),
        ("around $10 billion", "revenue was around $10 billion.", "approx"),
        ("roughly $10 billion", "revenue was roughly $10 billion.", "approx"),
        ("approximately $10 billion", "revenue was approximately $10 billion.", "approx"),
        ("nearly $10 billion", "revenue was nearly $10 billion.", "approx"),
        ("almost $10 billion", "revenue was almost $10 billion.", "approx"),
        ("close to $10 billion", "revenue was close to $10 billion.", "approx"),
        ("~$10 billion", "revenue was ~$10 billion.", "approx"),
        ("topped $100 billion", "revenue topped $100 billion.", "gt"),
        ("exceeded $100 billion", "revenue exceeded $100 billion.", "gt"),
        ("above $100 billion", "revenue was above $100 billion.", "gt"),
        ("more than $100 billion", "revenue was more than $100 billion.", "gt"),
        ("over $100 billion", "revenue was over $100 billion.", "gt"),
        ("at least $100 billion", "revenue was at least $100 billion.", "gte"),
        ("no less than $100 billion", "revenue was no less than $100 billion.", "gte"),
        ("below $100 billion", "revenue was below $100 billion.", "lt"),
        ("under $100 billion", "revenue was under $100 billion.", "lt"),
        ("less than $100 billion", "revenue was less than $100 billion.", "lt"),
        ("at most $100 billion", "revenue was at most $100 billion.", "lte"),
        ("no more than $100 billion", "revenue was no more than $100 billion.", "lte"),
        ("up to $100 billion", "revenue was up to $100 billion.", "lte"),
    ],
)
def test_comparator_wording_table(
    stated_text: str, sub_claim_text: str, expected: str
) -> None:
    assert infer_comparator(stated_text, sub_claim_text) == expected


def test_comparator_uses_original_claim_sentence() -> None:
    assert (
        infer_comparator(
            "Tesla's Q3 2025 net income was $1.3 billion.",
            "Tesla's Q3 2025 net income was $1.3 billion.",
            "Tesla's Q3 2025 net income was about $1.3 billion.",
        )
        == "approx"
    )


def _fixture_client(tmp_path: Path) -> EdgarClient:
    cache = tmp_path / "cache"
    cache.mkdir()
    shutil.copyfile(FIXTURES / "company_tickers.json", cache / "company_tickers.json")
    for ticker, cik in (
        ("MSFT", "0000789019"),
        ("AAPL", "0000320193"),
        ("NVDA", "0001045810"),
    ):
        shutil.copyfile(
            FIXTURES / f"companyfacts-{ticker}-trimmed.json",
            cache / f"companyfacts-CIK{cik}.json",
        )
    return EdgarClient(cache)


@pytest.mark.parametrize(
    ("ticker", "fiscal_period", "fiscal_value", "calendar_period", "calendar_value"),
    [
        ("MSFT", "FY2025Q4", 76_441_000_000, "2025Q4", 81_273_000_000),
        ("AAPL", "FY2025Q4", 102_466_000_000, "2025Q4", 143_756_000_000),
        ("NVDA", "FY2025Q3", 35_082_000_000, "2025Q3", 57_006_000_000),
    ],
)
def test_fiscal_and_calendar_period_lookups(
    tmp_path: Path,
    ticker: str,
    fiscal_period: str,
    fiscal_value: int,
    calendar_period: str,
    calendar_value: int,
) -> None:
    runner = ToolRunner(_fixture_client(tmp_path))
    fiscal = runner.dispatch(
        "lookup_fact", {"ticker": ticker, "metric": "revenue", "period": fiscal_period}
    )
    calendar = runner.dispatch(
        "lookup_fact", {"ticker": ticker, "metric": "revenue", "period": calendar_period}
    )

    assert fiscal["value"] == fiscal_value
    assert fiscal["period_basis"] == "fiscal"
    assert calendar["value"] == calendar_value
    assert calendar["period_basis"] == "calendar"


def _interpretation_runner() -> SimpleNamespace:
    return SimpleNamespace(
        evidence={
            "E1": {
                "ticker": "MSFT",
                "metric": "revenue",
                "period": "2025Q4",
                "period_basis": "calendar",
                "period_type": "quarter",
                "value": 81.273e9,
            },
            "E2": {
                "ticker": "MSFT",
                "metric": "revenue",
                "period": "FY2025Q4",
                "period_basis": "fiscal",
                "period_type": "quarter",
                "value": 76.441e9,
            },
            "E3": {
                "ticker": "MSFT",
                "metric": "revenue",
                "period": "FY2025Q4",
                "period_basis": "fiscal",
                "period_type": "quarter",
                "value": 281.724e9,
            },
        },
        evidence_kind={"E1": "lookup_fact", "E2": "lookup_fact", "E3": "lookup_fact"},
    )


def _period_claim(**overrides: Any) -> dict[str, Any]:
    value = {
        "text": "Microsoft's fourth-quarter 2025 revenue was $281.7 billion.",
        "stated_text": "Microsoft's fourth-quarter 2025 revenue was $281.7 billion.",
        "claim_type": "value",
        "comparator": "eq",
        "stated_value": 281.7e9,
        "evidence_ids": ["E1", "E2"],
        "interpretations": ["E1", "E2"],
        "verdict": "contradicted",
        "model_found_value": 81.273e9,
        "note": "both readings",
    }
    value.update(overrides)
    return value


def test_period_interpretations_all_contradicted() -> None:
    check = evaluate_sub_claim(_period_claim(), _interpretation_runner())

    assert check["program_verdict"] == "contradicted"
    assert check["period_ambiguous"] is False
    assert "8.1273e+10" in check["reason"]
    assert "7.6441e+10" in check["reason"]


def test_period_interpretations_mixed_fail_closed_as_ambiguous() -> None:
    check = evaluate_sub_claim(
        _period_claim(evidence_ids=["E1", "E3"], interpretations=["E1", "E3"]),
        _interpretation_runner(),
    )

    assert check["program_verdict"] == "unchecked"
    assert check["period_ambiguous"] is True
    assert "period_ambiguous" in check["reason"]
    assert "8.1273e+10" in check["reason"]
    assert "2.81724e+11" in check["reason"]


def test_c22_replay_is_contradicted_with_both_quarter_readings() -> None:
    checks, verdict = evaluate_verdict(
        [_period_claim()],
        _interpretation_runner(),
    )

    assert checks[0]["program_verdict"] == "contradicted"
    assert verdict == "contradicted"


def test_c06_recorded_model_output_is_corrected_to_eq() -> None:
    runner = SimpleNamespace(
        evidence={"E1": {"value": 1.373e9}}, evidence_kind={"E1": "lookup_fact"}
    )
    claim = {
        "text": "Tesla's Q3 2025 net income was $1.3 billion.",
        "stated_text": "Tesla's Q3 2025 net income was $1.3 billion.",
        "claim_type": "value",
        "comparator": "approx",
        "stated_value": 1.3e9,
        "evidence_ids": ["E1"],
        "interpretations": [],
        "verdict": "supported",
        "model_found_value": 1.373e9,
        "note": "recorded C06 model output",
    }

    check = evaluate_sub_claim(claim, runner)
    assert check["program_verdict"] == "contradicted"
    assert check["comparator"] == "eq"
    assert check["model_comparator"] == "approx"
    assert check["comparator_corrected"] is True


def test_verdict_schema_requires_interpretations() -> None:
    assert "interpretations" in SUB_CLAIM_SCHEMA["required"]
    assert "interpretations" in VERDICT_SCHEMA["properties"]["sub_claims"]["items"]["required"]


@dataclass
class _Usage:
    input_tokens: int = 20
    output_tokens: int = 10
    input_tokens_details: Any = None

    def __post_init__(self) -> None:
        if self.input_tokens_details is None:
            self.input_tokens_details = {"cached_tokens": 0}


@dataclass
class _Call:
    name: str
    arguments: str
    call_id: str
    type: str = "function_call"


class _Response:
    def __init__(
        self,
        response_id: str,
        *,
        output: list[Any] | None = None,
        output_text: str | None = None,
    ) -> None:
        self.id = response_id
        self.output = output or []
        self.output_text = output_text
        self.usage = _Usage()
        self.status = None
        self.incomplete_details = None

    def model_dump(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "output": [getattr(item, "__dict__", item) for item in self.output],
            "output_text": self.output_text,
            "usage": self.usage.__dict__,
            "status": self.status,
            "incomplete_details": self.incomplete_details,
        }


class _ExpiredResponseError(RuntimeError):
    status_code = 400


class _FallbackResponses:
    def __init__(self, final: dict[str, Any]) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses = [
            _Response(
                "r1",
                output=[
                    _Call(
                        "lookup_fact",
                        json.dumps(
                            {"ticker": "META", "metric": "revenue", "period": "2025Q2"}
                        ),
                        "call-1",
                    )
                ],
            ),
            _ExpiredResponseError("400 referenced response not found or expired"),
            _Response("r2"),
            _Response("r3", output_text=json.dumps(final)),
        ]

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        next_response = self.responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


class _FallbackClient:
    def __init__(self, final: dict[str, Any]) -> None:
        self.responses = _FallbackResponses(final)


class _MetaReplayEdgar:
    def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, Any]:
        return {"ticker": ticker, "metric": metric, "period": period, "value": 47.516e9}

    def list_periods(self, ticker: str, metric: str) -> list[str]:
        return []


def test_meta_previous_response_fallback_replays_full_history(tmp_path: Path) -> None:
    final = {
        "verdict": "supported",
        "summary": "ok",
        "sub_claims": [
            {
                "text": "Meta Q2 2025 revenue was $47.5B",
                "stated_text": "$47.5B",
                "claim_type": "value",
                "comparator": "eq",
                "stated_value": 47.5e9,
                "evidence_ids": ["E1"],
                "interpretations": [],
                "verdict": "supported",
                "note": "ok",
                "model_found_value": 47.516e9,
            }
        ],
    }
    client = _FallbackClient(final)
    trace = TraceRecorder("Meta Q2 2025 revenue was $47.5B", "muse-spark-1.3")
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        _MetaReplayEdgar(),
        Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0),
        "muse-spark-1.3",
        trace=trace,
    )

    assert result["verdict"] == "supported"
    assert len(client.responses.calls) == 4
    fallback_request = client.responses.calls[2]
    assert "previous_response_id" not in fallback_request
    assert any(item.get("role") == "user" for item in fallback_request["input"])
    assert any(item.get("type") == "function_call" for item in fallback_request["input"])
    assert any(item.get("type") == "function_call_output" for item in fallback_request["input"])
    trace_dict = trace.as_dict()
    assert trace_dict["previous_response_fallback"] is True
    assert any(
        item.get("previous_response_fallback") is True
        for item in trace_dict["requests"]
    )
