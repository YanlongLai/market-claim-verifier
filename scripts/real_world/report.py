"""Rebuild news evaluation metrics offline from frozen gold and every result.

Primary financial truth and scope-policy agreement are deliberately separate.
Missing/failed pairs count wrong; review cases remain in operational denominators.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

PROVIDERS = ("baseten", "fireworks", "meta")
PATHS = ("agent", "post")


def wilson(k: int, n: int):
    if not n:
        return None
    z = 1.959963984540054
    p, denominator = k / n, 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0, center - half), min(1, center + half)]


def rate(k, n):
    return {"numerator": k, "denominator": n, "rate": k / n if n else None, "wilson_95": wilson(k, n)}


def outcome(row):
    if row["status"] not in {"completed"}:
        return row["status"]
    if row.get("verdict"):
        return row["verdict"]
    return "skipped"


def summarize(cases, gold, results):
    rows = [results.get(case["id"], {"id": case["id"], "status": "missing", "cost_usd": 0, "wall_seconds": 0, "model_calls": 0}) for case in cases]
    primary = [row for row in rows if gold[row["id"]]["gold_basis"] == "primary_release"]
    scope = [row for row in rows if gold[row["id"]]["gold_basis"] == "scope_policy"]
    resolved = primary + scope
    correct = lambda row: row["status"] == "completed" and row.get("verdict") == gold[row["id"]]["gold_verdict"]
    scope_correct = lambda row: row["status"] == "completed" and row.get("verdict") in {None, "insufficient_evidence"} and not row.get("any_supported")
    primary_negatives = [row for row in primary if gold[row["id"]]["gold_verdict"] != "supported"]
    resolved_negatives = [row for row in resolved if gold[row["id"]]["gold_verdict"] != "supported"]
    supported = lambda row: row.get("verdict") == "supported" or row.get("any_supported", False)
    counts = Counter(outcome(row) for row in rows)
    attempted = [row for row in rows if row["status"] not in {"missing", "budget_stopped"} or row.get("wall_seconds", 0) > 0]
    latencies = sorted(row["wall_seconds"] for row in attempted)
    model_latencies = sorted(row["wall_seconds"] for row in attempted if row.get("model_calls", 0))
    cost = sum(row["cost_usd"] for row in rows)
    checks = sum(row.get("verified_claims", int(row.get("path") == "agent" and row in attempted)) for row in rows)
    n = len(rows)
    return {
        "items": n, "attempted_items": len(attempted), "outcomes": dict(counts),
        "primary_factual_accuracy": rate(sum(correct(row) for row in primary), len(primary)),
        "scope_expected_abstention_agreement": rate(sum(scope_correct(row) for row in scope), len(scope)),
        "mixed_verdict_agreement_NOT_broad_factual_accuracy": rate(sum(correct(row) for row in primary) + sum(scope_correct(row) for row in scope), len(resolved)),
        "review_unscored": sum(gold[row["id"]]["gold_basis"] == "review_required" for row in rows),
        "primary_false_supported_rate": rate(sum(supported(row) for row in primary_negatives), len(primary_negatives)),
        "false_supported_vs_scope_policy": rate(sum(supported(row) for row in scope), len(scope)),
        "contradicted_vs_scope_policy": rate(sum(row.get("verdict") == "contradicted" for row in scope), len(scope)),
        "decisive_outputs_vs_scope_policy": rate(sum(supported(row) or row.get("verdict") == "contradicted" for row in scope), len(scope)),
        "false_supported_vs_all_resolved_negative_gold": rate(sum(supported(row) for row in resolved_negatives), len(resolved_negatives)),
        "adjudicated_share": rate(counts["supported"] + counts["contradicted"], n),
        "insufficient_share": rate(counts["insufficient_evidence"], n),
        "skipped_share": rate(counts["skipped"], n),
        "unsupported_or_insufficient_share": rate(counts["insufficient_evidence"] + counts["skipped"], n),
        "failure_items": sum(row["status"] in {"failed", "partial_failure", "missing"} for row in rows),
        "budget_stopped_items": counts["budget_stopped"],
        "verified_claims_or_agent_attempts": checks,
        "zero_model_call_items": sum(row.get("model_calls", 0) == 0 for row in attempted),
        "post_items_with_proposals": sum(row.get("proposed_count", 0) > 0 for row in rows),
        "post_items_entering_verification": sum(row.get("verified_claims", 0) > 0 for row in rows),
        "proposed_claims": sum(row.get("proposed_count", 0) for row in rows),
        "post_claim_status_counts": dict(sum((Counter(row.get("counts", {})) for row in rows), Counter())),
        "incomplete_agent_turns": sum(row.get("incomplete_turns", 0) for row in rows),
        "model_calls": sum(row.get("model_calls", 0) for row in rows),
        "cost_usd": cost,
        "mean_cost_per_sampled_item_usd": cost / n if n else None,
        "mean_cost_per_attempted_item_usd": cost / len(attempted) if attempted else None,
        "mean_cost_per_verified_claim_or_agent_attempt_usd": cost / checks if checks else None,
        "latency_seconds": {"n": len(latencies), "mean": statistics.mean(latencies) if latencies else None,
                            "p50": statistics.median(latencies) if latencies else None,
                            "p95_nearest_rank": latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None},
        "latency_seconds_items_with_model_calls": {"n": len(model_latencies), "mean": statistics.mean(model_latencies) if model_latencies else None,
                                                   "p50": statistics.median(model_latencies) if model_latencies else None,
                                                   "p95_nearest_rank": model_latencies[math.ceil(.95 * len(model_latencies)) - 1] if model_latencies else None},
    }


def fmt_rate(value):
    n, k = value["denominator"], value["numerator"]
    if not n:
        return "not estimable (0 negative truth labels)"
    lo, hi = value["wilson_95"]
    return f"{k}/{n} ({100*k/n:.1f}%; {100*lo:.1f}–{100*hi:.1f}%)"


def breakdown(out: Path, name: str, field: str, cases, gold, results):
    lines = [f"# Descriptive breakdown by {name}", "", "Small, selected strata; no outlet credibility ranking. Accuracy below uses primary-source truth only; scope and review rows remain in operational counts. All groups are retained, including failures. Full Wilson intervals and cost/latency fields are in metrics.json.", "",
             "| Provider/path | Group | n | Supported | Contradicted | Insufficient | Skipped | Failed | Budget | Primary correct/n | Scope abstentions/n | Mean seconds | USD |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    blocks = {}
    for provider in PROVIDERS:
        for path in PATHS:
            key = f"{provider}/{path}"
            blocks[key] = {}
            for value in sorted({case[field] for case in cases}):
                subset = [case for case in cases if case[field] == value]
                block = summarize(subset, gold, results[key])
                blocks[key][value] = block
                counts, a, scope = block["outcomes"], block["primary_factual_accuracy"], block["scope_expected_abstention_agreement"]
                latency = block["latency_seconds"]["mean"]
                lines.append(f"| {key} | {value} | {len(subset)} | {counts.get('supported',0)} | {counts.get('contradicted',0)} | {counts.get('insufficient_evidence',0)} | {counts.get('skipped',0)} | {block['failure_items']} | {block['budget_stopped_items']} | {a['numerator']}/{a['denominator']} | {scope['numerator']}/{scope['denominator']} | {latency:.2f} | {block['cost_usd']:.6f} |" if latency is not None else
                             f"| {key} | {value} | {len(subset)} | {counts.get('supported',0)} | {counts.get('contradicted',0)} | {counts.get('insufficient_evidence',0)} | {counts.get('skipped',0)} | {block['failure_items']} | {block['budget_stopped_items']} | {a['numerator']}/{a['denominator']} | {scope['numerator']}/{scope['denominator']} | — | {block['cost_usd']:.6f} |")
    (out / f"BY_{name.upper()}.md").write_text("\n".join(lines) + "\n")
    return blocks


def build(out: Path):
    if not (out / "RUN_END.json").exists():
        raise RuntimeError("paid run is not complete; do not publish a final report")
    run_start = json.loads((out / "RUN_START.json").read_text())
    run_end = json.loads((out / "RUN_END.json").read_text())
    run_seconds = (datetime.fromisoformat(run_end["finished_at"]) - datetime.fromisoformat(run_start["started_at"])).total_seconds()
    cases = [json.loads(line) for line in (out / "claims.jsonl").read_text().splitlines()]
    gold = {row["id"]: row for row in map(json.loads, (out / "gold.jsonl").read_text().splitlines())}
    results, blocks = {}, {}
    for provider in PROVIDERS:
        for path in PATHS:
            key = f"{provider}/{path}"
            rows = [json.loads(line) for line in (out / provider / path / "results.jsonl").read_text().splitlines()]
            if len(rows) != len({row["id"] for row in rows}):
                raise ValueError("duplicate paid pair; never select a preferred attempt")
            results[key] = {row["id"]: row for row in rows}
            blocks[key] = summarize(cases, gold, results[key])
    events = [json.loads(line) for line in (out / "ledger.jsonl").read_text().splitlines()]
    ledger = {}
    for provider in PROVIDERS:
        reservations, reconciled = {}, {}
        for event in events:
            if event["provider"] != provider:
                continue
            target = reservations if event["event"] == "reserve" else reconciled
            target[event["reservation_id"]] = event["amount"]
        unknown_cost = sum(value for key, value in reservations.items() if key not in reconciled)
        trace_files = list((out / provider / "agent").glob("*/trace.json")) + list((out / provider / "post").glob("*/traces/*.json"))
        requests = [request for file in trace_files for request in json.loads(file.read_text())["requests"]]
        if Counter(request["reservation"]["reservation_id"] for request in requests) != Counter({key: 1 for key in reservations}):
            raise ValueError("request/reservation inventory differs")
        error_types = Counter(str((request.get("raw_response") or {}).get("error", "unknown")) for request in requests if request.get("status") == "error")
        ledger[provider] = {"cost_usd": sum(reconciled.values()) + unknown_cost,
                            "reconciled_cost_usd": sum(reconciled.values()), "unreconciled_reserved_usd": unknown_cost,
                            "request_status_counts": dict(Counter(request.get("status", "unknown") for request in requests)),
                            "request_error_types": dict(error_types), "transport_error_requests": sum(error_types.values()),
                            "reservations": len(reservations), "reconciled": len(reconciled),
                            "unreconciled_reservations": len(set(reservations) - set(reconciled)), "cap_usd": 10}
        row_cost = sum(blocks[f"{provider}/{path}"]["cost_usd"] for path in PATHS)
        if abs(row_cost - ledger[provider]["cost_usd"]) > 1e-8 or ledger[provider]["cost_usd"] > 10:
            raise ValueError("ledger/results mismatch or task cap exceeded")
    by_type = breakdown(out, "type", "claim_type", cases, gold, results)
    by_source = breakdown(out, "source", "outlet", cases, gold, results)
    metrics = {"systems": blocks, "ledger": ledger, "total_cost_usd": sum(row["cost_usd"] for row in ledger.values()),
               "run_wall_seconds": run_seconds, "started_at": run_start["started_at"], "finished_at": run_end["finished_at"],
               "sample": {"items": len(cases), "by_market": dict(Counter(c["market"] for c in cases)), "by_gold_basis": dict(Counter(g["gold_basis"] for g in gold.values()))},
               "by_type": by_type, "by_outlet": by_source,
               "by_sample_group": {key: {group: summarize([case for case in cases if case["sample_group"] == group], gold, results[key]) for group in ("numeric_financial", "support_control")} for key in results},
               "input_fidelity_sensitivity_posthoc_NOT_preregistered": {
                   "excluded_ids": ["RW020", "RW077"], "reason": "Confirmed company-name translation error (RW077), unresolved issuer attribution in a multi-company snippet (RW020); see PARAPHRASE_REVIEW.md. Original 80-case records/gold retained; no corrected-input paid rerun.",
                   "systems": {key: summarize([case for case in cases if case["id"] not in {"RW020", "RW077"}], gold, results[key]) for key in results}},
               "latency_basis": "Per attempted item wall time, including preflight zero-call abstentions and CLI startup; p50 median, p95 nearest rank. Budget-unattempted rows excluded. Shared preseeded SEC cache; providers ran in parallel, items serial within each provider. Times include model transport, local checks and live SEC/tool work. One pass per pair, not an isolated model-latency or throughput benchmark.",
               "cost_basis": "Existing reservation/reconciliation ledger token-price estimates; failed/unknown-usage reservations retained; not an invoice. Per-item means include all 80 expected items; per-verified-claim means allocate extraction and skipped-item costs to actual checks.",
               "accuracy_basis": "Four primary-source truth cases. 53 scope-only expected abstentions have unresolved factual truth. 23 ambiguous US financial cases excluded from accuracy and retained in coverage/cost. Mixed agreement is not broad financial accuracy; abstain-all baseline 53/57."}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    lines = ["# Real-world DappGo News evaluation — 2026-11-02", "",
             "The CURRENT agent was evaluated on 80 paraphrased feed stories (60 numerical financial items and 20 support controls), on Baseten, Fireworks and Meta API, through both the claim agent and the actual post CLI. This is primarily a support/coverage probe: only **four** stories have independently resolved SEC truth labels. **23 US financial items require Claude/Owner review**; **53 scope-policy labels measure expected abstention, not financial truth**. Do not interpret agreement on those scope labels as broad real-world accuracy.", "",
             "**Observed issuer error:** multiple direct-agent and post paths contradicted Hon Precision's revenue-growth claim using Honeywell (`HON`) companyfacts. This is an invalid issuer match, not successful TW coverage. A zero false-supported count does not exclude erroneous contradictions. [Traces and development priorities](findings.md).", "",
             "**Input-quality limit:** one control has a confirmed company-name translation error (RW077); one forecast has ambiguous issuer attribution (RW020). The frozen inputs remain as run. [Paraphrase errata and correction](PARAPHRASE_REVIEW.md) explain both; metrics.json separately reports a post-hoc 78-item sensitivity panel. Corrected-input behavior was not tested, and these cases must not be represented as faithful source paraphrases.", "",
             "[Frozen protocol](protocol.json) · [claims](claims.jsonl) · [gold](gold.jsonl) · [review list](GOLD_REVIEW.md) · [run start / commit proof](RUN_START.json) · [ledger](ledger.jsonl) · [metrics](metrics.json) · [future sources](NEXT_SOURCES.md)", "",
             "## Primary financial accuracy", "", "Failures and skipped positive cases count wrong. Wilson 95% intervals are shown; four cases are too few for a general accuracy claim. All four gold cases are supported: factual false-supported rate is **not estimable**, because there are no independently contradicted/insufficient truth cases.", "",
             "| Provider/path | Primary correct / 4 (Wilson 95%) | Scope abstention / 53 (Wilson 95%) | Mixed agreement / 57 | False supported vs scope / 53 |",
             "|---|---|---|---|---|"]
    for key, block in blocks.items():
        lines.append(f"| {key} | {fmt_rate(block['primary_factual_accuracy'])} | {fmt_rate(block['scope_expected_abstention_agreement'])} | {fmt_rate(block['mixed_verdict_agreement_NOT_broad_factual_accuracy'])} | {fmt_rate(block['false_supported_vs_scope_policy'])} |")
    lines += ["", "The mixed denominator excludes the 23 review cases. An always-abstain system scores 53/57 (93.0%) on that mixed panel, but 0/4 on primary truth. The false-supported column concerns expected scope behavior; it is not an estimate of factual misinformation detection. For posts, any supported extracted claim counts as false support on a scope item even if the overall post is insufficient. Scope contradictions and all decisive scope outputs are also retained in metrics.json.", "",
              "## Coverage, failures, speed and cost", "", "An adjudicated item has a program verdict of supported or contradicted. Merely running verification is not successful support. Skipped post items include no extracted claim, screening rejection and unsupported kinds; those are retained separately in metrics.json. Every expected item remains in coverage and cost denominators.", "",
              "| Provider/path | Supported | Contradicted | Insufficient | Skipped | Failed | Budget stopped | Mean / p50 / p95 seconds | USD total | USD/item | USD/check* |",
              "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|"]
    for key, block in blocks.items():
        c, latency = block["outcomes"], block["latency_seconds"]
        value = lambda v: f"{v:.2f}" if v is not None else "—"
        check_cost = block["mean_cost_per_verified_claim_or_agent_attempt_usd"]
        lines.append(f"| {key} | {c.get('supported',0)} | {c.get('contradicted',0)} | {c.get('insufficient_evidence',0)} | {c.get('skipped',0)} | {block['failure_items']} | {block['budget_stopped_items']} | {value(latency['mean'])} / {value(latency['p50'])} / {value(latency['p95_nearest_rank'])} | {block['cost_usd']:.6f} | {block['mean_cost_per_sampled_item_usd']:.6f} | {check_cost:.6f} |" if check_cost is not None else
                     f"| {key} | {c.get('supported',0)} | {c.get('contradicted',0)} | {c.get('insufficient_evidence',0)} | {c.get('skipped',0)} | {block['failure_items']} | {block['budget_stopped_items']} | {value(latency['mean'])} / {value(latency['p50'])} / {value(latency['p95_nearest_rank'])} | {block['cost_usd']:.6f} | {block['mean_cost_per_sampled_item_usd']:.6f} | — |")
    lines += ["", "*USD/check divides all path costs, including extraction/skips/failures, by agent attempted sentences or post claims actually sent to verification. Each source item contains one registered paraphrase. Post extraction counts, zero-output items, verification invocation counts and rejected/not-checked/failed claims are in metrics.json. Mean USD/item uses all 80 expected stories. No paid repeats were selected or substituted.", "",
              metrics["latency_basis"], "", f"The complete parallel run took {run_seconds / 60:.1f} minutes wall time ({run_start['started_at']} to {run_end['finished_at']}). This includes serial agent/post work within each provider; it is not the sum of item latencies across providers.", "", f"**Total estimated/reserved spend: ${metrics['total_cost_usd']:.6f}.** Each provider's task cap was $10 across both paths and all retries/failures. This is a token-price ledger estimate, not a provider invoice.", ""]
    lines += [f"- {p}: ${ledger[p]['cost_usd']:.6f}; {ledger[p]['reservations']} reservations, {ledger[p]['reconciled']} reconciliations (${ledger[p]['reconciled_cost_usd']:.6f}), {ledger[p]['unreconciled_reservations']} retained unknown-usage reservations (${ledger[p]['unreconciled_reserved_usd']:.6f})." for p in PROVIDERS]
    lines += ["", "Item failures above differ from request failures: successful application retries remain in the cost ledger and traces. Request outcomes are:", ""]
    lines += [f"- {p}: {ledger[p]['transport_error_requests']} transport-error requests; types {json.dumps(ledger[p]['request_error_types'], sort_keys=True)}; all request statuses {json.dumps(ledger[p]['request_status_counts'], sort_keys=True)}." for p in PROVIDERS]
    lines += ["", "Sub-millisecond direct-agent medians reflect zero-call preflight abstentions. They are not API response times. The following conditional latency includes only items that made model calls, including failed attempts; post startup and tool work remain included.", "",
              "| Provider/path | Zero-call items / 80 | Items with model calls | Mean / p50 / p95 seconds with model calls |",
              "|---|---:|---:|---|"]
    for key, block in blocks.items():
        latency = block["latency_seconds_items_with_model_calls"]
        value = lambda v: f"{v:.2f}" if v is not None else "—"
        lines.append(f"| {key} | {block['zero_model_call_items']} | {latency['n']} | {value(latency['mean'])} / {value(latency['p50'])} / {value(latency['p95_nearest_rank'])} |")
    lines += ["", "## Sampling and gold limitations", "",
              "The US pointer contained 299 ticker-associated story occurrences, deduplicated to 278 URLs; TW contained 443 unique URLs. Collection occurred on November 2 in America/Los_Angeles (November 3 UTC); the TW publication date is already November 3 in its market timezone. The publisher's logical hash differs from the delivered-byte hash: both are recorded, the immutable same-market path/hash prefix is validated, and payload data_hash matches the pointer. The first collector attempt's overstrict byte-equality rejection is retained in collection-attempt1.json; no model calls occurred during that correction.", "",
              "The seed/rule were locally committed before collection. Human screening used a supplementary financial vocabulary pass before gold, yielding 60 complete numerical financial assertions across both feeds. All 60 were retained. Controls were sampled by the same seeded source/ticker round-robin and screened before gold; three candidates were rejected for an investment plan, unnamed EPS estimate and non-assertion ticker page. Screening and handwritten paraphrasing can introduce selection/interpretation bias; this is not a random estimate of the entire feed. Many stories repeat a company's metric, so item-level Wilson intervals do not adjust for issuer/article correlation.", "",
              "Source outlets are the feed's labels (for example Yahoo), not independently identified original authors. Original headlines/summaries/full articles were not sent to the models or committed. Original payloads remain only under ignored .cache directories; cache-retention.json records the reusable local copy. The paraphrases were intended to preserve missing periods, values and qualification; PARAPHRASE_REVIEW.md identifies two post-freeze fidelity problems. Publication dates are not supplied as claim context. SEC primary-source snapshots are retained compressed under sources/ and runtime retrieval bytes separately. The agent received only the claim string, never gold, outlet, expected verdict or metric annotations.", "",
              "The four primary-source cases are UNH adjusted-EPS minimum guidance (8-K), ARCC investment income (8-K), Shell rounded net income (6-K), and Starbucks US comparable-sales growth (8-K). All four use L4 unaudited issuer-release evidence, not an independent audit of the companies' accounts. Gold was constructed with an independent standard-library HTML parser and Decimal comparisons, without importing the agent's numeric parser/checker. Shell's $12,057m attributable income and $12,145m total income both round to $12.1bn. Guidance gold confirms what the issuer said, not whether the forecast will come true.", "",
              "TW filings, third-party estimate histories, market prices and several segment measures are beyond the current retrieval domain. Scope-only gold has not validated their truth. A later reviewed-gold analysis must be separately named and keep these original gold/results unchanged. No original feed summarization fidelity, OCR/ASR, full-article ingestion, DappGo published articles, or Threads content was tested.", "",
              "## Inspect and reproduce", "",
              "[By source outlet](BY_SOURCE.md) · [By claim type](BY_TYPE.md) · [raw command output](execution.console.log) · [frozen input/runtime hashes](FREEZE.json). Each provider/path directory retains every item result, trace and post CLI command/exit/stdout/stderr. The run manifest names the local gold commit. Existing runtime models/prompts/product code were not changed for this probe; the CLI transport hook only sets SDK retries=0 and timeout=90s so application attempts remain visible to the ledger.", "",
              "Offline metric rebuild (no calls):", "", "```sh", "python3 scripts/real_world/report.py --out docs/evidence/real-world-2026-11-02", "```", "",
              "[Artifact audit](audit.json) · [runtime source hashes](runtime-sources.json) · [validation receipt](validation.json) · [local commit/bundle handoff](HANDOFF.md). Collector/sampler regression fixture is synthetic. The final validation receipt records the full suites and UV_OFFLINE=1 sh scripts/verify.sh. See findings.md for specific traces, development priorities and review requests.", ""]
    (out / "REPORT.md").write_text("\n".join(lines))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    metrics = build(args.out)
    print(json.dumps({"total_cost_usd": metrics["total_cost_usd"], "systems": {key: block["primary_factual_accuracy"] for key, block in metrics["systems"].items()}}, indent=2))
