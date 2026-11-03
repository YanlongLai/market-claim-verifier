"""POST-HOC FIX RECHECK of seen frozen News and/or Threads text inputs.

prepare --input-set news=docs/evidence/real-world-2026-11-02
Commit the prepared manifest before run --set news. Later prepare/run a Threads
set in the same output root: every set and failure shares the same $5/provider
ledger. Input directories supply claims.jsonl, gold.jsonl and (optionally)
metrics.json. Claims need unique safe IDs, claim text and published_at; feed
tickers are sampling metadata, never authenticated issuer identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from run import freeze_proof, now, run_provider, write
from report import summarize
from claimcheck.budget import Ledger
from claimcheck.config import load_settings
from claimcheck.providers import BASETEN_DEFAULT_MODEL, FIREWORKS_DEFAULT_MODEL, META_DEFAULT_MODEL

MODELS = dict(baseten=BASETEN_DEFAULT_MODEL, fireworks=FIREWORKS_DEFAULT_MODEL, meta=META_DEFAULT_MODEL)
CAP = 5.0
DEFAULT_OUT = ROOT / "docs/evidence/real-world-2026-11-03-fixcheck"
BASELINE = ROOT / "docs/evidence/real-world-2026-11-02"
WORKERS = 4


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cases_from(path):
    import re
    from datetime import date
    cases = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("empty or duplicate frozen cases")
    for c in cases:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", c["id"]) or not isinstance(c.get("claim"), str) or not c["claim"].strip():
            raise ValueError("safe case ID and nonempty text required")
        date.fromisoformat(c["published_at"][:10])
    return cases


def prepare(out, declaration):
    name, source = declaration.split("=", 1)
    if name not in {"news", "threads"}:
        raise ValueError("input set must be news or threads")
    source = Path(source).resolve()
    cases = cases_from(source / "claims.jsonl")
    gold = [json.loads(l) for l in (source / "gold.jsonl").read_text().splitlines()]
    if {g["id"] for g in gold} != {c["id"] for c in cases} or len(gold) != len(cases):
        raise ValueError("frozen gold/case inventory mismatch")
    target = out / "sets" / name
    target.mkdir(parents=True, exist_ok=False)
    for filename in ("claims.jsonl", "gold.jsonl"):
        shutil.copyfile(source / filename, target / filename)
    inputs = target / "inputs"
    inputs.mkdir()
    for c in cases:
        (inputs / f"{c['id']}.txt").write_text(c["claim"] + "\n")
    if (source / "metrics.json").exists():
        shutil.copyfile(source / "metrics.json", target / "before-metrics.json")
    protocol = {"label": "POST-HOC FIX RECHECK", "held_out": False,
                "disclosure": "These exact text inputs and original outcomes were seen before the fixes. This is development evidence, not a held-out result.",
                "prepared_at": now(), "set": name, "items": len(cases),
                "source_directory": str(source.relative_to(ROOT)),
                "models": MODELS, "budget_usd_per_provider": CAP,
                "ledger": str((out / "ledger.jsonl").relative_to(ROOT)),
                "budget_scope": "All News/Threads direct-agent and actual post-CLI calls, application retries, failures and unknown-usage reservations in this root. Stop at cap; no outcome-driven repeats.",
                "order": "Frozen input order, split by index modulo 4; each shard serial, agent then post. Four independent caches/workers per provider.",
                "workers_per_provider": WORKERS, "max_turns": 6, "max_output_tokens": 3000,
                "sdk_retries": 0, "request_timeout_seconds": 90,
                "application_retry_policy": "existing production retry policy; each attempt separately reserved",
                "context_change": "Original text bytes unchanged; publication date supplied separately. TW market is a coverage constraint, never an issuer identifier. Fiscal/calendar and filing-date resolution recorded as evidence.",
                "cutoff": "inclusive SEC filing date <= item publication date (ISO date component); no assertion about intra-day availability",
                "limits": ["No new gold review; original four primary positives, scope expectations and review-required labels preserved.",
                           "News contains handwritten paraphrases, not full articles. No OCR/ASR or feed-summary fidelity retest.",
                           "Concurrency and source-date context changed; before/after is not a causal model/provider comparison.",
                           "No Threads inputs available at News registration; later Threads execution must freeze a separate set and reuse this ledger."]}
    write(target / "protocol.json", protocol)
    sources = [*sorted((ROOT / "src/claimcheck").glob("*.py")), *sorted((ROOT / "prompts").glob("*.md")),
               *sorted((ROOT / "scripts/real_world").rglob("*.py")), ROOT / "uv.lock", ROOT / "pyproject.toml",
               ROOT / "tests/test_real_world_fixes.py", *sorted(out.glob("source-supplement*")),
               *sorted(target.glob("*.json*")), *sorted(inputs.glob("*.txt"))]
    # Freeze original evidence too, including archives used to seed the caches.
    sources += [p for p in source.rglob("*") if p.is_file()]
    write(target / "FREEZE.json", {"prepared_at": now(), "sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources}})
    print(f"Prepared {name}: {len(cases)} seen frozen inputs; commit manifest before paid execution.")


def retain_cache(cache, out):
    archive = out / "runtime-cache.tar.gz"
    with tarfile.open(archive, "x:gz") as tar:
        for p in sorted(cache.rglob("*")):
            if p.is_file() and not p.is_symlink():
                tar.add(p, arcname=str(p.relative_to(cache)), recursive=False)
    write(out / "runtime-cache.json", {"archive": archive.name, "sha256": digest(archive),
                                       "files": {str(p.relative_to(cache)): digest(p) for p in sorted(cache.rglob("*")) if p.is_file()}})


def execute(out, name, cache, git_dir):
    target = out / "sets" / name
    if (target / "RUN_START.json").exists():
        raise RuntimeError("attempt exists; never overwrite or resume a paid set")
    proof = freeze_proof(target, git_dir)
    protocol = json.loads((target / "protocol.json").read_text())
    if protocol["models"] != MODELS or protocol["budget_usd_per_provider"] != CAP or protocol["workers_per_provider"] != WORKERS:
        raise ValueError("unexpected frozen model/budget/protocol")
    for provider, model in MODELS.items():
        settings = load_settings(provider=provider)
        if settings.model != model or not settings.model_api_key:
            raise RuntimeError(f"{provider}: missing credential or nonregistered model; no calls made")
    import os
    if any(os.environ.get(k) for k in ("CLAIMCHECK_REASONING_EFFORT", "CLAIMCHECK_MAX_OUTPUT_TOKENS")):
        raise RuntimeError("generation overrides not permitted")
    cases = cases_from(target / "claims.jsonl")
    # Isolated worker caches avoid shared partial-write reads. Seed from the
    # retained original SEC snapshots, never the author's ignored global cache.
    cache.mkdir(parents=True, exist_ok=False)
    for provider in MODELS:
        for shard in range(WORKERS):
            location = cache / provider / str(shard)
            location.mkdir(parents=True)
            with tarfile.open(BASELINE / f"runtime-cache-{provider}.tar.gz") as tar:
                tar.extractall(location, filter="data")
            if (out / "source-supplement.json").exists():
                supplement = json.loads((out / "source-supplement.json").read_text())
                archive = out / supplement["archive"]
                if digest(archive) != supplement["archive_sha256"]:
                    raise ValueError("source supplement archive changed")
                with tarfile.open(archive) as tar:
                    tar.extractall(location, filter="data")
                if any(digest(location / p) != h for p, h in supplement["files"].items()):
                    raise ValueError("starting source supplement mismatch")
    write(target / "RUN_START.json", {"started_at": now(), "freeze": proof, "command": sys.argv,
                                      "starting_ledger_usd": {p: Ledger(out / "ledger.jsonl", provider=p).spent_for_provider(p) for p in MODELS}})
    errors, summaries = [], []
    with ThreadPoolExecutor(max_workers=WORKERS * len(MODELS)) as executor:
        jobs = {executor.submit(run_provider, p, cases[i::WORKERS], target, cache / p / str(i),
                                budget=CAP, published_context=True, ledger_path=out / "ledger.jsonl", worker_id=i): (p, i)
                for p in MODELS for i in range(WORKERS)}
        for future in as_completed(jobs):
            try:
                summaries.append(future.result())
            except Exception as exc:
                # Other workers finish; a failure is retained, never retried.
                errors.append({"worker": jobs[future], "error": type(exc).__name__, "message": str(exc)})
    write(target / "RUN_END.json", {"finished_at": now(), "workers": summaries, "errors": errors})
    retain_cache(cache, target)
    # Check that neither frozen inputs nor runtime were edited while running.
    freeze_proof(target, git_dir)
    build_report(out)


def build_report(out):
    ledger = Ledger(out / "ledger.jsonl")
    costs = {p: ledger.spent_for_provider(p) for p in MODELS}
    if any(v > CAP + 1e-9 for v in costs.values()):
        raise ValueError("provider budget exceeded")
    data, lines = {}, ["# POST-HOC FIX RECHECK", "", "**Inputs were seen before these fixes. This is not a held-out result.** Original text and gold are unchanged; publication-date context is now supplied. No OCR/ASR was retested.", "",
                       "One append-only ledger covers News and later Threads sets, including retries, failures and unreconciled reservations. Cap: $5 per provider.", "",
                       "| Set / provider / path | Primary SEC positives before → after | Supported / contradicted / insufficient after | Failed / stopped |", "|---|---:|---:|---:|"]
    for target in sorted((out / "sets").iterdir()):
        if not (target / "RUN_START.json").exists():
            continue
        cases = cases_from(target / "claims.jsonl")
        gold = {g["id"]: g for g in map(json.loads, (target / "gold.jsonl").read_text().splitlines())}
        before = json.loads((target / "before-metrics.json").read_text()).get("systems", {}) if (target / "before-metrics.json").exists() else {}
        blocks = {}
        for provider in MODELS:
            for path in ("agent", "post"):
                key = f"{provider}/{path}"
                records = {p.parent.name: json.loads(p.read_text()) for p in (target / provider / path).glob("*/result.json")}
                blocks[key] = summarize(cases, gold, records)
                b, a = before.get(key, {}).get("primary_factual_accuracy", {}), blocks[key]["primary_factual_accuracy"]
                counts = blocks[key]["outcomes"]
                lines.append(f"| {target.name}/{key} | {b.get('numerator', '—')}/{b.get('denominator', '—')} → {a['numerator']}/{a['denominator']} | {counts.get('supported', 0)} / {counts.get('contradicted', 0)} / {counts.get('insufficient_evidence', 0)} | {blocks[key]['failure_items']} / {blocks[key]['budget_stopped_items']} |")
        data[target.name] = {"systems": blocks, "items": len(cases)}
    lines += ["", "Costs include unknown-usage reservations (estimates, not invoices): " + ", ".join(f"{p} ${v:.6f}" for p, v in costs.items()) + ".", "",
              "The News truth panel has only four independently SEC-confirmed positives. The other labels are scope expectations or unresolved review cases. Before/after fixes, source-date context and execution concurrency changed together; these counts do not establish broad real-world accuracy or a hosting effect.", "",
              "News and Threads sets use separate frozen manifests under `sets/`; every trace, failed CLI exit and result is retained there. Four concurrent workers per provider share an atomically locked ledger. Original evidence remains under `../real-world-2026-11-02/`.", "",
              "Threads inputs are pending the phase-2 merge unless a frozen `sets/threads/` manifest is present. Add them with `prepare --input-set threads=PATH`, commit the manifest, then `run --set threads`; the same root ledger and remaining caps apply."]
    write(out / "metrics.json", {"label": "POST-HOC FIX RECHECK", "held_out": False, "sets": data, "ledger_usd": costs, "cap_usd_per_provider": CAP})
    (out / "REPORT.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "report"))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--input-set")
    parser.add_argument("--set", choices=("news", "threads"))
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--git-dir", type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.action == "prepare":
        prepare(out, args.input_set)
    elif args.action == "run":
        execute(out, args.set, args.cache.resolve(), args.git_dir)
    else:
        build_report(out)


if __name__ == "__main__":
    main()
