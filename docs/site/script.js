(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));

  const COPY = {
    en: {
      metaTitle: "SEC fact-checks for finance posts · Market claim verifier",
      metaDescription: "Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations. Held-out text: 90.2% (240/266); false support 1/139. Corrected gold.",
      metaImageAlt: "Market claim verifier comparing an example finance post with its saved SEC filing, alongside the auditor robot.",
      a11y: {
        skip: "Skip to content",
        home: "Market claim verifier home",
        nav: "Primary navigation",
        language: "Language",
        exampleLanguage: "Example language",
        chart: "Accuracy comparison chart"
      },
      nav: { how: "How it works", example: "Example", results: "Results", trust: "Trust" },
      hero: {
        titleLine1: "Paste a finance post.",
        titleLine2: "See what's true.",
        lede: "Every checked number links to the SEC filing that proves it."
      },
      stamps: {
        region: "Real finance claims pass through the checker and receive True, False, or Can't check stamps.",
        gate: "Muse Spark agent + SEC check",
        claims: "Claims and report verdicts",
        postPanel: "① Post under review", filingPanel: "② SEC filing", progress: "Review progress",
        waiting: "Waiting for filing", noNumber: "No SEC number to check", claim: "Claim",
        noNumberExplanation: "No matching filed number for this opinion or forecast.",
        revenue: "revenue",
        caption: { read: "Reading the post…", reach: (form) => `Opening the ${form}…`,
          find: (value) => `Found it: ${value}`, compare: (filed, posted) => `${filed} filed vs ${posted} posted`, fullYear: "That's the full year",
          uncheckable: (kind) => `${kind} — not in any filing` },
        noClaim: "Opinion / forecast — no filed number", stamp: "Stamp", next: "Next:",
        thread: "Thread",
        social: "Social post",
        repost: "Repost", article: "Article", example: "Example post", repostedFrom: "Reposted from",
        input: { text: "Text", screenshot: "Screenshot", audio: "Audio", video: "Video" },
        activity: { label: "Example activity", reply: "Replies", repost: "Reposts", like: "Likes", views: "Views" },
        audience: "Public", transcript: "Transcript", by: "By", speaker: "Speaker", turn: "ASR turn",
        release: "Earnings release", releaseStatus: "Furnished · unaudited · L4",
        rangeMatch: "Both guidance endpoints match",
        releaseMatch: "Number and period match",
        exampleDetail: "Fictional author and example follower count. Claims and verdicts come from real program checks.",
        pause: "Pause",
        play: "Play",
        true: "TRUE",
        false: "FALSE",
        unknown: "CAN'T CHECK",
        filed: "Filed", accuracy: "Accuracy score", within: "Within tolerance", off: "off", short: "short",
        direction: "Direction wrong", millions: "USD in millions", filingUnits: "As reported in the filing",
        stated: "Post says", growth: "growth", accession: "Accession", nineMonths: "Nine months", quarter: "Q4 (derived)",
        severity: { exact: "Exact", minor: "Minor", moderate: "Moderate", major: "Major", severe: "Severe" }
      },
      example: {
        title: "A real post, checked.",
        english: "English post",
        chinese: "Chinese post",
        postLabel: "Post",
        loading: "Loading the report...",
        unavailable: "The report is not available in this view.",
        claimCount: (count) => `${count} claims found`
      },
      verdict: { true: "True", false: "False", unknown: "Can't check" },
      claimKind: { reported_fact: "Money claim", forecast: "Forecast", opinion: "Opinion", guidance: "Guidance", non_gaap: "Non-GAAP" },
      claimSource: {
        sec: "SEC says",
        filed: "filed",
        see: "See filing",
        derived: "SEC check",
        notChecked: "No filed fact to compare for this claim.",
        noSource: "No filing value returned."
      },
      filing: {
        title: "Filing passage",
        close: "Close filing passage",
        passage: "The number in the filing",
        sourceFacts: "Source facts",
        claimSaid: "Claim said",
        filingSays: "Filing says",
        filingShort: "Filing",
        summaryPost: "Post says",
        thisPeriod: "this period",
        comparisonPeriod: "comparison",
        company: "Company",
        formDate: "Form + filed",
        period: "Period",
        concept: "XBRL concept",
        inMillions: "in millions",
        inThousands: "in thousands",
        inBillions: "in billions",
        reportedUnits: (power) => `10^${power} scale`,
        notAvailable: "Not available",
        notEnoughForChange: "not enough matched periods",
        noPassage: "No matching passage was found in the selected filing.",
        reason: "Why",
        original: "Open this number in the original filing",
        primary: "Open the primary filing",
        inline: "Open in SEC inline viewer",
        noLink: "No SEC link was supplied for this fact.",
        component: (id) => id ? `Evidence ${id}` : "Evidence",
        table: "Filing table",
        text: "Filing text"
      },
      how: {
        title: "How it works",
        lede: "A short path from a social post to a source you can open.",
        step1: {
          title: "Find the claim",
          body: "The AI uses Meta's Muse Spark models to find each number, period, and comparison in the post."
        },
        step2: {
          title: "Open the filing",
          body: "It looks up the company's SEC filing for the same company, number, and time period."
        },
        step3: {
          title: "Code decides",
          body: "Code, not the AI, compares the numbers and gives the final True, False, or Can't check verdict."
        }
      },
      capabilities: {
        title: "What it can check", report: "Evidence report", replay: "Replay example",
        xbrl: { title: "SEC XBRL · L1–L3", limit: "Reported numbers and periods; tagging and restatements can limit evidence." },
        release: { title: "Earnings releases · L4", limit: "Guidance and non-GAAP; furnished, unaudited. 32 development claims, not held-out." },
        screenshot: { title: "Screenshots", limit: "OCR text enters SEC checks; extraction can lose context. Self-made test images." },
        audio: { title: "Audio / video", limit: "ASR turns + 3 sampled frames; speakers unverified. Known period-loss error in video." }
      },
      results: {
        title: "Does it work?",
        lede: "Adding an SEC lookup and simple checks raises accuracy for all three ways to run Muse.",
        caption: (count) => count ? `Tested on ${count} claims with known answers.` : "Tested on the evaluation claims with known answers.",
        without: "Without tools",
        withChecks: "With SEC lookup + checks",
        change: (points) => `+${points} points`
      },
      posthoc: {
        title: "After two fixes · post-hoc rerun",
        key: "Agents only · v2 → rerun",
        provider: "Provider",
        accuracy: "Accuracy",
        falseSupported: "False “supported”",
        note: "The fixes were made after seeing these mistakes, so this is a regression check, not a new test score. Accuracy changes are within noise; false 'supported' answers dropped to zero.",
        report: "Rerun report"
      },
      research: {
        summary: "For researchers",
        ci: "95% intervals",
        paired: "Paired tests",
        costLatency: "Average cost and time per claim",
        weakSpots: "Per-type weak spots",
        familyLabels: {
          record_first: "First-time record claims",
          yoy: "Year-over-year claims",
          period_trap: "Fiscal and calendar periods"
        },
        goldCorrections: [
          "Amazon's 12-month 10-Q value was trailing-twelve-month data, not a fiscal year.",
          "Apple's 52/53-week quarter ending 2023-07-01 belongs to calendar Q2, not Q3."
        ]
      },
      trust: {
        title: "Why you can trust it",
        lede: "The source and the rules stay visible.",
        item1: "Every answer links to the filing.",
        item2: "The AI cannot change the numbers it quotes. If the quote changes, it is rejected.",
        item3: "We publish our own mistakes in"
      },
      footer: {
        title: "Run the check yourself.",
        lede: "Read the results, open the source, or run the same command on your own post.",
        explorer: "Results explorer ↗",
        github: "GitHub repo ↗",
        run: "Run it yourself",
        hackathon: "Built for the Meta Global AI Developer Hackathon 2026.",
        builtBy: "Built by DappGo",
        source: "GitHub repo",
        top: "Back to top ↑"
      }
    },
    zh: {
      metaTitle: "財經貼文查核：用 SEC 申報文件驗證數字 · DappGo",
      metaDescription: "貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。 保留文字測試：90.2% (240/266)；誤判為「支持」1/139。使用修正後參考答案。",
      metaImageAlt: "財經貼文查核示範：對照貼文與已保存的 SEC 申報文件，旁邊是查核機器人。",
      a11y: {
        skip: "跳到主要內容",
        home: "財經說法查核首頁",
        nav: "主要導覽",
        language: "語言",
        exampleLanguage: "範例語言",
        chart: "準確率比較圖"
      },
      nav: { how: "運作方式", example: "實際查核", results: "結果", trust: "為什麼可信" },
      hero: {
        titleLine1: "貼上一則財經貼文。",
        titleLine2: "看看哪些數字是真的。",
        lede: "每個查過的數字，都連到證明它的 SEC 申報文件。"
      },
      stamps: {
        region: "真實財經說法通過查核，蓋上正確、錯誤或無法查核的印章。",
        gate: "Muse Spark 代理 + SEC 查核",
        claims: "說法與報告判定",
        postPanel: "① 待查核貼文", filingPanel: "② SEC 財報", progress: "查核進度",
        waiting: "等待財報", noNumber: "沒有可查核的 SEC 數字", claim: "說法",
        noNumberExplanation: "此看法或預測沒有對應的已申報數字。",
        revenue: "營收",
        caption: { read: "正在讀貼文⋯", reach: (form) => `正在打開 ${form}⋯`,
          find: (value) => `找到了：${value}`, compare: (filed, posted) => `財報 ${filed} vs 貼文 ${posted}`, fullYear: "那是全年數字",
          uncheckable: (kind) => `${kind} — 不在任何財報中` },
        noClaim: "看法／預測 — 沒有財報數字", stamp: "蓋章", next: "接下來：",
        thread: "討論串",
        social: "社群貼文",
        repost: "轉貼", article: "新聞報導", example: "示範貼文", repostedFrom: "轉貼自",
        input: { text: "文字", screenshot: "截圖", audio: "音訊", video: "影片" },
        activity: { label: "示範互動", reply: "回覆", repost: "轉貼", like: "喜歡", views: "瀏覽" },
        audience: "公開", transcript: "逐字稿", by: "作者", speaker: "說話者", turn: "ASR 話輪",
        release: "財報新聞稿", releaseStatus: "提供資料 · 未經審計 · L4",
        rangeMatch: "指引區間的兩個端點均吻合",
        releaseMatch: "數字與期間均吻合",
        exampleDetail: "作者與追蹤人數為虛構示範；說法與判定來自真實程式查核。",
        pause: "暫停",
        play: "播放",
        true: "正確",
        false: "錯誤",
        unknown: "無法查核",
        filed: "財報", accuracy: "準確分數", within: "在容許誤差內", off: "偏差", short: "未達門檻",
        direction: "方向錯誤", millions: "單位：百萬美元", filingUnits: "依財報原始單位",
        stated: "貼文說", growth: "成長率", accession: "申報編號", nineMonths: "前九個月", quarter: "第 4 季（推算）",
        severity: { exact: "吻合", minor: "輕微", moderate: "中度", major: "重大", severe: "嚴重" }
      },
      example: {
        title: "看一則真的貼文。",
        english: "英文貼文",
        chinese: "中文貼文",
        postLabel: "貼文",
        loading: "正在載入報告⋯",
        unavailable: "目前無法顯示報告。",
        claimCount: (count) => `找出 ${count} 個說法`
      },
      verdict: { true: "正確", false: "錯誤", unknown: "無法查核" },
      claimKind: { reported_fact: "財務說法", forecast: "預測", opinion: "看法", guidance: "業績指引", non_gaap: "非 GAAP" },
      claimSource: {
        sec: "SEC 顯示",
        filed: "申報日期",
        see: "查看申報文件",
        derived: "SEC 查核",
        notChecked: "此說法沒有可比對的已申報數字。",
        noSource: "報告沒有回傳申報數字。"
      },
      filing: {
        title: "申報文件段落",
        close: "關閉申報文件段落",
        passage: "申報文件中的數字",
        sourceFacts: "來源事實",
        claimSaid: "說法內容",
        filingSays: "財報寫",
        filingShort: "財報",
        summaryPost: "貼文說",
        thisPeriod: "本期",
        comparisonPeriod: "比較期",
        company: "公司",
        formDate: "表格＋申報日期",
        period: "期間",
        concept: "XBRL 概念",
        inMillions: "百萬美元",
        inThousands: "千美元",
        inBillions: "十億美元",
        reportedUnits: (power) => `10^${power} 單位`,
        notAvailable: "無法取得",
        notEnoughForChange: "沒有足夠的相符期間",
        noPassage: "在選定的申報文件中找不到相符段落。",
        reason: "原因",
        original: "在原始申報文件中打開這個數字",
        primary: "打開主要申報文件",
        inline: "在 SEC inline viewer 中打開",
        noLink: "這項事實沒有提供 SEC 連結。",
        component: (id) => id ? `證據 ${id}` : "證據",
        table: "申報文件表格",
        text: "申報文件文字"
      },
      how: {
        title: "怎麼運作",
        lede: "從社群貼文走到可打開的來源，只有三步。",
        step1: {
          title: "找出說法",
          body: "AI 使用 Meta 的 Muse Spark 模型，找出貼文裡每個數字、期間和比較。"
        },
        step2: {
          title: "打開財報",
          body: "它查找同一家公司、數字和期間的 SEC 申報文件。"
        },
        step3: {
          title: "程式判定",
          body: "由程式，不是 AI，比對數字，最後給出正確、錯誤或無法查核。"
        }
      },
      capabilities: {
        title: "能查核哪些內容", report: "查核紀錄", replay: "重播範例",
        xbrl: { title: "SEC XBRL · L1–L3", limit: "核對已申報數字與期間；標籤差異與重編可能限制證據。" },
        release: { title: "財報新聞稿 · L4", limit: "業績指引與非 GAAP；提供資料、未經審計。32 個開發測試案例，非獨立測試。" },
        screenshot: { title: "截圖", limit: "OCR 文字交由 SEC 查核；擷取可能遺失語境。使用自製測試圖片。" },
        audio: { title: "音訊／影片", limit: "ASR 話輪與 3 個抽樣畫面；說話者未驗證。影片已知有期間遺失錯誤。" }
      },
      results: {
        title: "有效嗎？",
        lede: "加上 SEC 查找和簡單檢查後，Muse 的三種執行方式都更準。",
        caption: (count) => count ? `以 ${count} 個有已知答案的說法測試。` : "以有已知答案的評估說法測試。",
        without: "不查文件",
        withChecks: "查 SEC + 檢查",
        change: (points) => `增加 ${points} 個百分點`
      },
      posthoc: {
        title: "修正後重跑（事後）",
        key: "僅 Agent · v2 → 重跑",
        provider: "執行方式",
        accuracy: "準確率",
        falseSupported: "把錯的判成正確",
        note: "這兩個修正是看到錯誤後才做的，所以這是回歸檢查，不是新的測試成績。準確率變化在誤差內；把錯的判成正確降到零。",
        report: "重跑報告"
      },
      research: {
        summary: "研究者資料",
        ci: "95% 區間",
        paired: "配對測試",
        costLatency: "每個說法的平均成本與時間",
        weakSpots: "各類型較弱的地方",
        familyLabels: {
          record_first: "首次創高說法",
          yoy: "年增減說法",
          period_trap: "財年與曆年期間"
        },
        goldCorrections: [
          "Amazon 的 12 個月 10-Q 數字是過去 12 個月資料，不是財年資料。",
          "Apple 截至 2023-07-01 的 52／53 週季度，屬於曆年第二季，不是第三季。"
        ]
      },
      trust: {
        title: "為什麼可信",
        lede: "來源和規則都看得到。",
        item1: "每個答案都連到申報文件。",
        item2: "AI 不能改動它引用的數字。引用一變，系統就拒絕。",
        item3: "我們公開自己的錯誤，放在"
      },
      footer: {
        title: "自己跑一次查核。",
        lede: "查看結果、打開來源，或對自己的貼文執行同一個指令。",
        explorer: "結果瀏覽器 ↗",
        github: "GitHub 程式庫 ↗",
        run: "自己執行",
        hackathon: "為 Meta Global AI Developer Hackathon 2026 打造。",
        builtBy: "由 DappGo 打造",
        source: "GitHub 程式庫",
        top: "回到頂端 ↑"
      }
    }
  };

  COPY.en.nav.live = "Live check";
  COPY.zh.nav.live = "即時查核";
  COPY.en.live = {
    cta: "Try a live check →",
    title: "Try a live check.",
    scope: "US equities · SEC financial facts only. No prices, forecasts, crypto or investment advice.",
    input: "Paste a financial sentence or short post", submit: "Check against SEC", useExample: "Use Apple example",
    password: "Live-check password",
    passwordNote: "Judges: the password is our team name; saved examples need none.",
    privacy: "Text goes to Baseten for this check; we do not save it. Anonymous rate counters expire after 10 minutes. 5 checks / 10 min.",
    recordedTitle: "Saved checks",
    savedPost: "Saved check · viral post · 28 Oct 2026", savedClaim: "Saved check · one claim",
    recordedNote: "Saved run · 28 Oct 2026 · actual model calls and SEC evidence. Available even when the live budget runs out.",
    loading: "Loading the recorded trace…", loadingFailed: "The saved trace could not load. Try refreshing the page.",
    pending: "Muse Spark is choosing tools and checking SEC facts… 6–90 s by provider.", complete: "Check complete. The program verdict and trace are below.",
    recorded: "Recorded run", live: "Live check", mock: "Offline replay · saved result for the Apple example only",
    claims: "Program checks", evidence: "SEC evidence", trace: "Agent trace", model: "Model step", tool_call: "Tool call",
    tool_result: "Tool result", program_check: "Program check", program_binding: "Program evidence binding", verdict: "Program verdict", raw: "Inspect data",
    supported: "Supported", contradicted: "Contradicted", insufficient_evidence: "Insufficient evidence", unchecked: "Unchecked",
    actual: "Filed / computed", stated: "Stated", tolerance: "Tolerance", period: "Period", strength: "Evidence strength",
    notRecorded: "Timestamp not recorded", noEvidence: "No matching SEC fact returned.", filing: "Open SEC filing", source: "Original recorded trace",
    timing: "Run start/end and model-call durations are recorded. Individual tool/check timestamps were not recorded.",
    honesty: "Meta Muse Spark selects tools and proposes claims. Python checks numbers, periods and evidence IDs. A supported verdict applies only to the assertions extracted; extraction can miss an assertion. Filed evidence can be incomplete or restated. SEC data may be cached for six hours.",
    bound: "Conservative cost bound", cost: "Model cost", seconds: "s", low: "low", medium: "medium", high: "high",
    savedExamples: "See the saved examples ↓",
    correctedDraft: "Corrected draft — only listed assertions checked",
    correctionScope: "Only the assertions listed below were checked; nothing else in the text was verified.",
    correctionChanges: "Cited changes", notCorrected: "Not corrected",
    traceSteps: (count) => `Agent trace (${count} steps)`,
    derivedQuarter: "Filed quarter = annual − nine months",
    fiscalAnnual: (year) => `fiscal ${year} (annual)`, fiscalQuarter: (year, quarter) => `fiscal Q${quarter} ${year}`,
    calendarAnnual: (year) => `calendar ${year} (annual)`, calendarQuarter: (year, quarter) => `calendar Q${quarter} ${year}`,
    monthsTo: (months, date) => `${["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"][months]} months to ${date}`,
    ended: (date) => `period ending ${date}`, unknownPeriod: "Period not recorded",
    annualComparison: (year, base) => `fiscal ${year} vs ${base}`,
    metrics: { revenue: "revenue", net_income: "net income", operating_income: "operating income", eps: "EPS" },
    growth: "growth",
    budget: {
      providerRemaining: "Today {daily} of {dailyLimit} · lifetime {lifetime} of {lifetimeLimit} left",
      dailyStop: "Paused · daily limit · resets 00:00 UTC", lifetimeStop: "Paused · lifetime cap", creditStop: "Paused · credit stop",
      loading: "Loading budget…", unavailable: "Budget unavailable. See saved examples.",
      mock: "Offline replay budget · no spending",
      budget_exhausted: "Daily limit reached. Resets {reset} (00:00 UTC).",
      total_budget_exhausted: "This provider is paused (lifetime cap). See the saved examples.",
      credit_exhausted: "This provider is paused (credit stop). See the saved examples."
    },
    errors: {
      invalid_input: "Enter 1–600 characters.", out_of_scope: "This check covers US equities and SEC financial facts only.",
      unauthorized: "Enter the live-check password to continue.",
      locked: "Too many incorrect passwords. Locked for 30 minutes.",
      busy: "The server is busy. Please try again shortly.",
      slow_down: "Too many requests. Please wait 10 minutes.",
      auth_rate_limited: "Too many incorrect passwords. {reset} The saved demo is available below.",
      budget_exhausted: "Today's budget is used up — see the saved examples. Resets 00:00 UTC.",
      total_budget_exhausted: "This provider is paused (lifetime cap). See the saved examples.",
      credit_exhausted: "This provider is paused (credit stop). See the saved examples.",
      rate_limited: "5 checks / 10 min per IP, including a shared office IP. {reset} The saved demo is available below.",
      unavailable: "Live checking is unavailable. Follow the saved demo below.", timeout: "The check reached its time limit, usually because the model provider is slow or overloaded. No verdict was issued. Try another provider, or retry in a few minutes.",
      provider_error: "The model service did not complete this check. No verdict was issued. The saved demo is below.",
      provider_overloaded: "The model provider is overloaded right now (it answered \u201cservice overloaded\u201d). No verdict was issued. Try another provider, or retry in a few minutes.",
      sec_unavailable: "SEC data is unavailable right now. No verdict was issued. The saved demo is below.",
      mock_input_only: "Offline mode replays the saved viral post or one-claim example only. Choose “Use Apple example”.",
      invalid_model_output: "The model did not return a complete claim report. No verdict was issued. The saved demo is below.",
      incomplete_model: "The model response was incomplete. No verdict was issued. The saved demo is below.",
      tool_limit: "This post exceeded the short-check limit. Try one sentence about one US issuer."
    }
  };
  COPY.zh.live = {
    cta: "試試即時查核 →",
    title: "試試即時查核。",
    scope: "限美股 SEC 財務事實。不查股價、預測、加密貨幣，也不提供投資建議。",
    input: "貼上一句財務敘述或短貼文", submit: "比對 SEC 資料", useExample: "使用 Apple 範例",
    password: "即時查核密碼",
    passwordNote: "評審：密碼是我們的隊名；已儲存範例免密碼。",
    privacy: "文字會傳至 Baseten 進行查核；本站不儲存文字。匿名限流計數於 10 分鐘後刪除。每 10 分鐘限 5 次。",
    recordedTitle: "已儲存的查核",
    savedPost: "已儲存查核 · 熱傳貼文 · 2026 年 10 月 28 日", savedClaim: "已儲存查核 · 單一主張",
    recordedNote: "已儲存紀錄 · 2026 年 10 月 28 日 · 真實模型呼叫與 SEC 證據。即時預算用完仍可查看。",
    loading: "正在讀取查核紀錄…", loadingFailed: "無法讀取查核紀錄，請重新整理頁面。",
    pending: "Muse Spark 正在選擇工具並比對 SEC 事實… 依供應商約需 6–90 秒。", complete: "查核完成。以下是程式裁定與執行過程。",
    recorded: "已儲存的執行紀錄", live: "即時查核", mock: "離線重播 · 僅回放已儲存的 Apple 範例",
    claims: "程式檢查", evidence: "SEC 證據", trace: "代理執行過程", model: "模型步驟", tool_call: "工具呼叫",
    tool_result: "工具回傳", program_check: "程式檢查", program_binding: "程式證據綁定", verdict: "程式裁定", raw: "檢視資料",
    supported: "證據支持", contradicted: "證據矛盾", insufficient_evidence: "證據不足", unchecked: "未能檢查",
    actual: "申報／計算值", stated: "貼文數字", tolerance: "容許誤差", period: "期間", strength: "證據強度",
    notRecorded: "未記錄時間戳", noEvidence: "未取得符合的 SEC 事實。", filing: "開啟 SEC 申報", source: "原始執行紀錄",
    timing: "已記錄整次開始／結束時間及各次模型耗時；未記錄個別工具／程式檢查的時間戳。",
    honesty: "Meta Muse Spark 選擇工具並提出待查敘述；Python 檢查數字、期間與證據 ID。支持裁定僅適用於抽取到的敘述，抽取仍可能遺漏。申報證據可能不完整或經重編。SEC 資料可能快取六小時。",
    bound: "保守費用上限", cost: "模型費用", seconds: "秒", low: "低", medium: "中", high: "高",
    savedExamples: "查看已儲存的範例 ↓",
    correctedDraft: "修正版草稿——僅核對列出的主張",
    correctionScope: "僅核對下方列出的主張；文中其餘內容均未經查證。",
    correctionChanges: "修改與引用來源", notCorrected: "未修正",
    traceSteps: (count) => `代理執行過程（${count} 個步驟）`,
    derivedQuarter: "申報季度 = 全年 − 前九個月",
    fiscalAnnual: (year) => `${year} 財年（全年）`, fiscalQuarter: (year, quarter) => `${year} 財年第 ${quarter} 季`,
    calendarAnnual: (year) => `${year} 曆年（全年）`, calendarQuarter: (year, quarter) => `${year} 曆年第 ${quarter} 季`,
    monthsTo: (months, date) => `截至 ${date}的 ${months} 個月`,
    ended: (date) => `截至 ${date} 的期間`, unknownPeriod: "未記錄期間",
    annualComparison: (year, base) => `${year} 對 ${base} 財年`,
    metrics: { revenue: "營收", net_income: "淨利", operating_income: "營業利益", eps: "每股盈餘" },
    growth: "成長",
    budget: {
      providerRemaining: "今日剩 {daily}／{dailyLimit} · 累計剩 {lifetime}／{lifetimeLimit}",
      dailyStop: "暫停 · 每日上限 · UTC 00:00 重設", lifetimeStop: "暫停 · 累計上限", creditStop: "暫停 · 額度用完",
      loading: "正在讀取預算…", unavailable: "預算暫時無法讀取。請查看已儲存範例。",
      mock: "離線重播預算 · 不產生費用",
      budget_exhausted: "已達每日上限，於 {reset}（UTC 00:00）重設。",
      total_budget_exhausted: "此供應商暫停（累計預算已用完）。請查看已儲存的範例。",
      credit_exhausted: "此供應商暫停（額度已用完）。請查看已儲存的範例。"
    },
    errors: {
      invalid_input: "請輸入 1–600 個字元。", out_of_scope: "此功能僅查核美股的 SEC 財務事實。",
      unauthorized: "請輸入即時查核密碼以繼續。",
      locked: "密碼錯誤次數過多，已鎖定 30 分鐘。",
      busy: "伺服器忙碌中，請稍後再試。",
      slow_down: "請求過於頻繁，請等候 10 分鐘。",
      auth_rate_limited: "密碼錯誤次數過多。{reset} 下方示範仍可查看。",
      budget_exhausted: "今日預算已用完，請查看已儲存的範例。於 UTC 00:00 重設。",
      total_budget_exhausted: "此供應商暫停（累計預算已用完）。請查看已儲存的範例。",
      credit_exhausted: "此供應商暫停（額度已用完）。請查看已儲存的範例。",
      rate_limited: "每個 IP 每 10 分鐘限 5 次，共用辦公室 IP 也共用此額度。{reset} 下方示範仍可查看。",
      unavailable: "即時查核暫時無法使用。請查看下方已儲存的示範。", timeout: "查核已達時間上限，通常是模型供應商回應緩慢或過載，未作出裁定。請改用其他供應商，或幾分鐘後再試。",
      provider_error: "模型服務未完成查核，未作出裁定。請查看下方示範。", provider_overloaded: "模型供應商目前過載（回應「service overloaded」），未作出裁定。請改用其他供應商，或幾分鐘後再試。", sec_unavailable: "SEC 資料暫時無法取得，未作出裁定。請查看下方示範。",
      mock_input_only: "離線模式僅重播已儲存的熱傳貼文或單一主張範例，請選擇「使用 Apple 範例」。",
      invalid_model_output: "模型未回傳完整報告，未作出裁定。請查看下方示範。", incomplete_model: "模型回應不完整，未作出裁定。請查看下方示範。",
      tool_limit: "此貼文超過簡短查核上限，請改用一家美股公司的一句敘述。"
    }
  };

  // Product copy, simplified for review round 2 (2026-11-03).
  COPY.en.facts = {
  "title": "Facts",
  "caption": "Eight answers about the verifier",
  "question": "Question",
  "answer": "Answer",
  "question1": "What it does",
  "answer1": "Checks financial claims against SEC filings; returns verdicts and cited corrections.",
  "question2": "Time span",
  "answer2": "SEC XBRL periods, generally 2009 onward, through the latest filing.",
  "question3": "Which US stocks",
  "answer3": "US-GAAP SEC filers: ≈8,000 companies; 23 tested.",
  "question4": "Inputs",
  "answer4": "Website: text ≤600 characters. CLI: text, images, PDFs, audio and video.",
  "question5": "Price",
  "answer5": "$0.01 per live check; $0.02 per claim in the benchmark.",
  "question6": "Speed",
  "answer6": "6 s live (one recorded production claim); 10 s median in the benchmark.",
  "question7": "Accuracy",
  "answer7": "90.2% (240/266) held out; false support 1/139.",
  "question8": "Fix the article?",
  "answer8": "Corrects disproved numbers and cites the filing."
};
  COPY.en.metaDescription = "Paste a finance post. Every number is checked against SEC filings, and you get a corrected draft with citations. Held-out text: 90.2% (240/266); false support 1/139. Corrected gold.";
  COPY.en.workflow = {
  "label": "How it works",
  "paste": "Paste",
  "evidence": "Muse finds SEC evidence",
  "decide": "Python decides + corrected draft"
};
  COPY.en.draft = {
  "title": "Corrected draft",
  "rule": "A corrected draft replaces disproved numbers with filed values and cites the filing.",
};
  COPY.en.evidence = {
  "title": "Evidence",
  "benchmark": "Original held-out text benchmark",
  "accuracy": "Accuracy",
  "falseSupport": "False support",
  "cost": "Mean / claim",
  "speed": "Median / claim",
  "seconds": "s",
  "benchmarkNote": "Corrected gold; failures count as wrong.",
  "report": "Read the benchmark and limits",
  "realworld": "Real-world coverage",
  "coverage": "Coverage ≠ accuracy; rechecks are post-hoc.",
  "wild": "Read the real-world study",
  "wildNav": "In the wild",
  "links": "Evidence links",
  "index": "Evidence index",
  "tour": "Saved demos and methodology",
  "origin": "DappGo publishes US-market commentary. An internal fact check found posts with the right number but the wrong period, unit or comparison. The model proposes, the program decides.",
  "earlier": "Earlier anchors →",
  "stamps": "Stamp walkthrough"
};
  Object.assign(COPY.en.nav, {"try": "Try", "facts": "Facts", "evidence": "Evidence"});
  Object.assign(COPY.en.hero, {"lede": "Every number is checked against SEC filings, and you get a corrected draft with citations.", "saved": "See a saved check (no password)"});
  Object.assign(COPY.en.live, {"title": "Try", "cta": "Try live check"});
  Object.assign(COPY.en.footer, {"explorer": "Results explorer", "disclosure": "DappGo existed before; this verifier, site and evidence were built during the hackathon, from 27 Oct 2026.", "legal": "Project credits", "build": "Build disclosure", "license": "MIT license", "credits": "Credits"});
  COPY.zh.facts = {
  "title": "產品事實",
  "caption": "關於查核器的八個答案",
  "question": "問題",
  "answer": "答案",
  "question1": "功能",
  "answer1": "用 SEC 申報核對財務主張，提供判定與附出處的修正。",
  "question2": "可查期間",
  "answer2": "SEC XBRL 申報期間，大致自 2009 年起至最新申報。",
  "question3": "支援哪些美股",
  "answer3": "US-GAAP 美股申報公司：約 8,000 家，已測試 23 家。",
  "question4": "輸入格式",
  "answer4": "網站：≤600 字元。CLI：文字、圖片、PDF、音訊與影片。",
  "question5": "費用",
  "answer5": "即時查核每次 $0.01；基準測試每題 $0.02。",
  "question6": "速度",
  "answer6": "即時 6 秒（單一正式環境主張紀錄）；基準測試中位數 10 秒。",
  "question7": "準確率",
  "answer7": "保留測試 90.2% (240/266)；誤判為支持 1/139。",
  "question8": "能修正文章嗎？",
  "answer8": "修正被證明錯誤的數字，並附申報出處。"
};
  COPY.zh.metaDescription = "貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。 保留文字測試：90.2% (240/266)；誤判為「支持」1/139。使用修正後參考答案。";
  COPY.zh.workflow = {
  "label": "查核流程",
  "paste": "貼上貼文",
  "evidence": "Muse 尋找 SEC 證據",
  "decide": "Python 判定並產出修正版草稿"
};
  COPY.zh.draft = {
  "title": "修正版草稿",
  "rule": "修正版草稿只將被證明錯誤的數字換成申報值，並附出處。",
};
  COPY.zh.evidence = {
  "title": "證據",
  "benchmark": "原始保留文字測試",
  "accuracy": "準確率",
  "falseSupport": "誤判為支持",
  "cost": "每題平均費用",
  "speed": "每題中位時間",
  "seconds": "秒",
  "benchmarkNote": "採用修正後參考答案；失敗計為錯誤。",
  "report": "閱讀基準測試與限制",
  "realworld": "真實貼文涵蓋率",
  "coverage": "涵蓋率 ≠ 準確率；事後重查未重測 OCR／ASR。",
  "wild": "閱讀真實貼文研究",
  "wildNav": "真實貼文",
  "links": "證據連結",
  "index": "證據索引",
  "tour": "已儲存展示與方法",
  "origin": "DappGo 發布美股評論。內部事實查核發現，數字正確也可能配錯期間、單位或比較方式。模型提出，程式判定。",
  "earlier": "Earlier anchors →",
  "stamps": "印章查核導覽"
};
  Object.assign(COPY.zh.nav, {"try": "試用", "facts": "事實", "evidence": "證據"});
  Object.assign(COPY.zh.hero, {"titleLine1": "貼上財經貼文，逐一用 SEC 申報資料核對數字，並產出附出處的修正版草稿。", "lede": "", "saved": "查看已儲存查核（免密碼）"});
  Object.assign(COPY.zh.live, {"title": "試用", "cta": "試試即時查核"});
  Object.assign(COPY.zh.footer, {"explorer": "結果瀏覽器", "disclosure": "DappGo 在黑客松前已存在；此查核器、網站與證據從 2026 年 10 月 27 日起於黑客松期間建立。", "legal": "專案出處", "build": "建置揭露", "license": "MIT 授權", "credits": "出處與致謝"});

  COPY.en.examples = {
    title: "One post, five ways in", note: "Our own example post. Run a fresh check with the password, or read a saved result without one.",
    textTitle: "Text", imageTitle: "Image", pdfTitle: "PDF", audioTitle: "Audio", videoTitle: "Video",
    text: "Big Tech post; wrong Apple quarter.",
    image: "Muse reads this screenshot.", pdf: "One page of selectable text.",
    audio: "Breeze voice; Muse transcription.",
    video: "Muse reads frames and narration.",
    run: "Run live", saved: "See saved result", savedPending: "Saved result pending", reused: "Saved text run · 28 Oct 2026",
    savedReady: "Saved result available · no password", pendingDetails: "Recording status", openMedia: "Play the file",
    openText: "Read the full post", openImage: "Open the image", openPdf: "Open the PDF", nativeText: "1 page · native text",
    imageAlt: "Screenshot of our example Big Tech post", videoAlt: "Preview of the example video still",
    loading: "Loading the saved example…",
    privacy: "Example images and audio go to the Meta Model API for reading; the extracted text goes to Baseten for SEC checks. 5 checks / 10 min; separate provider budgets.",
  };
  COPY.zh.examples = {
    title: "同一篇貼文，五種輸入", note: "使用我們自製的範例貼文。輸入密碼即可即時查核；查看已儲存結果不需密碼。",
    textTitle: "文字", imageTitle: "圖片", pdfTitle: "PDF", audioTitle: "音訊", videoTitle: "影片",
    text: "科技股貼文，含 Apple 季度錯誤。", image: "Muse 讀取貼文截圖。",
    pdf: "單頁 PDF，可直接擷取文字。", audio: "Breeze 旁白，由 Muse 轉錄。",
    video: "Muse 讀取影格與旁白。",
    run: "即時查核", saved: "查看已儲存結果", savedPending: "已儲存結果待補", reused: "文字查核紀錄 · 2026 年 10 月 28 日",
    savedReady: "可查看已儲存結果 · 免密碼", pendingDetails: "製作狀態", openMedia: "播放檔案",
    openText: "閱讀完整貼文", openImage: "開啟圖片", openPdf: "開啟 PDF", nativeText: "1 頁 · 原生文字",
    imageAlt: "自製科技股範例貼文截圖", videoAlt: "範例影片的靜態預覽",
    loading: "正在讀取已儲存範例…",
    privacy: "範例圖片與音訊由 Meta Model API 讀取，再將擷取文字交給 Baseten 核對 SEC。每 10 分鐘限 5 次，共用每日預算。",
  };
  Object.assign(COPY.en.live, { read: "What the model read", preprocessing: "Input reading", local: "Local text extraction",
    preprocessingEvent: "Read input", mock: "Offline replay · saved example", inputTiming: "Input reading time not recorded",
    mediaPending: "Muse is reading the example, then checking SEC facts…", recordedTiming: "Timing details belong to this recorded request; see its source record." });
  Object.assign(COPY.zh.live, { read: "模型讀到了什麼", preprocessing: "輸入讀取", local: "本機文字擷取",
    preprocessingEvent: "讀取輸入", mock: "離線重播 · 已儲存範例", inputTiming: "未記錄輸入讀取耗時",
    mediaPending: "Muse 正在讀取範例，接著核對 SEC 財務事實…", recordedTiming: "耗時資訊屬於此筆執行紀錄，詳見原始紀錄。" });
  Object.assign(COPY.en.live.errors, { unknown_example: "This example is not available.", example_unavailable: "This example file is still being prepared. See its saved-result status.",
    preprocessing_failed: "Reading the input did not finish. No complete check was issued.", saved_result_pending: "Saved result pending" });
  Object.assign(COPY.zh.live.errors, { unknown_example: "無此範例。", example_unavailable: "此範例檔案仍在製作中，請查看已儲存結果狀態。",
    preprocessing_failed: "輸入讀取未完成，未產出完整查核。", saved_result_pending: "已儲存結果待補" });
  Object.assign(COPY.en.live, { rateReset: "Resets {time}.", rateResetUnknown: "Reset time unavailable." });
  Object.assign(COPY.zh.live, { rateReset: "重設時間：{time}。", rateResetUnknown: "目前無法取得重設時間。" });

  COPY.en.matrix = {
    intro: "Three stories. Five inputs. Follow each number to the filing.",
    story: "1 · Choose a story", kind: "2 · Choose an input", provider: "3 · Choose a provider", inputType: "Input type",
    storyA: "A · Wrong period", storyB: "B · All correct", storyC: "C · Mixed",
    expected: "Expected outcome", expectedA: "Contradicted · $416.2B → $102.5B", expectedB: "Supported · nothing to correct",
    expectedC: "Contradicted · $164,501B → $164.5B · forecast and opinion not judged", reset: "Reset example", openInput: "Open input file",
    fireworksNote: "Fireworks responses are slow today (provider-side); Baseten is fastest.",
    historyErrors: { provider_error: "Provider error", provider_overloaded: "Provider overloaded", timeout: "Timeout", budget_exhausted: "Budget", total_budget_exhausted: "Budget",
      credit_exhausted: "Credit limit", rate_limited: "Rate limit", busy: "Server busy", locked: "Locked", slow_down: "Too many requests", sec_unavailable: "SEC unavailable", preprocessing_failed: "Input error",
      invalid_model_output: "Invalid response", incomplete_model: "Incomplete", tool_limit: "Tool limit", unavailable: "Unavailable", unknown: "Failed" },
    compareAll: "Compare on all", compareNote: "Sequential runs · separate provider budgets", run: "Run check", runCompare: "Compare providers",
    privacy: "Authenticated runs and their input text are public in history for 14 days. OCR/ASR uses the Meta Model API; SEC checks use your chosen provider. 5 checks / 10 min per IP; a shared office IP shares this limit. A rate-limited request shows the reset time.",
    history: "Recent checks", historyNote: "Last 50 runs · public · retained for 14 days", refresh: "Refresh", historyLoading: "Loading history…",
    historyEmpty: "No checks yet.", historyUnavailable: "History is unavailable. Try Refresh.", historyOpening: "Opening the saved check…",
    historyDialog: "Saved check", historyInput: "Input text", historyClose: "Close",
    historyFailed: "This check could not be opened. Try again.", whenDevice: "Time / device", storyKind: "Story / input",
    providerVerdict: "Provider / verdict", timeCost: "Duration / cost", custom: "Custom text", edit: "Edit & re-run",
    assetPending: "Example asset pending", assetsLoading: "Loading examples…", assetsFailed: "Examples could not be loaded. Reload to try again.", textLoading: "Loading example text…", textFailed: "Example text could not be loaded. Try Reset example.",
    comparing: "Running providers in sequence, each with its own budget…", comparison: "Provider comparison", openResult: "Open full result",
    corrections: "Corrections", duration: "Duration", cost: "Verifier cost", prepCost: "Input reading cost", receipt: "Run receipt", verifier: "Verifier",
    noPreprocessing: "No preprocessing", nothingToCorrect: "Nothing to correct in the checked claims.", notJudged: "Not judged", notRun: "Not run",
    noScript: "Enable JavaScript to choose an input or read live history. The recorded text result is also available below."
  };
  COPY.zh.matrix = {
    intro: "三個故事，五種輸入；每個數字都能追溯到申報文件。",
    story: "1 · 選擇故事", kind: "2 · 選擇輸入", provider: "3 · 選擇供應商", inputType: "輸入格式",
    storyA: "A · 期間錯誤", storyB: "B · 全部正確", storyC: "C · 混合主張",
    expected: "預期結果", expectedA: "證據矛盾 · $416.2B → $102.5B", expectedB: "證據支持 · 無需修正",
    expectedC: "證據矛盾 · $164,501B → $164.5B · 預測與意見不予判定", reset: "重設範例", openInput: "開啟輸入檔案",
    fireworksNote: "Fireworks 今日回應較慢（供應商端）；Baseten 最快。",
    historyErrors: { provider_error: "供應商錯誤", provider_overloaded: "供應商過載", timeout: "逾時", budget_exhausted: "預算上限", total_budget_exhausted: "預算上限",
      credit_exhausted: "額度上限", rate_limited: "頻率上限", busy: "伺服器忙碌", locked: "已鎖定", slow_down: "請求過於頻繁", sec_unavailable: "SEC 暫不可用", preprocessing_failed: "輸入錯誤",
      invalid_model_output: "回應無效", incomplete_model: "回應不完整", tool_limit: "工具次數上限", unavailable: "暫不可用", unknown: "失敗" },
    compareAll: "比較全部供應商", compareNote: "依序執行 · 各供應商獨立預算", run: "執行查核", runCompare: "比較供應商",
    privacy: "通過密碼驗證的查核與輸入文字會公開於歷史紀錄，保留 14 天。OCR／ASR 使用 Meta Model API；SEC 查核使用所選供應商。每個 IP 每 10 分鐘限 5 次；共用辦公室 IP 也共用此額度。達到限制時會顯示重設時間。",
    history: "最近查核", historyNote: "最近 50 次 · 公開 · 保留 14 天", refresh: "重新整理", historyLoading: "正在讀取歷史紀錄…",
    historyEmpty: "尚無查核紀錄。", historyUnavailable: "無法讀取歷史紀錄，請重新整理。", historyOpening: "正在開啟已儲存查核…",
    historyDialog: "已儲存查核", historyInput: "輸入文字", historyClose: "關閉",
    historyFailed: "無法開啟此筆查核，請再試一次。", whenDevice: "時間／裝置", storyKind: "故事／輸入",
    providerVerdict: "供應商／判定", timeCost: "耗時／費用", custom: "自訂文字", edit: "編輯並重新查核",
    assetPending: "範例檔案待補", assetsLoading: "正在讀取範例…", assetsFailed: "無法讀取範例，請重新載入。", textLoading: "正在讀取範例文字…", textFailed: "無法讀取範例文字，請重設範例。",
    comparing: "正依序執行各供應商；各自使用獨立預算…", comparison: "供應商比較", openResult: "開啟完整結果",
    corrections: "修正數", duration: "耗時", cost: "查核費用", prepCost: "輸入讀取費用", receipt: "執行收據", verifier: "查核",
    noPreprocessing: "無前處理", nothingToCorrect: "已核對的主張無需修正。", notJudged: "不予判定", notRun: "未執行",
    noScript: "請啟用 JavaScript 以選擇輸入或讀取即時歷史紀錄。下方也提供已儲存的文字查核。"
  };
  COPY.en.live.privacy = COPY.en.matrix.privacy;
  COPY.zh.live.privacy = COPY.zh.matrix.privacy;
  COPY.en.examples.privacy = COPY.en.matrix.privacy;
  COPY.zh.examples.privacy = COPY.zh.matrix.privacy;
  COPY.en.tryUI = {
    runTitle: "Run a check", runIntro: "Pick a story and an input, or paste your own post.",
    storyA: "Wrong period", storyB: "All correct", storyC: "Mixed claims",
    storyAShort: "Wrong", storyBShort: "Correct", storyCShort: "Mixed", expected: "Expected",
    sidebar: "Current and recent checks", now: "Now", idle: "No check running.",
    idleHint: "Press Run check to watch each server step here.",
    running: "Running", checking: "Checking…", done: "Done", viewRunning: "View running check",
    stage0: "Sent", stage1: "Model", stage2: "SEC tools", stage3: "Model", stage4: "Program checks", stage5: "Verdict", stage2Short: "SEC", stage4Short: "Checks",
    stageSentences: ["Request sent to the server", "Model is reading the input", "SEC tools are checking the filings",
      "Model is reading the SEC evidence", "Program is checking the numbers", "Preparing the verdict"],
    modelStep: n => ` (step ${n})`, finished: time => `finished in ${time}`, time: "Time", cost: "Cost", claims: "Claims",
    serverLog: "Server log · this request", lines: n => `${n} lines`, log: n => `Server log (${n} lines)`,
    viewResult: "View result ↓", showMore: "Show more", you: "you", nowTime: "now",
    minutesAgo: n => `${n} min ago`, hoursAgo: n => `${n} h ago`, story: letter => `Story ${letter}`,
    daily: amount => `${amount} left today`, lifetime: (left, limit) => `lifetime ${left} of ${limit}`, providerMetaShort: "Meta"
  };
  COPY.zh.tryUI = {
    runTitle: "執行查核", runIntro: "選擇故事和輸入格式，或貼上自己的貼文。",
    storyA: "期間錯誤", storyB: "全部正確", storyC: "混合主張",
    storyAShort: "期間錯", storyBShort: "全對", storyCShort: "混合", expected: "預期",
    sidebar: "目前與最近的查核", now: "目前狀態", idle: "目前沒有執行中的查核。",
    idleHint: "按下「執行查核」，即可在這裡看到伺服器的每個步驟。",
    running: "執行中", checking: "查核中…", done: "完成", viewRunning: "查看執行中的查核",
    stage0: "已送出", stage1: "模型", stage2: "SEC 工具", stage3: "模型", stage4: "程式檢查", stage5: "判定", stage2Short: "SEC", stage4Short: "檢查",
    stageSentences: ["請求已送至伺服器", "模型正在讀取輸入內容", "SEC 工具正在核對申報文件",
      "模型正在讀取 SEC 證據", "程式正在核對數字", "正在產生判定"],
    modelStep: n => `（第 ${n} 步）`, finished: time => `用時 ${time}`, time: "用時", cost: "費用", claims: "主張",
    serverLog: "伺服器紀錄 · 本次請求", lines: n => `${n} 行`, log: n => `伺服器紀錄（${n} 行）`,
    viewResult: "查看結果 ↓", showMore: "顯示更多", you: "你", nowTime: "剛剛",
    minutesAgo: n => `${n} 分鐘前`, hoursAgo: n => `${n} 小時前`, story: letter => `故事 ${letter}`,
    daily: amount => `今日剩餘 ${amount}`, lifetime: (left, limit) => `累計額度剩餘 ${left}，上限 ${limit}`, providerMetaShort: "Meta"
  };
  Object.assign(COPY.en.matrix, { story: "Story", kind: "Input", provider: "Model provider", fireworksNote: "Slow today",
    compareAll: "Compare on all three", compareNote: "runs one after another", historyNote: "Last 50 runs · public · kept 14 days" });
  Object.assign(COPY.zh.matrix, { story: "故事", kind: "輸入", provider: "模型供應商", fireworksNote: "今日較慢",
    compareAll: "比較三家供應商", compareNote: "依序執行，各有獨立預算" });
  Object.assign(COPY.en.live, { password: "Password", passwordNote: "Password is our team name. Saved results need none." });
  Object.assign(COPY.zh.live, { password: "密碼", passwordNote: "密碼是我們的隊名。查看儲存結果不需密碼。" });
  Object.assign(COPY.en.live.errors, { invalid_provider: "Choose an available provider.", invalid_providers: "Choose available providers." });
  Object.assign(COPY.zh.live.errors, { invalid_provider: "請選擇可用的供應商。", invalid_providers: "請選擇可用的供應商。" });


  COPY.en.brand = "market claim verifier";
  COPY.zh.brand = "財經主張查核器";
  // Site presentation v2: shared static and runtime copy.
  COPY.en.facts = {
  "title": "Facts",
  "question": "Fact",
  "answer": "Recorded scope",
  "caption": "Six answers about the verifier",
  "source": "Evidence ↗",
  "label": "Fact:",
  "question1": "What it checks",
  "detail1": "The model selects SEC evidence. Python checks periods, units and values.",
  "summary1": "Cited verdicts + corrections",
  "answer1": "Checks financial claims against SEC filings; returns verdicts and cited corrections.",
  "question2": "Coverage",
  "detail2": "US-GAAP SEC XBRL periods: generally 2009 onward, through the latest filing.",
  "summary2": "≈8,000 companies · 23 tested",
  "answer2": "US-GAAP SEC filers: ≈8,000 companies; 23 tested. SEC XBRL periods, generally 2009 onward, through the latest filing.",
  "question3": "Inputs",
  "detail3": "The CLI accepts text, images, PDFs, audio and video.",
  "summary3": "Website: ≤600 characters",
  "answer3": "Website: text ≤600 characters. CLI: text, images, PDFs, audio and video.",
  "question4": "Cost & speed",
  "detail4": "Benchmark: $0.02 per claim; 10 s median. Live headline: one production claim.",
  "summary4": "$0.01 per live check · 6 s live",
  "answer4": "$0.01 per live check; 6 s live (one recorded production claim). $0.02 per claim; 10 s median in the benchmark. Separate daily and lifetime caps per provider.",
  "question5": "Accuracy",
  "detail5": "Held-out text, corrected gold. False support: 1/139; coverage ≠ accuracy.",
  "summary5": "90.2% (240/266) held out",
  "answer5": "90.2% (240/266) held out; false support 1/139.",
  "question6": "Corrections",
  "detail6": "Only disproved numbers change; the rest of the post keeps its wording.",
  "summary6": "Cited corrections; no article approval",
  "answer6": "Corrects disproved numbers and cites the filing. Never labels an article approved."
};
  COPY.en.language = {
  "en": "EN",
  "zh": "ZH"
};
  COPY.en.presentation = {
  "follow": "Follow one number",
  "followNote": "The viral post puts an annual number in a single quarter. Open each step from the saved check.",
  "saved": "Saved check · 28 Oct 2026 · Baseten",
  "claim": "Extracted claim",
  "fact": "Filed facts",
  "check": "Program check",
  "loading": "Loading the saved check…",
  "failed": "The saved check could not load. Open the retained record below.",
  "raw": "Open the saved check data",
  "claimNote": "Apple revenue · fiscal Q4 2025 · stated $416.2B",
  "annual": "Annual revenue",
  "nineMonths": "Nine-month revenue",
  "quarter": "Quarter = annual − nine months",
  "source": "Open the component filing",
  "noScript": "The saved claim, filing values and program verdict are available in the retained data.",
  "historical": "Historical results",
  "historicalNote": "All 357 claims: 91 development + 266 held out; corrected gold. This chart is historical. The held-out headline above uses 266 claims.",
  "providers": "Filter historical results by provider",
  "all": "All providers",
  "limits": "Limits & honesty",
  "limit1": "Two gold answers were corrected after the original run; registered-gold scores remain available.",
  "limit2": "The run manifest records a dirty working tree.",
  "limit3": "Post-hoc rechecks reuse seen inputs and are not a fresh held-out evaluation.",
  "limit4": "Frozen-transcript rechecks do not retest image reading or speech transcription (OCR/ASR). Extraction can miss assertions.",
  "limit5": "Each provider has daily and lifetime caps; 5 checks / 10 min per IP. Authenticated runs are public for 14 days.",
  "details": "Details",
  "privacySummary": "Authenticated runs are public in history for 14 days · 5 checks / 10 min per IP",
  "privacyDetails": "Input text is retained with each authenticated run. Images and speech use the Meta Model API; SEC checks use your chosen provider. A shared office IP shares the rate limit. Limited requests show the reset time.",
  "noscriptTrace": "The interactive trace needs JavaScript.",
  "providerBaseten": "Baseten",
  "providerFireworks": "Fireworks",
  "providerMeta": "Meta Model API",
  "today": "today",
  "yesterday": "yesterday",
  "utc": "UTC",
  "savedOn": "Recorded",
  "readmeAlt": "Auditor robot comparing a post with a filing and stamping the program verdict"
};
  COPY.zh.facts = {
  "title": "產品事實",
  "question": "項目",
  "answer": "已記錄範圍",
  "caption": "關於查核器的六個答案",
  "source": "證據 ↗",
  "label": "事實：",
  "question1": "查核內容",
  "detail1": "模型選擇申報證據，程式核對期間、單位與數值。",
  "summary1": "附出處的判定與修正",
  "answer1": "以美國證管會申報核對財務主張，提供判定與附出處的修正。",
  "question2": "涵蓋範圍",
  "detail2": "美國會計準則公司，結構化申報期間大致自 2009 年起至最新申報。",
  "summary2": "約 8,000 家 · 已測試 23 家",
  "answer2": "美國會計準則申報公司：約 8,000 家，已測試 23 家。結構化申報期間大致自 2009 年起至最新申報。",
  "question3": "輸入格式",
  "detail3": "命令列可讀文字、圖片、文字型文件、音訊與影片。",
  "summary3": "網站 ≤600 字元",
  "answer3": "網站：≤600 字元。命令列：文字、圖片、文字型文件、音訊與影片。",
  "question4": "費用與速度",
  "detail4": "基準每題 $0.02，中位數 10 秒；即時主要數字來自單一正式環境主張。",
  "summary4": "即時每次 $0.01 · 6 秒",
  "answer4": "即時查核每次 $0.01；即時 6 秒（單一正式環境主張紀錄）。基準測試每題 $0.02；中位數 10 秒。各供應商有獨立每日與累計上限。",
  "question5": "準確率",
  "detail5": "保留文字測試、修正後答案；誤判為支持 1/139，涵蓋率 ≠ 準確率。",
  "summary5": "保留測試 90.2% (240/266)",
  "answer5": "保留測試 90.2% (240/266)；誤判為支持 1/139。",
  "question6": "修正範圍",
  "detail6": "只改被證明錯誤的數字，其餘文字保留原樣。",
  "summary6": "附申報出處；不核准整篇文章",
  "answer6": "修正被證明錯誤的數字，並附申報出處。絕不標示整篇文章已核准。"
};
  COPY.zh.language = {
  "en": "英文",
  "zh": "繁中"
};
  COPY.zh.presentation = {
  "follow": "跟著一個數字查到底",
  "followNote": "熱門貼文把全年營收寫成單季營收。逐步打開這份已儲存查核。",
  "saved": "已儲存查核 · 2026-10-28 · 供應商一",
  "claim": "擷取的主張",
  "fact": "申報數值",
  "check": "程式檢查",
  "loading": "正在讀取已儲存查核…",
  "failed": "無法讀取已儲存查核，請開啟下方保留紀錄。",
  "raw": "開啟已儲存查核資料",
  "claimNote": "蘋果公司營收 · 2025 會計年度第 4 季 · 主張 $416.2B",
  "annual": "全年營收",
  "nineMonths": "前九個月營收",
  "quarter": "單季＝全年－前九個月",
  "source": "開啟組成數值的申報文件",
  "noScript": "保留資料包含擷取的主張、申報數值與程式判定。",
  "historical": "歷史測試結果",
  "historicalNote": "全部 357 題：91 題開發資料與 266 題保留測試，採修正後參考答案。此圖為歷史結果；上方準確率採 266 題保留測試。",
  "providers": "依供應商篩選歷史結果",
  "all": "全部供應商",
  "limits": "限制與誠實揭露",
  "limit1": "原始執行後修正了兩題參考答案；原先登記答案的分數仍保留。",
  "limit2": "執行清單記錄當時工作目錄有未提交的變更。",
  "limit3": "事後重查使用已看過的輸入，不是全新的保留測試。",
  "limit4": "凍結對話重查未重測圖片辨識或語音轉錄；擷取可能遺漏主張。",
  "limit5": "各供應商使用獨立的每日與累計預算；每個網路位址每 10 分鐘限 5 次。驗證後的查核公開保留 14 天。",
  "details": "詳細規則",
  "privacySummary": "驗證後查核公開保留 14 天 · 每個網路位址每 10 分鐘限 5 次",
  "privacyDetails": "通過驗證的輸入文字會隨查核保留。圖片與語音由官方模型介面讀取，申報查核使用所選供應商。共用辦公室網路也共用額度；達到限制時顯示重設時間。",
  "noscriptTrace": "互動紀錄需要啟用瀏覽器指令。",
  "providerBaseten": "Baseten",
  "providerFireworks": "Fireworks",
  "providerMeta": "Meta Model API",
  "today": "今天",
  "yesterday": "昨天",
  "utc": "世界協調時間",
  "savedOn": "記錄日期",
  "readmeAlt": "稽核機器人比對貼文與申報文件，蓋上程式判定印章"
};
  Object.assign(COPY.en.nav, { how: "How it works" });
  Object.assign(COPY.zh.nav, { how: "運作方式" });
  Object.assign(COPY.zh.a11y, { home: "財經主張查核器首頁", chart: "歷史準確率比較圖" });
  Object.assign(COPY.zh.hero, { titleLine1: "貼上財經貼文。", lede: "逐一用美國證管會申報資料核對數字，並產出附出處的修正版草稿。" });
  Object.assign(COPY.zh.workflow, { evidence: "模型尋找申報證據", decide: "程式判定並產出修正版草稿" });
  Object.assign(COPY.zh.how, { lede: "從貼文一路找到可開啟的來源。" });
  COPY.zh.how.step1.body = "模型擷取貼文中的數字、期間與比較。";
  COPY.zh.how.step2.body = "查找同一家公司、數字與期間的申報資料。";
  COPY.zh.how.step3.body = "程式核對數字，產出支持、矛盾或證據不足的判定。";
  COPY.zh.metaTitle = "財經主張查核器 · 核對貼文數字";
  COPY.zh.metaDescription = "貼上財經貼文，逐一用美國證管會申報資料核對數字，並產出附出處的修正版草稿。保留文字測試：90.2% (240/266)；誤判為支持 1/139。採修正後參考答案。";
  Object.assign(COPY.zh.footer, { source: "原始碼程式庫", license: "開放原始碼授權", builtBy: "由團隊打造", disclosure: "原有財經評論服務在黑客松前已存在；此查核器、網站與證據從 2026-10-27 起於黑客松期間建立。" });
  Object.assign(COPY.zh.evidence, { origin: "團隊發布美股評論。內部查核發現，數字正確也可能配錯期間、單位或比較方式。模型提出，程式判定。", coverage: "涵蓋率 ≠ 準確率；事後重查未重測圖片辨識與語音轉錄。" });
  Object.assign(COPY.zh.examples, { pdfTitle: "文件", image: "模型讀取貼文截圖。", pdf: "單頁文件，可直接擷取文字。", audio: "固定聲線旁白，由模型轉錄。", video: "模型讀取影格與旁白。", openPdf: "開啟文件", text: "科技股貼文，含蘋果公司季度錯誤。" });
  Object.assign(COPY.zh.live, { scope: "美股申報財務數據；不含價格、預測、加密資產或投資建議。", pending: "模型正在選擇工具並核對申報事實…", evidence: "申報證據", filing: "開啟申報文件", honesty: "模型選擇工具並提出主張，程式核對數字、期間與證據識別碼。支持判定只適用於已擷取的主張，擷取可能遺漏。申報可能不完整或經過重述；申報資料可能快取六小時。" });
  COPY.en.live.privacy = COPY.en.presentation.privacySummary;
  COPY.zh.live.privacy = COPY.zh.presentation.privacySummary;
  COPY.en.matrix.privacy = COPY.en.presentation.privacySummary;
  COPY.zh.matrix.privacy = COPY.zh.presentation.privacySummary;
  COPY.en.examples.privacy = COPY.en.presentation.privacyDetails;
  COPY.zh.examples.privacy = COPY.zh.presentation.privacyDetails;

  COPY.en.presentation.benchmarkDuration = "10 s";
  COPY.en.how.step1.body = "Muse extracts each number, period and comparison.";
  COPY.en.how.step2.body = "Find the same company, metric and period in the filing.";
  COPY.en.how.step3.body = "Python checks the values and their numeric tolerance.";
  COPY.zh.presentation.benchmarkDuration = "10 秒";
  COPY.zh.stamps.filingPanel = "② 申報文件";
  COPY.zh.live.recordedNote = "已儲存紀錄 · 2026-10-28 · 真實模型呼叫與申報證據。即時預算用完仍可查看。";
  COPY.zh.matrix.noScript = "請啟用瀏覽器指令以選擇輸入或讀取即時歷史紀錄。下方也提供已儲存的文字查核。";
  // The static page builder imports this same dictionary through Node.
  // No DOM, provider calls or page initialization run during generation.
  if (typeof document === "undefined") {
    if (typeof module === "object") module.exports = COPY;
    return;
  }

  let pageLanguage = readLanguage();
  let exampleLanguage = pageLanguage;
  let siteData = null;
  let chartProvider = "all", followStep = 1, followRecord = null;
  const savedExampleRecords = new Map();
  let stampConveyor = null;
  let activeFilingClaim = null;
  let filingReturnFocus = null;
  let savedLiveDemo = null;
  let savedDemoKind = "post";
  const savedDemos = {};
  let liveResult = null;
  let liveStatus = "";
  const LIVE_PASSWORD_KEY = "claimcheck.livePassword";
  let liveBudget = null;
  let liveBusy = false;
  let budgetLoaded = false;
  let budgetRequest = 0;
  let budgetTimer = null;
  let budgetDay = "";
  const exampleIds = ["text", "image", "pdf", "audio", "video"];
  let examplesIndex = [];
  let exampleSavedStatus = "";
  const providers = {
    meta: { label: "Meta Model API", model: "muse-spark-1.3" },
    baseten: { label: "Baseten", model: "meta-models/muse-spark-open-1026" },
    fireworks: { label: "Fireworks", model: "accounts/fireworks/models/muse-spark-open" }
  };
  let stories = [
    { id: "A", titleKey: "storyA", expectedKey: "expectedA" },
    { id: "B", titleKey: "storyB", expectedKey: "expectedB" },
    { id: "C", titleKey: "storyC", expectedKey: "expectedC" }
  ];
  let selectedStory = "A", selectedKind = "text", selectedProvider = "baseten";
  let customText = false, inputLoadState = "assetsLoading", compareRuns = [], resultContext = null;
  let rateLimitReset = null;
  let historyRows = [], historyState = "historyLoading", historyRequest = 0, resultRequest = 0, inputRequest = 0;
  let historyVisible = 6, pendingHistoryRows = [], liveTerminalView = null;
  let historyDetailRequest = 0, historyDetailController = null, historyModalRecord = null, historyModalResult = null;
  let historyModalState = "", historyReturnId = null, historyBodyOverflow = "";
  const exampleTexts = new Map();

  function matrixCopy(key) { return COPY[pageLanguage].matrix[key] || ""; }
  function tryCopy(key, ...args) {
    const value = COPY[pageLanguage].tryUI[key];
    return typeof value === "function" ? value(...args) : value;
  }
  function validId(value) { return typeof value === "string" && /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(value); }
  function selectedAsset() { return examplesIndex.find(row => row.story === selectedStory && row.kind === selectedKind); }
  function providerLabel(value) { return pageLanguage === "zh" && providers[value] ? getCopy(`presentation.provider${value[0].toUpperCase()}${value.slice(1)}`) : providers[value]?.label || String(value || liveCopy("notRecorded")); }
  function money(value, decimals = 5) { return Number.isFinite(value) ? `$${value.toFixed(decimals)}` : "—"; }
  function duration(value) { return Number.isFinite(value) ? `${(value / 1000).toFixed(1)} ${liveCopy("seconds")}` : "—"; }
  function runReceipt(result) {
    return result.receipt || { provider: result.provider, model: result.model, latency_ms: result.latency_ms,
      cost_usd: result.cost_usd, preprocessing: result.input?.preprocessing };
  }

  function liveCopy(key) { return COPY[pageLanguage].live[key]; }

  function liveErrorText(error) {
    const reset = rateLimitReset === null ? liveCopy("rateResetUnknown") : liveCopy("rateReset").replace("{time}",
      new Date(rateLimitReset).toLocaleString(pageLanguage === "zh" ? "zh-TW" : "en-US", {
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZoneName: "short"
      }));
    return (liveCopy("errors")[error] || liveCopy("errors").unavailable).replace("{reset}", reset);
  }

  function liveNode(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }

  function liveNumber(value) {
    return typeof value === "number" && Number.isFinite(value)
      ? value.toLocaleString(pageLanguage === "zh" ? "zh-TW" : "en-US", { maximumFractionDigits: 4 }) : "—";
  }

  // Presentation only: recorded values, spans and verdicts stay in Inspect data.
  // A known stated scale wins over the magnitude (e.g. $1,024.7M stays in M).
  function financialNumber(value, unit = "USD", statedText = "") {
    if (typeof value !== "number" || !Number.isFinite(value)) return "—";
    const scale = String(statedText).match(/\$[\d,.]+\s*(billion|million|B|M)\b/i)?.[1]?.toLowerCase();
    if (unit === "USD") {
      const divisor = scale === "b" || scale === "billion" ? 1e9 : scale === "m" || scale === "million" ? 1e6
        : Math.abs(value) >= 1e9 ? 1e9 : Math.abs(value) >= 1e6 ? 1e6 : 1;
      const number = (Math.abs(value) / divisor).toLocaleString("en-US", {
        minimumFractionDigits: divisor === 1 ? 0 : 1, maximumFractionDigits: divisor === 1 ? 4 : 1
      });
      return `${value < 0 ? "−" : ""}$${number}${divisor === 1e9 ? "B" : divisor === 1e6 ? "M" : ""}`;
    }
    if (unit === "%" || unit === "percent") return `${value.toFixed(1)}%`;
    return `${liveNumber(value)}${unit ? ` ${unit}` : ""}`;
  }

  function draftMoney(text) {
    return text.replace(/(-?)\$([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)\b/gi, (token, sign, number, scale) =>
      financialNumber(Number(`${sign}${number.replaceAll(",", "")}`) * (/^b/i.test(scale) ? 1e9 : 1e6), "USD", token));
  }

  function readableDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return "";
    if (pageLanguage === "zh") return formatDate(value);
    const [year, month, day] = value.split("-").map(Number);
    return `${day} ${["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month - 1]} ${year}`;
  }

  function readablePeriod(fact, context = {}) {
    const period = String(fact.period || context.period || "");
    const match = period.match(/^(FY|CY)?(\d{4})(?:Q([1-4]))?$/i);
    const fiscal = match?.[1]?.toUpperCase() === "FY" || fact.period_basis === "fiscal" || context.period_basis === "fiscal";
    const year = match?.[2] || fact.fiscal_year || fact.end?.slice(0, 4);
    if (fact.period_type === "ytd" && fact.start && fact.end) {
      // SEC's 52/53-week calendars use week-aligned rather than month-aligned dates.
      const months = Math.round((Date.parse(fact.end) - Date.parse(fact.start) + 86400000) / 86400000 / 30.4375);
      if (months >= 1 && months <= 12) return liveCopy("monthsTo")(months, readableDate(fact.end));
    }
    if (year && (fact.period_type === "annual" || (match && !match[3]))) {
      return liveCopy(fiscal ? "fiscalAnnual" : "calendarAnnual")(year);
    }
    if (match?.[3]) return liveCopy(fiscal ? "fiscalQuarter" : "calendarQuarter")(year, match[3]);
    return readableDate(fact.end) ? liveCopy("ended")(readableDate(fact.end)) : liveCopy("unknownPeriod");
  }

  function financialMetric(metric) {
    return liveCopy("metrics")[metric] || String(metric || "").replaceAll("_", " ");
  }

  function secLink(urlText, label) {
    try {
      const url = new URL(urlText);
      if (url.protocol === "https:" && url.host === "www.sec.gov" && !url.username && !url.password &&
          url.pathname.startsWith("/Archives/edgar/data/")) {
        const link = liveNode("a", label);
        link.href = url.href;
        link.rel = "noreferrer";
        return link;
      }
    } catch (_error) { /* Invalid filing URLs remain plain text. */ }
    return null;
  }

  function liveRaw(parent, data, primary) {
    const details = liveNode("details", null, "trace-data");
    const summary = liveNode("summary");
    if (primary) {
      details.classList.toggle("evidence-data", true);
      summary.append(primary, liveNode("span", ` · ${liveCopy("raw")}`, "evidence-inspect"));
    } else summary.textContent = liveCopy("raw");
    details.append(summary, liveNode("pre", JSON.stringify(data, null, 2)));
    parent.append(details);
  }

  function liveVerdict(value) {
    if (["not_judged", "opinion", "forecast"].includes(value)) return matrixCopy("notJudged");
    return ["supported", "contradicted", "insufficient_evidence", "unchecked"].includes(value) ? liveCopy(value) : "—";
  }

  function renderLiveCorrections(corrections, target, evidence = []) {
    if (!corrections || typeof corrections.original_text !== "string" ||
        corrections.span_unit !== "unicode_codepoints") return;
    const section = liveNode("section", null, "live-corrections");
    section.append(liveNode("h5", liveCopy("correctedDraft")));
    // Python offsets count code points. Array.from keeps emoji before an edit
    // from shifting its span in JavaScript's UTF-16 strings.
    const original = Array.from(corrections.original_text);
    const draft = liveNode("p", null, "corrected-draft-text");
    const changes = liveNode("ol", null, "correction-changes");
    let cursor = 0;
    for (const edit of Array.isArray(corrections.edits) ? corrections.edits : []) {
      if (!Number.isInteger(edit.start) || !Number.isInteger(edit.end) || edit.start < cursor ||
          edit.end <= edit.start || edit.end > original.length || typeof edit.replacement !== "string" ||
          original.slice(edit.start, edit.end).join("") !== edit.original) continue;
      // Keep the draft code-point exact; compact money only in the edit list.
      draft.append(liveNode("span", original.slice(cursor, edit.start).join("")),
        liveNode("del", edit.original), document.createTextNode(" → "), liveNode("strong", edit.replacement));
      cursor = edit.end;
      const item = liveNode("li");
      item.append(liveNode("del", draftMoney(edit.original)), document.createTextNode(" → "), liveNode("strong", draftMoney(edit.replacement)));
      const fact = evidence.find((entry) => edit.evidence_ids?.includes(entry.evidence_id));
      const components = fact?.components || edit.citations || [];
      const annual = components.find((entry) => entry.period_type === "annual");
      const nineMonths = components.find((entry) => entry.period_type === "ytd" &&
        Math.round((Date.parse(entry.end) - Date.parse(entry.start)) / 86400000 / 30.4375) === 9);
      if (annual && nineMonths && /Q4$/i.test(edit.period) &&
          Math.abs(annual.value - nineMonths.value - edit.actual_value) < 0.01) {
        item.append(liveNode("p", liveCopy("derivedQuarter"), "correction-derivation"));
      }
      const citations = liveNode("ul", null, "correction-citations");
      for (const citation of Array.isArray(edit.citations) ? edit.citations : []) {
        const row = liveNode("li");
        const primary = liveNode("p", null, "citation-primary");
        const value = [financialNumber(citation.value, citation.unit, edit.original), financialMetric(fact?.metric)].filter(Boolean).join(" ");
        primary.append(liveNode("span", `${[citation.form, readablePeriod(citation, edit), value].filter(Boolean).join(" · ")}`));
        const link = secLink(citation.url, liveCopy("filing"));
        if (link) primary.append(document.createTextNode(" · "), link);
        row.append(primary);
        citations.append(row);
      }
      item.append(citations);
      liveRaw(item, edit);
      changes.append(item);
    }
    draft.append(liveNode("span", original.slice(cursor).join("")));
    section.append(draft, liveNode("p", liveCopy("correctionScope"), "correction-scope"));
    if (changes.children.length) section.append(liveNode("h6", liveCopy("correctionChanges")), changes);
    if (Array.isArray(corrections.not_corrected) && corrections.not_corrected.length) {
      const unchanged = liveNode("ol", null, "correction-unchanged");
      for (const item of corrections.not_corrected) {
        const row = liveNode("li");
        row.append(liveNode("p", item.text, "correction-assertion"), liveNode("p", item.reason?.[pageLanguage] || "", "correction-reason"));
        unchanged.append(row);
      }
      section.append(liveNode("h6", liveCopy("notCorrected")), unchanged);
    }
    target.append(section);
    return changes.children.length > 0;
  }

  function renderLiveTrace(result, target) {
    if (!target) return;
    target.replaceChildren();
    target.hidden = false;
    const input = typeof result.input === "string" ? { text_read: result.input } : result.input;
    if (input && typeof input.text_read === "string") {
      const read = liveNode("section", null, "live-input-read");
      read.append(liveNode("h5", liveCopy("read")), liveNode("blockquote", input.text_read, "trace-input"));
      const prep = result.receipt?.preprocessing || input.preprocessing;
      if (prep && typeof prep === "object") {
        read.append(liveNode("p", [input.kind, prep.provider, prep.model].filter(value => typeof value === "string").join(" · "), "live-small"));
      }
      target.append(read);
    }
    const receipt = runReceipt(result);
    const receiptBlock = liveNode("section", null, "live-receipt");
    receiptBlock.append(liveNode("h5", matrixCopy("receipt")),
      liveNode("p", [providerLabel(receipt.provider), receipt.model || liveCopy("notRecorded"),
        duration(receipt.latency_ms), `${result.cost_is_bound ? liveCopy("bound") : matrixCopy("cost")}: ${money(receipt.cost_usd, 2)}`].join(" · ")));
    const prep = receipt.preprocessing;
    receiptBlock.append(liveNode("p", prep
      ? [liveCopy("preprocessing"), prep.model || liveCopy("notRecorded"), duration(prep.latency_ms), money(prep.cost_usd, 2)].join(" · ")
      : `${matrixCopy("noPreprocessing")} · ${receipt.preprocessing === null ? "$0.00" : liveCopy("notRecorded")}`, "live-small"));
    target.append(receiptBlock);
    const head = liveNode("div", null, "trace-head");
    head.append(liveNode("p", target === $("#live-result") && result.mode === "recorded" && input?.example_id ? savedRecordingLabel(result) : liveCopy(result.mode === "recorded" ? "recorded" : result.mode === "mock" ? "mock" : "live"), "trace-mode"));
    if (result.error) head.append(liveNode("p", liveErrorText(result.error), "live-error"));
    if (result.started_at) head.append(liveNode("p", `${result.started_at} → ${result.finished_at}`, "live-small"));
    if (result.verdict) head.append(liveNode("h4", liveVerdict(result.verdict), `trace-verdict is-${result.verdict}`));
    target.append(head);
    const evidence = (result.evidence || []).filter((fact) => !fact.error);
    const hasCorrection = renderLiveCorrections(result.corrections, target, evidence);
    if (!hasCorrection && result.verdict === "supported") {
      let draft = target.querySelector(".live-corrections");
      if (!draft) {
        draft = liveNode("section", null, "live-corrections");
        draft.append(liveNode("h5", liveCopy("correctedDraft")));
        target.append(draft);
      }
      draft.append(liveNode("p", matrixCopy("nothingToCorrect")));
    }
    const proof = liveNode("section", null, "live-proof");
    proof.append(liveNode("h5", liveCopy("evidence")));
    const rows = liveNode("div", null, "live-evidence");
    if (!evidence.length) rows.append(liveNode("p", liveCopy("noEvidence")));
    evidence.forEach((fact) => {
      const row = liveNode("div", null, "live-evidence-row");
      const current = fact.current_fact || fact.current;
      const base = fact.base_fact || fact.base;
      const growth = typeof fact.pct_change === "number";
      const stated = (result.claims || []).find((claim) => claim.evidence_ids?.includes(fact.evidence_id))?.text || "";
      const company = { AMZN: "Amazon", NVDA: "NVIDIA", AAPL: "Apple" }[fact.ticker] || fact.entity || fact.ticker || "";
      const metric = financialMetric(fact.metric) + (growth ? `${pageLanguage === "zh" ? "" : " "}${liveCopy("growth")}` : "");
      const subject = [company, metric].filter(Boolean).join(" ");
      const period = growth && /^FY\d{4}$/.test(fact.period) && /^FY\d{4}$/.test(fact.base_period)
        ? liveCopy("annualComparison")(fact.period.slice(2), fact.base_period.slice(2))
        : growth && base ? `${readablePeriod(current || fact)} / ${readablePeriod(base)}` : readablePeriod(fact);
      const forms = fact.derived ? [...new Set((fact.components || []).map((entry) => entry.form))].join(" − ")
        : fact.form || current?.form;
      const primary = liveNode("span", null, "evidence-primary");
      primary.append(liveNode("span", `${financialNumber(growth ? fact.pct_change : fact.value ?? fact.abs_change,
        growth ? "%" : fact.unit, stated)} · ${subject} · ${period}`));
      if (forms) {
        primary.append(document.createTextNode(" · "), secLink(fact.filing_url, forms) || liveNode("span", forms));
      }
      liveRaw(row, fact, primary);
      rows.append(row);
    });
    proof.append(rows);
    if (result.claims && result.claims.length) {
      proof.append(liveNode("h5", liveCopy("claims")));
      const claims = liveNode("ol", null, "live-claims");
      result.claims.forEach((check) => {
        const item = liveNode("li");
        item.append(liveNode("strong", liveVerdict(check.program_verdict), `is-${check.program_verdict}`), liveNode("p", check.text));
        const source = evidence.find((fact) => check.evidence_ids?.includes(fact.evidence_id));
        const unit = typeof source?.pct_change === "number" ? "%" : source?.unit || "";
        item.append(liveNode("p", `${liveCopy("stated")}: ${financialNumber(check.stated_value_used, unit, check.text)} · ${liveCopy("actual")}: ${financialNumber(check.actual_value, unit, check.text)} · ${liveCopy("tolerance")}: ${financialNumber(check.tolerance, unit)}`, "live-small"));
        item.append(liveNode("p", `${liveCopy("strength")}: ${liveCopy(check.evidence_strength) || "—"}`, "live-small"));
        liveRaw(item, check);
        claims.append(item);
      });
      proof.append(claims);
    }
    target.append(proof);
    const trace = liveNode("details", null, "live-trace");
    trace.open = !hasCorrection;
    trace.append(liveNode("summary", liveCopy("traceSteps")((result.events || []).length), "agent-trace-summary"));
    const steps = liveNode("ol", null, "agent-trace");
    (result.events || []).forEach((event, i) => {
      const step = liveNode("li", null, `trace-step trace-${event.kind}`);
      const label = liveNode("div", null, "trace-step-label");
      label.append(liveNode("span", String(i + 1).padStart(2, "0"), "trace-step-number"),
        liveNode("strong", `${liveCopy(event.kind === "preprocessing" ? "preprocessingEvent" : event.kind) || event.kind}${event.step ? ` ${event.step}` : ""}`));
      step.append(label);
      step.append(liveNode("small", typeof event.at_ms === "number" ? `+${(event.at_ms / 1000).toFixed(1)} ${liveCopy("seconds")} · ${event.timestamp || ""}` : liveCopy("notRecorded"), "trace-time"));
      if (event.kind === "model") {
        step.append(liveNode("p", `${(event.latency_ms / 1000).toFixed(1)} ${liveCopy("seconds")} · ${cost(event.cost_usd)} · ${event.finish_reason || ""}`));
        liveRaw(step, event);
      } else if (event.kind === "tool_call") {
        step.append(liveNode("code", `${event.name}(${JSON.stringify(event.arguments)})`));
      } else if (event.kind === "tool_result") {
        const fact = event.result || {};
        step.append(liveNode("p", `${fact.evidence_id || ""} · ${liveNumber(fact.value ?? fact.pct_change ?? fact.abs_change)} ${fact.unit || ""} · ${fact.period || ""}`));
        liveRaw(step, fact);
      } else if (event.kind === "program_check") {
        const check = event.check || {};
        step.append(liveNode("p", `${liveVerdict(check.program_verdict)} · ${check.reason || ""}`));
        liveRaw(step, check);
      } else if (event.kind === "program_binding") {
        step.append(liveNode("p", `${event.source} · ${(event.evidence_ids || []).join(", ")} · ${event.reason}`));
        liveRaw(step, event);
      } else if (event.kind === "verdict") {
        step.append(liveNode("strong", liveVerdict(event.verdict), `is-${event.verdict}`));
      }
      steps.append(step);
    });
    trace.append(steps, liveNode("p", liveCopy("honesty"), "live-small"));
    if (result.mode === "recorded" || result.mode === "mock") {
      trace.append(liveNode("p", liveCopy(result.recording?.receipt ? "recordedTiming" : "timing"), "live-small"));
      if (typeof result.source === "string" && /^docs\/evidence\/[\w/.-]+\.json$/.test(result.source)) {
        const link = liveNode("a", liveCopy("source"));
        link.href = `https://github.com/YanlongLai/market-claim-verifier/blob/main/${result.source}`;
        trace.append(link);
      }
    }
    target.append(trace);
  }

  function providerStop(provider) {
    const stops = ["credit_exhausted", "total_budget_exhausted", "budget_exhausted"];
    const status = liveBudget?.providers?.[provider]?.status;
    return stops.includes(status) ? status : "";
  }

  function memberStop(provider) {
    const media = !customText && ["image", "audio", "video"].includes(selectedKind);
    return providerStop(provider) || (media ? providerStop("meta") : "");
  }

  function liveStop() {
    if ($("#compare-all")?.checked) {
      return Object.keys(providers).every(id => memberStop(id)) ? memberStop(selectedProvider) : "";
    }
    return memberStop(selectedProvider);
  }

  function budgetStopText(stop) {
    return (liveCopy("budget")[stop] || "").replace("{reset}", liveBudget?.resets_at?.slice(0, 10) || "00:00 UTC");
  }

  function renderLiveBudget() {
    if (!$("#budget-baseten-text")) return;  // Historical evidence pages have no live chooser.
    const copy = liveCopy("budget");
    const dollars = amount => `$${amount.toFixed(2)}`;
    Object.keys(providers).forEach(id => {
      const text = $(`#budget-${id}-text`), meter = $(`#budget-${id}-meter`), note = $(`#budget-${id}-status`);
      const budget = liveBudget?.providers?.[id], stop = providerStop(id);
      text.replaceChildren();
      if (budget) {
        const amount = liveNode("span", dollars(budget.daily_remaining), "provider-amount");
        const caption = liveNode("span", tryCopy("daily", dollars(budget.daily_remaining)), "provider-daily");
        text.append(amount, caption);
      } else text.textContent = copy[budgetLoaded ? "unavailable" : "loading"];
      const model = $(`#live-form input[value="${id}"]`)?.parentElement?.querySelector("small") ||
        $$(".provider-model")[Object.keys(providers).indexOf(id)];
      if (model) model.title = [providers[id].model, budget ? tryCopy("lifetime", dollars(budget.lifetime_remaining), dollars(budget.lifetime_limit)) : ""].filter(Boolean).join(" · ");
      if (liveBudget?.mode === "mock") text.textContent = copy.mock;
      meter.hidden = !budget;
      if (budget) {
        meter.max = Math.max(budget.daily_limit, 0.01);
        meter.value = budget.daily_remaining;
        meter.setAttribute("aria-valuetext", tryCopy("daily", dollars(budget.daily_remaining)));
      }
      note.textContent = stop ? copy[{ budget_exhausted: "dailyStop", total_budget_exhausted: "lifetimeStop", credit_exhausted: "creditStop" }[stop]] : "";
      note.hidden = !note.textContent;
    });
    const disabled = liveBusy || !liveBudget;
    $("#live-input").disabled = disabled;
    const asset = selectedAsset();
    $("#live-submit").disabled = disabled || Boolean(liveStop()) || (!customText && (!asset?.ready || inputLoadState === "textLoading"));
    $("#live-example").disabled = disabled;
    $("#live-password").disabled = liveBusy;
    $("#example-saved").disabled = liveBusy;
    $("#result-edit").disabled = liveBusy;
  }

  async function refreshLiveBudget() {
    const id = ++budgetRequest;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);
    try {
      const response = await fetch("/api/budget", {
        cache: "no-store", headers: { "Cache-Control": "no-cache" }, signal: controller.signal
      });
      const data = await response.json();
      if (!response.ok || !["ready", "budget_exhausted", "total_budget_exhausted", "credit_exhausted"].includes(data.status) ||
          !Object.keys(providers).every(id => {
            const row = data.providers?.[id];
            return row && ["ready", "budget_exhausted", "total_budget_exhausted", "credit_exhausted"].includes(row.status) &&
              ["daily_limit", "daily_spent", "daily_remaining", "lifetime_limit", "lifetime_spent", "lifetime_remaining"]
                .every(key => typeof row[key] === "number" && Number.isFinite(row[key]) && row[key] >= 0);
          }) ||
          !Number.isFinite(Date.parse(data.resets_at))) throw new Error("budget unavailable");
      if (id !== budgetRequest) return;
      if (budgetDay && data.day !== budgetDay && liveStatus === "budget_exhausted") liveStatus = "";
      if (data.status === "ready" && ["credit_exhausted", "total_budget_exhausted"].includes(liveStatus)) liveStatus = "";
      budgetDay = data.day;
      liveBudget = data;
      clearTimeout(budgetTimer);
      // Re-read the server at midnight; the browser never resets a counter.
      budgetTimer = setTimeout(refreshLiveBudget, Math.max(1000, Date.parse(data.resets_at) - Date.now() + 50));
      budgetTimer?.unref?.();
    } catch {
      if (id === budgetRequest) liveBudget = null;
    } finally {
      clearTimeout(timeout);
      if (id === budgetRequest) { budgetLoaded = true; localizeLive(); }
    }
  }

  function localizeLive() {
    if (savedLiveDemo) renderLiveTrace(savedLiveDemo, $("#recorded-trace"));
    if (liveResult) renderLiveTrace(liveResult, $("#live-result"));
    const status = $("#live-status");
    if (status) status.textContent = liveStop() ? budgetStopText(liveStop()) : liveStatus === "comparing"
      ? matrixCopy("comparing") : ["pending", "complete", "mediaPending"].includes(liveStatus)
        ? liveCopy(liveStatus) : liveStatus ? liveErrorText(liveStatus) : "";
    if (status) status.classList.toggle("visually-hidden", !liveStop() && ["pending", "complete", "mediaPending", "comparing"].includes(liveStatus));
    const savedStatus = $("#example-saved-status");
    if (savedStatus) savedStatus.textContent = COPY[pageLanguage].examples[exampleSavedStatus] || "";
    if ($("#result-edit")) $("#result-edit").hidden = !liveResult;
    renderMatrix();
    renderComparison();
    renderHistory();
    renderHistoryDialog();
    renderLiveBudget();
    liveTerminalView?.();
  }

  // Asset paths are confined to our committed examples, including previews.
  function exampleUrl(path) {
    if (typeof path !== "string" || !path || !/^[a-zA-Z0-9_./-]+$/.test(path) || path.split("/").includes("..")) return null;
    if (path.startsWith("/")) return path.startsWith("/examples/") ? path : null;
    return `/examples/${path.replace(/^\.\//, "")}`;
  }

  function acceptManifest(data) {
    const array = Array.isArray(data);
    const source = array ? data : data?.examples;
    if (!Array.isArray(source) || !source.length) throw Error("invalid example manifest");
    const legacy = array && source.every(row => !row.story);
    const nextStories = !array ? data.stories : legacy ? stories :
      [...new Set(source.map(row => row.story))].map((id, index) => {
        const row = source.find(row => row.story === id);
        return { id, title_en: `${String(id).toUpperCase()} · ${row.story_title?.en || id}`,
          title_zh: `${String(id).toUpperCase()} · ${row.story_title?.zh || id}`,
          expectedKey: ["expectedA", "expectedB", "expectedC"][index] };
      });
    if (!Array.isArray(nextStories) || nextStories.length !== 3 || nextStories.some(row => !validId(row.id) ||
      (!legacy && (typeof row.title_en !== "string" || typeof row.title_zh !== "string"))) ||
      new Set(nextStories.map(row => row.id)).size !== 3) throw Error("invalid stories");
    const rows = source.map(row => ({ ...row, story: legacy ? nextStories[0].id : row.story,
      url: exampleUrl(row.file), previewUrl: exampleUrl(row.preview),
      ready: row.status !== "pending" && !String(row.file).includes(".pending.") }));
    if (rows.some(row => !validId(row.id) || !exampleIds.includes(row.kind) || !row.url ||
      !nextStories.some(story => story.id === row.story) || !/^[a-f0-9]{64}$/i.test(row.sha256)) ||
      new Set(rows.map(row => row.id)).size !== rows.length ||
      new Set(rows.map(row => `${row.story}/${row.kind}`)).size !== rows.length) throw Error("invalid examples");
    rows.forEach(row => {
      if (!row.previewUrl && ["pdf", "video"].includes(row.kind))
        row.previewUrl = rows.find(image => image.story === row.story && image.kind === "image" && image.ready)?.url;
    });
    stories = nextStories;
    examplesIndex = rows;
    if (!stories.some(row => row.id === selectedStory)) selectedStory = stories[0].id;
  }

  async function loadExamples() {
    if (!$("#input-panel")) return;
    try {
      let response = await fetch("/examples/manifest.json", { cache: "no-store" });
      if (!response.ok) response = await fetch("/data/examples/index.json", { cache: "no-store" });
      if (!response.ok) throw Error("missing manifest");
      acceptManifest(await response.json());
      await loadExampleText();
      const id = selectedAsset()?.id;
      if (id) readExampleSaved(id).then(() => { if (selectedAsset()?.id === id) renderMatrix(); }).catch(() => {});
    } catch { inputLoadState = "assetsFailed"; }
    localizeLive();
  }

  function renderMatrix() {
    if (!$("#input-panel")) return;
    $$("[data-story-slot]").forEach((button, index) => {
      const story = stories[index];
      if (!story) return;
      button.setAttribute("aria-pressed", String(story.id === selectedStory));
      const letter = "ABC"[index];
      button.querySelector(".story-label").textContent = tryCopy(`story${letter}`);
      button.querySelector(".story-short").textContent = tryCopy(`story${letter}Short`);
      let expected = story.expectedKey ? matrixCopy(story.expectedKey) : story.expected?.[pageLanguage] || story.expected;
      if (expected === "supported") expected = matrixCopy("expectedB");
      else if (expected === "mixed") expected = matrixCopy("expectedC");
      else if (expected === "contradicted" && index === 0) expected = matrixCopy("expectedA");
      else if (["contradicted", "insufficient_evidence"].includes(expected)) expected = liveVerdict(expected);
      if (story.id === selectedStory) {
        const hint = $("#story-expected");
        const [verdict, ...detail] = (typeof expected === "string" ? expected : "—").split(" · ");
        hint.replaceChildren(document.createTextNode(`${tryCopy("expected")}${pageLanguage === "zh" ? "：" : ": "}`), liveNode("strong", verdict), document.createTextNode(detail.length ? ` · ${detail.join(" · ")}` : ""));
        hint.title = hint.textContent;
      }
      button.disabled = liveBusy;
    });
    $$("[data-input-kind]").forEach(button => {
      const active = button.dataset.inputKind === selectedKind;
      button.setAttribute("aria-selected", String(active));
      button.setAttribute("tabindex", active ? "0" : "-1");
      button.disabled = liveBusy;
    });
    $("#input-panel").setAttribute("aria-labelledby", `input-tab-${selectedKind}`);
    $("#text-input-panel").hidden = selectedKind !== "text";
    $("#live-input").required = selectedKind === "text";
    $("#input-preview").hidden = selectedKind === "text";
    const asset = selectedAsset();
    const description = customText ? matrixCopy("custom") : asset?.[`what_${pageLanguage}`] || asset?.contains?.[pageLanguage] || "";
    $("#input-description").textContent = inputLoadState ? matrixCopy(inputLoadState) :
      asset?.ready || customText ? description : matrixCopy(asset ? "assetPending" : "assetsLoading");
    $("#input-description").title = $("#input-description").textContent;
    $("#live-example").hidden = selectedKind !== "text";
    $("#live-count").hidden = selectedKind !== "text";
    const link = $("#input-file");
    link.hidden = !asset?.ready || customText;
    if (asset?.ready) link.href = asset.url;
    link.textContent = matrixCopy("openInput");
    // Do not reconstruct players on budget/history updates: playback keeps its position.
    const preview = $("#input-preview");
    const key = `${selectedStory}/${selectedKind}/${asset?.ready}/${asset?.url}/${asset?.previewUrl}/${asset?.sha256}`;
    if (preview.dataset.key !== key) {
      preview.dataset.key = key;
      preview.replaceChildren();
      if (asset && !asset.ready) preview.append(liveNode("p", matrixCopy("assetPending"), "asset-pending"));
      else if (selectedKind === "image" || selectedKind === "pdf") {
        const url = selectedKind === "image" ? asset.url : asset.previewUrl;
        if (url) { const image = liveNode("img"); image.src = url; image.alt = description; preview.append(image); }
        else preview.append(liveNode("p", COPY[pageLanguage].examples.nativeText));
      } else if (["audio", "video"].includes(selectedKind)) {
        const player = liveNode(selectedKind);
        player.controls = true;
        player.preload = "none";
        player.src = asset.url;
        if (selectedKind === "video" && asset.previewUrl) player.poster = asset.previewUrl;
        preview.append(player);
      }
    }
    const image = preview.querySelector("img");
    if (image) image.alt = description;
    const pending = preview.querySelector(".asset-pending");
    if (pending) pending.textContent = matrixCopy("assetPending");
    $$('#live-form input[name="provider"]').forEach(radio => { radio.checked = radio.value === selectedProvider; radio.disabled = liveBusy; });
    $("#fireworks-note").hidden = selectedProvider !== "fireworks";
    $("#compare-all").disabled = liveBusy;
    const submit = $("#live-submit");
    submit.replaceChildren();
    if (liveBusy) { const spinner = liveNode("span", "", "try-spinner"); spinner.setAttribute("aria-hidden", "true"); submit.append(spinner); }
    submit.append(document.createTextNode(liveBusy ? tryCopy("checking") : matrixCopy("run")));
    $("#live-count").textContent = `${Array.from($("#live-input").value || "").length} / 600`;
    const saved = asset && (savedExampleRecords.get(asset.id) || asset.saved_result === `/data/examples/${asset.id}.json`);
    $("#example-saved").textContent = COPY[pageLanguage].examples[saved ? "saved" : "savedPending"];
    const note = $("#example-recording");
    if (note) {
      const record = asset && savedExampleRecords.get(asset.id);
      note.textContent = record ? savedRecordingLabel(record) : "";
      $("#example-saved").title = note.textContent;
    }
  }

  async function loadExampleText() {
    const request = ++inputRequest;
    const asset = selectedAsset();
    inputLoadState = "";
    if (selectedKind !== "text" || customText || !asset?.ready) return;
    if (exampleTexts.has(asset.id)) { $("#live-input").value = exampleTexts.get(asset.id); return; }
    $("#live-input").value = "";
    inputLoadState = "textLoading";
    renderMatrix();
    try {
      const response = await fetch(asset.url, { cache: "no-store" });
      if (!response.ok) throw Error("missing text");
      const text = await response.text();
      if (!text.trim() || Array.from(text.trim()).length > 600) throw Error("invalid example text");
      exampleTexts.set(asset.id, text);
      if (request === inputRequest && !customText) { $("#live-input").value = text; inputLoadState = ""; }
    } catch { if (request === inputRequest && !customText) inputLoadState = "textFailed"; }
  }

  async function selectMatrix(story, kind) {
    if (liveBusy || !stories.some(row => row.id === story) || !exampleIds.includes(kind)) return;
    ++resultRequest;
    if (historyState === "historyOpening") historyState = "";
    // Stop a previous story's narration when changing input.
    for (const player of $$("#input-preview audio, #input-preview video")) player.pause?.();
    selectedStory = story;
    selectedKind = kind;
    customText = false;
    exampleSavedStatus = "";
    if (kind === "text") $("#live-input").value = "";
    await loadExampleText();
    localizeLive();
    const id = selectedAsset()?.id;
    if (id && !savedExampleRecords.has(id)) readExampleSaved(id).then(() => {
      if (selectedAsset()?.id === id) renderMatrix();
    }).catch(() => {});
  }

  function showResult(result, source = {}) {
    liveResult = result;
    const input = typeof result.input === "string" ? { text_read: result.input } : result.input;
    resultContext = { ...source, text: input?.text_read ?? source.input_text ?? "",
      provider: runReceipt(result).provider || source.provider || selectedProvider };
    renderLiveTrace(result, $("#live-result"));
    if ($("#result-edit")) $("#result-edit").hidden = false;
  }

  async function selectExampleSaved(id = selectedAsset()?.id) {
    const request = ++resultRequest;
    liveResult = null;
    compareRuns = [];
    $("#live-result").hidden = true;
    liveStatus = "";
    exampleSavedStatus = validId(id) ? "loading" : "savedPending";
    localizeLive();
    const asset = examplesIndex.find(row => row.id === id);
    if (!validId(id) || !asset) {
      exampleSavedStatus = "savedPending";
      localizeLive();
      return;
    }
    try {
      const result = await readExampleSaved(id);
      if (request !== resultRequest) return;
      if (result.mode !== "recorded" || result.input?.example_id !== id || typeof result.input.text_read !== "string") throw Error("invalid saved example");
      exampleSavedStatus = "";
      showResult(result);
    } catch { if (request === resultRequest) exampleSavedStatus = "savedPending"; }
    if (request === resultRequest) localizeLive();
  }

  function renderComparison() {
    const target = $("#compare-result");
    if (!target) return;
    target.hidden = !compareRuns.length;
    target.replaceChildren();
    if (!compareRuns.length) return;
    const table = liveNode("table", null, "compare-table");
    table.append(liveNode("caption", matrixCopy("comparison")));
    const head = liveNode("thead"), names = liveNode("tr"), body = liveNode("tbody");
    compareRuns.forEach(result => { const th = liveNode("th", providerLabel(runReceipt(result).provider)); th.scope = "col"; names.append(th); });
    head.append(names);
    const fields = [
      [liveCopy("verdict"), result => result._notRun ? matrixCopy("notRun") : result.error ? liveErrorText(result.error) : result.verdict ? liveVerdict(result.verdict) : "—"],
      [matrixCopy("corrections"), result => result.error || result._notRun ? "—" : result.corrections?.edits?.length ?? result.corrections_count ?? "—"],
      [matrixCopy("duration"), result => duration(runReceipt(result).latency_ms)],
      [matrixCopy("cost"), result => money(runReceipt(result).cost_usd)],
      [matrixCopy("prepCost"), result => runReceipt(result).preprocessing === null ? "$0.00000" : money(runReceipt(result).preprocessing?.cost_usd)]
    ];
    fields.forEach(([label, value]) => {
      const row = liveNode("tr");
      compareRuns.forEach(result => { const cell = liveNode("td"); cell.append(liveNode("span", label, "comparison-label"), liveNode("strong", value(result))); row.append(cell); });
      body.append(row);
    });
    const actions = liveNode("tr");
    compareRuns.forEach(result => {
      const cell = liveNode("td"), button = liveNode("button", matrixCopy("openResult"), "live-example");
      button.type = "button"; button.disabled = liveBusy || Boolean(result._notRun);
      button.addEventListener("click", () => { ++resultRequest; showResult(result); });
      cell.append(button); actions.append(cell);
    });
    body.append(actions); table.append(head, body); target.append(table);
  }

  async function refreshHistory() {
    if (!$("#history-rows")) return;
    const request = ++historyRequest;
    historyState = "historyLoading";
    renderHistory();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch("/api/history?limit=50", { cache: "no-store", signal: controller.signal });
      if (!response.ok) throw Error("history unavailable");
      const data = await response.json(), rows = Array.isArray(data) ? data : data.rows || data.history || data.items;
      if (!Array.isArray(rows)) throw Error("invalid history");
      if (request !== historyRequest) return;
      historyRows = rows.filter(row => row && validId(String(row.id))).slice(0, 50);
      pendingHistoryRows = pendingHistoryRows.filter(row => !row.finished);
      if (request !== historyRequest) return;
      historyState = historyRows.length ? "" : "historyEmpty";
    } catch {
      if (request === historyRequest) {
        historyState = "historyUnavailable";
        pendingHistoryRows = pendingHistoryRows.filter(row => !row.finished);
      }
    }
    finally { clearTimeout(timer); }
    if (request === historyRequest) renderHistory();
  }

  function historySubject(record) {
    return [record.story ? tryCopy("story", String(record.story).toUpperCase()) : matrixCopy("custom"),
      COPY[pageLanguage].examples[`${record.kind}Title`] || record.kind || "—"].join(" · ");
  }

  function relativeHistoryTime(value, now = Date.now()) {
    const date = new Date(value), age = Math.max(0, now - date.getTime());
    if (!Number.isFinite(date.getTime())) return "—";
    if (age < 60000) return tryCopy("nowTime");
    if (age < 3600000) return tryCopy("minutesAgo", Math.floor(age / 60000));
    if (age < 86400000) return tryCopy("hoursAgo", Math.floor(age / 3600000));
    return date.toLocaleDateString(pageLanguage === "zh" ? "zh-TW" : "en-US", {
      month: "short", day: "numeric", timeZone: "UTC", ...(date.getUTCFullYear() !== new Date(now).getUTCFullYear() ? { year: "numeric" } : {})
    });
  }

  function updateTrySticky() {
    const sidebar = $(".try-sidebar");
    if (sidebar) sidebar.classList.toggle("is-sticky", sidebar.getBoundingClientRect().height + 48 <= (window.innerHeight || 0));
  }

  function renderHistory() {
    const target = $("#history-rows");
    if (!target) return;
    $("#history-status").textContent = matrixCopy(historyState);
    $("#history-refresh").disabled = historyState === "historyLoading";
    const own = pendingHistoryRows.filter(record => !historyRows.some(saved => saved.id === record.id));
    const visible = Math.max(0, historyVisible - own.length);
    target.hidden = !historyRows.length && !own.length;
    $("#history-more").hidden = historyRows.length <= visible;
    target.replaceChildren();
    [...own, ...historyRows.slice(0, visible)].forEach(record => {
      const item = liveNode("li"), row = liveNode("button", "", `history-row history-open${record.pending ? " is-mine" : ""}`);
      row.type = "button";
      const errors = COPY[pageLanguage].matrix.historyErrors;
      const status = record.pending ? tryCopy("running") : record.verdict ? liveVerdict(record.verdict) : errors[record.error] || errors.unknown;
      const verdict = liveNode("span", "", `history-verdict is-${record.pending ? "running" : record.verdict || "unchecked"}${["timeout", "provider_overloaded"].includes(record.error) ? " is-timeout" : ""}`);
      if (record.pending) { const spinner = liveNode("span", "", "try-spinner"); spinner.setAttribute("aria-hidden", "true"); verdict.append(spinner); }
      verdict.append(document.createTextNode(status));
      const subject = historySubject(record), relative = record.pending ? tryCopy("nowTime") : relativeHistoryTime(record.at);
      const detail = liveNode("span", "", "history-description");
      const metrics = [providerLabel(record.provider), ...(record.pending ? [tryCopy("you")] : [duration(record.latency_ms), money(record.cost_usd, 2)])];
      const second = liveNode("span", "", "history-line-two");
      second.append(liveNode("span", providerLabel(record.provider), "history-provider-full"));
      if (record.provider === "meta") second.append(liveNode("span", tryCopy("providerMetaShort"), "history-provider-short"));
      second.append(document.createTextNode(` · ${record.pending ? tryCopy("you") : duration(record.latency_ms)}`));
      if (!record.pending) second.append(liveNode("span", ` · ${money(record.cost_usd, 2)}`, "history-cost"));
      second.append(liveNode("span", ` · ${relative}`, "history-mobile-time"));
      detail.append(liveNode("span", subject, "history-line-one"), second);
      row.title = [Number.isFinite(Date.parse(record.at)) ? new Date(record.at).toISOString() : "", record.device, record.browser,
        Number.isFinite(record.preprocessing_cost_usd) && record.preprocessing_cost_usd > 0 ? `+ ${money(record.preprocessing_cost_usd, 2)} ${liveCopy("preprocessing")}` : ""].filter(Boolean).join(" · ");
      row.setAttribute("aria-label", [subject, status, ...metrics, relative].join(" · "));
      if (!record.pending) {
        row.setAttribute("data-history-row", record.id);
        row.setAttribute("data-history-id", record.id);
        row.setAttribute("aria-haspopup", "dialog");
        row.setAttribute("tabindex", "0");
        row.addEventListener("keydown", event => {
          if (event.target === row && ["Enter", " "].includes(event.key)) { event.preventDefault(); return openHistoryRow(record); }
        });
        row.addEventListener("click", () => { if (!liveBusy) return openHistoryRow(record); });
      } else row.setAttribute("aria-disabled", "true");
      const chevron = liveNode("span", "›", "history-chevron");
      chevron.setAttribute("aria-hidden", "true");
      row.append(verdict, detail, liveNode("span", relative, "history-when"), chevron);
      item.append(row); target.append(item);
    });
    updateTrySticky();
  }

  function renderHistoryDialog() {
    if (!historyModalRecord) return;
    const record = historyModalRecord, result = historyModalResult;
    const receipt = result ? runReceipt(result) : record;
    const header = $("#history-dialog-meta");
    header.replaceChildren();
    header.append(liveNode("span", [historyTime(record.at), record.device, record.browser,
      providerLabel(receipt.provider || record.provider), receipt.model || record.model || liveCopy("notRecorded")].filter(Boolean).join(" · ")));
    const error = result?.error || record.error;
    const verdict = result?.verdict || record.verdict;
    const chip = liveNode("span", error ? COPY[pageLanguage].matrix.historyErrors[error] || COPY[pageLanguage].matrix.historyErrors.unknown
      : verdict ? liveVerdict(verdict) : "—", `history-verdict is-${error ? "unchecked" : verdict || "unchecked"}`);
    header.append(document.createTextNode(" · "), chip,
      liveNode("span", ` · ${duration(receipt.latency_ms)} · ${money(receipt.cost_usd, 2)}`));
    $("#history-dialog-status").textContent = matrixCopy(historyModalState);
    const input = typeof result?.input === "string" ? result.input : result?.input?.text_read;
    $("#history-dialog-input").textContent = input ?? record.input_text ?? "—";
    $("#history-dialog-content").hidden = !result;
    $("#history-dialog-edit").disabled = !result;
    const target = $("#history-dialog-result");
    if (result?.error) {
      target.replaceChildren(liveNode("p", `${liveErrorText(result.error)} · ${result.error}`, "live-error"));
      target.hidden = false;
    } else if (result) renderLiveTrace(result, target);
    else target.replaceChildren();
  }

  function finishHistoryDialog() {
    if (!historyModalRecord) return;
    ++historyDetailRequest;
    historyDetailController?.abort();
    historyDetailController = null;
    historyModalRecord = null;
    historyModalResult = null;
    document.querySelector("body").style.overflow = historyBodyOverflow;
    const row = $(`[data-history-row="${historyReturnId}"]`);
    (row || $("#history-refresh"))?.focus({ preventScroll: true });
  }

  function closeHistoryDialog() {
    const dialog = $("#history-dialog");
    if (dialog.open && typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
    finishHistoryDialog();
  }

  function setupHistoryDialog() {
    const dialog = $("#history-dialog");
    if (!dialog) return;
    $("#history-dialog-close").addEventListener("click", closeHistoryDialog);
    $("#history-dialog-edit").addEventListener("click", () => {
      if (!historyModalResult) return;
      const result = historyModalResult, record = historyModalRecord;
      closeHistoryDialog();
      showResult(result, record);
      editResult();
    });
    dialog.addEventListener("close", () => { if (!dialog.open) finishHistoryDialog(); });
    dialog.addEventListener("cancel", event => { event.preventDefault(); closeHistoryDialog(); });
    dialog.addEventListener("click", event => { if (event.target === dialog) closeHistoryDialog(); });
    dialog.addEventListener("keydown", event => {
      if (event.key === "Escape") { event.preventDefault(); closeHistoryDialog(); }
      if (event.key !== "Tab") return;
      const candidates = new Set(["button", "a[href]", "summary", "[tabindex]"].flatMap(selector => Array.from(dialog.querySelectorAll(selector))));
      const focusable = Array.from(dialog.querySelectorAll("*"))
        .filter(node => candidates.has(node) && !node.disabled && !node.hidden && node.getClientRects?.().length !== 0 && node.getAttribute("tabindex") !== "-1");
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    });
  }

  async function openHistoryRow(record) {
    if (liveBusy || !validId(String(record.id))) return;
    const dialog = $("#history-dialog");
    if (!dialog) return;
    const request = ++historyDetailRequest;
    historyDetailController?.abort();
    const controller = new AbortController();
    historyDetailController = controller;
    if (!historyModalRecord) {
      historyBodyOverflow = document.querySelector("body").style.overflow || "";
      document.querySelector("body").style.overflow = "hidden";
    }
    historyModalRecord = record;
    historyReturnId = record.id;
    historyModalResult = null;
    historyModalState = "historyOpening";
    renderHistoryDialog();
    if (!dialog.open) {
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
    $("#history-dialog-close").focus();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch(`/api/history/${encodeURIComponent(record.id)}`, { cache: "no-store", signal: controller.signal });
      if (!response.ok) throw Error("missing history result");
      const data = await response.json(), result = data.envelope || data;
      if (!result || typeof result !== "object" || (!result.verdict && !result.error)) throw Error("invalid history envelope");
      if (request !== historyDetailRequest) return;
      // Older rows can keep input/receipt fields alongside their envelope.
      const source = { ...record, ...data };
      if (!result.input && typeof source.input_text === "string") result.input = { kind: source.kind, text_read: source.input_text, example_id: source.example_id, story: source.story };
      if (!result.receipt) result.receipt = { provider: result.provider || source.provider, model: result.model || source.model,
        latency_ms: result.latency_ms ?? source.latency_ms, cost_usd: result.cost_usd ?? source.cost_usd,
        preprocessing: result.input?.preprocessing || (source.preprocessing_cost_usd ? { cost_usd: source.preprocessing_cost_usd } : null) };
      historyModalRecord = source;
      historyModalResult = result;
      historyModalState = "";
      renderHistoryDialog();
    } catch {
      if (request === historyDetailRequest) { historyModalState = "historyFailed"; renderHistoryDialog(); }
    } finally { clearTimeout(timer); }
  }

  function editResult() {
    if (liveBusy || !resultContext) return;
    ++resultRequest; ++inputRequest;
    const sourceStory = liveResult.input?.story || resultContext.story;
    if (stories.some(story => story.id === sourceStory)) selectedStory = sourceStory;
    const input = typeof liveResult.input === "object" ? liveResult.input : {};
    const exampleId = input.example_id || resultContext.example_id;
    const asset = examplesIndex.find(row => row.id === exampleId);
    selectedKind = asset?.kind || input.kind || resultContext.kind || "text";
    if (!exampleIds.includes(selectedKind)) selectedKind = "text";
    customText = selectedKind === "text";
    inputLoadState = "";
    $("#live-input").value = resultContext.text;
    if (providers[resultContext.provider]) selectedProvider = resultContext.provider;
    $("#compare-all").checked = false;
    localizeLive();
    $("#live-form").scrollIntoView?.({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    (selectedKind === "text" ? $("#live-input") : $("#live-submit")).focus?.();
  }

  async function selectSavedDemo(kind) {
    savedDemoKind = kind;
    savedLiveDemo = savedDemos[kind] || null;
    $$('[data-saved-demo]').forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.savedDemo === kind));
    });
    const loading = $("#recorded-loading");
    loading.hidden = Boolean(savedLiveDemo);
    if (!savedLiveDemo) {
      $("#recorded-trace").replaceChildren();
      loading.textContent = liveCopy("loading");
    }
    try {
      if (!savedDemos[kind]) {
        const path = kind === "post" ? "/data/live-demo-post.json" : "/data/live-demo.json";
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error("missing trace");
        savedDemos[kind] = await response.json();
      }
      if (savedDemoKind !== kind) return;
      savedLiveDemo = savedDemos[kind];
      loading.hidden = true;
      localizeLive();
    } catch (_error) {
      if (savedDemoKind === kind) loading.textContent = liveCopy("loadingFailed");
    }
  }

  function openLiveTerminals(ids, memberProviders) {
    const host = $("#live-progress"), bar = $("#live-running-bar");
    host.replaceChildren();
    host.hidden = false;
    $("#live-idle").hidden = true;
    const started = Date.now();
    let stopped = false, polling = false, timer = null, lastPoll = -Infinity, pending = Promise.resolve();
    pendingHistoryRows = [{ id: ids[0], pending: true, story: customText ? null : selectedStory,
      kind: customText ? "text" : selectedKind, provider: memberProviders[0] }];
    const panels = ids.map((id, index) => {
      const panel = liveNode("section", "", "live-terminal");
      const header = liveNode("div", "", "terminal-header");
      const dot = liveNode("span", "", "running-dot"); dot.setAttribute("aria-hidden", "true");
      const heading = liveNode("h3", tryCopy("running"));
      const clock = liveNode("span", "0:00", "terminal-clock");
      const pill = liveNode("span", "", "history-verdict"); pill.hidden = true;
      header.append(dot, heading, clock, pill);
      const status = liveNode("p", "", "terminal-status");
      status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
      const stages = liveNode("div", "", "terminal-stages");
      const chips = Array.from({ length: 6 }, (_, stage) => {
        const chip = liveNode("span"); chip.dataset.active = String(stage === 0);
        const mark = liveNode("i"); mark.setAttribute("aria-hidden", "true");
        chip.append(mark, liveNode("span", tryCopy(`stage${stage}`), "stage-label-full"));
        if ([2, 4].includes(stage)) chip.append(liveNode("span", tryCopy(`stage${stage}Short`), "stage-label-short"));
        stages.append(chip); return chip;
      });
      const metrics = liveNode("div", "", "terminal-metrics"); metrics.hidden = true;
      const footer = liveNode("div", "", "terminal-footer");
      const log = liveNode("details", "", "terminal-log"); log.open = true;
      const summary = liveNode("summary", tryCopy("serverLog"));
      const lines = liveNode("pre", "", "terminal-lines");
      // Protocol strings are only text nodes; no server text is ever parsed as HTML.
      lines.setAttribute("translate", "no");
      log.append(summary, lines);
      const link = liveNode("a", tryCopy("viewResult"), "terminal-result-link");
      link.href = "#live-result"; link.hidden = true;
      link.addEventListener("click", () => {
        const result = compareRuns.find(run => runReceipt(run).provider === memberProviders[index]);
        if (result && !result._notRun) { ++resultRequest; showResult(result); }
      });
      footer.append(log, link);
      panel.append(header, status, stages, metrics, footer); host.append(panel);
      return { id, provider: memberProviders[index], panel, dot, heading, pill, status, summary, log, clock, chips, lines, metrics, link,
        next: 0, done: false, count: 0, stage: 0, step: null, sawTools: false, result: null };
    });
    const elapsed = () => {
      const seconds = Math.floor((Date.now() - started) / 1000);
      return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    };
    const current = () => panels.find(panel => !panel.done) || panels[panels.length - 1];
    const stageSentence = panel => COPY[pageLanguage].tryUI.stageSentences[panel.stage] +
      ([1, 3].includes(panel.stage) && panel.step ? tryCopy("modelStep", panel.step) : "");
    const updateRunningBar = () => {
      const bounds = $("#live-now").getBoundingClientRect();
      bar.hidden = stopped || !window.matchMedia("(max-width: 959px)").matches ||
        (bounds.bottom > 0 && bounds.top < (window.innerHeight || 900));
      bar.querySelector(".running-bar-stage").textContent = stageSentence(current());
      bar.querySelector(".running-bar-clock").textContent = elapsed();
    };
    const render = () => {
      panels.forEach(panel => {
        const result = panel.result, failed = Boolean(result?.error || result?._notRun);
        panel.heading.textContent = stopped ? tryCopy("done") : tryCopy("running");
        panel.clock.textContent = elapsed(); panel.clock.hidden = stopped;
        panel.dot.hidden = stopped;
        panel.pill.hidden = !stopped;
        if (stopped) {
          panel.pill.textContent = result?._notRun ? matrixCopy("notRun") : failed ? COPY[pageLanguage].matrix.historyErrors[result.error] || COPY[pageLanguage].matrix.historyErrors.unknown : liveVerdict(result?.verdict);
          panel.pill.className = `history-verdict is-${failed ? "unchecked" : result?.verdict || "unchecked"}${["timeout", "provider_overloaded"].includes(result?.error) ? " is-timeout" : ""}`;
        }
        const receipt = result ? runReceipt(result) : null;
        const time = duration(receipt?.latency_ms ?? Date.now() - started);
        const sentence = stopped ? failed ? result?._notRun ? matrixCopy("notRun") : liveErrorText(result.error) : tryCopy("finished", time) : stageSentence(panel);
        if (panel.status.textContent !== `${providerLabel(panel.provider)} · ${sentence}`)
          panel.status.replaceChildren(liveNode("strong", providerLabel(panel.provider)), document.createTextNode(` · ${sentence}`));
        panel.chips.forEach((chip, index) => {
          chip.dataset.active = String(index === panel.stage);
          const done = (stopped && !failed) || index < panel.stage;
          chip.dataset.done = String(done);
          chip.children[0].textContent = done ? "✓" : "";
          chip.children[1].textContent = tryCopy(`stage${index}`);
          if (chip.children[2]) chip.children[2].textContent = tryCopy(`stage${index}Short`);
        });
        panel.summary.textContent = stopped ? tryCopy("log", panel.count) : `${tryCopy("serverLog")} · ${tryCopy("lines", panel.count)}`;
        panel.link.textContent = tryCopy("viewResult");
        panel.link.hidden = !stopped || !result || Boolean(result._notRun) || (!result.verdict && !result.events?.length);
        panel.metrics.hidden = !stopped || failed;
        if (stopped && !failed) {
          panel.metrics.replaceChildren();
          [["time", time], ["cost", money(receipt?.cost_usd, 2)], ["claims", String(result?.claims?.length ?? 0)]].forEach(([key, value]) => {
            const tile = liveNode("div"); tile.append(liveNode("span", tryCopy(key)), liveNode("b", value)); panel.metrics.append(tile);
          });
        }
      });
      if (!stopped && pendingHistoryRows[0]?.provider !== current().provider) {
        pendingHistoryRows[0].provider = current().provider;
        renderHistory();
      }
      updateRunningBar();
      updateTrySticky();
    };
    liveTerminalView = render;
    window.addEventListener?.("scroll", updateRunningBar, { passive: true });
    window.addEventListener?.("resize", updateRunningBar);
    // Display-only tidy of the server log line; stage detection above reads the raw text.
    const terminalDisplay = text => text.replace(/\s{2,}/g, " ").replace(/\bstep=(\d+)/g, "step $1")
      .replace(/\b\d{7,}\b/g, digits => Number(digits).toLocaleString("en-US"));
    const append = (panel, data) => {
      if (!Array.isArray(data.lines) || typeof data.done !== "boolean" || !Number.isSafeInteger(data.next)) return;
      for (const line of data.lines) {
        if (!Number.isFinite(line.t_s) || typeof line.text !== "string") continue;
        const text = line.text;
        if (text.startsWith("tool_")) { panel.stage = 2; panel.sawTools = true; }
        else if (text.startsWith("model")) {
          panel.stage = panel.sawTools ? 3 : 1;
          panel.step = text.match(/step[= ]+(\d+)/)?.[1] || null;
        } else if (text.startsWith("program_check")) panel.stage = 4;
        else if (text.startsWith("verdict")) panel.stage = 5;
        else if (text.startsWith("error")) panel.serverError = text.split(/\s+/)[1] || null;
        const row = liveNode("span", "", "terminal-line");
        row.append(liveNode("span", `+${line.t_s.toFixed(1)} s `, "terminal-time"), document.createTextNode(terminalDisplay(text)));
        panel.lines.append(row);
        panel.count++;
      }
      panel.next = data.next; panel.done = data.done;
      render();
      panel.lines.scrollTop = panel.lines.scrollHeight;
    };
    const poll = async panel => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      try {
        const response = await fetch(`/api/progress/${panel.id}?after=${panel.next}`, { cache: "no-store", signal: controller.signal });
        if (response.ok) append(panel, await response.json());
        else if (response.status !== 404) panel.done = true;
      } catch { panel.done = true; }
      finally { clearTimeout(timeout); }
    };
    const tick = () => {
      if (stopped) return;
      render();
      const panel = panels.find(item => !item.done);
      // Shared network cadence keeps compare + budget/history below 30/IP/min.
      // The clock/stage UI ticks every 700 ms; no overlapping progress fetches.
      if (panel && !polling && Date.now() - lastPoll >= 3000) {
        lastPoll = Date.now(); polling = true;
        pending = poll(panel);
        pending.finally(() => { lastPoll = Date.now(); polling = false; });
      }
      timer = setTimeout(tick, 700);
    };
    render();
    timer = setTimeout(tick, 700);
    return async (finalRead, results) => {
      stopped = true; clearTimeout(timer); bar.hidden = true;
      window.removeEventListener?.("scroll", updateRunningBar);
      window.removeEventListener?.("resize", updateRunningBar);
      await pending;
      // One last read even when the reply was empty: a proxy "unavailable" can hide the server's own error.
      await Promise.allSettled(panels.filter(panel => finalRead || !panel.done).map(panel => poll(panel)));
      panels.forEach((panel, index) => {
        panel.result = results.find(result => runReceipt(result).provider === panel.provider) || results[index] || { error: "unavailable" };
        if (panel.result.error === "unavailable" && panel.serverError && panel.serverError !== "unavailable")
          panel.result = { ...panel.result, error: panel.serverError };
        const failed = Boolean(panel.result.error || panel.result._notRun);
        panel.log.open = failed;
        if (!failed) panel.stage = 5;
      });
      pendingHistoryRows.forEach(row => { row.finished = true; });
      render();
      return panels.map(panel => panel.result?.error || null);
    };
  }

  function setupLive() {
    const form = $("#live-form");
    if (!form) return;
    const input = $("#live-input"), submit = $("#live-submit"), password = $("#live-password");
    password.value = "";
    try { password.value = sessionStorage.getItem(LIVE_PASSWORD_KEY) || ""; } catch { /* Storage may be blocked. */ }
    input.addEventListener("input", () => { ++inputRequest; customText = true; inputLoadState = ""; renderMatrix(); renderLiveBudget(); });
    $("#live-example").addEventListener("click", () => selectMatrix(selectedStory, "text"));
    $$('[data-story-slot]').forEach((button, index) => button.addEventListener("click", () => selectMatrix(stories[index].id, selectedKind)));
    $$('[data-input-kind]').forEach((button, index) => {
      button.addEventListener("click", () => selectMatrix(selectedStory, button.dataset.inputKind));
      button.addEventListener("keydown", event => {
        const keys = { ArrowRight: (index + 1) % exampleIds.length, ArrowLeft: (index + exampleIds.length - 1) % exampleIds.length,
          Home: 0, End: exampleIds.length - 1 };
        if (keys[event.key] === undefined || liveBusy) return;
        event.preventDefault();
        const next = exampleIds[keys[event.key]];
        selectMatrix(selectedStory, next);
        $(`#input-tab-${next}`).focus();
      });
    });
    $$('#live-form input[name="provider"]').forEach(radio => radio.addEventListener("change", () => {
      if (!liveBusy && providers[radio.value]) {
        selectedProvider = radio.value;
        if (["budget_exhausted", "total_budget_exhausted", "credit_exhausted"].includes(liveStatus)) liveStatus = "";
        localizeLive();
      }
    }));
    $("#compare-all").addEventListener("change", localizeLive);
    $("#example-saved").addEventListener("click", () => selectExampleSaved());
    $("#result-edit").addEventListener("click", editResult);
    $("#history-refresh").addEventListener("click", refreshHistory);
    $("#history-more").addEventListener("click", () => { historyVisible += 10; renderHistory(); });
    window.addEventListener?.("resize", updateTrySticky);
    $("#live-running-bar").addEventListener("click", () => $("#live-now").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" }));
    setupHistoryDialog();
    $$('[data-saved-demo]').forEach(button => button.addEventListener("click", () => selectSavedDemo(button.dataset.savedDemo)));

    const runLive = async () => {
      if (submit.disabled || liveBusy) return;
      const attemptedPassword = password.value;
      if (!attemptedPassword) { liveStatus = "unauthorized"; localizeLive(); password.focus(); return; }
      const asset = selectedAsset(), exampleId = customText ? null : asset?.id;
      const sentText = input.value.trim();
      if (!exampleId && (!sentText || Array.from(sentText).length > 600)) { liveStatus = "invalid_input"; localizeLive(); return; }
      const compare = $("#compare-all").checked;
      const provider = selectedProvider;
      const clientRunId = crypto.randomUUID();
      const memberProviders = compare ? Object.keys(providers) : [provider];
      const runIds = memberProviders.map((_, index) => clientRunId.slice(0, -1) +
        ((parseInt(clientRunId.slice(-1), 16) + index) % 16).toString(16));
      const finishTerminals = openLiveTerminals(runIds, memberProviders);
      let postComplete = false;
      const request = ++resultRequest;
      rateLimitReset = null;
      liveBusy = true;
      form.setAttribute("aria-busy", "true");
      liveResult = null; compareRuns = []; exampleSavedStatus = "";
      $("#live-result").hidden = true;
      liveStatus = compare ? "comparing" : exampleId && selectedKind !== "text" ? "mediaPending" : "pending";
      localizeLive();
      const controller = new AbortController();
      // Pages fetches comparison members sequentially, each with its own origin timeout.
      const timer = setTimeout(() => controller.abort(), compare ? 290000 : 100000);
      try {
        const response = await fetch(compare ? "/api/compare" : exampleId ? "/api/check-example" : "/api/check", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...(exampleId ? { example_id: exampleId } : { text: sentText }), password: attemptedPassword, client_run_id: clientRunId,
            ...(compare ? { providers: Object.keys(providers) } : { provider }) }), signal: controller.signal, cache: "no-store"
        });
        const result = await response.json();
        postComplete = !!(result.receipt || result.events?.length || result.runs?.length);
        if (request !== resultRequest) return;
        if (["rate_limited", "auth_rate_limited"].includes(result.error) && Number.isFinite(result.retry_after) && result.retry_after >= 0)
          rateLimitReset = Date.now() + result.retry_after * 1000;
        if (result.budget) liveBudget = result.budget;
        if (compare && Array.isArray(result.runs) && result.runs.length) {
          const runs = result.runs.slice(0, 3);
          compareRuns = Object.keys(providers).map((id, index) => {
            const run = runs.find(item => runReceipt(item).provider === id) ||
              (runs[index] && !runReceipt(runs[index]).provider ? runs[index] : null);
            return run ? { ...run, receipt: { ...runReceipt(run), provider: id } } : { _notRun: true, receipt: { provider: id } };
          });
          const first = compareRuns.find(run => !run.error && !run._notRun) || compareRuns.find(run => !run._notRun);
          if (first) {
            if (!first.input && !exampleId) first.input = { kind: "text", text_read: sentText };
            showResult(first, { provider, input_text: sentText });
          }
        } else if (!compare && result && typeof result === "object") {
          if (!result.input && !exampleId) result.input = { kind: "text", text_read: sentText };
          if (response.ok || result.events?.length || result.receipt) showResult(result, { provider, input_text: sentText });
        }
        if (!response.ok || result.error) {
          liveStatus = result.error || "unavailable";
          if (response.status === 401) {
            password.value = "";
            try { sessionStorage.removeItem(LIVE_PASSWORD_KEY); } catch { /* Storage may be blocked. */ }
          }
        } else {
          if (compare && !compareRuns.length) throw Error("missing comparison runs");
          liveStatus = "complete";
          try { sessionStorage.setItem(LIVE_PASSWORD_KEY, attemptedPassword); } catch { /* Check succeeded without storage. */ }
        }
      } catch (error) { if (request === resultRequest) liveStatus = error.name === "AbortError" ? "timeout" : "unavailable"; }
      finally {
        clearTimeout(timer);
        const serverErrors = await finishTerminals(postComplete, compareRuns.length ? compareRuns : [liveResult || { error: liveStatus, receipt: { provider } }]);
        if (!compare && liveStatus === "unavailable" && serverErrors?.[0] && serverErrors[0] !== "unavailable") liveStatus = serverErrors[0];
        await Promise.allSettled([refreshLiveBudget(), refreshHistory()]);
        liveBusy = false;
        form.setAttribute("aria-busy", "false");
        localizeLive();
      }
    };
    form.addEventListener("submit", event => { event.preventDefault(); return runLive(); });
    loadExamples();
    refreshLiveBudget();
    refreshHistory();
    document.addEventListener("visibilitychange", () => { if (!document.hidden) refreshLiveBudget(); });
    selectSavedDemo("post");
  }

  function readLanguage() {
    return document.documentElement.lang === "zh-Hant" ? "zh" : "en";
  }

  function getCopy(path) {
    return path.split(".").reduce((value, key) => value && value[key], COPY[pageLanguage]);
  }

  function applyCopy() {
    const copy = COPY[pageLanguage];
    document.documentElement.lang = pageLanguage === "zh" ? "zh-Hant" : "en";
    document.title = copy.metaTitle;
    const description = document.querySelector('meta[name="description"]');
    if (description) description.setAttribute("content", copy.metaDescription);

    $$('[data-i18n]').forEach((element) => {
      const value = getCopy(element.dataset.i18n);
      if (typeof value === "string") element.textContent = value;
      if (typeof value === "function") {
        const count = siteData && siteData.eval ? siteData.eval.claim_count : null;
        element.textContent = value(count);
      }
    });

    $$('[data-i18n-aria]').forEach((element) => {
      const value = getCopy(element.dataset.i18nAria);
      if (typeof value === "string") element.setAttribute("aria-label", value);
    });
    $$('[data-i18n-alt]').forEach((element) => {
      const value = getCopy(element.dataset.i18nAlt);
      if (typeof value === "string") element.setAttribute("alt", value);
    });

    $$('[data-language]').forEach((link) => {
      const active = link.dataset.language === pageLanguage;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });

    $$('[data-example]').forEach((button) => {
      const active = button.dataset.example === exampleLanguage;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });

    const closeButton = $("#filing-dialog-close");
    if (closeButton) closeButton.setAttribute("aria-label", getCopy("filing.close"));

    localizeLive();
    if (siteData) {
      renderStampScene();
      if (document.documentElement.dataset.evidenceTour !== undefined) renderExample(siteData.examples[exampleLanguage]);
      renderChart(siteData);
      if (document.documentElement.dataset.evidenceTour !== undefined) {
        renderPosthocRerun(siteData);
        renderResearch(siteData);
      }
      const dialog = $("#filing-dialog");
      if (activeFilingClaim && dialog && dialog.open) renderFilingDialog(activeFilingClaim);
    }
  }

  function renderStampScene() {
    if (!$("#stamp-scene")?.querySelector(".stamp-stage") || !siteData.stamp_cards || !siteData.stamp_cards.length) return;
    if (!stampConveyor) stampConveyor = createStampConveyor(siteData.stamp_cards);
    stampConveyor.localize();
  }

  function createStampConveyor(cards) {
    const scene = $("#stamp-scene");
    const stage = scene.querySelector(".stamp-stage");
    const track = $("#stamp-track");
    const filingContent = $("#stamp-filing-content");
    const filingState = scene.querySelector(".stamp-filing-state");
    const filingBox = scene.querySelector(".stamp-filing-box");
    const filingTitle = scene.querySelector(".stamp-filing-state-title");
    const filingExplanation = scene.querySelector(".stamp-filing-state-explanation");
    const filingKind = scene.querySelector(".stamp-filing-state-kind");
    const caption = scene.querySelector(".stamp-caption-beat");
    const captionVerdict = scene.querySelector(".stamp-caption-verdict");
    const pauseIcon = scene.querySelector(".stamp-pause-icon");
    const pauseLabel = scene.querySelector(".stamp-pause-label");
    const spotlight = scene.querySelector(".stamp-spotlight");
    const stageDim = spotlight.querySelector(".stamp-stage-dim");
    const paperDim = spotlight.querySelector(".stamp-paper-dim");
    const paperHole = spotlight.querySelector(".stamp-stage-hole-paper");
    const filingDim = spotlight.querySelector(".stamp-filing-dim");
    const filingVignette = spotlight.querySelector("#stamp-filing-vignette");
    const flash = spotlight.querySelector(".stamp-impact-flash");
    const letterbox = spotlight.querySelector(".stamp-letterbox");
    const bars = [spotlight.querySelector(".stamp-letterbox-top"), spotlight.querySelector(".stamp-letterbox-bottom")];
    const lights = Object.fromEntries(["post", "filing", "year"].map((name) => {
      const group = spotlight.querySelector(`.stamp-beam-${name}`);
      return [name, { group, cone: group.querySelector(".stamp-beam-cone"), haze: group.querySelector(".stamp-beam-haze"),
        gradient: spotlight.querySelector(`#stamp-light-${name}`) }];
    }));
    const pools = Object.fromEntries(["post", "row", "compare", "year"].map((name) => [name, spotlight.querySelector(`.stamp-pool-${name}`)]));
    const holes = Object.fromEntries(["post", "row", "compare", "year"].map((name) => [name,
      [spotlight.querySelector(`.stamp-dim-hole-${name}`), spotlight.querySelector(`.stamp-ink-hole-${name}`)]]));
    const dust = Array.from(spotlight.querySelectorAll(".stamp-dust"));
    const progress = Array.from(scene.querySelectorAll(".stamp-progress li"));
    const next = scene.querySelector(".stamp-ticker-list");
    const list = $("#stamp-static-list");
    const pause = $("#stamp-pause");
    const robot = scene.querySelector(".stamp-robot");
    const robotBand = scene.querySelector(".stamp-robot-band");
    const floorShadow = scene.querySelector(".stamp-floor-shadow");
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const phone = window.matchMedia("(max-width: 639px)");
    // One deterministic clock drives every beat and both layouts. Short reviews
    // have their own slots; cumulative starts keep seeking exact through the loop.
    const CHECKABLE = 8000;
    const UNCHECKABLE = 5400;
    const READ = 700;
    const REACH = 1500;
    const FIND = 2300;
    const COMPARE = 3700;
    const WINDUP = 4500;
    const STRIKE = 4800;
    const REACT = 5300;
    const EXIT = 6400;
    const REST = 7200;
    const UNKNOWN_STRIKE = 3000;
    const UNKNOWN_EXIT = 4600;
    const FADE = 120;
    const LEDGER_STAGGER = 200;
    const FIND_SWEEP = 600;
    const FIND_LOCK = FIND + FIND_SWEEP;
    const INITIAL = FIND_LOCK + FADE;
    const BLOOM = 180;
    const AMBER_SWEEP = 660;
    const LETTERBOX = 12;
    const LETTERBOX_EASE = 250;
    const FLASH = 80;
    const BURST = 400;
    const DIM_LIFT = 250;
    const POOL_PAD = 6;
    const VISOR_RADIUS = 2;
    const DUST_PERIOD = 2100;
    const FLOAT_PERIOD = 1600;
    const THRUSTER_FRAME = 80;
    const THRUSTER_BURST = 250;
    const DIP_DOWN = 60;
    const DIP_RECOVER = 160;
    // Image-pixel anchors from H/manifest.json, before CSS mirroring. Every
    // body uses one scale and a shared nozzle baseline; effects stay separate.
    const POSE_CANVAS = [704, 744];
    const POSE_ANCHORS = Object.freeze({
      idle: { visor: [415, 270], nozzle: [352, 520] }, inspect: { visor: [414, 304], nozzle: [352, 520] },
      reach: { visor: [415, 300], nozzle: [352, 520] }, present: { visor: [404, 285], nozzle: [352, 520] },
      point: { visor: [421, 280], nozzle: [352, 520] }, think: { visor: [416, 270], nozzle: [352, 520] },
      stamp: { visor: [412, 300], nozzle: [352, 520] }, "stamp-down": { visor: [417, 335], nozzle: [352, 520] },
      approve: { visor: [412, 276], nozzle: [352, 520] }, concern: { visor: [412, 286], nozzle: [352, 520] },
      shrug: { visor: [391, 280], nozzle: [352, 520] }
    });
    const POSE_VISORS = Object.fromEntries(Object.entries(POSE_ANCHORS).map(([name, anchors]) =>
      [name, anchors.visor.map((value, axis) => value / POSE_CANVAS[axis])]));
    const checkable = (card) => Boolean(card.excerpt) && card.status === "verified" && ["supported", "contradicted"].includes(card.verdict);
    const durations = cards.map((card) => checkable(card) ? CHECKABLE : UNCHECKABLE);
    const starts = durations.reduce((times, duration) => [...times, times[times.length - 1] + duration], [0]);
    const loop = starts.pop();
    const floatCycles = Math.round(loop / FLOAT_PERIOD);
    const clamp = (value) => Math.max(0, Math.min(1, value));
    const easeOut = (value) => 1 - Math.pow(1 - clamp(value), 3);
    const fadeIn = (age, at) => clamp((age - at) / FADE);
    const compact = (value) => (value || "").replace(/(-?\d+\.\d+)([BM%]?)/g,
      (_match, number, unit) => unit ? `${Number(number).toFixed(1)}${unit}` : String(Number(number)));
    const poseFallbacks = { reach: "present", point: "present", think: "inspect", "stamp-down": "stamp",
      approve: "idle", concern: "idle", shrug: "idle" };
    const facing = { idle: "front", inspect: "post", present: "filing", reach: "filing", point: "filing",
      think: "front", stamp: "post", "stamp-down": "post", approve: "front", concern: "front", shrug: "front" };
    // Begin with the post and all filing rows visible. Absolute seek times and
    // subsequent loop boundaries stay unchanged, including explicit ?stamp-t=0.
    let elapsed = INITIAL;
    let frame = null;
    let lastFrame = null;
    let inView = false;
    let userPaused = false;
    let assetsLoaded = false;
    let cardWidth = 0;
    let queuedIndex = -1;
    let sizeKey = "";
    let geometryKey = "";
    let geometry = null;

    function element(tag, className, text) {
      const node = document.createElement(tag);
      node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }

    function setText(node, text) {
      if (node.textContent !== text) node.textContent = text;
    }

    function svg(tag, attributes = {}) {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, String(value)));
      return node;
    }

    // Luminance masks tint the opaque black VFX plates without filters. No href
    // is assigned until playback/seek starts and that individual asset loads.
    function makeFxLayers() {
      const defs = spotlight.querySelector("defs"), sources = {}, fields = [];
      function image(asset, attributes = {}) {
        const node = svg("image", { "data-texture": asset, preserveAspectRatio: "none", ...attributes });
        (sources[asset] ||= []).push(node);
        return node;
      }
      function tiled(asset, size, id) {
        const pattern = svg("pattern", { id, patternUnits: "userSpaceOnUse", width: size, height: size });
        pattern.append(image(asset, { width: size, height: size }));
        defs.append(pattern);
        return pattern;
      }
      function emissive(id, asset, kind, parent, tileSize = 0) {
        const mask = svg("mask", { id, maskUnits: "userSpaceOnUse", maskContentUnits: "userSpaceOnUse", "mask-type": "luminance" });
        const pattern = tileSize ? tiled(asset, tileSize, `${id}-tile`) : null;
        const source = pattern ? svg("rect", { fill: `url(#${id}-tile)` }) : image(asset);
        mask.append(source);
        defs.append(mask);
        const plate = svg("rect", { class: `stamp-fx-screen stamp-fx-${kind}`, mask: `url(#${id})` });
        parent.append(plate);
        fields.push(mask, plate);
        if (pattern) fields.push(source);
        return { mask, source, plate, pattern, group: parent };
      }
      Object.entries(lights).forEach(([name, beam]) => {
        const clip = svg("clipPath", { id: `stamp-fx-clip-${name}`, clipPathUnits: "userSpaceOnUse" });
        beam.clip = svg("polygon");
        clip.append(beam.clip);
        defs.append(clip);
        const volume = svg("g", { "clip-path": `url(#stamp-fx-clip-${name})` });
        beam.group.append(volume);
        beam.texture = emissive(`stamp-fx-cone-${name}`, "beam-cone", "cone", volume);
        beam.motes = emissive(`stamp-fx-dust-${name}`, "dust-motes", "dust", volume, 512);
      });
      const poolTextures = Object.fromEntries(Object.keys(pools).map((name) => [name,
        emissive(`stamp-fx-pool-${name}`, "beam-pool", "pool", lights[name === "post" || name === "year" ? name : "filing"].group)]));
      const flare = emissive("stamp-fx-flare", "lens-flare", "flare", spotlight.querySelector(".stamp-fx-flare-wrap"));
      const burst = emissive("stamp-fx-burst", "impact-burst", "burst", spotlight.querySelector(".stamp-fx-burst-wrap"));
      // Keep the contact mark itself legible; the burst radiates around its ink.
      burst.exclusion = svg("rect", { fill: "black" });
      burst.mask.append(burst.exclusion);
      const atmosphere = spotlight.querySelector(".stamp-fx-atmosphere");
      tiled("film-grain", 256, "stamp-fx-grain-tile");
      const grain = svg("rect", { class: "stamp-fx-grain", fill: "url(#stamp-fx-grain-tile)" });
      const vignette = image("vignette", { class: "stamp-fx-vignette" });
      atmosphere.append(grain, vignette);
      return { sources, fields, pools: poolTextures, flare, burst, grain, vignette };
    }
    const fx = makeFxLayers();
    const polishImages = [];

    function polishImage(path, className, width, height, isStatic = false) {
      const image = element("img", `stamp-polish-art ${className}`);
      image.alt = "";
      image.width = width;
      image.height = height;
      image.loading = "lazy";
      image.decoding = "async";
      path = path.startsWith("/") ? path : "/" + path;
      image.dataset.src = path;
      // Image slots have fixed dimensions. Re-measure the actual text targets
      // after decoding too, including the intrinsic phone maxima.
      image.addEventListener("load", () => { sizeKey = ""; geometryKey = ""; measure(); });
      image.addEventListener("error", () => image.classList.toggle("is-unavailable", true));
      if (isStatic) image.src = path;
      else polishImages.push(image);
      return image;
    }

    function icon(name) {
      const paths = {
        reply: "M4 4h16v11H9l-5 5V4Z",
        repost: "m4 8 4-4 4 4M8 4v12h11m1 0-4 4-4-4m4 4V8H5",
        like: "M12 20 4 12C-2 5 7 1 12 7c5-6 14-2 8 5l-8 8Z",
        views: "M3 20V12m6 8V7m6 13V3m6 17v-9",
        audience: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM3 12h18M12 3c-5 5-5 13 0 18 5-5 5-13 0-18Z"
      };
      const graphic = svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" });
      graphic.append(svg("path", { d: paths[name] }));
      return graphic;
    }

    function makeInput(card, isStatic) {
      const data = card.input_media;
      const timestamp = data && typeof data.timestamp === "string" && /^\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?$/.test(data.timestamp);
      const thumbnail = data && typeof data.thumbnail === "string" && /^(?:img|media)\/(?!.*(?:\.\.|\/\/))[\w./-]+\.(?:webp|png|jpe?g|avif)$/.test(data.thumbnail);
      const transcript = data && data.transcript && ["en", "zh"].every((language) => typeof data.transcript[language] === "string" && data.transcript[language].trim());
      const waveform = data && Array.isArray(data.waveform) && data.waveform.length > 1 && data.waveform.length <= 128 &&
        data.waveform.every((sample) => Number.isFinite(sample) && sample >= 0 && sample <= 1);
      // Missing media payloads fall back to Text; media never becomes SEC evidence.
      const kind = card.input_kind === "audio" && timestamp && transcript && waveform ? "audio" :
        card.input_kind === "video" && timestamp && thumbnail ? "video" :
        card.input_kind === "screenshot" && thumbnail ? "screenshot" : "text";
      const badge = element("span", "stamp-input-badge");
      badge.dataset.inputKind = kind;
      if (kind === "text") return { badge, kind, body: null };
      const body = element("div", `stamp-input-media stamp-input-${kind}`);
      if (kind === "audio") {
        const strip = element("div", "stamp-waveform");
        strip.setAttribute("aria-hidden", "true");
        data.waveform.forEach((sample) => {
          const bar = element("span", "");
          bar.style.setProperty("--sample", String(sample));
          strip.append(bar);
        });
        body.append(strip);
      } else body.append(polishImage(data.thumbnail, "stamp-frame", 320, 180, isStatic));
      const timing = timestamp && kind !== "screenshot" ? element("p", "stamp-media-time") : null;
      if (timing) body.append(timing);
      const quote = kind === "audio" ? element("blockquote", "stamp-transcript") : null;
      if (quote) body.append(quote);
      const disclosure = data.disclosure ? element("p", "stamp-media-disclosure") : null;
      const limit = data.limit ? element("p", "stamp-media-limit") : null;
      if (disclosure) body.append(disclosure);
      if (limit) body.append(limit);
      return { badge, kind, body, quote, timing, disclosure, limit, transcript: data.transcript };
    }

    function paperDetails(parent, isStatic = false) {
      const grain = polishImage("/img/polish/paper-grain.webp", "stamp-paper-grain", 256, 256, isStatic);
      grain.addEventListener("load", () => parent.classList.toggle("has-paper-grain", true));
      parent.append(grain,
        polishImage("/img/polish/stack-edge.webp", "stamp-stack-edge", 384, 96, isStatic),
        polishImage("/img/polish/paperclip.webp", "stamp-paperclip", 96, 160, isStatic));
    }
    paperDetails(filingBox);

    // Two effect layers follow both nozzles during the 120 ms body cross-fade.
    // All seven images share a top attachment at (80, 20) on a 160px canvas.
    const thrusters = ["previous", "current"].map((name) => {
      const layer = element("div", `stamp-thruster stamp-thruster-${name}`);
      const frames = [...Array(6).keys(), "burst"].map((frame) => {
        const image = element("img", "stamp-thruster-frame");
        image.alt = "";
        image.width = 160;
        image.height = 160;
        image.loading = "lazy";
        image.decoding = "async";
        image.dataset.frame = String(frame);
        image.addEventListener("error", () => { image.dataset.failed = "true"; paint(); });
        layer.append(image);
        return image;
      });
      robot.append(layer);
      return { layer, frames };
    });

    const poses = Object.fromEntries(Object.keys(facing).map((name) => {
      const image = element("img", `stamp-robot-pose stamp-robot-${name}`);
      image.alt = "";
      image.width = POSE_CANVAS[0];
      image.height = POSE_CANVAS[1];
      // Phone poses must be ready even when a taller translated hero starts
      // them below the fold. They still paint from the same scene clock.
      image.loading = phone.matches ? "eager" : "lazy";
      image.decoding = "async";
      image.dataset.pose = name;
      image.dataset.facing = facing[name];
      image.addEventListener("error", () => {
        const fallback = poseFallbacks[name];
        if (fallback && image.dataset.asset !== fallback) {
          image.dataset.asset = fallback;
          image.src = `/img/auditor/H/${fallback}.webp`;
          geometryKey = "";
          measure();
        }
      });
      robot.append(image);
      return [name, image];
    }));

    function loadAssets() {
      if (assetsLoaded || motion.matches) return;
      assetsLoaded = true;
      polishImages.forEach((image) => { image.src = image.dataset.src; });
      Object.entries(poses).forEach(([name, image]) => {
        image.dataset.asset = name;
        image.addEventListener("load", () => {
          if (image.decode) image.decode().catch(() => {});
          geometryKey = "";
          measure();
        });
        image.src = `/img/auditor/H/${name}.webp`;
      });
      thrusters.forEach(({ frames }) => frames.forEach((image) => {
        image.src = `/img/auditor/H/thruster-${image.dataset.frame}.webp`;
      }));
      // A failed ink texture leaves solid, readable stamp text.
      const ink = element("img", "");
      ink.decoding = "async";
      ink.addEventListener("load", () => scene.classList.toggle("has-stamp-ink", ink.naturalWidth > 0));
      ink.addEventListener("error", () => scene.classList.remove("has-stamp-ink"));
      ink.src = "/img/stamp-ink.webp";
      Object.entries(fx.sources).forEach(([name, sources]) => {
        const image = element("img", "stamp-fx-preload"), url = `/img/fx/${name}.webp`;
        image.decoding = "async";
        image.dataset.texture = name;
        image.addEventListener("load", () => sources.forEach((node) => node.setAttribute("href", url)));
        image.addEventListener("error", () => sources.forEach((node) => node.removeAttribute("href")));
        image.src = url;
      });
    }

    function makePassage(card, isStatic) {
      if (!card.excerpt) return null;
      const source = card.excerpt;
      const passage = element("div", "stamp-passage");
      passage.classList.toggle("stamp-release", source.type === "release");
      passage.dataset.cardId = card.id;
      const header = element("div", "stamp-passage-header");
      const authority = element("p", "stamp-filing-authority", "UNITED STATES SECURITIES AND EXCHANGE COMMISSION");
      header.append(authority);
      const formLine = element("div", "stamp-form-line");
      const dateStamp = element("span", "stamp-filing-date");
      const filedDate = element("time", "");
      filedDate.dateTime = source.filed;
      dateStamp.append(polishImage("/img/polish/ink-ring.webp", "stamp-date-ring", 256, 128, isStatic), filedDate);
      formLine.append(element("p", "stamp-passage-meta", source.type === "release" ? "8-K · Item 2.02 · Ex 99.1" : `FORM ${source.form}`), dateStamp);
      header.append(formLine);
      header.append(element("p", "stamp-passage-company", source.company));
      if (source.headline) header.append(element("p", "stamp-release-headline", source.headline));
      if (source.section_title) header.append(element("p", "stamp-passage-section", source.section_title));
      const period = element("p", "stamp-passage-period");
      header.append(period);
      const details = element("div", "stamp-passage-details");
      const row = element(source.type === "release" ? "blockquote" : "p", "stamp-passage-row");
      const fact = element("mark", "stamp-fact");
      const sweep = element("span", "stamp-amber-sweep");
      fact.append(sweep, element("strong", "", source.value));
      if (source.type === "table") {
        row.append(element("span", "stamp-row-label", source.row_label), fact);
      } else {
        const offset = source.highlight_ranges ? source.highlight_ranges[0][0] : source.text.indexOf(source.value);
        row.append(document.createTextNode(source.text.slice(0, offset)), fact,
          document.createTextNode(source.text.slice(offset + source.value.length)));
      }
      const units = element("p", "stamp-passage-units");
      details.append(row, units);
      const ledgerRows = [];
      let ledger = null;
      if (!source.derivation && card.stated_value_display && card.filed_value_display) {
        ledger = { nine: element("span", "stamp-ledger-label"), quarter: element("span", "stamp-ledger-label"), direct: true };
        const statedRow = element("p", "stamp-ledger-row");
        ledger.statedValue = element("span", "stamp-ledger-value");
        statedRow.append(ledger.nine, ledger.statedValue);
        const filedRow = element("p", "stamp-ledger-row is-result");
        ledger.filedValue = element("span", "stamp-ledger-value");
        filedRow.append(ledger.quarter, ledger.filedValue);
        ledgerRows.push(statedRow, filedRow);
      } else if (source.derivation) {
        const millions = (value) => Math.round(value / 1e6).toLocaleString("en-US");
        const nine = source.derivation.nine_months;
        ledger = { nine: element("span", "stamp-ledger-label"), quarter: element("span", "stamp-ledger-label") };
        const nineRow = element("p", "stamp-ledger-row");
        nineRow.append(ledger.nine, element("span", "stamp-ledger-value", `− ${millions(nine.value)}`));
        const quarterRow = element("p", "stamp-ledger-row is-result");
        quarterRow.append(ledger.quarter, element("span", "stamp-ledger-value", `= ${millions(source.derivation.result)}`));
        ledger.nineSource = `${nine.form} · ${nine.filed}`;
        ledgerRows.push(nineRow, quarterRow);
      }
      const ledgerBox = element("div", "stamp-ledger");
      ledgerBox.append(...ledgerRows);
      if (source.derivation) details.append(ledgerBox);
      const derivation = source.derivation ? element("p", "stamp-derivation") : null;
      if (derivation) details.append(derivation);
      // Direct facts use their ledger as the comparison; a derived quarter
      // needs a separate pair so the filed result is not confused with full year.
      const compare = source.derivation ? element("div", "stamp-compare stamp-compare-pair") : ledgerBox;
      if (!source.derivation) compare.classList.toggle("stamp-compare", true);
      const statedLabel = source.derivation ? element("span", "stamp-compare-label") : ledger.nine;
      const filedLabel = source.derivation ? element("span", "stamp-compare-label") : ledger.quarter;
      const statedValue = source.derivation ? element("strong", "stamp-compare-stated") : ledger.statedValue;
      const filedValue = source.derivation ? element("strong", "stamp-compare-filed") : ledger.filedValue;
      if (source.derivation) {
        const statedCell = element("p", "");
        const filedCell = element("p", "");
        statedCell.append(statedLabel, statedValue);
        filedCell.append(filedLabel, filedValue);
        compare.append(statedCell, filedCell);
      }
      const accn = source.source_evidence && source.source_evidence.accn;
      const accession = accn ? element("p", "stamp-passage-accession") : null;
      passage.append(header, details, compare);
      if (accession) passage.append(accession);
      if (isStatic) paperDetails(passage, true);
      return { body: passage, header, details, row, fact, period, units, derivation, ledger, ledgerRows, accession, accn, sweep,
        compare, statedLabel, filedLabel, statedValue, filedValue, filedDate, authority };
    }
    function makeCard(card, index, isStatic) {
      const body = element(isStatic ? "a" : "article", `stamp-card ${verdictClass(card)}`);
      body.dataset.cardId = card.id;
      body.dataset.sourceKind = card.source_kind;
      body.dataset.severity = card.severity || "unknown";
      const hash = Array.from(card.id).reduce((value, character) => (value * 31 + character.charCodeAt(0)) >>> 0, 0);
      const angle = (hash % 13) - 6;
      body.style.setProperty("--stamp-angle", `${angle}deg`);
      if (isStatic) body.href = card.filing_url || card.source_report.replace(/^docs\//, "/");
      const postHeader = element("div", "stamp-post-header");
      const avatar = element("img", "stamp-avatar");
      avatar.alt = "";
      avatar.width = 56;
      avatar.height = 56;
      avatar.loading = "lazy";
      avatar.decoding = "async";
      avatar.src = "/" + card.persona.avatar;
      const identity = element("div", "stamp-identity");
      const authorRow = element("div", "stamp-author-row");
      const author = element("strong", "stamp-author");
      const example = element("span", "stamp-example");
      authorRow.append(author);
      if (card.source_kind !== "article") authorRow.append(example);
      const byline = element("p", "stamp-byline");
      const postMeta = element("p", "stamp-post-meta");
      const followers = element("span", "stamp-followers");
      const date = element("time", "stamp-post-date", card.post_date);
      date.dateTime = card.post_date;
      const audience = card.source_kind === "social" ? element("span", "stamp-audience") : null;
      if (audience) audience.append(icon("audience"));
      postMeta.append(byline, date);
      if (card.source_kind === "article") postMeta.append(example);
      if (audience) postMeta.append(audience);
      identity.append(authorRow, postMeta, followers);
      postHeader.append(avatar, identity);
      const header = element("div", "stamp-card-header");
      const metadata = element("span", "stamp-source");
      const source = element("span", "");
      const input = makeInput(card, isStatic);
      body.dataset.inputKind = input.kind;
      metadata.append(source);
      if (card.source_kind === "article") postMeta.append(input.badge);
      else metadata.append(input.badge);
      if (card.source_kind === "thread" && card.thread_index) metadata.append(element("span", "stamp-thread-index", card.thread_index));
      header.append(element("span", "stamp-ticker", `$${card.ticker}`), element("span", "stamp-company", card.company), metadata);
      identity.append(header);
      const reposted = card.reposted_from ? element("p", "stamp-reposted") : null;
      let original = null;
      let quoteHeader = null;
      if (card.source_kind === "repost") {
        original = cards.find((candidate) => candidate.id === card.same_claim_as);
        if (original) {
          quoteHeader = element("div", "stamp-quote-header");
          const originalAvatar = element("img", "stamp-avatar");
          originalAvatar.alt = "";
          originalAvatar.width = 56;
          originalAvatar.height = 56;
          originalAvatar.loading = "lazy";
          originalAvatar.decoding = "async";
          originalAvatar.src = "/" + original.persona.avatar;
          const identity = element("div", "stamp-identity");
          identity.append(element("strong", "stamp-original-author"), element("p", "stamp-original-byline"));
          const originalDate = element("time", "stamp-post-date", original.post_date);
          originalDate.dateTime = original.post_date;
          identity.append(originalDate);
          quoteHeader.append(originalAvatar, identity);
        }
      }
      const article = card.source_kind === "article" && card.article ? element("div", "stamp-article-deck") : null;
      const lead = article ? element("p", "stamp-article-lead") : null;
      if (article) {
        const masthead = polishImage("/img/polish/banana-masthead.webp", "stamp-masthead", 520, 96, isStatic);
        masthead.addEventListener("error", () => identity.classList.toggle("masthead-unavailable", true));
        identity.prepend(masthead);
        const pictures = element("div", "stamp-article-pictures");
        card.article.illustrations.forEach((path) => pictures.append(polishImage(path, "stamp-article-picture", 320, 180, isStatic)));
        article.append(lead, pictures);
      }
      const claim = element("p", "stamp-claim");
      const period = element("span", "stamp-period");
      period.hidden = false;
      const actions = element("div", `stamp-actions${card.source_kind === "social" ? " stamp-reactions" : ""}`);
      const actionLabels = [];
      if (card.example_activity && card.source_kind !== "article") {
        Object.entries(card.example_activity).forEach(([kind, count]) => {
          if (!["reply", "repost", "like", "views"].includes(kind) || !Number.isFinite(count)) return;
          const action = element("span", "stamp-action");
          action.append(icon(kind), element("span", "", count.toLocaleString("en-US")));
          actions.append(action);
          actionLabels.push({ action, kind });
        });
        actions.append(element("small", "stamp-activity-label"));
      }
      const filed = element("p", "stamp-filed");
      const footer = element("div", "stamp-review");
      const reviewCopy = element("div", "stamp-review-copy");
      const assessment = element("div", "stamp-assessment");
      reviewCopy.append(filed, assessment);
      let meter = null;
      let fill = null;
      let marker = null;
      let severity = null;
      let summary = null;
      let score = null;
      let gap = null;
      const checkable = card.score !== null && card.score !== undefined;
      if (checkable) {
        summary = element("p", "stamp-score-summary");
        severity = element("strong", "stamp-severity");
        score = element("span", "stamp-score");
        summary.append(severity, score);
        meter = element("span", "stamp-meter");
        meter.setAttribute("role", "meter");
        meter.setAttribute("aria-valuemin", "0");
        meter.setAttribute("aria-valuemax", "100");
        meter.setAttribute("aria-valuenow", String(Math.round(card.score)));
        fill = element("span", "stamp-meter-fill");
        marker = element("span", "stamp-meter-marker");
        marker.setAttribute("aria-hidden", "true");
        meter.append(fill, marker);
        gap = element("p", "stamp-gap");
        assessment.append(summary, meter, gap);
      } else {
        gap = element("p", "stamp-uncheckable");
        assessment.append(gap);
      }
      const mark = element("span", "stamp-mark");
      const impression = element("span", "stamp-impression");
      const bleed = element("span", "stamp-bleed");
      bleed.setAttribute("aria-hidden", "true");
      mark.append(impression, bleed);
      footer.append(reviewCopy, mark);
      body.append(postHeader);
      if (reposted) body.append(reposted);
      const content = element("div", original ? "stamp-post-content stamp-quote-card" : "stamp-post-content");
      if (quoteHeader) content.append(quoteHeader);
      content.append(claim);
      if (article) content.append(article);
      if (input.body) content.append(input.body);
      content.append(period);
      if (actions.children.length) content.append(actions);
      body.append(content, footer);
      let scan = null;
      if (!isStatic) {
        const clip = element("span", "stamp-scan");
        scan = element("span", "stamp-scan-light");
        clip.append(scan);
        body.append(clip);
      }
      const passage = makePassage(card, isStatic);
      const carrier = element(isStatic ? "li" : "div", isStatic ? "stamp-static-item" : "stamp-carrier");
      carrier.append(body);
      if (passage) (isStatic ? body : filingContent).append(passage.body);
      const unavailable = !passage && isStatic ? element("div", "stamp-static-unavailable") : null;
      if (unavailable) {
        unavailable.append(element("p", "stamp-no-number-title"), element("p", "stamp-no-number-explanation"), element("span", "stamp-no-number-kind"));
        body.append(unavailable);
      }
      (isStatic ? list : track).append(carrier);
      return { card, index, isStatic, body, source, claim, period, filed, footer, assessment, summary,
        author, example, byline, followers, reposted, original, quoteHeader, article, lead, input, actions, actionLabels, audience,
        severity, score, meter, fill, marker, gap, mark, impression, bleed, scan, passage, carrier, angle, unavailable, number: null, light: null, glow: null };
    }

    const moving = cards.map((card, index) => makeCard(card, index, false));
    const still = cards.map((card, index) => makeCard(card, index, true));

    function localize() {
      [...moving, ...still].forEach((item) => {
        const card = item.card;
        const text = card.text[pageLanguage];
        // Enlarge a number actually present in the post, never a year from its period.
        const number = text.match(/\$[\d,.]+[BM]?|[\d,.]+\s*億美元|\d+(?:\.\d+)?%|\d+(?:\.\d+)?x|\d+(?:\.\d+)?\s*倍/);
        item.claim.replaceChildren();
        item.glow = null;
        item.number = null;
        if (number) {
          const strong = element("strong", "stamp-number");
          item.number = strong;
          item.glow = element("span", "stamp-number-glow");
          strong.append(item.glow, document.createTextNode(number[0]));
          item.claim.append(document.createTextNode(text.slice(0, number.index)), strong,
            document.createTextNode(text.slice(number.index + number[0].length)));
        } else item.claim.textContent = text;
        item.source.textContent = getCopy(`stamps.${card.source_kind}`);
        item.author.textContent = card.persona.name[pageLanguage];
        item.byline.textContent = card.persona.byline[pageLanguage];
        item.byline.hidden = item.byline.textContent === item.author.textContent;
        item.followers.textContent = card.persona.follower_label[pageLanguage];
        item.input.badge.textContent = getCopy(`stamps.input.${item.input.kind}`);
        if (item.input.timing) item.input.timing.textContent = card.input_media.speaker && card.input_media.end_timestamp ?
          `${getCopy("stamps.turn")} ${card.input_media.timestamp}–${card.input_media.end_timestamp} · ${getCopy("stamps.speaker")} ${card.input_media.speaker}` : card.input_media.timestamp;
        if (item.input.disclosure) item.input.disclosure.textContent = card.input_media.disclosure[pageLanguage];
        if (item.input.limit) item.input.limit.textContent = card.input_media.limit[pageLanguage];
        if (item.input.quote) {
          item.input.quote.textContent = item.input.transcript[pageLanguage];
          item.input.quote.setAttribute("aria-label", getCopy("stamps.transcript"));
        }
        if (item.audience) item.audience.title = getCopy("stamps.audience");
        item.actions.setAttribute("aria-label", getCopy("stamps.activity.label"));
        item.actionLabels.forEach(({ action, kind }) => { action.title = `${getCopy("stamps.activity.label")} · ${getCopy(`stamps.activity.${kind}`)}`; });
        const activityLabel = item.actions.querySelector(".stamp-activity-label");
        if (activityLabel) activityLabel.textContent = getCopy("stamps.activity.label");
        if (item.original) {
          item.quoteHeader.querySelector(".stamp-original-author").textContent = item.original.persona.name[pageLanguage];
          item.quoteHeader.querySelector(".stamp-original-byline").textContent = item.original.persona.byline[pageLanguage];
        }
        if (item.lead) item.lead.textContent = card.article.lead[pageLanguage];
        item.example.textContent = getCopy("stamps.example");
        item.example.title = getCopy("stamps.exampleDetail");
        if (item.reposted) item.reposted.textContent = `${getCopy("stamps.repostedFrom")} ${card.reposted_from[pageLanguage]}`;
        item.period.textContent = checkable(card) ? `${getCopy("stamps.claim")}: ${compact(card.stated_value_display)} · ${card.period[pageLanguage]}` : getCopy("stamps.noClaim");
        if (item.unavailable) {
          item.unavailable.querySelector(".stamp-no-number-title").textContent = getCopy("stamps.noNumber");
          item.unavailable.querySelector(".stamp-no-number-explanation").textContent = getCopy("stamps.noNumberExplanation");
          item.unavailable.querySelector(".stamp-no-number-kind").textContent = getCopy(`claimKind.${card.kind}`);
        }
        const verdict = card.verdict === "supported" ? "true" : card.verdict === "contradicted" ? "false" : "unknown";
        item.impression.textContent = getCopy(`stamps.${verdict}`);
        item.bleed.textContent = item.impression.textContent;
        item.captions = {
          read: getCopy("stamps.caption.read"),
          reach: card.excerpt ? getCopy("stamps.caption.reach")(card.excerpt.form) : "",
          find: card.excerpt ? getCopy("stamps.caption.find")(card.excerpt.value) : "",
          compare: card.excerpt && card.excerpt.derivation ? getCopy("stamps.caption.fullYear") :
            card.filed_value_display ? getCopy("stamps.caption.compare")(compact(card.filed_value_display), compact(card.stated_value_display)) : "",
          verdict: item.impression.textContent,
          uncheckable: getCopy("stamps.caption.uncheckable")(getCopy(`claimKind.${card.kind}`))
        };
        item.filed.textContent = card.filed_value_display ? `${getCopy("stamps.filed")}: ${compact(card.filed_value_display)}` : "";
        if (item.meter) {
          item.severity.textContent = getCopy(`stamps.severity.${card.severity}`);
          item.score.textContent = `${Math.round(card.score)} / 100`;
          item.meter.setAttribute("aria-label", getCopy("stamps.accuracy"));
          const gap = card.gap_kind === "points" ? `${card.gap.toFixed(1)} pp` : `${(100 * card.gap).toFixed(card.gap >= 1 ? 0 : 1)}%`;
          item.gap.textContent = card.direction_wrong ? `${getCopy("stamps.direction")} · ${gap}` :
            card.severity === "exact" ? getCopy("stamps.within") : `${gap} ${getCopy(card.gap_relation === "shortfall" ? "stamps.short" : "stamps.off")}`;
        } else item.gap.textContent = checkable(card) && card.excerpt.type === "release" ?
          getCopy(card.kind === "guidance" ? "stamps.rangeMatch" : "stamps.releaseMatch") : getCopy(`claimKind.${card.kind}`);
        if (item.passage) {
          const source = card.excerpt;
          item.passage.filedDate.textContent = `${getCopy("stamps.filed")} ${source.filed}`;
          item.passage.period.textContent = source.derivation ? `${source.derivation.label[pageLanguage]} · ${source.period_header}` : source.period_header;
          if (source.type === "release") item.passage.authority.textContent = getCopy("stamps.release");
          item.passage.units.textContent = source.type === "release" ? getCopy("stamps.releaseStatus") :
            source.fact.scale === 6 ? getCopy("stamps.millions") : getCopy("stamps.filingUnits");
          if (item.passage.derivation) item.passage.derivation.textContent = source.derivation.text[pageLanguage];
          const growth = card.gap_kind === "points";
          const signed = (value) => growth ? value.replace(/^-/, "−").replace(/^(?=\d)/, "+") : value;
          const suffix = growth ? ` · ${getCopy("stamps.growth")}` : "";
          item.passage.statedLabel.textContent = `${getCopy("stamps.stated")}${suffix}`;
          item.passage.filedLabel.textContent = `${getCopy("stamps.filed")}${suffix}`;
          item.passage.statedValue.textContent = `${card.gap_relation === "shortfall" ? "> " : ""}${signed(compact(card.stated_value_display))}`;
          item.passage.filedValue.textContent = signed(compact(card.filed_value_display));
          const ledger = item.passage.ledger;
          if (ledger && ledger.direct) {
            // Percent-change claims compare growth rates, signed, not the revenue row itself.
            ledger.nine.textContent = `${getCopy("stamps.stated")}${suffix}`;
            ledger.statedValue.textContent = `${card.gap_relation === "shortfall" ? "> " : ""}${signed(compact(card.stated_value_display))}`;
            ledger.quarter.textContent = `${getCopy("stamps.filed")}${suffix}`;
            ledger.filedValue.textContent = signed(compact(card.filed_value_display));
          } else if (ledger) {
            ledger.nine.textContent = `${getCopy("stamps.nineMonths")} · ${ledger.nineSource}`;
            ledger.quarter.textContent = getCopy("stamps.quarter");
          }
          if (item.passage.accession) item.passage.accession.textContent = `${getCopy("stamps.accession")} ${item.passage.accn}`;
        }
        if (item.isStatic) {
          if (item.fill) item.fill.style.transform = `scaleX(${card.score / 100})`;
          if (item.marker) item.marker.style.transform = `translate3d(${card.score}%, 0, 0)`;
          if (item.glow) item.glow.style.opacity = "0";
          item.bleed.style.opacity = "0.12";
          if (item.passage) item.passage.sweep.style.transform = "scaleX(1)";
        }
      });
      queuedIndex = -1;
      geometryKey = "";
      paintPause();
      measure();
    }

    function paintPause() {
      const label = getCopy(userPaused ? "stamps.play" : "stamps.pause");
      pause.setAttribute("aria-label", label);
      pauseIcon.textContent = userPaused ? "▶" : "Ⅱ";
      pauseLabel.textContent = label;
    }

    function phaseAt(age, canCheck) {
      if (age < READ) return "enter";
      if (age < REACH) return "read";
      if (!canCheck) return age < UNKNOWN_STRIKE ? "shrug" : age < UNKNOWN_STRIKE + 500 ? "strike" :
        age < UNKNOWN_EXIT ? "react" : "exit";
      return age < FIND ? "reach" : age < COMPARE ? "find" : age < WINDUP ? "compare" :
        age < STRIKE ? "windup" : age < REACT ? "strike" : age < EXIT ? "react" : age < REST ? "exit" : "rest";
    }

    function paintRobot(age, card) {
      const canCheck = checkable(card);
      const transitions = canCheck ? [[0, "idle"], [READ, "inspect"], [REACH, "reach"], [FIND, "point"],
        [COMPARE, "think"], [WINDUP, "stamp"], [STRIKE, "stamp-down"],
        [REACT, card.verdict === "supported" ? "approve" : "concern"], [EXIT, "idle"]] :
        [[0, "idle"], [READ, "inspect"], [REACH, "shrug"], [UNKNOWN_EXIT, "idle"]];
      const current = transitions.findLastIndex(([at]) => age >= at);
      const [at, pose] = transitions[current];
      const previous = current > 0 ? transitions[current - 1][1] : pose;
      const blend = current > 0 ? fadeIn(age, at) : 1;
      Object.entries(poses).forEach(([name, image]) => {
        image.style.opacity = String(name === pose ? blend : name === previous ? 1 - blend : 0);
      });
      const directionOf = (name) => facing[name] === "post" ? -1 : facing[name] === "filing" ? 1 : 0;
      const direction = directionOf(previous) * (1 - blend) + directionOf(pose) * blend;
      const lean = direction * 3 * (0.5 + 0.5 * Math.sin(elapsed / 420));
      const strike = canCheck ? STRIKE : UNKNOWN_STRIKE;
      const sinceStrike = age - strike;
      const dip = sinceStrike < 0 || sinceStrike >= DIP_DOWN + DIP_RECOVER ? 0 : sinceStrike < DIP_DOWN ?
        8 * easeOut(sinceStrike / DIP_DOWN) : 8 * (1 - easeOut((sinceStrike - DIP_DOWN) / DIP_RECOVER));
      const burst = sinceStrike >= 0 && sinceStrike < THRUSTER_BURST;
      const bob = 4 * Math.sin(elapsed / loop * Math.PI * 2 * floatCycles);
      robot.style.transform = `translate3d(0px, ${bob + dip}px, 0) rotate(${lean}deg)`;
      robot.dataset.pose = pose;
      robot.dataset.facing = facing[pose];
      robot.dataset.gesture = !canCheck && age >= REACH && age < UNKNOWN_EXIT ? "shrug" : "review";
      robot.dataset.bob = String(bob);
      robot.dataset.dip = String(dip);
      robot.dataset.thruster = burst ? "burst" : String(Math.floor(elapsed / THRUSTER_FRAME) % 6);
      if (!geometry) return { x: 0, y: 0 };
      thrusters.forEach(({ layer, frames }, index) => {
        const name = index ? pose : previous, nozzle = geometry.nozzles[name];
        const frame = frames.find((image) => image.dataset.frame === robot.dataset.thruster && image.dataset.failed !== "true") ||
          frames.find((image) => image.dataset.failed !== "true");
        frames.forEach((image) => { image.style.opacity = image === frame ? "1" : "0"; });
        const scale = nozzle.scale * (burst ? 1.6 : 1);
        layer.style.opacity = String(index ? blend : 1 - blend);
        layer.style.transform = `translate3d(${nozzle.x}px, ${nozzle.y}px, 0) scale(${scale}) scaleX(${facing[name] === "post" ? -1 : 1}) translate3d(-80px, -20px, 0)`;
        layer.dataset.pose = name;
        layer.dataset.facing = facing[name];
        layer.dataset.nozzleX = String(nozzle.x);
        layer.dataset.nozzleY = String(nozzle.y);
        layer.dataset.scale = String(burst ? 1.6 : 1);
        layer.dataset.frame = frame?.dataset.frame || "none";
      });
      const shadowScale = 0.9 + (bob + dip) * 0.025;
      floorShadow.style.transform = `translate3d(${geometry.floor.x}px, ${geometry.floor.y}px, 0) scale(${geometry.floor.scale * shadowScale}) translate3d(-110px, -17px, 0)`;
      floorShadow.style.opacity = String(0.8 * shadowScale);
      floorShadow.dataset.scale = String(shadowScale);
      const from = geometry.visors[previous], to = geometry.visors[pose];
      const x = from.x + (to.x - from.x) * blend - geometry.pivot.x;
      const y = from.y + (to.y - from.y) * blend - geometry.pivot.y;
      const radians = lean * Math.PI / 180;
      const visor = { x: geometry.pivot.x + x * Math.cos(radians) - y * Math.sin(radians),
        y: geometry.pivot.y + x * Math.sin(radians) + y * Math.cos(radians) + bob + dip };
      robot.dataset.visorX = String(visor.x);
      robot.dataset.visorY = String(visor.y);
      return visor;
    }

    function currentCard() {
      const index = starts.findLastIndex((start) => elapsed >= start);
      return { index, age: elapsed - starts[index] };
    }

    function paint() {
      const { index, age } = currentCard();
      const active = moving[index];
      const canCheck = checkable(active.card);
      const exit = canCheck ? EXIT : UNKNOWN_EXIT;
      const phase = phaseAt(age, canCheck);
      scene.dataset.phase = phase;
      scene.dataset.cardId = active.card.id;
      track.dataset.sourceKind = active.card.source_kind;
      const step = age < READ || age >= exit ? 0 : !canCheck ? (age < UNKNOWN_STRIKE ? 1 : 4) : phase === "read" ? 1 :
        phase === "reach" || phase === "find" ? 2 : phase === "compare" || phase === "shrug" ? 3 : 4;
      scene.dataset.step = String(step);
      progress.forEach((node, offset) => {
        const lit = offset + 1 === step;
        node.classList.toggle("is-active", lit);
        node.classList.toggle("is-skipped", !canCheck && (offset === 1 || offset === 2));
        node.querySelector("button").disabled = !canCheck && (offset === 1 || offset === 2);
        if (lit) node.setAttribute("aria-current", "step");
        else node.removeAttribute("aria-current");
      });
      if (queuedIndex !== index) {
        const upcoming = [1, 2].map((offset) => cards[(index + offset) % cards.length]);
        next.replaceChildren(...upcoming.map((card) => {
          const concept = card.excerpt && card.excerpt.source_evidence && card.excerpt.source_evidence.concept;
          const kind = concept && /Revenue/.test(concept) ? getCopy("stamps.revenue") : getCopy(`claimKind.${card.kind}`);
          return element("span", "stamp-next-chip", `$${card.ticker}${upcoming[0].ticker === upcoming[1].ticker ? ` ${kind.toLowerCase()}` : ""}`);
        }));
        queuedIndex = index;
      }
      const noNumber = !canCheck && age >= REACH;
      setText(filingTitle, getCopy(noNumber ? "stamps.noNumber" : "stamps.waiting"));
      setText(filingExplanation, getCopy("stamps.noNumberExplanation"));
      setText(filingKind, getCopy(`claimKind.${active.card.kind}`));
      filingExplanation.hidden = !noNumber;
      filingKind.hidden = !noNumber;
      filingState.style.opacity = String(canCheck ? 1 - fadeIn(age, REACH) : 1 - clamp((age - UNKNOWN_EXIT) / 800));
      filingBox.dataset.state = !canCheck && age >= REACH ? "uncheckable" : age < REACH ? "waiting" : "filing";
      const words = active.captions;
      setText(caption, phase === "read" ? words.read : noNumber && phase === "shrug" ? words.uncheckable :
        phase === "reach" ? words.reach : phase === "find" ? words.find :
          phase === "compare" || phase === "windup" ? words.compare : phase === "strike" || phase === "react" ? words.verdict : words.read);
      captionVerdict.hidden = !phone.matches || (phase !== "compare" && phase !== "windup");
      setText(captionVerdict, words.verdict);
      moving.forEach((item) => {
        const selected = item.index === index;
        const age = selected ? currentCard().age : 0;
        const canCheck = checkable(item.card);
        item.carrier.hidden = !selected || age >= (canCheck ? REST : UNCHECKABLE);
        const itemPhase = selected ? phase : "rest";
        item.body.dataset.phase = itemPhase;
        if (item.passage) item.passage.body.hidden = !selected || age >= REST;
        const itemExit = canCheck ? EXIT : UNKNOWN_EXIT;
        const leave = clamp((age - itemExit) / 800);
        const x = age < READ ? -cardWidth * (1 - easeOut(age / READ)) : (cardWidth + 24) * easeOut(leave);
        item.carrier.style.transform = `translate3d(${x}px, 0, 0)`;
        item.carrier.style.opacity = String(age < READ ? clamp(age / 160) : 1 - leave);
        const scanning = age >= READ && age < REACH;
        const sweep = clamp((age - READ) / (REACH - READ));
        item.scan.style.transform = `translate3d(${(cardWidth + 48) * sweep - 48}px, 0, 0)`;
        item.scan.style.opacity = String(scanning ? Math.sin(sweep * Math.PI) * 0.22 : 0);
        if (item.glow) item.glow.style.opacity = String(scanning ? Math.sin(sweep * Math.PI) * 0.35 : 0);
        item.period.style.opacity = String(fadeIn(age, canCheck ? READ : REACH));
        const scored = fadeIn(age, COMPARE);
        item.filed.style.opacity = String(canCheck ? scored : 0);
        item.assessment.style.opacity = String(canCheck ? scored : fadeIn(age, REACH));
        const scoreProgress = easeOut((age - COMPARE) / (WINDUP - COMPARE));
        if (item.fill) item.fill.style.transform = `scaleX(${item.card.score / 100 * scoreProgress})`;
        if (item.marker) item.marker.style.transform = `translate3d(${item.card.score * scoreProgress}%, 0, 0)`;
        if (item.passage) {
          const passage = item.passage;
          passage.body.style.opacity = String(1 - leave);
          passage.header.style.opacity = String(fadeIn(age, REACH));
          passage.header.style.transform = `translate3d(0, ${8 * (1 - easeOut((age - REACH) / 250))}px, 0)`;
          passage.details.style.opacity = String(fadeIn(age, FIND));
          passage.ledgerRows.forEach((row, rowIndex) => {
            row.style.opacity = String(fadeIn(age, FIND + (rowIndex + 1) * LEDGER_STAGGER));
          });
          if (passage.derivation) passage.derivation.style.opacity = String(fadeIn(age, FIND + 3 * LEDGER_STAGGER));
          if (passage.accession) passage.accession.style.opacity = String(fadeIn(age, FIND + 3 * LEDGER_STAGGER));
          passage.sweep.style.transform = `scaleX(${clamp((age - FIND_LOCK) / AMBER_SWEEP)})`;
          passage.fact.style.setProperty("--stamp-bloom", String(age >= FIND_LOCK && age < STRIKE ?
            Math.sin(clamp((age - FIND_LOCK) / BLOOM) * Math.PI) : 0));
          passage.compare.style.opacity = String(passage.derivation ? scored : 1);
          passage.compare.classList.toggle("is-active", age >= COMPARE && age < itemExit);
        }
        const impact = age - (canCheck ? STRIKE : UNKNOWN_STRIKE);
        const scale = impact < 0 ? 1.32 : impact < 105 ? 1.32 - 0.36 * easeOut(impact / 105) :
          impact < 200 ? 0.96 + 0.04 * easeOut((impact - 105) / 95) : 1;
        item.mark.style.transform = `rotate(${item.angle}deg) scale(${scale})`;
        item.mark.style.opacity = String(clamp(impact / 45));
        item.bleed.style.opacity = String(impact < 0 ? 0 : 0.12 + 0.45 * (1 - clamp(impact / 300)));
        const shake = impact > 105 && impact < 300 ? Math.sin((impact - 105) / 14) * 1.8 * (1 - (impact - 105) / 195) : 0;
        item.body.style.transform = `translate3d(${shake}px, ${shake / 2}px, 0)`;
      });
      paintSpotlight(age, active, paintRobot(age, active.card));
    }

    const emptyBox = { x: 0, y: 0, width: 0, height: 0 };
    const center = (box) => ({ x: box.x + box.width / 2, y: box.y + box.height / 2 });
    const padBox = (box, pad) => ({ x: box.x - pad, y: box.y - pad, width: box.width + 2 * pad, height: box.height + 2 * pad });
    const unionBox = (a, b) => ({ x: Math.min(a.x, b.x), y: Math.min(a.y, b.y),
      width: Math.max(a.x + a.width, b.x + b.width) - Math.min(a.x, b.x),
      height: Math.max(a.y + a.height, b.y + b.height) - Math.min(a.y, b.y) });
    function setBox(node, box) {
      Object.entries(box).forEach(([name, value]) => node.setAttribute(name, String(value)));
    }

    // The convex hull includes every corner of the target box. Even a steep
    // phone beam stays narrow at the visor and covers the whole destination.
    function conePoints(visor, box, radius) {
      const target = center(box), dx = target.x - visor.x, dy = target.y - visor.y;
      const distance = Math.hypot(dx, dy) || 1;
      const nx = -dy / distance * radius, ny = dx / distance * radius;
      const points = [[visor.x + nx, visor.y + ny], [visor.x - nx, visor.y - ny],
        [box.x, box.y], [box.x + box.width, box.y], [box.x + box.width, box.y + box.height], [box.x, box.y + box.height]];
      points.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
      const half = (values) => values.reduce((hull, point) => {
        while (hull.length >= 2 && cross(hull[hull.length - 2], hull[hull.length - 1], point) <= 0) hull.pop();
        hull.push(point);
        return hull;
      }, []);
      return [...half(points).slice(0, -1), ...half([...points].reverse()).slice(0, -1)].map((point) => point.join(",")).join(" ");
    }

    function paintSpotlight(age, item, visor) {
      const enabled = !!item.light && !motion.matches;
      const light = item.light || { post: emptyBox, row: emptyBox, compare: emptyBox, search: [emptyBox] };
      const finding = enabled && age >= FIND && age < COMPARE;
      const comparing = enabled && age >= COMPARE && age < STRIKE;
      const compareIn = enabled ? fadeIn(age, COMPARE) : 0;
      const lift = 1 - easeOut((age - STRIKE) / DIM_LIFT);
      const filingAlpha = enabled && age < STRIKE ? fadeIn(age, FIND) : 0;
      const postAlpha = comparing ? compareIn : 0;
      const yearAlpha = enabled && light.quarter && age >= COMPARE && age < WINDUP ? 0.28 * compareIn : 0;
      let row = age >= COMPARE && light.quarter ? light.quarter : light.row;
      if (finding) {
        const sweep = clamp((age - FIND) / FIND_SWEEP) * (light.search.length - 1);
        const index = Math.min(Math.floor(sweep), light.search.length - 1);
        const from = light.search[index], to = light.search[Math.min(index + 1, light.search.length - 1)];
        const blend = easeOut(sweep - index);
        row = Object.fromEntries(Object.keys(from).map((name) => [name, from[name] + (to[name] - from[name]) * blend]));
      }
      const filingTarget = age >= COMPARE ? unionBox(row, light.compare) : row;
      const poolCenter = center(row);
      filingVignette.setAttribute("cx", String(poolCenter.x));
      filingVignette.setAttribute("cy", String(poolCenter.y));
      const targets = { post: light.post, filing: filingTarget, year: light.row };
      lights.post.group.style.opacity = String(postAlpha);
      lights.filing.group.style.opacity = String(filingAlpha);
      lights.year.group.style.opacity = String(yearAlpha);
      Object.entries(lights).forEach(([name, beam]) => {
        const target = targets[name], end = center(target), source = name === "year" ? center(light.post) : visor;
        const points = conePoints(source, target, VISOR_RADIUS);
        beam.cone.setAttribute("points", points);
        beam.clip.setAttribute("points", points);
        beam.haze.setAttribute("points", conePoints(source, padBox(target, POOL_PAD), VISOR_RADIUS + 1));
        Object.entries({ x1: source.x, y1: source.y, x2: end.x, y2: end.y }).forEach(([key, value]) => beam.gradient.setAttribute(key, String(value)));
        const dx = end.x - source.x, dy = end.y - source.y, distance = Math.hypot(dx, dy) || 1;
        const across = (Math.abs(dy) * target.width + Math.abs(dx) * target.height) / distance;
        const along = (Math.abs(dx) * target.width + Math.abs(dy) * target.height) / distance;
        const width = (distance + along / 2 + 12) / 0.95, height = Math.max(12, across * 1.4);
        setBox(beam.texture.source, { x: -width * 0.015, y: -height / 2, width, height });
        beam.texture.source.setAttribute("transform", `translate(${source.x} ${source.y}) rotate(${Math.atan2(dy, dx) * 180 / Math.PI})`);
        beam.motes.pattern.setAttribute("patternTransform", `translate(${age / 40 % 512} ${-age / 70 % 512})`);
      });
      const protectedBoxes = { post: light.post, row, compare: light.compare, year: light.row };
      Object.entries(protectedBoxes).forEach(([name, box]) => {
        const visible = enabled && (name === "year" ? yearAlpha > 0 :
          (name === "row" ? age >= FIND : age >= COMPARE) && age < STRIKE + DIM_LIFT);
        setBox(holes[name][0], visible ? padBox(box, POOL_PAD) : emptyBox);
        setBox(holes[name][1], visible ? box : emptyBox);
        const pool = pools[name], middle = center(box);
        Object.entries({ cx: middle.x, cy: middle.y, rx: box.width / 2 + 16, ry: box.height / 2 + 12 })
          .forEach(([key, value]) => pool.setAttribute(key, String(value)));
        pool.style.opacity = String(name === "compare" ? compareIn : 1);
        setBox(fx.pools[name].source, { x: box.x - 24, y: box.y - 16, width: box.width + 48, height: box.height + 32 });
      });
      const stageShade = compareIn * lift, filingShade = filingAlpha * (1 - compareIn);
      stageDim.style.opacity = String(stageShade);
      paperDim.style.opacity = String(stageShade);
      filingDim.style.opacity = String(filingShade);
      const dimmed = Math.max(stageShade, filingShade);
      const field = geometry ? (age < COMPARE ? geometry.filing : geometry.field) : emptyBox;
      setBox(fx.grain, field);
      setBox(fx.vignette, field);
      fx.grain.style.opacity = String(0.1 * dimmed);
      fx.vignette.style.opacity = String(0.24 * dimmed);
      const flareWidth = phone.matches ? 84 : 128;
      setBox(fx.flare.source, { x: visor.x - flareWidth / 2, y: visor.y - 10, width: flareWidth, height: 20 });
      fx.flare.group.style.opacity = String(Math.max(postAlpha, filingAlpha));
      const impact = age - (checkable(item.card) ? STRIKE : UNKNOWN_STRIKE);
      const burstSize = 160 * easeOut(impact / 110), contact = item.contact || emptyBox, strike = center(contact);
      setBox(fx.burst.source, { x: strike.x - burstSize / 2, y: strike.y - burstSize / 2, width: burstSize, height: burstSize });
      setBox(fx.burst.exclusion, contact);
      fx.burst.group.style.opacity = String(!motion.matches && item.contact && impact >= 0 && impact < BURST ? 1 - impact / BURST : 0);
      const barsIn = enabled ? easeOut((age - COMPARE) / LETTERBOX_EASE) * (1 - easeOut((age - REACT) / LETTERBOX_EASE)) : 0;
      const letterboxHeight = phone.matches ? 4 : LETTERBOX;
      letterbox.style.opacity = String(barsIn);
      bars[0].style.transform = `translate3d(0, ${-letterboxHeight * (1 - barsIn)}px, 0)`;
      bars[1].style.transform = `translate3d(0, ${letterboxHeight * (1 - barsIn)}px, 0)`;
      flash.style.opacity = String(enabled && age >= STRIKE && age < STRIKE + FLASH ? 0.7 * (1 - (age - STRIKE) / FLASH) : 0);
      dust.forEach((mote, index) => {
        const target = center(targets[index < 3 ? "post" : "filing"]);
        const travel = ((age + index * 347) % DUST_PERIOD) / DUST_PERIOD;
        const drift = Math.sin(travel * Math.PI * 2 + index) * 6 * travel;
        const dx = target.x - visor.x, dy = target.y - visor.y, distance = Math.hypot(dx, dy) || 1;
        mote.style.transform = `translate3d(${visor.x + dx * travel - dy / distance * drift}px, ${visor.y + dy * travel + dx / distance * drift}px, 0)`;
        mote.style.opacity = String(comparing ? 0.65 * Math.sin(travel * Math.PI) * (index < 3 ? postAlpha : filingAlpha) : 0);
      });
    }

    function measure() {
      cardWidth = track.clientWidth;
      const key = `${cardWidth}:${pageLanguage}:${phone.matches}`;
      if (motion.matches || geometryKey === key) { paint(); return; }
      const saved = moving.map((item) => ({ hidden: item.carrier.hidden, passageHidden: item.passage && item.passage.body.hidden,
        transform: item.carrier.style.transform, shake: item.body.style.transform, mark: item.mark.style.transform }));
      moving.forEach((item) => {
        item.carrier.hidden = false;
        if (item.passage) item.passage.body.hidden = false;
        item.carrier.style.transform = "translate3d(0px, 0, 0)";
        item.body.style.transform = "translate3d(0px, 0px, 0)";
        item.mark.style.transform = `rotate(${item.angle}deg) scale(1)`;
      });
      if (sizeKey !== key) {
        const explanationHidden = filingExplanation.hidden, kindHidden = filingKind.hidden;
        const title = filingTitle.textContent;
        filingTitle.textContent = getCopy("stamps.noNumber");
        filingExplanation.textContent = getCopy("stamps.noNumberExplanation");
        filingExplanation.hidden = false;
        filingKind.hidden = false;
        scene.classList.toggle("is-measuring", true);
        const inset = filingBox.getBoundingClientRect().height - filingContent.getBoundingClientRect().height;
        const postInset = track.getBoundingClientRect().width - track.clientWidth;
        const postHeight = Math.ceil(Math.max(...moving.map((item) => item.body.getBoundingClientRect().height)) + postInset);
        const unknownHeights = cards.filter((card) => !checkable(card)).map((card) => {
          filingKind.textContent = getCopy(`claimKind.${card.kind}`);
          return filingState.getBoundingClientRect().height;
        });
        const filingHeight = Math.ceil(Math.max(0, ...unknownHeights,
          ...moving.filter((item) => item.passage).map((item) => item.passage.body.getBoundingClientRect().height + inset)));
        scene.style.setProperty("--stamp-content-height", `${Math.max(postHeight, filingHeight)}px`);
        scene.style.setProperty("--stamp-post-height", `${postHeight}px`);
        scene.style.setProperty("--stamp-filing-height", `${filingHeight}px`);
        scene.classList.toggle("is-measuring", false);
        filingTitle.textContent = title;
        filingExplanation.hidden = explanationHidden;
        filingKind.hidden = kindHidden;
        sizeKey = key;
      }
      const origin = stage.getBoundingClientRect();
      const box = (node) => {
        const rect = node.getBoundingClientRect();
        return { x: rect.left - origin.left, y: rect.top - origin.top, width: rect.width, height: rect.height };
      };
      const robotTransform = robot.style.transform;
      robot.style.transform = "translate3d(0px, 0px, 0)";
      const robotBox = box(robot);
      const bandBox = box(robotBand);
      const bodyScale = Math.min(robotBox.width / POSE_CANVAS[0], robotBox.height / POSE_CANVAS[1]);
      geometry = { width: origin.width, height: origin.height,
        pivot: { x: robotBox.x + robotBox.width / 2, y: robotBox.y + robotBox.height }, visors: {}, nozzles: {},
        floor: { x: robotBox.x - bandBox.x + robotBox.width / 2,
          y: robotBox.y - bandBox.y + robotBox.height - (POSE_CANVAS[1] - 646) * bodyScale, scale: bodyScale } };
      Object.entries(poses).forEach(([name, image]) => {
        const anchor = POSE_VISORS[image.dataset.asset || name];
        const width = image.naturalWidth || POSE_CANVAS[0], height = image.naturalHeight || POSE_CANVAS[1];
        const scale = Math.min(robotBox.width / width, robotBox.height / height);
        const nozzle = POSE_ANCHORS[image.dataset.asset || name].nozzle;
        geometry.nozzles[name] = { x: (robotBox.width - width * scale) / 2 +
          (facing[name] === "post" ? 1 - nozzle[0] / POSE_CANVAS[0] : nozzle[0] / POSE_CANVAS[0]) * width * scale,
          y: robotBox.height - height * scale + nozzle[1] / POSE_CANVAS[1] * height * scale, scale };
        geometry.visors[name] = { x: robotBox.x + (robotBox.width - width * scale) / 2 +
          (facing[name] === "post" ? 1 - anchor[0] : anchor[0]) * width * scale,
        y: robotBox.y + robotBox.height - height * scale + anchor[1] * height * scale };
      });
      robot.style.transform = robotTransform;
      moving.forEach((item) => {
        item.contact = box(item.mark);
        if (!item.passage) return;
        const passage = item.passage;
        // Align the filed comparison's text baseline with the meter's center.
        // Only the measurement pass writes this fixed desktop offset.
        passage.body.style.setProperty("--stamp-compare-top", "0px");
        if (!phone.matches && item.meter) {
          const meter = box(item.meter), filed = box(passage.filedValue);
          passage.body.style.setProperty("--stamp-compare-top", `${meter.y + meter.height / 2 - filed.y - filed.height}px`);
        }
        const row = box(passage.row);
        item.light = { post: box(item.input.quote || item.number || item.claim), row, compare: box(passage.compare),
          quarter: passage.derivation ? box(passage.ledgerRows[passage.ledgerRows.length - 1]) : null,
          search: [row, ...passage.ledgerRows.map(box), row] };
      });
      const field = { x: 0, y: 0, width: origin.width, height: origin.height };
      spotlight.querySelectorAll(".stamp-mask-field").forEach((node) => setBox(node, field));
      ["#stamp-dim-mask", "#stamp-ink-mask", "#stamp-stage-mask"].forEach((selector) => setBox(spotlight.querySelector(selector), field));
      setBox(stageDim, field);
      const filingBounds = box(filingBox);
      geometry.field = field;
      geometry.filing = filingBounds;
      setBox(paperDim, filingBounds);
      setBox(paperHole, filingBounds);
      fx.fields.forEach((node) => setBox(node, field));
      setBox(filingDim, filingBounds);
      filingVignette.setAttribute("r", String(Math.max(filingBounds.width, filingBounds.height) * 0.75));
      setBox(flash, box(track));
      const letterboxHeight = phone.matches ? 4 : LETTERBOX;
      setBox(bars[0], { x: 0, y: 0, width: origin.width, height: letterboxHeight });
      setBox(bars[1], { x: 0, y: origin.height - letterboxHeight, width: origin.width, height: letterboxHeight });
      moving.forEach((item, index) => {
        const state = saved[index];
        item.carrier.hidden = state.hidden;
        if (item.passage) item.passage.body.hidden = state.passageHidden;
        item.carrier.style.transform = state.transform;
        item.body.style.transform = state.shake;
        item.mark.style.transform = state.mark;
      });
      geometryKey = key;
      paint();
    }

    function tick(now) {
      if (lastFrame !== null) elapsed = (elapsed + now - lastFrame) % loop;
      lastFrame = now;
      paint();
      frame = requestAnimationFrame(tick);
    }

    function updatePlayback() {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
      lastFrame = null;
      const animated = !motion.matches;
      scene.dataset.animated = String(animated);
      list.classList.toggle("is-sr-only", animated);
      still.forEach((item) => { item.body.tabIndex = animated ? -1 : 0; });
      const running = animated && inView && !document.hidden && !userPaused;
      scene.dataset.running = String(running);
      pause.setAttribute("aria-pressed", String(userPaused));
      paintPause();
      if (running) { loadAssets(); frame = requestAnimationFrame(tick); }
    }

    function seek(seconds) {
      if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) {
        throw new RangeError("Stamp scene time must be a finite, non-negative number of seconds.");
      }
      elapsed = Math.round((seconds % (loop / 1000)) * 1000) % loop;
      userPaused = true;
      loadAssets();
      updatePlayback();
      measure();
      return elapsed / 1000;
    }

    window.__stampScene = Object.freeze({ seek, timing: Object.freeze({ initial: INITIAL / 1000, checkable: CHECKABLE / 1000,
      uncheckable: UNCHECKABLE / 1000, read: READ / 1000, reach: REACH / 1000, find: FIND / 1000,
      compare: COMPARE / 1000, windup: WINDUP / 1000, strike: STRIKE / 1000, react: REACT / 1000,
      exit: EXIT / 1000, rest: REST / 1000, unknownStrike: UNKNOWN_STRIKE / 1000, unknownExit: UNKNOWN_EXIT / 1000,
      crossfade: FADE / 1000, ledgerStagger: LEDGER_STAGGER / 1000, findLock: FIND_LOCK / 1000, flash: FLASH / 1000, burst: BURST / 1000,
      floatPeriod: loop / floatCycles / 1000, thrusterFrame: THRUSTER_FRAME / 1000, thrusterBurst: THRUSTER_BURST / 1000,
      dipDown: DIP_DOWN / 1000, dipRecover: DIP_RECOVER / 1000,
      starts: Object.freeze(starts.map((time) => time / 1000)), loop: loop / 1000 }),
      getState: () => ({ seconds: elapsed / 1000, cardId: scene.dataset.cardId, phase: scene.dataset.phase,
        pose: robot.dataset.pose, facing: robot.dataset.facing, step: Number(scene.dataset.step), localTime: currentCard().age / 1000 }) });
    pause.addEventListener("click", () => { userPaused = !userPaused; updatePlayback(); });
    progress.forEach((node, index) => {
      node.querySelector("button").addEventListener("click", () => {
        const { index: cardIndex } = currentCard();
        const canCheck = checkable(cards[cardIndex]);
        const beats = canCheck ? [READ, FIND, COMPARE, STRIKE] : [READ, REACH, REACH, UNKNOWN_STRIKE];
        seek((starts[cardIndex] + beats[index] + FADE) / 1000);
      });
    });
    document.addEventListener("visibilitychange", updatePlayback);
    motion.addEventListener("change", () => { updatePlayback(); measure(); });
    phone.addEventListener("change", measure);
    scene.hidden = false;
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; updatePlayback(); }).observe(scene);
    } else inView = true;
    if ("ResizeObserver" in window) new ResizeObserver(measure).observe(scene);
    else window.addEventListener("resize", measure);
    // Font completion invalidates the intrinsic maxima and cached light boxes.
    if (document.fonts) document.fonts.ready.then(() => { sizeKey = ""; geometryKey = ""; measure(); });
    localize();
    const requested = new URLSearchParams(window.location.search).get("stamp-t");
    const seconds = requested === null || requested.trim() === "" ? NaN : Number(requested);
    if (Number.isFinite(seconds) && seconds >= 0) seek(seconds);
    else { updatePlayback(); measure(); }
    return { localize };
  }

  function verdictClass(claim) {
    if (claim.verdict === "supported") return "is-true";
    if (claim.verdict === "contradicted") return "is-false";
    return "is-unknown";
  }

  function verdictCopy(claim) {
    if (claim.verdict === "supported") return getCopy("verdict.true");
    if (claim.verdict === "contradicted") return getCopy("verdict.false");
    return getCopy("verdict.unknown");
  }

  function claimKindCopy(claim) {
    return getCopy(`claimKind.${claim.kind}`) || getCopy("claimKind.reported_fact");
  }

  function pythonOffsetToJavaScript(text, offset) {
    return Array.from(text).slice(0, offset).join("").length;
  }

  function renderPost(example) {
    const post = $("#post-text");
    if (!post || !example) return;
    const fragment = document.createDocumentFragment();
    const text = example.post || "";
    const claims = [...(example.claims || [])].sort((left, right) => left.span[0] - right.span[0]);
    let cursor = 0;

    claims.forEach((claim) => {
      if (!Array.isArray(claim.span) || claim.span.length !== 2) return;
      const start = pythonOffsetToJavaScript(text, claim.span[0]);
      const end = pythonOffsetToJavaScript(text, claim.span[1]);
      if (start < cursor || end <= start || start > text.length) return;
      fragment.append(document.createTextNode(text.slice(cursor, start)));
      const mark = document.createElement("mark");
      mark.className = verdictClass(claim);
      mark.dataset.claimIndex = String(claim.index);
      mark.title = `${verdictCopy(claim)}: ${claim.quote}`;
      mark.textContent = text.slice(start, end);
      fragment.append(mark);
      cursor = end;
    });

    fragment.append(document.createTextNode(text.slice(cursor)));
    post.replaceChildren(fragment);
  }

  function numberText(value, maximumFractionDigits = 1) {
    if (typeof value !== "number" || !Number.isFinite(value)) return getCopy("filing.notAvailable");
    return value.toLocaleString(pageLanguage === "zh" ? "zh-Hant" : "en-US", { maximumFractionDigits });
  }

  function formatMoneyShort(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return getCopy("filing.notAvailable");
    return financialNumber(value);
  }

  function formatPercent(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return getCopy("filing.notAvailable");
    return `${value >= 0 ? "+" : ""}${numberText(value)}%`;
  }

  function formatDate(value) {
    if (!value) return "";
    const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!match) return String(value);
    const [, year, month, day] = match;
    if (pageLanguage === "zh") return `${year} 年 ${Number(month)} 月 ${Number(day)} 日`;
    return new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))).toLocaleDateString("en-US", {
      timeZone: "UTC",
      month: "short",
      day: "numeric",
      year: "numeric"
    }).replace(",", "");
  }

  function fiscalPeriodLabel(evidence) {
    if (!evidence) return "";
    const yearMatch = String(evidence.period || "").match(/(?:FY|CY)?(\d{4})/i);
    const year = evidence.fiscal_year || (yearMatch && yearMatch[1]);
    const fiscalPeriod = String(evidence.fiscal_period || "").toUpperCase();
    if (fiscalPeriod === "FY" || /^FY\d{4}$/i.test(String(evidence.period || ""))) {
      return year ? (pageLanguage === "zh" ? `${year} 財年` : `Fiscal ${year}`) : "";
    }
    const quarterMatch = String(evidence.period || "").match(/(?:CY)?(\d{4})Q([1-4])/i);
    if (quarterMatch) {
      return pageLanguage === "zh"
        ? `曆年 Q${quarterMatch[2]} ${quarterMatch[1]}`
        : `Calendar Q${quarterMatch[2]} ${quarterMatch[1]}`;
    }
    return evidence.period || evidence.fiscal_period || "";
  }

  function periodText(evidence) {
    if (!evidence) return getCopy("filing.notAvailable");
    const period = fiscalPeriodLabel(evidence);
    const dates = [evidence.start, evidence.end].filter(Boolean).map(formatDate);
    const dateText = dates.join(pageLanguage === "zh" ? " – " : " – ");
    return period && dateText
      ? `${period} · ${dateText}`
      : period || dateText || getCopy("filing.notAvailable");
  }

  function scaleText(scale) {
    const numericScale = Number(scale);
    if (numericScale === 6) return getCopy("filing.inMillions");
    if (numericScale === 3) return getCopy("filing.inThousands");
    if (numericScale === 9) return getCopy("filing.inBillions");
    if (Number.isFinite(numericScale)) return getCopy("filing.reportedUnits")(numericScale);
    return getCopy("filing.notAvailable");
  }

  function recordEntries(claim) {
    const evidence = claim.evidence || [];
    const excerptRecords = claim.excerpts || [];
    const recordsByIndex = new Map(
      excerptRecords.map((record, index) => [
        Number.isInteger(record.evidence_index) ? record.evidence_index : index,
        record
      ])
    );
    return evidence.map((item, index) => ({
      evidence: item,
      record: recordsByIndex.get(index) || {
        evidence_id: item.id,
        evidence_index: index,
        evidence_key: `${item.id || "evidence"}:${index}`,
        role: item.role,
        excerpt: null,
        reason: getCopy("filing.noPassage"),
        primary_url: null,
        inline_url: null
      },
      index
    }));
  }

  function evidenceLabel(entry) {
    const id = entry.evidence.id || entry.record.evidence_id || "Evidence";
    if (entry.evidence.role === "current") return `${id} ${getCopy("filing.thisPeriod")}`;
    if (entry.evidence.role === "comparison") return `${id} ${getCopy("filing.comparisonPeriod")}`;
    return id;
  }

  function factIdentity(entry) {
    const evidence = entry.evidence || {};
    const fact = entry.record && entry.record.excerpt && entry.record.excerpt.fact;
    if (!fact && !entry.record?.excerpt) return `unmatched:${entry.index}`;
    return [
      evidence.accn || "",
      evidence.concept || "",
      evidence.start || "",
      evidence.end || "",
      evidence.unit || "",
      fact && fact.full_value !== undefined ? fact.full_value : evidence.value
    ].join("|");
  }

  function groupFilingRecords(claim) {
    const entries = recordEntries(claim);
    const entriesByIndex = new Map(entries.map((entry) => [entry.index, entry]));
    const roleRank = { current: 0, comparison: 1 };
    if (Array.isArray(claim.modal_blocks) && claim.modal_blocks.length) {
      return claim.modal_blocks
        .map((block) => {
          const records = (block.evidence_indices || [])
            .map((index) => entriesByIndex.get(index))
            .filter(Boolean);
          return {
            key: block.fact_key,
            records,
            label: records.map(evidenceLabel).join(" · ")
          };
        })
        .filter((group) => group.records.length)
        .sort((left, right) => {
          const leftRole = roleRank[left.records[0].evidence.role] ?? 0;
          const rightRole = roleRank[right.records[0].evidence.role] ?? 0;
          return leftRole - rightRole || left.records[0].index - right.records[0].index;
        });
    }
    const groups = new Map();
    entries.forEach((entry) => {
      const key = factIdentity(entry);
      if (!groups.has(key)) groups.set(key, { key, records: [] });
      groups.get(key).records.push(entry);
    });
    return Array.from(groups.values())
      .map((group) => {
        group.records.sort((left, right) => {
          const leftRank = roleRank[left.evidence.role] ?? 0;
          const rightRank = roleRank[right.evidence.role] ?? 0;
          return leftRank - rightRank || left.index - right.index;
        });
        group.label = group.records.map(evidenceLabel).join(" · ");
        return group;
      })
      .sort((left, right) => {
        const leftRole = roleRank[left.records[0].evidence.role] ?? 0;
        const rightRole = roleRank[right.records[0].evidence.role] ?? 0;
        return leftRole - rightRole || left.records[0].index - right.records[0].index;
      });
  }

  function evidenceForCheck(claim, check) {
    const ids = new Set(check.evidence_ids || []);
    const entries = recordEntries(claim);
    return ids.size ? entries.filter((entry) => ids.has(entry.evidence.id)) : entries;
  }

  function isChangeCheck(claim, check) {
    const entries = evidenceForCheck(claim, check);
    return entries.some((entry) => entry.evidence.role === "current")
      && entries.some((entry) => entry.evidence.role === "comparison")
      && typeof check.stated_value_used === "number"
      && Math.abs(check.stated_value_used) < 1000;
  }

  function reportedValue(entry) {
    const fact = entry && entry.record && entry.record.excerpt && entry.record.excerpt.fact;
    if (fact && fact.raw_value) return fact.raw_value;
    const scale = fact && Number.isFinite(Number(fact.scale)) ? Number(fact.scale) : null;
    const value = entry && entry.evidence && entry.evidence.value;
    if (typeof value === "number" && scale !== null) return numberText(value / (10 ** scale), 3);
    return typeof value === "number" ? numberText(value, 0) : getCopy("filing.notAvailable");
  }

  function summaryStatedValue(claim, check) {
    return isChangeCheck(claim, check)
      ? formatPercent(check.stated_value_used)
      : formatMoneyShort(check.stated_value_used);
  }

  function summaryFilingValue(claim, check) {
    const entries = evidenceForCheck(claim, check);
    if (isChangeCheck(claim, check)) {
      const current = entries.find((entry) => entry.evidence.role === "current");
      const comparison = entries.find((entry) => entry.evidence.role === "comparison");
      const filingLabel = pageLanguage === "zh"
        ? `${getCopy("filing.filingShort")}：`
        : `${getCopy("filing.filingShort")}: `;
      if (!current || !comparison || typeof check.actual_value !== "number") {
        return `${filingLabel}${getCopy("filing.notEnoughForChange")}`;
      }
      return `${filingLabel}${reportedValue(current)} vs ${reportedValue(comparison)} = ${formatPercent(check.actual_value)}`;
    }
    const evidence = entries[0] && entries[0].evidence;
    const period = fiscalPeriodLabel(evidence);
    const qualifier = period
      ? (pageLanguage === "zh" ? `（${period}）` : ` (${period.toLowerCase()})`)
      : "";
    return `${getCopy("filing.filingSays")} ${formatMoneyShort(check.actual_value)}${qualifier}`;
  }

  function filingSummaryText(claim) {
    const checks = claim.program_checks || [];
    if (!checks.length) return claim.summary || getCopy("filing.notAvailable");
    const stated = checks.map((check) => summaryStatedValue(claim, check)).join(" · ");
    const filing = checks.map((check) => summaryFilingValue(claim, check)).join(" · ");
    return `${getCopy("filing.summaryPost")} ${stated} · ${filing}`;
  }

  function appendMarkedText(parent, text, range) {
    if (!range || !Number.isInteger(range.start) || !Number.isInteger(range.end)) {
      parent.textContent = text || "";
      return;
    }
    const start = Math.max(0, Math.min(text.length, range.start));
    const end = Math.max(start, Math.min(text.length, range.end));
    parent.append(document.createTextNode(text.slice(0, start)));
    const mark = document.createElement("mark");
    mark.className = "filing-fact-highlight";
    mark.textContent = text.slice(start, end);
    parent.append(mark, document.createTextNode(text.slice(end)));
  }

  function appendFactTable(parent, excerpt) {
    const table = document.createElement("table");
    table.className = "filing-excerpt-table";
    const caption = document.createElement("caption");
    caption.textContent = excerpt.type === "table"
      ? (excerpt.compact && excerpt.compact.caption) || getCopy("filing.table")
      : getCopy("filing.text");
    table.append(caption);

    if (excerpt.type === "table") {
      if (excerpt.compact) {
        const head = document.createElement("thead");
        const headerRow = document.createElement("tr");
        (excerpt.compact.columns || []).forEach((column) => {
          const th = document.createElement("th");
          th.scope = "col";
          th.className = column.is_fact ? "is-period-header" : "";
          th.textContent = column.label || "";
          headerRow.append(th);
        });
        head.append(headerRow);
        table.append(head);

        const body = document.createElement("tbody");
        (excerpt.compact.rows || []).forEach((compactRow) => {
          const row = document.createElement("tr");
          (compactRow.cells || []).forEach((cell) => {
            const td = document.createElement("td");
            if (cell.is_fact) td.className = "is-fact";
            if (cell.is_row_label) td.classList.add("is-row-label");
            if (cell.is_fact || cell.is_row_label) {
              const strong = document.createElement("strong");
              strong.textContent = cell.text || "";
              td.append(strong);
            } else {
              td.textContent = cell.text || "";
            }
            row.append(td);
          });
          body.append(row);
        });
        table.append(body);
        const tableWrap = document.createElement("div");
        tableWrap.className = "filing-table-wrap";
        tableWrap.append(table);
        parent.append(tableWrap);
        return;
      }
      const head = document.createElement("thead");
      (excerpt.headers || []).forEach((header) => {
        const row = document.createElement("tr");
        (header.cells || []).forEach((cell) => {
          const th = document.createElement("th");
          th.scope = "col";
          th.colSpan = Math.max(1, Number(cell.colspan) || 1);
          th.className = cell.covers_fact ? "is-period-header" : "";
          th.textContent = cell.text || "";
          row.append(th);
        });
        head.append(row);
      });
      table.append(head);

      const body = document.createElement("tbody");
      const row = document.createElement("tr");
      (excerpt.row && excerpt.row.cells || []).forEach((cell) => {
        const td = document.createElement("td");
        td.colSpan = Math.max(1, Number(cell.colspan) || 1);
        if (cell.is_fact) {
          td.className = "is-fact";
          const strong = document.createElement("strong");
          strong.textContent = cell.text || "";
          td.append(strong);
        } else if (cell.is_row_label) {
          td.className = "is-row-label";
          const label = document.createElement("span");
          label.textContent = cell.text || "";
          td.append(label);
        } else {
          td.textContent = cell.text || "";
        }
        row.append(td);
      });
      body.append(row);
      table.append(body);
      const tableWrap = document.createElement("div");
      tableWrap.className = "filing-table-wrap";
      tableWrap.append(table);
      parent.append(tableWrap);
      return;
    }

    const paragraph = document.createElement("blockquote");
    paragraph.className = "filing-excerpt-text";
    appendMarkedText(paragraph, excerpt.text || "", excerpt.fact_range);
    parent.append(paragraph);
  }

  function appendFact(parent, label, value, className = "") {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    if (className) description.className = className;
    description.textContent = value || getCopy("filing.notAvailable");
    parent.append(term, description);
  }

  function appendFilingFacts(parent, claim, evidence, record) {
    const heading = document.createElement("h4");
    heading.textContent = getCopy("filing.sourceFacts");
    parent.append(heading);
    const facts = document.createElement("dl");
    facts.className = "filing-facts";
    const excerptFact = record.excerpt && record.excerpt.fact;
    appendFact(facts, getCopy("filing.company"), evidence.entity || evidence.ticker);
    const formDate = [evidence.form, evidence.filed].filter(Boolean).join(" · ");
    appendFact(facts, getCopy("filing.formDate"), formDate);
    appendFact(facts, getCopy("filing.period"), periodText(evidence));
    // Show the concept actually highlighted in the passage (an equivalent revenue tag may have matched).
    const shownConcept = (excerptFact && excerptFact.concept ? excerptFact.concept.replace(/^us-gaap:/, "") : "") || evidence.concept;
    appendFact(facts, getCopy("filing.concept"), shownConcept, "filing-concept");
    const fullValue = typeof evidence.value === "number" ? evidence.value : excerptFact && excerptFact.full_value;
    const rawValue = excerptFact && excerptFact.raw_value
      ? excerptFact.raw_value
      : (typeof fullValue === "number" ? formatMoneyShort(fullValue) : getCopy("filing.notAvailable"));
    const scale = excerptFact ? scaleText(excerptFact.scale) : getCopy("filing.notAvailable");
    const valueLine = document.createElement("p");
    valueLine.className = "filing-value-line";
    valueLine.textContent = `${rawValue} (${scale}) = ${formatMoneyShort(fullValue)}`;
    parent.append(valueLine);
    parent.append(facts);
  }

  function appendFilingLinks(parent, entries) {
    const links = document.createElement("div");
    links.className = "filing-links";
    const firstRecord = entries[0] && entries[0].record;
    const factId = firstRecord && firstRecord.excerpt && firstRecord.excerpt.fact && firstRecord.excerpt.fact.id;
    const primaryRecord = entries.find((entry) => entry.record.primary_url);
    const inlineRecord = entries.find((entry) => entry.record.inline_url);
    if (primaryRecord) {
      const original = document.createElement("a");
      original.href = factId ? `${primaryRecord.record.primary_url}#${encodeURIComponent(factId)}` : primaryRecord.record.primary_url;
      original.target = "_blank";
      original.rel = "noreferrer";
      original.textContent = factId ? getCopy("filing.original") : getCopy("filing.primary");
      links.append(original);
    }
    if (inlineRecord) {
      const inline = document.createElement("a");
      inline.href = inlineRecord.record.inline_url;
      inline.target = "_blank";
      inline.rel = "noreferrer";
      inline.textContent = getCopy("filing.inline");
      links.append(inline);
    }
    if (!links.children.length) {
      const noLink = document.createElement("p");
      noLink.className = "filing-no-link";
      noLink.textContent = getCopy("filing.noLink");
      links.append(noLink);
    }
    parent.append(links);
  }

  function appendFilingSummary(parent, claim) {
    const summary = document.createElement("p");
    summary.className = `filing-summary ${verdictClass(claim)}`;
    summary.append(document.createTextNode(`${filingSummaryText(claim)} · `));
    const verdict = document.createElement("strong");
    verdict.className = "filing-summary-verdict";
    verdict.textContent = verdictCopy(claim);
    summary.append(verdict);
    parent.append(summary);
  }

  function renderFilingEvidence(parent, claim, group) {
    const entry = group.records[0];
    const item = document.createElement("section");
    item.className = "filing-evidence";
    const itemHeading = document.createElement("h3");
    itemHeading.textContent = group.label || getCopy("filing.component")();
    item.append(itemHeading);

    if (entry.record.excerpt) {
      const passageHeading = document.createElement("h4");
      passageHeading.textContent = getCopy("filing.passage");
      item.append(passageHeading);
      if (entry.record.excerpt.section_title) {
        const sectionTitle = document.createElement("p");
        sectionTitle.className = "filing-section-title";
        sectionTitle.textContent = entry.record.excerpt.section_title;
        item.append(sectionTitle);
      }
      appendFactTable(item, entry.record.excerpt);
    } else {
      const empty = document.createElement("div");
      empty.className = "filing-empty";
      const noPassage = document.createElement("p");
      noPassage.textContent = getCopy("filing.noPassage");
      empty.append(noPassage);
      if (entry.record.reason) {
        const reason = document.createElement("p");
        reason.append(document.createElement("strong"));
        reason.firstChild.textContent = `${getCopy("filing.reason")}: `;
        reason.append(document.createTextNode(entry.record.reason));
        empty.append(reason);
      }
      item.append(empty);
    }

    appendFilingFacts(item, claim, entry.evidence, entry.record);
    appendFilingLinks(item, group.records);
    parent.append(item);
  }

  function renderFilingDialog(claim) {
    const title = $("#filing-dialog-title");
    const body = $("#filing-dialog-body");
    if (!title || !body || !claim) return;
    const firstEvidence = (claim.evidence || [])[0] || {};
    title.textContent = `${getCopy("filing.title")} · ${firstEvidence.ticker || claim.ticker || "SEC"}`;
    body.replaceChildren();
    appendFilingSummary(body, claim);
    groupFilingRecords(claim).forEach((group) => renderFilingEvidence(body, claim, group));
  }

  function focusableFilingElements(dialog) {
    return Array.from(dialog.querySelectorAll("button, a[href], [tabindex]:not([tabindex=\"-1\"])")).filter((element) => !element.hasAttribute("disabled"));
  }

  function closeFilingDialog() {
    const dialog = $("#filing-dialog");
    if (!dialog) return;
    if (dialog.open) dialog.close();
    else dialog.removeAttribute("open");
  }

  function openFilingDialog(claim, trigger) {
    const dialog = $("#filing-dialog");
    if (!dialog) return;
    activeFilingClaim = claim;
    filingReturnFocus = trigger;
    renderFilingDialog(claim);
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    requestAnimationFrame(() => $("#filing-dialog-close")?.focus());
  }

  function setupFilingDialog() {
    const dialog = $("#filing-dialog");
    const close = $("#filing-dialog-close");
    if (!dialog || !close) return;
    close.addEventListener("click", closeFilingDialog);
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeFilingDialog();
    });
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      closeFilingDialog();
    });
    dialog.addEventListener("keydown", (event) => {
      if (event.key === "Tab") {
        const focusable = focusableFilingElements(dialog);
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });
    dialog.addEventListener("close", () => {
      activeFilingClaim = null;
      const returnFocus = filingReturnFocus;
      filingReturnFocus = null;
      if (returnFocus && document.contains(returnFocus)) requestAnimationFrame(() => returnFocus.focus());
    });
  }

  function appendSource(card, claim) {
    const sourceLine = document.createElement("p");
    sourceLine.className = "claim-source";
    const source = claim.source;

    const addFilingTrigger = () => {
      if (claim.status !== "verified" || !(claim.evidence || []).length) return;
      const trigger = document.createElement("button");
      trigger.type = "button";
      trigger.className = "claim-filing-trigger";
      trigger.textContent = getCopy("claimSource.see");
      trigger.addEventListener("click", () => openFilingDialog(claim, trigger));
      sourceLine.append(document.createTextNode(" "), trigger);
    };

    if (!source) {
      sourceLine.textContent = getCopy("claimSource.notChecked");
      addFilingTrigger();
      card.append(sourceLine);
      return;
    }

    if (source.kind === "direct") {
      const form = source.form ? ` (${source.form}` : "";
      const filed = source.filed ? `${getCopy("claimSource.filed")} ${source.filed}` : "";
      const closing = form ? ")" : "";
      sourceLine.append(document.createTextNode(`${getCopy("claimSource.sec")}: ${source.display_value || ""}${form}${filed ? `${form ? ", " : " ("}${filed}` : ""}${closing}`));
    } else {
      const summary = (source.summary || claim.summary || "").split(". ")[0];
      sourceLine.append(document.createTextNode(`${getCopy("claimSource.derived")}: ${summary}${summary && !summary.endsWith(".") ? "." : ""}`));
    }

    addFilingTrigger();
    card.append(sourceLine);
  }

  function renderClaimCards(example) {
    const list = $("#claim-list");
    if (!list || !example) return;
    list.replaceChildren();

    (example.claims || []).forEach((claim) => {
      const card = document.createElement("article");
      card.className = `claim-card ${verdictClass(claim)}`;

      const top = document.createElement("div");
      top.className = "claim-card-top";
      const verdict = document.createElement("span");
      verdict.className = "claim-verdict";
      verdict.textContent = verdictCopy(claim);
      const kind = document.createElement("span");
      kind.className = "claim-kind";
      kind.textContent = claimKindCopy(claim);
      top.append(verdict, kind);

      const quote = document.createElement("p");
      quote.className = "claim-text";
      quote.textContent = claim.quote || claim.claim || "";

      card.append(top, quote);
      appendSource(card, claim);
      list.append(card);
    });
  }

  function renderExample(example) {
    if (!example) return;
    renderPost(example);
    renderClaimCards(example);
    const count = $("#post-count");
    if (count) count.textContent = getCopy("example.claimCount")(example.claims.length);
  }

  function percent(value, decimals = 0) {
    return `${(Number(value) * 100).toFixed(decimals)}%`;
  }

  function range(values) {
    return `${percent(values.lower, 1)}–${percent(values.upper, 1)}`;
  }

  function cost(value) {
    return `$${Number(value).toFixed(2)}`;
  }

  function seconds(value) {
    return `${Number(value).toFixed(1)} s`;
  }

  function providerName(provider) {
    const names = { meta: "Meta Model API", baseten: "Baseten", fireworks: "Fireworks" };
    return names[provider] || provider;
  }

  function createBarLine(label, value, className) {
    const line = document.createElement("div");
    line.className = "chart-bar-line";
    line.setAttribute("aria-label", `${label}: ${value}%`);

    const barLabel = document.createElement("span");
    barLabel.className = "bar-label";
    barLabel.textContent = label;
    const track = document.createElement("span");
    track.className = "bar-track";
    const fill = document.createElement("span");
    fill.className = `bar-fill ${className}`;
    fill.style.setProperty("--bar-width", `${value}%`);
    track.append(fill);
    const barValue = document.createElement("strong");
    barValue.className = "bar-value";
    barValue.textContent = `${value}%`;
    line.append(barLabel, track, barValue);
    return line;
  }

  function renderChart(data) {
    const chart = $("#chart");
    if (!chart || !data.chart) return;
    const caption = $(".chart-caption");
    if (caption) caption.textContent = getCopy("results.caption")(data.eval.claim_count);
    chart.replaceChildren();
    data.chart.filter(item => chartProvider === "all" || item.id === chartProvider).forEach((item) => {
      const row = document.createElement("div");
      row.className = "chart-row";
      const provider = document.createElement("strong");
      provider.className = "chart-provider";
      provider.textContent = providerLabel(item.id);
      row.append(provider);
      row.append(createBarLine(getCopy("results.without"), item.without.percent, "is-without"));
      row.append(createBarLine(getCopy("results.withChecks"), item.with_checks.percent, "is-with-checks"));
      chart.append(row);
    });
  }

  function renderPosthocRerun(data) {
    const block = $("#posthoc-rerun");
    const rows = $("#posthoc-rows");
    if (!block || !rows) return;
    block.hidden = !data.posthoc_rerun;
    rows.replaceChildren();
    if (!data.posthoc_rerun) return;
    data.posthoc_rerun.systems.forEach((system) => {
      const row = document.createElement("tr");
      const provider = document.createElement("th");
      provider.scope = "row";
      provider.textContent = system.provider;
      const accuracy = document.createElement("td");
      accuracy.textContent = `${percent(system.v2.accuracy, 1)} → ${percent(system.rerun.accuracy, 1)}`;
      const falseSupported = document.createElement("td");
      falseSupported.textContent = `${system.v2.false_supported} → ${system.rerun.false_supported}`;
      row.append(provider, accuracy, falseSupported);
      rows.append(row);
    });
    $("#posthoc-report").href = data.posthoc_rerun.report_url;
  }

  function addResearchItem(list, text) {
    const item = document.createElement("li");
    item.textContent = text;
    list.append(item);
  }

  function renderResearch(data) {
    const list = $("#research-list");
    if (!list || !data.research) return;
    list.replaceChildren();
    const research = data.research;

    const ciText = Object.entries(research.confidence_intervals)
      .map(([provider, values]) => `${providerName(provider)} ${getCopy("results.without")} ${range(values.without)}, ${getCopy("results.withChecks")} ${range(values.with_checks)}`)
      .join("; ");
    addResearchItem(list, `${getCopy("research.ci")}: ${ciText}.`);

    const pairedText = Object.entries(research.paired)
      .map(([provider, values]) => `${providerName(provider)} +${values.points} points, p ${values.mcnemar_exact_p < 0.0001 ? "< 0.0001" : `= ${values.mcnemar_exact_p.toFixed(4)}`}`)
      .join("; ");
    addResearchItem(list, `${getCopy("research.paired")}: ${pairedText}.`);

    const costText = Object.entries(research.cost_latency)
      .map(([provider, values]) => `${providerName(provider)} ${getCopy("results.withChecks")} ${cost(values.with_checks.cost_mean)}, ${seconds(values.with_checks.latency_mean_s)}`)
      .join("; ");
    addResearchItem(list, `${getCopy("research.costLatency")}: ${costText}.`);

    const weakText = research.families
      .map((family) => {
        const label = getCopy("research.familyLabels")[family.id] || family.id;
        const meta = family.systems["agent@meta"];
        const baseten = family.systems["agent@baseten"];
        const fireworks = family.systems["agent@fireworks"];
        return `${label}: Meta ${meta.correct}/${meta.n}, Baseten ${baseten.correct}/${baseten.n}, Fireworks ${fireworks.correct}/${fireworks.n}`;
      })
      .join("; ");
    addResearchItem(list, `${getCopy("research.weakSpots")}: ${weakText}.`);

    const corrections = pageLanguage === "zh" ? getCopy("research.goldCorrections") : research.gold_corrections;
    corrections.forEach((correction) => addResearchItem(list, correction));
  }

  function historyTime(value, now = new Date()) {
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return "—";
    const day = date.toISOString().slice(0, 10), today = now.toISOString().slice(0, 10);
    const yesterday = new Date(now.getTime() - 86400000).toISOString().slice(0, 10);
    const relative = day === today ? getCopy("presentation.today") : day === yesterday ? getCopy("presentation.yesterday") : day;
    return `${date.toISOString().slice(11, 16)} ${getCopy("presentation.utc")} · ${relative}`;
  }

  const savedExampleRequests = new Map();
  function readExampleSaved(id) {
    if (savedExampleRecords.has(id)) return Promise.resolve(savedExampleRecords.get(id));
    if (savedExampleRequests.has(id)) return savedExampleRequests.get(id);
    const request = (async () => {
      const response = await fetch(`/data/examples/${encodeURIComponent(id)}.json`, { cache: "no-store" });
      if (!response.ok) throw Error("saved example pending");
      const result = await response.json();
      if (result.mode !== "recorded" || result.input?.example_id !== id || typeof result.input.text_read !== "string") throw Error("invalid saved example");
      savedExampleRecords.set(id, result);
      return result;
    })();
    savedExampleRequests.set(id, request);
    request.finally(() => savedExampleRequests.delete(id)).catch(() => {});
    return request;
  }

  function savedRecordingLabel(result) {
    const path = String(result.recording?.receipt || result.source || "");
    const compact = path.match(/(?:^|\/)(\d{4})(\d{2})(\d{2})T\d/);
    const recordedDate = path.match(/\d{4}-\d{2}-\d{2}/)?.[0] ||
      (compact ? `${compact[1]}-${compact[2]}-${compact[3]}` : null);
    const timestamp = result.recording?.recorded_at || result.recorded_at ||
      result.events?.find(event => event.timestamp)?.timestamp || recordedDate;
    const date = timestamp && Number.isFinite(Date.parse(timestamp)) ? new Date(timestamp).toISOString().slice(0, 10) : liveCopy("notRecorded");
    return `${getCopy("presentation.savedOn")} ${date} · ${providerLabel(runReceipt(result).provider || result.provider)}`;
  }

  function renderFollowNumber() {
    const panel = $("#follow-panel");
    if (!panel || !followRecord) return;
    const claim = followRecord.claims.find(row => row.program_verdict === "contradicted");
    const fact = followRecord.evidence.find(row => claim?.evidence_ids?.includes(row.evidence_id));
    if (!claim || !fact) throw Error("saved claim has no matching fact");
    panel.replaceChildren();
    panel.setAttribute("aria-labelledby", `follow-step-${followStep}`);
    const heading = liveNode("h3", getCopy(`presentation.${["claim", "fact", "check"][followStep - 1]}`));
    panel.append(heading);
    if (followStep === 1) {
      panel.append(liveNode("p", getCopy("presentation.claimNote")));
      // These fields come directly from the saved claim and its bound SEC fact.
      const snapshot = pageLanguage === "zh" ? { 代號: fact.ticker, 期間: fact.period, 主張值: claim.stated_value, 證據: claim.evidence_ids }
        : { ticker: fact.ticker, period: fact.period, stated_value: claim.stated_value, evidence_ids: claim.evidence_ids };
      const pre = liveNode("pre"); pre.append(liveNode("code", JSON.stringify(snapshot, null, 2))); panel.append(pre);
    } else if (followStep === 2) {
      const list = liveNode("dl", null, "follow-values");
      panel.append(list);
      (fact.components || [fact]).forEach((component, index) => {
        list.append(liveNode("dt", getCopy(`presentation.${index === 0 ? "annual" : "nineMonths"}`)),
          liveNode("dd", financialNumber(component.value)));
        // SEC archive URL derived from the retained CIK/accession, never model text.
        const url = component.filing_url || (fact.cik && component.accn ? `https://www.sec.gov/Archives/edgar/data/${Number(fact.cik)}/${component.accn.replaceAll("-", "")}/` : null);
        const link = secLink(url, `${component.form} · ${component.filed} · ${getCopy("presentation.source")}`);
        if (link) panel.append(link);
      });
      list.append(liveNode("dt", getCopy("presentation.quarter")), liveNode("dd", financialNumber(fact.value)));
    } else {
      const list = liveNode("dl", null, "follow-values");
      [["stated", claim.stated_value], ["actual", claim.actual_value], ["tolerance", claim.tolerance]].forEach(([key, value]) => {
        list.append(liveNode("dt", liveCopy(key)), liveNode("dd", liveNumber(value)));
      });
      panel.append(list);
      const pre = liveNode("pre");
      pre.append(liveNode("code", `abs(${claim.actual_value} − ${claim.stated_value}) > ${claim.tolerance}`));
      panel.append(pre, liveNode("strong", liveVerdict(claim.program_verdict), `follow-verdict is-${claim.program_verdict}`));
    }
  }

  async function setupFollowNumber() {
    const panel = $("#follow-panel");
    if (!panel) return;
    const tabs = $$('[data-follow-step]');
    const select = (tab) => {
      followStep = Number(tab.dataset.followStep);
      tabs.forEach(other => { const active = other === tab; other.setAttribute("aria-selected", String(active)); other.setAttribute("tabindex", active ? "0" : "-1"); });
      renderFollowNumber();
    };
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => select(tab));
      tab.addEventListener("keydown", event => {
        const next = event.key === "Home" ? 0 : event.key === "End" ? 2 : ["ArrowRight", "ArrowDown"].includes(event.key) ? (index + 1) % 3 : ["ArrowLeft", "ArrowUp"].includes(event.key) ? (index + 2) % 3 : null;
        if (next !== null) { event.preventDefault(); select(tabs[next]); tabs[next].focus(); }
      });
    });
    try {
      const response = await fetch("/data/live-demo-post.json", { cache: "no-store" });
      if (!response.ok) throw Error("missing saved check");
      followRecord = await response.json();
      renderFollowNumber();
    } catch { followRecord = null; panel.replaceChildren(liveNode("p", getCopy("presentation.failed"))); }
  }

  function setupControls() {
    $$('[data-chart-provider]').forEach(button => button.addEventListener("click", () => {
      chartProvider = button.dataset.chartProvider;
      $$('[data-chart-provider]').forEach(other => other.setAttribute("aria-pressed", String(other === button)));
      if (siteData) renderChart(siteData);
    }));
    const revealSavedCheck = () => {
      const saved = $("#saved-check-details");
      if (saved && window.location.hash === "#recorded-run") {
        saved.open = true;
        if (savedDemoKind !== "post") selectSavedDemo("post");
      }
    };
    $$('a[href="#recorded-run"]').forEach((link) => {
      link.addEventListener("click", () => {
        const saved = $("#saved-check-details");
        if (saved) saved.open = true;
        if (savedDemoKind !== "post") selectSavedDemo("post");
      });
    });
    window.addEventListener("hashchange", revealSavedCheck);
    revealSavedCheck();
    $$('[data-example]').forEach((button) => {
      button.addEventListener("click", () => {
        exampleLanguage = button.dataset.example === "zh" ? "zh" : "en";
        $$('[data-example]').forEach((other) => {
          const active = other === button;
          other.classList.toggle("is-active", active);
          other.setAttribute("aria-selected", String(active));
        });
        if (siteData) renderExample(siteData.examples[exampleLanguage]);
      });
    });
  }

  async function loadData() {
    try {
      const response = await fetch("/data/site.json", { cache: "no-store" });
      if (!response.ok) throw new Error("site data unavailable");
      siteData = await response.json();
      renderStampScene();
      if (document.documentElement.dataset.evidenceTour !== undefined) renderExample(siteData.examples[exampleLanguage] || siteData.examples.en);
      renderChart(siteData);
      if (document.documentElement.dataset.evidenceTour !== undefined) {
        renderPosthocRerun(siteData);
        renderResearch(siteData);
      }
    } catch (_error) {
      const list = $("#claim-list");
      if (list) {
        list.replaceChildren();
        const message = document.createElement("p");
        message.className = "data-loading";
        message.textContent = getCopy("example.unavailable");
        list.append(message);
      }
    }
  }

  setupLive();
  setupFilingDialog();
  setupControls();
  setupFollowNumber();
  applyCopy();
  loadData();
})();
