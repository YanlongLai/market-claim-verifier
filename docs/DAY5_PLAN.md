# Day 5 product completion plan

Owner scope, 2026-10-30 (America/Los_Angeles). “Day 5” is the Owner's iteration label, not a claim that five calendar days have elapsed since the first commit.

## Product promise

Check US-equity financial claims, show exact evidence and clearly disclose what was not checked. Prioritize a reproducible judge journey over adding unsupported formats. Taiwan is outside this hackathon scope. Preserve Meta-family runtime models and the existing recorded benchmarks.

## Delivery order and acceptance gates

| Order | Status | Deliverable | Acceptance gate |
|---|---|---|---|
| 1 | Implemented in this iteration | Public provider/modality/pricing comparison | Official source links, dated prices, platform capability separate from repository integration; no credit balance claims |
| 2 | Implemented in this iteration | Honest ingestion coverage summary | JSON and HTML show proposed, accepted, checked and failed claim counts; unknown full-content recall never becomes 100% |
| 3 | Implemented in this iteration | Local PDF input | Page-scoped text and original-file hash; scanned/empty pages explicitly unsupported until OCR; limits and parser errors tested |
| 4 | Implemented | Evidence record interface and one US issuer document connector | Immutable source snapshot, publisher, time, locator, units/period; arbitrary uploads do not become authoritative; original SEC regression unchanged |
| 5 | Implemented | Complete evidence-to-verdict judge example | One official US issuer document, one false claim, one supported claim and one insufficient-evidence case; clickable source locations and cost breakdown |
| 6 | Implemented | Versioned policy and as-of time | Exact entity/unit/period rules remain mandatory in every mode; historical/restated facts distinguished |
| 7 | Implemented (serial, job-level resume) | Cost breakdown and bounded job queue | Reserved versus estimated/billed amounts distinguished; cache keys include model/prompt/policy/evidence versions; resume without duplicate successful calls |
| 8 | Planned | Independent evaluation and submission refresh | Freeze unseen issuers/documents before tuning; publish extraction recall, false-supported rate, abstention, p95 and cost; refresh judge docs and video only after results |
| 9 | Deferred until core gates pass | Direct readable URL ingestion | Public HTTPS plain text/Markdown only initially; explicit content type/size/time limits, network destination validation; no authentication, cookies, browser rendering or arbitrary HTML |
| 10 | Deferred | Adaptive video sampling, speaker identity, provider batch, custom domain pack | Evaluate separately; no universal video accuracy or batch discount claims without model-specific validation |

## Working agreement

Make milestone-sized commits with actual implementation and test results. Update this table, CHANGELOG and judge-facing references as each milestone finishes; never manufacture progress or rewrite recorded evaluations. Publish only tested changes. No video upload until the Owner chooses a final cut. Winning is a goal, not a promised result.

## Judge value

The demonstration should answer: what was claimed, where it appeared, what source supports the check, why the numeric result follows, what remains unchecked, and what it cost. A saved replay must remain labeled as a replay; live API execution must not be implied.

## Current limitations

Full-content recall has no ground-truth denominator on arbitrary user inputs. Claim-processing counts are operational coverage, not accuracy. Local native-text PDF ingestion is implemented; user-supplied authoritative evidence is not. PDF has a 100-page limit, no OCR and no cross-page context propagation. General web browsing, login pages and Taiwan data are out of the current delivery scope.

## Contributor handoff

The [extension guide](EXTENDING.md) describes reusable modules. The [evidence contract and first SEC connector](EVIDENCE_RECORDS.md) are implemented; a general plugin registry and non-SEC sources remain planned.

## Verification receipt — 2026-10-30

`sh scripts/verify.sh` passed: 846 product tests, 149 demo Python tests, 55 Node tests; fixture hashes, figure rebuild/check, three byte-identical generated outputs and Markdown links passed. The extension guide was added during the isolated run; a subsequent link check covered all 101 Markdown files and 770 local links/anchors. No model calls, paid inference or SEC fetches were used. This is offline regression verification, not a new PDF financial-accuracy benchmark.

## Language and presentation

English is the primary language for judge-facing pages and documentation. The explorer retains a Traditional Chinese switch with claim deep links. Preserve original evidence and model outputs in their recorded language; optional Chinese explanations must not replace English documentation.

### Milestone 4 verification — 2026-10-30

`sh scripts/verify.sh` passed with 855 product tests, 149 demo Python tests and 55 Node tests. Fixture checks, figures, three byte-identical generated outputs and all 778 local links passed. The META offline export was repeated successfully with identical record identity. No model calls or live SEC retrievals were performed; this is source-integrity/regression validation, not a new accuracy benchmark.

