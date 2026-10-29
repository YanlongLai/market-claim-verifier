from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.edgar import EdgarClient
from claimcheck.evaluate import run_evaluation
from claimcheck.trace import TraceRecorder, write_trace


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_client(tmp_path: Path) -> EdgarClient:
    tmp_path.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / "company_tickers.json", tmp_path / "company_tickers.json")
    shutil.copyfile(
        FIXTURES / "companyfacts-META-trimmed.json",
        tmp_path / "companyfacts-CIK0001326801.json",
    )
    return EdgarClient(tmp_path)


@dataclass
class FakeUsage:
    input_tokens: int = 90
    output_tokens: int = 24
    input_tokens_details: Any = None

    def __post_init__(self) -> None:
        if self.input_tokens_details is None:
            self.input_tokens_details = {"cached_tokens": 0}


@dataclass
class FakeCall:
    name: str
    arguments: str
    call_id: str
    type: str = "function_call"


class FakeResponse:
    def __init__(
        self,
        response_id: str,
        *,
        output: list[Any] | None = None,
        output_text: str | None = None,
        api_key: str | None = None,
        status: str | None = None,
        incomplete_details: Any = None,
    ) -> None:
        self.id = response_id
        self.output = output or []
        self.output_text = output_text
        self.usage = FakeUsage()
        self.api_key = api_key
        self.status = status
        self.incomplete_details = incomplete_details

    def model_dump(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "output": [getattr(item, "__dict__", item) for item in self.output],
            "output_text": self.output_text,
            "usage": self.usage.__dict__,
            "api_key": self.api_key,
            "status": self.status,
            "incomplete_details": self.incomplete_details,
        }


class FakeResponses:
    def __init__(self, final: dict[str, Any], *, response_api_key: str | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses = [
            FakeResponse(
                "r1",
                output=[
                    FakeCall(
                        "lookup_fact",
                        json.dumps({"ticker": "META", "metric": "revenue", "period": "2025Q2"}),
                        "call-1",
                    ),
                    FakeCall(
                        "lookup_fact",
                        json.dumps({"ticker": "META", "metric": "revenue", "period": "2025Q3"}),
                        "call-2",
                    ),
                ],
                api_key=response_api_key,
            ),
            FakeResponse("r2"),
            FakeResponse("r3", output_text=json.dumps(final), api_key=response_api_key),
        ]

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, final: dict[str, Any], *, response_api_key: str | None = None) -> None:
        self.responses = FakeResponses(final, response_api_key=response_api_key)


class ScriptedResponses:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses = responses

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class ScriptedClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = ScriptedResponses(responses)


def run_agent(tmp_path: Path, final: dict[str, Any], *, recorder: TraceRecorder | None = None):
    edgar = fixture_client(tmp_path / "edgar")
    ledger = Ledger(tmp_path / "runs" / "ledger.jsonl", budget_usd=0.50)
    client = FakeClient(final, response_api_key="secret-key")
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        edgar,
        ledger,
        "muse-spark-1.3",
        trace=recorder,
    )
    return result, client


def supported_final(**overrides: Any) -> dict[str, Any]:
    value = {
        "verdict": "supported",
        "summary": "The reported quarter matches the filing fact.",
        "sub_claims": [
            {
                "text": "Q2 2025 revenue",
                "stated_text": "$47.5B",
                "claim_type": "value",
                "comparator": "eq",
                "stated_value": 47_500_000_000,
                "verdict": "supported",
                "evidence_ids": ["E1"],
                "model_found_value": 47_516_000_000,
                "note": "Values are in billions of dollars.",
            }
        ],
    }
    value.update(overrides)
    return value


