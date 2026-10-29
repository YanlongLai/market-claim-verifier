#!/usr/bin/env python3
"""Trim already-cached SEC snapshots for tests; no downloads or model calls.

Raw inputs must match the existing v2 evaluation manifest. This creates test
inputs only, never evaluation claims, gold answers or recorded model results.
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = {
    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "NetIncomeLoss",
    "OperatingIncomeLoss", "GrossProfit", "Assets", "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "PaymentsToAcquirePropertyPlantAndEquipment", "ResearchAndDevelopmentExpense", "EarningsPerShareDiluted",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--cache", type=Path, help="Local original SEC snapshot directory")
    mode.add_argument("--check", action="store_true", help="Check committed fixture hashes without original snapshots")
    args = parser.parse_args()
    manifest_path = ROOT / "docs/evidence/eval-v2-2026-10-27/manifest.json"
    source_hashes = json.loads(manifest_path.read_text())["sec_companyfacts_snapshot_sha256"]
    target = ROOT / "tests/fixtures/sec-offline"
    if args.check:
        provenance = json.loads((target / "provenance.json").read_text())["snapshots"]
        if set(provenance) != set(source_hashes):
            raise ValueError("fixture inventory differs from the source manifest")
        for name, record in provenance.items():
            if record["original_sha256"] != source_hashes[name]:
                raise ValueError(f"{name}: original source hash drift")
            if hashlib.sha256((target / name).read_bytes()).hexdigest() != record["fixture_sha256"]:
                raise ValueError(f"{name}: fixture hash drift")
        print(f"PASS {len(provenance)} committed SEC fixture hashes and recorded source hashes")
        return
    target.mkdir(parents=True, exist_ok=True)
    provenance = {}
    for name, expected in sorted(source_hashes.items()):
        raw = (args.cache / name).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"{name}: raw input does not match the recorded v2 snapshot hash")
        document = json.loads(raw)
        facts = {}
        for concept, node in document["facts"]["us-gaap"].items():
            if concept in CONCEPTS:
                facts[concept] = {**node, "units": {
                    unit: [row for row in rows if row.get("end", "") >= "2022-01-01"]
                    for unit, rows in node["units"].items()
                }}
        document["facts"] = {"us-gaap": facts}
        output = (json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        (target / name).write_bytes(output)
        provenance[name] = {"original_sha256": actual, "fixture_sha256": hashlib.sha256(output).hexdigest()}
    tickers = json.loads((ROOT / "eval/v2/MANIFEST.json").read_text())["counts"]["by_company"]
    ticker_map = json.loads((args.cache / "company_tickers.json").read_text())
    selected = [record for record in ticker_map.values() if record["ticker"] in tickers]
    selected.sort(key=lambda record: record["ticker"])
    assert {record["ticker"] for record in selected} == set(tickers)
    (target / "company_tickers.json").write_text(json.dumps(dict(enumerate(selected)), indent=2) + "\n")
    (target / "provenance.json").write_text(json.dumps({
        "source_manifest": "docs/evidence/eval-v2-2026-10-27/manifest.json",
        "selection": {"namespace": "us-gaap", "concepts": sorted(CONCEPTS), "end_on_or_after": "2022-01-01"},
        "snapshots": provenance,
    }, indent=2) + "\n")
    print(f"Prepared {len(provenance)} trimmed SEC snapshots for offline tests")


if __name__ == "__main__":
    main()
