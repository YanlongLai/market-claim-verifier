// Offline DOM adapter. Exercises the shipped JS and HTML; no browser or network.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
let input = "";
for await (const chunk of process.stdin) input += chunk;
const config = JSON.parse(input);
const code = readFileSync(new URL("../docs/wild/script.js", import.meta.url), "utf8");
const page = await import(`data:text/javascript;base64,${Buffer.from(code).toString("base64")}`);

class Node {
  constructor(tag, attrs = {}, children = []) {
    this.tagName = tag;
    this.attrs = { ...attrs };
    this.children = children;
    this.events = {};
    this._text = "";
    this.hidden = Object.hasOwn(attrs, "hidden");
    this.value = attrs.value || "";
    this.dataset = {};
    for (const [key, value] of Object.entries(attrs)) {
      if (key.startsWith("data-")) this.dataset[key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = value;
    }
    if (tag === "select") this.value = children.find(c => c.tagName === "option")?.value || "";
  }
  get id() { return this.attrs.id; }
  set id(value) { this.attrs.id = value; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(""); }
  set textContent(value) { this._text = String(value); this.children = []; }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this._text = ""; this.children = nodes; }
  addEventListener(name, handler) { this.events[name] = handler; }
  fire(name) { assert.ok(this.events[name], `Missing ${name} handler on ${this.id || this.tagName}`); this.events[name](); }
}

function restore(raw) {
  if (typeof raw === "string") { const text = new Node("#text"); text.textContent = raw; return text; }
  return new Node(raw.tag, raw.attrs, raw.children.map(restore));
}
const root = restore(config.dom);
const walk = (node) => [node, ...node.children.flatMap(walk)];
const doc = {
  documentElement: walk(root).find(n => n.tagName === "html"),
  createElement: tag => new Node(tag),
  getElementById: id => walk(root).find(n => n.id === id),
  querySelectorAll: selector => {
    const attr = selector.slice(1, -1);
    return walk(root).filter(n => Object.hasOwn(n.attrs, attr));
  },
};
const saved = { "market-claim-verifier-language": config.language || "en" };
const requests = [];
const win = {
  location: { href: config.url || "https://example.test/project/wild/" },
  localStorage: {
    getItem(key) { if (config.storageBlocked) throw Error("blocked"); return saved[key] || null; },
    setItem(key, value) { if (config.storageBlocked) throw Error("blocked"); saved[key] = value; },
  },
  matchMedia: () => ({ matches: config.dark || false }),
  fetch: async (url, options) => {
    requests.push({ url: String(url), options });
    assert.equal(new URL(url).origin, new URL(win.location.href).origin, "External network request");
    return { ok: !config.unavailable, json: async () => config.data };
  },
};
assert.deepEqual(Object.keys(page.COPY.en).sort(), Object.keys(page.COPY.zh).sort());
for (const node of doc.querySelectorAll("[data-i18n]")) assert.ok(page.COPY.en[node.dataset.i18n], `Missing translation: ${node.dataset.i18n}`);
for (const node of doc.querySelectorAll("[data-i18n-aria]")) assert.ok(page.COPY.en[node.dataset.i18nAria]);
await page.initialize(doc, win);
assert.equal(requests.length, 1);
assert.equal(requests[0].url, new URL("data.json", win.location.href).href);
assert.equal(requests[0].options.credentials, "omit");
const switchLanguage = language => doc.querySelectorAll("[data-language]").find(n => n.dataset.language === language).fire("click");

if (config.unavailable) {
  assert.equal(doc.getElementById("load-status").hidden, false);
  assert.ok(doc.getElementById("load-status").textContent.includes("unavailable"));
  assert.equal(doc.getElementById("cards").children.length, 0);
  assert.equal(doc.getElementById("coverage-controls").hidden, true);
  switchLanguage("zh");
  assert.ok(doc.getElementById("load-status").textContent.includes("無法顯示"));
} else {
  assert.equal(doc.getElementById("load-status").hidden, true);
  assert.equal(doc.getElementById("coverage-controls").hidden, false);
  assert.equal(doc.getElementById("cards").children.length, config.data.cards.length);
  const languages = ["en", "zh", "en"];
  for (const language of languages) {
    switchLanguage(language);
    assert.equal(doc.documentElement.lang, language === "zh" ? "zh-Hant" : "en");
    for (const node of doc.querySelectorAll("[data-i18n]")) assert.equal(node.textContent, page.COPY[language][node.dataset.i18n]);
    for (const provider of ["baseten", "fireworks", "meta"]) {
      for (const route of ["agent", "post"]) {
        doc.getElementById("provider").value = provider;
        doc.getElementById("provider").fire("change");
        doc.getElementById("route").value = route;
        doc.getElementById("route").fire("change");
        const panels = doc.getElementById("coverage-results").children;
        assert.equal(panels.length, config.data.sources.length);
        for (let index = 0; index < panels.length; index++) {
          const expected = config.data.systems[`${provider}/${route}`][config.data.sources[index].id].outcomes;
          const values = walk(panels[index]).filter(n => n.tagName === "dd").map(n => Number(n.textContent));
          assert.deepEqual(values, [expected.supported, expected.contradicted, expected.insufficient_evidence, expected.skipped, expected.failed + expected.partial_failure, expected.budget_stopped]);
        }
      }
    }
    const cards = doc.getElementById("cards").textContent;
    assert.ok(cards.includes("@fixture"));
    assert.ok(cards.includes(language === "zh" ? "5,000 億美元" : "$500 billion"));
    assert.ok(cards.includes(language === "zh" ? "自動翻譯" : "auto-translation"));
    assert.ok(!cards.includes(page.COPY[language].likelyTranslation));
    assert.ok(!cards.includes("@unresolved"));
  }
  // Evidence text is always inserted as text, including an adversarial handle.
  const unsafe = structuredClone(config.data);
  unsafe.cards[0].handle = "<img src=x onerror=alert(1)>";
  page.renderCards(doc, unsafe, "en");
  assert.ok(doc.getElementById("cards").textContent.includes("<img"));
  assert.ok(!walk(doc.getElementById("cards")).some(n => n.tagName === "img"));
  assert.equal(page.metricLabel("FY2026 Q4 iPhone revenue", "zh"), "2026 會計年度第 4 季 iPhone 營收");
  assert.equal(page.formatValue("378", "percent", "zh"), "378%");
  assert.throws(() => page.repoLink("docs/../secrets"));
  assert.throws(() => page.repoLink("https://external.test/"));
  if (config.data.fixcheck) {
    assert.ok(doc.getElementById("fixcheck").textContent.includes("Before"));
    assert.ok(doc.getElementById("fixcheck").textContent.includes("After"));
  }
}
doc.getElementById("theme").fire("click");
assert.equal(doc.documentElement.dataset.theme, config.dark ? "light" : "dark");
doc.getElementById("theme").fire("click");
assert.equal(doc.documentElement.dataset.theme, config.dark ? "dark" : "light");
assert.equal(requests.length, 1, "UI interactions must not fetch additional data");
process.stdout.write("PASS wild page: i18n, filters, theme, relative URLs, missing data and no external requests\n");
