# Market Claim Verifier

[英文](../../README.md) · [繁體中文](../../README.zh-TW.md)

**用 Meta 開放權重模型 Muse Spark Open 對照 SEC 財報查核金融主張，讓每個結論都有可追溯的證據。**

Baseten · Muse Spark Open 查核流程，原始保留文字測試組，採修正後標準答案：

| 正確數 | 錯誤支持 | 每個主張平均費用 |
| --- | --- | --- |
| **[240/266 = 90.2%](eval-v2-2026-10-27/REPORT.md#metrics)** | **[1/139](eval-v2-2026-10-27/REPORT.md#per-gold-class-precision-and-recall)** 個不應支持的主張被接受 | **[約 $0.02](eval-v2-2026-10-27/REPORT.md#metrics)**（紀錄值 $0.019880） |

**Apple：「單季營收 $416.2B」→ 其實是全年。** 2025 財年第四季營收為 **$102.5B**，原主張約為該季的 **4 倍**。[保存的查核與計算](posts-2026-10-28/demo-thread-baseten/report.json) · [可閱讀報告](posts-2026-10-28/demo-thread-baseten/report.html)。

**[線上 示範](https://hackathon.dappgo.com/)** · **[評審導覽](../../JUDGES.md)** · [影片 — 待補（Claude 待補）](../../JUDGES.md#demo-video-todo) · [本機試用](#開始使用)

網站提供需要密碼的即時文字查核與免密碼的已儲存範例；CLI 也可即時查核。瀏覽器上傳仍在規劃中。[評測與產品限制](../../JUDGES.md#limits)。

<p align="center">
  <a href="https://hackathon.dappgo.com/"><img src="../figures/review-process-dark-3x-v3.gif" width="1012" alt="已保存的查核過程：金融主張、SEC 證據與程式判定"></a>
</p>

[![離線驗證](../badges/tests.svg)](../../.github/workflows/verify.yml) [![MIT 授權](../badges/license.svg)](../../LICENSE)

## 查看範例

先看 [Amazon 2023 年第三季營收主張](https://hackathon.dappgo.com/explorer/#G0119)：比較原始句子與 SEC 證據，再展開模型與程式的判斷紀錄。[三種結果示範](judge-walkthrough/REPORT.md)以離線程式檢查展示數字相符、數字被改動及期間錯誤時的處理。

真實公司資料可看 [Microsoft 法說會查核](real-av-context-live/REPORT.md)或 [Tesla 多文件查核](stock-context-posthoc-2026-10-30/REPORT.md)。每份報告保留原文、證據、計算與尚未釐清的問題。

[即時查核](https://hackathon.dappgo.com/zh/#live-check)（需密碼；已儲存範例不需密碼）· [真實世界](https://hackathon.dappgo.com/wild/)。

## 為什麼使用 Meta 開放權重模型

在相同的[保留測試主張](eval-v2-2026-10-27/REPORT.md#metrics)上，**Muse Spark Open 加上工具與程式檢查，在 Baseten 得到 90.2%，高於託管 Muse Spark 1.3 的 82.0%**；當次平均費用相近，約為**每個主張 $0.020 與 $0.026**。

| 平台／模型 | 查核流程正確數 | 無工具基準正確數 | 錯誤支持¹ | 查核平均費用 | 證據 |
| --- | ---: | ---: | ---: | ---: | --- |
| Baseten · Muse Spark Open | 240/266 · **90.2%** | 56/266 · 21.1% | 1/139 | $0.019880 | [保存結果](eval-v2-2026-10-27/REPORT.md) |
| Fireworks · Muse Spark Open | 237/266 · **89.1%** | 51/266 · 19.2% | 1/139 | $0.019973 | [保存結果](eval-v2-2026-10-27/REPORT.md) |
| Meta · Muse Spark 1.3 | 218/266 · **82.0%** | 111/266 · 41.7% | 4/139 | $0.025880 | [保存結果](eval-v2-2026-10-27/REPORT.md) |

¹ 錯誤支持指標準答案為矛盾或證據不足，卻被接受為支持。表格只使用 [266 個保留測試主張](eval-v2-2026-10-27/REPORT.md#metrics)，失敗均計為錯誤。

**可攜性：**同一套 代理 迴圈可在 Baseten 與 Fireworks 執行，沿用相同工具、證據 ID、預算紀錄與 Python 檢查。上表保存的開放權重結果涵蓋兩個平台。[平台轉接程式](../../src/claimcheck/providers.py) · [確切模型 ID 與執行 執行清單](eval-v2-2026-10-27/manifest.json)。

Meta 也透過 **`muse-voice-transcribe-1.0`** 提供語音轉錄，並以 Muse Spark OCR 讀取圖片及抽樣影片畫面，再交給選定平台進行文字查核。[媒體轉接程式](../../src/claimcheck/ingest_media.py) · [保存的影音查核](real-av-context-live/REPORT.md)。

## 代理運作：Muse 選擇下一步，Python 檢查答案

- **Muse 決定查什麼。** 自主選擇工具與參數：`lookup_fact`、用 `list_periods` 確認可用期間、用 `compute_change` 比較變化、用 `history_rank` 查核紀錄型主張；合格的展望與 non-GAAP 主張則使用 `find_earnings_release` 後接 `quote_release`，再引用回傳證據撰寫判定草稿。[工具定義](../../src/claimcheck/tools.py) · [公司公告工具](../../src/claimcheck/release_tools.py)。
- **Python 執行並驗證。** 計算數值、檢查期間、單位、精度、方向與證據 ID，驗證公告原始位元組及引文位置，並決定最終判定。模型呼叫前會先保留預算。[程式檢查](../../src/claimcheck/checks.py) · [公告檢查](../../src/claimcheck/release_checks.py) · [預算紀錄](../../src/claimcheck/budget.py)。

在一筆[真實 Alphabet 軌跡](2026-10-27/20261027T222758Z-8959a100.json)中，Muse 先選擇 `lookup_fact`，再用 `history_rank` 查核「首次」的說法；Python 檢查引用證據後才回傳判定。[時序圖](../diagrams/real-run-sequence.mmd)。

## 查核流程

1. **保留原文。** 抽出財務主張，記錄引用與可取得的頁碼、畫面或音訊位置。
2. **搜尋證據。** Meta Muse 模型選取對應公司與期間的 SEC 數值或合格公司公告。
3. **程式檢查。** Python 驗證引用、數字、單位、比較方向與四捨五入。最終摘要依程式判定產生，模型原稿另存於 軌跡。
4. **檢視報告。** 開啟 HTML 或重用 JSON；同一股票的多份文件可以彙整，未完成項目仍會顯示。

| 結果 | 意義 |
| --- | --- |
| `supported` | 在已檢查的期間與精度內，證據支持抽取出的主張。 |
| `contradicted` | 有效證據與主張衝突，報告列出實際比對的數值。 |
| `insufficient_evidence` | 缺少必要期間、來源或可支援的檢查，不能據此認定主張錯誤。 |

上傳文件是待查核的主張來源，不會自動成為可信的財務證據。

## 格式支援

可透過 CLI 試用文字、Markdown、圖片、文字型 PDF、聲音及影片。所有查核平台共用這些輸入轉接程式；圖片與影音使用 Meta OCR／ASR。[支援格式](../PROVIDERS.md#current-repository-input-contract) · [輸入與來源限制](../../JUDGES.md#input-and-source-boundaries) · [真實公司資料與控制組研究](../../JUDGES.md#media-studies)。

<!-- multimodal-v1:start -->
[格式控制組結果與限制](../../JUDGES.md#controlled-format-study) · [重用凍結的輸入與輸出](fair-multimodal-v1/REUSE.md)。
<!-- multimodal-v1:end -->

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

Meta 使用 `MODEL_API_KEY`，Fireworks 使用 `FIREWORKS_API_KEY`。即時查核需要網路，軌跡 與預算紀錄存於 `runs/`。多媒體前處理另外需要 Meta 金鑰。

### 查核整篇貼文

```sh
uv run python -m claimcheck post examples/posts/bigtech-thread.txt \
  --provider baseten --budget 1
```

HTML／JSON 報告保留原文、證據與程式檢查。[英文與中文保存範例](posts-2026-10-28)。

### 同一股票的多份文件

`review-stock` 結合有預算限制的文件佇列與股票摘要；`stock-summary` 可彙整已有報告，不再呼叫模型。[多文件指南](../STOCK_REVIEW.md)說明預算、證據快照、續跑與匯出；[事件期間指南](../EVENT_CONTEXT.md)說明如何提供已檢視的期間，而不將它混入原始發言。

單一圖片、聲音、影片或文字 PDF 可使用 `ingest`。[指令與限制](../PROVIDERS.md#current-repository-input-contract)。

## API 單價與使用成本

文件費用包含前處理、主張抽取與每次查核呼叫。開頭費用來自[保留文字測試組的保存平均值](eval-v2-2026-10-27/REPORT.md#metrics)。[費用、延遲與有日期的平台價格快照](../PROVIDERS.md) · [費用計算與 批次 限制](../../JUDGES.md#cost-accounting) · [最近一輪查核費用](real-av-context-live/REPORT.md#spend-usd-estimatedreserved)。

## 真實世界測試

[新聞 與 Threads 評測](real-world-2026-11-02/REPORT.md)保留了 80 則新聞改寫，以及第二階段的 30 則自家貼文、48 則第三方 Threads 改寫與兩張真實卡片。三個平台分別執行主張查核、貼文抽取查核及圖片匯入。Threads 來自 擁有者 授權的登入瀏覽與 熱門 搜尋結果，沒有可靠的互動數據，不能視為已驗證的高互動樣本。

第二階段只有 **5 筆**獨立 SEC 事實標籤，另有 36 筆僅評估範圍外的預期棄答、37 筆待審；自家貼文與圖片的事實準確率無法估計。六條圖片路徑均未完成主張查核：四條主張抽取未完成、一條抽取逾時、一條 OCR 未完成；所有失敗與費用均保留，每個計費平台共用 $8 上限。報告分開呈現翻譯顯示中的單位／比較期間錯誤、覆蓋、失敗、延遲及完整費用；原始貼文、卡片與逐字 OCR 留在本地忽略目錄。[合併結果](real-world-2026-11-02/REPORT.md#threads) · [待提供的自家 Reels／YouTube 檔案](real-world-2026-11-02/NEXT_SOURCES.md)。

在五筆事實標籤中，三個平台皆為直接查核 **2/5**（40%；Wilson 95% CI 11.8–76.9%）、貼文查核 **3/5**（60%；23.1–88.2%）；失敗計為錯誤，不能推論廣泛準確率。第二階段估計／保留費用共 **$10.537241**（Baseten $3.311842、Fireworks $3.316011、Meta $3.909388），兩階段合計 **$15.873363**。

## 限制

[JUDGES.md — 限制](../../JUDGES.md#limits)集中說明評測設計、來源範圍、媒體漏抽、附條件的事件期間與費用計算。

## 重現結果與擴充

執行 `sh scripts/verify.sh` 可檢查資料 固定測試資料、Python／Node 測試、圖表、資料重建與連結；完整驗證另需 Node 22+。安裝依賴可能使用網路，驗證本身則離線執行，不需要模型金鑰。[驗證指南](../../AGENTS.md) · [測試與可重用輸入輸出](../TEST_RECORDS.md)。

新增財務來源可從[擴充指南](../EXTENDING.md)、[證據格式](../EVIDENCE_RECORDS.md)及[資料政策](../DATA_SOURCES.md)開始。[開發計畫](../DAY5_PLAN.md)區分已完成能力，以及仍待開發的上傳介面、更多真實資料評測和跨模態整合。

專案 程式與 示範 工作均於 黑客松 期間建立。[建置紀錄](../../BUILD_LOG.md) · [更新紀錄](../../CHANGELOG.md) · [MIT 程式授權](../../LICENSE) · [資料與媒體來源](../../CREDITS.md)。英文為主要文件語言，原始證據保持原文。[語言規範](../LANGUAGE.md)。

## 技術參考

[英文技術附錄](../../README.md#technical-reference)保留歷史評測、證據規則、模型與程式分工、架構圖及可重建圖表。
