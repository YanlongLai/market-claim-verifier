from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_sub_claim, evaluate_verdict


FIXTURES = Path(__file__).parent / "fixtures" / "live"
EVIDENCE = Path(__file__).parents[1] / "docs" / "evidence" / "2026-10-27"


class ReplayCall:
    type = "function_call"

    def __init__(self, name: str, arguments: dict[str, Any], call_id: str) -> None:
        self.name = name
        self.arguments = json.dumps(arguments)
        self.call_id = call_id


class ReplayResponse:
    def __init__(
        self,
        response_id: str,
        *,
        calls: list[ReplayCall] | None = None,
        final: dict[str, Any] | None = None,
    ) -> None:
        self.id = response_id
        self.output = calls or []
        self.output_text = json.dumps(final) if final is not None else None
        self.status = "completed"
        self.incomplete_details = None
        self.usage = SimpleNamespace(
            input_tokens=20,
            output_tokens=20,
            input_tokens_details=SimpleNamespace(cached_tokens=0),
        )


class ReplayClient:
    def __init__(self, calls: list[ReplayCall], final: dict[str, Any]) -> None:
        self.responses = self
        self._responses = [
            ReplayResponse("r1", calls=calls),
            ReplayResponse("r2"),
            ReplayResponse("r3", final=final),
        ]

    def create(self, **_: Any) -> ReplayResponse:
        return self._responses.pop(0)


class ReplayEdgar:
    def __init__(
        self,
        facts: dict[tuple[str, str, str], dict[str, Any]],
        histories: dict[tuple[str, str, str], dict[str, Any]] | None = None,
    ) -> None:
        self.facts = facts
        self.histories = histories or {}

    def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, Any]:
        return copy.deepcopy(self.facts[(ticker, metric, period)])

    def list_periods(self, ticker: str, metric: str) -> list[str]:
        return []

    def history_rank(self, ticker: str, metric: str, period: str) -> dict[str, Any]:
        return copy.deepcopy(self.histories[(ticker, metric, period)])


def _load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _load_evidence(name: str) -> dict[str, Any]:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _fact(value: float, **extra: Any) -> dict[str, Any]:
    return {"value": value, **extra}


def _run(
    tmp_path: Path,
    fixture: dict[str, Any],
    calls: list[ReplayCall],
    final: dict[str, Any],
    edgar: ReplayEdgar,
) -> dict[str, Any]:
    ledger = Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0)
    return verify_claim(
        fixture["claim"],
        ReplayClient(calls, final),
        edgar,
        ledger,
        "muse-spark-1.3",
    )


