"""Rebuild phase-2 and combined source tables offline, retaining phase-1 results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from report import PROVIDERS, PATHS, fmt_rate, rate, summarize as phase1_summary

MARKER = "<!-- THREADS_PHASE2 -->"


def summarize(cases, gold, results):
    # A true extracted component of a false conjunction is not false support.
    # Keep phase-1 any-supported handling for scope items, where all support is
    # outside the intended domain. Primary false support uses aggregate verdict.
    scored = {}
    for id, row in results.items():
        score = dict(row)
        if gold[id]["gold_basis"] == "primary_release":
            score["any_supported"] = False
            if row["status"] != "completed":
                score["verdict"] = None
        scored[id] = score
    block = phase1_summary(cases, gold, scored)
    primary_negative = [c for c in cases if gold[c["id"]]["gold_basis"] == "primary_release" and gold[c["id"]]["gold_verdict"] == "contradicted"]
    block["any_supported_component_on_negative_post_NOT_false_support"] = rate(sum(bool(results.get(c["id"], {}).get("any_supported")) for c in primary_negative), len(primary_negative))
    block["negative_item_supported_output_exposure_phase1_definition"] = rate(sum(results.get(c["id"], {}).get("verdict") == 'supported' or bool(results.get(c["id"], {}).get("any_supported")) for c in primary_negative), len(primary_negative))
    block["items_with_extracted_proposals"] = sum(results.get(c["id"], {}).get("proposed_count", 0) > 0 for c in cases)
    block["items_with_verified_claims"] = sum(results.get(c["id"], {}).get("verified_claims", 0) > 0 for c in cases)
    block["extraction_item_coverage"] = rate(block["items_with_extracted_proposals"], len(cases))
    block["verification_item_coverage"] = rate(block["items_with_verified_claims"], len(cases))
    block["proposed_claims"] = sum(results.get(c["id"], {}).get("proposed_count", 0) for c in cases)
    block["supported_share"] = rate(block["outcomes"].get("supported", 0), len(cases))
    block["contradicted_share"] = rate(block["outcomes"].get("contradicted", 0), len(cases))
    return block


def load_rows(path):
    rows = list(map(json.loads, path.read_text().splitlines()))
    if len(rows) != len({r["id"] for r in rows}):
        raise ValueError("duplicate results; never choose a preferred attempt")
    return {r["id"]: r for r in rows}


def ledger_summary(out):
    events = list(map(json.loads, (out / "ledger.jsonl").read_text().splitlines()))
    reserved = {e["reservation_id"]: e for e in events if e["event"] == "reserve"}
    reconciled = {e["reservation_id"]: e for e in events if e["event"] == "reconcile"}
    blocks = {}
    for p in PROVIDERS:
        rows = [reconciled.get(id, e) for id, e in reserved.items() if e["provider"] == p]
        held = [e for id, e in reserved.items() if e["provider"] == p and id not in reconciled]
        blocks[p] = {"cost_usd": sum(e["amount"] for e in rows), "requests": len(rows),
                     "unreconciled_reserved_usd": sum(e["amount"] for e in held), "unreconciled_requests": len(held),
                     "cap_usd": 8, "cap_respected": sum(e["amount"] for e in rows) <= 8 + 1e-9}
    return blocks


def table_row(label, b):
    counts = b["outcomes"]
    return (f"| {label} | {b['items']} | {fmt_rate(b['primary_factual_accuracy'])} | {fmt_rate(b['primary_false_supported_rate'])} | "
            f"{b['scope_expected_abstention_agreement']['numerator']}/{b['scope_expected_abstention_agreement']['denominator']} | "
            f"{counts.get('supported',0)}/{counts.get('contradicted',0)}/{counts.get('insufficient_evidence',0)}/{counts.get('skipped',0)} | "
            f"{b['failure_items']}/{b['budget_stopped_items']} | {b['cost_usd']:.6f} |")


def findings(out):
    lines = ["# Threads findings and retained failures", "",
             "This is a selected real-input coverage probe. Five primary-source truth items cannot establish broad accuracy; review and scope labels have different meanings. No post-run product repair or outcome-driven paid repeat was made.", "",
             "## Independent truth cases", "", "| Case | Frozen gold | baseten/agent | baseten/post | fireworks/agent | fireworks/post | meta/agent | meta/post |",
             "|---|---|---|---|---|---|---|---|"]
    gold = load_rows(out / "gold.jsonl")
    for id in ("T02", "T03", "T09", "T19", "T33"):
        values = []
        for p in PROVIDERS:
            for path in PATHS:
                r = json.loads((out / p / path / id / "result.json").read_text())
                label = r.get("verdict") or "skipped"
                if r["status"] != "completed":
                    label = r["status"]
                values.append(f"[{label}]({p}/{path}/{id}/result.json)")
        lines.append(f"| {id} | {gold[id]['gold_verdict']} | " + " | ".join(values) + " |")
    lines += ["", "T02 is Alphabet's explicit Q3 2026 revenue and growth; T19 is AMD's explicit FY2026 Q2 revenue, growth, adjusted EPS, segment revenue and guidance. T03, T09 and T33 contain independently refuted unit or comparison-period components. Exact source coordinates/arithmetic are in [frozen gold](gold.jsonl). An insufficient response on a supported primary case counts wrong, even when abstention is safe operationally.", "",
              "## Issuer binding and scope", "",
              "[Baseten N03 trace](baseten/agent/N03/trace.json) maps **SM Entertainment**, a Korean issuer named in a KRW claim, to **SM ENERGY CO**, ticker `SM`, CIK `0000893538`, using USD facts and an unstated 2025 period. The resulting contradiction is an invalid issuer comparison. This repeats the kind of binding failure found in phase 1's Hon Precision → Honeywell case. A low false-supported rate does not exclude harmful false contradictions. The current production check validates selected evidence arithmetic without independently establishing that this is the company named by the input.", "",
              "Every decisive output on scope-only gold is listed below. These are operational disagreements, not independent truth adjudications of those posts.", "",
              "| Provider/path | Scope item | Aggregate verdict | Any supported extraction |",
              "|---|---|---|---|"]
    for p in PROVIDERS:
        for path in PATHS:
            for id, r in load_rows(out / p / path / "results.jsonl").items():
                if gold[id]["gold_basis"] == "scope_policy" and (r.get("verdict") in {"supported", "contradicted"} or r.get("any_supported")):
                    lines.append(f"| {p}/{path} | [{id}]({p}/{path}/{id}/result.json) | {r.get('verdict')} | {bool(r.get('any_supported'))} |")
    lines += ["", "## Media completion and privacy", "",
              "Each card ran through the actual image-ingest CLI once per verifier provider, with fresh Meta vision on every route. The authoring agent's visual review was frozen before paid OCR; no independent human reference transcript or truth adjudication was supplied. The frozen flag named `human_visual_review_before_ocr` is inaccurate provenance wording, corrected in [the media review notice](MEDIA_REVIEW_PROVENANCE.md) without changing original gold. Original cards and verbatim responses remain local and ignored. Public records retain request/reservation metadata and hashes of every full artifact.", "",
              "| Route | Status | OCR completed requests | Incomplete text requests | Proposals | Checked claims | Seconds | USD route |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for p in PROVIDERS:
        for id, r in load_rows(out / "media" / p / "results.jsonl").items():
            reqs = json.loads((out / "media" / p / id / "requests.json").read_text())
            ocr = sum(x['raw_artifact'].startswith('calls/') and x.get('status') == 'completed' for x in reqs)
            incomplete = sum(not x['raw_artifact'].startswith('calls/') and x.get('status') == 'incomplete' for x in reqs)
            lines.append(f"| [{p}/{id}](media/{p}/{id}/result.json) | {r['status']} | {ocr} | {incomplete} | {r['proposed_count']} | {r['verified_claims']} | {r['wall_seconds']:.2f} | {r['cost_usd']:.6f} |")
    lines += ["", "Media claim extraction uses the registered 3,000-token output limit (text-post extraction uses the phase-1 4,000-token default). Incomplete responses stay failures; no budget increase or repeated paid extraction was selected after observing them. OCR completion alone does not establish OCR fidelity. Text-only analysis of the frozen outputs would not retest image reading.", "",
              "## Translation and compound claims", "",
              "The report separately identifies T33's approximately tenfold Apple segment discrepancies, T03's CoreWeave unit/YTD problems, T09's sequential-versus-year-over-year growth and T10's unscored apparent unit-error candidate. Original-language causation was not verified. Preserve the shown input; do not silently replace it with a corrected number.", "",
              "Post-level supported means the checked extracted rows were all supported; unchecked source assertions can remain. Coverage is therefore reported separately from aggregate accuracy. True extracted components within a refuted compound post are counted in `any_supported_component_on_negative_post_NOT_false_support`, while an entirely supported aggregate on refuted gold is false support. Scope-only items retain phase-1's any-supported rule. Missing reporting years/metric definitions remain on the [review list](GOLD_REVIEW.md).", "",
              "## Follow-up work", "",
              "Bind issuer identity/currency before arithmetic; expose incomplete extraction as failed coverage; align every material component in compound posts; obtain explicit period context rather than guessing from publication dates; retain shown-language unit provenance. Start with offline replay of these retained failures. Future real audio/video uses [Owner-provided DappGo Reels/YouTube files](../NEXT_SOURCES.md), with independent references, frozen gold and a new explicit budget.", ""]
    (out / "FINDINGS.md").write_text("\n".join(lines))


def build(out):
    if not (out / "RUN_END.json").exists():
        raise RuntimeError("run incomplete; do not publish final metrics")
    parent = out.parent
    cases = list(map(json.loads, (out / "claims.jsonl").read_text().splitlines()))
    gold = load_rows(out / "gold.jsonl")
    media_gold = load_rows(out / "media-gold.jsonl")
    media_cases = [{"id": r["id"], "claim_type": "mixed_card", "scope": "financial_context_ambiguous", "source_group": "media"}
                   for r in json.loads((out / "media-inputs.json").read_text())]
    systems, by_source, by_type, by_scope, by_translation = {}, {}, {}, {}, {}
    for p in PROVIDERS:
        for path in PATHS:
            key = f"{p}/{path}"
            results = load_rows(out / p / path / "results.jsonl")
            if set(results) != {c["id"] for c in cases}:
                raise ValueError("missing or extra expected text pair")
            systems[key] = summarize(cases, gold, results)
            for field, store in [("source_group", by_source), ("claim_type", by_type), ("scope", by_scope), ("shown", by_translation)]:
                store[key] = {value: summarize([c for c in cases if c[field] == value], gold, results) for value in sorted({c[field] for c in cases})}
        results = load_rows(out / "media" / p / "results.jsonl")
        if set(results) != set(media_gold):
            raise ValueError("missing or extra expected image pair")
        systems[f"{p}/ingest"] = summarize(media_cases, media_gold, results)
        by_source[f"{p}/ingest"] = {"media": systems[f"{p}/ingest"]}
    ledger = ledger_summary(out)
    route_cost = sum(b["cost_usd"] for b in systems.values())
    ledger_cost = sum(b["cost_usd"] for b in ledger.values())
    if abs(route_cost - ledger_cost) > 1e-7 or not all(b["cap_respected"] for b in ledger.values()):
        raise ValueError("cost inventory/cap mismatch")
    news = json.loads((parent / "metrics.json").read_text())
    metrics = {"source": "Threads phase 2", "systems": systems, "by_source": by_source, "by_type": by_type,
               "by_scope": by_scope, "by_translation_display": by_translation, "ledger": ledger,
               "total_cost_usd": ledger_cost,
               "combined_phase1_phase2_cost_usd": news["total_cost_usd"] + ledger_cost,
               "gold_source_metadata": "Frozen gold.jsonl verdicts unchanged; quarterly/derived tier metadata corrected separately in gold-source-tiers-corrected.jsonl and GOLD_METADATA_ERRATA.md.",
               "cost_basis": "Configured token rates plus all retained reservations; not a provider invoice. Media route cost includes Meta OCR; ledger attributes it to Meta.",
               "latency_basis": "Observed wall time includes startup, retrieval/cache work and retries. Three provider workers ran concurrently; a guarded full product test suite overlapped part of execution. These are not isolated API/server latency measurements or a controlled speed ranking.",
               "primary_false_supported_definition": "Completed overall supported aggregate on an independently refuted item; true subclaims within false compound posts and incomplete/partial aggregates are not established false-supported statements without component alignment. Phase-1 any-supported exposure, including partial failures, is retained separately. Scope any-supported handling matches phase 1.",
               "coverage_limit": "Extracted rows and item coverage only; full-content recall unknown. Abstentions, skips, failures and all unattempted budget pairs stay in denominators."}
    (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n")
    header = ["| Source · provider/path | Items | Truth correct/n (Wilson 95%) | False supported/n (Wilson 95%) | Scope abstention/n | S/C/I/skip | Failed/budget | USD route |",
              "|---|---:|---|---|---:|---:|---:|---:|"]
    combined = list(header)
    for p in PROVIDERS:
        for path in PATHS:
            key = f"{p}/{path}"
            combined.append(table_row(f"News · {key}", news["systems"][key]))
            for source, label in [("own_posts", "Own posts"), ("third_party_threads", "Third-party Threads")]:
                combined.append(table_row(f"{label} · {key}", by_source[key][source]))
        combined.append(table_row(f"Media · {p}/ingest", systems[f"{p}/ingest"]))
    (parent / "COMBINED_SOURCES.md").write_text("# Combined source results\n\nRepeated issuer facts and media of two own posts are correlated. No pooled broad-accuracy score. Primary truth, scope expectations and unresolved items are separate. S/C/I = supported/contradicted/insufficient. Media route costs include Meta OCR.\n\n" + "\n".join(combined) + "\n")
    section = [MARKER, "## Threads", "",
               "Phase 2 evaluated **30 of 107 own posts, all 48 supplied third-party paraphrases, and two own-post cards through six actual image-ingest routes**. Owner-authorised logged-in browsing supplied the inputs; search used the **Top** tab and the four queries recorded in selection.json, collected November 2, 2026 in America/Los_Angeles. **No engagement metrics were recorded reliably**: this is a selected Top-search sample, not a measured high-engagement population. Supplied external dates include November 3; post dates are preserved as collected and are not fed to the models.", "",
               "[Phase-2 protocol](threads/protocol.json) · [protocol provenance errata](threads/PROTOCOL_METADATA_ERRATA.md) · [seed and full own-post population hashes](threads/selection.json) · [paraphrases](threads/claims.jsonl) · [gold](threads/gold.jsonl) · [review list](threads/GOLD_REVIEW.md) · [pre-call commit proof](threads/RUN_START.json) · [metrics](threads/metrics.json) · [ledger](threads/ledger.jsonl)", "",
               "The registered seed is `dappgo-threads-2026-11-02-v1`. Own-post selection uses post-type and ticker strata, plus two certainty selections corresponding to the supplied cards. Repeated issuers and subjects are not independent observations. Only paraphrases are public; original post bodies, cards and verbatim media extraction remain local and ignored. Ticker strata preserve the collection's labels and are not authenticated issuer identity. No additional Threads acquisition or third-party video download occurred.", "",
               "**Gold: five independent primary-source truth labels (two supported, three contradicted), 36 scope expectations, 37 unresolved review items.** All five truth cases are in the third-party sample; own posts have zero resolved truth cases (28 scope, two review), so their factual accuracy is not estimable. Both media cases remain review-only. Missing reporting years are never inferred from post dates. N07 remains review despite its collector N label: SEC releases can establish buyback authorizations, but dates are missing here. Annual 10-K facts (L1), quarterly 10-Q facts (L2), derived growth (L3), and release anchors (L4), exact coordinates, hashes, Decimal arithmetic and rounding are recorded. The frozen builder initially mislabelled quarterly facts and derived growth as L1; a [source-tier metadata erratum](threads/GOLD_METADATA_ERRATA.md) and [corrected metadata copy](threads/gold-source-tiers-corrected.jsonl) preserve all original bytes and unchanged verdict labels.", "",
               "Direct claims use one complete paraphrased item each, matching phase 1. The post CLI separately extracts up to eight claims. A contradiction in a known component refutes a compound item. Post accuracy uses the aggregate verdict; it does not establish that every statement was extracted. False-supported uses a completed overall supported verdict on independently refuted gold. Correctly supporting one true component of an otherwise false post is separately counted and is not itself false support. Partial-failure aggregates are not established factual false support without component alignment; their supported-output exposure remains in metrics under the phase-1 definition. Any supported extraction on an entirely out-of-scope item still counts as false support versus scope. Failures and budget stops count wrong; review items remain in coverage and cost denominators. [Scoring clarification](threads/SCORING_NOTE.json).", "",
               "The compound-item false-support interpretation was clarified during execution; both the phase-1 supported-output exposure and the completed whole-item count remain available. This reporting clarification did not change frozen truth labels or discard outcomes. The timestamps and post-result counts at clarification are retained in SCORING_NOTE.json.", "",
               "### Combined table across sources", "", *combined, "",
               "Wilson 95% intervals are descriptive and do not adjust for repeated issuers or overlapping cards. A dash means no eligible denominator, not zero error. News retains its original four truth labels and input-quality errata; phase-2 results do not replace phase 1. There is no pooled broad financial-accuracy claim.", "",
               "### Threads extraction, latency and cost", "",
               "| Provider/path | Extracted items/n | Checked items/n | Extracted rows | Checked rows/agent attempts | Calls | Mean/p50/p95 seconds | Mean/p50/p95 with calls | USD |",
               "|---|---:|---:|---:|---:|---:|---|---|---:|"]
    for key, b in systems.items():
        lat, model_lat = b["latency_seconds"], b["latency_seconds_items_with_model_calls"]
        def times(x):
            return " / ".join(f"{x[k]:.2f}" if x[k] is not None else "—" for k in ("mean", "p50", "p95_nearest_rank"))
        extracted = f"{b['items_with_extracted_proposals']}/{b['items']}" if not key.endswith('/agent') else "—"
        checked = f"{b['items_with_verified_claims']}/{b['items']}" if not key.endswith('/agent') else "—"
        section.append(f"| {key} | {extracted} | {checked} | {b['proposed_claims']} | {b['verified_claims_or_agent_attempts']} | {b['model_calls']} | {times(lat)} | {times(model_lat)} | {b['cost_usd']:.6f} |")
    section += ["", "Coverage counts extracted rows and items, not unique facts or full-content recall. Direct-agent zero-call scope abstentions are included in all-item latency; conditional latency isolates items making model calls. Startup, retrieval and retries remain included. Provider workers ran concurrently, and guarded product validation overlapped part of execution; this is not an isolated API/server speed benchmark. Metrics include Wilson intervals and operational/cost/latency breakdowns by claim type, scope, source and translation display. [Readable breakdowns](threads/BREAKDOWNS.md).", "",
                "| Provider/path | False supported vs scope (Wilson 95%) | Contradicted vs scope (Wilson 95%) | Supported-output exposure on negative truth items, phase-1 rule | Review items unscored |",
                "|---|---|---|---|---:|"]
    for key, b in systems.items():
        section.append(f"| {key} | {fmt_rate(b['false_supported_vs_scope_policy'])} | {fmt_rate(b['contradicted_vs_scope_policy'])} | {fmt_rate(b['negative_item_supported_output_exposure_phase1_definition'])} | {b['review_unscored']} |")
    section += ["",
                "| Billed provider | Phase 2 USD | Retained unreconciled USD | Requests | Cap | Phase 1 + 2 USD |",
                "|---|---:|---:|---:|---:|---:|"]
    for p, b in ledger.items():
        phase1 = news["ledger"][p]["cost_usd"]
        section.append(f"| {p} | {b['cost_usd']:.6f} | {b['unreconciled_reserved_usd']:.6f} | {b['requests']} | 8.00 | {phase1+b['cost_usd']:.6f} |")
    section += ["", f"**Phase-2 total estimated/reserved spend: ${ledger_cost:.6f}; both phases: ${metrics['combined_phase1_phase2_cost_usd']:.6f}.** Includes all failures/retries, and Meta vision on every media route; not a provider invoice. A locked shared ledger enforces the $8 phase-2 cap separately for each billed provider. Prior News authorization and costs are separate.", "",
                "### Translation and units", "",
                "The shown auto-translated text introduces an important evaluation layer: the displayed claim can contain a financial-number error even when the original author may not have written it. We have the collector's paraphrase and shown-language flag, not a paired original-language archive, so we cannot prove which errors were introduced by Threads translation.", "",
                "- **T33, confirmed displayed unit errors:** the SEC Apple release reports fiscal Q4 2026 iPhone revenue of $57,583 million and Greater China revenue of $17,539 million. The shown paraphrase says $575.8 billion and $175.4 billion, roughly ten times those amounts. Total revenue $114.48 billion, EPS $2.10 and 12% growth agree at the stated precision. [Exact source anchors](threads/gold.jsonl).",
                "- **T03, confirmed displayed numeric/period errors:** CoreWeave's $229 million 2023 and $5.131 billion 2025 revenue are shown as $2.29 billion and $51.31 billion. Its stated $4.653 billion Q1 2026 figure matches the six-month total; the quarter alone is $2.078 billion. The 2022 statement remains unverified, while the other explicit-year errors suffice to refute the conjunction.",
                "- **T09, comparison-period error:** SanDisk's 23% growth is sequential; its fiscal Q1 2027 year-over-year growth is 378%. The supplied paraphrase labels 23% as year over year. Both revenue and adjusted EPS agree with the release at their stated precision.",
                "- **T10, apparent unit-error candidate, unscored:** the shown Apple Q4 revenue is $1.144 billion, but no reporting year is given. It resembles an 億-to-billion conversion error relative to the latest release; the missing year prevents a primary gold label. Other translated posts with suspicious units remain on the review list rather than receiving inferred corrections.", "",
                "These are observed display-layer problems, not an estimated error prevalence for Threads or a ranking of authors. Top-search selection, paraphrasing and translation can each affect the tested input. [Full interpretation and retained failures](threads/FINDINGS.md).", "",
                "### Media and next inputs", "",
                "The two genuine cards were visually reviewed before paid OCR, then each passed through `claimcheck ingest` with Baseten, Fireworks and Meta verification. All six routes use fresh Meta vision; this is not a native image-model comparison. Images contain market prices, technical commentary, financing and a cloud-order backlog without enough reporting context for financial truth gold. Media accuracy and OCR recall are therefore not estimable; operational extraction/checking, errors, latency and cost are reported. They overlap own posts O04/O20 and are not additional independent facts.", "",
                "Public media artifacts are allowlisted numeric outcomes, coverage, commands and request/reservation metadata with SHA-256 links to full local artifacts. Original cards, verbatim OCR, full responses and traces are retained under ignored `runs/threads-phase2/media/`; they are not copied into the evidence corpus. The authoring agent performed the pre-OCR visual review; the frozen flag calling it human review is corrected in the [provenance notice](threads/MEDIA_REVIEW_PROVENANCE.md). No independent human transcript was supplied. [Media input hashes](threads/media-inputs.json) · [pre-OCR gold/review notes](threads/media-gold.jsonl).", "",
                "[Owner-provided Reels and YouTube audio/video plan](NEXT_SOURCES.md). No new real audio/video input was available for phase 2; no third-party video was downloaded.", "",
                "Offline rebuild: `python3 scripts/real_world/report_threads.py --out docs/evidence/real-world-2026-11-02/threads`. [Offline reuse and retained artifacts](threads/REUSE.md) · [artifact audit](threads/audit.json) · [validation](threads/validation.json) · [Git handoff](HANDOFF.md).", ""]
    existing = (parent / "REPORT.md").read_text().split(MARKER)[0].rstrip()
    (parent / "REPORT.md").write_text(existing + "\n\n" + "\n".join(section))
    (out / "REPORT.md").write_text("# Threads phase 2\n\nThe complete report, source comparison, limits and spend are in the [Threads section](../REPORT.md#threads).\n\n[Metrics](metrics.json) · [findings](FINDINGS.md) · [audit](audit.json) · [validation](validation.json)\n")
    lines = ["# Threads breakdowns", "", "All selected strata retained. Primary truth excludes scope and review. Small selected samples; no credibility ranking. Full Wilson intervals, latency and costs are in metrics.json.", ""]
    coverage_header = [header[0] + " Extracted items/n | Checked items/n | Mean seconds |",
                       header[1] + "---:|---:|---:|"]
    for title, store in [("Claim type", by_type), ("Scope", by_scope), ("Translation display", by_translation)]:
        lines += [f"## {title}", "", *coverage_header]
        for key, groups in store.items():
            for group, block in groups.items():
                extracted = f"{block['items_with_extracted_proposals']}/{block['items']}" if not key.endswith('/agent') else "—"
                checked = f"{block['items_with_verified_claims']}/{block['items']}" if not key.endswith('/agent') else "—"
                mean = block["latency_seconds"]["mean"]
                latency = f"{mean:.2f}" if mean is not None else "—"
                lines.append(table_row(f"{group} · {key}", block) + f" {extracted} | {checked} | {latency} |")
        lines.append("")
    (out / "BREAKDOWNS.md").write_text("\n".join(lines))
    # Synthetic report tests use budget-stopped rows without per-item artifacts.
    if (out / "baseten/agent/N03/trace.json").exists():
        findings(out)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print(json.dumps({"total_cost_usd": build(parser.parse_args().out)["total_cost_usd"]}))
