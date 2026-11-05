// Verdicts run in the unchanged Python core. This boundary only validates and
// forwards requests. The offline fixture is opt-in AND restricted to loopback.
const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
};
const diagnostic = originStatus => new Response(JSON.stringify({ error: "unavailable", demo: "data/live-demo.json",
  origin_status: originStatus }), { status: 503, headers });
const error = (code, status) => new Response(JSON.stringify({ error: code, demo: "data/live-demo.json" }), { status, headers });

async function originFetch(env, path, options = {}, timeout = 92000) {
  // Dashboard pastes can carry a trailing newline, which is invalid in a header.
  const clean = value => typeof value === "string" ? value.trim() : value;
  env = { ...env, LIVE_ORIGIN_HOST: clean(env.LIVE_ORIGIN_HOST), LIVE_ACCESS_CLIENT_ID: clean(env.LIVE_ACCESS_CLIENT_ID),
    LIVE_ACCESS_CLIENT_SECRET: clean(env.LIVE_ACCESS_CLIENT_SECRET), LIVE_ORIGIN_TOKEN: clean(env.LIVE_ORIGIN_TOKEN) };
  const host = env.LIVE_ORIGIN_HOST;
  if (typeof host !== "string" || host.length > 253 ||
      !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i.test(host) ||
      ![env.LIVE_ACCESS_CLIENT_ID, env.LIVE_ACCESS_CLIENT_SECRET, env.LIVE_ORIGIN_TOKEN]
        .every(value => typeof value === "string" && value.length > 0)) throw Error("unavailable");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(new Request(`https://${host}${path}`, {
      // Workers fetch supports only "follow"|"manual"; "error" throws. A 3xx is not ok, so it fails closed.
      ...options, redirect: "manual", signal: controller.signal,
      headers: { ...options.headers,
        "CF-Access-Client-Id": env.LIVE_ACCESS_CLIENT_ID,
        "CF-Access-Client-Secret": env.LIVE_ACCESS_CLIENT_SECRET,
        "X-Live-Origin-Token": env.LIVE_ORIGIN_TOKEN },
    }));
    // Include body consumption in the timeout. Access HTML/redirects fail closed.
    let data;
    try { data = await response.json(); }
    catch { throw Object.assign(Error("non_json"), { originStatus: `${response.status}-html` }); }
    return { response, data };
  } finally { clearTimeout(timer); }
}

const budgetStatuses = new Set(["ready", "budget_exhausted", "total_budget_exhausted", "credit_exhausted"]);
const budgetCounters = ["daily_limit", "daily_spent", "daily_remaining", "lifetime_limit", "lifetime_spent", "lifetime_remaining"];
function publicBudgetRow(row) {
  if (!row || !budgetStatuses.has(row.status) || !budgetCounters.every(key =>
    typeof row[key] === "number" && Number.isFinite(row[key]) && row[key] >= 0)) return null;
  return Object.fromEntries([...budgetCounters, "status"].map(key => [key, row[key]]));
}
function publicBudget(data) {
  if (!data || !/^\d{4}-\d{2}-\d{2}$/.test(data.day) || !Number.isFinite(Date.parse(data.resets_at)) ||
      !budgetStatuses.has(data.status)) return null;
  const providers = {};
  for (const name of ["baseten", "fireworks", "meta"]) {
    providers[name] = publicBudgetRow(data.providers?.[name]);
    if (!providers[name]) return null;
  }
  const result = { day: data.day, providers, status: data.status, resets_at: data.resets_at };
  // Compatibility sums contain public counters only; no ledger/hold fields.
  for (const key of budgetCounters) result[key + "_usd"] = Math.round(
    Object.values(providers).reduce((sum, row) => sum + row[key], 0) * 1e9) / 1e9;
  if ("global" in data) {
    result.global = publicBudgetRow(data.global);
    if (!result.global) return null;
  }
  return result;
}

