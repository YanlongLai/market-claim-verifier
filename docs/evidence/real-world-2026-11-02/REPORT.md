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

<!-- THREADS_PHASE2 -->
## Threads

Phase 2 evaluated **30 of 107 own posts, all 48 supplied third-party paraphrases, and two own-post cards through six actual image-ingest routes**. Owner-authorised logged-in browsing supplied the inputs; search used the **Top** tab and the four queries recorded in selection.json, collected November 2, 2026 in America/Los_Angeles. **No engagement metrics were recorded reliably**: this is a selected Top-search sample, not a measured high-engagement population. Supplied external dates include November 3; post dates are preserved as collected and are not fed to the models.

[Phase-2 protocol](threads/protocol.json) · [protocol provenance errata](threads/PROTOCOL_METADATA_ERRATA.md) · [seed and full own-post population hashes](threads/selection.json) · [paraphrases](threads/claims.jsonl) · [gold](threads/gold.jsonl) · [review list](threads/GOLD_REVIEW.md) · [pre-call commit proof](threads/RUN_START.json) · [metrics](threads/metrics.json) · [ledger](threads/ledger.jsonl)

The registered seed is `dappgo-threads-2026-11-02-v1`. Own-post selection uses post-type and ticker strata, plus two certainty selections corresponding to the supplied cards. Repeated issuers and subjects are not independent observations. Only paraphrases are public; original post bodies, cards and verbatim media extraction remain local and ignored. Ticker strata preserve the collection's labels and are not authenticated issuer identity. No additional Threads acquisition or third-party video download occurred.

**Gold: five independent primary-source truth labels (two supported, three contradicted), 36 scope expectations, 37 unresolved review items.** All five truth cases are in the third-party sample; own posts have zero resolved truth cases (28 scope, two review), so their factual accuracy is not estimable. Both media cases remain review-only. Missing reporting years are never inferred from post dates. N07 remains review despite its collector N label: SEC releases can establish buyback authorizations, but dates are missing here. Annual 10-K facts (L1), quarterly 10-Q facts (L2), derived growth (L3), and release anchors (L4), exact coordinates, hashes, Decimal arithmetic and rounding are recorded. The frozen builder initially mislabelled quarterly facts and derived growth as L1; a [source-tier metadata erratum](threads/GOLD_METADATA_ERRATA.md) and [corrected metadata copy](threads/gold-source-tiers-corrected.jsonl) preserve all original bytes and unchanged verdict labels.

Direct claims use one complete paraphrased item each, matching phase 1. The post CLI separately extracts up to eight claims. A contradiction in a known component refutes a compound item. Post accuracy uses the aggregate verdict; it does not establish that every statement was extracted. False-supported uses a completed overall supported verdict on independently refuted gold. Correctly supporting one true component of an otherwise false post is separately counted and is not itself false support. Partial-failure aggregates are not established factual false support without component alignment; their supported-output exposure remains in metrics under the phase-1 definition. Any supported extraction on an entirely out-of-scope item still counts as false support versus scope. Failures and budget stops count wrong; review items remain in coverage and cost denominators. [Scoring clarification](threads/SCORING_NOTE.json).

The compound-item false-support interpretation was clarified during execution; both the phase-1 supported-output exposure and the completed whole-item count remain available. This reporting clarification did not change frozen truth labels or discard outcomes. The timestamps and post-result counts at clarification are retained in SCORING_NOTE.json.

### Combined table across sources

