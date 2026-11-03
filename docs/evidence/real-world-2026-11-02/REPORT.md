# Real-world News and Threads evaluation — 2026-11-02

Phase 1 evaluated the CURRENT agent on 80 paraphrased feed stories (60 numerical financial items and 20 support controls), on Baseten, Fireworks and Meta API, through both the claim agent and the actual post CLI. This is primarily a support/coverage probe: only **four** stories have independently resolved SEC truth labels. **23 US financial items require Claude/Owner review**; **53 scope-policy labels measure expected abstention, not financial truth**. Do not interpret agreement on those scope labels as broad real-world accuracy.

**Observed issuer error:** multiple direct-agent and post paths contradicted Hon Precision's revenue-growth claim using Honeywell (`HON`) companyfacts. This is an invalid issuer match, not successful TW coverage. A zero false-supported count does not exclude erroneous contradictions. [Traces and development priorities](findings.md).

**Input-quality limit:** one control has a confirmed company-name translation error (RW077); one forecast has ambiguous issuer attribution (RW020). The frozen inputs remain as run. [Paraphrase errata and correction](PARAPHRASE_REVIEW.md) explain both; metrics.json separately reports a post-hoc 78-item sensitivity panel. Corrected-input behavior was not tested, and these cases must not be represented as faithful source paraphrases.

[Frozen protocol](protocol.json) · [claims](claims.jsonl) · [gold](gold.jsonl) · [review list](GOLD_REVIEW.md) · [run start / commit proof](RUN_START.json) · [ledger](ledger.jsonl) · [metrics](metrics.json) · [future sources](NEXT_SOURCES.md)

## Primary financial accuracy

Failures and skipped positive cases count wrong. Wilson 95% intervals are shown; four cases are too few for a general accuracy claim. All four gold cases are supported: factual false-supported rate is **not estimable**, because there are no independently contradicted/insufficient truth cases.

| Provider/path | Primary correct / 4 (Wilson 95%) | Scope abstention / 53 (Wilson 95%) | Mixed agreement / 57 | False supported vs scope / 53 |
|---|---|---|---|---|
| baseten/agent | 0/4 (0.0%; 0.0–49.0%) | 53/53 (100.0%; 93.2–100.0%) | 53/57 (93.0%; 83.3–97.2%) | 0/53 (0.0%; 0.0–6.8%) |
| baseten/post | 0/4 (0.0%; 0.0–49.0%) | 52/53 (98.1%; 90.1–99.7%) | 52/57 (91.2%; 81.1–96.2%) | 0/53 (0.0%; 0.0–6.8%) |
| fireworks/agent | 0/4 (0.0%; 0.0–49.0%) | 52/53 (98.1%; 90.1–99.7%) | 52/57 (91.2%; 81.1–96.2%) | 0/53 (0.0%; 0.0–6.8%) |
| fireworks/post | 0/4 (0.0%; 0.0–49.0%) | 52/53 (98.1%; 90.1–99.7%) | 52/57 (91.2%; 81.1–96.2%) | 0/53 (0.0%; 0.0–6.8%) |
| meta/agent | 0/4 (0.0%; 0.0–49.0%) | 51/53 (96.2%; 87.2–99.0%) | 51/57 (89.5%; 78.9–95.1%) | 0/53 (0.0%; 0.0–6.8%) |
| meta/post | 0/4 (0.0%; 0.0–49.0%) | 52/53 (98.1%; 90.1–99.7%) | 52/57 (91.2%; 81.1–96.2%) | 0/53 (0.0%; 0.0–6.8%) |

The mixed denominator excludes the 23 review cases. An always-abstain system scores 53/57 (93.0%) on that mixed panel, but 0/4 on primary truth. The false-supported column concerns expected scope behavior; it is not an estimate of factual misinformation detection. For posts, any supported extracted claim counts as false support on a scope item even if the overall post is insufficient. Scope contradictions and all decisive scope outputs are also retained in metrics.json.

## Coverage, failures, speed and cost

