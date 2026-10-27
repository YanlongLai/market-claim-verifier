from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from claimcheck.checks import evaluate_sub_claim, overall_program_verdict
from claimcheck.edgar import EdgarClient
from claimcheck.tools import ToolRunner


FIXTURES = Path(__file__).parent / "fixtures"


def runner_with_evidence(*values: float) -> SimpleNamespace:
    evidence = {f"E{index}": {"value": value} for index, value in enumerate(values, 1)}
    evidence_kind = {evidence_id: "lookup_fact" for evidence_id in evidence}
    return SimpleNamespace(evidence=evidence, evidence_kind=evidence_kind)


def claim(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "text": "Tesla Q3 2025 net income was about $1.4B",
        "stated_text": "about $1.4B",
        "claim_type": "value",
        "comparator": "approx",
        "stated_value": 1.4e9,
        "evidence_ids": ["E1"],
        "verdict": "supported",
        "model_found_value": 1.373e9,
        "note": "rounded claim",
    }
    value.update(overrides)
    return value


def test_approx_about_1_4b_supports_tesla_1_373b() -> None:
    check = evaluate_sub_claim(claim(), runner_with_evidence(1.373e9))
    assert check["program_verdict"] == "supported"
    assert check["actual_value"] == pytest.approx(1.373e9)
    assert check["tolerance"] == pytest.approx(100e6)


def test_exact_1_4b_uses_rounding_math_not_a_fixed_1_5_percent_rule() -> None:
    # $1.4B has precision $0.05B, so 1.373B is inside 1.35B..1.45B.
    check = evaluate_sub_claim(
        claim(stated_text="$1.4B", comparator="eq"), runner_with_evidence(1.373e9)
    )
    assert check["program_verdict"] == "supported"
    assert check["tolerance"] == pytest.approx(50e6)


def test_exceeded_100b_is_strict_inequality() -> None:
    check = evaluate_sub_claim(
        claim(
            text="Alphabet Q4 2024 revenue exceeded $100B",
            stated_text="exceeded $100B",
            comparator="gt",
            stated_value=100e9,
            model_found_value=96.469e9,
        ),
        runner_with_evidence(96.469e9),
    )
    assert check["program_verdict"] == "contradicted"
    assert check["tolerance"] == 0.0


def _fixture_runner(tmp_path: Path) -> ToolRunner:
    cache = tmp_path / "edgar"
    cache.mkdir()
    shutil.copyfile(FIXTURES / "company_tickers.json", cache / "company_tickers.json")
    shutil.copyfile(
        FIXTURES / "companyfacts-META-trimmed.json",
        cache / "companyfacts-CIK0001326801.json",
    )
    return ToolRunner(EdgarClient(cache))


@pytest.mark.parametrize("comparator", ["approx", "eq"])
def test_meta_growth_uses_compute_change_evidence(
    tmp_path: Path, comparator: str
) -> None:
    runner = _fixture_runner(tmp_path)
    change = runner.dispatch(
        "compute_change",
        {
            "ticker": "META",
            "metric": "revenue",
            "period": "2025Q2",
            "base_period": None,
        },
    )
    actual = change["pct_change"]
    result = evaluate_sub_claim(
        {
            "text": "Meta Q2 2025 revenue was up 22% YoY",
            "stated_text": "up 22%",
            "claim_type": "change_pct",
            "comparator": comparator,
            "stated_value": 22.0,
            "evidence_ids": [change["evidence_id"]],
            "verdict": "supported",
            "model_found_value": actual,
            "note": "year-over-year growth",
        },
        runner,
    )
    assert actual == pytest.approx(21.6144966855)
    assert result["actual_value"] == pytest.approx(actual)
    assert result["program_verdict"] == "supported"


