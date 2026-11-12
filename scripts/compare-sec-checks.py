#!/usr/bin/env python3
"""Frozen adversarial component comparison, not a blind article-quality study."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from claimcheck.check_json import check_document, digest
from claimcheck.edgar import EdgarClient

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
root = Path(__file__).resolve().parents[1]
cases = json.loads((root / "docs/evidence/sec-switch-20261111/cases.json").read_text())
issuers = json.loads((root / "docs/evidence/sec-switch-20261111/issuers.json").read_text())
with tempfile.TemporaryDirectory() as cache:
    for source, dest in [("company_tickers.json", "company_tickers.json"), ("companyfacts-META-trimmed.json", "companyfacts-CIK0001326801.json")]:
        shutil.copyfile(root / "tests/fixtures" / source, Path(cache) / dest)
    def offline(url): raise RuntimeError("no network in frozen comparison")
    client = EdgarClient(cache, fetcher=offline, as_of="2025-10-30")
    on = check_document(cases, issuers, client)
    off = check_document(cases, issuers, client, enabled=False)
    for name, value in [("enabled.json", on), ("paused.json", off)]:
        (args.out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n")
rows = []
for claim, result in zip(cases["claims"], on["results"]):
    before = f"{claim['ticker']} {claim['period']} {claim['metric']}: {claim['value']:,} {claim['unit']}."
    after = result.get("statement", "Omitted: no sufficiently bound SEC evidence.")
    rows.append({"id":claim["id"], "before":before, "after":after, "status":result["status"], "reason":result["reason"]})
    # Both surfaces use the identical adjudicated statement, preventing subtitle
    # and narration divergence; these are script excerpts, not rendered videos.
    (args.out / (claim["id"]+".md")).write_text(f"# {claim['id']}\n\nControlled article excerpt BEFORE:\n\n{before}\n\nControlled article excerpt AFTER:\n\n{after}\n\nVideo narration/subtitle BEFORE:\n\n{before}\n\nVideo narration/subtitle AFTER:\n\n{after}\n")
summary = {"design":"six predeclared adversarial component cases, one replay-inspired issuer failure; not representative traffic", "input_sha256":digest(cases), "baseline":{"accepted_claims":6,"valid_original_claims":1},"enabled":{"verified":sum(r["status"]=="verified" for r in rows),"corrected":sum(r["status"]=="corrected" for r in rows),"omitted":sum(r["status"]=="omitted" for r in rows)},"paused":{"publishable_sec_statements":len(off["publishable_statements"])},"limitations":["No blind readability evaluation","No rendered video, TTS, engagement or audience-quality measurement","Fixtures are historical and trimmed; no fresh market accuracy claim","Correct currency mismatch omitted despite a potentially recoverable numeric value","Issuer replay-inspired case reproduces the identity boundary, not the original full trace"],"cases":rows}
(args.out / "comparison.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({k:v for k,v in summary.items() if k!="cases"},indent=2))
