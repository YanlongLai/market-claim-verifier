<p align="center">
  <a href="https://hackathon.dappgo.com/"><img src="docs/figures/review-process-dark-3x-v3.gif" width="1012" alt="查核重播：輸入主張、SEC 證據、數字比對與判定"></a>
</p>

# Market Claim Verifier

[English（主要版本）](README.md) | **繁體中文**

**輸入金融說法，取得 SEC 證據與可追溯的查核判定。**

[🌐 網站](https://hackathon.dappgo.com/) · [🔎 結果瀏覽器](https://hackathon.dappgo.com/explorer/index.zh#G0119) · [⚖️ 評審指南](JUDGES.md) · [🚀 開始使用](#開始使用)

[![離線測試](docs/badges/tests.svg)](.github/workflows/verify.yml)
[![MIT 授權](docs/badges/license.svg)](LICENSE)
[![Meta AI hackathon](docs/badges/hackathon.svg)](BUILD_LOG.md)

Meta Muse 模型找出主張、選擇工具並擷取證據；Python 核對數字、期間、單位與引用。範圍是**美股**，證據來自 SEC XBRL 與公司提交的財報新聞稿。

> [!NOTE]
> 網站展示已儲存的查核結果；本機 CLI 可以呼叫即時模型。上傳文件屬於待查核內容，不會自動成為可信的財務證據。

**快速導覽：** [格式支援](#格式支援) · [準確度與平台比較](#準確度與平台比較) · [多媒體成本與品質](#多媒體成本與品質) · [API 單價](#api-單價) · [開始使用](#開始使用) · [限制](#限制)

## 格式支援

✅ 已接入 · 🟡 有限制／需要前處理 · — 未接入。這是**本專案的整合狀態**，不代表準確率、全文覆蓋率或供應商所有模型的能力。🟡 表示目前可執行但有前處理／限制，不只是規劃中的功能。

| 輸入格式 | Meta 文字查核 | Baseten 文字查核 | Fireworks 文字查核 | 實際流程與限制 |
| --- | :---: | :---: | :---: | --- |
| 📝 文字／Markdown | ✅ | ✅ | ✅ | 中英文金融主張；不保證找出全部主張 |
| 🖼️ PNG／JPEG／WebP | 🟡 | 🟡＋Meta 金鑰 | 🟡＋Meta 金鑰 | Meta OCR → 指定文字平台；不鑑定圖片真偽 |
| 📄 原生文字 PDF | 🟡 | 🟡 | 🟡 | 本機逐頁解析 → 文字查核；最多 100 頁，不跨頁傳遞語境 |
| 📠 掃描 PDF | — | — | — | 尚未實作 PDF OCR；無法讀取的頁面標為未查核 |
| 🎙️ 聲音檔案 | 🟡 | 🟡＋Meta 金鑰 | 🟡＋Meta 金鑰 | Meta ASR → 指定文字平台；時間戳涵蓋整段發言，講者身分未驗證 |
| 🎬 影片 | 🟡 | 🟡＋Meta 金鑰 | 🟡＋Meta 金鑰 | Meta ASR＋三張抽樣畫面的 OCR；不是完整逐幀查核 |
| 🔗 一般網頁 URL | — | — | — | 不處理登入、瀏覽器渲染或任意 HTML |
| 📦 供應商原生 Batch | — | — | — | 並行執行不等於供應商折扣批次服務 |

[測試紀錄索引與 reuse 指南](docs/TEST_RECORDS.md) · [新增六種格式實測](docs/evidence/input-formats-2026-10-30/REPORT.md)保留各案例的判定、覆蓋、耗時及費用；下方提供摘要。這些小型合成案例不代表完整的「格式 × 平台」評測。

檔案上限 **128 MiB**；影音最長 **2 小時**。這是接受範圍，不是該規模下的準確度保證。[詳細格式與平台能力](docs/PROVIDERS.md)。

## 準確度與平台比較

### 🔍 Single-shot 與 Agent 是什麼？

**Single-shot 讓模型直接回答；Agent 先檢索證據，再由 Python 核對答案。** 這是兩種執行模式，不是兩個模型名稱；同一平台的比較使用相同設定模型。

```text
single_shot：主張 → 模型直接回答 → 判定
agent：     主張 → 模型選擇 SEC 工具 → 取得證據 → 模型草稿
                    → Python 核對數字、期間與引用 → 最終判定
```

| 問題 | Single-shot（單次回答基準） | Agent（工具查核流程） |
| --- | --- | --- |
| 是否檢索 SEC 證據？ | 不用工具，依模型已有知識作答 | 使用 SEC 查詢與計算工具 |
| 誰決定最終結果？ | 模型的回答 | 程式檢查可修正模型草稿 |
| 能否查看支持判定的財報？ | 此流程沒有檢索財報證據 | 保留引用數字與原始來源連結 |
| 這個比較衡量什麼？ | 無工具的基準表現 | 完整「檢索＋程式檢查」流程 |

**例如：**「Amazon 在 2023 年曆年第三季營收為 $143.1B」。Agent 可取得 $143.083B，核對期間與四捨五入後判為 `supported`。Single-shot 可能答對或回覆證據不足，但不會在這次查核中檢索該財報。[查看已記錄案例](https://hackathon.dappgo.com/explorer/index.zh#G0119)。

> [!NOTE]
> `single_shot` 是無工具基準的名稱，不保證只有一次 API 請求；實際用量請看呼叫紀錄。下面的準確率提升衡量整套 Agent 流程，不能全部歸因於某一條規則。「無工具準確率」就是 single-shot 準確率；成本與時間欄位則是 **Agent** 流程。

### 📝 文字：相同資料集的歷史評測

**357 個主張、23 家公司：91 筆開發集＋266 筆獨立測試集。** 使用修正後標準答案；失敗或未完成皆計為錯誤。費用及速度是歷史平均值，不是每份文件的固定價格或服務保證。

| 平台／Meta 模型 | Agent 準確率 | 無工具準確率 | 錯誤支持¹ | 每主張平均費用 | 平均時間 |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Baseten · Spark Open** | **90.5%**（323/357） | 20.7% | 1/186 | **$0.020** | **12 秒** |
| **Fireworks · Spark Open** | **90.5%**（323/357） | 19.9% | 1/186 | **$0.020** | **67 秒** |
| **Meta API · Spark 1.3** | **83.2%**（297/357） | 44.3% | 4/186 | **$0.026** | **39 秒** |

¹ 標準答案不成立或證據不足，卻被判為成立。[完整報告與信賴區間](docs/evidence/eval-v2-2026-10-27/REPORT.md)。兩筆標準答案經修正，[原始登記版本](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md)仍保留；後續重跑是事後回歸，不是新的獨立測試。

Baseten 與 Fireworks 的總分相同，但答對案例不同。單看 266 筆獨立測試集，分別為 **240/266＝90.2%** 與 **237/266＝89.1%**；不能把總分相同解讀為能力完全一致。

### 📊 各格式的準確度證據

| 格式 | Meta | Baseten | Fireworks |
| --- | --- | --- | --- |
| 文字主張 | **83.2%**，357 筆 | **90.5%**，357 筆 | **90.5%**，357 筆 |
| 圖片 | 僅開發測試 | Meta OCR 的 JPEG 測試 | Meta OCR 的 WebP 測試 |
| 原生文字 PDF | 原生文字測試；無準確度評測 | 無準確度評測 | 無準確度評測 |
| 聲音 | 僅開發測試 | 使用 Meta ASR 的開發測試 | Meta ASR 的 MP3 測試 |
| 影片 | 僅開發測試 | 使用 Meta OCR／ASR 的開發測試 | 三張 Meta OCR 畫面的無聲 MP4 測試 |

> [!IMPORTANT]
> **文字準確率不能套用到 PDF、圖片、聲音或影片。** 多媒體還受辨識與主張抽取品質影響。開發測試不等於準確度評測；「無評測」表示沒有實測的評測準確率，不代表 0% 準確率或不支援。

## 多媒體成本與品質

以下為[2026-10-30 開發測試](docs/evidence/multimodal-2026-10-30/REPORT.md)的整份檔案流程估算。素材及設定不同，**不能當成平台排名**；失敗呼叫的保守預留費用可能仍計入。

| 素材 | 流程 | 總估算費用 | 經過時間 | 觀察到的覆蓋／限制 |
| --- | --- | ---: | ---: | --- |
| 🖼️ 截圖 | Meta OCR＋Meta 文字 | **$0.0738** | **59.7 秒** | 讀到 2/2 預期數值；小型合成控制案例 |
| 🎙️ 短音訊 | Meta ASR＋Baseten 文字 | **$0.0791** | **56.4 秒** | 5/5 數值主張經程式查核 |
| 🎙️ 雙人聲音訊 | Meta ASR＋Meta 文字 | **$0.0492** | **69.8 秒** | 兩個聲音被合併為同一講者標籤 |
| 🎙️ 12 分鐘音訊 | Meta ASR＋Baseten 文字 | **$0.2405** | **258.8 秒** | 該次歷史執行查核 19/60 個主張 |
| 🎬 表列影片 | Meta OCR／ASR＋Meta 文字 | **$0.3359** | **312.1 秒** | 8/9 個主張經查核；只抽三張畫面 |
| 🎬 字幕影片 | Meta OCR／ASR＋Baseten 文字 | **$0.1554** | **106.6 秒** | 該控制案例查核 9/9 個主張 |

[後續長音訊實驗](docs/evidence/multimodal-2026-10-30b/REPORT.md)把查核覆蓋提高到 44/60；對凍結的 ASR 文字重查達到 50/60。這是重複合成事實的事後覆蓋率，**不是判定真偽的準確率**。

### 新增格式實測 — 2026-10-30

[六個事先選定的合成案例](docs/evidence/input-formats-2026-10-30/REPORT.md)合計估計花費 **$0.32767930**，低於 $3 上限。**15 個抽出的主張列**全部經程式查核，每個案例都抓到刻意放錯的 EPS。這不是全文召回率或通用準確率，素材與流程不同也不能作為平台排名。

| 輸入 | 流程 | 已查核／已抽出 | 估計費用（美元） | 經過時間 |
| --- | --- | ---: | ---: | ---: |
| Markdown | Fireworks 文字 | 2/2 | $0.031686 | 110.4 秒 |
| JPEG | Meta OCR → Baseten 文字 | 2/2 | $0.039148 | 18.9 秒 |
| WebP | Meta OCR → Fireworks 文字 | 2/2 | $0.034332 | 163.7 秒 |
| MP3 | Meta ASR → Fireworks 文字 | 3/3 | $0.079938 | 444.1 秒 |
| 無聲 MP4 | 三張 Meta OCR 畫面 → Fireworks 文字 | 4/4 | $0.089863 | 463.6 秒 |
| 原生文字 PDF | 本機逐頁解析 → Meta 文字 | 2/2 | $0.052712 | 71.8 秒 |

五項狀態為完成；無聲 MP4 因沒有音軌保留 `partial`，但四個抽出的畫面主張都已查核。影片仍只抽三張畫面。這輪沒有測試或新增 PDF OCR、一般 URL、Baseten／Fireworks 原生影音端點。費用依用量估算，不是官方帳單；表內單項金額經四捨五入。

**這六項測試的各平台 API 花費（美元）：**

| 平台 | API 估計花費 |
| --- | ---: |
| Meta | $0.07223290 |
| Baseten | $0.03489420 |
| Fireworks | $0.22055220 |
| **合計** | **$0.32767930** |

依[逐筆請求 ledger](docs/evidence/input-formats-2026-10-30/ledger.jsonl)核算。合計包含一筆沒有 reconcile 事件的 ASR 預留費用 $0.00240000，保留為保守估算。Meta 費用包含供其他文字平台使用的 OCR／ASR 前處理，以及自身的文字查核。這些費用**已包含在上方各輸入格式的費用內**，不是額外加收；範圍僅限這六項測試，不是專案歷來總花費或官方帳單。

**重用測試紀錄：** [紀錄索引與指南](docs/TEST_RECORDS.md) · [機器可讀的執行索引](docs/evidence/input-formats-2026-10-30/runs.json) · [驗證紀錄與日誌](docs/evidence/input-formats-2026-10-30/validation.json)。已保留輸入／雜湊、參數、原始回應、trace、結果與費用。凍結的 OCR／ASR 文字可用於後續文字查核，省下再次前處理的費用；這不會重新驗證辨識或講者歸屬。重建既有報告可離線執行；重新呼叫模型會花費 credit：

```sh
# 離線：重建既有報告，檢查輸入雜湊與 ledger 費用加總。
python3 scripts/multimodal/build_format_report.py
# 付費：重跑六項，共用 $3 上限；必須使用新的輸出目錄。
.venv/bin/python scripts/multimodal/run_format_suite.py --out-root runs/formats-001
```

## API 單價

美元／**每百萬 tokens**，價格查核日期 **2026-10-30**。單價與上面的整條流程費用不同。

| 平台 | 模型 | 輸入 | 快取輸入 | 輸出 |
| --- | --- | ---: | ---: | ---: |
| Meta API | Muse Spark 1.3 Standard | $1.25 | $0.15 | $4.25 |
| Baseten | Muse Spark Open | $1.25 | $0.15 | $4.25 |
| Fireworks | Muse Spark Open | $1.25 | $0.15 | $4.25 |

| 額外步驟 | 費用依據 | 適用內容 |
| --- | --- | --- |
| Meta 圖片 OCR | 按 token；不是固定每張價格 | 圖片、影片抽樣畫面 |
| Meta ASR | **$0.18／小時，$0.003／分鐘** | 聲音、影片音軌 |
| 原生 PDF 解析 | 本機 CPU；抽取本身不需模型費用 | 後續主張查核仍按 token 計價 |
| 抽取與驗證 | 每次模型呼叫與適用重試 | 所有接受格式 |

**文件成本＝前處理＋抽取＋全部主張的查核呼叫。** 一份文件可能包含數十個主張，ledger 估算不是帳單。[官方價格來源、Contributor 模式條件與 Batch 限制](docs/PROVIDERS.md#price-comparison)。

## 為什麼需要這個工具

看似合理的金融句子可能用了錯誤季度、單位或比較方式。本專案起源於 DappGo AI 評論未通過內部主張檢查：流暢的說明不夠，每個可查核數字都需要來源、正確期間與可重現的比較。

## 查看範例

先看[三種結果的評審導覽](docs/evidence/judge-walkthrough/REPORT.md)：同一份官方來源，分別檢查相符數字、改錯數字與錯誤期間。這是離線程式查核，不是即時模型展示。

再開啟 [G0119](https://hackathon.dappgo.com/explorer/index.zh#G0119)，查看原句、修正後標準答案、六套系統與 SEC 引用。網站為已儲存的重播；[展示影片公開網址仍待補](demo/JUDGE_INTRO.md)。

## 查核流程

1. **抽取**：拆成個別主張，保留原始引用。
2. **檢索**：依公司與期間取得 SEC 事實或已接納的新聞稿引用。
3. **驗證**：Python 核對數字、單位、精度、比較詞與證據編號。
4. **說明**：輸出判定、來源定位、限制、成本與追蹤紀錄。

![兩次真實執行的判定與 SEC 證據](docs/figures/verdict-cards.svg)

*2026-10-27 的兩次真實執行；圖中數據來自保留的紀錄。*

結果為 `supported`（有證據支持）、`contradicted`（與證據矛盾）或 `insufficient_evidence`（證據不足）。流程完成不表示全部主張均已找到；沒有獨立標註的分母時，全文召回率維持未知。

## 開始使用

環境：**Python 3.12–3.14、uv、Node 22+**；影音另需 FFmpeg／ffprobe。以下指令從本機 repo 目錄執行。

**1. 不使用模型金鑰，驗證可重現性。**

```sh
sh scripts/verify.sh
```

首次會下載鎖定的依賴，之後在暫存副本離線檢查測試、圖表、資料重建與連結；這不是即時模型準確度評測。[預期輸出](AGENTS.md#offline-verification)。

**2. 安裝並預覽請求，不花費 API credit。**

```sh
uv sync
uv run python -m claimcheck verify --provider baseten --dry-run \
  'Meta Q2 2025 revenue was $47.5B'
```

**3. 執行有預算上限的即時查核。** 在 repo 外設定所選平台的 `MODEL_API_KEY`、`BASETEN_API_KEY` 或 `FIREWORKS_API_KEY`。

```sh
uv run python -m claimcheck verify --provider baseten --budget 1 \
  'Meta Q2 2025 revenue was $47.5B'
```

即時查核需要網路並可能收費；紀錄存於 `runs/`。其他模型、推理與 token 設定請看 `--help`。

### 查核整篇貼文

```sh
uv run python -m claimcheck post examples/posts/bigtech-thread.txt \
  --provider baseten --budget 1
```

輸出 `report.json`、`report.html`、原文引用與程式查核連結。抽取有上限，不保證找到全部主張。[中英文範例](docs/evidence/posts-2026-10-28/)。

### 圖片與其他本機檔案

```sh
uv run python -m claimcheck ingest tests/fixtures/multimodal/example-post.png \
  --provider baseten --budget 1 --out runs/example-input
```

多媒體前處理需要 Meta 金鑰，即使文字查核使用其他平台。輸出 `ingest.json` 與 `ingest.html`；已有輸出目錄不會覆寫。

PDF 使用 `ingest report.pdf` 與相同參數。保留頁碼與檔案 hash，拒絕加密文件；掃描／空白頁標示未查核。限制為 100 頁、每頁 100,000 字元、整份 1,000,000 字元；表格與閱讀順序仍需檢查。

## 限制

- SEC 標記錯誤、重編財報與財年差異可能影響證據。
- 期間不明、不支援的指標或證據未解決時，可能回傳證據不足。
- 公司展望只能證明公司曾這樣說，不保證未來實現。
- 多媒體測試是少量開發控制案例，不是實際財報電話會議的通用評測。
- 影片三張抽樣畫面不能涵蓋所有投影片；講者標籤不是身分驗證。
- 本次範圍限美股，不包含台灣資料與一般網頁爬取。

## 擴充與貢獻

[擴充指南](docs/EXTENDING.md) · [證據格式](docs/EVIDENCE_RECORDS.md) · [開發優先順序](docs/DAY5_PLAN.md) · [路線圖](ROADMAP.md) · [更新紀錄](CHANGELOG.md)。新增來源需要權威規則、不可變快照、定位與獨立評測，不只是更換 prompt。

## 技術參考

完整技術附錄以英文主版維護，避免兩份細節規格分歧：

| 主題 | 文件 |
| --- | --- |
| L4 公司新聞稿 | [來源與判定範圍](README.md#l4-earnings-release-evidence) |
| 原始評測、歷史執行與圖表 | [詳細結果](README.md#real-results) |
| Meta 模型與平台架構 | [模型使用方式](README.md#how-meta-models-are-used) |
| 比較詞、精度與最終判定 | [程式規則](README.md#why-you-can-trust-a-verdict) |
| L1–L4 證據層級 | [可稽核證據](README.md#evidence-you-can-audit) |
| 評測建立與執行 | [Evaluation](README.md#evaluation) |
| 架構與差距分數 | [技術附錄](README.md#technical-reference) |

## Hackathon、圖片與語言

所有 repo 程式與 demo 工作均於活動期間建立，沒有活動前既有的 repo 程式。[建置紀錄](BUILD_LOG.md) · [MIT 程式授權](LICENSE) · [資料與媒體來源](CREDITS.md)。

頂部動畫直接擷取網站審查場景；另保留 Hover 獨立動畫的[重建程式](docs/scripts/build_readme_robot.py)、[靜態版本](docs/site/img/auditor/H/present.webp)；[設計與生成歷程](docs/prompts/site/auditor-robot.md)。[AI 主視覺的可重用 prompt](docs/prompts/hero-image.md)另有記錄；AI 圖片是示意，數值圖表使用實測資料。

**英文 README 是主要版本。** 此頁提供繁體中文導覽；原始主張、證據與模型輸出維持原文。[語言規範](docs/LANGUAGE.md)。
