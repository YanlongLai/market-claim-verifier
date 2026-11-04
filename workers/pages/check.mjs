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

async function originFetch(env, path, options = {}, timeout = 25000) {
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

export const onBudget = async ({ request, env }) => {
  if (request.method !== "GET") return error("method_not_allowed", 405);
  const url = new URL(request.url);
  if (env.LIVE_CHECK_MOCK === "1" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) {
    const now = new Date(), reset = new Date(now);
    reset.setUTCHours(24, 0, 0, 0);
    return Response.json({ day: now.toISOString().slice(0, 10), daily_limit_usd: 3, daily_spent_usd: 0,
      daily_remaining_usd: 3, resets_at: reset.toISOString(), status: "ready", mode: "mock" }, { headers });
  }
  try {
    // Only origin credentials enter this request; no visitor headers or IP.
    const { response, data } = await originFetch(env, "/api/budget");
    // Status only (no body): tells Access (HTML 403), origin auth (JSON 401/403) and tunnel errors apart.
    if (!response.ok) return diagnostic(response.status);
    // Allowlist the public daily counters; never forward internal ledger data.
    const { day, daily_limit_usd, daily_spent_usd, daily_remaining_usd, resets_at, status } = data;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(Date.parse(resets_at)) ||
        ![daily_limit_usd, daily_spent_usd, daily_remaining_usd].every(v => typeof v === "number" && Number.isFinite(v) && v >= 0) ||
        !["ready", "budget_exhausted", "total_budget_exhausted", "credit_exhausted"].includes(status)) return error("unavailable", 503);
    // Post-check fetches bypass caches; ordinary page loads may reuse 5 s.
    return Response.json({ day, daily_limit_usd, daily_spent_usd, daily_remaining_usd, resets_at, status }, {
      headers: { ...headers, "Cache-Control": request.headers.get("Cache-Control") === "no-cache" ? "no-store" :
        "public, max-age=0, s-maxage=5, must-revalidate" }
    });
  } catch (failure) {
    // "config" = missing/invalid Pages settings; "network" = fetch threw before any response.
    return diagnostic(failure?.originStatus ?? (failure?.message === "unavailable" ? "config" : "network"));
  }
};

const exampleIds = new Set(["text", "image", "pdf", "audio", "video"]);
function publicInput(input) {
  const prep = input?.preprocessing;
  if (!exampleIds.has(input?.example_id) || input.kind !== input.example_id || typeof input.text_read !== "string" ||
      input.text_read.length > 50000 || typeof prep?.model !== "string" || prep.model.length > 200 ||
      !["meta", "local"].includes(prep.provider) || !Number.isFinite(prep.cost_usd) || prep.cost_usd < 0 ||
      !(prep.latency_ms === null || Number.isFinite(prep.latency_ms) && prep.latency_ms >= 0)) return null;
  return { example_id: input.example_id, kind: input.kind, text_read: input.text_read,
    preprocessing: { model: prep.model, provider: prep.provider, cost_usd: prep.cost_usd, latency_ms: prep.latency_ms } };
}

export const onRequest = context => onCheck(context, false);
export const onExample = context => onCheck(context, true);

async function onCheck({ request, env }, example) {
  const url = new URL(request.url);
  if (request.method !== "POST") return error("method_not_allowed", 405);
  if (request.headers.get("Origin") && request.headers.get("Origin") !== url.origin) return error("origin_rejected", 403);
  if (request.headers.get("Sec-Fetch-Site") === "cross-site") return error("origin_rejected", 403);
  if (!(request.headers.get("Content-Type") || "").toLowerCase().startsWith("application/json")) return error("invalid_input", 400);
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
      if (size > (example ? 1024 : 4096)) { await reader.cancel(); return error("invalid_input", 400); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    let data;
    try { data = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
    catch { return error("invalid_input", 400); }
    if (example ? !exampleIds.has(data?.example_id) :
      typeof data?.text !== "string" || !data.text.trim() || Array.from(data.text.trim()).length > 600) return error("invalid_input", 400);
    const mock = env.LIVE_CHECK_MOCK === "1" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
    if (mock) {
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
    const { response, data: result } = await originFetch(env, example ? "/api/check-example" : "/api/check", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Live-Client-IP": ip },
      body: JSON.stringify({ ...(example ? { example_id: data.example_id } : { text: data.text.trim() }),
        password: typeof data.password === "string" ? data.password : "" }),
    }, example ? 65000 : 25000);
    const errors = ["invalid_input", "unauthorized", "auth_rate_limited", "out_of_scope", "unavailable",
      "budget_exhausted", "total_budget_exhausted", "credit_exhausted", "rate_limited", "provider_error",
      "sec_unavailable", "incomplete_model", "tool_limit", "invalid_model_output", "timeout",
      ...(example ? ["unknown_example", "example_unavailable", "preprocessing_failed"] : [])];
    if (!result || typeof result !== "object" || Array.isArray(result) ||
        (response.status === 200 ? !["supported", "contradicted", "insufficient_evidence"].includes(result.verdict) :
          ![400, 401, 422, 429, 503, 504].includes(response.status) || !errors.includes(result.error))) {
      return error("unavailable", 503);
    }
    const fields = ["mode", "model", "provider", "events", "evidence", "cost_usd", "cost_is_bound", "latency_ms",
      "verdict", "model_verdict", "summary", "claims", "corrections", "scope", "error", "demo", "budget"];
    const publicResult = Object.fromEntries(fields.filter(key => key in result).map(key => [key, result[key]]));
    if (example && "input" in result) {
      const input = publicInput(result.input);
      if (!input || input.example_id !== data.example_id) return error("unavailable", 503);
      publicResult.input = input;
    } else if (example && response.status === 200) return error("unavailable", 503);
    return Response.json(publicResult, { status: response.status, headers });
  } catch {
    return error("unavailable", 503);
  }
}
