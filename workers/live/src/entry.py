"""Cloudflare adapters. This Worker has no public route: Pages service binding only."""
import asyncio
import json
import time
from urllib.parse import urlparse

from js import AbortSignal, Object, Request as JSRequest, Response as JSResponse, caches, fetch
from pyodide.ffi import to_js
from workers import DurableObject, Response, WorkerEntrypoint

from gate import prune, transition
from live import LiveError, LiveRun, SEC_AGENT, provider_credit_exhausted, provider_overloaded, validate_text


def js_options(value):
    return to_js(value, dict_converter=Object.fromEntries)


def reply(value, status=200, *, public=False):
    return Response(json.dumps(value, ensure_ascii=False), status=status, headers={
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=0, s-maxage=5, must-revalidate" if public else "no-store",
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
        expiries = [v["expires"] for group in ("auth_failures", "rates", "days", "holds") for v in state.get(group, {}).values()]
        if expiries:
            await self.ctx.storage.setAlarm(int(min(expiries) * 1000))

    async def fetch(self, request):
        data = await request.json()
        # No await between read/check/write. SQLite calls are synchronous, so
        # concurrent reservations cannot interleave this critical section.
        state = self.load()
        result, status = transition(state, data["action"], data["data"], now=time.time(),
                                    budget=str(getattr(self.env, "DAILY_BUDGET_USD", "3")),
                                    total_budget=str(getattr(self.env, "TOTAL_BUDGET_USD", "20")),
                                    provider_budgets={name: (
                                        str(getattr(self.env, name.upper() + "_DAILY_BUDGET_USD", "30")),
                                        str(getattr(self.env, name.upper() + "_LIFETIME_BUDGET_USD", "20")))
                                        for name in ("baseten", "fireworks", "meta")},
                                    reset_id=str(getattr(self.env, "BUDGET_RESET_ID", "")),
                                    password_secret=getattr(self.env, "LIVE_CHECK_PASSWORD", ""))
        self.save(state)
        await self.schedule(state)
        return reply(result, status)

    async def alarm(self):
        state = self.load()
        prune(state, time.time())
        self.save(state)
        # Never erase the lifetime counter or permanent stop flags during idle
        # cleanup. Only short-lived rate buckets, days and holds are pruned.
        await self.schedule(state)


class Services:
    # Plain helper, not a WorkerEntrypoint: no model/gate RPC entry points.
    def __init__(self, env):
        self.env = env

    async def gate(self, action, data):
        # One globally named object across all Pages regions and visitors.
        stub = self.env.SPEND_GATE.get(self.env.SPEND_GATE.idFromName("baseten-live-global-v1"))
        response = await stub.fetch(JSRequest.new("https://gate.internal/", js_options({
            "method": "POST", "body": json.dumps({"action": action, "data": data}),
            "headers": {"Content-Type": "application/json"}})))
        body = json.loads(await response.text())
        if response.status != 200:
            raise LiveError(body.get("error", "unavailable"), response.status, body.get("budget"))
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
            # A 402 remains a stop even if its body cannot be read. Never send
            # provider error text (which can include account details) to Pages.
            body = "" if response.status == 402 else await response.text()
            if provider_credit_exhausted(response.status, body):
                await self.gate("credit_exhausted", {"provider": "baseten"})
                raise LiveError("credit_exhausted", provider_status=response.status)
            if provider_overloaded(response.status, body):
                raise LiveError("provider_overloaded", provider_status=response.status)
            raise LiveError("provider_error", provider_status=response.status)
        return json.loads(await response.text())

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        services = Services(self.env)
        if request.method == "GET" and urlparse(request.url).path == "/api/budget":
            try:
                return reply(await services.gate("budget", {}), public=True)
            except Exception:
                return reply({"error": "unavailable"}, 503)
        if request.method != "POST" or urlparse(request.url).path != "/api/check":
            return reply({"error": "not_found"}, 404)
        run = None
        try:
            raw = await request.text()
            if len(raw.encode()) > 4096:
                raise LiveError("invalid_input", 400)
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                raise LiveError("invalid_input", 400) from None
            if not isinstance(data, dict):
                raise LiveError("invalid_input", 400)
            await services.gate("authenticate", {"ip": request.headers.get("X-Live-Client-IP"),
                                                  "password": data.pop("password", None)})
            if not getattr(self.env, "BASETEN_API_KEY", None):
                raise LiveError("unavailable")
            claim = validate_text(data.get("text"))
            budget = await services.gate("budget", {})
            status = budget["providers"]["baseten"]["status"]
            if status != "ready":
                raise LiveError(status, 429 if status == "budget_exhausted" else 503, budget)
            await services.gate("rate", {"ip": request.headers.get("X-Live-Client-IP")})
            run = LiveRun(services.model, services.sec, services.gate)
            return reply(await run.bounded(claim))
        except LiveError as error:
            fields = run.envelope() if run else {}
            return reply({**fields, "error": error.code, "demo": "data/live-demo.json",
                          **({"budget": error.budget} if error.budget else {})}, error.status)
        except Exception:
            # Never log request text, provider bodies, credentials or exceptions.
            return reply({**(run.envelope() if run else {}), "error": "unavailable",
                          "demo": "data/live-demo.json"}, 503)
