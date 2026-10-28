from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.evaluate import SYSTEMS, single_shot_request
from claimcheck.providers import chat_tool_definitions
from claimcheck.trace import TraceRecorder
from claimcheck.cli import _parse_systems


FIXTURES = Path(__file__).parent / "fixtures"


def _edgar(tmp_path: Path) -> EdgarClient:
    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "company_tickers.json", cache / "company_tickers.json")
    shutil.copyfile(
        FIXTURES / "companyfacts-META-trimmed.json",
        cache / "companyfacts-CIK0001326801.json",
    )
    return EdgarClient(cache)


def _verdict() -> dict[str, Any]:
    return {
        "verdict": "supported",
        "summary": "ok",
        "sub_claims": [
            {
                "text": "Q2 2025 revenue",
                "stated_text": "$47.5B",
                "claim_type": "value",
                "comparator": "eq",
                "stated_value": 47_500_000_000,
                "evidence_ids": ["E1"],
                "verdict": "supported",
                "note": "ok",
                "model_found_value": 47_516_000_000,
            }
        ],
    }


class RawResponse:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.headers = {
            "x-ratelimit-limit-requests": "100",
            "x-ratelimit-remaining-requests": "99",
            "x-ratelimit-limit-tokens": "2000000",
        }

    def parse(self) -> Any:
        return self.response


class FakeCompletions:
    def __init__(self, outputs: list[Any]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, Any]] = []
        self.with_raw_response = self

    def create(self, **kwargs: Any) -> RawResponse:
        self.calls.append(kwargs)
        return RawResponse(self.outputs.pop(0))


class FakeChatClient:
    def __init__(self, outputs: list[Any]) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(outputs))


def _usage() -> Any:
    return SimpleNamespace(
        prompt_tokens=666,
        completion_tokens=156,
        prompt_tokens_details=SimpleNamespace(cached_tokens=10),
        completion_tokens_details=SimpleNamespace(
            reasoning_tokens=52,
            accepted_prediction_tokens=4,
            rejected_prediction_tokens=1,
        ),
    )


def _response(*, content: str | None = None, tool_calls: list[Any] | None = None) -> Any:
    message = SimpleNamespace(
        role="assistant",
        content=content,
        tool_calls=tool_calls or [],
        reasoning_content="private reasoning",
    )
    choice = SimpleNamespace(
        finish_reason="tool_calls" if tool_calls else "stop",
        message=message,
    )
    return SimpleNamespace(id="response", choices=[choice], usage=_usage())


def _tool_call() -> Any:
    return SimpleNamespace(
        id="call-1",
        type="function",
        function=SimpleNamespace(
            name="lookup_fact",
            arguments=json.dumps(
                {"ticker": "META", "metric": "revenue", "period": "2025Q2"}
            ),
        ),
    )


def test_baseten_tool_loop_history_and_trace(tmp_path: Path) -> None:
    client = FakeChatClient(
        [
            _response(tool_calls=[_tool_call()]),
            _response(content="planning complete"),
            _response(content=json.dumps(_verdict())),
        ]
    )
    recorder = TraceRecorder(
        "Meta Q2 2025 revenue was $47.5B",
        "meta-models/muse-spark-open-1026",
        provider="baseten",
    )
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        _edgar(tmp_path),
        Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0),
        "meta-models/muse-spark-open-1026",
        trace=recorder,
        provider="baseten",
    )

    assert result["verdict"] == "supported"
    assert len(client.chat.completions.calls) == 3
    continuation = client.chat.completions.calls[1]
    assert [message["role"] for message in continuation["messages"]] == [
        "system",
        "user",
        "assistant",
        "tool",
    ]
    assert continuation["messages"][-1]["tool_call_id"] == "call-1"
    assert continuation["tools"] == chat_tool_definitions()
    assert recorder.as_dict()["provider"] == "baseten"
    request_trace = recorder.as_dict()["requests"][0]
    assert request_trace["raw_response"]["choices"][0]["message"]["reasoning_content"] == "private reasoning"
    assert request_trace["usage"] == {"input": 666, "cached": 10, "output": 156, "reasoning": 52}
    assert request_trace["raw_usage"]["completion_tokens_details"]["accepted_prediction_tokens"] == 4
    assert request_trace["rate_limit_headers"]["x-ratelimit-limit-requests"] == "100"
    assert request_trace["finish_reason"] == "tool_calls"


