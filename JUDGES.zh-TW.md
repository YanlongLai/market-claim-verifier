# 財經主張查核器 — 評審指南

**貼上財經貼文，逐一用美國證管會申報資料核對數字，並產出附出處的修正版草稿。**

## 三分鐘導覽

1. **觀看：**[展示影片待發布](#demo-video-todo)。
2. **跟著查：**[一個數字](https://hackathon.dappgo.com/zh/#how)，再看[已儲存熱門貼文查核](https://hackathon.dappgo.com/zh/#recorded-run)；免密碼。
3. **試用：**[3 個故事 × 5 種輸入](https://hackathon.dappgo.com/zh/#live-check)，可選擇供應商、比較與公開歷史。評審密碼見提交說明；已儲存範例免密碼。
4. **核對：**[保留測試](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) · [結果瀏覽器](https://hackathon.dappgo.com/explorer/index.zh.html) · [真實貼文涵蓋率](https://hackathon.dappgo.com/wild/) · [證據索引](docs/evidence/INDEX.md)。

## 產品事實

| 項目 | 答案 |
| --- | --- |
| 查核內容 | [以美國證管會申報核對財務主張，提供判定與附出處的修正。](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| 涵蓋範圍 | [美國會計準則申報公司：約 8,000 家，已測試 23 家。結構化申報期間大致自 2009 年起至最新申報。](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| 輸入格式 | [網站：≤600 字元。命令列：文字、圖片、文字型文件、音訊與影片。](docs/evidence/TECHNICAL_GUIDE.md#run-it) |
| 費用與速度 | [即時查核每次 $0.01；即時 6–20 秒（單一主張 → 含四項主張的貼文）。基準測試每題 $0.02；中位數 10 秒。每日 $10；累計 $60。](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| 準確率 | [保留測試 90.2% (240/266)；誤判為支持 1/139。](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics) |
| 修正範圍 | [修正被證明錯誤的數字，並附申報出處。絕不標示整篇文章已核准。](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json) |

## 限制

- 原始執行後修正了兩題參考答案；原先登記答案的分數仍保留。
- 執行清單記錄當時工作目錄有未提交的變更。
- 事後重查使用已看過的輸入，不是全新的保留測試。
- 凍結對話重查未重測圖片辨識或語音轉錄；擷取可能遺漏主張。
- 即時查核共用每日 $10、累計 $60 預算；每個網路位址每 10 分鐘限 5 次。驗證後的查核公開保留 14 天。

失敗計為錯誤；誤判為支持的分母為 139 題參考答案為矛盾或證據不足的主張。擷取可能遺漏主張。[完整限制與模型識別碼](docs/evidence/REVIEW_GUIDE.md#limits) · [正式環境收據](docs/evidence/live-prod-2026-11-03/REPORT.md) · [現行即時設定](docs/LIVE_CHECK.md#limits-and-failure-behavior)。

## 驗證

`bash scripts/verify.sh` 在可拋棄副本中執行離線測試並重建已儲存資料。[驗證指南](AGENTS.md) · [專案說明](README.zh-TW.md) · [英文](JUDGES.md)。

原有服務在黑客松前已存在；查核器、網站與證據自 2026-10-27 起建立。[建置揭露](BUILD_LOG.md#build-log) · [授權](LICENSE) · [出處與致謝](CREDITS.md)。

<a id="demo-video-todo"></a>
展示影片待發布；已儲存查核與原始紀錄目前皆可讀取。

<a id="60-second-path"></a><a id="bonus-categories"></a><a id="controlled-format-study"></a><a id="cost-accounting"></a><a id="four-equally-weighted-criteria"></a><a id="historical-results-and-failure-review"></a><a id="in-the-wild-todo"></a><a id="input-and-source-boundaries"></a><a id="limits-to-keep-in-view"></a><a id="live-check-todo"></a><a id="media-studies"></a><a id="original-text-evaluation"></a><a id="publication-links--todo-claude"></a><a id="real-company-materials-what-improved-what-remains-unresolved"></a><a id="verify-without-model-calls"></a><a id="what-is-new-during-the-hackathon"></a>
