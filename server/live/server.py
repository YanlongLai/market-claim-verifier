"""Single-process HTTP adapter for the unchanged live runner and spend gate."""
from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from urllib.parse import urlparse

from aiohttp import web
import httpx

from workers.live.src.gate import prune, transition
from workers.live.src.live import ExampleRun, LiveError, LiveRun, SEC_AGENT, provider_credit_exhausted, validate_text

GATE_LOCK = asyncio.Lock()  # One process, one critical section, including pruning.
TTL = 6 * 60 * 60
EXAMPLE_TIMEOUT = 60
EXAMPLES = {"text": "post.txt", "image": "post.png", "pdf": "post.pdf", "audio": "post.mp3", "video": "post.mp4"}


def secret(env, name):
    if name in env:
        return env[name]
    filename = env.get(name + "_FILE")
    return Path(filename).read_text().rstrip("\r\n") if filename else ""


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("/data")
    api_key: str = ""
    password: str = ""
    origin_token: str = ""
    daily_budget: str = "3"
    total_budget: str = "20"
    meta_api_key: str = ""
    examples_dir: Path = Path("/app/examples")

    @classmethod
    def from_env(cls):
        env = os.environ
        return cls(Path(env.get("LIVE_DATA_DIR", "/data")), secret(env, "BASETEN_API_KEY"),
                   secret(env, "LIVE_CHECK_PASSWORD"), secret(env, "LIVE_ORIGIN_TOKEN"),
                   env.get("DAILY_BUDGET_USD", "3"), env.get("TOTAL_BUDGET_USD", "20"),
                   secret(env, "META_MODEL_API_KEY"), Path(env.get("LIVE_EXAMPLES_DIR", "/app/examples")))


def load_example(folder, example_id):
    """Only the five packaged, hash-checked inputs; never accept a visitor path."""
    if not isinstance(example_id, str) or example_id not in EXAMPLES:
        raise LiveError("unknown_example", 400)
    try:
        rows = json.loads((folder / "manifest.json").read_text())
        row = next(row for row in rows if row["id"] == example_id)
        if row["kind"] != example_id or row["status"] != "ready" or row["file"] != EXAMPLES[example_id]:
            raise ValueError
        path = folder / row["file"]
        if path.is_symlink() or not 0 < path.stat().st_size <= 2_000_000 or row["size_bytes"] != path.stat().st_size:
            raise ValueError
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError
        return path, row["kind"]
    except (OSError, ValueError, TypeError, KeyError, StopIteration):
        raise LiveError("example_unavailable") from None


class SpendGate:
    def __init__(self, settings, clock=time.time):
        self.settings, self.clock = settings, clock
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(settings.data_dir / "ledger.sqlite3", isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY CHECK (id = 1), body TEXT NOT NULL)")

    async def update(self, action, data=None):
        async with GATE_LOCK:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT body FROM ledger WHERE id = 1").fetchone()
                state = json.loads(row[0]) if row else {}
                if action == "prune":
                    prune(state, self.clock())
                    result, status = {"ok": True}, 200
                else:
                    result, status = transition(state, action, data, now=self.clock(),
                                                budget=self.settings.daily_budget,
                                                total_budget=self.settings.total_budget,
                                                password_secret=self.settings.password)
                # No reset_id: lifetime counters and stop flags are never reset.
                self.db.execute("INSERT OR REPLACE INTO ledger (id, body) VALUES (1, ?)", (json.dumps(state),))
                self.db.execute("COMMIT")
            except BaseException:
                self.db.execute("ROLLBACK")
                raise
        if status != 200:
            raise LiveError(result.get("error", "unavailable"), status, result.get("budget"))
        return result

    def close(self):
        self.db.close()