export const onBudget = async ({ request, env }) => {
  if (request.method !== "GET") return error("method_not_allowed", 405);
  const url = new URL(request.url);
  if (!sameOrigin(request, url)) return error("origin_rejected", 403);
  if (env.LIVE_CHECK_MOCK === "1" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) {
    const now = new Date(), reset = new Date(now);
    reset.setUTCHours(24, 0, 0, 0);
    const row = { daily_limit: 30, daily_spent: 0, daily_remaining: 30,
      lifetime_limit: 20, lifetime_spent: 0, lifetime_remaining: 20, status: "ready" };
    return Response.json({ ...publicBudget({ day: now.toISOString().slice(0, 10), resets_at: reset.toISOString(),
      status: "ready", providers: { baseten: row, fireworks: row, meta: row } }), mode: "mock" }, { headers });
  }
  try {
    const { response, data } = await originFetch(env, "/api/budget", { headers: clientHeaders(request) });
    if (response.status === 429 && ["slow_down", "busy", "locked"].includes(data?.error)) return error(data.error, 429);
    // Status only (no body): tells Access (HTML 403), origin auth (JSON 401/403) and tunnel errors apart.
    if (!response.ok) return diagnostic(response.status);
    const budget = publicBudget(data);
    if (!budget) return error("unavailable", 503);
    // Post-check fetches bypass caches; ordinary page loads may reuse 5 s.
    return Response.json(budget, {
      headers: { ...headers, "Cache-Control": request.headers.get("Cache-Control") === "no-cache" ? "no-store" :
        "public, max-age=0, s-maxage=5, must-revalidate" }
    });
  } catch (failure) {
    // "config" = missing/invalid Pages settings; "network" = fetch threw before any response.
    return diagnostic(failure?.originStatus ?? (failure?.message === "unavailable" ? "config" : "network"));
  }
};

const kinds = ["text", "image", "pdf", "audio", "video"];
const exampleIds = new Set([...kinds, ...["a", "b", "c"].flatMap(story => kinds.map(kind => `${story}-${kind}`))]);
const models = { baseten: "meta-models/muse-spark-open-1026", fireworks: "accounts/fireworks/models/muse-spark-open", meta: "muse-spark-1.3" };
const preprocessingModels = new Set(["native-text", "native-pdf", "muse-spark-1.3", "muse-voice-transcribe-1.0", "muse-voice-transcribe-1.0 + muse-spark-1.3"]);
const errors = new Set(["invalid_input", "unauthorized", "auth_rate_limited", "locked", "busy", "slow_down", "out_of_scope", "unavailable",
  "unknown_provider", "budget_exhausted", "total_budget_exhausted", "credit_exhausted", "rate_limited", "provider_error", "provider_overloaded",
  "sec_unavailable", "incomplete_model", "tool_limit", "invalid_model_output", "timeout", "unknown_example", "example_unavailable", "preprocessing_failed"]);
const verdicts = new Set(["supported", "contradicted", "insufficient_evidence"]);
const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const number = value => typeof value === "number" && Number.isFinite(value) && value >= 0;
const provider = value => typeof value === "string" && Object.hasOwn(models, value);
const pick = (value, fields) => Object.fromEntries(fields.filter(key => Object.hasOwn(value, key)).map(key => [key, value[key]]));
const sameOrigin = (request, url) => (!request.headers.get("Origin") || request.headers.get("Origin") === url.origin) &&
  request.headers.get("Sec-Fetch-Site") !== "cross-site";
const mockMode = (env, url) => env.LIVE_CHECK_MOCK === "1" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);

function publicPreprocessing(prep, legacy = false) {
  if (!object(prep) || !preprocessingModels.has(prep.model) || !number(prep.cost_usd) ||
      !(number(prep.latency_ms) || legacy && prep.latency_ms === null) ||
      legacy && !["meta", "local"].includes(prep.provider)) return null;
  return pick(prep, legacy ? ["model", "provider", "latency_ms", "cost_usd"] : ["model", "latency_ms", "cost_usd"]);
}

function publicInput(input) {
  if (!object(input) || !kinds.includes(input.kind) || typeof input.text_read !== "string" ||
      Array.from(input.text_read).length > 12000 ||
      "example_id" in input && (!exampleIds.has(input.example_id) || input.example_id.split("-").at(-1) !== input.kind) ||
      "story" in input && (!["a", "b", "c"].includes(input.story) ||
        "example_id" in input && input.story !== (input.example_id.includes("-") ? input.example_id.split("-")[0] : "a"))) return null;
  const result = pick(input, ["kind", "example_id", "story", "text_read"]);
  if ("preprocessing" in input) {
    result.preprocessing = publicPreprocessing(input.preprocessing, true);
    if (!result.preprocessing) return null;
  }
  return result;
}

function publicReceipt(receipt) {
  if (!object(receipt) || !provider(receipt.provider) || models[receipt.provider] !== receipt.model ||
      !number(receipt.cost_usd) || !number(receipt.latency_ms)) return null;
  const preprocessing = receipt.preprocessing === null ? null : publicPreprocessing(receipt.preprocessing);
  if (receipt.preprocessing !== null && !preprocessing) return null;
  return { ...pick(receipt, ["provider", "model", "latency_ms", "cost_usd"]), preprocessing };
}

