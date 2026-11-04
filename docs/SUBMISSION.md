# Market Claim Verifier — submission draft

Prepared for the Owner to copy into the [hackathon submission form](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit). Complete the [pre-submission checklist](SUBMIT_CHECKLIST.md) before submitting. Form labels below are a typical field mapping, not a claim about the authenticated form's current fields.

## Project name

Market Claim Verifier

## One-line pitch

Check financial claims against SEC filings with Meta Muse Spark and Python checks you can inspect. ([Agent](../src/claimcheck/agent.py), [program checks](../src/claimcheck/checks.py).)

## 150-word description

Market Claim Verifier checks [financial sentences and posts](../src/claimcheck/post.py) against SEC filings. Meta Muse Spark separates a post into quoted claims, selects evidence tools, and drafts cited explanations. Python checks the stated [numbers, units, periods, comparison words, and evidence identifiers](../src/claimcheck/checks.py) before returning supported, contradicted, or insufficient evidence. The runtime uses [Muse Spark 1.3](evidence/eval-v2-2026-10-27/manifest.json) through Meta Model API and [open-weight Muse Spark Open](diagrams/providers.mmd) through Baseten or Fireworks. Local screenshots use Muse Spark for text extraction; audio uses [muse-voice-transcribe-1.0](evidence/multimodal-2026-10-30/REPORT.md#protocol-and-media). [Sampled video frames and transcripts](../src/claimcheck/ingest.py) enter the same checks. Reported figures use SEC XBRL facts; guidance and non-GAAP claims can use [furnished earnings releases](DATA_SOURCES.md#l4-parsing-and-decision-rules) with verified quote offsets. The public site replays saved examples, while the repository includes raw traces, independently calculated gold answers, and an [offline verifier](../scripts/verify.sh). Recorded evaluations disclose [corrected labels, development claims, and post-hoc fixes](../JUDGES.md#limits-to-keep-in-view). Missing evidence stays explicit, and audio speaker labels remain unverified. [Every runtime model is from Meta](evidence/multimodal-2026-10-30/REPORT.md#protocol-and-media).

## 50-word description

Market Claim Verifier checks financial posts against SEC filings. Meta Muse Spark extracts claims and selects lookup tools; [Python checks numbers, periods, and citations](../src/claimcheck/checks.py) before assigning a verdict. Open each cited filing, inspect saved model traces, and run [offline tests that rebuild published results from recorded evidence without model calls](../scripts/verify.py).

## Problem

A financial sentence can mix a reported value, a growth comparison, and a claim about a record. Getting the value right still leaves room for a wrong period, unit, comparator, or citation. The project began after the author's existing product's AI-written commentary failed its internal fact-assertion check; that product's code is outside this submission. ([Problem and pre-existing-work disclosure](../BUILD_LOG.md#build-log), [recorded failures and fixes](../README.md#how-the-system-got-there).)

## What it does

The CLI checks individual sentences and English or Chinese posts. It extracts exact source quotes, rejects unsupported numeric rewrites, retrieves SEC evidence, and returns `supported`, `contradicted`, or `insufficient_evidence`, with cited facts and program checks. Valuation opinions are labeled and skipped; supported earnings-release guidance is checked as a statement in a release, not as a prediction of future performance. ([Post checker](../src/claimcheck/post.py), [saved post reports](evidence/posts-2026-10-28/), [release rules](DATA_SOURCES.md#l4-parsing-and-decision-rules).)

Local text files, screenshots, audio, and sampled video enter the same post-checking path. Media is input to extract claims from; financial verdicts still require SEC evidence. The public site replays saved reports and lets readers inspect filing excerpts and original-filing links. ([Ingestion runtime](../src/claimcheck/ingest.py), [media probe and limits](evidence/multimodal-2026-10-30/REPORT.md), [site source](site/index.html), [filing-excerpt build record](site/BUILD_SUMMARY.md).)

## How Meta models are used

Every application runtime model is a Meta model. The recorded text providers share the agent loop and program checks; OCR and speech transcription use Meta Model API. ([Provider adapters](../src/claimcheck/providers.py), [runtime model protocol](evidence/multimodal-2026-10-30/REPORT.md#protocol-and-media).)

| Meta model / service | Role | Exact recorded model ID and evidence |
| --- | --- | --- |
| [Muse Spark 1.3](evidence/eval-v2-2026-10-27/manifest.json) · Meta Model API | Claim extraction, tool selection, cited explanation drafts; screenshot text extraction | [muse-spark-1.3](evidence/eval-v2-2026-10-27/manifest.json); [OCR protocol](evidence/multimodal-2026-10-30/REPORT.md#protocol-and-media) |
| Muse Spark Open · Baseten · open weights | Claim extraction and agentic SEC checks | [meta-models/muse-spark-open-1026](evidence/eval-v2-2026-10-27/manifest.json); [open-weights provider diagram](diagrams/providers.mmd) |
| Muse Spark Open · Fireworks · open weights | Agentic SEC checks and the recorded single-shot comparison | [accounts/fireworks/models/muse-spark-open](evidence/eval-v2-2026-10-27/manifest.json); [provider adapter](../src/claimcheck/providers.py) |
| Meta speech transcription · Meta Model API | Audio transcription with whole-turn timestamps and unverified speaker labels | [muse-voice-transcribe-1.0](evidence/multimodal-2026-10-30/REPORT.md#protocol-and-media) |

Offline illustration, narration, and music production are separately documented in the [media credits](../CREDITS.md#media-and-dependencies).

## Architecture

- **Extract source-bound claims.** Muse identifies a quote and a standalone claim; Python checks exact quote spans and numeric provenance. OCR and ASR supply text for local media. ([Post checker](../src/claimcheck/post.py), [ingestion](../src/claimcheck/ingest.py).)
- **Let the model select tools.** Muse calls fact lookup, period listing, change calculation, history ranking, and earnings-release tools before drafting a cited verdict. ([Agent loop](../src/claimcheck/agent.py), [tool definitions](../src/claimcheck/tools.py), [recorded sequence](diagrams/real-run-sequence.mmd).)
- **Keep the evidence attributable.** SEC XBRL facts retain filing accessions and source hashes; derived facts retain their components. Earnings-release quotes retain cached bytes and offsets. ([Evidence policy](DATA_SOURCES.md), [SEC tools](../src/claimcheck/tools.py), [release checks](../src/claimcheck/release_checks.py).)
- **Have Python determine the verdict.** Program rules check stated precision, units, comparison direction, periods, evidence IDs, and release quotes, then aggregate the sub-claims. ([Numeric checks](../src/claimcheck/checks.py), [release checks](../src/claimcheck/release_checks.py), [regressions](../tests/test_live_replay.py).)
- **Record and replay the work.** Calls reserve budget before execution and retain requests, responses, usage, and tool traces. Manifests record models and prompt hashes; offline builders rebuild the explorer and site from saved evidence. ([Ledger](../src/claimcheck/budget.py), [run manifest](evidence/eval-v2-2026-10-27/manifest.json), [offline verifier](../scripts/verify.py).)

## Recorded results

The original evaluation covers [357 claims](../eval/v2/MANIFEST.json), including [91 development and 266 held-out claims](evidence/eval-v2-2026-10-27/REPORT.md#metrics). The table uses [corrected gold](../eval/v2/claims-v2-corrected.jsonl); the [registered-gold report](evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) remains available. Missing, failed, incomplete, or budget-stopped predictions count as wrong. The [manifest records a dirty working tree](evidence/eval-v2-2026-10-27/manifest.json). These are recorded benchmark results, not measured user outcomes.

| Meta model / provider | Agent accuracy | Single-shot accuracy, no tools | Agent false-supported verdicts among non-supported gold claims |
| --- | --- | --- | --- |
| Muse Spark Open · Baseten | [323/357 = 90.5%](evidence/eval-v2-2026-10-27/REPORT.md) | [74/357 = 20.7%](evidence/eval-v2-2026-10-27/REPORT.md) | [1/186](evidence/eval-v2-2026-10-27/REPORT.md) |
| Muse Spark Open · Fireworks | [323/357 = 90.5%](evidence/eval-v2-2026-10-27/REPORT.md) | [71/357 = 19.9%](evidence/eval-v2-2026-10-27/REPORT.md) | [1/186](evidence/eval-v2-2026-10-27/REPORT.md) |
| [Muse Spark 1.3](evidence/eval-v2-2026-10-27/manifest.json) · Meta Model API | [297/357 = 83.2%](evidence/eval-v2-2026-10-27/REPORT.md) | [158/357 = 44.3%](evidence/eval-v2-2026-10-27/REPORT.md) | [4/186](evidence/eval-v2-2026-10-27/REPORT.md) |

The [per-claim explorer snapshot](explorer/data.json) supplies the individual completed verdicts behind these counts; the [verification guide](../AGENTS.md#inspect-the-key-numbers-without-dependencies) gives the counting command. The report includes uncertainty intervals and split-level results. The comparison evaluates the complete agent path against single-shot answers; it does not isolate each program rule's contribution.

Separately, the earnings-release regression recorded [31/32 = 96.9% accuracy and 0/19 false-supported verdicts](evidence/eval-l4-2026-10-29/REPORT.md). Its fixtures informed implementation, so this is a development regression, not a blinded held-out estimate. The retained miss is a supported free-cash-flow claim rejected for a claim-kind mismatch. ([Analysis and post-run changes](evidence/eval-l4-2026-10-29/ANALYSIS.md).)

## What is new during the hackathon

All repository code and demo work were created during the [October 27–November 4, 2026 build window](../BUILD_LOG.md#build-log). Nothing in this repository pre-existed the hackathon. The first commit is [7c5670b, authored October 27, 2026](../CHANGELOG.md#day-1--2026-10-27). SEC data and third-party dependencies are [credited separately](../CREDITS.md).

Implemented work includes the SEC tool loop, claim-aware program checks, provider adapters, independent gold builder, recorded evaluations, whole-post extraction, bilingual site, results explorer, filing excerpts, and demo pipeline. The [dated changelog](../CHANGELOG.md) and [build log](../BUILD_LOG.md) map that work to code and evidence. Earnings-release checks and local-media ingestion/hardening are also implemented, with their own [release regression](evidence/eval-l4-2026-10-29/ANALYSIS.md) and [media development records](evidence/multimodal-2026-10-30/REPORT.md).

## Limits

- The main table mixes development and held-out claims and uses [two corrected gold answers](../eval/v2/claims-v2-corrected.jsonl). The [later agent rerun](evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md) followed failure inspection on the same claims; it is post-hoc. Its empty single-shot rows are not results.
- SEC tagging, restatements, fiscal/calendar ambiguity, and incomplete history can limit a check. Furnished earnings releases are unaudited, and complex or unsupported release claims can remain insufficient evidence. ([Data quality](DATA_QUALITY.md), [source policy](DATA_SOURCES.md), [release regression limits](evidence/eval-l4-2026-10-29/ANALYSIS.md).)
- Media extraction can miss assertions or lose context. The recorded period-loss error was fixed on reused development media, but a text EPS control still returns insufficient evidence. Speaker labels remain unverified, and distinct synthetic voices were merged. Long-audio evidence uses a synthetic repeated clip and does not establish real-call performance. ([Before/after and retained failures](evidence/multimodal-2026-10-30/REPORT.md).)
- The website replays saved evidence. Fresh checks require model credentials and network access; offline verification rebuilds saved outputs and tests the code. ([Site builder](scripts/build_site.py), [runtime setup](../README.md#run-it), [offline verifier](../scripts/verify.py).)
- Earnings-call statement evidence, verified speaker attribution, market-multiple checks, and Taiwan filing support remain outside the completed evidence scope described here. The [roadmap](../ROADMAP.md) records planned extensions; Chinese-language post checking currently uses SEC sources.

## Links

| Destination | URL / status |
| --- | --- |
| Public site / saved demo | [hackathon.dappgo.com](https://hackathon.dappgo.com/) |
| Public repository | [YanlongLai/market-claim-verifier](https://github.com/YanlongLai/market-claim-verifier) |
| Results explorer | [Saved per-claim results](https://hackathon.dappgo.com/explorer/) |
| Demo video | `VIDEO_URL_PENDING` — Owner replaces with a public YouTube or Vimeo URL after checking the final upload against the [video checklist](SUBMIT_CHECKLIST.md#video) and [opening disclosure](../demo/JUDGE_INTRO.md). |
| Submission form | [Cerebral Valley submission](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit) |

## Field-by-field form draft

Use the matching field when present; check the authenticated form's labels and limits before pasting. Owner account details and the published video URL still need completion.

| Typical field | Draft answer |
| --- | --- |
| Project name | Market Claim Verifier |
| Tagline / one-line pitch | Check financial claims against SEC filings with Meta Muse Spark and Python checks you can inspect. |
| Short description | Copy the [50-word description](#50-word-description). |
| Project description | Copy the [150-word description](#150-word-description). |
| Problem / inspiration | Financial commentary can quote the right number with the wrong period, unit, or comparison. The project began after the author's existing commentary failed an internal fact check. See [problem and disclosure](../BUILD_LOG.md#build-log). |
| What it does | Extract quoted financial claims, retrieve SEC evidence, and return program-checked verdicts with filing links. Local screenshots, audio, and sampled video feed the same checking path. See [implemented behavior](#what-it-does). |
| How it was built / technical approach | Meta Muse Spark chooses SEC tools and drafts explanations; Python validates numeric and citation evidence. A reservation ledger and raw traces make calls auditable; independent gold and offline replay support verification. See [architecture](#architecture). |
| Meta AI tools and models | [Muse Spark 1.3 via Meta Model API](evidence/eval-v2-2026-10-27/manifest.json); open-weight Muse Spark Open via Baseten and Fireworks; [muse-voice-transcribe-1.0](evidence/multimodal-2026-10-30/REPORT.md#protocol-and-media). Exact IDs and roles are in [model usage](#how-meta-models-are-used). |
| Results / evaluation | Copy the [recorded results table and its scope notes](#recorded-results), including the corrected-gold and mixed-split disclosures. |
| Technical challenges / learning | Live traces exposed comparator, direction, period-label, duplicate-evidence, and source-context failures. Program checks and replay regressions address the recorded cases; unresolved limits remain explicit. See [failure/fix record](../README.md#how-the-system-got-there) and [media hardening](evidence/multimodal-2026-10-30/REPORT.md). |
| New work / pre-existing work | Nothing in this repository pre-existed the hackathon. All repository code and demo work belong to the [October 27–November 4, 2026 build window](../BUILD_LOG.md#build-log). Existing DappGo product code is excluded; SEC data and dependencies are [credited](../CREDITS.md). |
| Limitations | Copy the [limits](#limits); retain the distinction between recorded evaluation, post-hoc fixes, development probes, and planned work. |
| Project / demo website | https://hackathon.dappgo.com/ |
| Public source repository | https://github.com/YanlongLai/market-claim-verifier |
| Demo video URL | `VIDEO_URL_PENDING` — replace after public upload and [video checks](SUBMIT_CHECKLIST.md#video). |
| Team / teammates | Solo; no additional teammates. |
| Submitter name / email / profile | `OWNER_NAME_PENDING` / `OWNER_EMAIL_PENDING` / Owner's participating account profile. |

For the equally weighted judging criteria, the intended impact is auditable checking before sharing, supported by [saved post reports](evidence/posts-2026-10-28/); Meta tooling is documented in the [model records](#how-meta-models-are-used); technical depth is shown by the [agent and program checks](#architecture); the demo is represented by the [site](https://hackathon.dappgo.com/) and [video handoff](../demo/JUDGE_INTRO.md). [JUDGES.md](../JUDGES.md#four-equally-weighted-criteria) maps these criteria to repository evidence.

## Form answers — actual fields (read from the authenticated form, 2026-11-04)

Copy each answer into the matching field. Character limits are the form's.

| Field | Answer |
| --- | --- |
| Team Name | DappGo |
| Team Members | Yanlong (solo) |
| Which track are you submitting to? | **Indie Developer Track** (registered as indie; solo builder; judged on creativity, technical ambition and whether it works) |
| Which problem statement did you build towards? | **Build for Your World** (DappGo publishes US-market commentary; this fixes a problem found in our own fact checks) |
| Most Viral Track — X post link | `<X post URL>` (post the X cut first, then paste the link) |
| Public GitHub Repository | https://github.com/YanlongLai/market-claim-verifier |
| 3-Minute Demo Video | `<YouTube URL>` |
| Partner technologies feedback (≤150) | Baseten: fast Muse Spark Open, stable tool calling. Fireworks: works, latency tail to 100 s today. Credits and docs were enough. |
| How likely to build with Meta Model API? | Very likely |
| Overall opinion of Meta Model API | Very favorable |
| Permission checkbox | Accept (required to be judged/published) |
| Recommend Meta Model API (0–5) | 5 |
| Recommend Muse Code (0–5) | 3 (not used in this build — answer honestly; 3 = neutral) |
| Biggest obstacle | **Slow responses** (provider latency tails of 20–100 s forced a 50→90 s request budget) |
| Compared with other models for this work | Somewhat better (tool selection was reliable once the program decided verdicts) |
| What matters most when choosing a model | Agent abilities such as tool calling and multi-step tasks |
| Hardest part of switching models | Our product is tuned to our current model's behavior and prompts |
| What would stop production use | Rate limits or capacity too low for real traffic |

### Project Description (≤ 3,000 characters)

Market Claim Verifier checks every number in a finance post against SEC filings and hands back a corrected draft with citations.

The problem is one we hit in our own publishing at DappGo: a viral post quotes a real number with the wrong period, unit or comparison. "Apple pulled in $416.2 billion in fiscal Q4 2025" is the annual figure; the quarter was $102.5 billion. A fluent model summary does not catch that, and numbers like this move money.

How it works: Meta's Muse Spark reads the post, extracts each financial assertion and chooses which SEC tool to call (lookup_fact, compute_change, history_rank, list_periods). The tools return XBRL facts with evidence IDs, units, periods and filing links. Python, not the model, binds each claim to its evidence, does the arithmetic and returns the verdict: supported, contradicted or insufficient evidence. A correction strikes the disproved value and inserts the filed one, citing the 10-K/10-Q. The model proposes; the program decides.

Results: on 266 held-out text claims the agent scores 90.2% (240/266) and wrongly says "supported" once in 139; asking the same model directly, without tools, gets 20.7%. A live check costs about $0.02 and takes 6–25 s on Baseten; Fireworks and the Meta Model API are also wired. Inputs: text, screenshots (Muse OCR), PDFs, audio and video (Muse Voice Transcribe) — media becomes claim text first, verdicts still require SEC evidence.

What you can try: hackathon.dappgo.com has three stories × five input formats with saved results (no password) and live checks on any of the three providers (password = team name), with a public history that shows every run's provider, verdict, duration and cost. The repository (MIT) includes the CLI, the evaluation set frozen before execution, per-claim traces, an offline verifier that reproduces every committed data output, and a disclosure of what pre-existed (nothing in this repository — DappGo the company did).

Limits, stated plainly: text-benchmark accuracy is not accuracy on every post; coverage on real posts is reported separately; two gold labels were corrected after the run and both scorings are published; only US-GAAP SEC filers; extraction can miss claims.

### Describe your use of Meta products (≤ 3,000 characters)

Every model that runs at request time is a Meta model.

Muse Spark Open (meta-models/muse-spark-open-1026 on Baseten; accounts/fireworks/models/muse-spark-open on Fireworks) and Muse Spark 1.3 (Meta Model API) run the agent loop: claim extraction from the post, tool selection against our SEC XBRL tools, and the cited explanation draft. The three routes share one prompt registry with versioned hashes, and every recorded run stores the exact model ID.

Muse OCR (through the Meta Model API) reads screenshots; Muse Voice Transcribe (muse-voice-transcribe-1.0) transcribes audio and the audio track of video, with sampled frames read by OCR. These outputs become claim text; they are never treated as evidence.

Program design around the models: temperature 0, program-side evidence binding (the model's numbers are never allowed to become corrections — only values returned by the tools, with their evidence IDs), a reserve-before-call cost ledger per provider, and a trace of every request, tool call, result and program check that judges can open on the site.

Evaluation: 357 frozen claims (266 held out), run on all three routes; the agent-with-tools configuration reaches 323/357 on Baseten and Fireworks and 297/357 on the Meta Model API; single-shot answers from the same models reach 74, 71 and 158. The per-claim explorer and raw traces are public.

Built Oct 27 – Nov 4, 2026. Muse Code was not used.

### Why are Meta's models important to your solution? (≤ 3,000 characters)

Fact-checking a finance post is an agent problem, not a summarisation problem: the model has to split a post into checkable assertions, decide which filing fact answers each one, call a tool with the right ticker, metric and period, read what comes back and try again when the period is wrong. Muse Spark did that reliably enough that we could make the program, not the model, the judge: the model proposes tools and interpretations; Python binds evidence and decides. That split is what turns 20.7% (direct answers) into 90.2% (held-out, with tools), and it is only possible because tool calling with structured arguments works consistently across the open-weight and API routes.

The open weights matter for cost and control: Muse Spark Open on Baseten gives us about $0.02 per claim and 6–25 s, which is what makes "check every number before you post" affordable for a small publisher; the same weights on Fireworks give a second route; the Meta Model API adds OCR and speech so screenshots, PDFs, podcasts and videos enter the same pipeline. One model family across text, image and audio keeps the system simple enough that a solo developer could build, evaluate and ship it in nine days, with every run auditable.

### Social distribution (for the Most Viral bonus and reach)

The 60-second cut of the demo is posted on X first (its URL goes into the form), then cross-posted through DappGo's Postiz schedule to Threads, the Facebook Page and Instagram/Facebook Reels (9:16 variant). Links are recorded here after posting:

| Channel | URL |
| --- | --- |
| X | `<X post URL>` |
| Threads | `<URL>` |
| Facebook Page | `<URL>` |
| Instagram Reels | `<URL>` |