def test_agent_handles_parallel_calls_and_final_schema(tmp_path: Path) -> None:
    result, client = run_agent(tmp_path, supported_final())

    assert result["verdict"] == "supported"
    assert result["model_verdict"] == "supported"
    assert result["sub_claims"][0]["program_verdict"] == "supported"
    assert result["sub_claims"][0]["disagreement"] is False
    assert result["program_checks"][0]["gap"] == {
        "gap_kind": "relative", "gap": 0, "direction_wrong": False,
        "severity": "exact", "score": 100,
    }
    assert len(client.responses.calls) == 3
    assert len(client.responses.calls[1]["input"]) == 2
    assert client.responses.calls[1]["previous_response_id"] == "r1"
    assert "text" in client.responses.calls[2]
    assert "tools" not in client.responses.calls[2]


def test_agent_evaluation_persists_gaps_in_results_and_traces(tmp_path: Path) -> None:
    out = tmp_path / "eval"
    run_evaluation(
        [{"id": "gap", "split": "dev", "category": "exact_value_true", "claim": "Meta Q2 2025 revenue was $47.5B", "gold_verdict": "supported"}],
        systems=("agent",), out_dir=out, client=FakeClient(supported_final()),
        edgar=fixture_client(tmp_path / "edgar"), budget_usd=0.5,
    )
    result = json.loads((out / "gap--agent.json").read_text(encoding="utf-8"))
    trace = json.loads((out / result["trace_path"]).read_text(encoding="utf-8"))
    assert result["verdict"] == "supported"
    gap = result["program_checks"][0]["gap"]
    assert gap["severity"] == "exact" and gap["score"] == 100
    assert result["sub_claims"][0]["gap"] == trace["program_checks"][0]["gap"] == gap


def test_program_period_lookup_is_recorded_in_trace_with_program_role(
    tmp_path: Path,
) -> None:
    claim = "NVIDIA's Q2 2024 revenue was $13.5 billion."
    final = {
        "verdict": "supported",
        "summary": "The fiscal reading supports the claim.",
        "sub_claims": [
            {
                "text": claim,
                "stated_text": claim,
                "claim_type": "value",
                "comparator": "eq",
                "stated_value": 13.5e9,
                "evidence_ids": ["E1"],
                "interpretations": [],
                "verdict": "supported",
                "note": "fiscal reading",
                "model_found_value": 13.507e9,
            }
        ],
    }
    client = ScriptedClient(
        [
            FakeResponse(
                "r1",
                output=[
                    FakeCall(
                        "lookup_fact",
                        json.dumps(
                            {
                                "ticker": "NVDA",
                                "metric": "revenue",
                                "period": "FY2024Q2",
                            }
                        ),
                        "call-1",
                    )
                ],
            ),
            FakeResponse("r2"),
            FakeResponse("r3", output_text=json.dumps(final)),
        ]
    )

    class ReplayEdgar:
        def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, Any]:
            values = {
                "FY2024Q2": 13.507e9,
                "2024Q2": 30.04e9,
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

    trace = TraceRecorder(claim, "muse-spark-1.3")
    result = verify_claim(
        claim,
        client,
        ReplayEdgar(),
        Ledger(tmp_path / "runs" / "ledger.jsonl", budget_usd=0.50),
        "muse-spark-1.3",
        trace=trace,
    )

    assert result["verdict"] == "insufficient_evidence"
    assert result["program_checks"][0]["program_evidence_ids"] == ["P1"]
    program_calls = [
        call for call in trace.as_dict()["tool_calls"] if call.get("role") == "program"
    ]
    assert len(program_calls) == 1
    assert program_calls[0]["name"] == "lookup_fact"
    assert program_calls[0]["arguments"]["period"] == "2024Q2"
    assert program_calls[0]["result"]["evidence_id"] == "P1"


def test_incomplete_max_tokens_retries_and_reserves_both_attempts(tmp_path: Path) -> None:
    client = ScriptedClient(
        [
            FakeResponse(
                "incomplete-1",
                status="incomplete",
                incomplete_details={"reason": "max_output_tokens"},
            ),
            FakeResponse(
                "r1",
                output=[
                    FakeCall(
                        "lookup_fact",
                        json.dumps(
                            {"ticker": "META", "metric": "revenue", "period": "2025Q2"}
                        ),
                        "call-1",
                    )
                ],
                status="completed",
            ),
            FakeResponse("r2", status="completed"),
            FakeResponse(
                "r3",
                output_text=json.dumps(supported_final()),
                status="completed",
            ),
        ]
    )
    recorder = TraceRecorder("Meta Q2 2025 revenue was $47.5B", "muse-spark-1.3")
    edgar = fixture_client(tmp_path / "edgar")
    ledger = Ledger(tmp_path / "runs" / "ledger.jsonl", budget_usd=0.50)

    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        edgar,
        ledger,
        "muse-spark-1.3",
        trace=recorder,
    )

    assert result["verdict"] == "supported"
    assert [call["max_output_tokens"] for call in client.responses.calls] == [
        4_000,
        8_000,
        4_000,
        3_000,
    ]
    reservations = [
        json.loads(line)
        for line in (tmp_path / "runs" / "ledger.jsonl").read_text().splitlines()
        if json.loads(line)["event"] == "reserve"
    ]
    assert [item["max_output_tokens"] for item in reservations] == [
        4_000,
        8_000,
        4_000,
        3_000,
    ]
    assert recorder.as_dict()["incomplete_turns"] == [
        {
            "turn": 1,
            "attempt": 1,
            "phase": "tool",
            "status": "incomplete",
            "reason": "max_output_tokens",
            "max_output_tokens": 4_000,
        }
    ]


