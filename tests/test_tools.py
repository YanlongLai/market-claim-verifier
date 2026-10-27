from claimcheck.tools import LOOKUP_FACT_OUTPUT_SCHEMA, LOOKUP_FACT_TOOL


def test_lookup_tool_documents_period_and_derivation_fields() -> None:
    description = LOOKUP_FACT_TOOL["description"]
    assert "period_type" in description
    assert "derived" in description
    assert LOOKUP_FACT_OUTPUT_SCHEMA["properties"]["duration_days"]
    assert LOOKUP_FACT_OUTPUT_SCHEMA["properties"]["components"]
