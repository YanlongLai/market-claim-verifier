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
DEV_EVIDENCE = (
    Path(__file__).parents[1]
    / "docs"
    / "evidence"
    / "eval-2026-10-27-r2-dev"
)
CLAIMS_JSONL = Path(__file__).parents[1] / "eval" / "claims.jsonl"


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
        ("META", "0001326801"),
        ("MSFT", "0000789019"),
        ("AAPL", "0000320193"),
        ("NVDA", "0001045810"),
        ("TSLA", "0001318605"),
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


@pytest.mark.parametrize(
    ("ticker", "expected"),
    [("TSLA", True), ("META", True), ("MSFT", False), ("AAPL", False), ("NVDA", False)],
)
def test_fiscal_equals_calendar_is_reported_on_lookup_and_compute_results(
    tmp_path: Path, ticker: str, expected: bool
) -> None:
    runner = ToolRunner(_fixture_client(tmp_path))

    lookup = runner.dispatch(
        "lookup_fact", {"ticker": ticker, "metric": "revenue", "period": "FY2025"}
    )
    change = runner.dispatch(
        "compute_change",
        {
            "ticker": ticker,
            "metric": "revenue",
            "period": "FY2025",
            "base_period": "FY2024",
        },
    )

    assert lookup["fiscal_equals_calendar"] is expected
    assert change["fiscal_equals_calendar"] is expected


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


def test_fewer_than_two_period_readings_falls_back_to_evidence_ids() -> None:
    check = evaluate_sub_claim(
        _period_claim(evidence_ids=["E1"], interpretations=["E1"]),
        _interpretation_runner(),
    )

    assert check["program_verdict"] == "contradicted"
    assert check["interpretations"] == []
    assert check["invalid_interpretations"] is False
    assert check["period_ambiguous"] is False


def test_c22_replay_is_contradicted_with_both_quarter_readings() -> None:
    checks, verdict = evaluate_verdict(
        [_period_claim()],
        _interpretation_runner(),
    )

    assert checks[0]["program_verdict"] == "contradicted"
    assert verdict == "contradicted"


def test_identical_interpretations_are_one_reading_not_period_ambiguous() -> None:
    runner = SimpleNamespace(
        evidence={
            "E1": {
                "ticker": "TSLA",
                "metric": "revenue",
                "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
                "period": "2025Q3",
                "period_basis": "calendar",
                "period_type": "quarter",
                "start": "2025-07-01",
                "end": "2025-09-30",
                "value": 28.095e9,
            },
            "E2": {
                "ticker": "TSLA",
                "metric": "revenue",
                "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
                "period": "FY2025Q3",
                "period_basis": "fiscal",
                "period_type": "quarter",
                "start": "2025-07-01",
                "end": "2025-09-30",
                "value": 28.095e9,
            },
        },
        evidence_kind={"E1": "lookup_fact", "E2": "lookup_fact"},
    )
    claim = _period_claim(
        text="Tesla's Q3 2025 revenue was $28.1 billion.",
        stated_text="$28.1 billion",
        stated_value=28.1e9,
        evidence_ids=["E1", "E2"],
        interpretations=["E1", "E2"],
    )

    check = evaluate_sub_claim(claim, runner)

    assert check["program_verdict"] == "supported"
    assert check["period_ambiguous"] is False
    assert check["interpretations"] == ["E1"]
    assert check["evidence_ids"] == ["E1"]
    assert check["deduplicated_evidence"] == ["E1", "E2"]


TESLA_DUPLICATE_TRACE = (
    Path(__file__).parents[1]
    / "docs"
    / "evidence"
    / "2026-10-27"
    / "20261028T005808Z-44ac3d76.json"
)


def test_fireworks_tesla_duplicate_compute_replay_is_contradicted() -> None:
    trace = json.loads(TESLA_DUPLICATE_TRACE.read_text(encoding="utf-8"))
    evidence: dict[str, dict[str, Any]] = {}
    evidence_kind: dict[str, str] = {}
    for call in trace["tool_calls"]:
        result = call["result"]
        evidence_id = result.get("evidence_id")
        if evidence_id:
            evidence[evidence_id] = result
            evidence_kind[evidence_id] = call["name"]
        for field in ("current_fact", "base_fact"):
            nested = result.get(field)
            if isinstance(nested, dict) and nested.get("evidence_id"):
                evidence[nested["evidence_id"]] = nested
                evidence_kind[nested["evidence_id"]] = "lookup_fact"

    checks, verdict = evaluate_verdict(
        trace["final_verdict"]["sub_claims"],
        SimpleNamespace(evidence=evidence, evidence_kind=evidence_kind),
    )

    assert verdict == "contradicted"
    assert checks[0]["program_verdict"] == "contradicted"
    assert checks[0]["actual_value"] == pytest.approx(11.567786514176793)
    assert checks[0]["evidence_ids"] == ["E3"]
    assert checks[0]["deduplicated_evidence"] == ["E3", "E6"]


