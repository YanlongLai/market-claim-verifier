# Market Claim Verifier

**貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。**
貼上 → Muse 尋找 SEC 證據 → Python 判定並產出修正版草稿。

網站：文字 ≤600 字元。
即時查核每次 $0.01。
即時查核需時 6–20 秒（單一主張 → 含四項主張的貼文）。
保留測試準確率 90.2% (240/266)。

[即時查核](https://hackathon.dappgo.com/#live-check)（需要密碼；已儲存範例免密碼）· [已儲存查核](https://hackathon.dappgo.com/zh/#recorded-run)
[評審指南](JUDGES.md) · [證據](docs/evidence/INDEX.md) · [English](README.md)

## 產品事實

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

DappGo 發布美股評論；內部事實查核發現，數字正確也可能配錯期間、單位或比較方式。**模型提出，程式判定。**

## 證據與限制

[原始保留文字測試](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics)：90.2% (240/266)，誤判為支持 1/139。兩個參考答案已修正；[註冊時答案評分](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md)仍保留。擷取可能遺漏主張；涵蓋率 ≠ 準確率；事後重查不等於保留測試，也沒有重測 OCR／ASR。

[正式環境實測，2026-11-03](docs/evidence/live-prod-2026-11-03/REPORT.md)：Baseten `meta-models/muse-spark-open-1026`，每次 $0.01、單一主張 6.3 秒，每日預算 $3。[真實貼文](https://hackathon.dappgo.com/wild/) · [完整限制與紀錄](docs/evidence/REVIEW_GUIDE.md#limits) · [原技術文件](docs/evidence/TECHNICAL_GUIDE.zh-TW.md)。

## 離線驗證

[本機執行](docs/evidence/TECHNICAL_GUIDE.md#run-it) · [Video — TODO (Claude)](JUDGES.md#demo-video-todo)

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