def test_corrected_live_claims_replay_with_fake_client(tmp_path: Path) -> None:
    meta = _load("20261027T215912Z-318638f2.json")
    meta_final = copy.deepcopy(meta["final_verdict"])
    meta_final["verdict"] = "supported"
    meta_final["sub_claims"][1]["evidence_ids"] = ["E2", "E3", "E4"]
    meta_result = _run(
        tmp_path / "meta",
        meta,
        [
            ReplayCall("lookup_fact", meta["tool_calls"][0]["arguments"], "c1"),
            ReplayCall("compute_change", meta["tool_calls"][1]["arguments"], "c2"),
        ],
        meta_final,
        ReplayEdgar(
            {
                ("META", "revenue", "2025Q2"): _fact(47_516_000_000),
                ("META", "revenue", "2024Q2"): _fact(39_071_000_000),
            }
        ),
    )

    tesla = _load("20261027T220105Z-60aa1eb7.json")
    tesla_final = copy.deepcopy(tesla["final_verdict"])
    tesla_final["verdict"] = "contradicted"
    tesla_final["sub_claims"][0]["evidence_ids"] = ["E1", "E2", "E3"]
    tesla_result = _run(
        tmp_path / "tesla",
        tesla,
        [ReplayCall("compute_change", tesla["tool_calls"][0]["arguments"], "c1")],
        tesla_final,
        ReplayEdgar(
            {
                ("TSLA", "revenue", "2025Q3"): _fact(28_095_000_000),
                ("TSLA", "revenue", "2024Q3"): _fact(25_182_000_000),
            }
        ),
    )

    first_time = _load("20261027T220019Z-d41d5d2a.json")
    first_time_final = copy.deepcopy(first_time["final_verdict"])
    first_time_final["verdict"] = "supported"
    first_time_final["sub_claims"].append(
        {
            "text": "Alphabet's Q3 2025 revenue topped $100 billion for the first time",
            "stated_text": "$100 billion",
            "claim_type": "first_time_above",
            "comparator": "gt",
            "stated_value": 100_000_000_000,
            "evidence_ids": ["E2"],
            "verdict": "supported",
            "model_found_value": 102_346_000_000,
            "note": "No earlier comparable quarter exceeded $100B.",
        }
    )
    first_time_result = _run(
        tmp_path / "first-time",
        first_time,
        [
            ReplayCall("lookup_fact", first_time["tool_calls"][0]["arguments"], "c1"),
            ReplayCall(
                "history_rank",
                {"ticker": "GOOGL", "metric": "revenue", "period": "2025Q3"},
                "c2",
            ),
        ],
        first_time_final,
        ReplayEdgar(
            {("GOOGL", "revenue", "2025Q3"): _fact(102_346_000_000)},
            {
                ("GOOGL", "revenue", "2025Q3"): {
                    "period": "2025Q3",
                    "period_type": "quarter",
                    "value": 102_346_000_000,
                    "rank": 1,
                    "count": 4,
                    "is_highest": True,
                    "is_lowest": False,
                    "previous_high": {"period": "2025Q2", "value": 96_000_000_000},
                    "previous_low": {"period": "2024Q1", "value": 80_000_000_000},
                    "periods_considered": {"first": "2024Q1", "last": "2025Q3"},
                    "periods": [
                        {"period": "2024Q1", "value": 80_000_000_000},
                        {"period": "2025Q2", "value": 96_000_000_000},
                        {"period": "2025Q3", "value": 102_346_000_000},
                    ],
                }
            },
        ),
    )

    missing = _load("20261027T220157Z-8a35d825.json")
    missing_final = copy.deepcopy(missing["final_verdict"])
    missing_final["sub_claims"][0]["evidence_ids"] = ["E1"]
    missing_result = _run(
        tmp_path / "missing",
        missing,
        [ReplayCall("lookup_fact", missing["tool_calls"][0]["arguments"], "c1")],
        missing_final,
        ReplayEdgar(
            {
                ("META", "revenue", "2026Q4"): {
                    "error": "fact_not_found"
                }
            }
        ),
    )

    assert meta_result["verdict"] == "supported"
    assert [item["program_verdict"] for item in meta_result["sub_claims"]] == [
        "supported",
        "supported",
    ]

    pair = _load("20261027T215950Z-aaaa582a.json")
    pair_result = _run(
        tmp_path / "pair",
        pair,
        [
            ReplayCall("lookup_fact", pair["tool_calls"][0]["arguments"], "c1"),
            ReplayCall("lookup_fact", pair["tool_calls"][1]["arguments"], "c2"),
        ],
        pair["final_verdict"],
        ReplayEdgar(
            {
                ("TSLA", "net_income", "2025Q3"): _fact(1_373_000_000),
                ("GOOGL", "revenue", "2024Q4"): _fact(96_469_000_000),
            }
        ),
    )
    assert tesla_result["verdict"] == "contradicted"
    assert tesla_result["sub_claims"][0]["reason"] != "ambiguous_evidence"
    assert pair_result["verdict"] == "contradicted"
    assert [item["program_verdict"] for item in pair_result["sub_claims"]] == [
        "supported",
        "contradicted",
    ]
    assert first_time_result["verdict"] == "supported"
    assert len(first_time_result["sub_claims"]) == 2
    assert missing_result["verdict"] == "insufficient_evidence"
    assert missing_result["sub_claims"][0]["reason"] == "no_evidence"


def _recorded_runner(fixture: dict[str, Any]) -> SimpleNamespace:
    evidence: dict[str, dict[str, Any]] = {}
    evidence_kind: dict[str, str] = {}
    for call in fixture["tool_calls"]:
        result = copy.deepcopy(call["result"])
        evidence_id = result["evidence_id"]
        evidence[evidence_id] = result
        evidence_kind[evidence_id] = call["name"]
        for field in ("current_fact", "base_fact"):
            component = result.get(field)
            if isinstance(component, dict) and component.get("evidence_id"):
                component_id = component["evidence_id"]
                evidence[component_id] = component
                evidence_kind[component_id] = "lookup_fact"
    return SimpleNamespace(evidence=evidence, evidence_kind=evidence_kind)


