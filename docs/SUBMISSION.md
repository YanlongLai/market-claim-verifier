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
