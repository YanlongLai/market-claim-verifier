# 財經貼文查核

![查核機器人比對財經貼文與申報文件](docs/site/img/readme-robot.gif)

**貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。**

**保留測試準確率 90.2%（240/266）· 錯誤支持 1/139**（[測量方式](#accuracy)）。於黑客松期間（2026 年 10 月 27 日至 11 月 4 日）建立：DappGo 在此之前已存在，但本儲存庫的內容皆為期間內新建（[建置揭露](BUILD_LOG.md#build-log)）。

[即時網站](https://hackathon.dappgo.com/zh/) · [評審指南](JUDGES.zh-TW.md) · [證據索引](docs/evidence/INDEX.md)

## 評審的三分鐘路徑

| 步驟 | 開啟 | 檢視內容 |
| --- | --- | --- |
| 觀看 | [三分鐘示範影片](https://youtu.be/qIZTElkqpZc) | 依序看貼文、申報文件、判定與修正版草稿。 |
| 試用 | [即時查核](https://hackathon.dappgo.com/zh/#live-check) | 評審密碼是我們的隊名；選擇故事、輸入與平台。 |
| 重播 | [已儲存查核](https://hackathon.dappgo.com/zh/#recorded-run) | 不需密碼；展開 SEC 證據與代理軌跡。這是已記錄執行。 |
| 審核 | [保留測試報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) | 分母、失敗、費用與標準答案修正揭露。 |

<a id="demo-video"></a>
示範影片（3 分鐘）：https://youtu.be/qIZTElkqpZc

## 構想

DappGo 發布美股市場評論。內部事實查核發現一個反覆出現的問題：
財經貼文可能數字正確，期間、單位或比較方式卻錯了。
僅憑流暢的說明，無法確保抓出把全年營收寫成單季的錯誤。

**模型提出，程式決定。** Muse Spark 選擇證據工具並提出解讀；
Python 將主張綁定回傳證據，計算比較，
最後判定支持、矛盾或證據不足。

本作結合程式判定、附出處的修正版草稿與確定性的證據綁定。
模型提出的數字不能僅因看似合理就成為修正值；
修正必須使用程式計算值與該次查核保留的申報引用。

![輸入、Muse Spark、SEC 證據、Python 判定與附出處草稿的流程](docs/site/img/architecture-v4.svg)

1. 讀取輸入並擷取每個財務主張；輸入本身不當作證據。
2. Muse Spark 選用 `lookup_fact`、`compute_change`、`history_rank` 與 `list_periods` 等工具。
3. SEC 結果保留證據編號、公司、指標、單位、期間、申報識別碼與來源雜湊。
4. Python 解析主張數字、精度和比較詞，驗證證據與財年／曆年期間。
5. 程式計算判定；修正時刪除被否定的數字，填入附引用的申報值。
6. 儲存請求、工具呼叫、用量、費用與耗時，以便檢視及重播。

[代理迴圈](src/claimcheck/agent.py) · [程式檢查](src/claimcheck/checks.py) ·
[草稿修正器](src/claimcheck/correction.py) · [證據紀錄契約](docs/EVIDENCE_RECORDS.md)

## 功能

### 輸入與涵蓋範圍

| 項目 | 目前契約 | 來源 |
| --- | --- | --- |
| 網站 | 貼上 600 字內文字；另有文字、圖片、PDF、音訊與影片範例。任意瀏覽器上傳仍在規劃中。 | [即時契約](docs/LIVE_CHECK.md)、[範例報告](docs/evidence/try-v3-site-2026-11-03/REPORT.md) |
| CLI | 文字／Markdown、PNG／JPEG／WebP、文字型 PDF、音訊與影片。掃描 PDF 會標示未查核。 | [格式探測報告](docs/evidence/input-formats-2026-10-30/REPORT.md)、[輸入限制](docs/PROVIDERS.md#current-repository-input-contract) |
| 公司 | 以 US-GAAP 申報的 SEC 公司：約 8,000 家；深入測試 23 家。ETF／基金與 IFRS 外國公司支援有限或不支援。 | [範圍與數量來源](docs/evidence/REVIEW_GUIDE.md#facts-in-detail) |
| 期間 | SEC XBRL 期間大致自 2009 年起，直到最新申報；包含年度、季度與成長比較。 | [範圍報告](docs/evidence/REVIEW_GUIDE.md#facts-in-detail)、[期間規則](docs/evidence/TECHNICAL_GUIDE.md#technical-notes) |
| 更新 | 即時 SEC 快取每 6 小時更新；已儲存示範保留原記錄來源。 | [即時設定報告](docs/evidence/readme-v3-2026-11-04/REPORT.md#scope-and-limits) |

媒體先轉成主張文字。圖片使用 Muse OCR；音訊使用 Muse Voice Transcribe；
影片結合轉錄與抽樣畫面。這些步驟可能漏掉主張、圖形幾何，
或數字與投影片表頭的關係，亦不會認證上傳內容。
[平台與媒體邊界](docs/PROVIDERS.md) · [媒體研究](docs/evidence/fair-multimodal-v1/REPORT.md)

### 輸出

| 輸出 | 意義 |
| --- | --- |
| 判定 | 對每個擷取主張給出支持、矛盾或證據不足。 |
| 修正版草稿 | 刪除被否定的數字，填入程式值並引用申報；有歧義的修改保留原文與原因。 |
| SEC 證據 | 數值、單位、期間及申報連結；推算季度會引用組成申報。 |
| 代理軌跡 | 模型請求、所選工具、回傳證據編號與最終程式檢查。 |
| 收據 | 平台／模型、估計費用或保留上限及實測耗時；媒體前處理另列。 |

僅核對列出的主張；草稿絕不表示整篇文章「已核准」。
[修正報告](docs/evidence/corrected-draft-2026-11-03/REPORT.md) · [收據契約](docs/LIVE_CHECK.md#provider-receipts-compare-and-history)

### 平台

所有查核路徑均使用 Meta 模型；託管平台與模型版本分別記錄。

| 路徑 | 固定查核模型 | 媒體前處理 |
| --- | --- | --- |
| Meta Model API | `muse-spark-1.3` | Meta OCR／ASR |
| Baseten | `meta-models/muse-spark-open-1026` | Meta OCR／ASR |
| Fireworks | `accounts/fireworks/models/muse-spark-open` | Meta OCR／ASR |

開放與封閉 Spark 版本是不同模型。供應商列出某種輸入格式，
不代表本專案使用該平台原生的圖片、音訊或影片端點。
[平台報告與實測邊界](docs/PROVIDERS.md) · [已記錄模型清單](docs/evidence/eval-v2-2026-10-27/manifest.json)

## 使用方式

### 網站

開啟[試用區](https://hackathon.dappgo.com/zh/#live-check)，選擇器提供
[3 個故事 × 5 種輸入格式](docs/evidence/try-v3-site-2026-11-03/REPORT.md)：
可選期間錯誤的貼文（故事 A）、全部正確故事，或混合主張故事。
執行前先讀取所選輸入；尚無已儲存結果的媒體會明確標示待補。

<!-- readme-shot:try-story-a -->
![選取故事 A 的試用區](docs/site/img/readme/try-story-a.png)

選擇 Meta Model API、Baseten 或 Fireworks，預設選取 Baseten。「全部比較」會依序執行各平台，
各自使用獨立的每日與累計預算；額度用完的供應商會標示並略過。輸入評審密碼可執行新查核；
「查看已儲存結果」不需密碼，並保留歷史收據。查核執行時，「目前狀態」面板會顯示該次請求的伺服器紀錄（每個模型步驟、每次 SEC 查詢與程式檢查）及六步驟進度列；「最近查核」列出最近 50 次公開執行。

<!-- readme-shot:corrected-draft -->
![已儲存結果的修正版草稿與申報引用](docs/site/img/readme/corrected-draft.png)

展開「SEC 證據」與「代理軌跡」檢視判定。公開歷史可重開完整結果；
「編輯並重跑」會還原故事、輸入與平台。已認證輸入及結果
公開保留 [14 天](docs/evidence/readme-v3-2026-11-04/REPORT.md#scope-and-limits)。
截圖是保留資料的本機呈現，不是新的正式環境執行。
[擷取腳本](scripts/capture_readme_shots.py) · [截圖來源](docs/evidence/readme-v3-2026-11-04/REPORT.md#screenshots)

### CLI 快速開始

需要 Python 3.12–3.14 與 `uv`；完整驗證另需 Node 22+。
[前置需求與離線驗證](AGENTS.md#offline-verification)。

```sh
git clone https://github.com/YanlongLai/market-claim-verifier.git
cd market-claim-verifier
uv sync
```

不需金鑰、不呼叫模型或 SEC，即可預覽請求：

```sh
uv run python -m claimcheck verify --provider baseten --dry-run \
  'META Q2 2025 revenue was $47.5B'
```

在環境設定 `BASETEN_API_KEY`，再以明確費用上限查核單一主張：

```sh
uv run python -m claimcheck verify --provider baseten --budget 1 \
  'META Q2 2025 revenue was $47.5B'
```

查核整篇貼文並保留 HTML／JSON 報告：

```sh
uv run python -m claimcheck post examples/posts/bigtech-thread.txt \
  --provider baseten --budget 1
```

先讀取媒體，再查核擷取到的主張：

```sh
uv run python -m claimcheck ingest docs/examples/post.png --provider baseten --budget 1
uv run python -m claimcheck ingest docs/examples/post.pdf --provider baseten --budget 1
uv run python -m claimcheck ingest docs/examples/post.mp3 --provider baseten --budget 1
uv run python -m claimcheck ingest docs/examples/post.mp4 --provider baseten --budget 1
```

以下是[已儲存 Apple 修正](docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json)的可讀摘錄，
顯示值依保留來源四捨五入；並非新產生的 CLI 輸出：

```text
Claim: Apple revenue in fiscal Q4 2025 alone was $416.2B.
Program verdict: contradicted
Filed quarter: $102.5B = annual revenue minus nine-month revenue
Corrected draft: Apple revenue in fiscal Q4 2025 alone was ~~$416.2B~~ → $102.5B.
Citations: both component SEC filings retained in the report
```

[修正計算與重播限制](docs/evidence/corrected-draft-2026-11-03/REPORT.md#retained-apple-example)

### 模型與金鑰

以 `--provider meta`、`--provider baseten` 或 `--provider fireworks` 選擇供應商；未指定時讀取 `CLAIMCHECK_PROVIDER`，CLI 預設為 `meta`。查核使用的都是 Meta Muse 模型。

| 供應商 | 金鑰環境變數 | 金鑰檔設定與預設位置 | 預設模型識別碼 |
| --- | --- | --- | --- |
| Meta Model API | `MODEL_API_KEY` | `MODEL_API_KEY_FILE`；`~/.config/dappgo/meta-model-api.env`，使用 `MODEL_API_KEY=your-key` 一行 | `muse-spark-1.3` |
| Baseten | `BASETEN_API_KEY` | `BASETEN_API_KEY_FILE`；`~/secret/baseten_api_key.txt`，只放金鑰 | `meta-models/muse-spark-open-1026` |
| Fireworks | `FIREWORKS_API_KEY` | `FIREWORKS_API_KEY_FILE`；`~/secret/fireworks-api-key.txt`，只放金鑰 | `accounts/fireworks/models/muse-spark-open` |

非空的環境金鑰優先於檔案。金鑰檔放在儲存庫外，權限設為 `chmod 600`；不要放進指令參數、錄影或提交紀錄中。

查核模型可用 `--model ID` 或 `CLAIMCHECK_MODEL=ID` 覆寫，旗標優先。使用上表完整識別碼；Meta 的費用帳本另支援 `muse-wonder-1.0`，未知組合會在付費呼叫前被拒絕。OCR 固定使用 Meta `muse-spark-1.3`，ASR 使用 `muse-voice-transcribe-1.0`。即使交給 Baseten／Fireworks 查核文字，前處理仍需本機 `MODEL_API_KEY` 或 Meta 金鑰檔。原生文字 PDF 不需 OCR 金鑰；影音另需 FFmpeg／ffprobe。

`--budget` 設定擷取及全部查核請求的美元上限，預設讀取 `CLAIMCHECK_BUDGET_USD`，未設定時為 0.50 美元；所選供應商帳本的既有花費也計入。媒體匯入使用獨立帳本，混合供應商時平均分配上限。`verify --dry-run` 與 `post --dry-run` 不讀金鑰檔、不呼叫模型或 SEC；貼文只預覽首次擷取。`ingest` 沒有此旗標。[完整設定、優先順序與預算](docs/PROVIDERS.md#models--keys) · [CLI 參考](docs/evidence/TECHNICAL_GUIDE.md#run-it)。

**線上網站與本機 CLI 比較。** 網站使用 `dappgo-hackathon` 命名空間的 `Kubernetes` 機密 `live-check-secrets`，包含下表三個伺服器金鑰、`LIVE_CHECK_PASSWORD` 及 `LIVE_ORIGIN_TOKEN`。訪客輸入審閱密碼，供應商金鑰留在伺服器；網站上限與本機帳本分開。[部署設定](deploy/README.md#configuration-and-persistence) · [真實線上紀錄與本機 CLI 錄製](docs/REAL_TRACES.md)。

| 供應商 | 線上網站 | 本機 CLI |
| --- | --- | --- |
| Meta Model API | 伺服器 `META_MODEL_API_KEY`，供查核與 OCR／ASR 使用 | 自己的 `MODEL_API_KEY` 或 Meta 環境檔；`--provider meta` |
| Baseten | 伺服器 `BASETEN_API_KEY`；固定預設模型 | 自己的 `BASETEN_API_KEY` 或純金鑰檔；`--provider baseten` |
| Fireworks | 伺服器 `FIREWORKS_API_KEY`；固定預設模型 | 自己的 `FIREWORKS_API_KEY` 或純金鑰檔；`--provider fireworks` |

## 費用與速度

主要數字為即時 **$0.01／6 秒**（[正式環境收據](docs/evidence/live-prod-2026-11-03/REPORT.md)），
以及 [Baseten 基準](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics)的**每題 $0.02／中位數 10 秒**。
這些為已記錄觀察值的四捨五入；下列規劃區間不是實測極值，也不是服務承諾。

| 工作 | 估計費用（美元） | 耗時 | 證據與邊界 |
| --- | --- | --- | --- |
| 即時文字查核 | 依輸入大小約 $0.01–0.04 | 依供應商約需 6–90 秒 | [規劃區間與正式環境收據](docs/evidence/readme-v3-2026-11-04/REPORT.md#cost-and-speed)；一筆正式環境主張支持四捨五入的 $0.01／6 秒主要數字。 |
| 即時媒體範例 | 文字查核加 OCR／ASR 前處理 | 查核加前處理耗時 | [媒體報告](docs/evidence/media-examples-2026-11-03/REPORT.md)；沒有固定加價，Meta 前處理在收據逐項列出。 |
| Baseten 基準主張 | 每題 $0.02 | 中位數 10 秒；p95 21 秒 | [保留文字測試報告](docs/evidence/eval-v2-2026-10-27/REPORT.md#metrics)；已完成案例費用與延遲的四捨五入。 |
| 各供應商即時預算 | Meta、Baseten、Fireworks 各自設每日與累計上限；程式預設各每日 $30、累計 $20 | 每日 UTC 午夜重設 | [設定上限](deploy/README.md#setting-provider-caps)；部署者上線前依真實額度設定，另有全體總額上限。 |

選擇區顯示各供應商的今日及累計剩餘額度；Meta 前處理計入 Meta。舊帳本無法歸屬的花費保守計入每家上限，部署者依記錄花費與剩餘額度設定真實上限。[遷移與設定](deploy/README.md#setting-provider-caps)。

較長貼文可能超過規劃區間；保留的多主張範例另有自己的
[費用與耗時](docs/evidence/readme-v3-2026-11-04/REPORT.md#cost-and-speed)。
一份媒體文件可能產生多個計費主張。費用包含抽取、工具迴圈呼叫、
重試及前處理；帳本估值與保留額度並非供應商發票。
[價格與計費](docs/PROVIDERS.md#price-comparison) · [呼叫前預留帳本](src/claimcheck/budget.py)

<a id="accuracy"></a>

## 準確率與證據

**保留測試 90.2%（240/266）；錯誤支持 1/139**
（[原始修正標準答案報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標)）。
錯誤支持的分母是標準答案為矛盾／證據不足的主張。
失敗及缺漏結果均算錯；這是文字基準準確率，不是每篇貼文的保證。

### 原始基準

| 平台／方法 | 全部 357 題 | 保留 266 題 | 報告 |
| --- | --- | --- | --- |
| Meta Model API · 代理加 SEC 工具 | 83.2%（297/357） | 82.0%（218/266） | [原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) |
| Meta Model API · 單次回答 | 44.3%（158/357） | 41.7%（111/266） | [原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) |
| Baseten · 代理加 SEC 工具 | 90.5%（323/357） | 90.2%（240/266） | [原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) |
| Baseten · 單次回答 | 20.7%（74/357） | 21.1%（56/266） | [原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) |
| Fireworks · 代理加 SEC 工具 | 90.5%（323/357） | 89.1%（237/266） | [原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) |
| Fireworks · 單次回答 | 19.9%（71/357） | 19.2%（51/266） | [原始報告](docs/evidence/eval-v2-2026-10-27/REPORT.zh-TW.md#評測指標) |

全部題目欄包含開發集；只有保留測試欄供應主要數字。
主張於執行前凍結。兩個標準答案事後修正；
[註冊標準答案成績](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md)、
[執行清單](docs/evidence/eval-v2-2026-10-27/manifest.json)與
[逐題瀏覽器](https://hackathon.dappgo.com/explorer/index.zh.html)保留審核軌跡。
[後續代理重跑](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md)屬事後檢查；
空白的單次回答列不是結果。

### 真實世界與媒體證據

| 研究 | 可支持的結論 | 報告 |
| --- | --- | --- |
| 78 則 Threads／80 則新聞 | 抽取及查核涵蓋率、失敗與費用；涵蓋率不等於準確率。獨立標籤稀少，限制真實準確率主張。 | [原始真實世界報告](docs/evidence/real-world-2026-11-02/REPORT.md)、[來源審核](docs/evidence/real-world-2026-11-02/threads/GOLD_REVIEW.zh-TW.md) |
| 凍結文字修正檢查 | 曾見輸入的回歸行為；不重測 OCR／ASR。 | [事後報告](docs/evidence/real-world-2026-11-03-fixcheck/REPORT.md) |
| 配對媒體研究 | 各格式共用凍結的 Meta 前處理；原生圖片探測另列。 | [格式報告](docs/evidence/fair-multimodal-v1/REPORT.md) |
| 真實網路簡報探測 | 保留影音失敗、事件期間上下文與證據缺口。 | [原始影音報告](docs/evidence/real-av-v1/REPORT.md)、[上下文重查](docs/evidence/real-av-context-live/REPORT.md) |

[證據索引](docs/evidence/INDEX.md) · [真實世界瀏覽器](https://hackathon.dappgo.com/wild/) ·
[測試紀錄保留政策](docs/TEST_RECORDS.md) · [版本化證據匯出](docs/EVIDENCE_RECORDS.md)

### 離線驗證

```sh
bash scripts/verify.sh
# After the locked dependency cache is populated:
UV_OFFLINE=1 bash scripts/verify.sh
```

執行器先安裝鎖定依賴，再以網路防護且不含平台金鑰的環境執行 Python／Node 套件。
在拋棄式副本重建圖表、檢查儲存資料的重現性及 Markdown 連結。
不會執行即時評測、抓取 SEC 資料或渲染完整示範影片。
[驗證收據](docs/VERIFICATION.md) · [驗證指南](AGENTS.md)

## 限制與誠實揭露

| 限制 | 影響 |
| --- | --- |
| 修正標準答案 | 主要數字使用修正標籤；註冊標準答案報告仍可查閱。 |
| 非乾淨執行目錄 | 原始清單記錄工作目錄有未提交變更；儲存結果描述該次執行。 |
| 曾見輸入重查 | 事後與凍結逐字稿重查為回歸證據，並非新的保留評測；不重測 OCR／ASR。 |
| 抽取與來源 | 漏抽、歧義期間、重列、非 GAAP 定義與抽樣畫面都可能讓查核無法完成。 |
| 次數與費用 | 每 IP 每 10 分鐘 5 次；[供應商各自上限及全體總額上限](docs/LIVE_CHECK.md#atomic-cost-cap)。比較會略過額度用完的供應商；次數限制會終止比較。 |
| 修正 | 僅修改唯一綁定且被否定的數字；意見與未查核文字保留，絕不表示整篇文章已核准。 |

[完整限制](docs/evidence/REVIEW_GUIDE.md#limits) · [來源層級](docs/DATA_SOURCES.md) ·
[歷史申報日期政策](docs/VERIFICATION_POLICY.md)。本專案不提供投資建議。

## 專案目錄

| 路徑 | 用途 |
| --- | --- |
| [src/claimcheck/](src/claimcheck) | 代理迴圈、SEC 工具、平台、確定性檢查與修正 |
| [prompts/](prompts) | 版本化提示來源；執行紀錄保留雜湊 |
| [eval/v2/](eval/v2) | 凍結主張、修正標籤與獨立標準答案計算 |
| [docs/evidence/](docs/evidence) | 報告、清單、去除敏感資訊的軌跡與付費嘗試紀錄 |
| [docs/site/](docs/site) | 首頁、雙語資料與已提交美術素材 |
| [docs/explorer/](docs/explorer) | 逐題基準瀏覽器 |
| [server/live/](server/live)／[workers/live/](workers/live) | 共用帳本即時服務與執行器 |
| [tests/](tests) | 離線資料、程式回歸與網站生命週期測試 |
| [scripts/](scripts)／[docs/scripts/](docs/scripts) | 驗證、截圖與資料／圖表建構器 |
| [示範/](demo) | 獨立示範製作、測試與建置揭露 |

## 本機執行

```sh
uv sync
uv run python scripts/serve_site.py --port 8765
# Open http://127.0.0.1:8765/
```

預覽伺服器使用 Pages 疊加輸出與已提交結果。即時 API 路徑需要
另外[設定自架服務](docs/LIVE_CHECK.md#exact-handoff-for-claude--owner)。
新增證據連接器請參考[擴充指南](docs/EXTENDING.md)，
未完成功能見[規劃工作](ROADMAP.md)。

## 授權與致謝

程式採 [MIT](LICENSE)。財務證據來自 SEC EDGAR 申報，保留公司與申報識別碼。
模型使用 Meta Muse Spark 與 Muse Voice Transcribe，透過已記錄的平台路徑託管。
[致謝與媒體來源](CREDITS.md)區分模型生成的美術／旁白與財務證據。

[建置揭露](BUILD_LOG.md#build-log) · [更新紀錄](CHANGELOG.md) · [英文](README.md)
