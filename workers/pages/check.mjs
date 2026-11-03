// Verdicts run in the unchanged Python core. This boundary only validates and
// forwards requests. The offline fixture is opt-in AND restricted to loopback.
const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
};
const error = (code, status) => new Response(JSON.stringify({ error: code, demo: "data/live-demo.json" }), { status, headers });

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
    if (!env.LIVE_CHECK) return error("unavailable", 503);
    const ip = request.headers.get("CF-Connecting-IP");
    if (!ip) return error("unavailable", 503);
    const forwarded = new Request("https://live.internal/api/check", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Live-Client-IP": ip },
      body: JSON.stringify({ text: data.text.trim() }),
    });
    const response = await env.LIVE_CHECK.fetch(forwarded);
    return new Response(response.body, { status: response.status, headers });
  } catch {
    return error("unavailable", 503);
  }
};
