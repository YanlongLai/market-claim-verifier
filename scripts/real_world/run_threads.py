"""Execute phase-2 frozen Threads text and real images, with one $8/provider ledger.

Uses the same verifier, post CLI, generation settings and metrics as phase 1.
Media originals and verbatim OCR outputs remain in the ignored local run root.
Public media records contain numeric outcomes, hashes and request accounting.
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
from pathlib import Path

from run import ROOT, append, freeze_proof, now, write
from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.prompts import prompt_versions_for
from claimcheck.providers import get_provider
from claimcheck.release_fetch import ReleaseClient
from claimcheck.trace import TraceRecorder, redact

PROVIDERS = ("baseten", "fireworks", "meta")


def ledger_for(out, provider):
    return Ledger(out / "ledger.jsonl", provider=provider, budget_usd=8,
                  provider_budgets={p: 8 for p in PROVIDERS})


def cli(command, out, cache, started, secrets):
    env = dict(os.environ)
    for key in ("CLAIMCHECK_REASONING_EFFORT", "CLAIMCHECK_MAX_OUTPUT_TOKENS"):
        env.pop(key, None)
    env.update(CLAIMCHECK_CACHE_DIR=str(cache), CLAIMCHECK_RUNS_DIR=str(out),
               SEC_USER_AGENT="DappGo market-claim-verifier admin@dappgo.com",
               PYTHONPATH=os.pathsep.join([str(ROOT / "scripts/real_world/threads_transport"), str(ROOT / "src")]),
               PYTHONDONTWRITEBYTECODE="1", MCV_PHASE2_LEDGER=str(out / "ledger.jsonl"))
    p = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    return p, redact({"command": command, "started_at": started, "finished_at": now(),
                      "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}, secrets)


def post_result(report):
    checked = [c for c in report["claims"] if c.get("status") == "verified"]
    verdict = ("contradicted" if any(c.get("verdict") == "contradicted" for c in checked)
               else "supported" if checked and all(c.get("verdict") == "supported" for c in checked)
               else "insufficient_evidence" if checked else None)
    return {"status": "partial_failure" if report["counts"]["failed"] else "completed", "verdict": verdict,
            "counts": report["counts"], "proposed_count": report["proposed_count"], "verified_claims": len(checked),
            "any_supported": any(c.get("verdict") == "supported" for c in checked),
            "not_checked_reasons": [c.get("screen_reason") for c in report["claims"] if c.get("status") != "verified"]}


def public_media(local, target, provider, case, log, seconds, costs):
    """Allowlist public metadata; never copy OCR, headlines, images or payloads."""
    report = json.loads((local / "ingest.json").read_text()) if (local / "ingest.json").exists() else {}
    claims = [c for channel in report.get("channels", []) for c in channel.get("claims", [])]
    counts = {name: sum(c.get("status") == name for c in claims) for name in ("verified", "failed", "not_checked")}
    checked = [c for c in claims if c.get("status") == "verified"]
    verdicts = {name: sum(c.get("verdict") == name for c in checked) for name in ("supported", "contradicted", "insufficient_evidence")}
    verdict = "contradicted" if verdicts["contradicted"] else "supported" if checked and verdicts["supported"] == len(checked) else "insufficient_evidence" if checked else None
    row = {"id": case["id"], "provider": provider, "path": "ingest", "model": load_settings(provider=provider).model,
           "status": "completed" if report.get("status") == "completed" else "partial_failure" if report else "failed",
           "verdict": verdict, "any_supported": bool(verdicts["supported"]), "counts": counts, "verdicts": verdicts,
           "proposed_count": len(claims), "verified_claims": len(checked), "wall_seconds": seconds,
           "cost_usd": sum(costs.values()), "cost_by_billed_provider": costs, "coverage": report.get("coverage"),
           "started_at": log["started_at"], "finished_at": log["finished_at"], "input_sha256": case["sha256"],
           "raw_local_path": str(local), "raw_content_public": False}
    requests = []
    for p in sorted(local.rglob("*.json")):
        data = json.loads(p.read_text())
        for request in data.get("requests", []):
            requests.append({"reservation": request["reservation"], "status": request.get("status"),
                             "cost": request.get("cost"), "usage": request.get("usage"),
                             "raw_artifact": str(p.relative_to(local)), "artifact_sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        if p.parent.name == "calls":
            for attempt in data.get("attempts", []):
                requests.append({"reservation": attempt["reservation"], "status": attempt.get("status", "error"),
                                 "cost": attempt.get("cost_usd"), "usage": attempt.get("usage"),
                                 "error": attempt.get("error"), "raw_artifact": str(p.relative_to(local)),
                                 "artifact_sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    row["model_calls"] = len(requests)
    write(target / "result.json", row)
    write(target / "requests.json", requests)
    write(target / "execution.json", {k: log[k] for k in ("command", "started_at", "finished_at", "exit_code")})
    write(target / "local-artifacts.json", [{"path": str(p.relative_to(local)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
                                           for p in sorted(local.rglob("*")) if p.is_file()])
    return row


def run_media(out, cache, local):
    secrets = [load_settings(provider=p).model_api_key for p in PROVIDERS]
    for provider in PROVIDERS:
        ledger = ledger_for(out, provider)
        for case in sorted(json.loads((out / "media-inputs.json").read_text()), key=lambda c: c["id"]):
            target = out / "media" / provider / case["id"]
            raw = local / "media" / provider / case["id"]
            raw.mkdir(parents=True, exist_ok=False)
            started, clock = now(), time.monotonic()
            before = {p: ledger.spent_for_provider(p) for p in PROVIDERS}
            command = [sys.executable, "-m", "claimcheck", "ingest", case["input_local_path"], "--provider", provider,
                       "--model", load_settings(provider=provider).model, "--budget", "8", "--max-claims", "8",
                       "--max-output-tokens", "3000", "--as-of", "2026-11-02", "--out", str(raw)]
            process, log = cli(command, out, cache / provider, started, secrets)
            write(raw / "execution.json", log)
            costs = {p: ledger.spent_for_provider(p) - before[p] for p in PROVIDERS}
            row = public_media(raw, target, provider, case, log, round(time.monotonic() - clock, 6), costs)
            append(out / "media" / provider / "results.jsonl", row)
            print(f"{provider} ingest {case['id']} {row['status']} {row['verdict']} ${row['cost_usd']:.6f}", flush=True)


def run_text(provider, cases, out, cache):
    from openai import OpenAI
    settings = load_settings(provider=provider)
    secrets, ledger = [settings.model_api_key], ledger_for(out, provider)
    client = OpenAI(api_key=settings.model_api_key, base_url=get_provider(provider).base_url, max_retries=0, timeout=90)
    edgar = EdgarClient(cache, user_agent="DappGo market-claim-verifier admin@dappgo.com", as_of="2026-11-02")
    releases = ReleaseClient(cache, user_agent="DappGo market-claim-verifier admin@dappgo.com")
    stopped = None
    for path in ("agent", "post"):
        for case in cases:
            target = out / provider / path / case["id"]
            target.mkdir(parents=True, exist_ok=False)
            base = {"id": case["id"], "provider": provider, "path": path, "model": settings.model, "started_at": now(),
                    "status": "not_attempted", "verdict": None, "cost_usd": 0, "model_calls": 0, "wall_seconds": 0}
            if stopped:
                row = {**base, "status": "budget_stopped", "error": stopped, "finished_at": now()}
                write(target / "result.json", row); append(out / provider / path / "results.jsonl", row)
                continue
            before, clock = ledger.spent_for_provider(provider), time.monotonic()
            if path == "agent":
                trace = TraceRecorder(case["claim"], settings.model, provider=provider, secrets=secrets)
                try:
                    result = verify_claim(case["claim"], client, edgar, ledger, settings.model, provider=provider,
                                          max_turns=6, max_output_tokens=3000, trace=trace, release_client=releases)
                    row = {**base, "status": "completed", "verdict": result.get("verdict"), "result": result,
                           "incomplete_turns": len(trace.incomplete_turns)}
                except Exception as exc:
                    is_cap = isinstance(exc, BudgetExceeded)
                    row = {**base, "status": "budget_stopped" if is_cap else "failed", "error": "budget_exceeded" if is_cap else type(exc).__name__}
                    if is_cap:
                        stopped = "budget_exceeded"
                write(target / "trace.json", redact(trace.as_dict(), secrets))
                row.update(model_calls=trace.model_calls, trace_cost_usd=trace.total_cost)
            else:
                command = [sys.executable, "-m", "claimcheck", "post", str(out / "inputs" / f"{case['id']}.txt"),
                           "--provider", provider, "--model", settings.model, "--budget", "8", "--max-claims", "8",
                           "--max-output-tokens", "3000", "--as-of", "2026-11-02", "--out", str(target)]
                process, log = cli(command, out, cache, base["started_at"], secrets)
                write(target / "execution.json", log)
                if (target / "report.json").exists():
                    row = {**base, **post_result(json.loads((target / "report.json").read_text()))}
                else:
                    cap = "budget" in process.stderr.lower() and "Post check refused:" in process.stderr
                    row = {**base, "status": "budget_stopped" if cap else "failed", "exit_code": process.returncode, "error": "budget_exceeded" if cap else "post_cli_failed"}
                    if cap:
                        stopped = "budget_exceeded"
                traces = [json.loads(p.read_text()) for p in target.glob("traces/*.json")]
                row.update(model_calls=sum(t.get("model_calls", 0) for t in traces), trace_cost_usd=sum(t.get("cost_usd", 0) for t in traces))
            row.update(finished_at=now(), wall_seconds=round(time.monotonic() - clock, 6), cost_usd=ledger.spent_for_provider(provider) - before)
            row = redact(row, secrets)
            write(target / "result.json", row); append(out / provider / path / "results.jsonl", row)
            print(f"{provider} {path} {case['id']} {row['status']} {row.get('verdict')} {row['wall_seconds']:.1f}s task=${ledger.spent_for_provider(provider):.6f}", flush=True)
    summary = {"provider": provider, "model": settings.model, "finished_at": now(), "cost_usd": ledger.spent_for_provider(provider),
               "budget_stop": stopped, "companyfacts_hashes": edgar.companyfacts_snapshot_hashes()}
    write(out / provider / "execution-summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("out", "cache", "local", "git-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    out, cache, local = args.out.resolve(), args.cache.resolve(), args.local.resolve()
    if (out / "RUN_START.json").exists() or (out / "ledger.jsonl").exists():
        raise RuntimeError("paid attempt exists; no overwrite/resume")
    proof = freeze_proof(out, args.git_dir)
    protocol = json.loads((out / "protocol.json").read_text())
    for p, model in protocol["execution"]["models"].items():
        settings = load_settings(provider=p)
        if not settings.model_api_key or settings.model != model:
            raise RuntimeError("missing key or non-frozen model")
        for row in json.loads((out / "runtime-cache-start.json").read_text()):
            if hashlib.sha256((cache / p / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
                raise RuntimeError("starting cache mismatch")
    for media in json.loads((out / "media-inputs.json").read_text()):
        if hashlib.sha256(Path(media["input_local_path"]).read_bytes()).hexdigest() != media["sha256"]:
            raise RuntimeError("original media changed")
    if any(os.environ.get(k) for k in ("CLAIMCHECK_REASONING_EFFORT", "CLAIMCHECK_MAX_OUTPUT_TOKENS")):
        raise RuntimeError("generation overrides must be unset")
    write(out / "RUN_START.json", {"started_at": now(), "gold_freeze": proof, "command": sys.argv, "python": sys.version,
                                  "prompt_versions": {p: prompt_versions_for(f"agent@{p}") for p in PROVIDERS}})
    run_media(out, cache, local)
    cases = list(map(json.loads, (out / "claims.jsonl").read_text().splitlines()))
    with ThreadPoolExecutor(max_workers=3) as workers:
        summaries = list(workers.map(lambda p: run_text(p, cases, out, cache / p), PROVIDERS))
    write(out / "RUN_END.json", {"finished_at": now(), "providers": summaries})


if __name__ == "__main__":
    main()
