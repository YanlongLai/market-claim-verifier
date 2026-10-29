"""Record a small, explicitly trimmed XBRL replay corpus from cached SEC bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/releases"
CONCEPTS = {"Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "NetIncomeLoss", "OperatingIncomeLoss", "EarningsPerShareDiluted"}


def main():
    cache, out = ROOT / ".cache", FIXTURES / "xbrl"
    out.mkdir(exist_ok=True)
    sources = json.loads((FIXTURES / "manifest.json").read_text())
    tickers = json.loads((cache / "company_tickers.json").read_text())
    selected = {s["ticker"] for s in sources}
    tickers = {k: v for k, v in tickers.items() if v["ticker"] in selected}
    (out / "company_tickers.json").write_text(json.dumps(tickers, indent=2) + "\n")
    provenance = []
    for source in sources:
        filename = f"companyfacts-CIK{source['cik']}.json"
        raw = (cache / filename).read_bytes()
        doc = json.loads(raw)
        trimmed = {k: v for k, v in doc.items() if k != "facts"}
        facts = {}
        for concept, values in doc["facts"]["us-gaap"].items():
            if concept not in CONCEPTS:
                continue
            entry = {k: v for k, v in values.items() if k != "units"}
            entry["units"] = {unit: [v for v in series if "2024" <= v.get("end", "")[:4] <= "2026"] for unit, series in values["units"].items()}
            facts[concept] = entry
        trimmed["facts"] = {"us-gaap": facts}
        serialized = (json.dumps(trimmed, indent=2) + "\n").encode()
        (out / filename).write_bytes(serialized)
        original_meta = cache / (filename + ".meta.json")
        provenance.append({"file": filename, "url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{source['cik']}.json",
                           "original_sha256": hashlib.sha256(raw).hexdigest(), "fixture_sha256": hashlib.sha256(serialized).hexdigest(),
                           "original_cache_metadata": json.loads(original_meta.read_text()) if original_meta.is_file() else None,
                           "trim": {"concepts": sorted(CONCEPTS), "period_end_years": [2024, 2025, 2026]}})
    (out / "SNAPSHOTS.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Recorded {len(provenance)} trimmed XBRL snapshots; no network/model calls.")


if __name__ == "__main__":
    main()
