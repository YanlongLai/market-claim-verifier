"""Record the SEC source chain for the fixed L4 benchmark; never calls a model."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from claimcheck.release_fetch import ReleaseClient

SOURCES = [
    ("META", "1326801", "2025-07-30", "FY2025Q2"),
    ("AAPL", "320193", "2025-07-31", "FY2025Q3"),
    ("NVDA", "1045810", "2025-08-27", "FY2026Q2"),
    ("AMD", "2488", "2025-08-05", "FY2025Q2"),
    ("INTC", "50863", "2025-07-24", "FY2025Q2"),
    ("CRM", "1108524", "2025-09-03", "FY2026Q2"),
    ("ADBE", "796343", "2025-09-11", "FY2025Q3"),
    ("AMZN", "1018724", "2025-07-31", "FY2025Q2"),
]


def main() -> None:
    destination = ROOT / "tests/fixtures/releases"
    client = ReleaseClient(destination)
    manifest = []
    for ticker, cik, filed, period in SOURCES:
        filings = [row for row in client.filings(cik, period) if row["filingDate"] == filed]
        if len(filings) != 1:
            raise RuntimeError(f"{ticker}: expected exactly one Item 2.02 filing on {filed}")
        exhibits = client.exhibits(cik, filings[0])
        releases = [item for item in exhibits if item["exhibit"] == "99.1"]
        if len(releases) != 1:
            raise RuntimeError(f"{ticker}: expected one HTML Ex 99.1")
        source = {k: v for k, v in releases[0].items() if k != "raw"}
        source.update(ticker=ticker, report_period=period)
        manifest.append(source)
        print(ticker, source["accession"], len(releases[0]["raw"]), flush=True)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
