from pathlib import Path

import pytest


@pytest.fixture
def offline_stamp_facts(tmp_path, monkeypatch):
    """Rebuild stamp metadata from hash-checked fixtures, never an ignored cache."""
    from docs.scripts import build_site, filing_excerpts

    fixtures = Path(__file__).parent / "fixtures" / "sec-offline"

    def no_network(*_args, **_kwargs):
        raise AssertionError("Stamp tests must use committed SEC fixtures, not downloads")

    monkeypatch.setattr(build_site, "FILING_CACHE_PATH", tmp_path / "filings")
    monkeypatch.setattr(filing_excerpts, "urlopen", no_network)
    return fixtures
