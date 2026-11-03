import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { onRequest, onBudget } from "../../workers/pages/check.mjs";

const demo = JSON.parse(readFileSync(new URL("../../docs/site/data/live-demo.json", import.meta.url)));
const postDemo = JSON.parse(readFileSync(new URL("../../docs/site/data/live-demo-post.json", import.meta.url)));
const request = (body = { text: demo.input }, more = {}, host = "localhost") => new Request(`http://${host}/api/check`, {
  method: "POST", headers: { "Content-Type": "application/json", ...more }, body: JSON.stringify(body)
});
const assets = { fetch: async req => Response.json(new URL(req.url).pathname === "/data/live-demo-post.json" ? postDemo : demo) };
const origin = { LIVE_ORIGIN_HOST: "live-origin.example.com", LIVE_ACCESS_CLIENT_ID: "access-id-marker",
  LIVE_ACCESS_CLIENT_SECRET: "access-secret-marker", LIVE_ORIGIN_TOKEN: "origin-token-marker" };
const originHeaders = { "cf-access-client-id": origin.LIVE_ACCESS_CLIENT_ID,
  "cf-access-client-secret": origin.LIVE_ACCESS_CLIENT_SECRET, "x-live-origin-token": origin.LIVE_ORIGIN_TOKEN };
function envWithFetch(t, fetch) { t.mock.method(globalThis, "fetch", fetch); return { ...origin }; }

test("offline Pages mock is labelled, accepts both recorded inputs, and never fetches origin", async t => {
  const env = { ...envWithFetch(t, () => assert.fail("origin")), LIVE_CHECK_MOCK: "1", ASSETS: assets };
  const response = await onRequest({ request: request(), env });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
  assert.equal((await response.json()).mode, "mock");
  const postResponse = await onRequest({ request: request({ text: postDemo.input }), env });
  assert.equal(postResponse.status, 200);
  const postResult = await postResponse.json();
  assert.deepEqual(postResult, { ...postDemo, mode: "mock" });
  assert.equal(postResult.corrections.edits.length, 1);
  const trimmed = await onRequest({ request: request({ text: postDemo.input.trim() }), env });
  assert.equal(trimmed.status, 200);
  assert.equal((await onRequest({ request: request({ text: "Other claim" }), env })).status, 422);
  const budget = await onBudget({ request: new Request("http://localhost/api/budget"), env });
  assert.equal((await budget.json()).mode, "mock");
  assert.equal(budget.headers.get("Cache-Control"), "no-store");
  assert.equal((await onBudget({ request: new Request("https://site.example/api/budget"), env: { LIVE_CHECK_MOCK: "1" } })).status, 503);
});

test("production cannot enable the local mock or supply its own forwarded IP; origin gets Access credentials", async t => {
  let calls = 0;
  const env = { ...envWithFetch(t, async req => {
    calls++;
    assert.equal(req.url, "https://live-origin.example.com/api/check");
    assert.equal(req.redirect, "manual");
    assert.deepEqual(Object.fromEntries(req.headers), { ...originHeaders,
      "content-type": "application/json", "x-live-client-ip": "192.0.2.1" });
    assert.deepEqual(await req.json(), { text: demo.input, password: "offline-password" });
    return Response.json({ verdict: "supported", mode: "live", secret: origin.LIVE_ORIGIN_TOKEN },
      { headers: { "Set-Cookie": "private", "X-Private": origin.LIVE_ACCESS_CLIENT_SECRET } });
  }), LIVE_CHECK_MOCK: "1", ASSETS: assets };
  const response = await onRequest({ request: request({ text: demo.input, password: "offline-password", secret: "drop" }, {
    "CF-Connecting-IP": "192.0.2.1", "X-Live-Client-IP": "spoofed", Cookie: "private", Authorization: "private",
    "CF-Access-Client-Secret": "spoofed", "X-Live-Origin-Token": "spoofed"
  }, "hackathon.dappgo.com"), env });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { verdict: "supported", mode: "live" });
  assert.equal(response.headers.get("Set-Cookie"), null);
  assert.equal(response.headers.get("X-Private"), null);
  assert.equal(calls, 1);
});

test("Pages forwards deterministic corrections in its public result allowlist", async t => {
  const corrections = { label: { en: "Corrected draft — only listed assertions checked", zh: "修正版草稿——僅核對列出的主張" },
    original_text: "Apple: $416.2B", span_unit: "unicode_codepoints",
    edits: [{ start: 7, end: 14, original: "$416.2B", replacement: "$102.5B", evidence_ids: ["E1"],
      citations: [{ url: "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/" }] }],
    not_corrected: [] };
  const env = envWithFetch(t, async () => Response.json({ verdict: "contradicted", mode: "live", corrections,
    private_internal: "drop", password: "drop", secret: "drop" }));
  const response = await onRequest({ request: request({ text: "Apple: $416.2B" }, {
    "CF-Connecting-IP": "192.0.2.1"
  }, "hackathon.dappgo.com"), env });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { verdict: "contradicted", mode: "live", corrections });
});

