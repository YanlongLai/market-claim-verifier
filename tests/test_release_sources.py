from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from claimcheck.release_fetch import ReleaseClient, ReleaseError, exhibit_links
from claimcheck.release_text import date_labels, number, parse_html, period_labels

FIXTURES = Path(__file__).parent / "fixtures/releases"


def test_cache_hash_is_checked_on_every_read(tmp_path):
    url = "https://data.sec.gov/submissions/CIK0001326801.json"
    calls = []
    client = ReleaseClient(tmp_path, fetcher=lambda u: calls.append(u) or b'{"ok":true}')
    raw, meta = client.read(url)
    assert meta["sha256"] == hashlib.sha256(raw).hexdigest()
    assert client.read(url)[0] == raw and calls == [url]
    (tmp_path / "releases" / hashlib.sha256(url.encode()).hexdigest()).write_bytes(b"tampered")
    with pytest.raises(ReleaseError, match="integrity"):
        client.read(url)


def test_exhibits_must_be_sec_indexed_html_and_inside_accession():
    url = "https://www.sec.gov/Archives/edgar/data/1/000000000125000001/0000000001-25-000001-index.html"
    raw = b'''<table><tr><td>EX-99.1</td><td><a href="release.htm">release</a></td></tr>
    <tr><td>EX-99.2</td><td><a href="slides.html">slides</a></td></tr>
    <tr><td>EX-99.2</td><td><a href="slides.pdf">PDF</a></td></tr>
    <tr><td>EX-99.1</td><td><a href="https://evil.example/r.htm">external</a></td></tr>
    <tr><td>EX-99.1</td><td><a href="../r.htm">traversal</a></td></tr></table>'''
    assert [e for e, _ in exhibit_links(raw, url)] == ["99.1", "99.2"]


def test_old_submissions_shard_and_item_filter(tmp_path):
    recent = {"accessionNumber": ["0000000001-25-000001"], "form": ["8-K"], "items": ["5.02"], "filingDate": ["2025-04-01"]}
    archive = {"accessionNumber": ["0000000001-25-000002"], "form": ["8-K"], "items": ["2.02,9.01"], "filingDate": ["2025-01-20"]}
    root = {"filings": {"recent": recent, "files": [{"name": "CIK0000000001-submissions-001.json", "filingFrom": "2025-01-01", "filingTo": "2025-01-31"}]}}
    client = ReleaseClient(tmp_path, fetcher=lambda u: archive if "-submissions-" in u else root)
    assert [r["accessionNumber"] for r in client.filings("1", "FY2025Q1")] == ["0000000001-25-000002"]


def test_text_and_cell_offsets_are_exact_and_hidden_text_is_omitted():
    doc = parse_html('<head>ignore</head><p>Revenue&nbsp;was <b>$5</b>.</p><div style="display:none">999</div><table><tr><th colspan="2">Q3 2025</th></tr><tr><td>EPS</td><td>$(0.10)</td></tr></table>')
    assert doc.text == "Revenue was $5.\nQ3 2025\nEPS | $(0.10)"
    for span in doc.spans:
        assert doc.text[span["start"]:span["end"]] == span["text"]
        for cell in span.get("cells", []):
            assert doc.text[cell["start"]:cell["end"]] == cell["text"]
    assert doc.spans[1]["cells"][0]["colspan"] == 2


@pytest.mark.parametrize("phrase,low,high", [
    ("$47.5-50.5 billion", 47.5e9, 50.5e9),
    ("between $174.0 billion and $179.5 billion", 174e9, 179.5e9),
    ("$8.7 billion, plus or minus $300 million", 8.4e9, 9e9),
    ("$54.0 billion, plus or minus 2%", 52.92e9, 55.08e9),
    ("$(0.10)", -.1, -.1),
])
def test_numbers_are_literal_and_ranges_keep_both_endpoints(phrase, low, high):
    parsed = number(phrase)
    assert parsed is not None and (parsed["low"], parsed["high"]) == (low, high)


def test_table_scale_and_verbal_ranges():
    assert number("(503)", scale=Decimal(1000000))["low"] == -503e6
    assert number("low to mid single digits") is None
    assert number("mid-70% range") is None


def test_rowspan_preserves_column_coordinates():
    doc = parse_html('<table><tr><th rowspan="2">Metric</th><th>Quarter</th></tr><tr><th>Q3 2025</th></tr><tr><td>Revenue</td><td>100</td></tr></table>')
    assert doc.spans[1]["cells"][0]["column"] == 1
    assert doc.spans[2]["cells"][1]["column"] == 1


def test_fiscal_periods_do_not_become_calendar_periods():
    assert period_labels("third quarter of fiscal 2026") == {"FY2026Q3"}
    assert period_labels("fiscal 2025 third quarter") == {"FY2025Q3"}
    assert period_labels("first quarter", context="FY2025Q4") == {"FY2026Q1"}
    assert period_labels("next quarter") == set()
    assert date_labels("Aug. 29, 2025") == ["2025-08-29"]


def test_recorded_source_chains_and_all_snapshot_hashes():
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    assert len({s["ticker"] for s in manifest}) == 8
    client = ReleaseClient(FIXTURES, fetcher=lambda u: pytest.fail(f"offline: {u}"))
    for source in manifest:
        raw, meta = client.read(source["exhibit_url"])
        assert meta["sha256"] == source["sha256"]
        index, index_meta = client.read(source["index_url"])
        assert index_meta["sha256"] == source["index_sha256"]
        assert ("99.1", source["exhibit_url"]) in exhibit_links(index, source["index_url"])
        filings = client.filings(source["cik"], source["report_period"])
        assert any(f["accessionNumber"] == source["accession"] for f in filings)
