"""Run frozen DappGo news claims and the actual post CLI under shared task caps.

Refuses calls unless every frozen input/runtime byte matches the gold commit.
Gold and source metadata never enter the model's claim or post input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.prompts import prompt_versions_for
from claimcheck.providers import get_provider
from claimcheck.release_fetch import ReleaseClient
from claimcheck.trace import TraceRecorder, redact


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def append(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def freeze_proof(out: Path, git_dir: Path | None) -> dict:
    git = ["git", *([f"--git-dir={git_dir}"] if git_dir else [])]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    freeze = json.loads((out / "FREEZE.json").read_text())
    for relative, expected in freeze["sha256"].items():
        raw = (ROOT / relative).read_bytes()
        recorded = subprocess.run([*git, "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
        if hashlib.sha256(raw).hexdigest() != expected or recorded.returncode or raw != recorded.stdout:
            raise RuntimeError(f"uncommitted or changed frozen input: {relative}")
    freeze_relative = str((out / "FREEZE.json").relative_to(ROOT))
    frozen = subprocess.check_output([*git, "show", f"{revision}:{freeze_relative}"], cwd=ROOT)
    if frozen != (out / "FREEZE.json").read_bytes():
        raise RuntimeError("FREEZE.json must itself be committed")
    return {"revision": revision, "mode": "isolated local git directory" if git_dir else "worktree",
            "freeze_sha256": hashlib.sha256(frozen).hexdigest(), "files_checked": len(freeze["sha256"])}


def run_provider(provider: str, claims: list[dict], out: Path, cache: Path) -> dict:
    from openai import OpenAI

    settings = load_settings(provider=provider)
    if not settings.model_api_key:
        raise RuntimeError(f"{provider} key unavailable")
    secrets = [settings.model_api_key]
    ledger = Ledger(out / "ledger.jsonl", budget_usd=10, provider=provider,
                    provider_budgets={p: 10 for p in ("meta", "baseten", "fireworks")})
    adapter = get_provider(provider)
    client = OpenAI(api_key=settings.model_api_key, base_url=adapter.base_url, max_retries=0, timeout=90)
    model = settings.model
    edgar = EdgarClient(cache, user_agent="DappGo market-claim-verifier admin@dappgo.com", as_of="2026-11-02")
    releases = ReleaseClient(cache, user_agent="DappGo market-claim-verifier admin@dappgo.com")
    stopped = None
    started = now()
    for path_name in ("agent", "post"):
        for case in claims:
            target = out / provider / path_name / case["id"]
            target.mkdir(parents=True, exist_ok=False)
            base = {"id": case["id"], "provider": provider, "path": path_name, "model": model,
                    "started_at": now(), "status": "not_attempted", "verdict": None,
                    "cost_usd": 0, "model_calls": 0, "wall_seconds": 0}
            if stopped:
                row = {**base, "status": "budget_stopped", "error": stopped, "finished_at": now()}
                write(target / "result.json", row)
                append(out / provider / path_name / "results.jsonl", row)
                continue
            before = ledger.spent_for_provider(provider)
            clock = time.monotonic()
            if path_name == "agent":
                trace = TraceRecorder(case["claim"], model, provider=provider, secrets=secrets)
                try:
                    result = verify_claim(case["claim"], client, edgar, ledger, model, provider=provider,
                                          max_turns=6, max_output_tokens=3000, trace=trace, release_client=releases)
                    row = {**base, "status": "completed", "verdict": result.get("verdict"),
                           "result": result, "incomplete_turns": len(trace.incomplete_turns)}
                except Exception as exc:
                    error = "budget_exceeded" if isinstance(exc, BudgetExceeded) else type(exc).__name__
                    row = {**base, "status": "budget_stopped" if isinstance(exc, BudgetExceeded) else "failed", "error": error}
                    if isinstance(exc, BudgetExceeded):
                        stopped = "budget_exceeded"
                write(target / "trace.json", redact(trace.as_dict(), secrets))
                row["model_calls"] = trace.model_calls
                row["trace_cost_usd"] = trace.total_cost
            else:
                command = [sys.executable, "-m", "claimcheck", "post", str(out / "inputs" / f"{case['id']}.txt"),
                           "--provider", provider, "--model", model, "--budget", "10", "--max-claims", "8",
                           "--max-output-tokens", "3000", "--as-of", "2026-11-02", "--out", str(target)]
                env = dict(os.environ)
                # Do not inherit overrides capable of changing frozen model/policy settings.
                for key in ("CLAIMCHECK_REASONING_EFFORT", "CLAIMCHECK_MAX_OUTPUT_TOKENS"):
                    env.pop(key, None)
                env.update(CLAIMCHECK_CACHE_DIR=str(cache), CLAIMCHECK_RUNS_DIR=str(out),
                           SEC_USER_AGENT="DappGo market-claim-verifier admin@dappgo.com",
                           PYTHONPATH=os.pathsep.join([str(ROOT / "scripts/real_world/transport"), str(ROOT / "src")]),
                           PYTHONDONTWRITEBYTECODE="1")
                process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
                log = redact({"command": command, "started_at": base["started_at"], "finished_at": now(),
                              "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr}, secrets)
                write(target / "execution.json", log)
                if (target / "report.json").exists():
                    report = json.loads((target / "report.json").read_text())
                    verified = [c for c in report["claims"] if c.get("status") == "verified"]
                    verdict = ("contradicted" if any(c.get("verdict") == "contradicted" for c in verified)
                               else "supported" if verified and all(c.get("verdict") == "supported" for c in verified)
                               else "insufficient_evidence" if verified else None)
                    row = {**base, "status": "partial_failure" if report["counts"]["failed"] else "completed",
                           "verdict": verdict, "counts": report["counts"], "proposed_count": report["proposed_count"],
                           "verified_claims": len(verified), "any_supported": any(c.get("verdict") == "supported" for c in verified),
                           "not_checked_reasons": [c.get("screen_reason") for c in report["claims"] if c.get("status") != "verified"]}
                else:
                    budget_stop = "Post check refused:" in process.stderr and "budget" in process.stderr.lower()
                    row = {**base, "status": "budget_stopped" if budget_stop else "failed", "exit_code": process.returncode,
                           "error": "budget_exceeded" if budget_stop else "post_cli_failed"}
                    if budget_stop:
                        stopped = "budget_exceeded"
                traces = [json.loads(p.read_text()) for p in target.glob("traces/*.json")]
                row["model_calls"] = sum(t.get("model_calls", 0) for t in traces)
                row["trace_cost_usd"] = sum(t.get("cost_usd", 0) for t in traces)
            row.update(finished_at=now(), wall_seconds=round(time.monotonic() - clock, 6),
                       cost_usd=ledger.spent_for_provider(provider) - before)
            row = redact(row, secrets)
            write(target / "result.json", row)
            append(out / provider / path_name / "results.jsonl", row)
            print(f"{provider} {path_name} {case['id']} {row['status']} {row.get('verdict')} {row['wall_seconds']:.1f}s task=${ledger.spent_for_provider(provider):.6f}", flush=True)
    summary = {"provider": provider, "model": model, "started_at": started, "finished_at": now(),
               "cost_usd": ledger.spent_for_provider(provider), "budget_stop": stopped,
               "companyfacts_hashes": edgar.companyfacts_snapshot_hashes()}
    write(out / provider / "execution-summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--git-dir", type=Path)
    args = parser.parse_args()
    out, cache = args.out.resolve(), args.cache.resolve()
    if (out / "RUN_START.json").exists() or (out / "ledger.jsonl").exists():
        raise RuntimeError("paid attempt exists; do not overwrite or silently resume")
    proof = freeze_proof(out, args.git_dir)
    cache_manifest = json.loads((out / "runtime-cache-start.json").read_text())
    for provider in ("baseten", "fireworks", "meta"):
        for item in cache_manifest:
            path = cache / provider / item["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise RuntimeError(f"{provider}: frozen starting SEC cache mismatch")
    claims = [json.loads(line) for line in (out / "claims.jsonl").read_text().splitlines()]
    protocol = json.loads((out / "protocol.json").read_text())
    expected = protocol["execution"]["models"]
    for provider in ("baseten", "fireworks", "meta"):
        settings = load_settings(provider=provider)
        if not settings.model_api_key or settings.model != expected[provider]:
            raise RuntimeError(f"{provider}: missing key or unexpected model; no calls made")
    if any(os.environ.get(key) for key in ("CLAIMCHECK_REASONING_EFFORT", "CLAIMCHECK_MAX_OUTPUT_TOKENS")):
        raise RuntimeError("unset model generation overrides before starting")
    write(out / "RUN_START.json", {"started_at": now(), "gold_freeze": proof, "protocol_sha256": hashlib.sha256((out / "protocol.json").read_bytes()).hexdigest(),
                                    "prompt_versions": {p: prompt_versions_for(f"agent@{p}") for p in expected},
                                    "python": sys.version, "command": sys.argv})
    inputs = out / "inputs"
    inputs.mkdir(exist_ok=True)
    for claim in claims:
        (inputs / f"{claim['id']}.txt").write_text(claim["claim"] + "\n")
    with ThreadPoolExecutor(max_workers=3) as workers:
        futures = [workers.submit(run_provider, p, claims, out, cache / p) for p in expected]
        summaries = [f.result() for f in futures]
    write(out / "RUN_END.json", {"finished_at": now(), "providers": summaries})


if __name__ == "__main__":
    main()
