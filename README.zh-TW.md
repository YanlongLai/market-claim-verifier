# Market Claim Verifier

[English](README.md) · [繁體中文](README.zh-TW.md)

**用 SEC 財報查核金融主張，讓每個結論都有可追溯的證據。**

一段財務敘述可能數字正確，卻用錯季度、單位或會計口徑。Market Claim Verifier 從美股研究與公司資料中抽取主張，搜尋財報證據，再由 Python 檢查數值。每份報告保留原文、來源、計算與尚未釐清的問題。

**[查看一筆查核結果](https://hackathon.dappgo.com/explorer/#G0119)** · [產品展示](https://hackathon.dappgo.com/) · [本機試用](#開始使用) · [評審導覽](JUDGES.md)

網站展示已保存的結果，不需要 API key。即時查核透過本機 CLI 執行；瀏覽器多檔上傳介面仍在規劃中。

<p align="center">
  <a href="https://hackathon.dappgo.com/"><img src="docs/figures/review-process-dark-3x-v3.gif" width="1012" alt="已保存的查核過程：金融主張、SEC 證據與程式判定"></a>
</p>

[![離線驗證](docs/badges/tests.svg)](.github/workflows/verify.yml) [![MIT 授權](docs/badges/license.svg)](LICENSE)

## 查看範例

先看 [Amazon 2023 年第三季營收主張](https://hackathon.dappgo.com/explorer/#G0119)：比較原始句子與 SEC 證據，再展開模型與程式的判斷紀錄。[三種結果示範](docs/evidence/judge-walkthrough/REPORT.md)則展示數字相符、數字被改動及期間錯誤時的處理。

若想看真實影音，從 [Microsoft 法說會案例](docs/evidence/real-av-context-live/REPORT.md)開始。原始錄影、抽取的主張、另外提供的事件期間及後續財報查核都可追溯；結果包含有證據支持的主張，也保留仍缺少上下文的案例。

## 查核流程

1. **保留原文。** 抽出財務主張，記錄引用與可取得的頁碼、畫面或音訊位置。
2. **搜尋證據。** Meta Muse 模型選取對應公司與期間的 SEC 數值或合格公司公告。
3. **程式檢查。** Python 驗證引用、數字、單位、比較方向與四捨五入。最終摘要依程式判定產生，模型原稿另存於 trace。
4. **檢視報告。** 開啟 HTML 或重用 JSON；同一股票的多份文件可以彙整，未完成項目仍會顯示。

| 結果 | 意義 |
| --- | --- |
| `supported` | 在已檢查的期間與精度內，證據支持抽取出的主張。 |
| `contradicted` | 有效證據與主張衝突，報告列出實際比對的數值。 |
| `insufficient_evidence` | 缺少必要期間、來源或可支援的檢查，不能據此認定主張錯誤。 |

上傳文件是待查核的主張來源，不會自動成為可信的財務證據。

## 準確度與平台比較

### 文字查核：266 個保留測試題目

原始評測包含 23 家公司的 357 個主張，其中 91 個用於開發，**266 個為保留測試組**。下表只呈現保留測試組。同一平台的無工具基準與查核流程使用相同模型；查核流程另外加入資料檢索與程式檢查。

| 平台／模型 | 查核流程正確數 | 無工具基準正確數 | 錯誤支持¹ |
| --- | ---: | ---: | ---: |
| Meta · Muse Spark 1.3 | 218/266 · **82.0%** | 111/266 · 41.7% | 4/139 |
| Baseten · Muse Spark Open | 240/266 · **90.2%** | 56/266 · 21.1% | 1/139 |
| Fireworks · Muse Spark Open | 237/266 · **89.1%** | 51/266 · 19.2% | 1/139 |

¹ 標準答案為矛盾或證據不足，卻被查核流程判為支持；分母涵蓋測試組全部 139 個此類題目。

失敗與未完成回應均計為錯誤。這是原始評測的保存結果，採用修正後標籤；兩筆標籤修正與後續事後測試均在[完整報告](docs/evidence/eval-v2-2026-10-27/REPORT.md)揭露。題目混合生成的財務案例與來源句子的改寫，這些成績不能推論為真實多媒體準確率。

### 真實公司資料：改善了什麼，還缺什麼

Microsoft 真實法說會片段的聲音只說「本季」，投影片則標示「FY27 Q1」。原始流程讀到了數字，卻無法安全連結期間。後續加入有來源的事件期間資料，讓查核能使用明確季度，同時保留原始引用。

後續另存一輪六個主張的實際查核結果，**Baseten 與 Fireworks 各支持五項**：營收、淨利、稀釋 EPS、營業利益與營收成長。未補期間的調整後 EPS 對照案例仍是證據不足。Meta 則有一項支持、兩項證據不足、三項 HTTP 500 執行失敗。

例如，財報營收 **$92.279B** 在投影片的顯示精度內，支持 **$92.3B** 的說法。這個結論以另外提供的 FY2027 Q1 期間為條件，不代表整段錄影已通過查核。[結果、證據與失敗紀錄](docs/evidence/real-av-context-live/REPORT.md) · [原始 WAV 與 MP4](eval/real-av-v1/README.md)。

另外三張 Tesla 真實簡報已有[多文件查核紀錄](docs/evidence/stock-context-posthoc-2026-10-30/REPORT.md)。其中未能驗證的圖表促成了明確的覆蓋提示：讀到圖表文字，不代表柱高與序列數值已被驗證。[圖表問題分析](docs/evidence/chart-diagnosis-2026-10-30/REPORT.md)。

<details>
<summary>九種輸入格式的控制組比較</summary>

<!-- multimodal-v1:start -->

六家公司、24 個基礎主張，轉成九種格式；不是 216 個獨立題目。表格為正確數／24，漏抽、未完成與判錯均保留於分母。三家使用相同檔案與凍結的 Meta OCR／ASR 文字。

| 格式 | Meta | Baseten | Fireworks |
| --- | ---: | ---: | ---: |
| TXT | 22/24 | 24/24 | 24/24 |
| Markdown | 22/24 | 24/24 | 24/24 |
| PDF | 23/24 | 24/24 | 24/24 |
| PNG | 24/24 | 24/24 | 24/24 |
| JPEG | 22/24 | 24/24 | 24/24 |
| WebP | 23/24 | 24/24 | 24/24 |
| WAV | 18/24 | 23/24 | 24/24 |
| MP3 | 14/24 | 24/24 | 24/24 |
| MP4 | 19/24 | 24/24 | 24/24 |

這是清晰控制素材上的單次測試，音訊與影片為合成內容。另列的原生圖片測試中，三家 PNG／JPEG／WebP 均各完成 6/6 張；完成回應不等於財務判定正確。原生聲音／影片端點沒有在這份比較中測試。

[完整方法、失敗與限制](docs/evidence/fair-multimodal-v1/REPORT.md) · [重用輸入、輸出與離線重算](docs/evidence/fair-multimodal-v1/REUSE.md)。

<!-- multimodal-v1:end -->

</details>

## 格式支援

三家文字查核路線接受相同的 repo 輸入格式。圖片與影音都使用 **Meta OCR／ASR**，即使後續文字查核選擇 Baseten 或 Fireworks 也是如此。

| 輸入 | 處理流程 | 主要限制 |
| --- | --- | --- |
| 文字／Markdown | 本機文字 → 選定查核平台 | 主張抽取有數量限制。 |
| PNG／JPEG／WebP | Meta OCR → 選定查核平台 | 未驗證圖表幾何關係或圖片真偽。 |
| 文字型 PDF | 本機逐頁擷取 → 選定查核平台 | 尚無掃描 PDF OCR 或跨頁上下文。 |
| 聲音 | Meta ASR → 選定查核平台 | 講者標籤不代表身分已驗證；時間位置以發言段落為主。 |
| 影片 | 語音轉錄＋三張畫面 OCR → 選定查核平台 | 可能漏掉未抽樣畫面；聲音與畫面分開查核。 |

掃描 PDF 與一般網頁 URL 尚未整合。本機工作佇列也不是供應商的折扣 Batch API。[完整格式限制與平台能力](docs/PROVIDERS.md)。

## 開始使用

CLI 需要 Python 3.12–3.14 與 `uv`；影音處理另需 FFmpeg 和 ffprobe。

```sh
git clone https://github.com/YanlongLai/market-claim-verifier.git
cd market-claim-verifier
uv sync

# 檢視請求內容，不呼叫模型。
uv run python -m claimcheck verify --provider baseten --dry-run \
  'Meta Q2 2025 revenue was $47.5B'
```

在環境變數設定 `BASETEN_API_KEY`，即可用 $1 預算上限執行即時查核：

```sh
uv run python -m claimcheck verify --provider baseten --budget 1 \
  'Meta Q2 2025 revenue was $47.5B'
```

Meta 使用 `MODEL_API_KEY`，Fireworks 使用 `FIREWORKS_API_KEY`。即時查核需要網路，trace 與預算紀錄存於 `runs/`。多媒體前處理另外需要 Meta key。

### 查核整篇貼文

```sh
uv run python -m claimcheck post examples/posts/bigtech-thread.txt \
  --provider baseten --budget 1
```

HTML／JSON 報告保留原文、證據與程式檢查。[英文與中文保存範例](docs/evidence/posts-2026-10-28/)。

### 同一股票的多份文件

`review-stock` 結合有預算限制的文件佇列與股票摘要；`stock-summary` 可彙整已有報告，不再呼叫模型。[多文件指南](docs/STOCK_REVIEW.md)說明預算、證據快照、續跑與匯出；[事件期間指南](docs/EVENT_CONTEXT.md)說明如何提供已檢視的期間，而不將它混入原始發言。

單一圖片、聲音、影片或文字 PDF 可使用 `ingest`。[指令與限制](docs/PROVIDERS.md#current-repository-input-contract)。

## API 單價與使用成本

文件費用包含前處理、主張抽取與每次查核呼叫。歷史 357 題文字評測中，Baseten／Fireworks 平均約 **$0.020／主張**，Meta 約 **$0.026／主張**。這是當次流程的觀察值，不是每份文件的報價或服務保證。[實測費用與延遲](docs/evidence/eval-v2-2026-10-27/REPORT.md)。

2026-10-30 核對的公開價格快照；單位為每百萬 tokens、美元：

| 平台／模型 | 輸入 | 快取輸入 | 輸出 |
| --- | ---: | ---: | ---: |
| Meta · Muse Spark 1.3 Standard | $1.25 | $0.15 | $4.25 |
| Baseten · Muse Spark Open | $1.25 | $0.15 | $4.25 |
| Fireworks · Muse Spark Open | $1.25 | $0.15 | $4.25 |

Meta ASR 當時列價為 $0.18／小時；圖片 OCR 依 token 計費。Ledger 估算包含失敗與保留額，不等同供應商帳單。[官方價格來源與 Batch 說明](docs/PROVIDERS.md#price-comparison) · [最近一輪查核費用](docs/evidence/real-av-context-live/REPORT.md#spend-usd-estimatedreserved)。

## 限制

目前以美股及已支援的 SEC／公司公告證據為範圍。標記錯誤、財報重列、財政年度與 non-GAAP 證據缺漏都會影響結果。事件期間是可追溯、但未認證的補充 metadata。

媒體辨識與主張抽取仍可能漏失。真實影音測試只有一個場景；格式控制組使用合成影音，兩者都不足以代表廣泛的金融影音準確率。報告用於檢視敘述，不產生投資評級。

## 重現結果與擴充

執行 `sh scripts/verify.sh` 可檢查資料 fixture、Python／Node 測試、圖表、資料重建與連結；完整驗證另需 Node 22+。安裝依賴可能使用網路，驗證本身則離線執行，不需要模型金鑰。[驗證指南](AGENTS.md) · [測試與可重用輸入輸出](docs/TEST_RECORDS.md)。

新增財務來源可從[擴充指南](docs/EXTENDING.md)、[證據格式](docs/EVIDENCE_RECORDS.md)及[資料政策](docs/DATA_SOURCES.md)開始。[開發計畫](docs/DAY5_PLAN.md)區分已完成能力，以及仍待開發的上傳介面、更多真實資料評測和跨模態整合。

Repo 程式與 demo 工作均於 hackathon 期間建立。[建置紀錄](BUILD_LOG.md) · [更新紀錄](CHANGELOG.md) · [MIT 程式授權](LICENSE) · [資料與媒體來源](CREDITS.md)。英文為主要文件語言，原始證據保持原文。[語言規範](docs/LANGUAGE.md)。

## 技術參考

[英文技術附錄](README.md#technical-reference)保留歷史評測、證據規則、模型與程式分工、架構圖及可重建圖表。
