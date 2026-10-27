import pytest

from claimcheck.tools import (
    COMPUTE_CHANGE_TOOL,
    HISTORY_RANK_TOOL,
    LOOKUP_FACT_OUTPUT_SCHEMA,
    LOOKUP_FACT_TOOL,
    ToolRunner,
)


def test_lookup_tool_documents_period_and_derivation_fields() -> None:
    description = LOOKUP_FACT_TOOL["description"]
    assert "period_type" in description
    assert "derived" in description
    assert LOOKUP_FACT_OUTPUT_SCHEMA["properties"]["duration_days"]
    assert LOOKUP_FACT_OUTPUT_SCHEMA["properties"]["components"]


def test_compute_change_tool_is_strict_and_requires_nullable_base_period() -> None:
    assert COMPUTE_CHANGE_TOOL["strict"] is True
    parameters = COMPUTE_CHANGE_TOOL["parameters"]
    assert parameters["required"] == ["ticker", "metric", "period", "base_period"]
    assert parameters["properties"]["base_period"]["type"] == ["string", "null"]
    assert parameters["additionalProperties"] is False


def test_compute_change_rejects_mixed_period_kinds() -> None:
    runner = ToolRunner(object())
    result = runner.dispatch(
        "compute_change",
        {
            "ticker": "META",
            "metric": "revenue",
            "period": "2025Q2",
            "base_period": "FY2024",
        },
    )
    assert result["error"] == "invalid_tool_call"
    assert "same kind" in result["message"]


@pytest.mark.parametrize("base_period", [None, "", "null", "none"])
def test_compute_change_accepts_default_base_period_variants(base_period: object) -> None:
    edgar = RecordingEdgar()
    args = {
        "ticker": "META",
        "metric": "revenue",
        "period": "FY2025",
    }
    if base_period is not None:
        args["base_period"] = base_period
    result = ToolRunner(edgar).dispatch("compute_change", args)

    assert result["base_period"] == "FY2024"
    assert edgar.periods == ["FY2025", "FY2024"]


def test_history_rank_tool_is_strict() -> None:
    assert HISTORY_RANK_TOOL["strict"] is True
    assert HISTORY_RANK_TOOL["parameters"]["required"] == [
        "ticker",
        "metric",
        "period",
    ]


class RecordingEdgar:
    def __init__(self) -> None:
        self.periods: list[str] = []

    def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, int]:
        self.periods.append(period)
        return {"value": 120 if period == "FY2025" else 100}


def test_compute_change_defaults_to_prior_fiscal_year_and_numbers_all_evidence() -> None:
    edgar = RecordingEdgar()
    runner = ToolRunner(edgar)
    result = runner.dispatch(
        "compute_change",
        {
            "ticker": "META",
            "metric": "revenue",
            "period": "FY2025",
            "base_period": None,
        },
    )
    assert edgar.periods == ["FY2025", "FY2024"]
    assert result["base_period"] == "FY2024"
    assert result["abs_change"] == 20
    assert result["pct_change"] == 20
    assert result["current"]["evidence_id"] != result["base"]["evidence_id"]
    assert result["evidence_id"] not in {
        result["current"]["evidence_id"],
        result["base"]["evidence_id"],
    }


class ErrorEdgar:
    def lookup_fact(self, ticker: str, metric: str, period: str) -> dict[str, object]:
        return {
            "error": "not_additive_cannot_derive",
            "message": f"cannot derive {metric} for {period}",
            "available_periods": [],
        }


def test_compute_change_propagates_lookup_errors() -> None:
    result = ToolRunner(ErrorEdgar()).dispatch(
        "compute_change",
        {
            "ticker": "META",
            "metric": "eps_diluted",
            "period": "2025Q2",
            "base_period": None,
        },
    )
    assert result["error"] == "not_additive_cannot_derive"
    assert result["abs_change"] is None
    assert result["current"]["evidence_id"] != result["base"]["evidence_id"]
