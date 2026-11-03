// Verdicts run in the unchanged Python core. This boundary only validates and
// forwards requests. The offline fixture is opt-in AND restricted to loopback.
const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
};
const error = (code, status) => new Response(JSON.stringify({ error: code, demo: "data/live-demo.json" }), { status, headers });

async function originFetch(env, path, options = {}) {
  const host = env.LIVE_ORIGIN_HOST;
  if (typeof host !== "string" || host.length > 253 ||
      !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i.test(host) ||
      ![env.LIVE_ACCESS_CLIENT_ID, env.LIVE_ACCESS_CLIENT_SECRET, env.LIVE_ORIGIN_TOKEN]
        .every(value => typeof value === "string" && value.length > 0)) throw Error("unavailable");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 25000);
  try {
    const response = await fetch(new Request(`https://${host}${path}`, {
      ...options, redirect: "error", signal: controller.signal,
      headers: { ...options.headers,
        "CF-Access-Client-Id": env.LIVE_ACCESS_CLIENT_ID,
        "CF-Access-Client-Secret": env.LIVE_ACCESS_CLIENT_SECRET,
        "X-Live-Origin-Token": env.LIVE_ORIGIN_TOKEN },
    }));
    // Include body consumption in the timeout. Access HTML/redirects fail closed.
    const data = await response.json();
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
    if (!response.ok) return error("unavailable", 503);
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
  } catch { return error("unavailable", 503); }
};

export const onRequest = async ({ request, env }) => {
  const url = new URL(request.url);
  if (request.method !== "POST") return error("method_not_allowed", 405);
  if (request.headers.get("Origin") && request.headers.get("Origin") !== url.origin) return error("origin_rejected", 403);
  if (request.headers.get("Sec-Fetch-Site") === "cross-site") return error("origin_rejected", 403);
  if (!(request.headers.get("Content-Type") || "").toLowerCase().startsWith("application/json")) return error("invalid_input", 400);
  // Read at most 4 KiB even for chunked bodies. Content-Length is untrusted.
  const reader = request.body?.getReader();
  if (!reader) return error("invalid_input", 400);
  let size = 0;
  const chunks = [];
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 4096) { await reader.cancel(); return error("invalid_input", 400); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    let data;
    try { data = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
    catch { return error("invalid_input", 400); }
    if (typeof data?.text !== "string" || !data.text.trim() || Array.from(data.text.trim()).length > 600) return error("invalid_input", 400);
    const mock = env.LIVE_CHECK_MOCK === "1" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
    if (mock) {
      const response = await env.ASSETS.fetch(new Request(new URL("/data/live-demo.json", url)));
      if (!response.ok) return error("unavailable", 503);
      const demo = await response.json();
      if (data.text.trim() !== demo.input) return error("mock_input_only", 422);
      return new Response(JSON.stringify({ ...demo, mode: "mock" }), { headers });
    }
    const ip = request.headers.get("CF-Connecting-IP");
    if (!ip) return error("unavailable", 503);
    const { response, data: result } = await originFetch(env, "/api/check", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Live-Client-IP": ip },
      body: JSON.stringify({ text: data.text.trim(), password: typeof data.password === "string" ? data.password : "" }),
    });
    const errors = ["invalid_input", "unauthorized", "auth_rate_limited", "out_of_scope", "unavailable",
      "budget_exhausted", "total_budget_exhausted", "credit_exhausted", "rate_limited", "provider_error",
      "sec_unavailable", "incomplete_model", "tool_limit", "invalid_model_output", "timeout"];
    if (!result || typeof result !== "object" || Array.isArray(result) ||
        (response.status === 200 ? !["supported", "contradicted", "insufficient_evidence"].includes(result.verdict) :
          ![400, 401, 422, 429, 503, 504].includes(response.status) || !errors.includes(result.error))) {
      return error("unavailable", 503);
    }
    const fields = ["mode", "model", "provider", "events", "evidence", "cost_usd", "cost_is_bound", "latency_ms",
      "verdict", "model_verdict", "summary", "claims", "scope", "error", "demo", "budget"];
    const publicResult = Object.fromEntries(fields.filter(key => key in result).map(key => [key, result[key]]));
    return Response.json(publicResult, { status: response.status, headers });
  } catch {
    return error("unavailable", 503);
  }
};