def test_baseten_fenced_json_and_repair_path(tmp_path: Path) -> None:
    fenced = "```json\n" + json.dumps(_verdict()) + "\n```"
    client = FakeChatClient(
        [
            _response(tool_calls=[_tool_call()]),
            _response(content="planning complete"),
            _response(content=fenced),
        ]
    )
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        _edgar(tmp_path),
        Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0),
        "meta-models/muse-spark-open-1026",
        provider="baseten",
    )
    assert result["verdict"] == "supported"
    assert len(client.chat.completions.calls) == 3

    client = FakeChatClient(
        [
            _response(tool_calls=[_tool_call()]),
            _response(content="planning complete"),
            _response(content="not json"),
            _response(content=json.dumps(_verdict())),
        ]
    )
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        _edgar(tmp_path / "repair"),
        Ledger(tmp_path / "repair-ledger.jsonl", budget_usd=1.0),
        "meta-models/muse-spark-open-1026",
        provider="baseten",
    )
    assert result["verdict"] == "supported"
    assert len(client.chat.completions.calls) == 4
    assert client.chat.completions.calls[3]["messages"][-1]["role"] == "user"


def test_baseten_invalid_json_twice_fails_closed(tmp_path: Path) -> None:
    client = FakeChatClient(
        [
            _response(tool_calls=[_tool_call()]),
            _response(content="planning complete"),
            _response(content="bad"),
            _response(content="still bad"),
        ]
    )
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        _edgar(tmp_path),
        Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0),
        "meta-models/muse-spark-open-1026",
        provider="baseten",
    )
    assert result["verdict"] == "insufficient_evidence"
    assert result["invalid_model_json"] is True
    assert len(client.chat.completions.calls) == 4


def test_baseten_config_and_provider_budget_are_separate(tmp_path: Path) -> None:
    key_file = tmp_path / "baseten.key"
    key_file.write_text("raw-baseten-key", encoding="utf-8")
    settings = load_settings(
        {
            "CLAIMCHECK_PROVIDER": "baseten",
            "BASETEN_API_KEY_FILE": str(key_file),
        },
        read_key=True,
    )
    assert settings.provider == "baseten"
    assert settings.model == "meta-models/muse-spark-open-1026"
    assert settings.model_api_key == "raw-baseten-key"

    ledger = Ledger(tmp_path / "ledger.jsonl", budget_usd=0.00001)
    ledger.reserve({}, provider="meta", model="muse-spark-1.3", max_output_tokens=1)
    ledger.reserve({}, provider="baseten", model="meta-models/muse-spark-open-1026", max_output_tokens=1)
    with pytest.raises(BudgetExceeded):
        ledger.reserve(
            {"large": "x" * 100},
            provider="baseten",
            model="meta-models/muse-spark-open-1026",
            max_output_tokens=100,
        )


def test_baseten_request_and_eval_system_aliases() -> None:
    request = single_shot_request(
        "Meta revenue was $47.5B",
        "meta-models/muse-spark-open-1026",
        provider="baseten",
        today="2026-10-27",
        reasoning_effort="low",
    )
    assert set(request) == {"model", "messages", "max_tokens", "reasoning_effort"}
    assert "tools" not in request
    assert "2026-10-27" in request["messages"][0]["content"]
    assert _parse_systems("single_shot,agent") == ("single_shot@meta", "agent@meta")
    assert _parse_systems("single_shot,agent", provider="baseten") == (
        "single_shot@baseten",
        "agent@baseten",
    )
    assert SYSTEMS == (
        "single_shot@meta",
        "agent@meta",
        "single_shot@baseten",
        "agent@baseten",
        "single_shot@fireworks",
        "agent@fireworks",
    )