@pytest.mark.parametrize(
    "filename",
    [
        "20261027T215912Z-318638f2.json",
        "20261027T215950Z-aaaa582a.json",
        "20261027T220019Z-d41d5d2a.json",
        "20261027T220105Z-60aa1eb7.json",
        "20261027T220157Z-8a35d825.json",
        "20261027T221423Z-aca6a7ca.json",
        "20261027T222216Z-21a72526.json",
    ],
)
def test_exact_recorded_model_outputs_replay_with_evidence_resolution(filename: str) -> None:
    fixture = _load(filename)
    runner = _recorded_runner(fixture)
    checks, verdict = evaluate_verdict(fixture["final_verdict"]["sub_claims"], runner)

    if filename.endswith("215912Z-318638f2.json"):
        assert checks[1]["program_verdict"] == "supported"
    elif filename.endswith("220105Z-60aa1eb7.json"):
        assert checks[0]["program_verdict"] == "contradicted"
        assert checks[0]["stated_sign_corrected"] is False
    elif filename.endswith("220157Z-8a35d825.json"):
        assert checks[0]["reason"] == "ambiguous_evidence"
        assert verdict == "insufficient_evidence"
    elif filename.endswith("215950Z-aaaa582a.json"):
        assert [check["program_verdict"] for check in checks] == [
            "supported",
            "contradicted",
        ]
    elif filename.endswith("221423Z-aca6a7ca.json"):
        assert verdict == "supported"
        assert [check["program_verdict"] for check in checks] == [
            "supported",
            "supported",
        ]
        assert checks[1]["stated_text_unparsed"] is False
        assert checks[1]["threshold_from_model"] is False
    elif filename.endswith("222216Z-21a72526.json"):
        assert verdict == "supported"
        assert [check["program_verdict"] for check in checks] == [
            "supported",
            "supported",
        ]
    else:
        assert all(check["program_verdict"] == "supported" for check in checks)


@pytest.mark.parametrize("include_period", [False, True])
def test_recorded_first_time_trace_matches_by_dates_or_period(
    include_period: bool,
) -> None:
    trace = _load_evidence("20261027T222216Z-21a72526.json")
    if include_period:
        trace["tool_calls"][0]["result"]["period"] = "2025Q3"

    runner = _recorded_runner(trace)
    checks, verdict = evaluate_verdict(trace["final_verdict"]["sub_claims"], runner)

    assert checks[1]["program_verdict"] == "supported"
    assert verdict == "supported"


def test_first_time_above_is_contradicted_when_an_earlier_period_exceeds_threshold() -> None:
    fixture = _load("20261027T221423Z-aca6a7ca.json")
    fixture["tool_calls"][1]["result"]["periods"][0]["value"] = 101_000_000_000
    fixture["tool_calls"][1]["result"]["comparable_periods"][0]["value"] = 101_000_000_000
    runner = _recorded_runner(fixture)

    checks, verdict = evaluate_verdict(fixture["final_verdict"]["sub_claims"], runner)

    assert checks[1]["program_verdict"] == "contradicted"
    assert verdict == "contradicted"
    assert "earlier_periods_above" in checks[1]["reason"]


def test_first_time_above_fallback_threshold_is_flagged_without_unparsed_text() -> None:
    fixture = _load("20261027T221423Z-aca6a7ca.json")
    runner = _recorded_runner(fixture)
    first_time = copy.deepcopy(fixture["final_verdict"]["sub_claims"][1])
    first_time["evidence_ids"] = ["E2"]

    check = evaluate_sub_claim(first_time, runner)

    assert check["program_verdict"] == "supported"
    assert check["threshold_from_model"] is True
    assert check["stated_text_unparsed"] is False


def test_record_high_ignores_later_periods() -> None:
    fixture = _load("20261027T221423Z-aca6a7ca.json")
    runner = _recorded_runner(fixture)
    record_claim = {
        "text": "Alphabet's Q3 2025 revenue was a record high",
        "stated_text": "record high",
        "claim_type": "record_high",
        "comparator": "eq",
        "stated_value": 1,
        "evidence_ids": ["E2"],
        "verdict": "supported",
        "model_found_value": 1,
        "note": "Highest through the claimed quarter.",
    }

    check = evaluate_sub_claim(record_claim, runner)

    assert check["program_verdict"] == "supported"
