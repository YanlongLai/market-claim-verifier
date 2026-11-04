import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { onRequest, onExample, onCompare, onHistory, onBudget } from "../../workers/pages/check.mjs";

const env = { LIVE_ORIGIN_HOST: "live-origin.example.com", LIVE_ACCESS_CLIENT_ID: "access-id",
  LIVE_ACCESS_CLIENT_SECRET: "access-secret", LIVE_ORIGIN_TOKEN: "origin-token" };
const models = { baseten: "meta-models/muse-spark-open-1026", fireworks: "accounts/fireworks/models/muse-spark-open", meta: "muse-spark-1.3" };
const text = '<script>alert("hostile")</script> Apple FY2025 revenue $416.2B';
const post = (path, body, headers = {}) => new Request(`https://site.example/api/${path}`, { method: "POST",
  headers: { "Content-Type": "application/json", "CF-Connecting-IP": "192.0.2.1", ...headers }, body: JSON.stringify(body) });
const receipt = (provider = "baseten") => ({ provider, model: models[provider], latency_ms: 300, cost_usd: .01, preprocessing: null });
const envelope = (provider = "baseten", extra = {}) => ({ mode: "live", provider, model: models[provider], verdict: "supported",
  input: { kind: "text", text_read: text }, receipt: receipt(provider), ...extra });
const row = (extra = {}) => ({ id: "a".repeat(32), at: "2026-11-04T01:00:00.000Z", ip_masked: "192.0.*.*#1234abcd",
  device: "Windows / desktop", browser: "Edge", kind: "text", example_id: null, story: null, input_text: text,
  provider: "baseten", model: models.baseten, verdict: "supported", corrections_count: 0, latency_ms: 300,
  cost_usd: .01, preprocessing_cost_usd: 0, ...extra });

test("provider selection reaches only the allowlisted origin JSON and receipt fields", async t => {
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.url, "https://live-origin.example.com/api/check");
    assert.deepEqual(await req.json(), { text, password: "test-password", provider: "fireworks" });
    assert.equal(req.headers.get("X-Live-Client-IP"), "192.0.2.1");
    assert.equal(req.headers.get("User-Agent"), "test-browser/1");
    assert.equal(req.headers.get("Cookie"), null);
    return Response.json(envelope("fireworks", { raw_ip: "drop", user_agent: "drop",
      receipt: { ...receipt("fireworks"), api_key: "drop" }, input: { kind: "text", text_read: text, raw_ua: "drop" } }));
  });
  const response = await onRequest({ request: post("check", { text, password: "test-password", provider: "fireworks" },
    { "X-Live-Client-IP": "spoofed", "User-Agent": "test-browser/1", Cookie: "private" }), env });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), envelope("fireworks"));
});

test("all POST endpoints reject extra keys, unknown providers and bodies over 1 KiB", async t => {
  t.mock.method(globalThis, "fetch", () => assert.fail("hostile request forwarded"));
  const cases = [
    [onRequest, "check", { text, password: "x", provider: "__proto__" }, 400],
    [onRequest, "check", { text, provider: null }, 400],
    [onRequest, "check", { text, provider: "Meta" }, 400],
    [onRequest, "check", { text, model: models.meta }, 400],
    [onRequest, "check", { text: "中".repeat(500) }, 400],
    [onExample, "check-example", { example_id: "a-text", file: "/etc/passwd" }, 400],
    [onCompare, "compare", { text, providers: ["meta"] }, 400],
    [onCompare, "compare", { text, providers: ["meta", "meta"] }, 400],
    [onCompare, "compare", { text, providers: ["meta", "unknown"] }, 400],
    [onCompare, "compare", { text, example_id: "a-text", providers: ["meta", "baseten"] }, 400],
    [onCompare, "compare", { text, providers: ["meta", "baseten"], provider: "meta" }, 400],
  ];
  for (const [handler, path, body, status] of cases) assert.equal((await handler({ request: post(path, body), env })).status, status);
  for (const [handler, path, body] of [[onRequest, "check", { text }], [onExample, "check-example", { example_id: "a-text" }],
    [onCompare, "compare", { text, providers: ["meta", "baseten"] }]]) {
    assert.equal((await handler({ request: post(path, body, { Origin: "https://evil.example" }), env })).status, 403);
    assert.equal((await handler({ request: post(path, body, { "Sec-Fetch-Site": "cross-site" }), env })).status, 403);
    assert.equal((await handler({ request: post(path, body, { "Content-Type": "application/json-evil" }), env })).status, 400);
    const bodyStream = new ReadableStream({ start(c) { c.enqueue(new Uint8Array(1025)); c.close(); } });
    const request = new Request(`https://site.example/api/${path}`, { method: "POST", body: bodyStream, duplex: "half",
      headers: { "Content-Type": "application/json", "Content-Length": "1" } });
    assert.equal((await handler({ request, env })).status, 400);
  }
});

