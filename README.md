# Market Claim Verifier

**Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations.**
Paste → Muse finds SEC evidence → Python decides + corrected draft.

Website: text ≤600 characters.
$0.01 per live check.
6 s live.
90.2% (240/266) held-out accuracy.

[Live check](https://hackathon.dappgo.com/#live-check) (password-protected; saved examples need none) · [Saved check](https://hackathon.dappgo.com/#recorded-run)
[Judges](JUDGES.md) · [Evidence](docs/evidence/INDEX.md) · [繁體中文](README.zh-TW.md)

## Facts

| Question | Answer |
| --- | --- |
| What it does | Checks financial claims against SEC filings; returns verdicts and cited corrections.<br>用 SEC 申報核對財務主張，提供判定與附出處的修正。 |
| Time span | SEC XBRL periods, generally 2009 onward, through the latest filing.<br>SEC XBRL 申報期間，大致自 2009 年起至最新申報。 |
| Which US stocks | US-GAAP SEC filers: ≈8,000 companies; 23 tested.<br>US-GAAP 美股申報公司：約 8,000 家，已測試 23 家。 |
| Inputs | Website: text ≤600 characters. CLI: text, images, PDFs, audio and video.<br>網站：≤600 字元。CLI：文字、圖片、PDF、音訊與影片。 |
| Price | $0.01 per live check; $0.02 per claim in the benchmark.<br>即時查核每次 $0.01；基準測試每題 $0.02。 |
| Speed | 6 s live; 10 s median in the benchmark.<br>即時 6 秒；基準測試中位數 10 秒。 |
| Accuracy | 90.2% (240/266) held out; false support 1/139.<br>保留測試 90.2% (240/266)；誤判為支持 1/139。 |
| Fix the article? | Corrects disproved numbers and cites the filing.<br>修正被證明錯誤的數字，並附申報出處。 |

[Facts in detail](docs/evidence/REVIEW_GUIDE.md#facts-in-detail).

## Why it exists

DappGo publishes US-market commentary. An internal fact check found posts with the right number but the wrong period, unit or comparison. **The model proposes, the program decides.** Muse Spark picks SEC tools; Python computes and validates the verdict. [Agent, tools and trace](docs/evidence/TECHNICAL_GUIDE.md#agentic-muse-chooses-the-next-check-python-checks-the-answer).

## Evidence and limits

[Original held-out text results](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics): **90.2% (240/266)**, false support **1/139** reference contradicted/insufficient claims. Corrected gold includes two changes; [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) remain available. These are benchmark results, not a guarantee on every post. Extraction can miss assertions; coverage ≠ accuracy; post-hoc rechecks are not held out.

[Production check, 2026-11-03](docs/evidence/live-prod-2026-11-03/REPORT.md): Baseten `meta-models/muse-spark-open-1026`, $0.01 per live check, 6 s live; $3/day live budget. [In the wild](https://hackathon.dappgo.com/wild/) · [Evidence index](docs/evidence/INDEX.md) · [Detailed review and honesty labels](docs/evidence/REVIEW_GUIDE.md#limits).

## Verify offline

[Run locally](docs/evidence/TECHNICAL_GUIDE.md#run-it) · [Video — TODO (Claude)](JUDGES.md#demo-video-todo)

```sh
bash scripts/verify.sh
```

Python 3.12–3.14, uv and Node 22+; no model keys or SEC fetches. After dependencies are cached, use `UV_OFFLINE=1 bash scripts/verify.sh`. [Verification guide](AGENTS.md) · [Retained test records](docs/TEST_RECORDS.md).

DappGo existed before; this verifier, site and evidence were built during the hackathon, from 27 Oct 2026. [Build disclosure](BUILD_LOG.md#build-log) · [MIT](LICENSE) · [Credits](CREDITS.md).

<details>
<summary>Earlier section links</summary>

<a id="agentic-muse-chooses-the-next-check-python-checks-the-answer"></a>[agentic muse chooses the next check python checks the answer](docs/evidence/TECHNICAL_GUIDE.md#agentic-muse-chooses-the-next-check-python-checks-the-answer)<br>
<a id="check-a-whole-post"></a>[check a whole post](docs/evidence/TECHNICAL_GUIDE.md#check-a-whole-post)<br>
<a id="cost-speed-and-provider-choice"></a>[cost speed and provider choice](docs/evidence/TECHNICAL_GUIDE.md#cost-speed-and-provider-choice)<br>
<a id="evaluation"></a>[evaluation](docs/evidence/TECHNICAL_GUIDE.md#evaluation)<br>
<a id="evidence-you-can-audit"></a>[evidence you can audit](docs/evidence/TECHNICAL_GUIDE.md#evidence-you-can-audit)<br>
<a id="gap-score"></a>[gap score](docs/evidence/TECHNICAL_GUIDE.md#gap-score)<br>
<a id="how-meta-models-are-used"></a>[how meta models are used](docs/evidence/TECHNICAL_GUIDE.md#how-meta-models-are-used)<br>
<a id="how-the-system-got-there"></a>[how the system got there](docs/evidence/TECHNICAL_GUIDE.md#how-the-system-got-there)<br>
<a id="key-results"></a>[key results](docs/evidence/TECHNICAL_GUIDE.md#key-results)<br>
<a id="l4-earnings-release-evidence"></a>[l4 earnings release evidence](docs/evidence/TECHNICAL_GUIDE.md#l4-earnings-release-evidence)<br>
<a id="limitations"></a>[limitations](docs/evidence/TECHNICAL_GUIDE.md#limitations)<br>
<a id="local-pdf-input"></a>[local pdf input](docs/evidence/TECHNICAL_GUIDE.md#local-pdf-input)<br>
<a id="one-real-run"></a>[one real run](docs/evidence/TECHNICAL_GUIDE.md#one-real-run)<br>
<a id="other-inputs"></a>[other inputs](docs/evidence/TECHNICAL_GUIDE.md#other-inputs)<br>
<a id="real-results"></a>[real results](docs/evidence/TECHNICAL_GUIDE.md#real-results)<br>
<a id="real-world-test"></a>[real world test](docs/evidence/TECHNICAL_GUIDE.md#real-world-test)<br>
<a id="reproduce-or-extend"></a>[reproduce or extend](docs/evidence/TECHNICAL_GUIDE.md#reproduce-or-extend)<br>
<a id="review-several-files-for-one-stock"></a>[review several files for one stock](docs/evidence/TECHNICAL_GUIDE.md#review-several-files-for-one-stock)<br>
<a id="run-it"></a>[run it](docs/evidence/TECHNICAL_GUIDE.md#run-it)<br>
<a id="support-and-boundaries"></a>[support and boundaries](docs/evidence/TECHNICAL_GUIDE.md#support-and-boundaries)<br>
<a id="technical-notes"></a>[technical notes](docs/evidence/TECHNICAL_GUIDE.md#technical-notes)<br>
<a id="technical-reference"></a>[technical reference](docs/evidence/TECHNICAL_GUIDE.md#technical-reference)<br>
<a id="text-verification-266-held-out-claims"></a>[text verification 266 held out claims](docs/evidence/TECHNICAL_GUIDE.md#text-verification-266-held-out-claims)<br>
<a id="try-it"></a>[try it](docs/evidence/TECHNICAL_GUIDE.md#try-it)<br>
<a id="what-it-does"></a>[what it does](docs/evidence/TECHNICAL_GUIDE.md#what-it-does)<br>
<a id="why-meta-open-weights"></a>[why meta open weights](docs/evidence/TECHNICAL_GUIDE.md#why-meta-open-weights)<br>
<a id="why-you-can-trust-a-verdict"></a>[why you can trust a verdict](docs/evidence/TECHNICAL_GUIDE.md#why-you-can-trust-a-verdict)<br>

</details>
