import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { onProgress, onRequest, onCompare, onBudget, onHistory } from "../../workers/pages/check.mjs";

const id = "12345678-1234-4567-89ab-123456789abf";
const env = { LIVE_ORIGIN_HOST: "live-origin.example.com", LIVE_ACCESS_CLIENT_ID: "access-id-marker",
  LIVE_ACCESS_CLIENT_SECRET: "access-secret-marker", LIVE_ORIGIN_TOKEN: "origin-token-marker" };
const headers = { "CF-Connecting-IP": "192.0.2.1", "X-Live-Client-IP": "spoofed", Cookie: "private" };
const get = (path, options = {}) => new Request(`https://site.example/api/${path}`, { headers, ...options });
const post = (path, body, options = {}) => get(path, { method: "POST", body: JSON.stringify(body),
  headers: { ...headers, "Content-Type": "application/json" }, ...options });
const envelope = provider => ({ verdict: "supported", receipt: { provider, model: provider === "meta" ? "muse-spark-1.3" :
  "meta-models/muse-spark-open-1026", cost_usd: .01, latency_ms: 1000, preprocessing: null }, input: { kind: "text", text_read: "Apple FY2025 revenue was $416B." } });

test("progress proxy forwards Access/trusted IP, validates cursor and projects fields only", async t => {
  t.mock.method(globalThis, "fetch", async req => {
    assert.equal(req.url, `https://live-origin.example.com/api/progress/${id}?after=3`);
    assert.equal(req.headers.get("X-Live-Client-IP"), "192.0.2.1");
    assert.equal(req.headers.get("CF-Access-Client-Id"), env.LIVE_ACCESS_CLIENT_ID);
    assert.equal(req.headers.get("CF-Access-Client-Secret"), env.LIVE_ACCESS_CLIENT_SECRET);
    assert.equal(req.headers.get("X-Live-Origin-Token"), env.LIVE_ORIGIN_TOKEN);
    assert.equal(req.headers.get("Cookie"), null);
    assert.equal(req.redirect, "manual");
    return Response.json({ lines: [{ t_s: 4.3, text: "tool_result  E1  143100000000  USD  10-Q", secret: "drop" }],
      done: false, next: 4, input_text: "drop", ip: "drop" });
  });
  const response = await onProgress({ request: get(`progress/${id}?after=3`), env });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
  assert.deepEqual(await response.json(), { lines: [{ t_s: 4.3, text: "tool_result  E1  143100000000  USD  10-Q" }], done: false, next: 4 });
});

test("progress rejects wrong IDs, cursors, methods and cross-origin before origin I/O", async t => {
  t.mock.method(globalThis, "fetch", () => assert.fail("invalid progress forwarded"));
  for (const path of ["progress/bad", `progress/${id.replace("-4567-", "-1567-")}`, `progress/${id}?after=-1`,
    `progress/${id}?after=1&after=2`, `progress/${id}?password=x`]) {
    assert.equal((await onProgress({ request: get(path), env })).status, 400);
  }
  assert.equal((await onProgress({ request: get(`progress/${id}`, { method: "POST" }), env })).status, 405);
  assert.equal((await onProgress({ request: get(`progress/${id}`, { headers: { ...headers, Origin: "https://evil.example" } }), env })).status, 403);
});

test("unknown progress, burst denial and malformed upstream data fail closed", async t => {
  let output, status;
  t.mock.method(globalThis, "fetch", () => Response.json(output, { status }));
  for (const [value, code, expected] of [[{ error: "not_found", secret: "drop" }, 404, 404],
    [{ error: "slow_down", secret: "drop" }, 429, 429], [{ error: "secret-marker" }, 503, 503],
    [{ lines: [{ t_s: -1, text: "bad" }], done: false, next: 1 }, 200, 503],
    [{ lines: [{ t_s: 0, text: "bad\nline" }], done: false, next: 1 }, 200, 503],
    [{ lines: [], done: "false", next: 0 }, 200, 503],
    [{ lines: [], done: false, next: -1 }, 200, 503],
    [{ lines: Array(201).fill({ t_s: 0, text: "x" }), done: true, next: 201 }, 200, 503]]) {
    output = value; status = code;
    const response = await onProgress({ request: get(`progress/${id}`), env });
    assert.equal(response.status, expected);
    assert.ok(!(await response.text()).includes("secret"));
  }
});

