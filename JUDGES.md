# Market Claim Verifier — judge guide

**Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations.**

## 3-minute path

1. **Watch:** [Demo video — publication pending](#demo-video-todo).
2. **Follow:** [One number](https://hackathon.dappgo.com/#how), then [the saved viral check](https://hackathon.dappgo.com/#recorded-run); no password.
3. **Try:** [3 stories × 5 inputs](https://hackathon.dappgo.com/#live-check), with provider choice, comparison and public history. Judges: password in the submission notes; saved examples need none.
4. **Audit:** [Held-out benchmark](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) · [Explorer](https://hackathon.dappgo.com/explorer/) · [Real-world coverage](https://hackathon.dappgo.com/wild/) · [Evidence index](docs/evidence/INDEX.md).

## Facts

| Fact | Answer |
| --- | --- |
| What it checks | [Checks financial claims against SEC filings; returns verdicts and cited corrections.](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| Coverage | [US-GAAP SEC filers: ≈8,000 companies; 23 tested. SEC XBRL periods, generally 2009 onward, through the latest filing.](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| Inputs | [Website: text ≤600 characters. CLI: text, images, PDFs, audio and video.](docs/evidence/TECHNICAL_GUIDE.md#run-it) |
| Cost & speed | [$0.01 per live check; 6–20 s live (one claim → four-assertion post). $0.02 per claim; 10 s median in the benchmark. $10/day; $60 lifetime.](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| Accuracy | [90.2% (240/266) held out; false support 1/139.](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) |
| Corrections | [Corrects disproved numbers and cites the filing. Never labels an article approved.](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json) |

## Limits

- Two gold answers were corrected after the original run; registered-gold scores remain available.
- The run manifest records a dirty working tree.
- Post-hoc rechecks reuse seen inputs and are not a fresh held-out evaluation.
- Frozen-transcript rechecks do not retest image reading or speech transcription (OCR/ASR). Extraction can miss assertions.
- Live runs share $10/day and $60 lifetime; 5 checks / 10 min per IP. Authenticated runs are public for 14 days.

Failures count as wrong; false support uses 139 reference contradicted/insufficient claims. Extraction can miss assertions. [Full limits and model IDs](docs/evidence/REVIEW_GUIDE.md#limits) · [Production receipt](docs/evidence/live-prod-2026-11-03/REPORT.md) · [Current live configuration](docs/LIVE_CHECK.md#limits-and-failure-behavior).

## Verify

`bash scripts/verify.sh` runs offline suites and rebuilds saved data in a disposable copy. [Verification guide](AGENTS.md) · [README](README.md) · [Traditional Chinese](JUDGES.zh-TW.md).

DappGo existed before; the verifier, site and evidence were built from 27 Oct 2026. [Build disclosure](BUILD_LOG.md#build-log) · [MIT](LICENSE) · [Credits](CREDITS.md).

<a id="demo-video-todo"></a>
Demo video publication is pending; the saved check and raw traces are available now.

<a id="60-second-path"></a><a id="bonus-categories"></a><a id="controlled-format-study"></a><a id="cost-accounting"></a><a id="four-equally-weighted-criteria"></a><a id="historical-results-and-failure-review"></a><a id="in-the-wild-todo"></a><a id="input-and-source-boundaries"></a><a id="limits-to-keep-in-view"></a><a id="live-check-todo"></a><a id="media-studies"></a><a id="original-text-evaluation"></a><a id="publication-links--todo-claude"></a><a id="real-company-materials-what-improved-what-remains-unresolved"></a><a id="verify-without-model-calls"></a><a id="what-is-new-during-the-hackathon"></a>
