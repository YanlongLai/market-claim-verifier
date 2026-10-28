(() => {
  "use strict";

  document.documentElement.classList.add("has-js");

  // The page can still explain itself when GitHub Pages has not served data/site.json yet.
  // Keep this snapshot aligned with the checked-in data produced by build_site.py.
  const FALLBACK_DATA = {
    eval: { claim_count: 357, result_count: 2142, generated_at: "2026-10-28T06:27:01.922840Z" },
    systems: [
      { id: "agent@baseten", mode: "agent", provider: "Baseten", short: "Agent · Baseten", n: 357, correct: 323, accuracy: 0.9047619047619048, accuracy_ci: { lower: 0.8698604594051126, upper: 0.931045292790084 }, false_supported: 1, false_supported_denominator: 186, cost_mean: 0.020380065826330528, latency_mean_s: 11.678653828003732 },
      { id: "agent@fireworks", mode: "agent", provider: "Fireworks", short: "Agent · Fireworks", n: 357, correct: 323, accuracy: 0.9047619047619048, accuracy_ci: { lower: 0.8698604594051126, upper: 0.931045292790084 }, false_supported: 1, false_supported_denominator: 186, cost_mean: 0.020295625910364143, latency_mean_s: 66.98953745167681 },
      { id: "agent@meta", mode: "agent", provider: "Meta API", short: "Agent · Meta API", n: 357, correct: 297, accuracy: 0.8319327731092437, accuracy_ci: { lower: 0.7896564008489223, upper: 0.867141741954751 }, false_supported: 4, false_supported_denominator: 186, cost_mean: 0.026363472829131655, latency_mean_s: 39.28851581497394 },
      { id: "single_shot@meta", mode: "single-shot", provider: "Meta API", short: "Single-shot · Meta API", n: 357, correct: 158, accuracy: 0.4425770308123249, accuracy_ci: { lower: 0.39193672156972204, upper: 0.49443997102542314 }, false_supported: 9, false_supported_denominator: 186, cost_mean: 0.019421636974789908, latency_mean_s: 20.0266540428889 },
      { id: "single_shot@baseten", mode: "single-shot", provider: "Baseten", short: "Single-shot · Baseten", n: 357, correct: 74, accuracy: 0.20728291316526612, accuracy_ci: { lower: 0.1684587037125242, upper: 0.2523395585407768 }, false_supported: 1, false_supported_denominator: 186, cost_mean: 0.01161584761904761, latency_mean_s: 8.679807027268057 },
      { id: "single_shot@fireworks", mode: "single-shot", provider: "Fireworks", short: "Single-shot · Fireworks", n: 357, correct: 71, accuracy: 0.19887955182072828, accuracy_ci: { lower: 0.16077615372431311, upper: 0.24339430744535054 }, false_supported: 0, false_supported_denominator: 186, cost_mean: 0.01150906918767507, latency_mean_s: 50.89797223893096 }
    ],
    paired: {
      meta: { points: 38, mcnemar_exact_p: 3.571991065704909e-30, n: 352 },
      baseten: { points: 70, mcnemar_exact_p: 6.039282377631001e-69, n: 355 },
      fireworks: { points: 70, mcnemar_exact_p: 1.1349374541135807e-66, n: 355 }
    },
    families: [
      { id: "record_first", systems: { "agent@meta": { correct: 16, n: 31 }, "agent@baseten": { correct: 18, n: 31 }, "agent@fireworks": { correct: 18, n: 31 } } },
      { id: "yoy", systems: { "agent@meta": { correct: 29, n: 48 }, "agent@baseten": { correct: 45, n: 48 }, "agent@fireworks": { correct: 45, n: 48 } } },
      { id: "period_trap", systems: { "agent@meta": { correct: 23, n: 30 }, "agent@baseten": { correct: 24, n: 30 }, "agent@fireworks": { correct: 24, n: 30 } } }
    ],
    examples: [
      { id: "G0144", family: "unit_trap", claim: "For full-year 2025, the net income figure was $4.3B at AMD.", gold: "supported", single_shot_verdict: "insufficient_evidence", agent_verdict: "supported", evidence_summary: "Evidence: audited 10-K, confirmed in 1 filing, not restated", evidence: [{ ticker: "AMD", value: 4335000000, unit: "USD", form: "10-K", period: "FY2025", period_basis: "fiscal", tier: "L1", strength: "medium" }] },
      { id: "G0235", family: "ambiguous_period", claim: "NVIDIA's Q2 2024 revenue was $13.5 billion.", gold: "insufficient_evidence", single_shot_verdict: "supported", agent_verdict: "insufficient_evidence", period_ambiguous: true, evidence_summary: "Evidence: reviewed 10-Q, confirmed in 2 filings, not restated", evidence: [{ ticker: "NVDA", value: 30040000000, unit: "USD", form: "10-Q", period: "2024Q2", period_basis: "calendar", tier: "L2", strength: "medium" }, { ticker: "NVDA", value: 13507000000, unit: "USD", form: "10-Q", period: "FY2024Q2", period_basis: "fiscal", tier: "L2", strength: "medium" }] },
      { id: "G0193", family: "record_first", claim: "Johnson & Johnson's fiscal Q2 2025 revenue was its highest ever, at $25.6 billion.", gold: "contradicted", single_shot_verdict: "insufficient_evidence", agent_verdict: "contradicted", evidence_summary: "Evidence: reviewed 10-Q, confirmed in 2 filings, not restated", evidence: [{ ticker: "JNJ", value: 23743000000, unit: "USD", form: "10-Q", period: "FY2025Q2", period_basis: "fiscal", tier: "L2", strength: "medium" }] }
    ]
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  let currentData = FALLBACK_DATA;
  let currentFilter = "all";

  const formatPercent = (value) => `${(value * 100).toFixed(1)}%`;
  const formatCI = (ci) => `${formatPercent(ci.lower)}–${formatPercent(ci.upper)}`;
  const formatCost = (value) => `$${value.toFixed(3)}`;
  const formatLatency = (value) => `${Math.round(value)} s`;
  const formatVerdict = (value) => value === "insufficient_evidence" ? "insufficient evidence" : value;
  const formatNumber = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
    const number = Number(value);
    if (Math.abs(number) >= 1e9) return `$${(number / 1e9).toFixed(3).replace(/0+$/, "").replace(/\.$/, "")}B`;
    if (Math.abs(number) >= 1e6) return `$${(number / 1e6).toFixed(1).replace(/\.0$/, "")}M`;
    if (Math.abs(number) >= 1e3) return `$${(number / 1e3).toFixed(1).replace(/\.0$/, "")}K`;
    if (String(value).includes(".")) return `$${number.toFixed(2)}`;
    return `$${number}`;
  };

  function evidenceLabel(item) {
    const period = item.period_basis === "fiscal" ? `fiscal ${item.period}` : `calendar ${item.period}`;
    const tier = item.tier ? ` · ${item.tier}` : "";
    return `${period} · ${item.form || "evidence"}${tier}`;
  }

  function renderHero(data) {
    const baseten = data.systems.find((system) => system.id === "agent@baseten") || FALLBACK_DATA.systems[0];
    const single = data.systems.find((system) => system.id === "single_shot@meta") || FALLBACK_DATA.systems[3];
    $("#hero-agent-score").textContent = formatPercent(baseten.accuracy);
    $("#hero-single-score").textContent = formatPercent(single.accuracy);
    $("#hero-claim-count").textContent = `n = ${data.eval.claim_count}`;
    $("#hero-agent-ci").textContent = formatCI(baseten.accuracy_ci);
    const heroNote = $(".hero-metric-note");
    heroNote.setAttribute("title", `The strongest single-shot comparison is ${formatPercent(single.accuracy)} on the Meta API.`);
  }

  function verdictColor(verdict) {
    if (verdict === "supported") return "forest";
    if (verdict === "contradicted") return "coral";
    return "amber";
  }

  function renderExamples(data) {
    const container = $("#claim-examples");
    container.replaceChildren();
    data.examples.forEach((example) => {
      const article = document.createElement("article");
      article.className = "claim-example reveal";
      article.dataset.verdict = example.agent_verdict;

      const copy = document.createElement("div");
      copy.className = "claim-copy";
      const quote = document.createElement("blockquote");
      quote.textContent = example.claim;
      const id = document.createElement("span");
      id.className = "claim-id";
      id.textContent = `${example.id} · single-shot: ${formatVerdict(example.single_shot_verdict)}`;
      copy.append(quote, id);

      const evidence = document.createElement("div");
      evidence.className = "claim-evidence";
      const uniqueEvidence = example.evidence.filter((item, index, all) => index === all.findIndex((other) => other.value === item.value && other.period === item.period && other.period_basis === item.period_basis));
      uniqueEvidence.forEach((item) => {
        const actual = document.createElement("strong");
        actual.textContent = `${item.ticker} actual ${formatNumber(item.value)}`;
        const details = document.createElement("span");
        details.textContent = `${evidenceLabel(item)} · ${item.strength || "recorded"} strength`;
        evidence.append(actual, details);
      });
      if (example.period_ambiguous) {
        const note = document.createElement("span");
        note.textContent = "Two period readings disagree.";
        evidence.append(note);
      }

      const verdict = document.createElement("div");
      verdict.className = "claim-verdict";
      verdict.dataset.verdict = example.agent_verdict;
      const verdictWord = document.createElement("span");
      verdictWord.className = "verdict-word";
      verdictWord.textContent = formatVerdict(example.agent_verdict);
      const verdictNote = document.createElement("span");
      verdictNote.className = "verdict-note";
      verdictNote.textContent = example.evidence_summary || "Program-owned verdict";
      verdict.append(verdictWord, verdictNote);

      article.append(copy, evidence, verdict);
      container.append(article);
    });
  }

  function svgElement(name, attributes = {}, text = "") {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text) element.textContent = text;
    return element;
  }

  function cssColor(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function renderChart(data, filter = "all") {
    const svg = $("#accuracy-chart");
    const systems = data.systems.filter((system) => filter === "all" || system.mode === filter);
    const colors = {
      ink: cssColor("--deep-ink"),
      muted: cssColor("--deep-muted"),
      panel: cssColor("--deep-panel"),
      forest: cssColor("--forest"),
      slate: cssColor("--slate"),
      amber: cssColor("--amber")
    };
    svg.replaceChildren();
    svg.append(
      svgElement("title", { id: "chart-title" }, "Accuracy with 95 percent Wilson intervals"),
      svgElement("desc", { id: "chart-desc" }, "Six evaluation systems shown on a zero to one hundred percent scale with their Wilson confidence intervals.")
    );

    const left = 266;
    const top = 52;
    const plotWidth = 430;
    const rowHeight = 56;
    const axisY = top + systems.length * rowHeight + 10;
    [0, 50, 100].forEach((tick) => {
      const x = left + plotWidth * (tick / 100);
      svg.append(svgElement("line", { x1: x, y1: top - 25, x2: x, y2: axisY - 15, stroke: colors.panel, "stroke-width": 3 }));
      svg.append(svgElement("text", { x, y: axisY + 10, fill: colors.muted, "font-size": 12, "text-anchor": tick === 0 ? "start" : tick === 100 ? "end" : "middle" }, `${tick}%`));
    });

    systems.forEach((system, index) => {
      const y = top + index * rowHeight;
      const barY = y - 10;
      const accuracyX = left + plotWidth * system.accuracy;
      const lowX = left + plotWidth * system.accuracy_ci.lower;
      const highX = left + plotWidth * system.accuracy_ci.upper;
      const fill = system.mode === "agent" ? colors.forest : colors.slate;
      svg.append(svgElement("text", { x: 8, y: y - 3, fill: colors.ink, "font-size": 14, "font-weight": 700 }, system.short));
      svg.append(svgElement("text", { x: 8, y: y + 15, fill: colors.muted, "font-size": 11 }, `${system.correct}/${system.n} correct`));
      svg.append(svgElement("rect", { x: left, y: barY, width: plotWidth, height: 20, fill: colors.panel }));
      svg.append(svgElement("rect", { x: left, y: barY, width: plotWidth * system.accuracy, height: 20, fill }));
      svg.append(svgElement("line", { x1: lowX, y1: y, x2: highX, y2: y, stroke: colors.ink, "stroke-width": 4 }));
      svg.append(svgElement("line", { x1: lowX, y1: y - 7, x2: lowX, y2: y + 7, stroke: colors.ink, "stroke-width": 4 }));
      svg.append(svgElement("line", { x1: highX, y1: y - 7, x2: highX, y2: y + 7, stroke: colors.ink, "stroke-width": 4 }));
      svg.append(svgElement("circle", { cx: accuracyX, cy: y, r: 6, fill: colors.ink }));
      svg.append(svgElement("text", { x: 735, y: y + 5, fill: colors.ink, "font-size": 14, "font-weight": 700, "text-anchor": "end" }, formatPercent(system.accuracy)));
    });
    svg.setAttribute("viewBox", `0 0 760 ${axisY + 34}`);
    $("#chart-status").textContent = `Showing ${filter === "all" ? "all six systems" : filter === "agent" ? "agent paths" : "single-shot paths"} · n = ${data.eval.claim_count} claims`;
  }

  function renderTable(data) {
    const body = $("#results-table-body");
    body.replaceChildren();
    data.systems.forEach((system) => {
      const row = document.createElement("tr");
      const values = [
        system.short,
        formatPercent(system.accuracy),
        formatCI(system.accuracy_ci),
        formatCost(system.cost_mean),
        formatLatency(system.latency_mean_s),
        `${system.false_supported} / ${system.false_supported_denominator}`
      ];
      values.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });
      body.append(row);
    });
  }

  function renderPaired(data) {
    ["meta", "baseten", "fireworks"].forEach((provider) => {
      const comparison = data.paired[provider];
      $(`#delta-${provider}`).textContent = `+${comparison.points} pts`;
    });
    const allSmall = ["meta", "baseten", "fireworks"].every((provider) => data.paired[provider].mcnemar_exact_p < 0.0001);
    $("#mcnemar-note").textContent = allSmall ? "p < 0.0001" : "exact p values in the snapshot";
  }

  function renderWeakSpots(data) {
    const labels = {
      record_first: (family) => `Record / first-time claims: ${family.systems["agent@meta"].correct}–${family.systems["agent@baseten"].correct} of ${family.systems["agent@meta"].n} right.`,
      yoy: (family) => `Year-over-year claims: Meta API ${family.systems["agent@meta"].correct} of ${family.systems["agent@meta"].n} right; Baseten and Fireworks ${family.systems["agent@baseten"].correct} of ${family.systems["agent@baseten"].n}.`,
      period_trap: (family) => `Fiscal/calendar traps: ${family.systems["agent@meta"].correct}–${family.systems["agent@baseten"].correct} of ${family.systems["agent@meta"].n} right.`
    };
    const list = $("#weak-spot-list");
    list.replaceChildren();
    data.families.forEach((family) => {
      const item = document.createElement("li");
      item.textContent = labels[family.id] ? labels[family.id](family) : family.id;
      list.append(item);
    });
  }

  function observeReveals() {
    const revealItems = $$(".reveal:not(.is-visible)");
    if (!("IntersectionObserver" in window)) {
      revealItems.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries, instance) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          instance.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revealItems.forEach((item) => observer.observe(item));
  }

  function setupFilters() {
    $$(".chart-filter").forEach((button) => {
      button.addEventListener("click", () => {
        currentFilter = button.dataset.filter;
        $$(".chart-filter").forEach((other) => other.classList.toggle("is-selected", other === button));
        renderChart(currentData, currentFilter);
      });
    });
  }

  async function loadData() {
    let fromFallback = false;
    try {
      const response = await fetch("data/site.json", { cache: "no-store" });
      if (!response.ok) throw new Error("site data unavailable");
      currentData = await response.json();
    } catch (_error) {
      fromFallback = true;
      currentData = FALLBACK_DATA;
    }

    renderHero(currentData);
    renderExamples(currentData);
    renderChart(currentData, currentFilter);
    renderTable(currentData);
    renderPaired(currentData);
    renderWeakSpots(currentData);
    setupFilters();
    observeReveals();
    if (fromFallback) $("#chart-status").textContent += " · showing the checked fallback snapshot";
  }

  loadData();
})();