def test_incomplete_twice_fails_closed_without_verdict(tmp_path: Path) -> None:
    client = ScriptedClient(
        [
            FakeResponse(
                "incomplete-1",
                status="incomplete",
                incomplete_details={"reason": "max_output_tokens"},
            ),
            FakeResponse(
                "incomplete-2",
                status="incomplete",
                incomplete_details={"reason": "max_output_tokens"},
            ),
        ]
    )
    recorder = TraceRecorder("Meta Q2 2025 revenue was $47.5B", "muse-spark-1.3")
    edgar = fixture_client(tmp_path / "edgar")
    ledger = Ledger(tmp_path / "runs" / "ledger.jsonl", budget_usd=0.50)

    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        edgar,
        ledger,
        "muse-spark-1.3",
        trace=recorder,
    )

    assert result["verdict"] == "insufficient_evidence"
    assert result["incomplete_response"] is True
    assert len(client.responses.calls) == 2
    assert [item["status"] for item in recorder.as_dict()["requests"]] == [
        "incomplete",
        "incomplete",
    ]
    assert len(recorder.as_dict()["incomplete_turns"]) == 2


def test_program_check_uses_cited_evidence_not_model_found_value(tmp_path: Path) -> None:
    final = supported_final(
        sub_claims=[
            {
                "text": "Q2 2025 revenue",
                "stated_text": "$47.5B",
                "claim_type": "value",
                "comparator": "eq",
                "stated_value": 47_500_000_000,
                "verdict": "supported",
                "evidence_ids": ["E1"],
                "model_found_value": 99_900_000_000,
                "note": "wrong value",
            }
        ]
    )
    result, _ = run_agent(tmp_path, final)

    assert result["verdict"] == "supported"
    assert result["model_program_disagreement"] is False
    assert result["sub_claims"][0]["model_found_value"] == 99_900_000_000
    assert result["sub_claims"][0]["program_verdict"] == "supported"


def test_program_verdict_wins_when_model_overall_is_wrong(tmp_path: Path) -> None:
    final = supported_final(
        verdict="contradicted",
        summary="The model says the reported value is wrong.",
    )
    result, _ = run_agent(tmp_path, final)

    assert result["verdict"] == "supported"
    assert result["model_program_disagreement"] is True
    assert result["model_verdict"] == "contradicted"
    assert result["program_checks"][0]["program_verdict"] == "supported"


