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

| Question | Answer |
| --- | --- |
| What it does | Checks financial claims against SEC filings; returns verdicts and cited corrections.<br>用 SEC 申報核對財務主張，提供判定與附出處的修正。 |
| Time span | SEC XBRL periods, generally 2009 onward, through the latest filing.<br>SEC XBRL 申報期間，大致自 2009 年起至最新申報。 |
| Which US stocks | US-GAAP SEC filers: ≈8,000 companies; 23 tested.<br>US-GAAP 美股申報公司：約 8,000 家，已測試 23 家。 |
| Inputs | Website: text ≤600 characters. CLI: text, images, PDFs, audio and video.<br>網站：≤600 字元。CLI：文字、圖片、PDF、音訊與影片。 |
| Price | $0.01 per live check; $0.02 per claim in the benchmark.<br>即時查核每次 $0.01；基準測試每題 $0.02。 |
| Speed | 6–20 s live (one claim → four-assertion post); 10 s median in the benchmark.<br>即時 6–20 秒（單一主張 → 含四項主張的貼文）；基準測試中位數 10 秒。 |
| Accuracy | 90.2% (240/266) held out; false support 1/139.<br>保留測試 90.2% (240/266)；誤判為支持 1/139。 |
| Fix the article? | Corrects disproved numbers and cites the filing.<br>修正被證明錯誤的數字，並附申報出處。 |

[Facts in detail](docs/evidence/REVIEW_GUIDE.md#facts-in-detail).

## Limits

Headline: **90.2% (240/266), false support 1/139** reference contradicted/insufficient claims, Baseten Muse Spark Open. Corrected gold (two changes); [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) retained; failures count as wrong. The manifest records a dirty working tree. Extraction can miss assertions. Coverage ≠ accuracy; post-hoc rechecks are not held out and do not retest OCR/ASR. [Full limits, model IDs and historical results](docs/evidence/REVIEW_GUIDE.md#limits).

DappGo existed before; this verifier, site and evidence were built during the hackathon, from 27 Oct 2026. [Build disclosure](BUILD_LOG.md#build-log) · [Code and model responsibilities](docs/evidence/TECHNICAL_GUIDE.md#agentic-muse-chooses-the-next-check-python-checks-the-answer) · [Offline verification](AGENTS.md) (`bash scripts/verify.sh`) · [MIT](LICENSE) · [Credits](CREDITS.md).

<a id="demo-video-todo"></a><br>
Video — TODO (Claude). [Extended review: criteria, bonus categories, media studies and failure review](docs/evidence/REVIEW_GUIDE.md).

<a id="60-second-path"></a><a id="bonus-categories"></a><a id="controlled-format-study"></a><a id="cost-accounting"></a><a id="four-equally-weighted-criteria"></a><a id="historical-results-and-failure-review"></a><a id="in-the-wild-todo"></a><a id="input-and-source-boundaries"></a><a id="limits-to-keep-in-view"></a><a id="live-check-todo"></a><a id="media-studies"></a><a id="original-text-evaluation"></a><a id="publication-links--todo-claude"></a><a id="real-company-materials-what-improved-what-remains-unresolved"></a><a id="verify-without-model-calls"></a><a id="what-is-new-during-the-hackathon"></a>

Earlier anchors → [REVIEW_GUIDE.md](docs/evidence/REVIEW_GUIDE.md).