test("check and compare forward only validated UUID v4 IDs; compare derives unique member IDs", async t => {
  const seen = [];
  t.mock.method(globalThis, "fetch", async req => {
    const body = await req.json(); seen.push(body.client_run_id);
    assert.deepEqual(Object.keys(body).sort(), ["client_run_id", "password", "provider", "text"]);
    return Response.json(envelope(body.provider));
  });
  const response = await onCompare({ request: post("compare", { text: "Apple FY2025 revenue was $416B.", password: "x",
    providers: ["meta", "baseten"], client_run_id: id }), env });
  assert.equal(response.status, 200);
  assert.deepEqual(seen, [id, id.slice(0, -1) + "0"]);
  for (const client_run_id of [false, {}, "../private", id.replace("-4567-", "-1567-")]) {
    assert.equal((await onRequest({ request: post("check", { text: "Apple FY2025 revenue was $416B.", client_run_id }), env })).status, 400);
  }
  assert.equal(seen.length, 2);
});

test("all new 429 states survive Pages and non-JSON / >16 KiB bodies never reach origin", async t => {
  let code, calls = 0;
  t.mock.method(globalThis, "fetch", () => { calls++; return Response.json({ error: code, secret: "drop" }, { status: 429 }); });
  for (code of ["locked", "busy", "slow_down"]) {
    const response = await onRequest({ request: post("check", { text: "Apple FY2025 revenue was $416B.", client_run_id: id }), env });
    assert.equal(response.status, 429); assert.equal((await response.json()).error, code);
  }
  code = "slow_down";
  for (const [handler, path] of [[onBudget, "budget"], [onHistory, "history"]]) {
    const response = await handler({ request: get(path), env });
    assert.equal(response.status, 429); assert.equal((await response.json()).error, code);
  }
  const before = calls;
  const oversized = new ReadableStream({ start(c) { c.enqueue(new Uint8Array(16385)); c.close(); } });
  for (const request of [post("check", { text: "x" }, { headers: { ...headers, "Content-Type": "text/plain" } }),
    post("check", {}, { body: oversized, duplex: "half" })]) {
    assert.equal((await onRequest({ request, env })).status, 400);
  }
  assert.equal(calls, before);
});

test("Pages route and Docker image include progress", () => {
  assert.ok(JSON.parse(readFileSync(new URL("../../docs/_routes.json", import.meta.url))).include.includes("/api/progress/*"));
  assert.ok(readFileSync(new URL("../../functions/api/progress/[id].ts", import.meta.url), "utf8").includes("onProgress as onRequest"));
  assert.match(readFileSync(new URL("../../server/live/Dockerfile", import.meta.url), "utf8"), /COPY server\/live\/server.py server\/live\/progress.py/);
});

test("history summary exposes only an allowlisted saved error", async t => {
  const row = { id: "a".repeat(32), at: "2026-11-03T17:00:00.000Z", ip_masked: "unknown", device: "Unknown / unknown",
    browser: "Other", kind: "text", example_id: null, story: null, input_text: "Apple FY2025 revenue was $416B.",
    provider: "baseten", model: "meta-models/muse-spark-open-1026", verdict: null, corrections_count: 0,
    latency_ms: 10, cost_usd: 0, preprocessing_cost_usd: 0, error: "busy" };
  t.mock.method(globalThis, "fetch", () => Response.json({ rows: [{ ...row, secret: "drop" }] }));
  const response = await onHistory({ request: get("history"), env });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { rows: [row] });
  row.error = "private-provider-body";
  assert.equal((await onHistory({ request: get("history"), env })).status, 503);
});