An adjudicated item has a program verdict of supported or contradicted. Merely running verification is not successful support. Skipped post items include no extracted claim, screening rejection and unsupported kinds; those are retained separately in metrics.json. Every expected item remains in coverage and cost denominators.

| Provider/path | Supported | Contradicted | Insufficient | Skipped | Failed | Budget stopped | Mean / p50 / p95 seconds | USD total | USD/item | USD/check* |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| baseten/agent | 0 | 0 | 80 | 0 | 0 | 0 | 7.14 / 0.00 / 23.01 | 0.800201 | 0.010003 | 0.010003 |
| baseten/post | 0 | 1 | 43 | 36 | 0 | 0 | 7.00 / 3.74 / 26.21 | 0.752567 | 0.009407 | 0.017104 |
| fireworks/agent | 0 | 1 | 79 | 0 | 0 | 0 | 26.47 / 0.00 / 98.08 | 0.824198 | 0.010302 | 0.010302 |
| fireworks/post | 0 | 1 | 42 | 36 | 1 | 0 | 37.41 / 22.75 / 148.06 | 0.763036 | 0.009538 | 0.017745 |
| meta/agent | 0 | 1 | 77 | 0 | 2 | 0 | 25.31 / 0.00 / 87.36 | 1.312080 | 0.016401 | 0.016401 |
| meta/post | 0 | 1 | 42 | 36 | 1 | 0 | 20.04 / 10.86 / 79.46 | 0.884040 | 0.011051 | 0.020559 |

*USD/check divides all path costs, including extraction/skips/failures, by agent attempted sentences or post claims actually sent to verification. Each source item contains one registered paraphrase. Post extraction counts, zero-output items, verification invocation counts and rejected/not-checked/failed claims are in metrics.json. Mean USD/item uses all 80 expected stories. No paid repeats were selected or substituted.

Per attempted item wall time, including preflight zero-call abstentions and CLI startup; p50 median, p95 nearest rank. Budget-unattempted rows excluded. Shared preseeded SEC cache; providers ran in parallel, items serial within each provider. Times include model transport, local checks and live SEC/tool work. One pass per pair, not an isolated model-latency or throughput benchmark.

The complete parallel run took 85.2 minutes wall time (2026-11-03T03:08:14.942418Z to 2026-11-03T04:33:27.089473Z). This includes serial agent/post work within each provider; it is not the sum of item latencies across providers.

**Total estimated/reserved spend: $5.336122.** Each provider's task cap was $10 across both paths and all retries/failures. This is a token-price ledger estimate, not a provider invoice.

- baseten: $1.552768; 227 reservations, 227 reconciliations ($1.552768), 0 retained unknown-usage reservations ($0.000000).
- fireworks: $1.587234; 221 reservations, 220 reconciliations ($1.569159), 1 retained unknown-usage reservations ($0.018075).
- meta: $2.196121; 252 reservations, 225 reconciliations ($1.770923), 27 retained unknown-usage reservations ($0.425198).

Item failures above differ from request failures: successful application retries remain in the cost ledger and traces. Request outcomes are:

- baseten: 0 transport-error requests; types {}; all request statuses {"completed": 224, "incomplete": 3}.
- fireworks: 1 transport-error requests; types {"APITimeoutError": 1}; all request statuses {"completed": 219, "error": 1, "incomplete": 1}.
- meta: 27 transport-error requests; types {"BadRequestError": 1, "InternalServerError": 26}; all request statuses {"completed": 218, "error": 27, "incomplete": 7}.

Sub-millisecond direct-agent medians reflect zero-call preflight abstentions. They are not API response times. The following conditional latency includes only items that made model calls, including failed attempts; post startup and tool work remain included.

