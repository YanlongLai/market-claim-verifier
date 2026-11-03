export const COPY = {
  en: {
    skip: "Skip to content", navigation: "Page navigation", language: "Language", theme: "Theme", themeLabel: "Switch color theme",
    title: "In the wild", caughtNav: "Posts", coverageNav: "Coverage", fixesNav: "Fixes",
    lede: "What happens when the verifier meets real posts from DappGo News and Threads?", action: "Read the findings",
    study: "Development probes. Post-hoc labels. Not a held-out benchmark.", loading: "Loading the saved evidence…",
    unavailable: "Saved findings are unavailable. Required evidence must be merged and compiled before results can appear here.",
    caughtTitle: "Caught in the wild", caughtIntro: "Displayed numbers that conflict with primary sources. These are independent reference checks, separate from the agent’s outputs below.",
    translationNote: "A displayed unit error does not prove who caused it. Auto-translation is recorded where present; original-language causation was not verified.",
    unresolvedNote: "Claims without a resolved reporting period remain unscored. They are excluded from these conflict cards.",
    coverageTitle: "How much could it check?", coverageIntro: "Abstentions, skips, failures and budget stops stay visible. A supported output is not a measure of full-post coverage.",
    provider: "Provider", route: "Workflow", agent: "Direct claim agent", post: "Post extraction + verification",
    samplingNote: "Threads posts came from a selected Top-search sample. Reliable engagement counts were not recorded, so this is not a measured high-engagement population.",
    truthNote: "Only independently resolved primary-source items enter the truth denominator. Expected abstention on out-of-scope items is a policy check; unresolved items are not financial truth labels.",
    latencyNote: "Latency is observed wall time, including retrieval, caches and retries. Provider workers and some tests overlapped; this is not a controlled speed comparison. Budget stops have no latency sample.",
    costNote: "Costs are recorded token-rate estimates and retained reservations, not invoices. Cost per item uses every sampled item, including skips and failures.",
    newsLimit: "News limitations include issuer confusion between Hon Precision and Honeywell, plus retained paraphrase errors. Zero false support would not exclude erroneous contradictions.",
    fixesTitle: "What we fixed after this test", fixesIntro: "A recheck of known failures is post-hoc development evidence. The original results stay above.", noFixcheck: "No completed fix recheck is included in the available page data.",
    provenanceTitle: "Follow the receipts", provenanceIntro: "The page is compiled offline from retained inputs, reference labels, all result rows and accounting summaries. No model runs happen here.",
    hashes: "Source files and SHA-256 hashes", footer: "Check the number. Keep the context.", demo: "Open the saved demo", explorer: "Explore the original benchmark",
    contradicted: "Contradicted", supported: "Supported", insufficient_evidence: "Insufficient", skipped: "Skipped", failed: "Failed / partial", budget_stopped: "Budget stopped",
    displayed: "Post, paraphrased", filed: "Primary-source value", filing: "SEC source", reference: "Reference labels", shownTranslation: "Shown via auto-translation; cause unverified.", likelyTranslation: "Likely unit/translation error",
    news: "DappGo News feed", own_posts: "DappGo’s own Threads posts", third_party_threads: "Third-party Threads posts",
    phase: "Phase", items: "sampled items", attempted: "Attempted / sampled", outside: "Outside this filing check / expected abstention", taiwan: "Taiwan", price_moves: "price moves", private_companies: "private companies", other: "other scope limits",
    costItem: "Estimated USD / item", latency: "Latency: mean / p50 / p95", seconds: "s", latencySamples: "timed items",
    truth: "Primary truth correct", noTruth: "No resolved truth items", review: "Unresolved, unscored", report: "Study report", records: "Results and study records", rawData: "Page data", compiler: "Offline compiler",
    phaseCost: "Recorded phase totals across routes", mediaIncluded: "Threads includes the separate image-ingest routes; images are not shown on this page.",
    before: "Before", after: "After", fixEvidence: "Recheck evidence", reportWording: "Before/after cells retain the report’s original wording.", emptyCards: "No independently refuted third-party posts are recorded in these data.",
  },
  zh: {
    skip: "跳至內容", navigation: "頁面導覽", language: "語言", theme: "外觀", themeLabel: "切換明暗外觀",
    title: "真實貼文實測", caughtNav: "貼文", coverageNav: "涵蓋範圍", fixesNav: "修正",
    lede: "當查核器遇上 DappGo News 與 Threads 的真實財經貼文，會發生什麼事？", action: "閱讀實測發現",
    study: "開發探測。事後標記。非獨立保留測試。", loading: "正在載入已保存的證據…",
    unavailable: "目前無法顯示實測結果。須先合併必要證據並編譯資料，才會在此顯示結果。",
    caughtTitle: "在真實貼文中發現", caughtIntro: "畫面上的數字與第一手來源不符。這是獨立的參考答案查核，與下方模型輸出分開呈現。",
    translationNote: "顯示單位有誤，不代表已確認成因。資料會註明自動翻譯，但未驗證原文是否導致錯誤。",
    unresolvedNote: "無法確定報告期間的主張維持未評分，不列入這些數字衝突卡片。",
    coverageTitle: "究竟能查核多少？", coverageIntro: "證據不足、跳過、失敗與預算停止都保留。輸出「支持」不代表已涵蓋整篇貼文。",
    provider: "供應商", route: "流程", agent: "直接主張查核", post: "貼文擷取與查核",
    samplingNote: "Threads 貼文取自指定搜尋的「熱門」結果。未可靠記錄互動數，因此不能稱為經量測的高互動貼文母體。",
    truthNote: "只有經第一手來源獨立確認的項目才列入真實性分母。範圍外預期棄答屬政策檢查；未解項目並無財務真值標籤。",
    latencyNote: "延遲為觀察到的總耗時，包含檢索、快取與重試。不同供應商及部分測試同時執行，並非受控速度比較。預算停止項目沒有延遲樣本。",
    costNote: "費用依記錄中的 token 費率及保留預算估計，非供應商帳單。每項費用以全體抽樣項目為分母，包含跳過與失敗。",
    newsLimit: "News 測試限制包含將鴻海誤認為 Honeywell，以及保留下來的改寫錯誤。即使沒有錯誤支持，也不代表沒有錯誤反駁。",
    fixesTitle: "實測後修正了什麼", fixesIntro: "已知失敗案例的重測屬事後開發證據。上方仍保留原始結果。", noFixcheck: "目前頁面資料未包含已完成的修正重測。",
    provenanceTitle: "追溯每筆證據", provenanceIntro: "本頁離線編譯自保留的輸入、參考標籤、全部結果及費用摘要，不在此執行模型。",
    hashes: "來源檔案與 SHA-256 雜湊", footer: "核對數字，保留脈絡。", demo: "開啟已保存的示範", explorer: "探索原始評測",
    contradicted: "不符", supported: "支持", insufficient_evidence: "證據不足", skipped: "跳過", failed: "失敗／部分失敗", budget_stopped: "預算停止",
    displayed: "貼文主張（改寫）", filed: "第一手來源數值", filing: "SEC 來源", reference: "參考標籤", shownTranslation: "畫面顯示為自動翻譯；成因未確認。", likelyTranslation: "可能是單位或翻譯錯誤",
    news: "DappGo News 新聞動態", own_posts: "DappGo 自有 Threads 貼文", third_party_threads: "第三方 Threads 貼文",
    phase: "階段", items: "項抽樣", attempted: "已嘗試／抽樣", outside: "本查核範圍外／預期棄答", taiwan: "台灣", price_moves: "股價變動", private_companies: "未上市公司", other: "其他範圍限制",
    costItem: "每項估計費用（美元）", latency: "延遲：平均／中位／第 95 百分位", seconds: "秒", latencySamples: "項有耗時紀錄",
    truth: "第一手真值答對", noTruth: "無已解真值項目", review: "未解、未評分", report: "實測報告", records: "結果與實測紀錄", rawData: "頁面資料", compiler: "離線編譯器",
    phaseCost: "各流程合計的階段費用", mediaIncluded: "Threads 合計包含獨立圖片擷取流程；本頁未展示貼文圖片。",
    before: "修正前", after: "修正後", fixEvidence: "重測證據", reportWording: "前後對照欄保留報告原文。", emptyCards: "這份資料沒有經第一手來源獨立反駁的第三方貼文。",
  },
};

