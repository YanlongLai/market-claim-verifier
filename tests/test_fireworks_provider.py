from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.cli import _parse_systems
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.evaluate import report_evaluation, run_evaluation, single_shot_request
from claimcheck.providers import (
    FIREWORKS_BASE_URL,
    FIREWORKS_DEFAULT_MODEL,
    FIREWORKS_PROVIDER,
    baseten_final_verdict_prompt,
    fireworks_final_verdict_prompt,
    chat_tool_definitions,
    get_provider,
)
from claimcheck.prompts import prompt_registry, prompt_versions_for
from claimcheck.trace import TraceRecorder


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
                "interpretations": [],
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
            "x-ratelimit-over-limit": "0",
            "content-type": "application/json",
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


def test_fireworks_tool_loop_history_trace_and_headers(tmp_path: Path) -> None:
    client = FakeChatClient(
        [
            _response(tool_calls=[_tool_call()]),
            _response(content="planning complete"),
            _response(content=json.dumps(_verdict())),
        ]
    )
    recorder = TraceRecorder(
        "Meta Q2 2025 revenue was $47.5B",
        FIREWORKS_DEFAULT_MODEL,
        provider=FIREWORKS_PROVIDER,
    )
    result = verify_claim(
        "Meta Q2 2025 revenue was $47.5B",
        client,
        _edgar(tmp_path),
        Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0),
        FIREWORKS_DEFAULT_MODEL,
        trace=recorder,
        provider=FIREWORKS_PROVIDER,
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
    trace = recorder.as_dict()
    assert trace["provider"] == FIREWORKS_PROVIDER
    request_trace = trace["requests"][0]
    assert request_trace["raw_response"]["choices"][0]["message"]["reasoning_content"] == "private reasoning"
    assert request_trace["usage"] == {"input": 666, "cached": 10, "output": 156, "reasoning": 52}
    assert request_trace["raw_usage"]["completion_tokens_details"]["accepted_prediction_tokens"] == 4
    assert request_trace["rate_limit_headers"]["x-ratelimit-over-limit"] == "0"
    assert request_trace["finish_reason"] == "tool_calls"


def test_fireworks_plain_json_repair_path(tmp_path: Path) -> None:
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
        _edgar(tmp_path),
        Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0),
        FIREWORKS_DEFAULT_MODEL,
        provider=FIREWORKS_PROVIDER,
    )

    assert result["verdict"] == "supported"
    assert len(client.chat.completions.calls) == 4
    assert client.chat.completions.calls[3]["messages"][-1]["role"] == "user"


def test_fireworks_config_pricing_and_budget_pool_isolation(tmp_path: Path) -> None:
    key_file = tmp_path / "fireworks.key"
    key_file.write_text("raw-fireworks-key", encoding="utf-8")
    settings = load_settings(
        {
            "CLAIMCHECK_PROVIDER": FIREWORKS_PROVIDER,
            "FIREWORKS_API_KEY_FILE": str(key_file),
        },
        read_key=True,
    )
    assert settings.provider == FIREWORKS_PROVIDER
    assert settings.model == FIREWORKS_DEFAULT_MODEL
    assert settings.model_api_key == "raw-fireworks-key"
    assert settings.fireworks_api_key_file == key_file

    provider = get_provider(FIREWORKS_PROVIDER)
    assert provider.base_url == FIREWORKS_BASE_URL
    assert provider.api_key_env == "FIREWORKS_API_KEY"
    assert provider.default_api_key_file == "~/secret/fireworks-api-key.txt"
    assert provider.pricing == {
        "input": 1.25 / 1_000_000,
        "cached_input": 0.15 / 1_000_000,
        "output": 4.25 / 1_000_000,
    }

    ledger = Ledger(
        tmp_path / "ledger.jsonl",
        budget_usd=0.00001,
        provider_budgets={"meta": 0.00001, FIREWORKS_PROVIDER: 0.00001},
    )
    ledger.reserve(
        {}, model="muse-spark-1.3", max_output_tokens=1, provider="meta"
    )
    ledger.reserve(
        {}, model=FIREWORKS_DEFAULT_MODEL, max_output_tokens=1, provider=FIREWORKS_PROVIDER
    )
    assert ledger.spent_for_provider("meta") > 0
    assert ledger.spent_for_provider(FIREWORKS_PROVIDER) > 0
    with pytest.raises(BudgetExceeded):
        ledger.reserve(
            {"large": "x" * 100},
            model=FIREWORKS_DEFAULT_MODEL,
            max_output_tokens=100,
            provider=FIREWORKS_PROVIDER,
        )


def test_fireworks_request_and_prompt_aliases() -> None:
    request = single_shot_request(
        "Meta revenue was $47.5B",
        FIREWORKS_DEFAULT_MODEL,
        provider=FIREWORKS_PROVIDER,
        today="2026-10-27",
        reasoning_effort="low",
    )
    assert set(request) == {"model", "messages", "max_tokens", "reasoning_effort"}
    assert request["model"] == FIREWORKS_DEFAULT_MODEL
    assert "tools" not in request
    assert "2026-10-27" in request["messages"][0]["content"]
    assert fireworks_final_verdict_prompt() == baseten_final_verdict_prompt()
    assert _parse_systems("single_shot,agent", provider=FIREWORKS_PROVIDER) == (
        "single_shot@fireworks",
        "agent@fireworks",
    )


def test_fireworks_prompt_registry_reuses_baseten_hashes() -> None:
    registry = prompt_registry()
    for fireworks_name, baseten_name in (
        ("fireworks_tool_loop_instructions", "baseten_tool_loop_instructions"),
        ("fireworks_final_verdict_prompt", "baseten_final_verdict_prompt"),
        ("fireworks_repair_prompt", "baseten_repair_prompt"),
        ("fireworks_single_shot_instructions", "baseten_single_shot_instructions"),
    ):
        assert registry[fireworks_name]["sha256"] == registry[baseten_name]["sha256"]
    assert prompt_versions_for("single_shot@fireworks")["fireworks_single_shot_instructions"] == registry[
        "baseten_single_shot_instructions"
    ]["sha256"]


def test_fireworks_appears_in_provider_report(tmp_path: Path) -> None:
    claim = {
        "id": "C01",
        "split": "dev",
        "category": "exact_value_true",
        "claim": "Meta revenue was $47.5B.",
        "gold_verdict": "supported",
    }
    claims_path = tmp_path / "claims.jsonl"
    claims_path.write_text(json.dumps(claim) + "\n", encoding="utf-8")
    out = tmp_path / "eval"
    run_evaluation(
        [claim],
        systems=("single_shot@fireworks",),
        out_dir=out,
        client=FakeChatClient([_response(content=json.dumps(_verdict()))]),
        budget_usd=1.0,
        split="dev",
        claims_path=claims_path,
    )
    summary = report_evaluation(out, claims_path=claims_path)
    assert summary["provider_comparison"][FIREWORKS_PROVIDER]["pairs"] == 1
    assert "| fireworks |" in (out / "REPORT.md").read_text(encoding="utf-8")