def _recorded_runner(claim_id: str) -> SimpleNamespace:
    recorded = json.loads(
        (DEV_EVIDENCE / f"{claim_id}--agent@meta.json").read_text(encoding="utf-8")
    )
    trace = json.loads(
        (DEV_EVIDENCE / recorded["trace_path"]).read_text(encoding="utf-8")
    )
    evidence: dict[str, dict[str, Any]] = {}
    evidence_kind: dict[str, str] = {}
    for call in trace["tool_calls"]:
        result = call["result"]
        evidence_id = result.get("evidence_id")
        if evidence_id:
            evidence[evidence_id] = result
            evidence_kind[evidence_id] = call["name"]
        for field in ("current_fact", "base_fact"):
            nested = result.get(field)
            if isinstance(nested, dict) and nested.get("evidence_id"):
                evidence[nested["evidence_id"]] = nested
                evidence_kind[nested["evidence_id"]] = "lookup_fact"
    return SimpleNamespace(evidence=evidence, evidence_kind=evidence_kind)


def _recorded_model_sub_claims(claim_id: str) -> list[dict[str, Any]]:
    recorded = json.loads(
        (DEV_EVIDENCE / f"{claim_id}--agent@meta.json").read_text(encoding="utf-8")
    )
    fields = (
        "text",
        "stated_text",
        "claim_type",
        "comparator",
        "stated_value",
        "evidence_ids",
        "interpretations",
        "verdict",
        "note",
        "model_found_value",
    )
    return [
        {field: sub_claim[field] for field in fields}
        for sub_claim in recorded["sub_claims"]
    ]


V2_EVIDENCE = Path(__file__).parents[1] / "docs" / "evidence" / "eval-v2-2026-10-27"


def _v2_program_replay(
    tmp_path: Path, claim_id: str, ticker: str, cik: str
) -> tuple[ToolRunner, list[dict[str, Any]], dict[str, Any]]:
    recorded = json.loads(
        (V2_EVIDENCE / f"{claim_id}--agent@meta.json").read_text(encoding="utf-8")
    )
    trace = json.loads(
        (V2_EVIDENCE / recorded["trace_path"]).read_text(encoding="utf-8")
    )
    runner = ToolRunner(_fixture_client(tmp_path))
    for call in trace["tool_calls"]:
        runner.dispatch(call["name"], call["arguments"])
    fields = (
        "text",
        "stated_text",
        "claim_type",
        "comparator",
        "stated_value",
        "evidence_ids",
        "interpretations",
        "verdict",
        "note",
        "model_found_value",
    )
    sub_claims = [
        {
            **{field: sub_claim[field] for field in fields},
            "original_claim": recorded["claim"],
        }
        for sub_claim in trace["final_verdict"]["sub_claims"]
    ]
    return runner, sub_claims, recorded


@pytest.mark.parametrize(
    ("claim_id", "ticker", "cik", "period"),
    [
        ("G0235", "NVDA", "0001045810", "2024Q2"),
        ("G0240", "AAPL", "0000320193", "2023Q4"),
        ("G0249", "AAPL", "0000320193", "2023Q3"),
    ],
)
def test_v2_unlabeled_quarter_program_fetches_missing_reading(
    tmp_path: Path, claim_id: str, ticker: str, cik: str, period: str
) -> None:
    runner, sub_claims, _ = _v2_program_replay(tmp_path, claim_id, ticker, cik)

    checks, verdict = evaluate_verdict(sub_claims, runner)
    check = checks[0]

    assert verdict == "insufficient_evidence"
    assert check["program_verdict"] == "unchecked"
    assert check["period_ambiguous"] is True
    assert check["program_added_interpretation"] is True
    assert check["program_evidence_ids"] == ["P1"]
    assert check["interpretations"] == ["E2", "P1"]
    assert any(
        call.get("role") == "program"
        and call["name"] == "lookup_fact"
        and call["arguments"] == {
            "ticker": ticker,
            "metric": "net_income" if claim_id == "G0249" else "revenue",
            "period": period,
        }
        for call in runner.calls
    )


