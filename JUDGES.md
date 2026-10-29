# Market Claim Verifier — judge guide

Checks financial sentences and posts against SEC filings, returning cited `supported`, `contradicted`, or `insufficient_evidence` verdicts ([agent](src/claimcheck/agent.py), [post checker](src/claimcheck/post.py)).
Muse Spark chooses tools and drafts explanations; Python checks numbers, periods and evidence IDs ([checks](src/claimcheck/checks.py), [real trace](docs/evidence/2026-10-27/20261027T222758Z-8959a100.json)).

## 60-second path

1. Open the [website](https://yanlonglai.github.io/market-claim-verifier/site/) ([site source](docs/site/index.html)) and its saved post/filing example.
2. **Demo video: publication link pending.** [Demo records](demo/BUILD_LOG.md) document the approved video; use the [opening disclosure](demo/JUDGE_INTRO.md): **“Nothing in this repository pre-existed the hackathon.”** ([build log](BUILD_LOG.md#build-log)).
3. Run `sh scripts/verify.sh`: offline tests, figure rebuild/check, byte-identical site rebuild, and Markdown links ([script](scripts/verify.sh), [prerequisites and expected output](AGENTS.md#offline-verification)).

## Four equally weighted criteria

| Impact | Concrete evidence |
| --- | --- |
| Auditable checks before sharing financial claims | [English/Chinese post reports](docs/evidence/posts-2026-10-28/), [verdict cards](docs/figures/verdict-cards.svg). On **357 claims**, original v2 agents: **90.5%** Baseten/Fireworks vs **20.7% / 19.9%** single-shot; Meta API **83.2%** vs **44.3%** ([REPORT](docs/evidence/eval-v2-2026-10-27/REPORT.md), [figure](docs/figures/eval-summary.svg)). Benchmark results, not measured user outcomes. |

| Use of Meta AI tooling | Concrete evidence |
| --- | --- |
| **Muse Spark 1.3 via Meta Model API**; **Muse Spark Open on Baseten/Fireworks (open weights)** | [Exact IDs/adapters](src/claimcheck/providers.py), [recorded models](docs/evidence/eval-v2-2026-10-27/manifest.json), [open-weights diagram](docs/diagrams/providers.mmd), [tool-loop prompt](prompts/agent-tool-loop-instructions.md), [extraction prompt](prompts/post-extraction.md), [prompt registry](src/claimcheck/prompts.py). Recorded verifier calls use Meta models; offline media tooling is separately [credited](CREDITS.md#media-and-dependencies). |

| Technical depth | Concrete evidence |
| --- | --- |
| Agentic tool selection → SEC evidence → program verdict | [Sequence](docs/diagrams/real-run-sequence.mmd), [raw tool/response trace](docs/evidence/2026-10-27/20261027T222758Z-8959a100.json), [budget reservations](src/claimcheck/budget.py), [L1–L3 provenance](docs/DATA_SOURCES.md), [data quality](docs/DATA_QUALITY.md), [independent gold](eval/build_gold.py), [replay tests](tests/test_live_replay.py), [provider tests](tests/test_fireworks_provider.py). Build/failure record: [Day 1](BUILD_LOG.md#day-1--2026-10-27-tue), [next iteration](BUILD_LOG.md#day-2-scope--started-2026-10-27-tue-afternoon), [post checking](BUILD_LOG.md#day-3--2026-10-28-wed). |

| Demo | Concrete evidence |
| --- | --- |
| Saved examples, filing passages and reproducible verification | [Site source](docs/site/index.html), [per-claim explorer](docs/explorer/index.html), [post/filing example](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.html), [storyboard](demo/storyboard.yaml), [video approval/rebuild record](demo/BUILD_LOG.md), [verification commands](AGENTS.md). |

## What is new during the hackathon

**Everything in this repository was built for this event; no repository code pre-existed** ([disclosure/window: Oct 27–Nov 4, 2026](BUILD_LOG.md#build-log)). First commit: **`7c5670b`, 2026-10-27 14:20:17 −07:00**; [dated commit/evidence map](CHANGELOG.md#day-1--2026-10-27) and [Git verification command](AGENTS.md#verify-the-build-window). SEC data and dependencies are [credited](CREDITS.md).

## Limits to keep in view

- The **357-claim** v2 set includes development claims; **266** are held out. Two gold corrections and the dirty-worktree manifest are disclosed ([original/corrected results](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md), [corrected claims](eval/v2/claims-v2-corrected.jsonl), [manifest](docs/evidence/eval-v2-2026-10-27/manifest.json)).
- Later **92.2% / 91.0% / 85.4%** agent results are **post-hoc**, after inspecting failures; zero false-supported verdicts on that rerun do not establish a general error rate ([rerun report](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md)).
- Current ground truth is SEC XBRL, with tagging/restatement and period limitations; forecasts and valuation opinions are skipped. L4/L5, market multiples and Taiwan filings are **planned** ([source policy](docs/DATA_SOURCES.md), [post checker](src/claimcheck/post.py), [roadmap](ROADMAP.md)). The site replays saved evidence; fresh model runs require keys/network ([site builder](docs/scripts/build_site.py), [runtime setup](README.md#run-it)).

Code: [MIT](LICENSE). Data/media: [credits](CREDITS.md). AI readers: [llms.txt](llms.txt) → [AGENTS.md](AGENTS.md).