| Provider/path | Zero-call items / 80 | Items with model calls | Mean / p50 / p95 seconds with model calls |
|---|---:|---:|---|
| baseten/agent | 45 | 35 | 16.33 / 11.94 / 46.83 |
| baseten/post | 0 | 80 | 7.00 / 3.74 / 26.21 |
| fireworks/agent | 45 | 35 | 60.50 / 45.46 / 174.39 |
| fireworks/post | 0 | 80 | 37.41 / 22.75 / 148.06 |
| meta/agent | 45 | 35 | 57.84 / 50.55 / 105.80 |
| meta/post | 0 | 80 | 20.04 / 10.86 / 79.46 |

## Sampling and gold limitations

The US pointer contained 299 ticker-associated story occurrences, deduplicated to 278 URLs; TW contained 443 unique URLs. Collection occurred on November 2 in America/Los_Angeles (November 3 UTC); the TW publication date is already November 3 in its market timezone. The publisher's logical hash differs from the delivered-byte hash: both are recorded, the immutable same-market path/hash prefix is validated, and payload data_hash matches the pointer. The first collector attempt's overstrict byte-equality rejection is retained in collection-attempt1.json; no model calls occurred during that correction.

The seed/rule were locally committed before collection. Human screening used a supplementary financial vocabulary pass before gold, yielding 60 complete numerical financial assertions across both feeds. All 60 were retained. Controls were sampled by the same seeded source/ticker round-robin and screened before gold; three candidates were rejected for an investment plan, unnamed EPS estimate and non-assertion ticker page. Screening and handwritten paraphrasing can introduce selection/interpretation bias; this is not a random estimate of the entire feed. Many stories repeat a company's metric, so item-level Wilson intervals do not adjust for issuer/article correlation.

Source outlets are the feed's labels (for example Yahoo), not independently identified original authors. Original headlines/summaries/full articles were not sent to the models or committed. Original payloads remain only under ignored .cache directories; cache-retention.json records the reusable local copy. The paraphrases were intended to preserve missing periods, values and qualification; PARAPHRASE_REVIEW.md identifies two post-freeze fidelity problems. Publication dates are not supplied as claim context. SEC primary-source snapshots are retained compressed under sources/ and runtime retrieval bytes separately. The agent received only the claim string, never gold, outlet, expected verdict or metric annotations.

The four primary-source cases are UNH adjusted-EPS minimum guidance (8-K), ARCC investment income (8-K), Shell rounded net income (6-K), and Starbucks US comparable-sales growth (8-K). All four use L4 unaudited issuer-release evidence, not an independent audit of the companies' accounts. Gold was constructed with an independent standard-library HTML parser and Decimal comparisons, without importing the agent's numeric parser/checker. Shell's $12,057m attributable income and $12,145m total income both round to $12.1bn. Guidance gold confirms what the issuer said, not whether the forecast will come true.

TW filings, third-party estimate histories, market prices and several segment measures are beyond the current retrieval domain. Scope-only gold has not validated their truth. A later reviewed-gold analysis must be separately named and keep these original gold/results unchanged. Phase 1 did not test original feed summarization fidelity, OCR/ASR, full-article ingestion, DappGo published articles or Threads content; the Threads and image extension is reported separately below.

## Inspect and reproduce

[By source outlet](BY_SOURCE.md) · [By claim type](BY_TYPE.md) · [raw command output](execution.console.log) · [frozen input/runtime hashes](FREEZE.json). Each provider/path directory retains every item result, trace and post CLI command/exit/stdout/stderr. The run manifest names the local gold commit. Existing runtime models/prompts/product code were not changed for this probe; the CLI transport hook only sets SDK retries=0 and timeout=90s so application attempts remain visible to the ledger.

Offline metric rebuild (no calls):

```sh
python3 scripts/real_world/report.py --out docs/evidence/real-world-2026-11-02
```

[Artifact audit](audit.json) · [runtime source hashes](runtime-sources.json) · [validation receipt](validation.json) · [local commit/bundle handoff](HANDOFF.md). Collector/sampler regression fixture is synthetic. The final validation receipt records the full suites and UV_OFFLINE=1 sh scripts/verify.sh. See findings.md for specific traces, development priorities and review requests.
