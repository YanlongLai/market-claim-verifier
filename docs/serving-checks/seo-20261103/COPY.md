# Exact SEO copy — 2026-11-03

This records the final authored copy. Page titles and descriptions are repeated verbatim in OG/Twitter metadata; descriptions also appear in JSON-LD. Existing visible H1s and COPY translations are retained.

## Titles and descriptions

### Landing — English

Title: SEC fact-checks for finance posts · Market claim verifier

Description: Check finance posts against SEC filings. On 357 claims, Baseten scored 90.5% with SEC lookup vs 20.7% without. Explore saved verdicts and filing evidence.

Description length: 154 Unicode characters.

### Landing — Traditional Chinese

Title: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

Description: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

Description length: 151 Unicode characters.

### Explorer — English

Title: How SEC evidence changes model accuracy · Market claim verifier

Description: Explore 357 financial claims and 2,142 verdicts: SEC-tool agents vs single-shot answers, with corrected reference labels, filing evidence and errors.

Description length: 149 Unicode characters.

Dataset name: Market claim verifier — SEC evaluation set

Count labels: Financial claims, Recorded verdicts.

### Explorer — Traditional Chinese

Title: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

Description: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

Description length: 110 Unicode characters.

Dataset name: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

Count labels: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

## Image alternatives

English OG and explorer Twitter (existing landing-page OG wording): Market claim verifier comparing an example finance post with its saved SEC filing, alongside the auditor robot.

English landing Twitter (retained): A real post and SEC filing in the Market claim verifier demo.

Traditional Chinese OG/Twitter: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

## Visible copy changes

English footer: All repository code and demo work were created during the hackathon.

Traditional Chinese footer: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

404 navigation addition: [See the separate Traditional Chinese copy](COPY.zh-TW.md).

The footer follows [README.md](../../../README.md#reproduce-or-extend); it makes no new claim about a named event. The generated Chinese body and accessibility labels reuse the existing [COPY dictionary](../../site/script.js) and can be read in full in the [generated page](../../zh/index.html). Language link labels remain English / Traditional Chinese. The static results caption uses the existing Chinese template with the published claim count.

## Structured data and crawler directives

The application name remains Market claim verifier. Both WebApplication records describe a free Web application in FinanceApplication, published by DappGo (https://dappgo.com), and link the public GitHub repository. Dataset counts are 357 financial claims and 2,142 recorded verdicts. No ratings or dataset-license assertion were added; the README specifies an MIT code license, without an explicit evaluation-dataset license grant.

robots.txt addition: `Content-Signal: search=yes, ai-input=yes, ai-train=no`

Sitemap lastmod: 2026-11-03, the date these four pages were updated. Canonical, hreflang and schema URLs refer only to the four published routes and existing public source pages.

## Source of every new numerical claim

| Number | Published source |
| --- | --- |
| 357 claims | [site.json](../../site/data/site.json), `eval.claim_count`; independently counted in [explorer/data.json](../../explorer/data.json) and already stated in both explorer introductions. |
| 90.5% with SEC lookup | [site.json](../../site/data/site.json), `systems[id=agent@baseten].accuracy`, using the existing landing chart’s one-decimal percentage format. This is the full-set score displayed in “Does it work?”. |
| 20.7% without SEC lookup | [site.json](../../site/data/site.json), `systems[id=single_shot@baseten].accuracy`, using that same existing chart format. |
| 2,142 verdicts | [site.json](../../site/data/site.json), `eval.result_count`; already stated in both explorer introductions and independently counted from the explorer’s per-claim results. |

These are saved full-set workflow results with corrected reference labels and failures counted wrong. They are not described as fresh held-out results. The [original report](../../evidence/eval-v2-2026-10-27/REPORT.md) and [post-hoc report](../../evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md) retain their separate scopes.

## Complete new crawler-guide copy

The production file is [docs/llms.txt](../../llms.txt). Its complete text follows:

```markdown
# Market claim verifier

> Check finance-post numbers against SEC filings and inspect the evidence behind each verdict. The website replays saved checks; fresh checks run through the repository's CLI.

## Reading policy

You may search, read and cite these public pages. Please do not use them for model training. The robots.txt Content-Signal states search=yes, ai-input=yes, ai-train=no; it expresses a preference, not an access-control mechanism or a guarantee of crawler behavior.

## How verdicts are decided

The model proposes; the program decides. Meta Muse models identify claims, select SEC lookup tools and propose evidence. Program rules parse the claim's numbers, precision, periods and comparisons, validate evidence IDs and quotations, perform calculations and determine the final supported, contradicted or insufficient verdict. The model cannot override that result.

## Start here

- [English website](https://hackathon.dappgo.com/)
- [Traditional Chinese site](https://hackathon.dappgo.com/zh/)
- [Results explorer — English](https://hackathon.dappgo.com/explorer/)
- [Explorer — Traditional Chinese](https://hackathon.dappgo.com/explorer/index.zh.html)
- [Published landing-page data](https://hackathon.dappgo.com/data/site.json)
- [Per-claim explorer data](https://hackathon.dappgo.com/explorer/data.json)
- [GitHub repository and CLI instructions](https://github.com/YanlongLai/market-claim-verifier)
- [DappGo](https://dappgo.com)

## Evaluation evidence

- [Original evaluation report](https://hackathon.dappgo.com/evidence/eval-v2-2026-10-27/REPORT.md): the explorer contains 357 claims and 2,142 verdicts. The landing page shows Baseten accuracy of 90.5% with SEC lookup and 20.7% without. These are recorded workflow results on the full evaluation set, using corrected reference labels; incomplete and provider-error results count as wrong.
- [Registered-gold report](https://hackathon.dappgo.com/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md): original reference-label scores remain available alongside the corrections.
- [Post-hoc agent rerun](https://hackathon.dappgo.com/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md): fixes followed inspection of the original errors. This is a regression recheck on previously seen claims, not a fresh held-out evaluation. Empty single-shot summary rows are not results.
- [Earnings-release development report](https://hackathon.dappgo.com/evidence/eval-l4-2026-10-29/ANALYSIS.md): furnished, unaudited release evidence has different limits from SEC XBRL facts.
- [Judge guide and limits](https://github.com/YanlongLai/market-claim-verifier/blob/main/JUDGES.md#limits)

## Limits and citation

Scope is US equities and supported SEC facts or eligible issuer-release passages. Opinions, forecasts without matching evidence, missing facts and ambiguous periods can remain uncheckable. Tagging, restatements, source coverage and derived quarters limit evidence. OCR, transcription and sampled video frames can lose context; speakers are unverified.

Cite the specific saved report or filing, retain its date, evidence tier, reference-label corrections and post-hoc status, and distinguish benchmark correctness from user impact or broad real-world accuracy. The run manifest records a dirty working tree. Website examples do not perform a live model call or accept browser uploads. This is an informational research tool, not personalized investment advice.
```
