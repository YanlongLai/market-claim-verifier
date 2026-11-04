# Market Claim Verifier — judge guide

**Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations.**

[Live site](https://hackathon.dappgo.com/) · [README](README.md) · [Evidence index](docs/evidence/INDEX.md)

## For judges — 3-minute path

| Step | Open | Inspect |
| --- | --- | --- |
| Watch | [Demo video — publication pending](#demo-video-todo) | Post → evidence → program verdict → corrected draft. |
| Try | [Live check](https://hackathon.dappgo.com/#live-check) | Choose a story, input and provider. Password: the team name (dappgo). |
| Replay | [Saved check](https://hackathon.dappgo.com/#recorded-run) | No password; open the corrected draft, SEC citations and agent trace. |
| Audit | [Original benchmark](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) | Read held-out results, failures and the corrected-gold disclosure. |

## The idea

DappGo's internal fact checking found right numbers paired with wrong periods, units or comparisons.
Muse Spark chooses SEC tools; Python binds evidence, calculates the verdict and builds cited corrections.
**The model proposes; the program decides.** [Architecture and walkthrough](README.md#the-idea).

## Facts

| Fact | Answer and evidence |
| --- | --- |
| What it does | Extracts assertions, checks SEC evidence and returns verdicts, a corrected draft, trace and receipt. [Correction report](docs/evidence/corrected-draft-2026-11-03/REPORT.md). |
| Coverage | US-GAAP SEC filers: ≈8,000 companies; 23 tested. SEC XBRL periods, generally 2009 onward through the latest filing. Annual, quarterly and growth comparisons. [Scope report](docs/evidence/REVIEW_GUIDE.md#facts-in-detail). |
| Inputs | Website: text ≤600 characters and 3 stories × 5 packaged inputs. CLI: text, images, PDFs, audio and video. [Site report](docs/evidence/try-v3-site-2026-11-03/REPORT.md), [format report](docs/evidence/input-formats-2026-10-30/REPORT.md). |
| Providers | Meta Model API, Baseten and Fireworks, all Meta verifier models; media uses Meta OCR/ASR. [Recorded models](docs/evidence/eval-v2-2026-10-27/manifest.json). |
| Cost & speed | Live headline: $0.01 / 6 s. Planning band: $0.01–0.04 / 6–90 s by provider, plus media preprocessing. Benchmark: $0.02 per claim, 10 s median, p95 21 s. [Receipts and scope](docs/evidence/readme-v3-2026-11-04/REPORT.md#cost-and-speed). |
| Accuracy | 90.2% (240/266) held out; false support 1/139 reference contradicted/insufficient claims. Failures count as wrong. [Original report](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics). |
| Corrections | Strike disproved numbers, insert program values and cite component filings. Only uniquely bound checked assertions change; never article approval. [Retained Apple example](docs/evidence/corrected-draft-2026-11-03/REPORT.md#retained-apple-example). |
| Live limits | Per-provider daily/lifetime caps; 5 checks / 10 min per IP. Authenticated inputs/results are public for 14 days. [Cap settings and migration](deploy/README.md#setting-provider-caps). |

## Accuracy & evidence

The [README benchmark table](README.md#original-benchmark) compares agent and single-shot methods by provider,
including the historical all-claim column separately from held-out results.
[78 Threads / 80 news](docs/evidence/real-world-2026-11-02/REPORT.md) measure real-world coverage;
coverage ≠ accuracy. [Explorer](https://hackathon.dappgo.com/explorer/) · [Real-world explorer](https://hackathon.dappgo.com/wild/).

<a id="limits"></a>

## Limits & honesty

- Two gold answers were corrected after the original run; [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) remain available.
- The original [manifest](docs/evidence/eval-v2-2026-10-27/manifest.json) records a dirty working tree.
- [Post-hoc rechecks](docs/evidence/real-world-2026-11-03-fixcheck/REPORT.md) reuse seen inputs; frozen transcripts do not retest OCR/ASR.
- Extraction can miss assertions. Ambiguous periods, sampled frames and missing evidence limit coverage.
- Compare spends sequentially from independent provider limits and an aggregate ceiling; exhausted providers are labeled and skipped. The planning band is not an observed extreme or an SLA; saved receipts keep their historical values.

[Full limits](docs/evidence/REVIEW_GUIDE.md#limits) · [Provider/input boundaries](docs/PROVIDERS.md) · [Test-record policy](docs/TEST_RECORDS.md).

## Verify offline

```sh
bash scripts/verify.sh
```

Locked dependencies are installed first; verification then runs offline in a disposable copy.
[Verification guide](AGENTS.md) · [Recorded verification](docs/VERIFICATION.md).

## Licence & credits

DappGo existed before the hackathon; the verifier, site and evidence were built during it.
[Build disclosure](BUILD_LOG.md#build-log) · [MIT](LICENSE) · [Credits](CREDITS.md) · [Traditional Chinese](JUDGES.zh-TW.md).

<a id="demo-video-todo"></a>
Demo video publication is pending; the saved check and raw traces are available now.

<a id="60-second-path"></a><a id="bonus-categories"></a><a id="controlled-format-study"></a><a id="cost-accounting"></a><a id="four-equally-weighted-criteria"></a><a id="historical-results-and-failure-review"></a><a id="in-the-wild-todo"></a><a id="input-and-source-boundaries"></a><a id="limits-to-keep-in-view"></a><a id="live-check-todo"></a><a id="media-studies"></a><a id="original-text-evaluation"></a><a id="publication-links--todo-claude"></a><a id="real-company-materials-what-improved-what-remains-unresolved"></a><a id="verify-without-model-calls"></a><a id="what-is-new-during-the-hackathon"></a>