test("password goes only in the private request body, with no browser headers or URL forwarding", async t => {
  const env = envWithFetch(t, async req => {
    assert.equal(req.url, "https://live-origin.example.com/api/check");
    for (const name of ["Authorization", "Cookie", "X-Live-Password", "Origin", "Sec-Fetch-Site"]) {
      assert.equal(req.headers.get(name), null);
    }
    const data = await req.json();
    assert.deepEqual(Object.keys(data), ["text", "password"]);
    assert.equal(data.text, demo.input);
    assert.equal(typeof data.password, "string");
    return Response.json({ error: "unauthorized" }, { status: 401 });
  });
  for (const password of [undefined, "", "wrong-test-password"]) {
    const response = await onRequest({ request: request({ text: demo.input, password }, {
      "CF-Connecting-IP": "192.0.2.1", "X-Live-Password": "spoofed", Cookie: "private", Authorization: "private"
    }, "hackathon.dappgo.com"), env });
    assert.equal(response.status, 401);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    assert.deepEqual(await response.json(), { error: "unauthorized" });
  }
});

test("origin, length, byte size, JSON and content-type checks happen before forwarding", async t => {
  const env = envWithFetch(t, () => assert.fail("forwarded invalid request"));
  for (const [req, status] of [
    [request({ text: "x".repeat(601) }), 400], [request({ text: "   " }), 400],
    [request({ text: "ok", large: "a".repeat(5000) }), 400], [request(null), 400],
    [request({}, { "Content-Type": "text/plain" }), 400],
    [request({}, { Origin: "https://evil.example" }), 403],
    [request({}, { "Sec-Fetch-Site": "cross-site" }), 403],
    [new Request("http://localhost/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{" }), 400],
    [new Request("http://localhost/api/check"), 405],
  ]) assert.equal((await onRequest({ request: req, env })).status, status);
  const body = new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(4097)); controller.close(); } });
  const chunked = new Request("http://localhost/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body, duplex: "half" });
  assert.equal((await onRequest({ request: chunked, env })).status, 400);
});

test("missing configuration or trusted IP fails closed before fetch", async t => {
  envWithFetch(t, () => assert.fail("fetch without configuration/IP"));
  assert.equal((await onRequest({ request: request(), env: origin })).status, 503);
  const configs = [{}];
  for (const key of Object.keys(origin)) configs.push({ ...origin, [key]: "" });
  for (const host of ["https://live.example.com", "user@live.example.com", "live.example.com/path", "live.example.com:443", "live.example.com?x=1"]) {
    configs.push({ ...origin, LIVE_ORIGIN_HOST: host });
  }
  for (const env of configs) {
    const response = await onRequest({ request: request(undefined, { "CF-Connecting-IP": "192.0.2.1" }), env });
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), { error: "unavailable", demo: "data/live-demo.json" });
  }
});

const budget = { day: "2026-11-02", daily_limit_usd: 3, daily_spent_usd: .59,
  daily_remaining_usd: 2.41, resets_at: "2026-11-03T00:00:00Z", status: "ready" };

test("public budget sends only origin credentials, excludes private data, and caches for at most five seconds", async t => {
  let calls = 0;
  const env = envWithFetch(t, async req => {
    calls++;
    assert.equal(req.url, "https://live-origin.example.com/api/budget");
    assert.equal(req.method, "GET");
    assert.equal(req.redirect, "manual");
    assert.deepEqual(Object.fromEntries(req.headers), originHeaders);
    return Response.json({ ...budget, holds: "private", salt: "private", lifetime_nanos: 12345,
      secret: origin.LIVE_ACCESS_CLIENT_SECRET });
  });
  for (const fresh of [false, true]) {
    const response = await onBudget({ request: new Request("https://site.example/api/budget", {
      headers: { "Authorization": "must-not-forward", "Cookie": "must-not-forward", "CF-Connecting-IP": "private",
        ...(fresh ? { "Cache-Control": "no-cache" } : {}) }
    }), env });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("Cache-Control"), fresh ? "no-store" : "public, max-age=0, s-maxage=5, must-revalidate");
    assert.deepEqual(await response.json(), budget);
  }
  assert.equal(calls, 2);
});

