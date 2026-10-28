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

    if (siteData) {
      renderExample(siteData.examples[exampleLanguage]);
      renderChart(siteData);
      renderResearch(siteData);
    }
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

  function appendSource(card, claim) {
    const sourceLine = document.createElement("p");
    sourceLine.className = "claim-source";
    const source = claim.source;

    if (!source) {
      sourceLine.textContent = getCopy("claimSource.notChecked");
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

    if (source.filing_url) {
      const link = document.createElement("a");
      link.href = source.filing_url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = getCopy("claimSource.see");
      sourceLine.append(link);
    }
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
      renderExample(siteData.examples[exampleLanguage] || siteData.examples.en);
      renderChart(siteData);
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

  setupControls();
  applyCopy();
  loadData();
})();
