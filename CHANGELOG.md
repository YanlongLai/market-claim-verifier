# Changelog

Dates below are **America/Los_Angeles** calendar days counted from the hackathon's October 27 start ([build window/disclosure](BUILD_LOG.md#build-log)). The build log's “Day 2” and “Day 3” headings are iteration labels: the former started October 27, the latter October 28. [Demo build records](demo/BUILD_LOG.md) use UTC, so their October 29 evening-work records fall on October 28 locally.

Commit IDs below identify the Git history; `git show <id>` reads each locally. [AGENTS.md](AGENTS.md#verify-the-build-window) gives commands to inspect dates. No future work is recorded as completed; plans are in [ROADMAP.md](ROADMAP.md).

## Day 1 — 2026-10-27

The first/root commit is **`7c5670b84e6052db9fa67fd86606fb2ee11ee42c`**, authored **2026-10-27T14:20:17-07:00**, “Day 1: EDGAR fact tool, budget ledger, Meta Responses tool-call loop.” No repository code pre-existed ([build disclosure](BUILD_LOG.md#build-log)).

- Created the SEC EDGAR fact tools, Meta Responses agent loop, program checks and reserve-before-call budget ledger (`7c5670b`, `97b5365`, `f0acc85`); recorded [Day 1 live evidence](BUILD_LOG.md#day-1--2026-10-27-tue) and [traces](docs/evidence/2026-10-27/).
- Added claim-aware precision/comparators, changes, record/first-time checks and replay regressions (`ffd012f`, `ba4349c`, `4102dff`); [iteration record](BUILD_LOG.md#day-2-scope--started-2026-10-27-tue-afternoon), [replay tests](tests/test_live_replay.py).
- Added the first labeled evaluation, independent gold builder and request/response/prompt recording (`f54f5d6`, `7f07973`); [claim set](eval/claims.yaml), [gold builder](eval/build_gold.py), [preserved partial run](docs/evidence/eval-2026-10-27-aborted-partial/README.md).
- Added Muse Spark Open adapters for Baseten and Fireworks and the six-system evaluation (`2aee01d`, `e7eeb02`, `42e7bd4`); [provider code](src/claimcheck/providers.py), [six-system report](docs/evidence/eval-2026-10-27-r4-all/REPORT.md).
- Added judge-facing diagrams, figures and visual prompts; used evaluation failures to refine program checks (`7709b88`, `660da1f`, `bc0e834`, `63ccffe`); [figure registry](docs/figures/figures.json), [prompts](docs/prompts/), [failure/fix record](README.md#how-the-system-got-there).
- Added L1–L3 provenance, restatement/confirmation strength, source registry and quality reports; corrected fiscal labels and excluded annual-as-quarter tags (`8c352e2`, `efc08f6`, `564d863`); [source policy](docs/DATA_SOURCES.md), [quality findings](docs/DATA_QUALITY.md).
- Froze the 357-claim v2 set before execution, recorded six-system results, and retained gold corrections/lookup fixes (`5d90b3b`, `61cbdc6`); [frozen manifest](eval/v2/MANIFEST.json), [original-gold report](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md), [corrected-gold report](docs/evidence/eval-v2-2026-10-27/REPORT.md), [run account](BUILD_LOG.md#eval-v2-run-357-claims--6-systems--2026-10-27-tue-night-utc-2026-10-28-03090627).

## Day 3 — 2026-10-28

- Added the per-claim results explorer and bilingual project site (`95267d3`, `d5e7bbc`, `5b94526`, `aefcc2d`); [explorer](docs/explorer/index.html), [site](docs/site/index.html), [data builder](docs/scripts/build_site.py).
- Added whole-post claim extraction, exact-quote/number screening, English/Chinese examples, unit/multiplier fixes and both YoY source facts (`6190c17`, `f4a1533`); [post checker](src/claimcheck/post.py), [saved reports](docs/evidence/posts-2026-10-28/), [build-log account](BUILD_LOG.md#day-3--2026-10-28-wed).
- Added the exact-passage filing pop-up (`7675b40`); [filing excerpts](docs/scripts/filing_excerpts.py), [site build summary](docs/site/BUILD_SUMMARY.md).
- Added program-side fiscal/calendar ambiguity checks, ran the three-agent post-hoc regression, and showed it separately (`102b20c`, `7152c81`, `2c1f6e1`); [rerun report](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md), [fix regressions](tests/test_eval_fixes.py).
- Added social assets, the annual-as-quarter demo post and evidence-driven site stamp animation (`aa606c6`, `0ac9789`, `abff7c7`, `77b00fb`); [demo post report](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.html), [stamp record](docs/site/STAMPS_SUMMARY.md).
- Recorded media tooling/process and built the demo storyboard/motion/voice/caption pipeline (`28a95f5`, `40f199c`, `d286602`); [process](docs/PROCESS-media.md), [playbook](docs/playbooks/media/README.md), [demo tests](demo/tests/).
- Recorded the narration license, media-loss incident, byte-identical v005/v006 rebuild and final Owner approval (`811e80b`, `e4e2215`, `f06ac10`); [demo build log](demo/BUILD_LOG.md), [media/license record](docs/PROCESS-media.md#demo-video).

## Day 4 — 2026-10-29

- Added [JUDGES.md](JUDGES.md), [llms.txt](llms.txt), [AGENTS.md](AGENTS.md), README skimmer navigation, [credits](CREDITS.md), this dated history and a [planned-only roadmap](ROADMAP.md).
- Added [one-command offline verification](scripts/verify.sh), [push/PR CI](.github/workflows/verify.yml), [Markdown file/anchor checking](scripts/check_links.py) and the [verification receipt](docs/VERIFICATION.md). Refreshed stale figure-input metadata and repaired local-output Markdown links; product code, recorded results and chart values are unchanged.
- Removed test dependencies on ignored SEC caches, Git metadata, narrator audio and local subtitle exports using [committed SEC fixtures](tests/fixtures/sec-offline/README.md), [metadata injection](tests/test_eval_recording.py), [synthetic test references](demo/tests/test_motion.py) and [frozen subtitle text](demo/tests/fixtures/README.md). Added [narrow secret-scan exceptions](.gitleaks.toml) for recorded SHA-256 media cache identifiers.
- Added the required [pre-existing-work opening disclosure](demo/JUDGE_INTRO.md) for presentation/publication. The video publication link remains pending; no upload is recorded.
- Added L4 evidence: SEC 8-K Item 2.02 earnings releases (Ex 99.1, HTML Ex 99.2) for guidance and non-GAAP claims, with program-verified quote offsets and XBRL precedence; froze a 32-claim gold set before the run; Baseten agent scored 31/32 with 0/19 false-supported for $0.7157 ([analysis](docs/evidence/eval-l4-2026-10-29/ANALYSIS.md), [release checks](src/claimcheck/release_checks.py)).

## Day 5 iteration — 2026-10-30

- Added the US-equity-only [delivery plan](docs/DAY5_PLAN.md) with ordered acceptance gates; general web pages and Taiwan are outside current scope.
- Published [provider modalities, integration boundaries, pricing and recorded quality](docs/PROVIDERS.md). No account balance or untested endpoint support is claimed.
- Ingestion JSON/HTML now separates proposed, accepted, program-checked, rejected and failed claims. Full-content recall remains explicitly unknown rather than inferred from extracted rows.

- Added local native-text PDF ingestion with page provenance, explicit unreadable-page errors and encrypted/malformed input rejection. No general URL ingestion or PDF OCR is claimed.

- Added the versioned evidence export contract and SEC release connector, wired into verified L4 quotes. Includes source/text hashes, quote locators, fact ranges and authority boundaries, plus a no-network META fixture export example.

- Explorer now defaults to English and offers Traditional Chinese with preserved claim deep links; recorded evidence remains unchanged.

- Added a reproducible three-outcome judge walkthrough using one recorded META outlook: matching range, altered range and wrong period. Publishes exact source locators, raw/text hashes, full program checks and a zero-incremental-API-cost breakdown explicitly limited to offline execution.

- Added `us-financial-v1` policy identity and `--as-of` for edgar/verify/post/ingest. Filters SEC facts before normalization/derivation and release evidence before admission/reuse, records policy in reports/traces, and preserves no-cutoff model replay payloads. Historical archive and intraday reconstruction remain out of scope.

- Added a bounded serial ingestion queue with frozen source/input snapshots, versioned execution identity, successful-job reuse, crash/partial-result review states and conservative per-job admission caps. Added stage/attempt cost estimates and retained-reservation reporting; provider billed amounts remain unknown.

## Input-format evidence refresh — 2026-10-30

- Clarified README support symbols: integration is separate from accuracy, full-content coverage and vendor-native modalities.
- Added six preselected paid format probes with a shared $3 cap: Markdown, JPEG, WebP, MP3, silent MP4 and native-text PDF. [Results, per-provider spend, limits and raw reports](docs/evidence/input-formats-2026-10-30/REPORT.md) remain auditable; no failed attempt is discarded.
- Extended the existing probe runner to Fireworks text verification, with three equal provider budget partitions; removed stale prior-run budget metadata. Added an offline format-report builder that checks input hashes and cost reconciliation.
- Added the [test-record index and reuse contract](docs/TEST_RECORDS.md), frozen raw/normalized per-channel text, and a suite runner that records command/log/exit-code history without overwriting prior runs.

## Fresh SEC snapshot and real issuer inputs — 2026-10-30

- Fetched and archived 47 raw SEC responses for the existing 23-company scope, with hashes, retrieval timestamps, date-filtered coverage and offline restoration. [Snapshot report](docs/evidence/sec-refresh-2026-10-30/REPORT.md). Historical fixtures/default cache remain unchanged; the new snapshot is selected explicitly.
- Added [three real Tesla slide images and official Microsoft/Tesla presentation/webcast sources](docs/evidence/real-media-2026-10-30/README.md), clearly separating prepared inputs from un-downloaded recordings and unevaluated candidates. No paid model calls.
- Offline verification: 884 product tests, 149 demo Python tests and 55 Node tests passed; all 47 archives restored with verified hashes and CIK identity.

## 2026-10-30 — paired media benchmark and single-stock document review

- Published same-input nine-format results, native-image probes, full input/output artifacts, frozen source archives and spend audits; corrected English/Chinese support tables.
- Added bounded stock context and contiguous table quotation rules to multi-file review; retained both real Tesla follow-up attempts and an evidence-linked summary.
- Final offline verification passed 901 product, 149 demo Python and 55 Node tests. Upload UI, validated AI narrative and real-recording accuracy evaluation remain planned.

## 2026-10-30 — explain unchecked chart content

Added per-channel coverage diagnostics and actionable next steps to ingestion and stock summaries. Retained the real Tesla chart diagnosis and offline summary replay, without changing paid records or claiming chart geometry is verified.

## 2026-10-30 — genuine webcast audio/video corpus

Added a real Microsoft CFO webcast clip and its audio track, preregistered six-case test, retained API inputs/outputs and cost accounting. Coverage diagnostics now also flag unverified geometry in sampled video frames. Real-input period and table-header failures remain visible; no synthetic benchmark scores were replaced.

## 2026-10-30 — reviewed event periods and program explanations

Added optional reviewed event JSON to stock review, with queue identity and separate provenance. Resolve short fiscal-year headers only with a matching full-year anchor; retain invented-number and conflicting-context guards. Final summaries now follow program outcomes and preserve model prose separately. Real-AV offline replay retains all original paid results.
