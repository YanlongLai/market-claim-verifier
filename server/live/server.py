"""Single-process HTTP adapter, provider spend gates and bounded public history."""
from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

from aiohttp import web
import httpx

from workers.live.src.gate import prune, transition
from claimcheck.providers import get_provider
from workers.live.src.live import (ExampleRun, LiveError, LiveRun, SEC_AGENT, provider_credit_exhausted,
                                   validate_provider, validate_text)

GATE_LOCK = asyncio.Lock()  # One process, one critical section, including pruning.
TTL = 6 * 60 * 60
EXAMPLE_TIMEOUT = 60
EXAMPLES = {"text": "post.txt", "image": "post.png", "pdf": "post.pdf", "audio": "post.mp3", "video": "post.mp4"}
HISTORY_TTL = 14 * 86400
HISTORY_MAX_ROWS = 5000
HISTORY_ENVELOPE_BYTES = 64 * 1024
HISTORY_ID = re.compile(r"[0-9a-f]{32}")


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
    fireworks_api_key: str = ""
    meta_daily_budget: str = "30"
    meta_lifetime_budget: str = "20"
    baseten_daily_budget: str = "30"
    baseten_lifetime_budget: str = "20"
    fireworks_daily_budget: str = "30"
    fireworks_lifetime_budget: str = "20"

    @property
    def provider_budgets(self):
        return {name: (getattr(self, name + "_daily_budget"), getattr(self, name + "_lifetime_budget"))
                for name in ("baseten", "fireworks", "meta")}

    @classmethod
    def from_env(cls):
        env = os.environ
        return cls(Path(env.get("LIVE_DATA_DIR", "/data")), secret(env, "BASETEN_API_KEY"),
                   secret(env, "LIVE_CHECK_PASSWORD"), secret(env, "LIVE_ORIGIN_TOKEN"),
                   env.get("DAILY_BUDGET_USD", "3"), env.get("TOTAL_BUDGET_USD", "20"),
                   secret(env, "META_MODEL_API_KEY"), Path(env.get("LIVE_EXAMPLES_DIR", "/app/examples")),
                   secret(env, "FIREWORKS_API_KEY"),
                   **{name + "_" + period + "_budget": env.get(name.upper() + "_" + period.upper() + "_BUDGET_USD", default)
                      for name in ("baseten", "fireworks", "meta")
                      for period, default in (("daily", "30"), ("lifetime", "20"))})


def load_example(folder, example_id):
    """Only packaged, hash-checked inputs; IDs never become visitor paths."""
    if not isinstance(example_id, str) or not re.fullmatch(r"(?:[abc]-)?(?:text|image|pdf|audio|video)", example_id):
        raise LiveError("unknown_example", 400)
    try:
        rows = json.loads((folder / "manifest.json").read_text())
        row = next(row for row in rows if row["id"] == example_id)
        kind = row["kind"]
        story, _, suffix = example_id.partition("-")
        expected_kind = suffix if suffix else story
        filename = row["file"]
        if (kind != expected_kind or kind not in EXAMPLES or row["status"] != "ready" or
                not isinstance(filename, str) or not re.fullmatch(r"[a-zA-Z0-9_./-]{1,100}", filename) or
                Path(filename).is_absolute() or ".." in Path(filename).parts or
                Path(filename).suffix != Path(EXAMPLES[kind]).suffix):
            raise ValueError
        path = folder / filename
        if (any(parent.is_symlink() for parent in [path, *path.parents] if parent != folder.parent) or
                not path.resolve().is_relative_to(folder.resolve()) or not path.is_file() or
                not 0 < path.stat().st_size <= 2_000_000 or row["size_bytes"] != path.stat().st_size):
            raise ValueError
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError
        return path, kind
    except (OSError, ValueError, TypeError, KeyError, StopIteration):
        raise LiveError("example_unavailable") from None


def masked_ip(value, salt):
    """Retain a coarse prefix and keyed short hash, never the source address."""
    try:
        address = ipaddress.ip_address(value)
    except (ValueError, TypeError):
        return "unknown"
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    digest = hmac.new(salt, address.packed, hashlib.sha256).hexdigest()[:8]
    prefix = (".".join(str(address).split(".")[:2]) + ".*.*" if address.version == 4 else
              ":".join(address.exploded.split(":")[:2]) + ":*")
    return prefix + "#" + digest


