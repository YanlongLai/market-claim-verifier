# Market Claim Verifier

**貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。**
貼上 → Muse 尋找 SEC 證據 → Python 判定並產出修正版草稿。

限以 US-GAAP XBRL 申報的美股公司；網站貼上 600 字內文字，檔案與媒體使用 CLI。
即時每次約 $0.01、實測 6.3 秒；基準每題 $0.020、中位數 10 秒、p95 21 秒。
**保留測試 240/266（90.2%）；誤判為「支持」1/139。** 使用修正後參考答案，失敗計為錯誤。
修正版草稿只改被證明錯誤的數字並附申報出處，不標示為「已核准」。

[即時查核](https://hackathon.dappgo.com/#live-check)（需要密碼；已儲存範例免密碼）· [已儲存查核](https://hackathon.dappgo.com/zh/#recorded-run)
[評審指南](JUDGES.md) · [證據](docs/evidence/INDEX.md) · [本機執行](docs/evidence/TECHNICAL_GUIDE.md#run-it) · [English](README.md) · [Video — TODO (Claude)](JUDGES.md#demo-video-todo)

## 產品事實

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

DappGo 發布美股評論；內部事實查核發現，數字正確也可能配錯期間、單位或比較方式。**模型提出，程式判定。**

## 證據與限制

[原始保留文字測試](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics)：240/266（90.2%），誤判為支持 1/139。兩個參考答案已修正；[註冊時答案評分](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md)仍保留。擷取可能遺漏主張；涵蓋率 ≠ 準確率；事後重查不等於保留測試，也沒有重測 OCR／ASR。

[正式環境實測，2026-11-03](docs/evidence/live-prod-2026-11-03/REPORT.md)：Baseten `meta-models/muse-spark-open-1026`，$0.00988、6.34 秒，每日預算 $3。[真實貼文](https://hackathon.dappgo.com/wild/) · [完整限制與紀錄](docs/evidence/REVIEW_GUIDE.md#limits) · [原技術文件](docs/evidence/TECHNICAL_GUIDE.zh-TW.md)。

## 離線驗證

```sh
bash scripts/verify.sh
```

需要 Python 3.12–3.14、uv、Node 22+，不需要模型金鑰或 SEC 請求。依賴快取完成後可加上 `UV_OFFLINE=1`。[驗證指南](AGENTS.md) · [測試紀錄](docs/TEST_RECORDS.md)。

DappGo 在黑客松前已存在；此查核器、網站與證據從 2026-10-27 起於黑客松期間建立。[建置揭露](BUILD_LOG.md#build-log) · [MIT](LICENSE) · [出處](CREDITS.md)。

<details>
<summary>原章節連結</summary>

<a id="agenticmuse-選擇下一步python-檢查答案"></a>[agenticmuse 選擇下一步python 檢查答案](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#agenticmuse-選擇下一步python-檢查答案)<br>
<a id="api-單價與使用成本"></a>[api 單價與使用成本](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#api-單價與使用成本)<br>
<a id="同一股票的多份文件"></a>[同一股票的多份文件](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#同一股票的多份文件)<br>
<a id="技術參考"></a>[技術參考](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#技術參考)<br>
<a id="查核整篇貼文"></a>[查核整篇貼文](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#查核整篇貼文)<br>
<a id="查核流程"></a>[查核流程](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#查核流程)<br>
<a id="查看範例"></a>[查看範例](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#查看範例)<br>
<a id="格式支援"></a>[格式支援](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#格式支援)<br>
<a id="為什麼使用-meta-開放權重模型"></a>[為什麼使用 meta 開放權重模型](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#為什麼使用-meta-開放權重模型)<br>
<a id="真實世界測試"></a>[真實世界測試](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#真實世界測試)<br>
<a id="重現結果與擴充"></a>[重現結果與擴充](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#重現結果與擴充)<br>
<a id="開始使用"></a>[開始使用](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#開始使用)<br>
<a id="限制"></a>[限制](docs/evidence/TECHNICAL_GUIDE.zh-TW.md#限制)<br>

</details>