class Services:
    def __init__(self, settings, client, clock=time.time):
        self.settings, self.client, self.clock = settings, client, clock
        self.ledger = SpendGate(settings, clock)
        self.cache_dir = settings.data_dir / "sec-cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache = {}

    async def gate(self, action, data):
        return await self.ledger.update(action, data)

    async def sec(self, url):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc not in {"www.sec.gov", "data.sec.gov"}:
            raise LiveError("sec_unavailable")
        now = self.clock()
        hit = self.cache.get(url)
        if hit and hit[0] > now:
            return hit[1]
        path = self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        try:
            expires = path.stat().st_mtime + TTL
            if expires > now:
                body = path.read_text()
                json.loads(body)
                self.cache[url] = (expires, body)
                return body
        except (OSError, ValueError):
            pass
        try:
            async with asyncio.timeout(22):
                async with self.client.stream("GET", url, headers={"User-Agent": SEC_AGENT,
                                               "Accept": "application/json"},
                                               follow_redirects=False, timeout=22) as response:
                    if not response.is_success:
                        raise LiveError("sec_unavailable")
                    body = (await response.aread()).decode("utf-8")
                    json.loads(body)  # Never cache HTML errors or redirects.
            # Atomic cache replacement; only validated JSON bodies enter disk.
            fd, tmp = tempfile.mkstemp(dir=self.cache_dir)
            try:
                with os.fdopen(fd, "w") as output:
                    output.write(body)
                os.replace(tmp, path)
            finally:
                with suppress(FileNotFoundError):
                    os.unlink(tmp)
            self.cache[url] = (self.clock() + TTL, body)
            return body
        except (httpx.HTTPError, TimeoutError, ValueError, OSError):
            raise LiveError("sec_unavailable") from None

    async def model(self, payload):
        try:
            async with asyncio.timeout(22):
                async with self.client.stream("POST", "https://inference.baseten.co/v1/chat/completions",
                                               headers={"Authorization": "Bearer " + self.settings.api_key,
                                                        "Content-Type": "application/json"},
                                               content=json.dumps(payload), follow_redirects=False,
                                               timeout=22) as response:
                    if not response.is_success:
                        # Latch 402 before reading a possibly broken/private body.
                        body = "" if response.status_code == 402 else (await response.aread()).decode("utf-8", errors="replace")
                        if provider_credit_exhausted(response.status_code, body):
                            await self.gate("credit_exhausted", {})
                            raise LiveError("credit_exhausted")
                        raise LiveError("provider_error")
                    return json.loads(await response.aread())
        except (httpx.HTTPError, TimeoutError, ValueError):
            raise LiveError("provider_error") from None

    async def media(self, operation, payload, audio=None):
        """Meta Model API only for OCR/ASR, with no automatic retries."""
        from claimcheck.providers import META_BASE_URL
        options = ({"json": payload} if operation == "ocr" else {"files": {
            "request": (None, json.dumps(payload), "application/json"), "audio": ("audio.wav", audio, "audio/wav")}})
        try:
            async with self.client.stream("POST", META_BASE_URL + ("/responses" if operation == "ocr" else "/asr/transcribe"),
                    headers={"Authorization": "Bearer " + self.settings.meta_api_key, "Accept": "application/json"},
                    **options, follow_redirects=False, timeout=50) as response:
                if not response.is_success:
                    body = "" if response.status_code == 402 else (await response.aread()).decode("utf-8", errors="replace")
                    if provider_credit_exhausted(response.status_code, body):
                        await self.gate("credit_exhausted", {})
                        raise LiveError("credit_exhausted")
                    raise LiveError("preprocessing_failed")
                return json.loads(await response.aread())
        except httpx.TimeoutException:
            raise LiveError("timeout", 504) from None
        except (httpx.HTTPError, ValueError):
            raise LiveError("preprocessing_failed") from None

    async def prune(self):
        await self.ledger.update("prune")
        now = self.clock()
        self.cache = {url: hit for url, hit in self.cache.items() if hit[0] > now}
        for path in self.cache_dir.glob("*.json"):
            if path.stat().st_mtime + TTL <= now:
                path.unlink(missing_ok=True)


SERVICES = web.AppKey("services", Services)


def reply(value, status=200, *, public=False):
    return web.Response(text=json.dumps(value, ensure_ascii=False), status=status, headers={
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=0, s-maxage=5, must-revalidate" if public else "no-store",
        "X-Content-Type-Options": "nosniff"})