function publicEnvelope(value, required = false) {
  if (!object(value) || !(verdicts.has(value.verdict) || errors.has(value.error)) ||
      "error" in value && !errors.has(value.error) || "mode" in value && !["live", "mock", "recorded"].includes(value.mode) ||
      "history_truncated" in value && typeof value.history_truncated !== "boolean" ||
      "cost_is_bound" in value && typeof value.cost_is_bound !== "boolean") return null;
  const result = pick(value, ["mode", "model", "provider", "events", "evidence", "cost_usd", "cost_is_bound", "latency_ms",
    "verdict", "model_verdict", "summary", "claims", "corrections", "scope", "error", "demo", "history_truncated", "request_id"]);
  if ("budget" in value) {
    result.budget = publicBudget(value.budget);
    if (!result.budget) return null;
  }
  if (required || "receipt" in value) {
    result.receipt = publicReceipt(value.receipt);
    if (!result.receipt || "provider" in value && value.provider !== result.receipt.provider ||
        "model" in value && value.model !== result.receipt.model) return null;
  }
  if (required || "input" in value) {
    result.input = publicInput(value.input);
    if (!result.input) return null;
  }
  if (result.receipt) {
    const prep = result.receipt.preprocessing;
    if ("cost_usd" in result && (!number(result.cost_usd) ||
        Math.abs(result.cost_usd - result.receipt.cost_usd - (prep?.cost_usd ?? 0)) > 1e-8) ||
        "latency_ms" in result && (!number(result.latency_ms) ||
        Math.abs(result.latency_ms - result.receipt.latency_ms - (prep?.latency_ms ?? 0)) > .01)) return null;
  }
  return result;
}

export const onRequest = context => onCheck(context, "check");
export const onExample = context => onCheck(context, "check-example");
export const onCompare = context => onCheck(context, "compare");

async function onCheck({ request, env }, action) {
  const url = new URL(request.url);
  const compare = action === "compare";
  if (request.method !== "POST") return error("method_not_allowed", 405);
  if (!sameOrigin(request, url)) return error("origin_rejected", 403);
  if ((request.headers.get("Content-Type") || "").split(";", 1)[0].trim().toLowerCase() !== "application/json" || url.search) return error("invalid_input", 400);
  // Byte limits include chunked bodies. Content-Length is untrusted.
  const reader = request.body?.getReader();
  if (!reader) return error("invalid_input", 400);
  let size = 0;
  const chunks = [];
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 1024) { await reader.cancel(); return error("invalid_input", 400); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    let data;
    try { data = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
    catch { return error("invalid_input", 400); }
    if (!object(data)) return error("invalid_input", 400);
    if ("client_run_id" in data && (typeof data.client_run_id !== "string" || !runId.test(data.client_run_id))) return error("invalid_input", 400);
    const example = action === "check-example" || compare && "example_id" in data;
    const inputKey = example ? "example_id" : "text";
    const allowed = new Set([inputKey, "password", "client_run_id", compare ? "providers" : "provider"]);
    if (Object.keys(data).some(key => !allowed.has(key)) || (example ? !exampleIds.has(data.example_id) :
      typeof data?.text !== "string" || !data.text.trim() || Array.from(data.text.trim()).length > 600)) return error("invalid_input", 400);
    if (compare ? !Array.isArray(data.providers) || data.providers.length < 2 || data.providers.length > 3 ||
        new Set(data.providers).size !== data.providers.length : false) return error("invalid_input", 400);
    const requestedProviders = compare ? data.providers : [data.provider ?? "baseten"];
    if (requestedProviders.some(value => !provider(value)) || "provider" in data && !provider(data.provider)) return error("unknown_provider", 400);
    if (mockMode(env, url)) {
      if (compare || requestedProviders[0] !== "baseten") return error("mock_input_only", 422);
      if (example) {
        const response = await env.ASSETS.fetch(new Request(new URL(`/data/examples/${data.example_id}.json`, url)));
        if (!response.ok) return error("saved_result_pending", 503);
        const demo = await response.json();
        const input = publicInput(demo.input);
        if (!input || input.example_id !== data.example_id) return error("unavailable", 503);
        return Response.json({ ...demo, input, mode: "mock" }, { headers });
      }
      for (const path of ["/data/live-demo-post.json", "/data/live-demo.json"]) {
        const response = await env.ASSETS.fetch(new Request(new URL(path, url)));
        if (!response.ok) return error("unavailable", 503);
        const demo = await response.json();
        if (data.text.trim() === demo.input.trim()) {
          return new Response(JSON.stringify({ ...demo, mode: "mock" }), { headers });
        }
      }
      return error("mock_input_only", 422);
    }
    const ip = request.headers.get("CF-Connecting-IP");
    if (!ip) return error("unavailable", 503);
    // Each member gets a separate origin response below Cloudflare's 100 s limit.
    // The shared deadline also bounds three 97 s example requests to 290 s total.
    const deadline = Date.now() + 290000;
    const runs = [];
    for (const [index, selected] of requestedProviders.entries()) {
      const remaining = deadline - Date.now();
      if (remaining <= 0) return error("timeout", 504);
      const { response, data: result } = await originFetch(env, `/api/${example ? "check-example" : "check"}`, {
        method: "POST", headers: { "Content-Type": "application/json", "X-Live-Client-IP": ip,
          ...(request.headers.get("User-Agent") ? { "User-Agent": request.headers.get("User-Agent").slice(0, 1024) } : {}) },
        body: JSON.stringify({ ...(example ? { example_id: data.example_id } : { text: data.text.trim() }),
          ...("client_run_id" in data ? { client_run_id: memberId(data.client_run_id, index) } : {}),
          password: typeof data.password === "string" ? data.password : "",
          ...(compare || "provider" in data ? { provider: selected } : {}) }),
      }, Math.min(example ? 97000 : 92000, remaining));
      if (response.status !== 200 && (![400, 401, 422, 429, 503, 504].includes(response.status) || !errors.has(result?.error))) return error("unavailable", 503);
      // Authentication/validation failures have not started a member run.
      const rejected = ["invalid_input", "unauthorized", "auth_rate_limited", "locked", "slow_down", "unknown_provider", "out_of_scope", "unknown_example", "example_unavailable"].includes(result?.error);
      const requireReceipt = response.status === 200 || compare && !rejected;
      const publicResult = publicEnvelope(result, requireReceipt);
      if (!publicResult || response.status === 200 && !verdicts.has(publicResult.verdict) ||
          requireReceipt && (publicResult.receipt.provider !== selected ||
            example && publicResult.input.example_id !== data.example_id)) return error("unavailable", 503);
      if (!compare || rejected) return Response.json(publicResult, { status: response.status, headers });
      runs.push(publicResult);
      if (["rate_limited", "busy", "slow_down", "locked"].includes(publicResult.error)) break;
    }
    return Response.json({ runs }, { headers });
  } catch {
    return error("unavailable", 503);
  }
}

