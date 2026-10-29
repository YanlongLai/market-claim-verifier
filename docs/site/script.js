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
      nav: { how: "How it works", results: "Results", trust: "Trust" },
      hero: {
        titleLine1: "Paste a finance post.",
        titleLine2: "See what's true.",
        lede: "Every checked number links to the SEC filing that proves it."
      },
      stamps: {
        region: "Real finance claims pass through the checker and receive True, False, or Can't check stamps.",
        gate: "Muse Spark agent + SEC check",
        claims: "Claims and report verdicts",
        thread: "Thread",
        social: "Social post",
        pause: "Pause animation",
        play: "Play animation",
        true: "TRUE",
        false: "FALSE",
        unknown: "CAN'T CHECK"
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
          title: "Find every money claim",
          body: "The AI uses Meta's Muse Spark models to find each number, period, and comparison in the post."
        },
        step2: {
          title: "Open the official filing",
          body: "It looks up the company's SEC filing for the same company, number, and time period."
        },
        step3: {
          title: "Let code decide",
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
      nav: { how: "運作方式", results: "結果", trust: "為什麼可信" },
      hero: {
        titleLine1: "貼上一則財經貼文。",
        titleLine2: "看看哪些數字是真的。",
        lede: "每個查過的數字，都連到證明它的 SEC 申報文件。"
      },
      stamps: {
        region: "真實財經說法通過查核，蓋上正確、錯誤或無法查核的印章。",
        gate: "Muse Spark 代理 + SEC 查核",
        claims: "說法與報告判定",
        thread: "討論串",
        social: "社群貼文",
        pause: "暫停動畫",
        play: "播放動畫",
        true: "正確",
        false: "錯誤",
        unknown: "無法查核"
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
          title: "找出每個財務說法",
          body: "AI 使用 Meta 的 Muse Spark 模型，找出貼文裡每個數字、期間和比較。"
        },
        step2: {
          title: "打開官方申報文件",
          body: "它查找同一家公司、數字和期間的 SEC 申報文件。"
        },
        step3: {
          title: "讓程式做決定",
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
    const track = $("#stamp-track");
    const list = $("#stamp-static-list");
    const pause = $("#stamp-pause");
    const gateBeam = scene.querySelector(".stamp-gate-beam");
    const gateLabel = scene.querySelector(".stamp-gate-label");
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const narrowViewport = window.matchMedia("(max-width: 639px)");
    const TRAVEL = 6000;
    const DESKTOP_INTERVAL = 2000;
    const NARROW_INTERVAL = 2500;
    const CROSSING = TRAVEL / 2;
    const clamp = (value) => Math.max(0, Math.min(1, value));
    const easeOut = (value) => 1 - Math.pow(1 - clamp(value), 3);
    let elapsed = CROSSING;
    let interval = DESKTOP_INTERVAL;
    let loop = cards.length * interval;
    let lastFrame = null;
    let frame = null;
    let inView = false;
    let userPaused = false;
    let width = 0;
    let cardWidth = 0;

    function refreshTiming() {
      interval = narrowViewport.matches ? NARROW_INTERVAL : DESKTOP_INTERVAL;
      loop = cards.length * interval;
    }

    function makeCard(card, index, isStatic) {
      const body = document.createElement(isStatic ? "a" : "article");
      body.className = `stamp-card ${verdictClass(card)}`;
      body.dataset.cardId = card.id;
      // Stable per-claim variation, including when the list loops or language changes.
      const hash = Array.from(card.id).reduce((value, character) => (value * 31 + character.charCodeAt(0)) >>> 0, 0);
      const angle = (hash % 21) - 12;
      body.style.setProperty("--stamp-angle", `${angle}deg`);
      // GitHub Pages publishes docs/ as its root; this also works in the checkout.
      if (isStatic) body.href = card.filing_url || card.source_report.replace(/^docs\//, "../");

      const header = document.createElement("div");
      header.className = "stamp-card-header";
      const ticker = document.createElement("span");
      ticker.className = "stamp-ticker";
      ticker.textContent = `$${card.ticker}`;
      const source = document.createElement("span");
      source.className = "stamp-source";
      header.append(ticker, source);
      const claim = document.createElement("p");
      claim.className = "stamp-claim";

      const mark = document.createElement("span");
      mark.className = "stamp-mark";
      const impression = document.createElement("span");
      impression.className = "stamp-impression";
      mark.append(impression);
      let bleed = null;
      let scan = null;
      if (!isStatic) {
        bleed = document.createElement("span");
        bleed.className = "stamp-bleed";
        bleed.setAttribute("aria-hidden", "true");
        mark.append(bleed);
        const scanClip = document.createElement("span");
        scanClip.className = "stamp-scan";
        scan = document.createElement("span");
        scan.className = "stamp-scan-light";
        scanClip.append(scan);
        body.append(scanClip);
      }

      body.append(header, claim, mark);
      let evidence = null;
      if (card.evidence_label) {
        evidence = document.createElement("span");
        evidence.className = "stamp-evidence";
        evidence.textContent = card.evidence_label;
        body.append(evidence);
      }

      const carrier = document.createElement(isStatic ? "li" : "div");
      carrier.className = isStatic ? "stamp-static-item" : "stamp-carrier";
      carrier.append(body);
      (isStatic ? list : track).append(carrier);
      return { card, index, angle, body, source, claim, mark, impression, bleed, evidence, scan, carrier };
    }

    const moving = cards.map((card, index) => makeCard(card, index, false));
    const still = cards.map((card, index) => makeCard(card, index, true));

    function localize() {
      [...moving, ...still].forEach((item) => {
        item.claim.textContent = item.card.text[pageLanguage];
        item.source.textContent = getCopy(`stamps.${item.card.source_kind}`);
        const verdict = item.card.verdict === "supported" ? "true" : item.card.verdict === "contradicted" ? "false" : "unknown";
        item.impression.textContent = getCopy(`stamps.${verdict}`);
        if (item.bleed) item.bleed.textContent = item.impression.textContent;
      });
      pause.textContent = getCopy(userPaused ? "stamps.play" : "stamps.pause");
      // A language switch changes the card's intrinsic text width. Repaint the
      // current frame now so a later console seek cannot inherit a stale layout.
      measure();
    }

    function measure() {
      refreshTiming();
      width = scene.clientWidth;
      // The accessible list also has measurable card widths in reduced-motion mode.
      cardWidth = still[0].body.getBoundingClientRect().width;
      // Cards must never overlap: on narrow screens the fixed interval gives a pitch smaller than the card.
      if (width + cardWidth > 0) {
        interval = Math.max(interval, Math.ceil(TRAVEL * (cardWidth + 24) / (width + cardWidth)));
        loop = cards.length * interval;
      }
      paint();
    }

    function paint() {
      let gatePulse = 0;
      moving.forEach((item) => {
        const age = ((elapsed - item.index * interval) % loop + loop) % loop;
        const visible = age < TRAVEL;
        if (item.carrier.hidden !== !visible) item.carrier.hidden = !visible;
        if (!visible) return;
        const progress = age / TRAVEL;
        item.carrier.style.transform = `translate3d(${-cardWidth + (width + cardWidth) * progress}px, 0, 0)`;
        item.carrier.style.opacity = String(Math.min(clamp(progress / 0.08), clamp((1 - progress) / 0.12)));
        // Outgoing cards must stay above incoming cards until they leave the track.
        // Demoting them one second after the gate hid stamps on overlapping cards.
        // Only change stacking at discrete stages; animate transform/opacity only.
        const layer = 1 + Math.floor(age / interval);
        if (item.layer !== layer) {
          item.carrier.style.zIndex = String(layer);
          item.layer = layer;
        }

        // Start 400 ms early so the stamp lands with the card centred on the gate, not past it.
        const sinceGate = age - (CROSSING - 400);
        const sweep = clamp(sinceGate / 300);
        item.scan.style.transform = `translate3d(${(cardWidth + 48) * sweep - 48}px, 0, 0)`;
        item.scan.style.opacity = String(sinceGate >= 0 && sinceGate < 300 ? Math.sin(sweep * Math.PI) * 0.28 : 0);
        if (item.evidence) {
          const pop = easeOut((sinceGate - 300) / 100);
          item.evidence.style.opacity = String(pop);
          item.evidence.style.transform = `translateY(${6 * (1 - pop)}px) scale(${0.9 + pop * 0.1})`;
        }

        // 300ms sweep → 100ms evidence pop → 300ms impact/ink settle (700ms total).
        const impact = sinceGate - 400;
        const phase = impact >= 0 ? "stamped" : sinceGate >= 300 ? "evidence" : sinceGate >= 0 ? "scanning" : "incoming";
        if (item.body.dataset.phase !== phase) item.body.dataset.phase = phase;
        let scale = 1;
        if (impact < 0) scale = 1.8;
        else if (impact < 105) scale = 1.8 - 0.86 * easeOut(impact / 105);
        else if (impact < 160) scale = 0.94 + 0.10 * easeOut((impact - 105) / 55);
        else if (impact < 200) scale = 1.04 - 0.04 * easeOut((impact - 160) / 40);
        item.mark.style.transform = `rotate(${item.angle}deg) scale(${scale})`;
        item.mark.style.opacity = String(clamp(impact / 45));
        // The permanent impression and a little ink bleed survive the impact.
        // Reset only when this card is recycled to the incoming side of the loop.
        item.bleed.style.opacity = String(impact >= 0 ? 0.12 + 0.88 * (1 - clamp((impact - 150) / 150)) : 0);
        const shakeAge = impact - 105;
        const shake = shakeAge >= 0 && shakeAge < 150 ? Math.sin(shakeAge / 13) * 3 * (1 - shakeAge / 150) : 0;
        item.body.style.transform = `translate3d(${shake}px, ${shake * 0.5}px, 0)`;
        gatePulse = Math.max(gatePulse, clamp(1 - Math.abs(impact - 105) / 180));
      });
      gateBeam.style.transform = `scaleY(${0.7 + Math.sin(elapsed / interval * Math.PI * 2) * 0.15})`;
      gateBeam.style.opacity = String(0.4 + Math.sin(elapsed / interval * Math.PI * 2) * 0.15);
      // Reduced motion keeps the pill completely still, including when seeking.
      if (motion.matches) gatePulse = 0;
      gateLabel.style.transform = `translateX(-50%) scale(${1 + gatePulse * 0.06})`;
      gateLabel.style.opacity = String(0.88 + gatePulse * 0.12);
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
      lastFrame = null; // Resuming must not jump through time spent off-screen/hidden.
      const animated = !motion.matches;
      scene.dataset.animated = String(animated);
      list.classList.toggle("is-sr-only", animated);
      still.forEach((item) => { item.body.tabIndex = animated ? -1 : 0; });
      const running = animated && inView && !document.hidden && !userPaused;
      scene.dataset.running = String(running);
      pause.setAttribute("aria-pressed", String(userPaused));
      localize();
      if (running) frame = requestAnimationFrame(tick);
    }

    function seek(seconds) {
      if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) {
        throw new RangeError("Stamp scene time must be a finite, non-negative number of seconds.");
      }
      measure(); // Normalize against the measured spacing, including the narrow-screen minimum gap.
      // Keep console seeks on the same millisecond grid as animation frames so
      // exact boundary states do not drift through floating-point remainders.
      elapsed = Math.round((seconds % (loop / 1000)) * 1000);
      userPaused = true;
      updatePlayback();
      measure();
      return elapsed / 1000;
    }

    window.__stampScene = Object.freeze({ seek });

    // A failed mask image must never erase the permanent stamp. Enable the grain
    // only after the existing local asset loads; otherwise leave solid ink.
    const ink = document.createElement("img");
    ink.addEventListener("load", () => { scene.classList.toggle("has-stamp-ink", ink.naturalWidth > 0); });
    ink.addEventListener("error", () => { scene.classList.toggle("has-stamp-ink", false); });
    ink.src = "img/stamp-ink.webp";

    pause.addEventListener("click", () => {
      userPaused = !userPaused;
      updatePlayback();
    });
    document.addEventListener("visibilitychange", updatePlayback);
    motion.addEventListener("change", () => { updatePlayback(); measure(); });
    narrowViewport.addEventListener("change", measure);
    scene.hidden = false;
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(([entry]) => {
        inView = entry.isIntersecting;
        updatePlayback();
      });
      observer.observe(scene);
    } else {
      inView = true;
    }
    if ("ResizeObserver" in window) new ResizeObserver(measure).observe(scene);
    else window.addEventListener("resize", measure);
    const requestedTime = new URLSearchParams(window.location.search).get("stamp-t");
    const seconds = requestedTime === null || requestedTime.trim() === "" ? NaN : Number(requestedTime);
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
