# 財經貼文查核 — 評審指南

**貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。**

[即時網站](https://hackathon.dappgo.com/zh/) · [專案說明](README.zh-TW.md) · [證據索引](docs/evidence/INDEX.md)

## 評審的三分鐘路徑

| 步驟 | 開啟 | 檢視 |
| --- | --- | --- |
| 觀看 | [示範影片待發布](#demo-video-todo) | 貼文、證據、程式判定、修正版草稿。 |
| 試用 | [即時查核](https://hackathon.dappgo.com/zh/#live-check) | 選故事、輸入與平台；評審密碼在提交備註。 |
| 重播 | [已儲存查核](https://hackathon.dappgo.com/zh/#recorded-run) | 不需密碼；開啟修正版草稿、SEC 引用與代理軌跡。 |
| 審核 | [原始基準](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) | 閱讀保留結果、失敗及標準答案修正揭露。 |

## 構想

DappGo 內部事實查核發現正確數字搭配錯誤期間、單位或比較方式。
Muse Spark 選擇 SEC 工具；Python 綁定證據、計算判定並產生附出處修正。
**模型提出，程式決定。** [架構與流程](README.zh-TW.md#構想)。

## 事實

| 項目 | 答案與證據 |
| --- | --- |
| 功能 | 擷取主張、查核 SEC 證據，回傳判定、修正版草稿、軌跡與收據。[修正報告](docs/evidence/corrected-draft-2026-11-03/REPORT.md)。 |
| 範圍 | US-GAAP SEC 公司約 8,000 家；深入測試 23 家。SEC XBRL 期間大致從 2009 年起直到最新申報，含年度、季度及成長比較。[範圍報告](docs/evidence/REVIEW_GUIDE.md#facts-in-detail)。 |
| 輸入 | 網站：600 字內文字與 3 個故事 × 5 種範例輸入。CLI：文字、圖片、PDF、音訊與影片。[網站報告](docs/evidence/try-v3-site-2026-11-03/REPORT.md)、[格式報告](docs/evidence/input-formats-2026-10-30/REPORT.md)。 |
| 平台 | Baseten、Fireworks、Meta Model API，均為 Meta 查核模型；媒體使用 Meta OCR／ASR。[已記錄模型](docs/evidence/eval-v2-2026-10-27/manifest.json)。 |
| 費用與速度 | 即時主要數字為 $0.01／6 秒。依輸入大小的規劃區間為 $0.01–0.04／6–25 秒，另加媒體前處理。基準每題 $0.02，中位數 10 秒，p95 21 秒。[收據與範圍](docs/evidence/readme-v3-2026-11-04/REPORT.md#cost-and-speed)。 |
| 準確率 | 保留測試 90.2%（240/266）；矛盾／證據不足參考主張的錯誤支持為 1/139。失敗算錯。[原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標)。 |
| 修正 | 刪除被否定數字、填入程式值、引用組成申報。僅修改唯一綁定的已查核主張；並非文章核准。[保留 Apple 範例](docs/evidence/corrected-draft-2026-11-03/REPORT.md#retained-apple-example)。 |
| 即時限制 | 各供應商有獨立每日與累計上限；每 IP 每 10 分鐘 5 次。已認證輸入／結果公開 14 天。[上限設定與遷移](deploy/README.md#setting-provider-caps)。 |

## 準確率與證據

[專案基準表](README.zh-TW.md#原始基準)依平台比較代理與單次回答，
將歷史全部題目欄與保留結果分開。
[78 則 Threads／80 則新聞](docs/evidence/real-world-2026-11-02/REPORT.md)評估真實世界涵蓋；
涵蓋率不等於準確率。[逐題瀏覽器](https://hackathon.dappgo.com/explorer/index.zh.html) · [真實世界瀏覽器](https://hackathon.dappgo.com/wild/)。

## 限制與誠實揭露

- 兩個標準答案於原始執行後修正；[註冊標準答案成績](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md)仍可查閱。
- 原始[執行清單](docs/evidence/eval-v2-2026-10-27/manifest.json)記錄工作目錄有未提交變更。
- [事後重查](docs/evidence/real-world-2026-11-03-fixcheck/REPORT.md)重用曾見輸入；凍結逐字稿不重測 OCR／ASR。
- 抽取可能漏掉主張；歧義期間、抽樣畫面及缺漏證據限制涵蓋。
- 比較依序使用各供應商獨立上限及全體總額限制；額度用完的供應商會標示並略過。規劃區間不是實測極值或服務承諾；已儲存收據保留歷史值。

[完整限制](docs/evidence/REVIEW_GUIDE.md#limits) · [平台／輸入邊界](docs/PROVIDERS.md) · [測試紀錄政策](docs/TEST_RECORDS.md)。

## 離線驗證

```sh
bash scripts/verify.sh
```

先安裝鎖定依賴，接著在拋棄式副本離線驗證。
[驗證指南](AGENTS.md) · [已記錄驗證](docs/VERIFICATION.md)。

## 授權與致謝

DappGo 在黑客松前已存在；查核器、網站與證據於黑客松期間建立。
[建置揭露](BUILD_LOG.md#build-log) · [MIT](LICENSE) · [致謝](CREDITS.md) · [英文](JUDGES.md)。

<a id="demo-video-todo"></a>
示範影片待發布；已儲存查核與原始軌跡現在可查閱。