def test_change_evidence_allows_its_two_component_fact_ids(tmp_path: Path) -> None:
    runner = _fixture_runner(tmp_path)
    change = runner.dispatch(
        "compute_change",
        {
            "ticker": "META",
            "metric": "revenue",
            "period": "2025Q2",
            "base_period": "2024Q2",
        },
    )
    result = evaluate_sub_claim(
        {
            "text": "Meta revenue was up 22%",
            "stated_text": "up 22%",
            "claim_type": "change_pct",
            "comparator": "approx",
            "stated_value": 22.0,
            "evidence_ids": [
                change["current_fact"]["evidence_id"],
                change["base_fact"]["evidence_id"],
                change["evidence_id"],
            ],
            "verdict": "supported",
            "model_found_value": change["pct_change"],
            "note": "component citations are allowed",
        },
        runner,
    )

    assert result["program_verdict"] == "supported"
    assert result["actual_value"] == pytest.approx(21.6144966855)


def test_value_evidence_deduplicates_matching_lookup_and_compute_component(
    tmp_path: Path,
) -> None:
    runner = _fixture_runner(tmp_path)
    lookup = runner.dispatch(
        "lookup_fact",
        {"ticker": "META", "metric": "revenue", "period": "2025Q2"},
    )
    change = runner.dispatch(
        "compute_change",
        {
            "ticker": "META",
            "metric": "revenue",
            "period": "2025Q2",
            "base_period": "2024Q2",
        },
    )
    result = evaluate_sub_claim(
        claim(
            evidence_ids=[lookup["evidence_id"], change["evidence_id"]],
            stated_text="$47.5B",
            stated_value=47.5e9,
        ),
        runner,
    )

    assert result["program_verdict"] == "supported"
    assert result["evidence_valid"] is True


def test_no_numeric_or_error_only_citations_are_no_evidence() -> None:
    runner = SimpleNamespace(
        evidence={"E1": {"error": "fact_not_found"}, "E2": {"value": ["2025Q2"]}},
        evidence_kind={"E1": "lookup_fact", "E2": "list_periods"},
    )
    result = evaluate_sub_claim(claim(evidence_ids=["E1", "E2"]), runner)

    assert result["program_verdict"] == "unchecked"
    assert result["reason"] == "no_evidence"


@pytest.mark.parametrize(
    ("text", "stated_text", "stated_value", "actual", "expected", "sign_flag"),
    [
        ("Revenue fell 10%", "fell 10%", -10.0, 11.5678, "contradicted", False),
        ("Revenue fell 10%", "10%", 10.0, -10.0, "supported", True),
        ("Revenue grew 22%", "22%", -22.0, 21.6145, "supported", True),
    ],
)
def test_change_direction_is_parsed_and_model_sign_can_be_corrected(
    text: str,
    stated_text: str,
    stated_value: float,
    actual: float,
    expected: str,
    sign_flag: bool,
) -> None:
    runner = runner_with_evidence()
    runner.evidence = {"E1": {"pct_change": actual}}
    runner.evidence_kind = {"E1": "compute_change"}
    result = evaluate_sub_claim(
        {
            "text": text,
            "stated_text": stated_text,
            "claim_type": "change_pct",
            "comparator": "approx",
            "stated_value": stated_value,
            "evidence_ids": ["E1"],
            "verdict": expected,
            "model_found_value": actual,
            "note": "direction",
        },
        runner,
    )

    assert result["program_verdict"] == expected
    assert result["stated_sign_corrected"] is sign_flag


def test_value_tolerance_is_capped_at_ten_percent_of_stated() -> None:
    result = evaluate_sub_claim(
        claim(
            stated_text="$2 trillion",
            stated_value=2e12,
            evidence_ids=["E1"],
        ),
        runner_with_evidence(2.25e12),
    )

    assert result["tolerance"] == pytest.approx(0.2e12)
    assert result["program_verdict"] == "contradicted"


