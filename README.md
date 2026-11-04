# Market Claim Verifier

![Auditor robot comparing a post with a filing](docs/site/img/readme-robot.gif)
<!-- Placeholder still; host capture: python3 scripts/capture_readme_gif.py -->

**Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations.**

[Try the site](https://hackathon.dappgo.com/) · [Saved check](https://hackathon.dappgo.com/#recorded-run) · [Judge guide](JUDGES.md) · [Traditional Chinese](README.zh-TW.md)

## What it does

- Extracts financial claims from text or media.
- Muse Spark chooses SEC tools; Python checks numbers, periods and evidence IDs.
- Returns supported, contradicted or insufficient evidence, plus a cited corrected draft for disproved numbers.

## Why

DappGo publishes US-market commentary.
An internal check found right numbers paired with wrong periods, units or comparisons.
The model proposes; the program decides.

## How it works

![Post → Muse Spark → SEC facts → Python verdict → corrected draft](docs/site/img/architecture-v4.svg)

1. Read the input and extract each financial assertion.
2. Muse Spark chooses the next SEC tool call.
3. Bind returned evidence to the company, metric and period.
4. Python calculates the verdict and checks numeric tolerance.
5. Correct only disproved numbers, citing the filing.

[Follow one number on the site](https://hackathon.dappgo.com/#how) · [Code and model responsibilities](docs/evidence/TECHNICAL_GUIDE.md#agentic-muse-chooses-the-next-check-python-checks-the-answer)

## Try it

On the [site](https://hackathon.dappgo.com/#live-check): 3 stories × 5 inputs (text, image, PDF, audio, video). Choose Baseten, Fireworks or Meta Model API, or compare all three. Public history reopens full results; **Edit & re-run** restores story, input and provider. Judges: password in the submission notes; saved examples need none.

CLI examples after [local setup](#run-locally). The first command is offline; the other two require the chosen provider key and spend within their explicit budget.

```sh
uv run python -m claimcheck verify --provider baseten --dry-run 'META Q2 2025 revenue was $47.5B'
uv run python -m claimcheck verify --provider baseten --budget 1 'META Q2 2025 revenue was $47.5B'
uv run python -m claimcheck post examples/posts/bigtech-thread.txt --provider baseten --budget 1
```

## Facts

| Fact | Answer |
| --- | --- |
| What it checks | [Checks financial claims against SEC filings; returns verdicts and cited corrections.](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| Coverage | [US-GAAP SEC filers: ≈8,000 companies; 23 tested. SEC XBRL periods, generally 2009 onward, through the latest filing.](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| Inputs | [Website: text ≤600 characters. CLI: text, images, PDFs, audio and video.](docs/evidence/TECHNICAL_GUIDE.md#run-it) |
| Cost & speed | [$0.01 per live check; 6–20 s live (one claim → four-assertion post). $0.02 per claim; 10 s median in the benchmark. $10/day; $60 lifetime.](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| Accuracy | [90.2% (240/266) held out; false support 1/139.](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) |
| Corrections | [Corrects disproved numbers and cites the filing. Never labels an article approved.](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json) |

## Evidence & honesty

[Held-out benchmark](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) · [Registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) · [Run manifest](docs/evidence/eval-v2-2026-10-27/manifest.json) · [Real-world coverage](https://hackathon.dappgo.com/wild/) · [Explorer](https://hackathon.dappgo.com/explorer/) · [Evidence index](docs/evidence/INDEX.md) · [Full limits](docs/evidence/REVIEW_GUIDE.md#limits)

- Two gold answers were corrected after the original run; registered-gold scores remain available.
- The run manifest records a dirty working tree.
- Post-hoc rechecks reuse seen inputs and are not a fresh held-out evaluation.
- Frozen-transcript rechecks do not retest image reading or speech transcription (OCR/ASR). Extraction can miss assertions.
- Live runs share $10/day and $60 lifetime; 5 checks / 10 min per IP. Authenticated runs are public for 14 days.

## Repository map

| Path | Purpose |
| --- | --- |
| [src/claimcheck/](src/claimcheck) | Tool loop, providers, program checks and corrections |
| [prompts/](prompts) | Versioned prompt text and hashes |
| [eval/v2/](eval/v2) | Frozen claims, corrected gold and reference calculations |
| [docs/evidence/](docs/evidence) | Reports, raw redacted traces and failed attempts |
| [docs/site/](docs/site) | English site, local art and saved-check data |
| [docs/zh/](docs/zh) | Generated Traditional Chinese mirror |
| [server/live/](server/live) | Self-hosted Python service and durable history |
| [functions/api/](functions/api) | Same-origin Pages API forwarding |
| [tests/](tests) | Offline fixtures and product/site regressions |
| [demo/](demo) | Demo source, narration and retained production records |

## Run locally

Python 3.12–3.14, uv and Node 22+:

```sh
uv sync --frozen
python3 scripts/serve_site.py
bash scripts/verify.sh
```

The local preview serves committed files. Verification uses a disposable copy, removes credentials and blocks network access during tests and builders. After the dependency cache is populated, `UV_OFFLINE=1 bash scripts/verify.sh` also sets up dependencies offline. [Verification guide](AGENTS.md) · [Retained test records](docs/TEST_RECORDS.md) · [CLI details](docs/evidence/TECHNICAL_GUIDE.md#run-it)

To replace the GIF placeholder with a 720 px, 6–8 s capture under 3 MB, see [the capture script](scripts/capture_readme_gif.py). It uses Playwright on the host and reads only the local saved scene.

## Licence

[MIT](LICENSE) · [Credits](CREDITS.md). DappGo existed before; this verifier, site and evidence were built during the hackathon, from 27 Oct 2026. [Build disclosure](BUILD_LOG.md#build-log).

<a id="agentic-muse-chooses-the-next-check-python-checks-the-answer"></a><a id="check-a-whole-post"></a><a id="cost-speed-and-provider-choice"></a><a id="evaluation"></a><a id="evidence-you-can-audit"></a><a id="gap-score"></a><a id="how-meta-models-are-used"></a><a id="how-the-system-got-there"></a><a id="key-results"></a><a id="l4-earnings-release-evidence"></a><a id="limitations"></a><a id="local-pdf-input"></a><a id="one-real-run"></a><a id="other-inputs"></a><a id="real-results"></a><a id="real-world-test"></a><a id="reproduce-or-extend"></a><a id="review-several-files-for-one-stock"></a><a id="run-it"></a><a id="support-and-boundaries"></a><a id="technical-notes"></a><a id="technical-reference"></a><a id="text-verification-266-held-out-claims"></a><a id="try-it"></a><a id="what-it-does"></a><a id="why-meta-open-weights"></a><a id="why-you-can-trust-a-verdict"></a>