test("compare fetches members sequentially and keeps public envelopes through a budget stop", async t => {
  const stopped = envelope("fireworks", { verdict: undefined, error: "budget_exhausted", receipt: { ...receipt("fireworks"), cost_usd: 0 } });
  const seen = [];
  let active = 0;
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(++active, 1, "members must never overlap");
    assert.equal(req.url, "https://live-origin.example.com/api/check");
    const body = await req.json();
    seen.push(body.provider);
    assert.deepEqual(body, { text, password: "x", provider: ["meta", "fireworks", "baseten"][seen.length - 1] });
    assert.equal(req.headers.get("X-Live-Client-IP"), "192.0.2.1");
    const result = body.provider === "fireworks" ? stopped : { ...envelope(body.provider), password: "drop", raw_ip: "drop" };
    const response = Response.json(result, { status: body.provider === "fireworks" ? 429 : 200 });
    const read = response.json.bind(response);
    response.json = async () => { const data = await read(); active--; return data; };
    return response;
  });
  const response = await onCompare({ request: post("compare", { text, password: "x", providers: ["meta", "fireworks", "baseten"] }), env });
  assert.equal(response.status, 200);
  const expected = JSON.parse(JSON.stringify({ runs: [envelope("meta"), stopped, envelope("baseten")] }));
  assert.deepEqual(await response.json(), expected);
  assert.deepEqual(seen, ["meta", "fireworks", "baseten"]);
});

test("compare gives each example its own sub-100 s fetch and shares a 290 s deadline", async t => {
  let now = 0;
  const durations = [], cleared = [], seen = [];
  t.mock.method(Date, "now", () => now);
  t.mock.method(globalThis, "setTimeout", (fn, ms) => { durations.push(ms); return durations.length; });
  t.mock.method(globalThis, "clearTimeout", id => cleared.push(id));
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.url, "https://live-origin.example.com/api/check-example");
    const body = await req.json();
    assert.deepEqual(body, { example_id: "a-text", password: "x", provider: ["meta", "baseten", "fireworks"][seen.length] });
    seen.push(body.provider);
    now += durations.at(-1);
    return Response.json(envelope(body.provider, { input: { kind: "text", example_id: "a-text", story: "a", text_read: text } }));
  });
  const response = await onCompare({ request: post("compare", { example_id: "a-text", password: "x", providers: ["meta", "baseten", "fireworks"] }), env });
  assert.equal(response.status, 200);
  assert.deepEqual((await response.json()).runs.map(run => run.receipt.provider), seen);
  assert.deepEqual(durations, [97000, 97000, 96000]);
  assert.deepEqual(cleared, [1, 2, 3]);
  assert.equal(now, 290000);
});

test("compare continues after provider timeouts and stops after a rate limit", async t => {
  const seen = [];
  t.mock.method(globalThis, "fetch", async req => {
    const { provider } = await req.json();
    seen.push(provider);
    return Response.json(envelope(provider, { verdict: undefined, error: provider === "meta" ? "timeout" : "rate_limited" }),
      { status: provider === "meta" ? 504 : 429 });
  });
  const response = await onCompare({ request: post("compare", { text, providers: ["meta", "baseten", "fireworks"] }), env });
  assert.equal(response.status, 200);
  assert.deepEqual((await response.json()).runs.map(run => run.error), ["timeout", "rate_limited"]);
  assert.deepEqual(seen, ["meta", "baseten"]);
});