def test_invalid_evidence_id_is_flagged(tmp_path: Path) -> None:
    final = supported_final(
        sub_claims=[
            {
                "text": "Q2 2025 revenue",
                "stated_text": "$47.5B",
                "claim_type": "value",
                "comparator": "eq",
                "stated_value": 47_500_000_000,
                "verdict": "supported",
                "evidence_ids": ["E999"],
                "model_found_value": 47_500_000_000,
                "note": "unknown evidence",
            }
        ]
    )
    result, _ = run_agent(tmp_path, final)

    assert result["verdict"] == "insufficient_evidence"
    assert result["model_program_disagreement"] is True
    assert result["program_checks"][0]["evidence_valid"] is False
    assert result["program_checks"][0]["reason"] == "no_evidence"
    assert result["program_checks"][0]["gap"] is None


def test_trace_does_not_contain_model_key(tmp_path: Path) -> None:
    recorder = TraceRecorder(
        "Meta Q2 2025 revenue was $47.5B",
        "muse-spark-1.3",
        secrets=["secret-key"],
    )
    result, _ = run_agent(tmp_path, supported_final(), recorder=recorder)
    recorder.finish(result)
    trace_path = write_trace(tmp_path / "runs", recorder)

    assert "secret-key" not in trace_path.read_text()
    assert "[REDACTED]" in trace_path.read_text()


class ReplayEdgar:
    def __init__(self, facts: dict[tuple[str, str, str], dict[str, Any]]) -> None:
        self.facts = facts

    def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, Any]:
        return dict(self.facts[(ticker, metric, period)])

    def list_periods(self, ticker: str, metric: str) -> list[str]:
        return []


def test_replay_two_live_claims_with_new_schema(tmp_path: Path) -> None:
    final = {
        "verdict": "contradicted",
        "summary": "Tesla is supported; Alphabet is contradicted.",
        "sub_claims": [
            {
                "text": "Tesla's Q3 2025 net income was about $1.4 billion",
                "stated_text": "about $1.4 billion",
                "claim_type": "value",
                "comparator": "approx",
                "stated_value": 1_400_000_000,
                "evidence_ids": ["E1"],
                "verdict": "supported",
                "note": "$1.373B rounds to about $1.4B.",
                "model_found_value": 1_373_000_000,
            },
            {
                "text": "Alphabet's Q4 2024 revenue exceeded $100 billion",
                "stated_text": "exceeded $100 billion",
                "claim_type": "value",
                "comparator": "gt",
                "stated_value": 100_000_000_000,
                "evidence_ids": ["E2"],
                "verdict": "contradicted",
                "note": "$96.469B is below $100B.",
                "model_found_value": 96_469_000_000,
            },
        ],
    }
    client = ScriptedClient(
        [
            FakeResponse(
                "r1",
                output=[
                    FakeCall(
                        "lookup_fact",
                        json.dumps(
                            {
                                "ticker": "TSLA",
                                "metric": "net_income",
                                "period": "2025Q3",
                            }
                        ),
                        "call-1",
                    ),
                    FakeCall(
                        "lookup_fact",
                        json.dumps(
                            {
                                "ticker": "GOOGL",
                                "metric": "revenue",
                                "period": "2024Q4",
                            }
                        ),
                        "call-2",
                    ),
                ],
            ),
            FakeResponse("r2"),
            FakeResponse("r3", output_text=json.dumps(final)),
        ]
    )
    edgar = ReplayEdgar(
        {
            ("TSLA", "net_income", "2025Q3"): {"value": 1_373_000_000},
            ("GOOGL", "revenue", "2024Q4"): {"value": 96_469_000_000},
        }
    )
    ledger = Ledger(tmp_path / "runs" / "ledger.jsonl", budget_usd=0.50)
    result = verify_claim(
        "Tesla's Q3 2025 net income was about $1.4 billion and Alphabet's Q4 2024 revenue exceeded $100 billion.",
        client,
        edgar,
        ledger,
        "muse-spark-1.3",
    )

    assert result["verdict"] == "contradicted"
    assert result["model_verdict"] == "contradicted"
    assert [item["program_verdict"] for item in result["sub_claims"]] == [
        "supported",
        "contradicted",
    ]
    assert result["model_program_disagreement"] is False
