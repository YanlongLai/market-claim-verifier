"""Cloudflare adapters. This Worker has no public route: Pages service binding only."""
import asyncio
import json
import time
from urllib.parse import urlparse

from js import AbortSignal, Object, Request as JSRequest, Response as JSResponse, caches, fetch
from pyodide.ffi import to_js
from workers import DurableObject, Response, WorkerEntrypoint

from gate import prune, transition
from live import LiveError, LiveRun, SEC_AGENT, validate_text


def js_options(value):
    return to_js(value, dict_converter=Object.fromEntries)


def reply(value, status=200):
    return Response(json.dumps(value, ensure_ascii=False), status=status, headers={
        "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff"})


async def outbound(url, **options):
    # Abort the network operation too, rather than only timing out its awaiter.
    options["signal"] = AbortSignal.timeout(22000)
    return await fetch(url, js_options(options))


class SpendGate(DurableObject):
    def load(self):
        sql = self.ctx.storage.sql
        sql.exec("CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
        rows = sql.exec("SELECT body FROM ledger WHERE id = 1").toArray()
        return json.loads(rows[0].body) if len(rows) else {}

    def save(self, state):
        self.ctx.storage.sql.exec("INSERT OR REPLACE INTO ledger (id, body) VALUES (1, ?)", json.dumps(state))

    async def schedule(self, state):
        expiries = [v["expires"] for group in ("rates", "days", "holds") for v in state.get(group, {}).values()]
        if expiries:
            await self.ctx.storage.setAlarm(int(min(expiries) * 1000))

    async def fetch(self, request):
        data = await request.json()
        # No await between read/check/write. SQLite calls are synchronous, so
        # concurrent reservations cannot interleave this critical section.
        state = self.load()
        result, status = transition(state, data["action"], data["data"], now=time.time(),
                                    budget=str(getattr(self.env, "DAILY_BUDGET_USD", "3")))
        self.save(state)
        await self.schedule(state)
        return reply(result, status)

    async def alarm(self):
        state = self.load()
        prune(state, time.time())
        self.save(state)
        if state.get("rates") or state.get("holds") or state.get("days"):
            await self.schedule(state)
        else:
            self.ctx.storage.sql.exec("DELETE FROM ledger")


class Default(WorkerEntrypoint):
    async def gate(self, action, data):
        # One globally named object across all Pages regions and visitors.
        stub = self.env.SPEND_GATE.get(self.env.SPEND_GATE.idFromName("baseten-live-global-v1"))
        response = await stub.fetch(JSRequest.new("https://gate.internal/", js_options({
            "method": "POST", "body": json.dumps({"action": action, "data": data}),
            "headers": {"Content-Type": "application/json"}})))
        body = json.loads(await response.text())
        if response.status != 200:
            raise LiveError(body.get("error", "unavailable"), response.status)
        return body

    async def sec(self, url):
        parsed = urlparse(url)
        if parsed.netloc not in {"www.sec.gov", "data.sec.gov"}:
            raise LiveError("sec_unavailable")
        cache = getattr(caches, "default")
        key = JSRequest.new(url)
        hit = await cache.match(key)
        if hit:
            return await hit.text()
        response = await outbound(url, headers={"User-Agent": SEC_AGENT, "Accept": "application/json"}, redirect="error")
        if not response.ok:
            raise LiveError("sec_unavailable")
        body = await response.text()
        json.loads(body)  # don't cache an HTML error response
        await cache.put(key, JSResponse.new(body, js_options({"headers": {
            "Content-Type": "application/json", "Cache-Control": "public, max-age=21600"}})))
        return body

    async def model(self, payload):
        response = await outbound("https://inference.baseten.co/v1/chat/completions", method="POST",
                                  headers={"Authorization": "Bearer " + self.env.BASETEN_API_KEY,
                                           "Content-Type": "application/json"},
                                  body=json.dumps(payload), redirect="error")
        if not response.ok:
            raise LiveError("provider_error")
        return json.loads(await response.text())

    async def fetch(self, request):
        if request.method != "POST" or urlparse(request.url).path != "/api/check":
            return reply({"error": "not_found"}, 404)
        run = None
        try:
            if not getattr(self.env, "BASETEN_API_KEY", None):
                raise LiveError("unavailable")
            raw = await request.text()
            if len(raw.encode()) > 4096:
                raise LiveError("invalid_input", 400)
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                raise LiveError("invalid_input", 400) from None
            claim = validate_text(data.get("text") if isinstance(data, dict) else None)
            await self.gate("rate", {"ip": request.headers.get("X-Live-Client-IP")})
            run = LiveRun(self.model, self.sec, self.gate)
            return reply(await run.bounded(claim))
        except LiveError as error:
            fields = run.envelope() if run else {}
            return reply({**fields, "error": error.code, "demo": "data/live-demo.json"}, error.status)
        except Exception:
            # Never log request text, provider bodies, credentials or exceptions.
            return reply({**(run.envelope() if run else {}), "error": "unavailable",
                          "demo": "data/live-demo.json"}, 503)
