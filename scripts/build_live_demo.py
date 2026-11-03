#!/usr/bin/env python3
"""Publish public steps from one real Apple trace; never publish reasoning text.

The source has per-call durations and run start/end, but no individual tool
timestamps. Null timestamps preserve that distinction. No paid run is created.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from claimcheck.correction import build_corrections  # noqa: E402

EVIDENCE = ROOT / "docs/evidence/eval-v2-2026-10-27"
SOURCE = EVIDENCE / "R06--agent@baseten.json"
OUTPUT = ROOT / "docs/site/data/live-demo.json"


def build():
    record = json.loads(SOURCE.read_text())
    trace_path = EVIDENCE / record["trace_path"]
    trace = json.loads(trace_path.read_text())
    events = []
    emitted = set()
    elapsed = 0.0
    for i, request in enumerate(trace["requests"]):
        elapsed += request["latency_ms"]
        message = request["raw_response"]["choices"][0]["message"]
        events.append({"kind": "model", "step": i + 1, "at_ms": None, "timestamp": None,
                       "latency_ms": request["latency_ms"], "cost_usd": request["cost"],
                       "cost_is_bound": False,
                       "finish_reason": request["raw_response"]["choices"][0]["finish_reason"]})
        for call in message.get("tool_calls") or []:
            tool = next(t for t in trace["tool_calls"] if t.get("call_id") == call["id"])
            emitted.add(call["id"])
            events.extend([
                {"kind": "tool_call", "at_ms": None, "timestamp": None,
                 "name": tool["name"], "arguments": tool["arguments"]},
                {"kind": "tool_result", "at_ms": None, "timestamp": None,
                 "name": tool["name"], "result": tool["result"]},
            ])
    assert len(emitted) == len(trace["tool_calls"]), "every recorded tool must appear"
    checks = trace["program_checks"]
    events.extend({"kind": "program_check", "at_ms": None, "timestamp": None, "check": c} for c in checks)
    events.append({"kind": "verdict", "at_ms": None, "timestamp": None,
                   "verdict": trace["final_verdict"]["verdict"]})
    evidence = [t["result"] for t in trace["tool_calls"]]
    return {"mode": "recorded", "input": record["claim"], "provider": trace["provider"],
            "model": trace["model"], "verdict": trace["final_verdict"]["verdict"],
            "model_verdict": trace["final_verdict"].get("model_verdict"),
            "summary": trace["final_verdict"]["summary"], "claims": checks,
            "evidence": evidence, "events": events,
            "corrections": build_corrections(record["claim"], checks, evidence),
            "cost_usd": trace["cost_usd"], "cost_is_bound": False, "latency_ms": trace["latency_ms"],
            "started_at": record["started_at"], "finished_at": record["finished_at"],
            "source": str(trace_path.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
            "timing_note": "Run start/end and model-call durations are recorded. Tool/check timestamps were not recorded."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != raw:
            raise SystemExit("live-demo.json is stale; run scripts/build_live_demo.py")
    else:
        OUTPUT.write_text(raw)


if __name__ == "__main__":
    main()