test("compare returns authentication rejection without starting another member", async t => {
  let calls = 0;
  t.mock.method(globalThis, "fetch", () => { calls++; return Response.json({ error: "unauthorized" }, { status: 401 }); });
  const response = await onCompare({ request: post("compare", { text, password: "wrong", providers: ["meta", "baseten"] }), env });
  assert.equal(response.status, 401);
  assert.deepEqual(await response.json(), { error: "unauthorized" });
  assert.equal(calls, 1);
});

test("new story example IDs and preprocessing receipts survive the proxy allowlist", async t => {
  const prep = { model: "muse-voice-transcribe-1.0", latency_ms: 200, cost_usd: .001 };
  const input = { kind: "audio", example_id: "c-audio", story: "c", text_read: text };
  const expected = envelope("meta", { input, receipt: { ...receipt("meta"), preprocessing: prep }, cost_usd: .011, latency_ms: 500 });
  t.mock.method(globalThis, "fetch", async req => {
    assert.deepEqual(await req.json(), { example_id: "c-audio", password: "x", provider: "meta" });
    return Response.json({ ...expected, receipt: { ...expected.receipt, preprocessing: { ...prep, raw_response: "drop" } },
      input: { ...input, private_path: "drop" } });
  });
  const response = await onExample({ request: post("check-example", { example_id: "c-audio", password: "x", provider: "meta" }), env });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), expected);
});

test("invalid provider, receipt math, result inputs and compare order fail closed", async t => {
  let output;
  t.mock.method(globalThis, "fetch", () => Response.json(output));
  for (output of [envelope("baseten", { receipt: { ...receipt(), model: "arbitrary-model" } }),
    envelope("baseten", { receipt: { ...receipt(), cost_usd: -1 } }), envelope("baseten", { receipt: null }),
    envelope("baseten", { input: { kind: "upload", text_read: text } }), envelope("baseten", { receipt: undefined }),
    envelope("baseten", { cost_usd: .03 }), envelope("baseten", { latency_ms: 900 }),
    envelope("baseten", { history_truncated: "private" }), envelope("baseten", { cost_is_bound: "private" })]) {
    assert.equal((await onRequest({ request: post("check", { text }), env })).status, 503);
  }
  for (output of [{ runs: [envelope("fireworks"), envelope("baseten")] }, { runs: [envelope()] },
    { runs: [envelope(), envelope("meta"), envelope("fireworks")] }]) {
    assert.equal((await onCompare({ request: post("compare", { text, providers: ["baseten", "meta"] }), env })).status, 503);
  }
});

test("history summaries and detail never forward raw IP/UA or unknown fields", async t => {
  let detail = false;
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.url, `https://live-origin.example.com/api/history${detail ? "/" + "a".repeat(32) : "?limit=1"}`);
    for (const name of ["Cookie", "User-Agent", "Authorization"]) assert.equal(req.headers.get(name), null);
    assert.equal(req.headers.get("X-Live-Client-IP"), "192.0.2.1");
    const value = row({ ip: "192.0.2.1", raw_ip: "192.0.2.1", ua: "raw UA", user_agent: "raw UA", password: "drop",
      envelope: { ...envelope(), raw_ip: "192.0.2.1", user_agent: "raw UA", receipt: { ...receipt(), raw_ua: "drop" } } });
    return Response.json(detail ? value : { rows: [value], internal: "drop" });
  });
  for (detail of [false, true]) {
    const request = new Request(`https://site.example/api/history${detail ? "/" + "a".repeat(32) : "?limit=1"}`, {
      headers: { "User-Agent": "private UA", "CF-Connecting-IP": "192.0.2.1", Cookie: "private" } });
    const response = await onHistory({ request, env });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    assert.deepEqual(await response.json(), detail ? row({ envelope: envelope() }) : { rows: [row()] });
  }
});

