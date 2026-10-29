"""Original first-filing documents back every on-screen number, fully offline."""
import json
from pathlib import Path

import pytest

from docs.scripts.filing_excerpts import SECFilingFetcher, extract_filing_excerpt


FIXTURES = Path(__file__).parent / "fixtures/sec-filings"


def first_sources():
    site = json.loads((FIXTURES.parents[2] / "docs/site/data/site.json").read_text())
    return {fact["accn"]: {**fact, "filed": fact["first_filed"], "value": fact["first_reported_value"],
                          "filing_url": f"https://www.sec.gov/Archives/edgar/data/{fact['cik']}/{fact['accn'].replace('-', '')}/"}
            for card in site["stamp_cards"] for fact in card["date_basis"]["facts"]}


def test_all_first_filing_values_including_growth_and_q4_components_have_original_ixbrl(tmp_path, monkeypatch):
    from docs.scripts import filing_excerpts
    monkeypatch.setattr(filing_excerpts, "urlopen", lambda *_a, **_k: pytest.fail("Fixture reader used network"))
    fetcher = SECFilingFetcher(tmp_path / "empty-cache", offline=True, fixture_dir=FIXTURES)
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    sources = first_sources()
    assert len(sources) == 11 and sources.keys() == manifest["filings"].keys()
    assert {p.stem.removesuffix(".html") for p in FIXTURES.glob("*.html.gz")} == sources.keys()
    for accession, source in sources.items():
        filing = fetcher.load_filing(source)
        parsed = extract_filing_excerpt(filing["html"], source)
        assert parsed["matched"], (accession, parsed["reason"])
        assert parsed["excerpt"]["fact"]["full_value"] == source["value"]
        assert len(filing["html"].encode("utf-8")) == manifest["filings"][accession]["bytes"]
    assert list((tmp_path / "empty-cache").iterdir()) == []


def test_a_modified_filing_fixture_fails_closed_without_a_cache_or_download_fallback(tmp_path):
    source = next(iter(first_sources().values()))
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    manifest["filings"][source["accn"]]["sha256"] = "0" * 64
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    name = f"{source['accn']}.html.gz"
    (tmp_path / name).write_bytes((FIXTURES / name).read_bytes())
    fetcher = SECFilingFetcher(tmp_path / "cache", offline=True, fixture_dir=tmp_path)
    with pytest.raises(ValueError, match="hash mismatch"):
        fetcher.load_filing(source)