export function formatValue(raw, unit, language) {
  const value = Number(raw);
  const format = (n) => new Intl.NumberFormat(language === "zh" ? "zh-TW" : "en-US", { maximumFractionDigits: 6 }).format(n);
  if (unit === "percent") return `${format(value)}%`;
  if (language === "zh") return Math.abs(value) >= 1e8 ? `${format(value / 1e8)} 億美元` : `${format(value)} 美元`;
  if (Math.abs(value) >= 1e9) return `$${format(value / 1e9)} billion`;
  if (Math.abs(value) >= 1e6) return `$${format(value / 1e6)} million`;
  return `$${format(value)}`;
}

export function metricLabel(metric, language) {
  if (language === "en") return metric;
  return metric.replace(/FY(\d+) Q(\d) /, "$1 會計年度第 $2 季 ")
    .replace(/(\d+) Q(\d) /, "$1 年第 $2 季 ")
    .replace(/(\d+) annual revenue/, "$1 年度營收")
    .replace("year-over-year revenue growth", "營收年增率")
    .replace("Greater China revenue", "大中華區營收")
    .replace("iPhone revenue", "iPhone 營收")
    .replace("revenue", "營收");
}

export function repoLink(path) {
  if (!path.startsWith("docs/") || path.split("/").includes("..")) throw new Error("Expected a docs-relative evidence path");
  return `../${path.slice(5)}`;
}

