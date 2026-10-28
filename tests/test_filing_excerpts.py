from docs.scripts.filing_excerpts import claim_excerpts, extract_filing_excerpt, group_excerpt_records


TABLE_HTML = """
<html><body>
  <xbrli:context id="c-segment">
    <xbrli:startDate>2023-01-01</xbrli:startDate>
    <xbrli:endDate>2023-09-30</xbrli:endDate>
    <xbrli:segment><xbrldi:explicitMember>x</xbrldi:explicitMember></xbrli:segment>
  </xbrli:context>
  <xbrli:context id="c-consolidated">
    <xbrli:startDate>2023-01-01</xbrli:startDate>
    <xbrli:endDate>2023-09-30</xbrli:endDate>
  </xbrli:context>
  <h2>CONSOLIDATED STATEMENTS OF OPERATIONS</h2>
  <table>
    <tr>
      <th></th>
      <th colspan="2">Three Months Ended September 30, 2023</th>
    </tr>
    <tr>
      <th>Revenue</th><th>2023</th><th>2022</th>
    </tr>
    <tr>
      <td>Total net sales</td>
      <td><ix:nonFraction name="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
          contextRef="c-segment" scale="6" id="segmented-fact">63,171</ix:nonFraction></td>
      <td><ix:nonFraction name="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
          contextRef="c-consolidated" scale="6" id="f-204">63,171</ix:nonFraction></td>
    </tr>
  </table>
</body></html>
"""


TEXT_HTML = """
<html><body>
  <xbrli:context id="c-instant">
    <xbrli:instant>2024-12-31</xbrli:instant>
  </xbrli:context>
  <p>Revenue increased to <ix:nonFraction name="us-gaap:Revenues"
      contextRef="c-instant" scale="6" id="f-text">123,456</ix:nonFraction> million during the year.</p>
</body></html>
"""


def test_table_excerpt_ignores_segment_and_marks_colspan_header():
    result = extract_filing_excerpt(
        TABLE_HTML,
        {
            "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "value": 63171000000,
            "start": "2023-01-01",
            "end": "2023-09-30",
        },
    )

    assert result["matched"] is True
    excerpt = result["excerpt"]
    assert excerpt["type"] == "table"
    assert excerpt["section_title"] == "CONSOLIDATED STATEMENTS OF OPERATIONS"
    assert excerpt["fact"]["id"] == "f-204"
    assert excerpt["fact"]["scale"] == 6
    assert excerpt["fact"]["full_value"] == 63171000000
    assert excerpt["row"]["fact_cell_index"] == 2
    assert excerpt["row"]["row_label_cell_index"] == 0
    assert excerpt["row"]["cells"][0]["is_row_label"] is True
    assert excerpt["row"]["cells"][2]["is_fact"] is True
    assert excerpt["headers"][0]["cells"][1]["covers_fact"] is True
    assert excerpt["headers"][0]["cells"][1]["colspan"] == 2


def test_table_excerpt_builds_compact_period_columns_and_highlights_fact():
    result = extract_filing_excerpt(
        TABLE_HTML,
        {
            "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "value": 63171000000,
            "start": "2023-01-01",
            "end": "2023-09-30",
        },
    )

    compact = result["excerpt"]["compact"]
    assert compact["columns"] == [
        {"key": "label", "label": "", "column_start": 0, "column_end": 1, "is_fact": False},
        {"key": "2023", "label": "2023", "column_start": 1, "column_end": 2, "is_fact": False},
        {"key": "2022", "label": "2022", "column_start": 2, "column_end": 3, "is_fact": True},
    ]
    assert compact["rows"] == [
        {
            "cells": [
                {"text": "Total net sales", "is_fact": False, "is_row_label": True},
                {"text": "63,171", "is_fact": False, "is_row_label": False},
                {"text": "63,171", "is_fact": True, "is_row_label": False},
            ]
        }
    ]


DOLLAR_TABLE_HTML = """
<html><body>
  <xbrli:context id="c-current">
    <xbrli:startDate>2023-07-01</xbrli:startDate>
    <xbrli:endDate>2024-06-30</xbrli:endDate>
  </xbrli:context>
  <table>
    <tr><th></th><th colspan="2">2024</th><th>2023</th></tr>
    <tr>
      <td>Total revenue</td><td>$</td>
      <td><ix:nonFraction name="us-gaap:Revenues" contextRef="c-current"
          scale="6" id="f-dollar">245,122</ix:nonFraction></td>
      <td>211,915</td>
    </tr>
  </table>
</body></html>
"""


def test_compact_table_joins_currency_symbol_with_value():
    result = extract_filing_excerpt(
        DOLLAR_TABLE_HTML,
        {
            "concept": "Revenues",
            "value": 245122000000,
            "start": "2023-07-01",
            "end": "2024-06-30",
        },
    )

    compact = result["excerpt"]["compact"]
    assert [column["label"] for column in compact["columns"]] == ["", "2024", "2023"]
    assert compact["rows"][0]["cells"][1]["text"] == "$245,122"
    assert compact["rows"][0]["cells"][1]["is_fact"] is True