| Source · provider/path | Items | Truth correct/n (Wilson 95%) | False supported/n (Wilson 95%) | Scope abstention/n | S/C/I/skip | Failed/budget | USD route |
|---|---:|---|---|---:|---:|---:|---:|
| News · baseten/agent | 80 | 0/4 (0.0%; 0.0–49.0%) | not estimable (n=0) | 53/53 | 0/0/80/0 | 0/0 | 0.800201 |
| Own posts · baseten/agent | 30 | not estimable (n=0) | not estimable (n=0) | 27/28 | 0/1/29/0 | 0/0 | 0.669635 |
| Third-party Threads · baseten/agent | 48 | 2/5 (40.0%; 11.8–76.9%) | 0/3 (0.0%; 0.0–56.1%) | 7/8 | 1/9/38/0 | 0/0 | 1.263137 |
| News · baseten/post | 80 | 0/4 (0.0%; 0.0–49.0%) | not estimable (n=0) | 52/53 | 0/1/43/36 | 0/0 | 0.752567 |
| Own posts · baseten/post | 30 | not estimable (n=0) | not estimable (n=0) | 27/28 | 0/0/3/26 | 1/0 | 0.245060 |
| Third-party Threads · baseten/post | 48 | 3/5 (60.0%; 23.1–88.2%) | 0/3 (0.0%; 0.0–56.1%) | 7/8 | 1/2/36/4 | 5/0 | 1.106817 |
| Media · baseten/ingest | 2 | not estimable (n=0) | not estimable (n=0) | 0/0 | 0/0/0/0 | 2/0 | 0.044425 |
| News · fireworks/agent | 80 | 0/4 (0.0%; 0.0–49.0%) | not estimable (n=0) | 52/53 | 0/1/79/0 | 0/0 | 0.824198 |
| Own posts · fireworks/agent | 30 | not estimable (n=0) | not estimable (n=0) | 24/28 | 0/1/25/0 | 4/0 | 0.746174 |
| Third-party Threads · fireworks/agent | 48 | 2/5 (40.0%; 11.8–76.9%) | 0/3 (0.0%; 0.0–56.1%) | 6/8 | 1/6/34/0 | 7/0 | 1.309770 |
| News · fireworks/post | 80 | 0/4 (0.0%; 0.0–49.0%) | not estimable (n=0) | 52/53 | 0/1/42/36 | 1/0 | 0.763036 |
| Own posts · fireworks/post | 30 | not estimable (n=0) | not estimable (n=0) | 24/28 | 0/0/3/23 | 4/0 | 0.365325 |
| Third-party Threads · fireworks/post | 48 | 3/5 (60.0%; 23.1–88.2%) | 0/3 (0.0%; 0.0–56.1%) | 6/8 | 1/2/28/3 | 14/0 | 0.880469 |
| Media · fireworks/ingest | 2 | not estimable (n=0) | not estimable (n=0) | 0/0 | 0/0/0/0 | 2/0 | 0.041444 |
| News · meta/agent | 80 | 0/4 (0.0%; 0.0–49.0%) | not estimable (n=0) | 51/53 | 0/1/77/0 | 2/0 | 1.312080 |
| Own posts · meta/agent | 30 | not estimable (n=0) | not estimable (n=0) | 28/28 | 0/0/30/0 | 0/0 | 0.960251 |
| Third-party Threads · meta/agent | 48 | 2/5 (40.0%; 11.8–76.9%) | 0/3 (0.0%; 0.0–56.1%) | 8/8 | 1/5/42/0 | 0/0 | 1.367081 |
| News · meta/post | 80 | 0/4 (0.0%; 0.0–49.0%) | not estimable (n=0) | 52/53 | 0/1/42/36 | 1/0 | 0.884040 |
| Own posts · meta/post | 30 | not estimable (n=0) | not estimable (n=0) | 26/28 | 0/0/1/27 | 2/0 | 0.275964 |
| Third-party Threads · meta/post | 48 | 3/5 (60.0%; 23.1–88.2%) | 0/3 (0.0%; 0.0–56.1%) | 6/8 | 1/2/26/3 | 16/0 | 1.219663 |
| Media · meta/ingest | 2 | not estimable (n=0) | not estimable (n=0) | 0/0 | 0/0/0/0 | 2/0 | 0.042025 |

Wilson 95% intervals are descriptive and do not adjust for repeated issuers or overlapping cards. A dash means no eligible denominator, not zero error. News retains its original four truth labels and input-quality errata; phase-2 results do not replace phase 1. There is no pooled broad financial-accuracy claim.

### Threads extraction, latency and cost

