#!/usr/bin/env python3
"""Offline Story C recheck using retained public text and SEC tool results.

The public envelope omits the private model response. Reconstruct the four
typed assertions from its saved check texts and the original numeric literals;
this tests program binding/correction, not extraction, OCR/ASR or model recall.
No provider client, SEC client, credentials or network requests are used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from claimcheck.checks import evaluate_verdict
from claimcheck.correction import build_corrections

ROOT = Path(__file__).resolve().parents[1]


def proposals(envelope: dict) -> list[dict]:
    literals = ("$281.7 billion", "$164,501 billion", "$281.7 billion", "")
    values = (281.7e9, 164_501e9, 281.7e9, None)
    return [
        {"text": saved["text"], "original_claim": envelope["input"]["text_read"],
         "claim_type": "value" if index < 2 else "other", "comparator": "eq",
         "stated_text": literals[index], "stated_value": values[index],
         "evidence_ids": saved["evidence_ids"], "interpretations": [],
         "verdict": ("supported", "contradicted", "insufficient_evidence", "insufficient_evidence")[index]}
        for index, saved in enumerate(envelope["claims"])
    ]


def retained_runner(envelope: dict) -> SimpleNamespace:
    calls = []
    pending = None
    for event in envelope["events"]:
        if event["kind"] == "tool_call":
            pending = {"name": event["name"], "arguments": event["arguments"]}
        elif event["kind"] == "tool_result" and pending and pending["name"] == event["name"]:
            calls.append({**pending, "result": event["result"]})
            pending = None
    return SimpleNamespace(
        evidence={fact["evidence_id"]: fact for fact in envelope["evidence"]},
        evidence_kind={fact["evidence_id"]: "lookup_fact" for fact in envelope["evidence"]},
        calls=calls,
    )


def replay(envelope: dict) -> dict:
    checks, verdict = evaluate_verdict(proposals(envelope), retained_runner(envelope))
    return {"verdict": verdict, "checks": checks,
            "corrections": build_corrections(envelope["input"]["text_read"], checks, envelope["evidence"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="+", default=["c-text"],
                        choices=[f"c-{kind}" for kind in ("text", "image", "pdf", "audio", "video")])
    args = parser.parse_args()
    results = {}
    for example_id in args.ids:
        path = ROOT / f"docs/site/data/examples/{example_id}.json"
        raw = path.read_bytes()
        envelope = json.loads(raw)
        results[example_id] = {
            "source": str(path.relative_to(ROOT)), "source_sha256": hashlib.sha256(raw).hexdigest(),
            "recorded_verdict": envelope["verdict"],
            "recorded_reasons": [check["reason"] for check in envelope["claims"]],
            "retests_ocr_asr": False, "paid_calls": 0, **replay(envelope)}
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