const devices = new Set(["iPadOS / tablet", "iOS / mobile", "Android / mobile", "Android / tablet", "ChromeOS / desktop",
  "Windows / desktop", "macOS / desktop", "Linux / desktop", "Unknown / unknown"]);
const browsers = new Set(["Edge", "Opera", "Samsung Internet", "Firefox", "Chrome", "Safari", "Internet Explorer", "Other"]);
const historyId = /^[0-9a-f]{32}$/;
function publicHistoryRow(row, full = false) {
  if (!object(row) || typeof row.id !== "string" || !historyId.test(row.id) || typeof row.at !== "string" ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(row.at) || !Number.isFinite(Date.parse(row.at)) ||
      typeof row.ip_masked !== "string" || !/^(?:unknown|(?:\d{1,3}\.\d{1,3}\.\*\.\*|[0-9a-f]{4}:[0-9a-f]{4}:\*)#[0-9a-f]{8})$/.test(row.ip_masked) ||
      !devices.has(row.device) || !browsers.has(row.browser) || !kinds.includes(row.kind) ||
      !(row.example_id === null || exampleIds.has(row.example_id) && row.example_id.split("-").at(-1) === row.kind) ||
      !(row.story === null || ["a", "b", "c"].includes(row.story)) ||
      typeof row.input_text !== "string" || Array.from(row.input_text).length > 600 || !provider(row.provider) || models[row.provider] !== row.model ||
      !(row.verdict === null || verdicts.has(row.verdict)) || !Number.isSafeInteger(row.corrections_count) || row.corrections_count < 0 ||
      ![row.latency_ms, row.cost_usd, row.preprocessing_cost_usd].every(number)) return null;
  const result = pick(row, ["id", "at", "ip_masked", "device", "browser", "kind", "example_id", "story", "input_text",
    "provider", "model", "verdict", "corrections_count", "latency_ms", "cost_usd", "preprocessing_cost_usd"]);
  if ("error" in row) {
    if (!errors.has(row.error)) return null;
    result.error = row.error;
  }
  if (full) {
    if (new TextEncoder().encode(JSON.stringify(row.envelope)).length > 65536) return null;
    result.envelope = publicEnvelope(row.envelope, true);
    if (!result.envelope || result.envelope.receipt.provider !== row.provider || result.envelope.input.kind !== row.kind ||
        (result.envelope.input.example_id ?? null) !== row.example_id || (result.envelope.input.story ?? null) !== row.story ||
        Array.from(result.envelope.input.text_read).slice(0, 600).join("") !== row.input_text ||
        !result.envelope.history_truncated && (result.envelope.corrections?.edits?.length ?? 0) !== row.corrections_count ||
        (result.envelope.verdict ?? null) !== row.verdict || result.envelope.receipt.cost_usd !== row.cost_usd ||
        result.envelope.receipt.latency_ms !== row.latency_ms ||
        (result.envelope.receipt.preprocessing?.cost_usd ?? 0) !== row.preprocessing_cost_usd) return null;
  }
  return result;
}

export async function onHistory({ request, env }) {
  const url = new URL(request.url);
  if (request.method !== "GET") return error("method_not_allowed", 405);
  if (!sameOrigin(request, url)) return error("origin_rejected", 403);
  const detail = /^\/api\/history\/([0-9a-f]{32})$/.exec(url.pathname);
  let path;
  if (detail) {
    if (url.search) return error("invalid_input", 400);
    path = `/api/history/${detail[1]}`;
  } else {
    const limits = url.searchParams.getAll("limit");
    if (url.pathname !== "/api/history" || [...url.searchParams.keys()].some(key => key !== "limit") || limits.length > 1 ||
        !/^[1-9][0-9]?$/.test(limits[0] ?? "50") || Number(limits[0] ?? 50) > 50) return error("invalid_input", 400);
    path = `/api/history?limit=${limits[0] ?? 50}`;
  }
  if (mockMode(env, url)) return detail ? error("not_found", 404) : Response.json({ rows: [] }, { headers });
  try {
    const { response, data } = await originFetch(env, path, { headers: clientHeaders(request) });
    if (response.status === 429 && data?.error === "slow_down") return error("slow_down", 429);
    if (response.status === 404 && detail && data?.error === "not_found") return error("not_found", 404);
    if (!response.ok) return error("unavailable", 503);
    if (detail) {
      const row = publicHistoryRow(data, true);
      return row && row.id === detail[1] ? Response.json(row, { headers }) : error("unavailable", 503);
    }
    if (!Array.isArray(data?.rows) || data.rows.length > Number(url.searchParams.get("limit") ?? 50)) return error("unavailable", 503);
    const rows = data.rows.map(row => publicHistoryRow(row));
    return rows.every(Boolean) ? Response.json({ rows }, { headers }) : error("unavailable", 503);
  } catch { return error("unavailable", 503); }
}


const runId = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const memberId = (id, index) => id.slice(0, -1) + ((parseInt(id.at(-1), 16) + index) % 16).toString(16);
function clientHeaders(request) {
  const ip = request.headers.get("CF-Connecting-IP");
  if (!ip) throw Error("unavailable");
  return { "X-Live-Client-IP": ip };
}

export async function onProgress({ request, env }) {
  const url = new URL(request.url);
  if (request.method !== "GET") return error("method_not_allowed", 405);
  if (!sameOrigin(request, url)) return error("origin_rejected", 403);
  const id = url.pathname.slice("/api/progress/".length);
  const after = url.searchParams.get("after") ?? "0";
  if (!url.pathname.startsWith("/api/progress/") || !runId.test(id) ||
      [...url.searchParams.keys()].some(key => key !== "after") || url.searchParams.getAll("after").length > 1 ||
      !/^(?:0|[1-9][0-9]{0,8})$/.test(after)) return error("invalid_input", 400);
  if (mockMode(env, url)) return error("not_found", 404);
  try {
    const { response, data } = await originFetch(env, `/api/progress/${id}?after=${after}`,
      { headers: clientHeaders(request) }, 10000);
    if (response.status === 404 && data?.error === "not_found") return error("not_found", 404);
    if (response.status === 429 && data?.error === "slow_down") return error("slow_down", 429);
    if (!response.ok || !object(data) || !Array.isArray(data.lines) || data.lines.length > 200 ||
        typeof data.done !== "boolean" || !Number.isSafeInteger(data.next) || data.next < Number(after) ||
        data.next - Number(after) < data.lines.length || data.lines.some(line => !object(line) || !number(line.t_s) ||
          typeof line.text !== "string" || line.text.length > 512 || /[\x00-\x1f\x7f]/.test(line.text))) return error("unavailable", 503);
    return Response.json({ lines: data.lines.map(line => pick(line, ["t_s", "text"])), done: data.done, next: data.next }, { headers });
  } catch { return error("unavailable", 503); }
}
