#!/usr/bin/env python3
"""Publish public steps from the saved Apple claim and post; never reasoning text.

The source has per-call durations and run start/end, but no individual tool
timestamps. Null timestamps preserve that distinction. No paid run is created.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from claimcheck.correction import build_corrections  # noqa: E402

EVIDENCE = ROOT / "docs/evidence/eval-v2-2026-10-27"
SOURCE = EVIDENCE / "R06--agent@baseten.json"
OUTPUT = ROOT / "docs/site/data/live-demo.json"
POST_SOURCE = ROOT / "docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json"
POST_OUTPUT = ROOT / "docs/site/data/live-demo-post.json"


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


def qualify_evidence(value, claim_index):
    """Each claim trace restarts at E1; keep references unique in the envelope."""
    if isinstance(value, dict):
        return {key: qualify_evidence(item, claim_index) for key, item in value.items()}
    if isinstance(value, list):
        return [qualify_evidence(item, claim_index) for item in value]
    if isinstance(value, str) and re.fullmatch(r"E\d+", value):
        return f"C{claim_index}:{value}"
    return value


def build_post():
    record = json.loads(POST_SOURCE.read_text())
    sources = []
    events, checks, evidence = [], [], []
    model_step = 0

    def read_source(path):
        sources.append({"path": str(path.relative_to(ROOT)),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return json.loads(path.read_text())

    read_source(POST_SOURCE)

    def append_trace(path, claim_index=None):
        nonlocal model_step
        trace = read_source(path)
        public = qualify_evidence(trace, claim_index) if claim_index is not None else trace
        emitted = set()
        context = {"claim_index": claim_index, "at_ms": None, "timestamp": None}
        for request in public["requests"]:
            model_step += 1
            choice = request["raw_response"]["choices"][0]
            events.append({**context, "kind": "model", "step": model_step,
                           "latency_ms": request["latency_ms"], "cost_usd": request["cost"],
                           "cost_is_bound": False, "finish_reason": choice["finish_reason"]})
            for call in choice["message"].get("tool_calls") or []:
                tool = next(t for t in public["tool_calls"] if t.get("call_id") == call["id"])
                emitted.add(call["id"])
                evidence.append(tool["result"])
                events.extend([
                    {**context, "kind": "tool_call", "name": tool["name"], "arguments": tool["arguments"]},
                    {**context, "kind": "tool_result", "name": tool["name"], "result": tool["result"]},
                ])
        assert len(emitted) == len(public["tool_calls"]), "every recorded tool must appear"
        return context

    append_trace(POST_SOURCE.parent / record["extraction_trace"])
    for claim in record["claims"]:
        index = claim["index"]
        if claim["status"] == "not_checked":
            # A screened opinion has no program verdict or model check trace.
            checks.append({"claim_index": index, "text": claim["quote"],
                           "program_verdict": "unchecked", "evidence_ids": [],
                           "reason": claim["screen_reason"]})
            continue
        context = append_trace(POST_SOURCE.parent / claim["trace_path"], index)
        for check in qualify_evidence(claim["program_checks"], index):
            check = {**check, "claim_index": index}
            checks.append(check)
            events.append({**context, "kind": "program_check", "check": check})
    verdict = next(v for v in ("contradicted", "insufficient_evidence", "supported")
                   if record["verdicts"].get(v))
    events.append({"kind": "verdict", "at_ms": None, "timestamp": None, "verdict": verdict})
    return {"mode": "recorded", "input": record["post"], "provider": record["provider"],
            "model": record["model"], "verdict": verdict, "claims": checks,
            "evidence": evidence, "events": events,
            "corrections": build_corrections(record["post"], checks, evidence),
            "cost_usd": record["cost_usd"], "cost_is_bound": False,
            "latency_ms": record["wall_clock_s"] * 1000,
            "source": str(POST_SOURCE.relative_to(ROOT)), "source_sha256": sources[0]["sha256"],
            "sources": sources,
            "timing_note": "Recorded post run labelled 28 Oct 2026; trace filenames use UTC. "
                           "The report records wall-clock duration and model-call durations, "
                           "not run start/end or individual tool/check timestamps."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for output, data in ((OUTPUT, build()), (POST_OUTPUT, build_post())):
        raw = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not output.exists() or output.read_text() != raw:
                raise SystemExit(f"{output.name} is stale; run scripts/build_live_demo.py")
        else:
            output.write_text(raw)


if __name__ == "__main__":
    main()
