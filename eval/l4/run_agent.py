"""One preregistered Baseten agent run, a shared $5 ceiling, offline SEC replay.

Refuses to call any model until gold/annotations/builder/source snapshots match
a local Git commit. The runner only passes claim text to the agent, never gold,
metric, kind, period, reference coordinates, or the expected verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.prompts import prompt_versions_for
from claimcheck.providers import BASETEN_BASE_URL, BASETEN_DEFAULT_MODEL
from claimcheck.release_fetch import ReleaseClient, ReleaseError
from claimcheck.trace import TraceRecorder, redact

GOLD = ROOT / "eval/l4"
FIXTURES = ROOT / "tests/fixtures/releases"


def wilson(success: int, n: int) -> list[float] | None:
    if not n:
        return None
    z, p = 1.959963984540054, success / n
    divisor = 1 + z * z / n
    center = (p + z * z / (2 * n)) / divisor
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / divisor
    return [max(0, center - half), min(1, center + half)]


def freeze_proof(git_dir: Path | None = None) -> dict:
    git = ["git"] + ([f"--git-dir={git_dir}"] if git_dir else [])
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    paths = [GOLD / name for name in ("annotations.json", "claims.jsonl", "gold_facts.json", "MANIFEST.json", "build_gold.py")]
    paths += [p for p in FIXTURES.rglob("*") if p.is_file()]
    paths += sorted((ROOT / "src/claimcheck").glob("*.py"))
    paths += [Path(__file__).resolve(), ROOT / "pyproject.toml", ROOT / "uv.lock"]
    hashes = {}
    for path in paths:
        relative = str(path.relative_to(ROOT))
        frozen = subprocess.run([*git, "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
        if frozen.returncode or frozen.stdout != path.read_bytes():
            raise RuntimeError(f"Gold must be committed before a model run: {relative}")
        hashes[relative] = hashlib.sha256(frozen.stdout).hexdigest()
    gold_commit = subprocess.check_output([*git, "log", "-1", "--format=%H", "--", "eval/l4/claims.jsonl"], cwd=ROOT).decode().strip()
    return {"revision": revision, "gold_commit": gold_commit, "sha256": hashes,
            "repository_mode": "isolated local Git directory" if git_dir else "worktree Git directory"}


def _offline(url: str):
    raise ReleaseError("URL not in the recorded L4 source corpus")


def summarize(rows: list[dict], spend: float) -> dict:
    n = len(rows)
    correct = sum(r["predicted"] == r["gold"] for r in rows)
    negatives = [r for r in rows if r["gold"] != "supported"]
    false_supported = sum(r["predicted"] == "supported" for r in negatives)
    supported = [r for r in rows if r["predicted"] == "supported"]
    latencies = sorted(r["wall_seconds"] for r in rows)
    return {"n": n, "correct": correct, "accuracy": correct / n if n else None,
            "accuracy_wilson_95": wilson(correct, n),
            "false_supported": false_supported, "non_supported_gold": len(negatives),
            "false_supported_rate": false_supported / len(negatives) if negatives else None,
            "false_supported_wilson_95": wilson(false_supported, len(negatives)),
            "false_discovery_among_supported": false_supported / len(supported) if supported else None,
            "cost_usd": spend, "trace_cost_usd": sum(r["cost_usd"] for r in rows),
            "wall_seconds_total": sum(latencies), "wall_seconds_median": statistics.median(latencies) if n else None,
            "wall_seconds_p95_nearest_rank": latencies[math.ceil(.95 * n) - 1] if n else None,
            "model_calls": sum(r["model_calls"] for r in rows),
            "confusion": dict(Counter(f"{r['gold']} -> {r['predicted']}" for r in rows)),
            "by_kind": {kind: {"correct": sum(r["gold"] == r["predicted"] for r in rows if r["kind"] == kind),
                                "n": sum(r["kind"] == kind for r in rows)} for kind in sorted({r["kind"] for r in rows})}}


def write_report(out: Path, rows: list[dict], ledger: Ledger, protocol: dict) -> None:
    metrics = summarize(rows, ledger.spent_total)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    n, correct = metrics["n"], metrics["correct"]
    interval = metrics["accuracy_wilson_95"]
    accuracy = f"{correct}/{n} = {100 * metrics['accuracy']:.1f}% (Wilson 95% {100*interval[0]:.1f}–{100*interval[1]:.1f}%)" if n else "not run"
    lines = ["# L4 Baseten agent evaluation", "", f"Accuracy: {accuracy}.", "",
             f"False-supported: {metrics['false_supported']}/{metrics['non_supported_gold']} non-supported gold claims.", "",
             f"Ledger spend: ${metrics['cost_usd']:.6f}; model calls: {metrics['model_calls']}.", "",
             f"Median wall latency: {metrics['wall_seconds_median']} s; p95: {metrics['wall_seconds_p95_nearest_rank']} s.", "",
             f"Gold/source freeze commit: `{protocol['gold_freeze']['revision']}`.", "",
             "One run of 32 generated atomic claims from eight issuers; 13 supported, 10 numeric perturbations, nine insufficient. "
             "The same fixtures informed implementation: this is a regression benchmark, not a blinded held-out estimate. "
             "The model sees only claim text and tool responses. SEC retrieval is restricted to recorded source chains and explicitly trimmed XBRL snapshots; "
             "missing corpus documents fail closed. No live SEC lookups, gold coordinates, or expected verdicts are supplied to the agent. "
             "Errors and budget stops remain scored as insufficient_evidence. All calls share one $5 ledger; SDK retries are disabled. "
             "Cost uses [Baseten's published rates](https://www.baseten.co/pricing/) checked 2026-10-29 "
             "($1.25/M input, $0.15/M cached input, $4.25/M output), not a provider invoice.", "",
             "| Claim | Gold | Program | Seconds | Cost |", "|---|---|---|---:|---:|"]
    lines += [f"| {r['id']} | {r['gold']} | {r['predicted']} | {r['wall_seconds']:.2f} | ${r['cost_usd']:.5f} |" for r in rows]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/evidence/eval-l4-2026-10-29")
    parser.add_argument("--budget-usd", type=float, default=5.0)
    parser.add_argument("--git-dir", type=Path, help="Optional isolated local Git directory when shared worktree metadata is read-only")
    parser.add_argument("--check", action="store_true", help="Verify pre-eval commit and hashes without reading a key or calling a model")
    args = parser.parse_args()
    if not 0 < args.budget_usd <= 5:
        parser.error("budget must be greater than zero and at most $5")
    proof = freeze_proof(args.git_dir)
    if args.check:
        print(json.dumps({"revision": proof["revision"], "gold_commit": proof["gold_commit"], "frozen_files": len(proof["sha256"]), "model_calls": 0}))
        return 0
    from openai import OpenAI
    settings = load_settings(provider="baseten")
    if not settings.model_api_key:
        raise RuntimeError("Baseten key unavailable; no model calls made")
    out = args.out
    if out.exists() and any(out.glob("results.jsonl")):
        raise RuntimeError("This evaluation already has results; never silently overwrite or rerun it")
    out.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=settings.model_api_key, base_url=BASETEN_BASE_URL, max_retries=0, timeout=90)
    ledger = Ledger(out / "ledger.jsonl", budget_usd=args.budget_usd, provider="baseten")
    protocol = {"started_at": datetime.now(timezone.utc).isoformat(), "provider": "baseten", "model": BASETEN_DEFAULT_MODEL,
                "budget_usd": args.budget_usd, "gold_freeze": proof,
                "pricing_source": "https://www.baseten.co/pricing/", "pricing_checked": "2026-10-29",
                "prompt_versions": prompt_versions_for("agent@baseten"), "max_turns": 5,
                "max_output_tokens": 2200, "sdk_retries": 0, "retrieval": "offline recorded SEC snapshots"}
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    claims = [json.loads(line) for line in (GOLD / "claims.jsonl").read_text().splitlines()]
    rows = []
    for case in claims:
        trace = TraceRecorder(case["claim"], BASETEN_DEFAULT_MODEL, provider="baseten", secrets=[settings.model_api_key])
        edgar = EdgarClient(FIXTURES / "xbrl", fetcher=_offline)
        releases = ReleaseClient(FIXTURES, fetcher=_offline)
        start, error = time.monotonic(), None
        try:
            result = verify_claim(case["claim"], client, edgar, ledger, BASETEN_DEFAULT_MODEL, provider="baseten",
                                  max_turns=5, max_output_tokens=2200, trace=trace, release_client=releases)
        except Exception as exc:
            error = "budget_exceeded" if isinstance(exc, BudgetExceeded) else type(exc).__name__
            result = {"verdict": "insufficient_evidence", "error": error}
            trace.finish(result)
        row = {"id": case["id"], "claim": case["claim"], "kind": case["kind"], "gold": case["gold_verdict"],
               "predicted": result["verdict"], "wall_seconds": round(time.monotonic() - start, 6),
               "cost_usd": trace.total_cost, "model_calls": trace.model_calls, "error": error,
               "trace": f"traces/{case['id']}.json"}
        (out / "traces").mkdir(exist_ok=True)
        (out / row["trace"]).write_text(json.dumps(redact(trace.as_dict(), [settings.model_api_key]), indent=2, default=str) + "\n")
        rows.append(row)
        with (out / "results.jsonl").open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        write_report(out, rows, ledger, protocol)
        print(f"{case['id']} {row['predicted']} {row['wall_seconds']:.1f}s ledger=${ledger.spent_total:.5f}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        # Only our own errors are surfaced here; SDK details/keys never printed.
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