def parse_user_agent(value):
    """Small deterministic families; versions and raw UA are never retained."""
    ua = value[:1024] if isinstance(value, str) else ""
    browser = next((name for pattern, name in (
        (r"(?:EdgA?|EdgiOS|Edge)/", "Edge"), (r"(?:OPR|Opera)/", "Opera"),
        (r"SamsungBrowser/", "Samsung Internet"), (r"(?:Firefox|FxiOS)/", "Firefox"),
        (r"(?:Chrome|CriOS|Chromium)/", "Chrome"), (r"Version/.*Safari/", "Safari"),
        (r"(?:MSIE |Trident/)", "Internet Explorer")) if re.search(pattern, ua, re.I)), "Other")
    if re.search(r"iPad|Macintosh.*Mobile/", ua, re.I):
        device = "iPadOS / tablet"
    elif re.search(r"iPhone|iPod", ua, re.I):
        device = "iOS / mobile"
    elif "Android" in ua:
        device = "Android / " + ("mobile" if "Mobile" in ua else "tablet")
    elif "CrOS" in ua:
        device = "ChromeOS / desktop"
    elif "Windows" in ua:
        device = "Windows / desktop"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        device = "macOS / desktop"
    elif "Linux" in ua:
        device = "Linux / desktop"
    else:
        device = "Unknown / unknown"
    return device, browser