function element(doc, tag, text, className) {
  const node = doc.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function link(doc, text, href, className) {
  const node = element(doc, "a", text, className);
  node.setAttribute("href", href);
  if (href.startsWith("https://")) node.setAttribute("rel", "noreferrer");
  return node;
}

export function renderCards(doc, data, language) {
  const copy = COPY[language];
  const root = doc.getElementById("cards");
  root.replaceChildren();
  if (!data.cards.length) root.append(element(doc, "p", copy.emptyCards));
  for (const card of data.cards) {
    const article = element(doc, "article", undefined, "post-card");
    const titleId = `post-${card.id}`;
    article.setAttribute("aria-labelledby", titleId);
    const header = element(doc, "header", undefined, "card-header");
    const attribution = element(doc, "div");
    const title = element(doc, "h3");
    title.id = titleId;
    title.append(link(doc, card.handle, card.post_url));
    const date = element(doc, "time", card.posted, "post-date");
    date.setAttribute("datetime", card.posted);
    attribution.append(title, date);
    header.append(attribution, element(doc, "p", copy.contradicted, "verdict"));
    const comparisons = element(doc, "div", undefined, "comparison-list");
    for (const row of card.components) {
      const comparison = element(doc, "div", undefined, "comparison");
      comparison.append(element(doc, "p", metricLabel(row.metric, language), "metric"));
      for (const [kind, label, value] of [["claimed", copy.displayed, row.claimed], ["filed", copy.filed, row.filed]]) {
        const group = element(doc, "div", undefined, kind);
        group.append(element(doc, "span", label, "value-label"), element(doc, "span", formatValue(value, row.unit, language), "value"));
        if (kind === "filed") group.append(link(doc, `${copy.filing} · ${row.tier}`, row.source_url, "filing-link"));
        comparison.append(group);
      }
      comparisons.append(comparison);
    }
    article.append(header, comparisons);
    if (card.likely_unit_translation_error) article.append(element(doc, "p", copy.likelyTranslation, "card-note"));
    else if (card.auto_translated) article.append(element(doc, "p", copy.shownTranslation, "card-note"));
    article.append(link(doc, `${copy.reference} · ${card.id}`, repoLink(card.evidence_path), "card-evidence"));
    root.append(article);
  }
}

export function renderCoverage(doc, data, language, provider, route) {
  const copy = COPY[language];
  const root = doc.getElementById("coverage-results");
  root.replaceChildren();
  const system = data.systems[`${provider}/${route}`];
  const time = (n) => n === null ? "—" : n > 0 && n < .01 ? "<0.01" : n.toFixed(2);
  for (const source of data.sources) {
    const row = system[source.id];
    const panel = element(doc, "article", undefined, "source-panel");
    const heading = element(doc, "div", undefined, "source-heading");
    heading.append(element(doc, "h3", copy[source.id]), element(doc, "span", `${row.items} ${copy.items} · ${copy.phase} ${source.phase}`, "sample-size"));
    const counts = element(doc, "dl", undefined, "outcomes");
    for (const key of ["supported", "contradicted", "insufficient_evidence", "skipped", "failed", "budget_stopped"]) {
      const group = element(doc, "div");
      const value = row.outcomes[key] + (key === "failed" ? row.outcomes.partial_failure : 0);
      group.append(element(doc, "dt", copy[key]), element(doc, "dd", String(value)));
      counts.append(group);
    }
    const detail = element(doc, "div", undefined, "source-detail");
    detail.append(element(doc, "p", `${copy.attempted}: ${row.attempted}/${row.items}`));
    const reasons = Object.entries(row.outside_check.by_reason).map(([key, count]) => `${copy[key]} ${count}`).join(" · ");
    detail.append(element(doc, "p", `${copy.outside}: ${row.outside_check.items}/${row.items} (${(row.outside_check.share * 100).toFixed(1)}%). ${reasons}.`, "scope"));
    detail.append(element(doc, "p", `${copy.costItem}: $${row.cost_per_item_usd.toFixed(6)}`));
    detail.append(element(doc, "p", `${copy.latency}: ${[row.latency_seconds.mean, row.latency_seconds.p50, row.latency_seconds.p95].map(time).join(" / ")} ${copy.seconds} (${row.latency_seconds.n} ${copy.latencySamples})`));
    detail.append(element(doc, "p", row.primary_truth.items ? `${copy.truth}: ${row.primary_truth.correct}/${row.primary_truth.items}` : copy.noTruth));
    detail.append(element(doc, "p", `${copy.review}: ${row.review_unscored}`));
    panel.append(heading, counts, detail, link(doc, copy.report, repoLink(source.report_path), "source-reference"));
    root.append(panel);
  }
}

export function renderFixcheck(doc, data, language) {
  const root = doc.getElementById("fixcheck");
  const copy = COPY[language];
  root.replaceChildren();
  if (!data.fixcheck) {
    root.append(element(doc, "p", copy.noFixcheck));
    return;
  }
  const list = element(doc, "div", undefined, "fix-list");
  if (data.fixcheck.report_excerpt) root.append(element(doc, "p", copy.reportWording, "note"));
  const text = (value) => typeof value === "string" ? value : value[language];
  for (const row of data.fixcheck.comparisons) {
    const article = element(doc, "article", undefined, "fix-row");
    article.append(element(doc, "h3", text(row.description)));
    const pair = element(doc, "div", undefined, "before-after");
    for (const key of ["before", "after"]) {
      const column = element(doc, "div");
      column.append(element(doc, "strong", copy[key]), element(doc, "p", text(row[key])));
      pair.append(column);
    }
    article.append(pair, link(doc, copy.fixEvidence, repoLink(row.evidence_path)));
    list.append(article);
  }
  root.append(list);
}

export function renderProvenance(doc, data, language) {
  const copy = COPY[language];
  const links = doc.getElementById("evidence-links");
  links.replaceChildren(
    link(doc, copy.records, "../evidence/real-world-2026-11-02/REPORT.md"),
    link(doc, copy.rawData, "data.json"),
    link(doc, copy.compiler, "../scripts/build_wild.py"),
  );
  const totals = element(doc, "p", `${copy.phaseCost}: News $${data.phase_costs_usd.news.toFixed(6)}; Threads $${data.phase_costs_usd.threads_including_media.toFixed(6)}. ${copy.mediaIncluded}`);
  links.append(totals);
  const list = doc.getElementById("hash-list");
  list.replaceChildren();
  for (const [path, hash] of Object.entries(data.evidence_sha256)) {
    const item = element(doc, "li");
    item.append(link(doc, path.replace("docs/", ""), repoLink(path)), element(doc, "span", hash, "hash"));
    list.append(item);
  }
  doc.getElementById("hashes").hidden = false;
}

export async function initialize(doc, win) {
  const languageKey = "market-claim-verifier-language";
  const themeKey = "market-claim-verifier-theme";
  const stored = (key) => { try { return win.localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { win.localStorage.setItem(key, value); } catch { /* private browsing */ } };
  let language = stored(languageKey) === "zh" ? "zh" : "en";
  let data = null;
  let failed = false;
  const provider = doc.getElementById("provider");
  const route = doc.getElementById("route");
  const status = doc.getElementById("load-status");
  const theme = stored(themeKey);
  if (["light", "dark"].includes(theme)) doc.documentElement.dataset.theme = theme;
  const render = () => {
    doc.documentElement.lang = language === "zh" ? "zh-Hant" : "en";
    doc.title = language === "zh" ? "真實貼文實測 · 財經主張查核器" : "In the wild · Market claim verifier";
    doc.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = COPY[language][node.dataset.i18n]; });
    doc.querySelectorAll("[data-i18n-aria]").forEach((node) => { node.setAttribute("aria-label", COPY[language][node.dataset.i18nAria]); });
    doc.querySelectorAll("[data-language]").forEach((node) => { node.setAttribute("aria-pressed", String(node.dataset.language === language)); });
    if (failed) status.textContent = COPY[language].unavailable;
    if (!data) return;
    renderCards(doc, data, language);
    renderCoverage(doc, data, language, provider.value, route.value);
    renderFixcheck(doc, data, language);
    renderProvenance(doc, data, language);
  };
  doc.querySelectorAll("[data-language]").forEach((button) => button.addEventListener("click", () => {
    language = button.dataset.language === "zh" ? "zh" : "en";
    save(languageKey, language);
    render();
  }));
  doc.getElementById("theme").addEventListener("click", () => {
    const current = doc.documentElement.dataset.theme || (win.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    doc.documentElement.dataset.theme = current === "dark" ? "light" : "dark";
    save(themeKey, doc.documentElement.dataset.theme);
  });
  provider.addEventListener("change", render);
  route.addEventListener("change", render);
  render();
  try {
    const response = await win.fetch(new URL("data.json", win.location.href), { credentials: "omit", cache: "no-cache" });
    if (!response.ok) throw new Error("Saved evidence unavailable");
    const parsed = await response.json();
    if (parsed.schema_version !== 1 || parsed.study_kind !== "development_probe") throw new Error("Unsupported page data");
    data = parsed;
    render();
    status.hidden = true;
    doc.getElementById("coverage-controls").hidden = false;
  } catch {
    failed = true;
    status.hidden = false;
    status.textContent = COPY[language].unavailable;
  }
}

if (typeof document !== "undefined") initialize(document, window);