| Provider/path | Extracted items/n | Checked items/n | Extracted rows | Checked rows/agent attempts | Calls | Mean/p50/p95 seconds | Mean/p50/p95 with calls | USD |
|---|---:|---:|---:|---:|---:|---|---|---:|
| baseten/agent | — | — | 0 | 78 | 162 | 13.39 / 11.10 / 46.37 | 23.20 / 17.95 / 52.98 | 1.932772 |
| baseten/post | 62/78 | 42/78 | 123 | 96 | 156 | 11.21 / 6.76 / 52.02 | 11.21 / 6.76 / 52.02 | 1.351878 |
| baseten/ingest | 0/2 | 0/2 | 0 | 0 | 4 | 21.12 / 21.12 / 22.00 | 21.12 / 21.12 / 22.00 | 0.044425 |
| fireworks/agent | — | — | 0 | 78 | 148 | 87.68 / 76.97 / 273.31 | 151.98 / 113.35 / 319.52 | 2.055944 |
| fireworks/post | 50/78 | 34/78 | 92 | 71 | 123 | 74.75 / 63.43 / 174.28 | 74.75 / 63.43 / 174.28 | 1.245794 |
| fireworks/ingest | 0/2 | 0/2 | 0 | 0 | 3 | 74.07 / 74.07 / 111.30 | 74.07 / 74.07 / 111.30 | 0.041444 |
| meta/agent | — | — | 0 | 78 | 178 | 43.66 / 37.30 / 140.24 | 75.67 / 68.18 / 149.65 | 2.327332 |
| meta/post | 50/78 | 30/78 | 76 | 52 | 132 | 29.37 / 21.02 / 85.65 | 29.37 / 21.02 / 85.65 | 1.495628 |
| meta/ingest | 0/2 | 0/2 | 0 | 0 | 4 | 36.82 / 36.82 / 37.91 | 36.82 / 36.82 / 37.91 | 0.042025 |

Coverage counts extracted rows and items, not unique facts or full-content recall. Direct-agent zero-call scope abstentions are included in all-item latency; conditional latency isolates items making model calls. Startup, retrieval and retries remain included. Provider workers ran concurrently, and guarded product validation overlapped part of execution; this is not an isolated API/server speed benchmark. Metrics include Wilson intervals and operational/cost/latency breakdowns by claim type, scope, source and translation display. [Readable breakdowns](threads/BREAKDOWNS.md).

| Provider/path | False supported vs scope (Wilson 95%) | Contradicted vs scope (Wilson 95%) | Supported-output exposure on negative truth items, phase-1 rule | Review items unscored |
|---|---|---|---|---:|
| baseten/agent | 0/36 (0.0%; 0.0–9.6%) | 2/36 (5.6%; 1.5–18.1%) | 0/3 (0.0%; 0.0–56.1%) | 37 |
| baseten/post | 0/36 (0.0%; 0.0–9.6%) | 0/36 (0.0%; 0.0–9.6%) | 1/3 (33.3%; 6.1–79.2%) | 37 |
| baseten/ingest | not estimable (n=0) | not estimable (n=0) | not estimable (n=0) | 2 |
| fireworks/agent | 0/36 (0.0%; 0.0–9.6%) | 2/36 (5.6%; 1.5–18.1%) | 0/3 (0.0%; 0.0–56.1%) | 37 |
| fireworks/post | 0/36 (0.0%; 0.0–9.6%) | 0/36 (0.0%; 0.0–9.6%) | 0/3 (0.0%; 0.0–56.1%) | 37 |
| fireworks/ingest | not estimable (n=0) | not estimable (n=0) | not estimable (n=0) | 2 |
| meta/agent | 0/36 (0.0%; 0.0–9.6%) | 0/36 (0.0%; 0.0–9.6%) | 0/3 (0.0%; 0.0–56.1%) | 37 |
| meta/post | 0/36 (0.0%; 0.0–9.6%) | 0/36 (0.0%; 0.0–9.6%) | 0/3 (0.0%; 0.0–56.1%) | 37 |
| meta/ingest | not estimable (n=0) | not estimable (n=0) | not estimable (n=0) | 2 |

