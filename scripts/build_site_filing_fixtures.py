#!/usr/bin/env python3
"""Record lossless first-filing iXBRL for the site; --check never uses the network."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from docs.scripts.filing_excerpts import SECFilingFetcher, extract_filing_excerpt

FIXTURES = ROOT / "tests/fixtures/sec-filings"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/filings")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cards = json.loads((ROOT / "docs/site/data/site.json").read_text())["stamp_cards"]
    facts = {fact["accn"]: fact for card in cards for fact in card["date_basis"]["facts"]}
    # The fixture reader performs hash, metadata and accession/URL checks too.
    fetcher = SECFilingFetcher(args.cache, offline=args.check, fixture_dir=FIXTURES if args.check else None)
    records = {}
    for accession, fact in sorted(facts.items()):
        source = {**fact, "value": fact["first_reported_value"], "filed": fact["first_filed"],
                  "filing_url": f"https://www.sec.gov/Archives/edgar/data/{fact['cik']}/{accession.replace('-', '')}/"}
        filing = fetcher.load_filing(source)
        parsed = extract_filing_excerpt(filing["html"], source)
        if not parsed["matched"] or parsed["excerpt"]["fact"]["full_value"] != source["value"]:
            raise ValueError(f"First-filing fact mismatch for {accession}: {parsed['reason']}")
        if not args.check:
            raw = filing["html"].encode("utf-8")
            compressed = gzip.compress(raw, mtime=0)
            FIXTURES.mkdir(parents=True, exist_ok=True)
            (FIXTURES / f"{accession}.html.gz").write_bytes(compressed)
            records[accession] = {"ticker": fact["ticker"], "cik": fact["cik"], "form": fact["form"],
                                  "filed": source["filed"], "primary_url": filing["primary_url"],
                                  "primary_document": filing["primary_document"], "inline_url": filing["inline_url"],
                                  "bytes": len(raw), "gzip_bytes": len(compressed),
                                  "sha256": hashlib.sha256(raw).hexdigest(),
                                  "gzip_sha256": hashlib.sha256(compressed).hexdigest()}
    if args.check:
        manifest = json.loads((FIXTURES / "manifest.json").read_text())
        assert set(manifest["filings"]) == set(facts), "Fixture inventory differs from first-filing date basis"
        assert {p.name for p in FIXTURES.glob("*.html.gz")} == {f"{accn}.html.gz" for accn in facts}
    else:
        manifest = {"source": "U.S. Securities and Exchange Commission, EDGAR",
                    "recorded_at": datetime.now(UTC).isoformat(),
                    "encoding": "UTF-8 iXBRL, losslessly gzip-compressed; no trimming or rewriting",
                    "filings": records}
        (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"PASS {len(facts)} first-filing iXBRL documents and exact fact values")


if __name__ == "__main__":
    main()
