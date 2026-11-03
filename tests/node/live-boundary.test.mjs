import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { onRequest, onBudget } from "../../workers/pages/check.mjs";

const demo = JSON.parse(readFileSync(new URL("../../docs/site/data/live-demo.json", import.meta.url)));
const request = (body = { text: demo.input }, more = {}, host = "localhost") => new Request(`http://${host}/api/check`, {
  method: "POST", headers: { "Content-Type": "application/json", ...more }, body: JSON.stringify(body)
});
const assets = { fetch: async () => Response.json(demo) };

test("offline Pages mock is labelled, accepts only the recorded input, and does not call a model", async () => {
  const env = { LIVE_CHECK_MOCK: "1", ASSETS: assets, LIVE_CHECK: { fetch() { assert.fail("model"); } } };
  const response = await onRequest({ request: request(), env });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
  assert.equal((await response.json()).mode, "mock");
  assert.equal((await onRequest({ request: request({ text: "Other claim" }), env })).status, 422);
  const budget = await onBudget({ request: new Request("http://localhost/api/budget"), env });
  assert.equal((await budget.json()).mode, "mock");
  assert.equal(budget.headers.get("Cache-Control"), "no-store");
  assert.equal((await onBudget({ request: new Request("https://site.example/api/budget"), env: { LIVE_CHECK_MOCK: "1" } })).status, 503);
});

test("production cannot enable the local mock or supply its own forwarded IP", async () => {
  let calls = 0;
  const env = { LIVE_CHECK_MOCK: "1", ASSETS: assets, LIVE_CHECK: { async fetch(req) {
    calls++;
    assert.equal(req.url, "https://live.internal/api/check");
    assert.equal(req.headers.get("X-Live-Client-IP"), "192.0.2.1");
    assert.equal(req.headers.get("Authorization"), null);
    assert.deepEqual(await req.json(), { text: demo.input });
    return Response.json({ verdict: "supported", mode: "live" });
  } } };
  const response = await onRequest({ request: request({ text: demo.input, secret: "drop" }, {
    "CF-Connecting-IP": "192.0.2.1", "X-Live-Client-IP": "spoofed"
  }, "hackathon.dappgo.com"), env });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).mode, "live");
  assert.equal(calls, 1);
});

test("origin, length, byte size, JSON and content-type checks happen before forwarding", async () => {
  const env = { LIVE_CHECK: { fetch() { assert.fail("forwarded invalid request"); } } };
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

test("missing service, missing trusted IP, and service failures fail closed with saved demo", async () => {
  const missingIP = await onRequest({ request: request(), env: { LIVE_CHECK: { fetch() { assert.fail("IP missing"); } } } });
  assert.equal(missingIP.status, 503);
  for (const env of [{}, { LIVE_CHECK: { fetch() { throw new Error("private detail"); } } }]) {
    const response = await onRequest({ request: request(undefined, { "CF-Connecting-IP": "192.0.2.1" }), env });
    assert.equal(response.status, 503);
    assert.equal((await response.json()).demo, "data/live-demo.json");
  }
});

const budget = { day: "2026-11-02", daily_limit_usd: 3, daily_spent_usd: .59,
  daily_remaining_usd: 2.41, resets_at: "2026-11-03T00:00:00Z", status: "ready" };

test("public budget uses the private ledger, excludes private data, and caches for at most five seconds", async () => {
  let calls = 0;
  const env = { LIVE_CHECK: { async fetch(req) {
    calls++;
    assert.equal(req.url, "https://live.internal/api/budget");
    assert.equal(req.method, "GET");
    assert.deepEqual([...req.headers], []);
    return Response.json({ ...budget, holds: "private", salt: "private", lifetime_nanos: 12345 });
  } } };
  for (const fresh of [false, true]) {
    const response = await onBudget({ request: new Request("https://site.example/api/budget", {
      headers: { "Authorization": "must-not-forward", "Cookie": "must-not-forward", ...(fresh ? { "Cache-Control": "no-cache" } : {}) }
    }), env });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("Cache-Control"), fresh ? "no-store" : "public, max-age=0, s-maxage=5, must-revalidate");
    assert.deepEqual(await response.json(), budget);
  }
  assert.equal(calls, 2);
});

test("budget errors are uncached and never expose service exceptions", async () => {
  const req = new Request("https://site.example/api/budget");
  for (const env of [{}, { LIVE_CHECK: { fetch() { throw Error("private"); } } },
    { LIVE_CHECK: { fetch: async () => Response.json({ error: "private" }, { status: 503 }) } },
    { LIVE_CHECK: { fetch: async () => Response.json({ ...budget, daily_remaining_usd: -1 }) } }]) {
    const response = await onBudget({ request: req, env });
    assert.equal(response.status, 503);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    assert.deepEqual(await response.json(), { error: "unavailable", demo: "data/live-demo.json" });
  }
  assert.equal((await onBudget({ request: new Request(req.url, { method: "POST" }), env: {} })).status, 405);
});
