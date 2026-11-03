#!/usr/bin/env python3
"""Rebuild the full saved post's corrections offline, without changing its checks."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from claimcheck.correction import build_corrections  # noqa: E402

SOURCE = ROOT / "docs/evidence/posts-2026-10-28/demo-thread-baseten"
OUTPUT = ROOT / "docs/evidence/corrected-draft-2026-11-03/apple-corrections.json"


def build():
    report = json.loads((SOURCE / "report.json").read_text())
    checks, evidence = [], []
    for item in report["claims"]:
        if item["status"] == "not_checked":
            checks.append({"text": item["quote"], "claim_type": item["kind"],
                           "program_verdict": "unchecked"})
            continue
        trace = json.loads((SOURCE / item["trace_path"]).read_text())
        # Evidence IDs are local to each recorded claim. Namespace copies so
        # Amazon's E1 and NVIDIA's E1 cannot collide with Apple's E1.
        prefix = f"C{item['index']}:"
        for check in item["program_checks"]:
            checks.append({**check, "evidence_ids": [prefix + eid for eid in check["evidence_ids"]]})
        for call in trace["tool_calls"]:
            fact = call.get("result")
            if isinstance(fact, dict) and fact.get("evidence_id"):
                evidence.append({**fact, "evidence_id": prefix + fact["evidence_id"]})
    return build_corrections(report["post"], checks, evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != raw:
            raise SystemExit("apple-corrections.json is stale; run scripts/build_corrected_draft_example.py")
    else:
        OUTPUT.write_text(raw)


if __name__ == "__main__":
    main()