| Billed provider | Phase 2 USD | Retained unreconciled USD | Requests | Cap | Phase 1 + 2 USD |
|---|---:|---:|---:|---:|---:|
| baseten | 3.311842 | 0.000000 | 320 | 8.00 | 4.864609 |
| fireworks | 3.316011 | 0.664855 | 272 | 8.00 | 4.903245 |
| meta | 3.909388 | 0.017989 | 318 | 8.00 | 6.105509 |

**Phase-2 total estimated/reserved spend: $10.537241; both phases: $15.873363.** Includes all failures/retries, and Meta vision on every media route; not a provider invoice. A locked shared ledger enforces the $8 phase-2 cap separately for each billed provider. Prior News authorization and costs are separate.

### Translation and units

The shown auto-translated text introduces an important evaluation layer: the displayed claim can contain a financial-number error even when the original author may not have written it. We have the collector's paraphrase and shown-language flag, not a paired original-language archive, so we cannot prove which errors were introduced by Threads translation.

- **T33, confirmed displayed unit errors:** the SEC Apple release reports fiscal Q4 2026 iPhone revenue of $57,583 million and Greater China revenue of $17,539 million. The shown paraphrase says $575.8 billion and $175.4 billion, roughly ten times those amounts. Total revenue $114.48 billion, EPS $2.10 and 12% growth agree at the stated precision. [Exact source anchors](threads/gold.jsonl).
- **T03, confirmed displayed numeric/period errors:** CoreWeave's $229 million 2023 and $5.131 billion 2025 revenue are shown as $2.29 billion and $51.31 billion. Its stated $4.653 billion Q1 2026 figure matches the six-month total; the quarter alone is $2.078 billion. The 2022 statement remains unverified, while the other explicit-year errors suffice to refute the conjunction.
- **T09, comparison-period error:** SanDisk's 23% growth is sequential; its fiscal Q1 2027 year-over-year growth is 378%. The supplied paraphrase labels 23% as year over year. Both revenue and adjusted EPS agree with the release at their stated precision.
- **T10, apparent unit-error candidate, unscored:** the shown Apple Q4 revenue is $1.144 billion, but no reporting year is given. It resembles an hundred-million units-to-billion conversion error relative to the latest release; the missing year prevents a primary gold label. Other translated posts with suspicious units remain on the review list rather than receiving inferred corrections.

These are observed display-layer problems, not an estimated error prevalence for Threads or a ranking of authors. Top-search selection, paraphrasing and translation can each affect the tested input. [Full interpretation and retained failures](threads/FINDINGS.md).

### Media and next inputs

The two genuine cards were visually reviewed before paid OCR, then each passed through `claimcheck ingest` with Baseten, Fireworks and Meta verification. All six routes use fresh Meta vision; this is not a native image-model comparison. Images contain market prices, technical commentary, financing and a cloud-order backlog without enough reporting context for financial truth gold. Media accuracy and OCR recall are therefore not estimable; operational extraction/checking, errors, latency and cost are reported. They overlap own posts O04/O20 and are not additional independent facts.

Public media artifacts are allowlisted numeric outcomes, coverage, commands and request/reservation metadata with SHA-256 links to full local artifacts. Original cards, verbatim OCR, full responses and traces are retained under ignored `runs/threads-phase2/media/`; they are not copied into the evidence corpus. The authoring agent performed the pre-OCR visual review; the frozen flag calling it human review is corrected in the [provenance notice](threads/MEDIA_REVIEW_PROVENANCE.md). No independent human transcript was supplied. [Media input hashes](threads/media-inputs.json) · [pre-OCR gold/review notes](threads/media-gold.jsonl).

[Owner-provided Reels and YouTube audio/video plan](NEXT_SOURCES.md). No new real audio/video input was available for phase 2; no third-party video was downloaded.

Offline rebuild: `python3 scripts/real_world/report_threads.py --out docs/evidence/real-world-2026-11-02/threads`. [Offline reuse and retained artifacts](threads/REUSE.md) · [artifact audit](threads/audit.json) · [validation](threads/validation.json) · [Git handoff](HANDOFF.md).