def test_record_and_first_time_claims_use_history_rank(tmp_path: Path) -> None:
    runner = _fixture_runner(tmp_path)
    record_history = runner.dispatch(
        "history_rank",
        {"ticker": "META", "metric": "revenue", "period": "2026Q3"},
    )
    history = runner.dispatch(
        "history_rank",
        {"ticker": "META", "metric": "revenue", "period": "2025Q3"},
    )
    record = evaluate_sub_claim(
        {
            "text": "Meta Q3 2026 revenue was a record high",
            "stated_text": "record high",
            "claim_type": "record_high",
            "comparator": "eq",
            "stated_value": 1,
            "evidence_ids": [record_history["evidence_id"]],
            "verdict": "supported",
            "model_found_value": 1,
            "note": "history",
        },
        runner,
    )
    first_time = evaluate_sub_claim(
        {
            "text": "Meta Q3 2025 revenue topped $50B for the first time",
            "stated_text": "$50B",
            "claim_type": "first_time_above",
            "comparator": "gt",
            "stated_value": 50e9,
            "evidence_ids": [history["evidence_id"]],
            "verdict": "supported",
            "model_found_value": history["value"],
            "note": "history",
        },
        runner,
    )

    assert record["program_verdict"] == "supported"
    assert "periods_considered" in record["reason"]
    assert first_time["program_verdict"] == "supported"


def test_other_claims_are_always_unchecked() -> None:
    result = evaluate_sub_claim(
        {
            "text": "Meta is headquartered in Menlo Park",
            "stated_text": "headquartered in Menlo Park",
            "claim_type": "other",
            "comparator": "eq",
            "stated_value": None,
            "evidence_ids": [],
            "verdict": "supported",
            "model_found_value": None,
            "note": "not checked by SEC fact tools",
        },
        runner_with_evidence(),
    )

    assert result["program_verdict"] == "unchecked"
    assert result["reason"] == "unchecked_other_claim"


def test_subclaim_disagreement_is_model_verdict_vs_program_verdict() -> None:
    check = evaluate_sub_claim(
        claim(verdict="contradicted"), runner_with_evidence(1.373e9)
    )
    assert check["program_verdict"] == "supported"
    assert check["disagreement"] is True


def test_ambiguous_evidence_is_unchecked() -> None:
    check = evaluate_sub_claim(
        claim(evidence_ids=["E1", "E2"]), runner_with_evidence(1.373e9, 1.374e9)
    )
    assert check["program_verdict"] == "unchecked"
    assert check["reason"] == "ambiguous_evidence"
    assert check["disagreement"] is False


def test_stated_text_correction_and_unparsed_fallback_are_flagged() -> None:
    corrected = evaluate_sub_claim(
        claim(stated_text="$1.3B"), runner_with_evidence(1.3e9)
    )
    assert corrected["stated_value_corrected"] is True
    assert corrected["stated_value_used"] == pytest.approx(1.3e9)

    unparsed = evaluate_sub_claim(
        claim(stated_text="not stated", stated_value=1.4e9), runner_with_evidence(1.4e9)
    )
    assert unparsed["stated_text_unparsed"] is True
    assert unparsed["precision"] == pytest.approx(7e6)
    assert unparsed["program_verdict"] == "supported"


def test_gte_and_lte_accept_equality_within_precision() -> None:
    gte = evaluate_sub_claim(
        claim(stated_text="$1.4B", comparator="gte"), runner_with_evidence(1.36e9)
    )
    lte = evaluate_sub_claim(
        claim(stated_text="$1.4B", comparator="lte"), runner_with_evidence(1.44e9)
    )
    assert gte["program_verdict"] == "supported"
    assert lte["program_verdict"] == "supported"


def test_overall_program_verdict_rules() -> None:
    assert overall_program_verdict([{"program_verdict": "supported"}]) == "supported"
    assert overall_program_verdict(
        [{"program_verdict": "supported"}, {"program_verdict": "contradicted"}]
    ) == "contradicted"
    assert overall_program_verdict(
        [{"program_verdict": "supported"}, {"program_verdict": "unchecked"}]
    ) == "insufficient_evidence"
    assert overall_program_verdict([]) == "insufficient_evidence"
