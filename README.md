# Market Claim Verifier

**Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations.**
Paste → Muse finds SEC evidence → Python decides + corrected draft.

US-listed SEC filers · reported periods (generally 2009 onward) · text ≤600 characters on the website; media via CLI.
≈$0.01/live check · 6.3 s measured; benchmark $0.020/claim · median 10 s, p95 21 s.
**240/266 (90.2%) held-out accuracy · false support 1/139** · corrected gold; failures count as wrong.
Corrected drafts change only disproved numbers and cite the filing; never labelled "approved".

[Live check](https://hackathon.dappgo.com/#live-check) (password-protected; saved examples need none) · [Saved check](https://hackathon.dappgo.com/#recorded-run)
[Judges](JUDGES.md) · [Evidence](docs/evidence/INDEX.md) · [Run locally](docs/evidence/TECHNICAL_GUIDE.md#run-it) · [繁體中文](README.zh-TW.md) · [Video — TODO (Claude)](JUDGES.md#demo-video-todo)

## Facts

| # | Question | Answer (EN) | 答案（繁中） |
|---|---|---|---|
| 1 | What it does | Extracts each financial claim → Muse Spark picks SEC tools → Python computes the verdict (supported / contradicted / insufficient evidence) → corrected draft for contradicted numbers. | 擷取每個財務主張 → Muse Spark 選擇 SEC 工具 → Python 計算判定（支持／矛盾／證據不足）→ 為矛盾的數字產出修正版草稿。 |
| 2 | Time span | Any period the company has reported in SEC XBRL (generally 2009 onward, earlier when restated) up to its latest 10-Q/10-K. Annual, quarterly and growth comparisons. Live SEC data refreshes every 6 h. | 公司在 SEC XBRL 申報過的期間皆可（大致 2009 年起，較早期間若被後續申報重述也可），直到最新 10-Q/10-K。支援年度、季度與成長比較。即時版 SEC 資料每 6 小時更新。 |
| 3 | Which US stocks | US-listed companies filing 10-K/10-Q with US-GAAP XBRL — the SEC ticker map lists ≈8,000 companies. Deeply tested on 23. Not ETFs/funds; IFRS foreign filers limited. | 以 US-GAAP XBRL 申報 10-K/10-Q 的美股公司——SEC 代號表約 8,000 家。深入測試 23 家。不含 ETF／基金；IFRS 外國公司支援有限。 |
| 4 | Inputs | Website: pasted text ≤600 characters. CLI: text, screenshots (Muse OCR), PDFs with text, audio/video (Muse Voice Transcribe). | 網站：貼上 600 字內文字。CLI：文字、截圖（Muse OCR）、文字型 PDF、音訊／影片（Muse Voice Transcribe）。 |
| 5 | Price | ≈$0.01 per live check (measured $0.0099); $0.020 per claim on the 266-claim benchmark (Baseten). | 即時查核每次約 $0.01（實測 $0.0099）；266 題基準平均每題 $0.020（Baseten）。 |
| 6 | Speed | Live: 6.3 s (verified production run). Benchmark: median 10 s, p95 21 s per claim. | 即時：6.3 秒（正式環境實測）。基準：每題中位數 10 秒、p95 21 秒。 |
| 7 | Accuracy | **90.2% (240/266) on held-out claims; wrongly says "supported" 1 in 139 times.** Benchmark text, not a guarantee on every post; real-world coverage reported separately. | **保留測試 90.2%（240/266）；誤判為「支持」僅 1/139。** 為基準測試文字，不保證每篇貼文；真實貼文的涵蓋率另列。 |
| 8 | Fix the article? | Yes, for numbers it disproves: a corrected draft strikes the wrong number, inserts the filed value and cites the filing. Only checked assertions are changed; never labelled "approved". | 可以，限被證明錯誤的數字：修正版草稿刪除錯誤數字、填入申報值並附出處。只修改核對過的主張，不標示為「已核准」。 |

## Why it exists

DappGo publishes US-market commentary. An internal fact check found posts with the right number but the wrong period, unit or comparison. **The model proposes, the program decides.** Muse Spark picks SEC tools; Python computes and validates the verdict. [Agent, tools and trace](docs/evidence/TECHNICAL_GUIDE.md#agentic-muse-chooses-the-next-check-python-checks-the-answer).

## Evidence and limits

[Original held-out text results](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics): **240/266 (90.2%)**, false support **1/139** reference contradicted/insufficient claims. Corrected gold includes two changes; [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) remain available. These are benchmark results, not a guarantee on every post. Extraction can miss assertions; coverage ≠ accuracy; post-hoc rechecks are not held out.

[Production check, 2026-11-03](docs/evidence/live-prod-2026-11-03/REPORT.md): Baseten `meta-models/muse-spark-open-1026`, $0.00988, 6.34 s; $3/day live budget. [In the wild](https://hackathon.dappgo.com/wild/) · [Evidence index](docs/evidence/INDEX.md) · [Detailed review and honesty labels](docs/evidence/REVIEW_GUIDE.md#limits).

## Verify offline

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