### Milestone 5 verification — 2026-10-30

The [judge walkthrough](evidence/judge-walkthrough/REPORT.md) is implemented and linked from README/JUDGES. Its three predefined atomic claims produce supported, contradicted and insufficient_evidence through the existing checker. Generated artifacts rebuild byte for byte, and modified evidence bundles are rejected. `sh scripts/verify.sh` passed: 857 product tests, 149 demo Python tests, 55 Node tests; fixture/figure checks, three generated outputs and 786 local links passed. No live model or SEC calls were made. The $0 incremental API cost applies only to this offline walkthrough, not live verification.

### Milestone 6 verification — 2026-10-30

[Policy versioning and filing-date cutoffs](VERIFICATION_POLICY.md) are implemented for edgar/verify/post/ingest. Eleven new policy regressions cover prior versus later filings, date validation, missing dates, derived/history/latest selection, release revalidation and early-abstention audit metadata. Existing recorded media replay passes with unchanged default tool payloads. `sh scripts/verify.sh` passed: 868 product tests, 149 demo Python tests, 55 Node tests; source/figure integrity, three byte-identical data outputs and local Markdown links passed. No live model or SEC requests were used. This is filing-date filtering of available data, not a historical SEC archive or intraday reconstruction.

### Milestone 7 verification — 2026-10-30

[Cost accounting and bounded queue](QUEUE_AND_COSTS.md) are implemented as a serial, job-level resume workflow with frozen SEC evidence. Twelve new queue/cost tests cover admission limits, successful-job reuse, unknown outcomes, partial results, source/input/model changes, artifact tampering, process locks, duplicate inputs and cost overruns. `sh scripts/verify.sh` passed: 880 product tests, 149 demo Python tests, 55 Node tests; fixtures, figures, three byte-identical generated outputs and local links passed. No paid model calls or live SEC requests were used. Provider bills, per-channel retry/resume, parallel workers and native discounted Batch APIs remain unimplemented.

### Input-format validation follow-up — 2026-10-30

Owner-authorized paid format probes supplement milestones 1–3: Markdown, JPEG, WebP, MP3, silent MP4 and native-text PDF, with a $3 shared cap and retained failures. [Registered cases and measured results](evidence/input-formats-2026-10-30/REPORT.md) distinguish live-tested routes from repository integration. These known synthetic examples do not satisfy milestone 8’s independent-evaluation gate. URL ingestion, PDF OCR and native provider media adapters remain deferred.

### Paired benchmark and stock-review milestone — 2026-10-30

The [new delivery plan](FAIR_BENCHMARK_AND_STOCK_REVIEW_PLAN.md) replaces one-format-per-provider examples with a frozen same-input comparison. [Corpus and scorer](../eval/multimodal-v1/README.md) were committed in `d58bd53` before paid execution, with $40 authorized per provider and $35 admission ceilings. Results must distinguish shared Meta preprocessing, native image reading and unscored real issuer diagnostics. A [single-stock multi-file CLI and deterministic summary](STOCK_REVIEW.md) is implemented; the upload UI and optional citation-validated AI narrative remain next priorities.

## 2026-10-30 completed paired benchmark and stock context

Published the [nine-format paired study](evidence/fair-multimodal-v1/REPORT.md), [Chinese analysis](evidence/fair-multimodal-v1/ANALYSIS.zh-TW.md), reproducible inputs, raw calls, source archives and offline integrity audits. README tables separate integration, native-image completion and strict correctness. Total estimated/reserved task spend is Meta $4.23601935, Baseten $2.09934800, Fireworks $2.01364550; $40 each remains a ceiling, not a spending target.

Shipped bounded single-stock multi-file review, unauthenticated ticker context and evidence-linked deterministic summaries. Both real-document repair attempts remain public; the final [Tesla example](evidence/stock-context-posthoc-2026-10-30/attempt-2/summary/stock-review.html) has three supported and five insufficient occurrences, with the chart unchecked. Verification: 901 product tests, 149 demo Python tests and 55 Node tests passed, plus figures, byte-identical outputs and Markdown links.

Next: (1) multi-file ticker upload UI using the existing queue and budget gates; (2) independently labeled real tables and recordings plus cash-flow/KPI evidence coverage; (3) optional AI narrative with validated citations/numbers and an explicit budget; (4) native audio/video adapters, long-media continuation and vendor Batch. These remain planned, not shipped. See the [delivery plan](FAIR_BENCHMARK_AND_STOCK_REVIEW_PLAN.md).