def test_labeled_fiscal_quarter_does_not_add_program_interpretation(
    tmp_path: Path,
) -> None:
    runner, sub_claims, _ = _v2_program_replay(
        tmp_path, "G0235", "NVDA", "0001045810"
    )
    sub_claims[0]["original_claim"] = (
        "NVIDIA's fiscal Q2 2024 revenue was $13.5 billion."
    )

    checks, verdict = evaluate_verdict(sub_claims, runner)

    assert verdict == "supported"
    assert checks[0]["program_verdict"] == "supported"
    assert checks[0]["program_added_interpretation"] is False
    assert not any(call.get("role") == "program" for call in runner.calls)


def test_amazon_calendar_issuer_keeps_unlabeled_quarter_supported(
    tmp_path: Path,
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    cached_snapshot = Path(".cache")
    shutil.copyfile(cached_snapshot / "company_tickers.json", cache / "company_tickers.json")
    shutil.copyfile(
        cached_snapshot / "companyfacts-CIK0001018724.json",
        cache / "companyfacts-CIK0001018724.json",
    )
    runner = ToolRunner(EdgarClient(cache))
    fact = runner.dispatch(
        "lookup_fact", {"ticker": "AMZN", "metric": "revenue", "period": "2023Q3"}
    )
    check = evaluate_sub_claim(
        {
            "text": "Amazon's Q3 2023 revenue was $143.1 billion.",
            "stated_text": "$143.1 billion",
            "claim_type": "value",
            "comparator": "eq",
            "stated_value": 143.1e9,
            "evidence_ids": [fact["evidence_id"]],
            "interpretations": [],
            "verdict": "supported",
            "model_found_value": fact["value"],
            "note": "calendar issuer",
            "original_claim": "Amazon's Q3 2023 revenue was $143.1 billion.",
        },
        runner,
    )

    assert fact["fiscal_equals_calendar"] is True
    assert check["program_verdict"] == "supported"
    assert check["program_added_interpretation"] is False
    assert not any(call.get("role") == "program" for call in runner.calls)


class _AgreeingProgramRunner:
    def __init__(self) -> None:
        self.evidence = {
            "E1": {
                "ticker": "MSFT",
                "metric": "revenue",
                "period": "FY2025Q4",
                "period_basis": "fiscal",
                "period_type": "quarter",
                "value": 100.0,
                "fiscal_equals_calendar": False,
            }
        }
        self.evidence_kind = {"E1": "lookup_fact"}
        self.calls: list[dict[str, Any]] = []

    def dispatch_program(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = {
            "ticker": "MSFT",
            "metric": "revenue",
            "period": "2025Q4",
            "period_basis": "calendar",
            "period_type": "quarter",
            "value": 100.0,
            "fiscal_equals_calendar": False,
            "evidence_id": "P1",
        }
        self.evidence["P1"] = result
        self.evidence_kind["P1"] = "lookup_fact"
        self.calls.append(
            {"name": name, "arguments": arguments, "result": result, "role": "program"}
        )
        return result


def test_program_fetched_reading_that_agrees_stays_supported() -> None:
    runner = _AgreeingProgramRunner()
    check = evaluate_sub_claim(
        {
            "text": "Microsoft's Q4 2025 revenue was $100.",
            "stated_text": "$100",
            "claim_type": "value",
            "comparator": "eq",
            "stated_value": 100.0,
            "evidence_ids": ["E1"],
            "interpretations": [],
            "verdict": "supported",
            "model_found_value": 100.0,
            "note": "both readings agree",
            "original_claim": "Microsoft's Q4 2025 revenue was $100.",
        },
        runner,
    )

    assert check["program_verdict"] == "supported"
    assert check["period_ambiguous"] is False
    assert check["program_added_interpretation"] is True
    assert check["interpretations"] == ["E1", "P1"]


def test_program_fetches_both_facts_for_missing_change_reading() -> None:
    class ReplayEdgar:
        def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, Any]:
            values = {
                "FY2024Q2": 100.0,
                "FY2023Q2": 50.0,
                "2024Q2": 150.0,
                "2023Q2": 50.0,
            }
            return {
                "ticker": ticker,
                "metric": metric,
                "period": period,
                "value": values[period],
                "period_type": "quarter",
                "fiscal_equals_calendar": False,
            }

        def list_periods(self, ticker: str, metric: str) -> list[str]:
            return []

    runner = ToolRunner(ReplayEdgar())
    change = runner.dispatch(
        "compute_change",
        {
            "ticker": "NVDA",
            "metric": "revenue",
            "period": "FY2024Q2",
            "base_period": "FY2023Q2",
        },
    )
    check = evaluate_sub_claim(
        {
            "text": "NVIDIA's Q2 2024 revenue grew 100%.",
            "stated_text": "grew 100%",
            "claim_type": "change_pct",
            "comparator": "eq",
            "stated_value": 100.0,
            "evidence_ids": [change["evidence_id"]],
            "interpretations": [],
            "verdict": "supported",
            "model_found_value": 100.0,
            "note": "fiscal reading",
            "original_claim": "NVIDIA's Q2 2024 revenue grew 100%.",
        },
        runner,
    )

    assert check["program_verdict"] == "unchecked"
    assert check["period_ambiguous"] is True
    assert check["program_added_interpretation"] is True
    assert check["interpretations"] == [change["evidence_id"], "P3"]
    assert {
        call["arguments"]["period"]
        for call in runner.calls
        if call.get("role") == "program" and call["name"] == "lookup_fact"
    } == {"2024Q2", "2023Q2"}


def _gold_by_id() -> dict[str, dict[str, Any]]:
    return {
        row["id"]: row
        for row in (
            json.loads(line)
            for line in CLAIMS_JSONL.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


@pytest.mark.parametrize("claim_id", ["C09", "C10", "C12", "C15", "C22"])
def test_recorded_invalid_interpretations_replay_to_gold(claim_id: str) -> None:
    runner = _recorded_runner(claim_id)
    checks, verdict = evaluate_verdict(
        _recorded_model_sub_claims(claim_id),
        runner,
    )
    expected = _gold_by_id()[claim_id]["gold_verdict"]

    assert verdict == expected
    assert all(check["program_verdict"] == expected for check in checks)
    assert all(check["invalid_interpretations"] is True for check in checks)
    assert all(check["period_ambiguous"] is False for check in checks)
    assert all("period_ambiguous" not in check["reason"] for check in checks)
    assert all(
        evidence_id in runner.evidence
        for check in checks
        for evidence_id in check["interpretations"]
    )


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


def test_interpretations_schema_describes_evidence_ids_without_pattern() -> None:
    item_schema = SUB_CLAIM_SCHEMA["properties"]["interpretations"]["items"]
    assert item_schema["description"] == "evidence id like E3 — never free text"
    assert "pattern" not in item_schema


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
    def __init__(
        self,
        final: dict[str, Any],
        *,
        error_message: str = "400 referenced response not found or expired",
        include_reasoning: bool = False,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        first_output: list[Any] = []
        if include_reasoning:
            first_output.append(
                {"type": "reasoning", "id": "rs_expired", "summary": []}
            )
        first_output.append(
            _Call(
                "lookup_fact",
                json.dumps(
                    {"ticker": "META", "metric": "revenue", "period": "2025Q2"}
                ),
                "call-1",
            )
        )
        self.responses = [
            _Response("r1", output=first_output),
            _ExpiredResponseError(error_message),
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
    def __init__(
        self,
        final: dict[str, Any],
        *,
        error_message: str = "400 referenced response not found or expired",
        include_reasoning: bool = False,
    ) -> None:
        self.responses = _FallbackResponses(
            final,
            error_message=error_message,
            include_reasoning=include_reasoning,
        )


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


def test_meta_reasoning_item_fallback_drops_prior_reasoning_items(tmp_path: Path) -> None:
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
    client = _FallbackClient(
        final,
        error_message="400 Referenced reasoning item 'rs_expired' was not found or has expired.",
        include_reasoning=True,
    )
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
    assert any(
        item.get("type") == "function_call_output"
        for item in fallback_request["input"]
    )
    assert not any(item.get("type") == "reasoning" for item in fallback_request["input"])
    assert trace.as_dict()["previous_response_fallback"] is True
