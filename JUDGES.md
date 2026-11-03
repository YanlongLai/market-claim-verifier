# Market Claim Verifier — judge guide

**Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations.**
**貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。**

Paste → Muse finds SEC evidence → Python decides + corrected draft. DappGo publishes US-market commentary; internal checks found right numbers with wrong periods, units or comparisons. **The model proposes, the program decides.**

## 3-minute path

1. **Watch:** [Video — TODO (Claude)](#demo-video-todo).
2. **Try a saved check:** [Apple trace](https://hackathon.dappgo.com/#recorded-run), no password. For the wrong-period example, [the saved post](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.html) claims $416.2B in fiscal Q4 2025; the filed quarter was $102.5B (annual minus nine months).
3. **Try live:** [Live check](https://hackathon.dappgo.com/#live-check) — password-protected; saved examples need none. Judges: password in the submission notes. [Verified production run](docs/evidence/live-prod-2026-11-03/REPORT.md), 2026-11-03; $3/day budget.
4. **Read evidence:** [Original benchmark](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) · [Explorer](https://hackathon.dappgo.com/explorer/) · [In the wild](https://hackathon.dappgo.com/wild/) · [Evidence index](docs/evidence/INDEX.md).

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

## Limits

Headline: **240/266 (90.2%), false support 1/139** reference contradicted/insufficient claims, Baseten Muse Spark Open. Corrected gold (two changes); [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) retained; failures count as wrong. The manifest records a dirty working tree. Extraction can miss assertions. Coverage ≠ accuracy; post-hoc rechecks are not held out and do not retest OCR/ASR. [Full limits, model IDs and historical results](docs/evidence/REVIEW_GUIDE.md#limits).

DappGo existed before; this verifier, site and evidence were built during the hackathon, from 27 Oct 2026. [Build disclosure](BUILD_LOG.md#build-log) · [Code and model responsibilities](docs/evidence/TECHNICAL_GUIDE.md#agentic-muse-chooses-the-next-check-python-checks-the-answer) · [Offline verification](AGENTS.md) (`bash scripts/verify.sh`) · [MIT](LICENSE) · [Credits](CREDITS.md).

<a id="demo-video-todo"></a><br>
Video — TODO (Claude). [Extended review: criteria, bonus categories, media studies and failure review](docs/evidence/REVIEW_GUIDE.md).

<details>
<summary>Earlier section links</summary>

<a id="60-second-path"></a>[60 second path](docs/evidence/REVIEW_GUIDE.md#60-second-path)<br>
<a id="bonus-categories"></a>[bonus categories](docs/evidence/REVIEW_GUIDE.md#bonus-categories)<br>
<a id="controlled-format-study"></a>[controlled format study](docs/evidence/REVIEW_GUIDE.md#controlled-format-study)<br>
<a id="cost-accounting"></a>[cost accounting](docs/evidence/REVIEW_GUIDE.md#cost-accounting)<br>
<a id="four-equally-weighted-criteria"></a>[four equally weighted criteria](docs/evidence/REVIEW_GUIDE.md#four-equally-weighted-criteria)<br>
<a id="historical-results-and-failure-review"></a>[historical results and failure review](docs/evidence/REVIEW_GUIDE.md#historical-results-and-failure-review)<br>
<a id="in-the-wild-todo"></a>[In the wild](docs/evidence/REVIEW_GUIDE.md#in-the-wild-todo)<br>
<a id="input-and-source-boundaries"></a>[input and source boundaries](docs/evidence/REVIEW_GUIDE.md#input-and-source-boundaries)<br>
<a id="limits-to-keep-in-view"></a>[limits to keep in view](docs/evidence/REVIEW_GUIDE.md#limits-to-keep-in-view)<br>
<a id="live-check-todo"></a>[Live check](docs/evidence/REVIEW_GUIDE.md#live-check-todo)<br>
<a id="media-studies"></a>[media studies](docs/evidence/REVIEW_GUIDE.md#media-studies)<br>
<a id="original-text-evaluation"></a>[original text evaluation](docs/evidence/REVIEW_GUIDE.md#original-text-evaluation)<br>
<a id="publication-links--todo-claude"></a>[publication links  todo claude](docs/evidence/REVIEW_GUIDE.md#publication-links--todo-claude)<br>
<a id="real-company-materials-what-improved-what-remains-unresolved"></a>[real company materials what improved what remains unresolved](docs/evidence/REVIEW_GUIDE.md#real-company-materials-what-improved-what-remains-unresolved)<br>
<a id="verify-without-model-calls"></a>[verify without model calls](docs/evidence/REVIEW_GUIDE.md#verify-without-model-calls)<br>
<a id="what-is-new-during-the-hackathon"></a>[what is new during the hackathon](docs/evidence/REVIEW_GUIDE.md#what-is-new-during-the-hackathon)<br>

</details>