ROLE_HTML = """
<html><body>
  <xbrli:context id="c-current">
    <xbrli:startDate>2024-01-01</xbrli:startDate>
    <xbrli:endDate>2024-12-31</xbrli:endDate>
  </xbrli:context>
  <xbrli:context id="c-comparison">
    <xbrli:startDate>2023-01-01</xbrli:startDate>
    <xbrli:endDate>2023-12-31</xbrli:endDate>
  </xbrli:context>
  <p>Current revenue <ix:nonFraction name="us-gaap:Revenues"
      contextRef="c-current" scale="6" id="fact-current">245,122</ix:nonFraction> million.</p>
  <p>Comparison revenue <ix:nonFraction name="us-gaap:Revenues"
      contextRef="c-comparison" scale="6" id="fact-comparison">211,915</ix:nonFraction> million.</p>
</body></html>
"""


class _StubFetcher:
    def load_filing(self, _evidence):
        return {
            "html": ROLE_HTML,
            "primary_url": "https://www.sec.gov/Archives/edgar/data/123/000000000000000001/filing.htm",
            "inline_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/123/000000000000000001/filing.htm",
            "primary_document": "filing.htm",
        }


def test_claim_excerpts_keys_same_id_rows_and_keeps_their_own_facts():
    claim = {
        "status": "verified",
        "evidence": [
            {
                "id": "E4",
                "role": "current",
                "concept": "Revenues",
                "value": 245122000000,
                "start": "2024-01-01",
                "end": "2024-12-31",
                "accn": "0000000000-00-000001",
                "filing_url": "https://www.sec.gov/Archives/edgar/data/123/000000000000000001/",
            },
            {
                "id": "E4",
                "role": "comparison",
                "concept": "Revenues",
                "value": 211915000000,
                "start": "2023-01-01",
                "end": "2023-12-31",
                "accn": "0000000000-00-000001",
                "filing_url": "https://www.sec.gov/Archives/edgar/data/123/000000000000000001/",
            },
        ],
    }

    records = claim_excerpts(claim, _StubFetcher())

    assert [record["evidence_index"] for record in records] == [0, 1]
    assert [record["evidence_key"] for record in records] == ["E4:current", "E4:comparison"]
    assert [record["excerpt"]["fact"]["full_value"] for record in records] == [
        245122000000,
        211915000000,
    ]


def test_group_excerpt_records_merges_identical_fact_and_keeps_comparison_separate():
    evidence = [
        {"id": "E1", "accn": "a", "concept": "Revenue", "start": "s", "end": "e", "value": 10},
        {
            "id": "E4",
            "role": "current",
            "accn": "a",
            "concept": "Revenue",
            "start": "s",
            "end": "e",
            "value": 10,
        },
        {
            "id": "E4",
            "role": "comparison",
            "accn": "a",
            "concept": "Revenue",
            "start": "p",
            "end": "q",
            "value": 8,
        },
    ]
    records = [
        {"evidence_index": 0, "evidence_key": "E1:0", "excerpt": {"fact": {"full_value": 10}}},
        {"evidence_index": 1, "evidence_key": "E4:current", "excerpt": {"fact": {"full_value": 10}}},
        {"evidence_index": 2, "evidence_key": "E4:comparison", "excerpt": {"fact": {"full_value": 8}}},
    ]

    groups = group_excerpt_records(evidence, records)

    assert [group["evidence_indices"] for group in groups] == [[0, 1], [2]]
    assert groups[0]["evidence_keys"] == ["E1:0", "E4:current"]
    assert groups[1]["evidence_keys"] == ["E4:comparison"]


def test_text_excerpt_returns_short_passage_and_fact_range():
    result = extract_filing_excerpt(
        TEXT_HTML,
        {"concept": "Revenues", "value": 123456000000, "end": "2024-12-31"},
    )

    assert result["matched"] is True
    excerpt = result["excerpt"]
    assert excerpt["type"] == "text"
    assert len(excerpt["text"]) <= 400
    fact_range = excerpt["fact_range"]
    assert excerpt["text"][fact_range["start"] : fact_range["end"]] == "123,456"
    assert excerpt["fact"]["id"] == "f-text"
    assert excerpt["fact"]["full_value"] == 123456000000


def test_unmatched_value_is_explicitly_reported():
    result = extract_filing_excerpt(
        TEXT_HTML,
        {"concept": "Revenues", "value": 99900000000, "end": "2024-12-31"},
    )

    assert result["matched"] is False
    assert result["excerpt"] is None
    assert "reported value did not match" in result["reason"]
