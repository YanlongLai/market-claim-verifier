# Market Claim Verifier — judge guide

Check financial claims against SEC filings with Meta’s open-weight Muse Spark Open; inspect the quotation, evidence, calculation and unresolved questions behind each verdict. [Try the saved demo](https://hackathon.dappgo.com/) · [Local live-check CLI](README.md#run-it).

**Original held-out text results, Baseten Muse Spark Open:** [240/266 correct (90.2%), 1/139 false support, $0.019880 mean cost per claim](docs/evidence/eval-v2-2026-10-27/REPORT.md). Corrected reference labels; failures count as wrong. [Limits](#limits) are part of these claims.

<a id="60-second-path"></a>

Day 5: [delivery plan](docs/DAY5_PLAN.md) · [provider capabilities and prices](docs/PROVIDERS.md). US equities only; planned features are not current capabilities.

[Open-weight LoRA attempt (Nov 3 UTC)](docs/evidence/lora-2026-11-03/REPORT.md): Fireworks NVFP4 LoRA initialization confirmed; tokenizer access blocked training. $0 estimated spend, no trained adapter or extraction improvement claim. [Feasibility and rates](docs/evidence/lora-2026-11-03/FEASIBILITY.md).

## 3-minute path

1. **Try a check.** Apple’s “$416.2B in one quarter” uses the full-year figure; fiscal Q4 2025 was $102.5B, making the claim about 4× the quarter. Open the [saved check](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json) or [readable post report](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.html), then the [demo](https://hackathon.dappgo.com/). The [three-outcome walkthrough](docs/evidence/judge-walkthrough/REPORT.md) is an offline program example, not a live model run.
2. **Compare Meta model routes.** On the same [266 held-out claims](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics), the tool-using agents scored **90.2% Baseten / 89.1% Fireworks** with Muse Spark Open, versus **82.0%** for hosted Muse Spark 1.3. Mean costs were **$0.019880 / $0.019973 / $0.025880** respectively. The same agent loop runs on both open-weight hosts. [Model manifest](docs/evidence/eval-v2-2026-10-27/manifest.json) · [Adapters](src/claimcheck/providers.py).
3. **Inspect the agent’s decisions.** In the [Alphabet trace](docs/evidence/2026-10-27/20261027T222758Z-8959a100.json), Muse chooses `lookup_fact` then `history_rank` for “first time.” [Sequence diagram](docs/diagrams/real-run-sequence.mmd) · [Model versus Python responsibilities](README.md#agentic-muse-chooses-the-next-check-python-checks-the-answer) · [Video — TODO (Claude)](#demo-video-todo).

## Four equally weighted criteria

| Criterion | What to inspect |
| --- | --- |
| **Impact** | Review a financial sentence before sharing it: original quote, cited SEC evidence, calculation and explicit unknowns. [English/Chinese post reports](docs/evidence/posts-2026-10-28/) · [Verdict cards](docs/figures/verdict-cards.svg). Benchmark correctness is not measured user impact. |
| **Use of Meta AI tooling** | Muse Spark Open on Baseten/Fireworks; Muse Spark 1.3 via Meta Model API; **`muse-voice-transcribe-1.0`** for audio and Muse Spark OCR for images/sample frames. [Exact verifier IDs](docs/evidence/eval-v2-2026-10-27/manifest.json) · [Media adapter](src/claimcheck/ingest_media.py) · [Recorded media review](docs/evidence/real-av-context-live/REPORT.md) · [Prompts](prompts/). |
| **Technical depth** | Muse selects tools, periods, comparisons and release quotes; Python calculates, validates citations and determines the verdict. [Tools](src/claimcheck/tools.py) · [Release tools](src/claimcheck/release_tools.py) · [Program checks](src/claimcheck/checks.py) · [Release checks](src/claimcheck/release_checks.py) · [Budget reservations](src/claimcheck/budget.py) · [Independent gold](eval/build_gold.py) · [Replay tests](tests/test_live_replay.py) · [Provider tests](tests/test_fireworks_provider.py). |
| **Demo** | [Saved post/filing example](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.html), [per-claim explorer](docs/explorer/index.html), [site source](docs/site/index.html), [storyboard](demo/storyboard.yaml) and [video approval/rebuild record](demo/BUILD_LOG.md). The website replays saved evidence; the CLI performs fresh checks. |

## Bonus categories

| Category | Concrete case |
| --- | --- |
| **Best Build on Meta Open Weight Models** | The [held-out comparison](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) puts Muse Spark Open ahead of hosted Muse Spark 1.3 in this workflow, at similar observed cost. [Same-loop provider diagram](docs/diagrams/providers.mmd) and [recorded model IDs](docs/evidence/eval-v2-2026-10-27/manifest.json) make the portability claim inspectable. |
| **Best Agentic Use-Case** | The agent chooses which evidence to retrieve and which calculation to request; Python owns arithmetic and evidence acceptance. Follow the [real trace](docs/evidence/2026-10-27/20261027T222758Z-8959a100.json), [tool-loop prompt](prompts/agent-tool-loop-instructions.md), [extraction prompt](prompts/post-extraction.md) and [prompt registry](src/claimcheck/prompts.py). |
| **Most Viral** | The [Apple quarter/year correction](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json) gives a shareable explanation with a receipt. [In the wild — TODO (Claude)](#in-the-wild-todo); no measured reach, adoption or virality is claimed. |

## Publication links — TODO (Claude)

<a id="demo-video-todo"></a>

- **Video — TODO (Claude):** add the publication URL. [Demo records](demo/BUILD_LOG.md) retain the approved video and [opening disclosure](demo/JUDGE_INTRO.md).

<a id="live-check-todo"></a>

- **Live check — TODO (Claude):** add the public live-check URL. The current [local CLI](README.md#run-it) needs keys and network; browser uploads are planned.

<a id="in-the-wild-todo"></a>

- **In the wild — TODO (Claude):** add the findings link. Current real-media development studies are listed under [Limits](#media-studies).

## What is new during the hackathon

**“Nothing in this repository pre-existed the hackathon.”** [Opening disclosure](demo/JUDGE_INTRO.md) · [Build log and window: Oct 27–Nov 4, 2026](BUILD_LOG.md#build-log). First commit: **`7c5670b`, 2026-10-27 14:20:17 −07:00** ([dated commit/evidence map](CHANGELOG.md#day-1--2026-10-27), [Git verification command](AGENTS.md#verify-the-build-window)). SEC data and dependencies are [credited](CREDITS.md).

Build/failure record: [Day 1](BUILD_LOG.md#day-1--2026-10-27-tue), [next iteration](BUILD_LOG.md#day-2-scope--started-2026-10-27-tue-afternoon), [post checking](BUILD_LOG.md#day-3--2026-10-28-wed). [Delivery plan](docs/DAY5_PLAN.md) separates implemented capabilities from planned work.

## Verify without model calls

Run `python3 scripts/check_links.py` and `UV_OFFLINE=1 sh scripts/verify.sh` with dependencies cached. The verifier runs the Python/Node suites, figure rebuild/check, byte-identical site-data rebuild and local Markdown links in a disposable copy with network guards. [Entry point](scripts/verify.sh) · [Prerequisites and first-run setup](AGENTS.md#offline-verification) · [Recorded verification](docs/VERIFICATION.md). Do not run paid evaluation, SEC fetches or media synthesis to verify these saved claims.

<a id="limits-to-keep-in-view"></a>

## Limits

### Original text evaluation

The original [v2 evaluation](docs/evidence/eval-v2-2026-10-27/REPORT.md) has **357 claims across 23 companies: 91 development and 266 held out**. README headlines and the comparison above use only the held-out split. The corpus combines generated financial cases and paraphrased source sentences; these scores do not establish real-world multimedia accuracy. No-tool and agent methods use the same model within a provider. Muse Spark Open and Muse Spark 1.3 are different model variants; this comparison does not isolate hosting as a cause.

Failures, missing pairs, provider errors and budget stops count as wrong. False support means a gold `contradicted` or `insufficient_evidence` claim accepted as `supported`; the held-out denominator is [139 such claims](docs/evidence/eval-v2-2026-10-27/REPORT.md#per-gold-class-precision-and-recall). Latency and mean cost follow completed-pair accounting in the [report](docs/evidence/eval-v2-2026-10-27/REPORT.md).

The [original frozen claims](eval/v2/claims-v2.jsonl) were committed before execution. Displayed results use [two corrected gold answers](eval/v2/claims-v2-corrected.jsonl); [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) remain available. The [manifest](docs/evidence/eval-v2-2026-10-27/manifest.json) records a dirty working tree, exact model IDs, prompt versions and snapshot hashes. These are recorded runs, not fresh measurements of the current code.

Later **92.2% / 91.0% / 85.4%** agent results are **post-hoc**, after inspecting failures. Zero false-supported verdicts on that rerun do not establish a general error rate ([rerun report](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md)). Empty single-shot summary rows in that run are not results.

### Input and source boundaries

The current scope is US equities and supported SEC/issuer evidence. Tagging errors, restatements, fiscal calendars and missing non-GAAP evidence can change the result. Context supplied for an event is recorded as conditional metadata, not authenticated evidence.

Media extraction and claim recall remain incomplete. The real audio/video study uses one scene; the controlled format study uses synthetic media. Neither supports a claim of general financial-media accuracy. Reports are intended for reviewing statements, not issuing investment ratings.

All three text-verifier routes accept the same repository formats. Images and media use **Meta OCR/ASR**, including when Baseten or Fireworks performs the text verification.

| Input | Processing | Main boundary |
| --- | --- | --- |
| Text / Markdown | Local text → chosen verifier | Claim extraction is bounded. |
| PNG / JPEG / WebP | Meta OCR → chosen verifier | Chart geometry and image authenticity are not verified. |
| Text PDF | Local page extraction → chosen verifier | No scanned-PDF OCR or cross-page context. |
| Audio | Meta ASR → chosen verifier | Speaker labels do not establish identity; timestamps cover turns. |
| Video | Audio transcription + three OCR frames → chosen verifier | Unsampled visuals can be missed; audio and frames are checked separately. |

Scanned PDFs and general webpage URLs are not integrated. The local job queue is not a provider's discounted Batch API. [Detailed format limits and provider capabilities](docs/PROVIDERS.md).

Segment KPIs, deliveries, market share and share prices remain outside the supported financial checks; missing supported evidence yields `insufficient_evidence`. [Source scope](docs/DATA_SOURCES.md) · [Planned sources](ROADMAP.md).

Current financial evidence includes [SEC XBRL tiers L1–L3](docs/DATA_SOURCES.md) and eligible L4 issuer earnings releases. Tagging, restatements and period handling remain material ([data quality](docs/DATA_QUALITY.md)). Valuation opinions are skipped. L4 guidance/non-GAAP support scored [31/32 on a fixture-based regression set](docs/evidence/eval-l4-2026-10-29/ANALYSIS.md), not a held-out benchmark. L5, market multiples, Taiwan filings and verified full-call speaker attribution remain [planned](ROADMAP.md). The site [replays saved evidence](docs/scripts/build_site.py); fresh runs require [keys and network](README.md#run-it). This project is not investment advice.

### Media studies

[Original local-input probe](docs/evidence/multimodal-2026-10-29/REPORT.md), followed by separately retained hardening and recall work:

- Local audio/video results are **development probes**, not held-out scoring. The period-loss error remains fixed; earlier short-audio numeric-assertion coverage is **5/5**, row-only video **8/9** ([hardening report](docs/evidence/multimodal-2026-10-30/REPORT.md)). The [recall follow-up](docs/evidence/multimodal-2026-10-30b/REPORT.md) fixes the text EPS-error control to `contradicted`. The 12-minute full-media control improves guarded/program-checked coverage **19/60 → 44/60**, with ASR **55/60**; the final recheck of identical frozen ASR text reaches **50/60** guarded assertions. A failed extraction attempt, insufficient-evidence verdicts and remaining misses are retained. These are repeated readings of a few facts; no verified speaker identity, word alignment or real-call benchmark. The earlier two-voice control still merged both voices into A.

#### Real company materials: what improved, what remains unresolved

In a genuine Microsoft earnings-call excerpt, the audio says “this quarter” while the slide says “FY27 Q1.” The initial workflow could read the numbers but could not safely bind the period. A separate, reviewed event-context record made the period explicit without changing the original quotation.

In the subsequent six-claim check, **Baseten and Fireworks each supported five claims**: revenue, net income, diluted EPS, operating income and revenue growth. Both kept the unchanged, undated adjusted-EPS control as insufficient evidence. Meta returned one supported, two insufficient and three HTTP 500 failures.

For example, the filing value **$92.279B** supports the slide's **$92.3B revenue** at its displayed precision. That conclusion is conditional on the supplied fiscal Q1 2027 context. It does not certify the whole recording. [Results, evidence and failures](docs/evidence/real-av-context-live/REPORT.md) · [Original WAV and MP4](eval/real-av-v1/README.md).

Three real Tesla slides also have a [multi-document review](docs/evidence/stock-context-posthoc-2026-10-30/REPORT.md). Its unresolved chart led to an explicit coverage warning: reading chart labels does not verify bar heights or series values. [Chart diagnosis](docs/evidence/chart-diagnosis-2026-10-30/REPORT.md).

<a id="controlled-format-study"></a>

<details>
<summary>Controlled comparison across nine input formats</summary>

<!-- multimodal-v1:start -->

Six issuers, 24 underlying assertions, nine encodings—not 216 independent facts. Cells show correct / 24; missing, incomplete and wrong outcomes remain in the denominator. All providers use the same files and frozen Meta OCR/ASR text.

| Format | Meta | Baseten | Fireworks |
| --- | ---: | ---: | ---: |
| TXT | 22/24 | 24/24 | 24/24 |
| Markdown | 22/24 | 24/24 | 24/24 |
| PDF | 23/24 | 24/24 | 24/24 |
| PNG | 24/24 | 24/24 | 24/24 |
| JPEG | 22/24 | 24/24 | 24/24 |
| WebP | 23/24 | 24/24 | 24/24 |
| WAV | 18/24 | 23/24 | 24/24 |
| MP3 | 14/24 | 24/24 | 24/24 |
| MP4 | 19/24 | 24/24 | 24/24 |

One controlled run on clean inputs, with synthetic audio and video. Separate native-image probes completed 6/6 PNG, JPEG and WebP inputs per provider; response completion is not financial accuracy. Native audio/video endpoints were not tested in this comparison.

[Methods, failures and limits](docs/evidence/fair-multimodal-v1/REPORT.md) · [Reusable inputs, outputs and offline replay](docs/evidence/fair-multimodal-v1/REUSE.md).

<!-- multimodal-v1:end -->

</details>

Open the [real Tesla three-document summary](docs/evidence/stock-context-posthoc-2026-10-30/attempt-2/summary/stock-review.html): three supported occurrences, five needing evidence, and a chart with no checked claims. The summary costs no additional model call and exposes incomplete coverage. Both repair attempts are retained separately from the benchmark. [Run your own stock review](docs/STOCK_REVIEW.md).

### Cost accounting

A document's cost includes preprocessing, claim extraction and every verification turn. The historical 357-claim text study averaged approximately **$0.020 per claim** for Baseten/Fireworks and **$0.026** for Meta. Those are observed workflow costs, not per-document prices or service guarantees. [Recorded costs and latency](docs/evidence/eval-v2-2026-10-27/REPORT.md).

Published rate snapshot, checked 2026-10-30; USD per million tokens:

| Platform / model | Input | Cached input | Output |
| --- | ---: | ---: | ---: |
| Meta · Muse Spark 1.3 Standard | $1.25 | $0.15 | $4.25 |
| Baseten · Muse Spark Open | $1.25 | $0.15 | $4.25 |
| Fireworks · Muse Spark Open | $1.25 | $0.15 | $4.25 |

Meta ASR was listed at $0.18/hour; image OCR uses tokens. Ledger estimates include failed attempts and reservations and are not vendor invoices. [Official rate sources and Batch caveats](docs/PROVIDERS.md#price-comparison) · [Latest recorded follow-up spend](docs/evidence/real-av-context-live/REPORT.md#spend-usd-estimatedreserved).

The text-verifier mean does not include document OCR/ASR or extraction. Pricing is a dated snapshot; a document may contain many chargeable claims. The local queue is not discounted provider Batch. [Provider and ledger accounting](docs/PROVIDERS.md#price-comparison).

### Historical results and failure review

<details>
<summary>Combined development/test totals, errors, gold corrections and post-hoc reruns</summary>

The following preserves the earlier README’s full-set discussion. It includes development claims; use the original held-out split for the headline. [Original report](docs/evidence/eval-v2-2026-10-27/REPORT.md) · [Post-hoc report](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md).

**357 claims about 23 companies.** 260 are generated from SEC data across 10 trap families. 54 are model paraphrases of those. 43 are real sentences from news, aggregator and investor-relations pages, paraphrased.

- **Gold answers** come from an [independent script](eval/build_gold.py) and were **committed before any v2 run** ([`5d90b3b`](https://github.com/YanlongLai/market-claim-verifier/commit/5d90b3b)).
- **The run:** six systems, one code version, 2,142 verdicts ([report](docs/evidence/eval-v2-2026-10-27/REPORT.md)).

| System | Accuracy (95% CI) | Says "supported" when false | Mean cost / claim | Mean latency |
| --- | --- | --- | --- | --- |
| **Agent · Muse Spark Open on Baseten** | **323/357 = 90.5%** (87.0–93.1) | 1 / 186 | $0.020 | 12 s |
| **Agent · Muse Spark Open on Fireworks** | **323/357 = 90.5%** (87.0–93.1) | 1 / 186 | $0.020 | 67 s |
| **Agent · Muse Spark 1.3 on Meta Model API** | **297/357 = 83.2%** (79.0–86.7) | 4 / 186 | $0.026 | 39 s |
| Single-shot · Muse Spark 1.3 (no tools) | 158/357 = 44.3% (39.2–49.4) | 9 / 186 | $0.019 | 20 s |
| Single-shot · Muse Spark Open, Baseten | 74/357 = 20.7% (16.8–25.2) | 1 / 186 | $0.012 | 9 s |
| Single-shot · Muse Spark Open, Fireworks | 71/357 = 19.9% (16.1–24.3) | 0 / 186 | $0.012 | 51 s |

- **The complete agent path outperformed single-shot on this recorded set.** On the same claims, agent accuracy beats single-shot by:
  - Meta API: **+38 points** (95% paired bootstrap CI +33 to +44).
  - Baseten: **+70** (+65 to +74).
  - Fireworks: **+70** (+65 to +76).

  McNemar p < 0.0001 for all three.
- **Real-world sentences:** the agent was right on 43/43 (Baseten, Fireworks) and 39/43 (Meta API). Single-shot was right on 6/43, because it mostly answers "insufficient evidence" for 2025–2026 numbers it cannot know.
- **Without tools, the hosted model guesses more.** Single-shot Muse Spark 1.3 said "supported" for 9 false claims. The open-weights model refused instead (0–1 false "supported").
- **Open weights scored higher in this recorded workflow.** Muse Spark Open with the agent beat the hosted Muse Spark 1.3 agent by 7 points (paired CI +4 to +10, p = 0.0001). Baseten had the lowest mean latency among the agents; the open-weight routes had similar mean cost.
- **Where the agent still fails:**
  - "First time / record" claims: 16–18 of 31 right.
  - Year-over-year claims on the Meta API: 29/48, against 45/48 on Baseten and Fireworks.
  - Fiscal-vs-calendar traps: 23–24 of 30.

  Per-family tables are in the [report](docs/evidence/eval-v2-2026-10-27/REPORT.md).
- **The remaining false "supported" verdicts trace to two causes.**
  - **A lookup-tool bug, now fixed.** Apple's quarter ending 2023-07-01 was treated as calendar Q3 instead of Q2.
  - **"Q2 2024" for a non-calendar issuer.** The Meta API agent checked only the fiscal reading. Both readings disagree here, so the gold answer is "insufficient evidence". Now fixed: the program fetches the missing reading itself (see the post-hoc rerun below).
- **Post-hoc rerun after both fixes (not pre-registered).** Same 357 claims, same corrected gold, the three agents only ([report](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md)). The fixes were made after seeing v2 failures, so treat this as a regression check, not a new held-out score.

  | Agent | v2 | Rerun | Says "supported" when false |
  | --- | --- | --- | --- |
  | Muse Spark Open on Fireworks | 90.5% | **329/357 = 92.2%** | 1 → **0** / 186 |
  | Muse Spark Open on Baseten | 90.5% | **325/357 = 91.0%** | 1 → **0** / 186 |
  | Muse Spark 1.3 on Meta Model API | 83.2% | **305/357 = 85.4%** | 4 → **0** / 186 |

  - All ambiguous-quarter claims the agents had called "supported" (G0235, G0240, G0249) are now "insufficient evidence".
  - The accuracy gains are within run-to-run noise (paired McNemar p = 0.15–0.79); the drop to zero false "supported" is the point.
  - The Meta API had 3 provider errors (two 400 tool-call errors, one 503), counted as wrong. Cost: $7–9 per provider.
- **Two gold answers were wrong, and the run exposed them.** The gold script had mistaken Amazon for a June year-end issuer: it read a trailing-twelve-month figure in a 10-Q as an annual period. That made two true Amazon claims "contradicted".
  - The frozen set is unchanged. Corrections are listed with reasons in [`eval/v2/claims-v2-corrected.jsonl`](eval/v2/claims-v2-corrected.jsonl), and the table above uses them.
  - Scores against the registered gold are in [`REPORT-registered-gold.md`](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md). Every system moves by at most 2 claims.
- **Honest scope:**
  - The held-out split is 266 claims: agent 90.2% on Baseten, 89.1% on Fireworks and 82.0% on the Meta API.
  - Meta API spend hit the run's $15 cap after 262 claims. The 95 stopped pairs were kept as evidence and resumed under a $30 cap ([`budget-stopped-attempt1/`](docs/evidence/eval-v2-2026-10-27/budget-stopped-attempt1/)).
  - The v1 set of 30 hand-reviewed claims and its six runs remain in [`docs/evidence/`](docs/evidence/). Run 4 there: agent 30/30 (Baseten, Fireworks), 26/30 (Meta API).

</details>

Code: [MIT](LICENSE). Data/media: [credits](CREDITS.md). Recorded verifier calls use Meta models; offline image, narrator and music production have separate [model provenance and credits](CREDITS.md#media-and-dependencies) and [media process records](docs/PROCESS-media.md). AI readers: [llms.txt](llms.txt) → [AGENTS.md](AGENTS.md). [Test records](docs/TEST_RECORDS.md) retain failed and partial attempts for reuse.
