from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.edgar import EdgarClient
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
                "verdict": "supported",
                "evidence_ids": ["E1"],
                "expected_value": 47.5,
                "found_value": 47.516,
                "note": "Values are in billions of dollars.",
            }
        ],
    }
    value.update(overrides)
    return value


def test_agent_handles_parallel_calls_and_final_schema(tmp_path: Path) -> None:
    result, client = run_agent(tmp_path, supported_final())

    assert result["verdict"] == "supported"
    assert result["sub_claims"][0]["program_check"] == "match"
    assert len(client.responses.calls) == 3
    assert len(client.responses.calls[1]["input"]) == 2
    assert client.responses.calls[1]["previous_response_id"] == "r1"
    assert "text" in client.responses.calls[2]
    assert "tools" not in client.responses.calls[2]


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


def test_program_check_overrides_wrong_supported(tmp_path: Path) -> None:
    final = supported_final(
        sub_claims=[
            {
                "text": "Q2 2025 revenue",
                "verdict": "supported",
                "evidence_ids": ["E1"],
                "expected_value": 47.5,
                "found_value": 99.9,
                "note": "wrong value",
            }
        ]
    )
    result, _ = run_agent(tmp_path, final)

    assert result["verdict"] == "insufficient_evidence"
    assert result["model_program_disagreement"] is True
    assert result["sub_claims"][0]["program_check"] == "mismatch"


def test_program_check_flags_contradicted_when_all_values_match(tmp_path: Path) -> None:
    final = supported_final(
        verdict="contradicted",
        summary="The model says the reported value is wrong.",
    )
    result, _ = run_agent(tmp_path, final)

    assert result["verdict"] == "insufficient_evidence"
    assert result["model_program_disagreement"] is True
    assert result["program_checks"][0]["program_check"] == "match"


def test_invalid_evidence_id_is_flagged(tmp_path: Path) -> None:
    final = supported_final(
        sub_claims=[
            {
                "text": "Q2 2025 revenue",
                "verdict": "supported",
                "evidence_ids": ["E999"],
                "expected_value": 47.5,
                "found_value": 47.5,
                "note": "unknown evidence",
            }
        ]
    )
    result, _ = run_agent(tmp_path, final)

    assert result["verdict"] == "insufficient_evidence"
    assert result["model_program_disagreement"] is True
    assert result["program_checks"][0]["evidence_valid"] is False


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