test("origin/network/Access failures return the uncached 503 demo fallback without secrets", async t => {
  const handlers = [() => { throw Error(origin.LIVE_ACCESS_CLIENT_SECRET); },
    () => new Response("<html>Access login</html>", { status: 403 }),
    () => Response.json({ error: "origin_rejected" }, { status: 401 }),
    () => Response.json({ error: "origin_rejected" }, { status: 403 }),
    () => Response.json({ error: "unauthorized" }, { status: 403 }),
    () => Response.json({ error: origin.LIVE_ORIGIN_TOKEN }, { status: 503 }),
    () => Response.json({ error: "gateway error", secret: origin.LIVE_ACCESS_CLIENT_ID }, { status: 502 }),
    () => Response.json({ ...budget, daily_remaining_usd: -1 })];
  let handler;
  const env = envWithFetch(t, req => handler(req));
  for (handler of handlers) {
    for (const budgetRequest of [false, true]) {
      const response = await (budgetRequest ? onBudget({ request: new Request("https://site.example/api/budget"), env }) :
        onRequest({ request: request(undefined, { "CF-Connecting-IP": "192.0.2.1" }), env }));
      assert.equal(response.status, 503);
      assert.equal(response.headers.get("Cache-Control"), "no-store");
      const { origin_status, ...body } = await response.json();
      assert.deepEqual(body, { error: "unavailable", demo: "data/live-demo.json" });
      // Budget failures carry only a diagnostic status code/kind, never origin bodies or secrets.
      if (budgetRequest) assert.ok(origin_status === undefined || Number.isInteger(origin_status) || /^(config|network|\d{3}-html)$/.test(origin_status));
      else assert.equal(origin_status, undefined);
    }
  }
  assert.equal((await onBudget({ request: new Request("https://site.example/api/budget", { method: "POST" }), env })).status, 405);
});

test("25 second abort covers fetch and body consumption for check and budget", async t => {
  let timers = 0, cleared = 0, bodyWait = false;
  t.mock.method(globalThis, "setTimeout", (callback, ms) => {
    assert.equal(ms, 25000); timers++; queueMicrotask(callback); return timers;
  });
  t.mock.method(globalThis, "clearTimeout", () => cleared++);
  const env = envWithFetch(t, req => {
    const wait = () => new Promise((_, reject) => {
      if (req.signal.aborted) reject(Error("aborted"));
      else req.signal.addEventListener("abort", () => reject(Error("aborted")), { once: true });
    });
    return bodyWait ? Promise.resolve({ json: wait }) : wait();
  });
  for (bodyWait of [false, true]) {
    assert.equal((await onRequest({ request: request(undefined, { "CF-Connecting-IP": "192.0.2.1" }), env })).status, 503);
    assert.equal((await onBudget({ request: new Request("https://site.example/api/budget"), env })).status, 503);
  }
  assert.equal(timers, 4); assert.equal(cleared, 4);
});

test("known backend errors retain partial traces and existing status/error codes", async t => {
  const partial = { mode: "live", error: "credit_exhausted", demo: "data/live-demo.json", cost_usd: .03,
    cost_is_bound: true, events: [], evidence: [] };
  const env = envWithFetch(t, () => Response.json({ ...partial, secret: origin.LIVE_ORIGIN_TOKEN }, { status: 503 }));
  const response = await onRequest({ request: request(undefined, { "CF-Connecting-IP": "192.0.2.1" }), env });
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), partial);
});

test("dashboard-pasted values with trailing newlines still reach the origin as clean headers", async t => {
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.url, "https://live-origin.example.com/api/budget");
    assert.equal(req.headers.get("x-live-origin-token"), origin.LIVE_ORIGIN_TOKEN);
    assert.equal(req.headers.get("cf-access-client-secret"), origin.LIVE_ACCESS_CLIENT_SECRET);
    return Response.json({ day: "2026-11-03", daily_limit_usd: 3, daily_spent_usd: 0, daily_remaining_usd: 3,
      resets_at: "2026-11-04T00:00:00Z", status: "ready" });
  });
  const env = Object.fromEntries(Object.entries(origin).map(([k, v]) => [k, `${v}\n`]));
  const response = await onBudget({ request: new Request("https://hackathon.dappgo.com/api/budget"), env });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).daily_remaining_usd, 3);
});

test("origin fetch uses a redirect mode the Workers runtime accepts", () => {
  const source = readFileSync(new URL("../../workers/pages/check.mjs", import.meta.url), "utf8");
  assert.ok(!/redirect:\s*"error"/.test(source), "Workers fetch throws on redirect: \"error\"");
});