test("history query and method limits, raw metadata substitution, 64 KiB and extra row bounds fail closed", async t => {
  let output = { rows: [] }, code = 200;
  t.mock.method(globalThis, "fetch", () => Response.json(output, { status: code }));
  for (const path of ["?limit=0", "?limit=51", "?limit=-1", "?limit=1&limit=2", "?all=1", "/../../private", "/bad-id"]) {
    assert.equal((await onHistory({ request: new Request("https://site.example/api/history" + path), env })).status, 400);
  }
  for (const headers of [{ Origin: "https://evil.example" }, { "Sec-Fetch-Site": "cross-site" }]) {
    assert.equal((await onHistory({ request: new Request("https://site.example/api/history", { headers }), env })).status, 403);
  }
  assert.equal((await onHistory({ request: post("history", {}), env })).status, 405);
  for (output of [{ rows: [row({ ip_masked: "192.0.2.1" })] }, { rows: [row({ browser: "Mozilla raw UA" })] },
    { rows: [row({ model: "private-model" })] }, { rows: [row({ id: ["a".repeat(32)] })] },
    { rows: [row({ at: "1" })] }, { rows: [row(), row()] }]) {
    assert.equal((await onHistory({ request: new Request("https://site.example/api/history?limit=1", { headers: { "CF-Connecting-IP": "192.0.2.1" } }), env })).status, 503);
  }
  output = row({ envelope: envelope("baseten", { events: [{ kind: "tool_result", result: "x".repeat(65537) }] }) });
  assert.equal((await onHistory({ request: new Request("https://site.example/api/history/" + "a".repeat(32), { headers: { "CF-Connecting-IP": "192.0.2.1" } }), env })).status, 503);
  output = { error: "not_found", secret: "drop" }; code = 404;
  assert.equal((await onHistory({ request: new Request("https://site.example/api/history/" + "a".repeat(32), { headers: { "CF-Connecting-IP": "192.0.2.1" } }), env })).status, 404);
});

test("history detail validates row identity and preserves failed or truncated attempts", async t => {
  let output;
  t.mock.method(globalThis, "fetch", () => Response.json(output));
  const request = () => new Request("https://site.example/api/history/" + "a".repeat(32), { headers: { "CF-Connecting-IP": "192.0.2.1" } });
  for (output of [row({ envelope: envelope("meta") }), row({ input_text: "different", envelope: envelope() }),
    row({ story: "b", envelope: envelope() }), row({ corrections_count: 1, envelope: envelope() })]) {
    assert.equal((await onHistory({ request: request(), env })).status, 503);
  }
  output = row({ verdict: null, envelope: envelope("baseten", { verdict: undefined, error: "budget_exhausted" }) });
  assert.equal((await onHistory({ request: request(), env })).status, 200);
  output = row({ verdict: "contradicted", corrections_count: 1,
    envelope: envelope("baseten", { verdict: "contradicted", history_truncated: true }) });
  assert.equal((await onHistory({ request: request(), env })).status, 200);
});

test("Pages manifest and Function entries cover compare and both history routes", () => {
  const routes = JSON.parse(readFileSync(new URL("../../docs/_routes.json", import.meta.url)));
  for (const route of ["/api/check", "/api/check-example", "/api/compare", "/api/history", "/api/history/*", "/api/budget"]) {
    assert.ok(routes.include.includes(route), route);
  }
  for (const [path, handler] of [["compare.ts", "onCompare"], ["history.ts", "onHistory"], ["history/[id].ts", "onHistory"]]) {
    assert.match(readFileSync(new URL("../../functions/api/" + path, import.meta.url), "utf8"), new RegExp(handler + " as onRequest"));
  }
});

test("budget uses the same origin rule as check, compare and history", async t => {
  t.mock.method(globalThis, "fetch", () => assert.fail("cross-origin request forwarded"));
  for (const headers of [{ Origin: "https://evil.example" }, { "Sec-Fetch-Site": "cross-site" }]) {
    assert.equal((await onBudget({ request: new Request("https://site.example/api/budget", { headers }), env })).status, 403);
  }
});
