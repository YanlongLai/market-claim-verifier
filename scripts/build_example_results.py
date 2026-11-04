#!/usr/bin/env python3
"""Build saved example envelopes from retained runs, never synthesize results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/site/data/examples"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def from_record(folder, example_id, asset):
    receipt_path = folder / example_id / "receipt.json"
    response_path = folder / example_id / "response.json"
    receipt = json.loads(receipt_path.read_text())
    raw = response_path.read_bytes()
    result = json.loads(raw)
    if (receipt["http_status"] != 200 or receipt.get("attempts") != 1 or receipt.get("example_id") != example_id or
        result.get("mode") != "live" or receipt["response_sha256"] != sha(raw) or
        receipt["asset_sha256"] != asset["sha256"] or result.get("error") or
        result.get("verdict") not in {"supported", "contradicted", "insufficient_evidence"} or
        result.get("input", {}).get("example_id") != example_id or result["input"].get("kind") != asset["kind"] or
        not isinstance(result["input"].get("text_read"), str) or not result["input"]["text_read"].strip()):
        raise ValueError(f"Incomplete/mismatched retained run: {example_id}; keep it, do not publish as a result")
    result.update(mode="recorded", source=str(response_path.relative_to(ROOT)), source_sha256=sha(raw),
                  recording={"receipt": str(receipt_path.relative_to(ROOT)), "receipt_sha256": sha(receipt_path.read_bytes()),
                             "asset_sha256": asset["sha256"], "attempts": 1},
                  timing_note="One real example request; includes OCR/ASR/PDF preprocessing, not a frozen-transcript recheck.")
    return result


def build(*, check=False, records=None):
    assets = json.loads((ROOT / "docs/site/examples/manifest.json").read_text())
    original = json.loads((ROOT / "docs/site/data/live-demo-post.json").read_text())
    text = original["input"]
    original["input"] = {"example_id": "text", "kind": "text", "text_read": text,
                         "preprocessing": {"model": "native-text", "provider": "local", "cost_usd": 0, "latency_ms": None}}
    original["recording"] = {"type": "reused_saved_text", "note": "Original saved post run; no new request or preprocessing timing.",
                             "asset_sha256": assets[0]["sha256"]}
    results = {"text": original}
    for asset in assets:
        example_id = asset["id"]
        if records is not None and (records / example_id).exists():
            results[example_id] = from_record(records, example_id, asset)
        elif (OUTPUT / f"{example_id}.json").exists():
            saved = json.loads((OUTPUT / f"{example_id}.json").read_text())
            if saved.get("recording", {}).get("receipt"):
                folder = (ROOT / saved["recording"]["receipt"]).parent.parent
                results[example_id] = from_record(folder, example_id, asset)
            elif example_id != "text":
                raise ValueError(f"Missing retained recording provenance: {example_id}")
    outputs = {OUTPUT / f"{key}.json": encoded(value) for key, value in results.items()}
    outputs[OUTPUT / "index.json"] = encoded([{**asset, "saved_result": f"/data/examples/{asset['id']}.json" if asset["id"] in results else None}
                                               for asset in assets])
    for path, raw in outputs.items():
        if check:
            if not path.exists() or path.read_bytes() != raw:
                raise ValueError(f"Stale saved example: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--records", type=Path, help="Explicit retained host recording directory")
    args = parser.parse_args()
    if args.check and args.records:
        parser.error("--check only verifies the already selected records")
    build(check=args.check, records=args.records.resolve() if args.records else None)


if __name__ == "__main__":
    main()