async def handle(request):
    services = request.app[SERVICES]
    expected = services.settings.origin_token
    supplied = request.headers.get("X-Live-Origin-Token", "")
    # Fixed-size constant-time comparison, including missing/Unicode headers.
    matches = hmac.compare_digest(hashlib.sha256(supplied.encode()).digest(),
                                 hashlib.sha256(expected.encode()).digest())
    if not supplied or not expected or not matches:
        return reply({"error": "origin_rejected", "demo": "data/live-demo.json"}, 401 if not supplied else 403)
    if request.method == "GET" and request.path in {"/api/budget", "/healthz"}:
        try:
            budget = await services.gate("budget", {})
            return reply(budget, public=True) if request.path == "/api/budget" else reply({"ok": True})
        except Exception:
            return reply({"error": "unavailable"}, 503)
    if request.method != "POST" or request.path not in {"/api/check", "/api/check-example"}:
        return reply({"error": "not_found"}, 404)
    is_example = request.path == "/api/check-example"
    limit = 1024 if is_example else 4096
    run = None
    try:
        async with asyncio.timeout(EXAMPLE_TIMEOUT if is_example else 28):
            raw = bytearray()
            async for chunk in request.content.iter_chunked(4096):
                raw.extend(chunk)
                if len(raw) > limit:
                    raise LiveError("invalid_input", 400)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (ValueError, TypeError):
                raise LiveError("invalid_input", 400) from None
            if not isinstance(data, dict):
                raise LiveError("invalid_input", 400)
            await services.gate("authenticate", {"ip": request.headers.get("X-Live-Client-IP"),
                                                  "password": data.pop("password", None)})
            if is_example:
                if set(data) != {"example_id"}:
                    raise LiveError("invalid_input", 400)
                path, kind = load_example(services.settings.examples_dir, data["example_id"])
                if kind in {"image", "audio", "video"} and not services.settings.meta_api_key:
                    raise LiveError("unavailable")
            if not services.settings.api_key:
                raise LiveError("unavailable")
            claim = None if is_example else validate_text(data.get("text"))
            budget = await services.gate("budget", {})
            if budget["status"] != "ready":
                raise LiveError(budget["status"], 429 if budget["status"] == "budget_exhausted" else 503, budget)
            await services.gate("rate", {"ip": request.headers.get("X-Live-Client-IP")})
            if is_example:
                run = ExampleRun(services.model, services.sec, services.gate, services.media, data["example_id"], kind)
                return reply(await run.check_example(path))
            run = LiveRun(services.model, services.sec, services.gate)
            return reply(await run.bounded(claim))
    except (LiveError, TimeoutError) as error:
        if isinstance(error, TimeoutError):
            error = LiveError("timeout", 504)
        return reply({**(run.envelope() if run else {}), "error": error.code, "demo": "data/live-demo.json",
                      **({"budget": error.budget} if error.budget else {})}, error.status)
    except Exception:
        # Do not log exceptions, request text, provider bodies or credentials.
        return reply({**(run.envelope() if run else {}), "error": "unavailable", "demo": "data/live-demo.json"}, 503)


def create_app(settings, *, client=None, clock=time.time):
    app = web.Application(client_max_size=4096)

    async def lifecycle(app):
        transport = client if client is not None else httpx.AsyncClient(trust_env=False)
        services = app[SERVICES] = Services(settings, transport, clock)

        async def periodic():
            while True:
                await asyncio.sleep(60)
                try:
                    await services.prune()
                except Exception:
                    # Retain the ledger on cleanup failure; never reset it.
                    pass

        task = asyncio.create_task(periodic())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            services.ledger.close()
            if client is None:
                await transport.aclose()

    app.cleanup_ctx.append(lifecycle)
    app.router.add_route("*", "/{path:.*}", handle)
    return app


if __name__ == "__main__":
    os.umask(0o077)
    try:
        settings = Settings.from_env()
    except (OSError, ValueError):
        raise SystemExit("live check configuration unavailable") from None
    web.run_app(create_app(settings), host="0.0.0.0", port=8080, access_log=None, print=None)