def compact_json(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def retained_envelope(envelope):
    """Keep every attempt, with an explicit marker if a trace exceeds 64 KiB."""
    saved = json.loads(compact_json(envelope))
    if len(compact_json(saved).encode()) <= HISTORY_ENVELOPE_BYTES:
        return saved
    saved["history_truncated"] = True
    # Long tool traces are the usual source of excess bytes. Retain the result,
    # corrections, receipt and input before reducing the evidence/claim detail.
    for field in ("events", "evidence", "claims"):
        while saved.get(field) and len(compact_json(saved).encode()) > HISTORY_ENVELOPE_BYTES:
            saved[field].pop()
    if len(compact_json(saved).encode()) > HISTORY_ENVELOPE_BYTES:
        saved.pop("corrections", None)
        saved["input"]["text_read"] = saved["input"]["text_read"][:600]
        saved["summary"] = str(saved.get("summary", ""))[:600]
    if len(compact_json(saved).encode()) > HISTORY_ENVELOPE_BYTES:
        raise LiveError("unavailable")
    return saved


class SpendGate:
    def __init__(self, settings, clock=time.time):
        self.settings, self.clock = settings, clock
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(settings.data_dir / "ledger.sqlite3", isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY CHECK (id = 1), body TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS history (id TEXT PRIMARY KEY, created_at REAL NOT NULL, "
                        "body TEXT NOT NULL, envelope TEXT NOT NULL CHECK(length(CAST(envelope AS BLOB)) <= 65536))")
        self.db.execute("CREATE INDEX IF NOT EXISTS history_created ON history(created_at, id)")
        self.db.execute("CREATE TABLE IF NOT EXISTS history_meta (id INTEGER PRIMARY KEY CHECK(id = 1), salt TEXT NOT NULL)")
        self.db.execute("INSERT OR IGNORE INTO history_meta(id, salt) VALUES(1, ?)", (secrets.token_hex(32),))
        self.history_salt = bytes.fromhex(self.db.execute("SELECT salt FROM history_meta WHERE id = 1").fetchone()[0])

    def prune_history(self):
        self.db.execute("DELETE FROM history WHERE created_at <= ?", (self.clock() - HISTORY_TTL,))
        self.db.execute("DELETE FROM history WHERE id IN (SELECT id FROM history "
                        "ORDER BY created_at DESC, rowid DESC LIMIT -1 OFFSET ?)", (HISTORY_MAX_ROWS,))

    async def record(self, envelope, ip, user_agent):
        saved = retained_envelope(envelope)
        receipt, source = saved["receipt"], saved["input"]
        device, browser = parse_user_agent(user_agent)
        now = self.clock()
        row = {"id": uuid4().hex, "at": datetime.fromtimestamp(now, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
               "ip_masked": masked_ip(ip, self.history_salt), "device": device, "browser": browser,
               "kind": source["kind"], "example_id": source.get("example_id"), "story": source.get("story"),
               "input_text": source["text_read"][:600], "provider": receipt["provider"], "model": receipt["model"],
               "verdict": envelope.get("verdict"), "corrections_count": len(envelope.get("corrections", {}).get("edits", [])),
               "latency_ms": receipt["latency_ms"], "cost_usd": receipt["cost_usd"],
               "preprocessing_cost_usd": (receipt["preprocessing"] or {}).get("cost_usd", 0.0)}
        async with GATE_LOCK:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute("INSERT INTO history(id, created_at, body, envelope) VALUES (?, ?, ?, ?)",
                                (row["id"], now, compact_json(row), compact_json(saved)))
                self.prune_history()
                self.db.execute("COMMIT")
            except BaseException:
                self.db.execute("ROLLBACK")
                raise
        return row["id"]

    async def history(self, *, limit=50, record_id=None):
        async with GATE_LOCK:
            if record_id is not None:
                hit = self.db.execute("SELECT body, envelope FROM history WHERE id = ? AND created_at > ?",
                                      (record_id, self.clock() - HISTORY_TTL)).fetchone()
                if not hit:
                    raise LiveError("not_found", 404)
                return {**json.loads(hit[0]), "envelope": json.loads(hit[1])}
            hits = self.db.execute("SELECT body FROM history WHERE created_at > ? "
                                   "ORDER BY created_at DESC, rowid DESC LIMIT ?", (self.clock() - HISTORY_TTL, limit))
            return {"rows": [json.loads(hit[0]) for hit in hits]}

    async def update(self, action, data=None):
        async with GATE_LOCK:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT body FROM ledger WHERE id = 1").fetchone()
                state = json.loads(row[0]) if row else {}
                if action == "prune":
                    prune(state, self.clock())
                    self.prune_history()
                    result, status = {"ok": True}, 200
                else:
                    result, status = transition(state, action, data, now=self.clock(),
                                                budget=self.settings.daily_budget,
                                                total_budget=self.settings.total_budget,
                                                provider_budgets=self.settings.provider_budgets,
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

    def provider_key(self, provider):
        return {"baseten": self.settings.api_key, "fireworks": self.settings.fireworks_api_key,
                "meta": self.settings.meta_api_key}[provider]

    async def model(self, payload, *, provider="baseten"):
        adapter = get_provider(validate_provider(provider))
        try:
            async with asyncio.timeout(22):
                async with self.client.stream("POST", adapter.base_url + ("/chat/completions" if adapter.chat_completions else "/responses"),
                                               headers={"Authorization": "Bearer " + self.provider_key(provider),
                                                        "Content-Type": "application/json"},
                                               content=json.dumps(payload), follow_redirects=False,
                                               timeout=22) as response:
                    if not response.is_success:
                        # Latch 402 before reading a possibly broken/private body.
                        body = "" if response.status_code == 402 else (await response.aread()).decode("utf-8", errors="replace")
                        if provider_credit_exhausted(response.status_code, body):
                            await self.gate("credit_exhausted", {"provider": provider})
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
                        await self.gate("credit_exhausted", {"provider": "meta"})
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
    return web.Response(text=compact_json(value), status=status, headers={
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=0, s-maxage=5, must-revalidate" if public else "no-store",
        "X-Content-Type-Options": "nosniff"})


def failure_envelope(run, error):
    run.log("error", code=error.code, status=error.status, cost_usd=run.cost,
            cost_is_bound=run.cost_is_bound)
    return {**run.envelope(), "error": error.code, "demo": "data/live-demo.json",
            **({"budget": error.budget} if error.budget else {})}


async def execute(services, request, provider, *, claim=None, example=None):
    async def model(payload):
        return await services.model(payload, provider=provider)

    log_secrets = (services.settings.api_key, services.settings.fireworks_api_key,
                   services.settings.meta_api_key, services.settings.password, services.settings.origin_token)
    if example:
        example_id, path, kind = example
        run = ExampleRun(model, services.sec, services.gate, services.media, example_id, kind,
                         provider=provider, story=example_id.split("-")[0] if "-" in example_id else "a",
                         log_secrets=log_secrets)
    else:
        run = LiveRun(model, services.sec, services.gate, provider=provider, log_secrets=log_secrets)
        run.input_info["text_read"] = claim
    run.log_start(len(claim) if claim is not None else 0)
    status = 200
    try:
        async with asyncio.timeout(EXAMPLE_TIMEOUT if example else 55):
            # Check this member's provider and any paid Meta preprocessing.
            # Each external paid call still requires an atomic reservation.
            budget = await services.gate("budget", {})
            needed = [provider, "meta"] if example and example[2] in {"image", "audio", "video"} else [provider]
            for name in needed:
                budget_status = budget["providers"][name]["status"]
                if budget_status != "ready":
                    raise LiveError(budget_status, 429 if budget_status == "budget_exhausted" else 503, budget)
            if not services.provider_key(provider) or (example and example[2] in {"image", "audio", "video"}
                                                       and not services.settings.meta_api_key):
                raise LiveError("unavailable")
            await services.gate("rate", {"ip": request.headers.get("X-Live-Client-IP")})
            result = await run.check_example(example[1]) if example else await run.bounded(claim)
    except (LiveError, TimeoutError) as error:
        if isinstance(error, TimeoutError):
            error = LiveError("timeout", 504)
        result, status = failure_envelope(run, error), error.status
    except Exception:
        result, status = failure_envelope(run, LiveError("unavailable")), 503
    # Authentication and input validation have succeeded. Retain failed and
    # partial attempts too; neither the password nor raw visitor metadata enter
    # the runner, ledger, envelope or history table.
    await services.ledger.record(result, request.headers.get("X-Live-Client-IP"), request.headers.get("User-Agent", ""))
    return result, status


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
    if request.method == "GET" and (request.path == "/api/history" or request.path.startswith("/api/history/")):
        try:
            if request.path == "/api/history":
                if (set(request.query) - {"limit"} or len(request.query.getall("limit", [])) > 1 or
                        not re.fullmatch(r"[1-9][0-9]?", request.query.get("limit", "50"))):
                    raise LiveError("invalid_input", 400)
                limit = int(request.query.get("limit", "50"))
                if limit > 50:
                    raise LiveError("invalid_input", 400)
                return reply(await services.ledger.history(limit=limit))
            record_id = request.path.removeprefix("/api/history/")
            if not HISTORY_ID.fullmatch(record_id) or request.query:
                raise LiveError("invalid_input", 400)
            return reply(await services.ledger.history(record_id=record_id))
        except LiveError as error:
            return reply({"error": error.code}, error.status)
        except Exception:
            return reply({"error": "unavailable"}, 503)
    if request.method != "POST" or request.path not in {"/api/check", "/api/check-example", "/api/compare"}:
        return reply({"error": "not_found"}, 404)
    fallback = LiveRun(services.model, services.sec, services.gate)
    try:
        async with asyncio.timeout(55):
            if request.content_type != "application/json" or request.query:
                raise LiveError("invalid_input", 400)
            raw = bytearray()
            async for chunk in request.content.iter_chunked(1024):
                raw.extend(chunk)
                if len(raw) > 1024:
                    raise LiveError("invalid_input", 400)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (ValueError, TypeError):
                raise LiveError("invalid_input", 400) from None
            if not isinstance(data, dict):
                raise LiveError("invalid_input", 400)
            await services.gate("authenticate", {"ip": request.headers.get("X-Live-Client-IP"),
                                                  "password": data.pop("password", None)})
            compare = request.path == "/api/compare"
            is_example = request.path == "/api/check-example" or (compare and "example_id" in data)
            key = "example_id" if is_example else "text"
            if not {key} <= set(data) <= {key, "providers" if compare else "provider"}:
                raise LiveError("invalid_input", 400)
            if compare:
                providers = data.get("providers")
                if not isinstance(providers, list) or not 2 <= len(providers) <= 3:
                    raise LiveError("invalid_input", 400)
                providers = [validate_provider(value) for value in providers]
                if len(set(providers)) != len(providers):
                    raise LiveError("invalid_input", 400)
            else:
                providers = [validate_provider(data.get("provider", "baseten"))]
            example = None
            if is_example:
                path, kind = load_example(services.settings.examples_dir, data["example_id"])
                example = (data["example_id"], path, kind)
            claim = None if is_example else validate_text(data.get("text"))
        runs = []
        for provider in providers:
            result, status = await execute(services, request, provider, claim=claim, example=example)
            if not compare:
                return reply(result, status)
            runs.append(result)
            if result.get("error") == "rate_limited":
                break
        return reply({"runs": runs})
    except (LiveError, TimeoutError) as error:
        if isinstance(error, TimeoutError):
            error = LiveError("timeout", 504)
        return reply(failure_envelope(fallback, error), error.status)
    except Exception:
        # Do not log exceptions, request text, provider bodies or credentials.
        return reply(failure_envelope(fallback, LiveError("unavailable")), 503)


def create_app(settings, *, client=None, clock=time.time):
    app = web.Application(client_max_size=1024)

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
    logger = logging.getLogger("claimcheck.live")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    logger.propagate = False
    try:
        settings = Settings.from_env()
    except (OSError, ValueError):
        raise SystemExit("live check configuration unavailable") from None
    web.run_app(create_app(settings), host="0.0.0.0", port=8080, access_log=None, print=None,
                shutdown_timeout=195)
