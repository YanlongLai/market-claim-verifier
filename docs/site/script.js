(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const LANGUAGE_KEY = "market-claim-verifier-language";

  const COPY = {
    en: {
      metaTitle: "Market claim verifier",
      metaDescription: "Paste a finance post and check its numbers against SEC filings.",
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
        noNumberExplanation: "Filings report results, not opinions or forecasts.",
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
        audience: "Public", transcript: "Transcript", by: "By",
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
        chinese: "中文貼文",
        postLabel: "Post",
        loading: "Loading the report...",
        unavailable: "The report is not available in this view.",
        claimCount: (count) => `${count} claims found`
      },
      verdict: { true: "True", false: "False", unknown: "Can't check" },
      claimKind: { reported_fact: "Money claim", forecast: "Forecast", opinion: "Opinion" },
      claimSource: {
        sec: "SEC says",
        filed: "filed",
        see: "See filing",
        derived: "SEC check",
        notChecked: "Forecasts and opinions are not checked.",
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
        top: "Back to top ↑"
      }
    },
    zh: {
      metaTitle: "Market claim verifier｜財經說法查核",
      metaDescription: "貼上財經貼文，將其中的數字與 SEC 申報文件比對。",
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
        noNumberExplanation: "財報記錄已發生的結果，不包含看法或預測。",
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
        audience: "公開", transcript: "逐字稿", by: "作者",
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
      claimKind: { reported_fact: "財務說法", forecast: "預測", opinion: "看法" },
      claimSource: {
        sec: "SEC 顯示",
        filed: "申報日期",
        see: "查看申報文件",
        derived: "SEC 查核",
        notChecked: "預測和看法不在查核範圍內。",
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
        top: "回到頂端 ↑"
      }
    }
  };

  let pageLanguage = readLanguage();
  let exampleLanguage = pageLanguage;
  let siteData = null;
  let stampConveyor = null;
  let activeFilingClaim = null;
  let filingReturnFocus = null;

  function readLanguage() {
    try {
      return localStorage.getItem(LANGUAGE_KEY) === "zh" ? "zh" : "en";
    } catch (_error) {
      return "en";
    }
  }

  function saveLanguage(language) {
    try {
      localStorage.setItem(LANGUAGE_KEY, language);
    } catch (_error) {
      // Private browsing and locked-down embeds can reject storage.
    }
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

    $$('[data-language]').forEach((button) => {
      const active = button.dataset.language === pageLanguage;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });

    $$('[data-example]').forEach((button) => {
      const active = button.dataset.example === exampleLanguage;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });

    const closeButton = $("#filing-dialog-close");
    if (closeButton) closeButton.setAttribute("aria-label", getCopy("filing.close"));

    if (siteData) {
      renderStampScene();
      renderExample(siteData.examples[exampleLanguage]);
      renderChart(siteData);
      renderPosthocRerun(siteData);
      renderResearch(siteData);
      const dialog = $("#filing-dialog");
      if (activeFilingClaim && dialog && dialog.open) renderFilingDialog(activeFilingClaim);
    }
  }

  function renderStampScene() {
    if (!siteData.stamp_cards || !siteData.stamp_cards.length) return;
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
    const checkable = (card) => card.score !== null && card.score !== undefined;
    const durations = cards.map((card) => checkable(card) ? CHECKABLE : UNCHECKABLE);
    const starts = durations.reduce((times, duration) => [...times, times[times.length - 1] + duration], [0]);
    const loop = starts.pop();
    const floatCycles = Math.round(loop / FLOAT_PERIOD);
    const clamp = (value) => Math.max(0, Math.min(1, value));
    const easeOut = (value) => 1 - Math.pow(1 - clamp(value), 3);
    const fadeIn = (age, at) => clamp((age - at) / FADE);
    const compact = (value) => (value || "").replace(/-?\d+\.\d+/, (number) => Number(number).toFixed(1));
    const poseFallbacks = { reach: "present", point: "present", think: "inspect", "stamp-down": "stamp",
      approve: "idle", concern: "idle", shrug: "idle" };
    const facing = { idle: "front", inspect: "post", present: "filing", reach: "filing", point: "filing",
      think: "front", stamp: "post", "stamp-down": "post", approve: "front", concern: "front", shrug: "front" };
    let elapsed = 0;
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
      // Current recorded inputs are text. No waveform, frame or timestamp is
      // fabricated for them; future variants require their actual payload.
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
      if (timestamp && kind !== "screenshot") body.append(element("time", "stamp-media-time", data.timestamp));
      const quote = kind === "audio" ? element("blockquote", "stamp-transcript") : null;
      if (quote) body.append(quote);
      return { badge, kind, body, quote, transcript: data.transcript };
    }

    function paperDetails(parent, isStatic = false) {
      const grain = polishImage("img/polish/paper-grain.webp", "stamp-paper-grain", 256, 256, isStatic);
      grain.addEventListener("load", () => parent.classList.toggle("has-paper-grain", true));
      parent.append(grain,
        polishImage("img/polish/stack-edge.webp", "stamp-stack-edge", 384, 96, isStatic),
        polishImage("img/polish/paperclip.webp", "stamp-paperclip", 96, 160, isStatic));
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
      image.loading = "lazy";
      image.decoding = "async";
      image.dataset.pose = name;
      image.dataset.facing = facing[name];
      image.addEventListener("error", () => {
        const fallback = poseFallbacks[name];
        if (fallback && image.dataset.asset !== fallback) {
          image.dataset.asset = fallback;
          image.src = `img/auditor/H/${fallback}.webp`;
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
        image.src = `img/auditor/H/${name}.webp`;
      });
      thrusters.forEach(({ frames }) => frames.forEach((image) => {
        image.src = `img/auditor/H/thruster-${image.dataset.frame}.webp`;
      }));
      // A failed ink texture leaves solid, readable stamp text.
      const ink = element("img", "");
      ink.decoding = "async";
      ink.addEventListener("load", () => scene.classList.toggle("has-stamp-ink", ink.naturalWidth > 0));
      ink.addEventListener("error", () => scene.classList.remove("has-stamp-ink"));
      ink.src = "img/stamp-ink.webp";
      Object.entries(fx.sources).forEach(([name, sources]) => {
        const image = element("img", "stamp-fx-preload"), url = `img/fx/${name}.webp`;
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
      passage.dataset.cardId = card.id;
      const header = element("div", "stamp-passage-header");
      header.append(element("p", "stamp-filing-authority", "UNITED STATES SECURITIES AND EXCHANGE COMMISSION"));
      const formLine = element("div", "stamp-form-line");
      const dateStamp = element("span", "stamp-filing-date");
      const filedDate = element("time", "");
      filedDate.dateTime = source.filed;
      dateStamp.append(polishImage("img/polish/ink-ring.webp", "stamp-date-ring", 256, 128, isStatic), filedDate);
      formLine.append(element("p", "stamp-passage-meta", `FORM ${source.form}`), dateStamp);
      header.append(formLine);
      header.append(element("p", "stamp-passage-company", source.company));
      if (source.section_title) header.append(element("p", "stamp-passage-section", source.section_title));
      const period = element("p", "stamp-passage-period");
      header.append(period);
      const details = element("div", "stamp-passage-details");
      const row = element("p", "stamp-passage-row");
      const fact = element("mark", "stamp-fact");
      const sweep = element("span", "stamp-amber-sweep");
      fact.append(sweep, element("strong", "", source.value));
      if (source.type === "table") {
        row.append(element("span", "stamp-row-label", source.row_label), fact);
      } else {
        const offset = source.text.indexOf(source.value);
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
        compare, statedLabel, filedLabel, statedValue, filedValue, filedDate };
    }
    function makeCard(card, index, isStatic) {
      const body = element(isStatic ? "a" : "article", `stamp-card ${verdictClass(card)}`);
      body.dataset.cardId = card.id;
      body.dataset.sourceKind = card.source_kind;
      body.dataset.severity = card.severity || "unknown";
      const hash = Array.from(card.id).reduce((value, character) => (value * 31 + character.charCodeAt(0)) >>> 0, 0);
      const angle = (hash % 13) - 6;
      body.style.setProperty("--stamp-angle", `${angle}deg`);
      if (isStatic) body.href = card.filing_url || card.source_report.replace(/^docs\//, "../");
      const postHeader = element("div", "stamp-post-header");
      const avatar = element("img", "stamp-avatar");
      avatar.alt = "";
      avatar.width = 56;
      avatar.height = 56;
      avatar.loading = "lazy";
      avatar.decoding = "async";
      avatar.src = card.persona.avatar;
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
          originalAvatar.src = original.persona.avatar;
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
        const masthead = polishImage("img/polish/banana-masthead.webp", "stamp-masthead", 520, 96, isStatic);
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
        if (item.reposted) item.reposted.textContent = `${getCopy("stamps.repostedFrom")} ${card.reposted_from}`;
        item.period.textContent = item.meter ? `${getCopy("stamps.claim")}: ${compact(card.stated_value_display)} · ${card.period[pageLanguage]}` : getCopy("stamps.noClaim");
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
            item.meter ? getCopy("stamps.caption.compare")(compact(card.filed_value_display), compact(card.stated_value_display)) : "",
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
        } else item.gap.textContent = getCopy(`claimKind.${card.kind}`);
        if (item.passage) {
          const source = card.excerpt;
          item.passage.filedDate.textContent = `${getCopy("stamps.filed")} ${source.filed}`;
          item.passage.period.textContent = source.derivation ? `${source.derivation.label[pageLanguage]} · ${source.period_header}` : source.period_header;
          item.passage.units.textContent = source.fact.scale === 6 ? getCopy("stamps.millions") : getCopy("stamps.filingUnits");
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
      const canCheck = !!active.meter;
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
        item.carrier.hidden = !selected || age >= (item.meter ? REST : UNCHECKABLE);
        const itemPhase = selected ? phase : "rest";
        item.body.dataset.phase = itemPhase;
        if (item.passage) item.passage.body.hidden = !selected || age >= REST;
        const itemExit = item.meter ? EXIT : UNKNOWN_EXIT;
        const leave = clamp((age - itemExit) / 800);
        const x = age < READ ? -cardWidth * (1 - easeOut(age / READ)) : (cardWidth + 24) * easeOut(leave);
        item.carrier.style.transform = `translate3d(${x}px, 0, 0)`;
        item.carrier.style.opacity = String(age < READ ? clamp(age / 160) : 1 - leave);
        const scanning = age >= READ && age < REACH;
        const sweep = clamp((age - READ) / (REACH - READ));
        item.scan.style.transform = `translate3d(${(cardWidth + 48) * sweep - 48}px, 0, 0)`;
        item.scan.style.opacity = String(scanning ? Math.sin(sweep * Math.PI) * 0.22 : 0);
        if (item.glow) item.glow.style.opacity = String(scanning ? Math.sin(sweep * Math.PI) * 0.35 : 0);
        item.period.style.opacity = String(fadeIn(age, item.meter ? READ : REACH));
        const scored = fadeIn(age, COMPARE);
        item.filed.style.opacity = String(item.meter ? scored : 0);
        item.assessment.style.opacity = String(item.meter ? scored : fadeIn(age, REACH));
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
        const impact = age - (item.meter ? STRIKE : UNKNOWN_STRIKE);
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
      const impact = age - (item.meter ? STRIKE : UNKNOWN_STRIKE);
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
        item.light = { post: box(item.number || item.claim), row, compare: box(passage.compare),
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

    window.__stampScene = Object.freeze({ seek, timing: Object.freeze({ checkable: CHECKABLE / 1000,
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
    const sign = value < 0 ? "-" : "";
    const absolute = Math.abs(value);
    if (pageLanguage === "zh") {
      if (absolute >= 100000000) return `${sign}${numberText(absolute / 100000000, 0)} 億美元`;
      if (absolute >= 10000) return `${sign}${numberText(absolute / 10000, 0)} 萬美元`;
      return `${sign}${numberText(absolute, 0)} 美元`;
    }
    if (absolute >= 1000000000) return `${sign}$${numberText(absolute / 1000000000)}B`;
    if (absolute >= 1000000) return `${sign}$${numberText(absolute / 1000000)}M`;
    return `${sign}$${numberText(absolute, 0)}`;
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
    return `$${Number(value).toFixed(3)}`;
  }

  function seconds(value) {
    return `${Number(value).toFixed(1)}s`;
  }

  function providerName(provider) {
    const names = { meta: "Meta API", baseten: "Baseten", fireworks: "Fireworks" };
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
    data.chart.forEach((item) => {
      const row = document.createElement("div");
      row.className = "chart-row";
      const provider = document.createElement("strong");
      provider.className = "chart-provider";
      provider.textContent = item.provider;
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

  function setupControls() {
    $$('[data-language]').forEach((button) => {
      button.addEventListener("click", () => {
        pageLanguage = button.dataset.language === "zh" ? "zh" : "en";
        exampleLanguage = pageLanguage;
        saveLanguage(pageLanguage);
        applyCopy();
      });
    });

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
      const response = await fetch("data/site.json", { cache: "no-store" });
      if (!response.ok) throw new Error("site data unavailable");
      siteData = await response.json();
      renderStampScene();
      renderExample(siteData.examples[exampleLanguage] || siteData.examples.en);
      renderChart(siteData);
      renderPosthocRerun(siteData);
      renderResearch(siteData);
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

  setupFilingDialog();
  setupControls();
  applyCopy();
  loadData();
})();
