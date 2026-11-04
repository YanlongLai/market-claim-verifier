"""Pure state transition used by the SQLite Durable Object and offline tests."""
from __future__ import annotations

import hashlib
import hmac
import math
import secrets
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR

NANOS = 1_000_000_000
AUTH_WINDOW = 15 * 60
AUTH_FAILURES = 5
AUTH_LOCKOUT = 30 * 60
PROVIDERS = ("baseten", "fireworks", "meta")


def password_matches(value, secret):
    # Always compare fixed-size digests, including for missing/non-string input.
    attempted = value.encode("utf-8", errors="surrogatepass") if isinstance(value, str) else b""
    return hmac.compare_digest(hashlib.sha256(attempted).digest(),
                               hashlib.sha256(secret.encode("utf-8")).digest())


def ip_key(state, ip):
    if "salt" not in state:
        state["salt"] = secrets.token_hex(32)
    return hmac.new(state["salt"].encode(), str(ip).encode(), hashlib.sha256).hexdigest()


def authenticate(state, data, now, secret):
    if not isinstance(secret, str) or not secret:
        return {"error": "unavailable"}, 503
    if not data.get("ip"):
        return {"error": "unavailable"}, 503
    # Only expiring counts/timestamps and a salted IP bucket enter storage.
    # Neither the password nor its digest is retained or logged.
    failures = state["auth_failures"] = {
        key: row for key, row in state.get("auth_failures", {}).items() if row["expires"] > now}
    key = ip_key(state, data["ip"])
    row = failures.get(key)
    if row and row.get("locked_until", 0) > now:
        return {"error": "locked", "retry_after": math.ceil(row["locked_until"] - now)}, 429
    if password_matches(data.get("password"), secret):
        return {"ok": True}, 200
    row = failures.setdefault(key, {"count": 0, "times": [], "expires": now + AUTH_WINDOW})
    # Rolling window; retain old-format counters conservatively until expiry.
    times = [t for t in row.get("times", [now] * row["count"]) if t > now - AUTH_WINDOW]
    times.append(now)
    row.update(times=times, count=len(times), expires=now + AUTH_WINDOW)
    if row["count"] >= AUTH_FAILURES:
        row["locked_until"] = row["expires"] = now + AUTH_LOCKOUT
        return {"error": "locked", "retry_after": AUTH_LOCKOUT}, 429
    return {"error": "unauthorized"}, 401


def money(value, rounding=ROUND_CEILING):
    return int((Decimal(str(value)) * NANOS).to_integral_value(rounding=rounding))


def snapshot(state, now, daily_limit, total_limit):
    today = datetime.fromtimestamp(now, timezone.utc)
    day = today.strftime("%Y-%m-%d")
    row = state["days"].get(day, {})
    spent = row.get("amount_nanos", 0)
    if state["lifetime_nanos"] >= total_limit:
        state["lifetime_exhausted"] = True
    status = ("credit_exhausted" if state.get("credit_exhausted") else
              "total_budget_exhausted" if state.get("lifetime_exhausted") else
              "budget_exhausted" if spent >= daily_limit or row.get("daily_exhausted") else "ready")
    return {"daily_limit": daily_limit / NANOS, "daily_spent": spent / NANOS,
            "daily_remaining": max(0, daily_limit - spent) / NANOS,
            "lifetime_limit": total_limit / NANOS, "lifetime_spent": state["lifetime_nanos"] / NANOS,
            "lifetime_remaining": max(0, total_limit - state["lifetime_nanos"]) / NANOS,
            "status": status}


def migrate(state):
    """Upgrade in place without forgiving spending or deleting recorded rows.

    V1 recorded no provider on holds or lifetime totals. Its unattributable
    spending and stops conservatively count against *each* provider. Never infer
    a lifetime split from the public history, which expires after fourteen days
    and cannot account for every in-flight/failed call. The original aggregate
    stays intact as a separate sum guard and migration evidence.
    """
    for group in ("days", "holds", "rates"):
        state.setdefault(group, {})
    for row in state["days"].values():
        if "amount_nanos" not in row:
            row["amount_nanos"] = money(row["amount"])
    state.setdefault("lifetime_nanos", sum(r["amount_nanos"] for r in state["days"].values()))
    if "providers" not in state:
        legacy = {key: deepcopy(state[key]) for key in
                  ("days", "lifetime_nanos", "credit_exhausted", "lifetime_exhausted") if key in state}
        state["providers"] = {name: deepcopy(legacy) for name in PROVIDERS}
        for hold in state["holds"].values():
            hold["providers"] = list(PROVIDERS)
        state["provider_migration"] = {"version": 2, "legacy_lifetime_nanos": state["lifetime_nanos"],
                                       "allocation": "conservative_all_providers"}


def prune(state: dict, now: float):
    # Migration must precede expiry, including alarm/idle cleanup of a v1 DB.
    migrate(state)
    state["auth_failures"] = {k: v for k, v in state.get("auth_failures", {}).items() if v["expires"] > now}
    state["bursts"] = {k: v for k, v in state.get("bursts", {}).items() if v["expires"] > now}
    state["site_runs"] = [t for t in state.get("site_runs", []) if t > now - 600]
    state["rates"] = {k: v for k, v in state.get("rates", {}).items() if v["expires"] > now}
    state["holds"] = {k: v for k, v in state.get("holds", {}).items() if v["expires"] > now}
    state["days"] = {k: v for k, v in state.get("days", {}).items() if v["expires"] > now}
    for provider in state["providers"].values():
        provider["days"] = {k: v for k, v in provider["days"].items() if v["expires"] > now}


def public_budget(state, now, limits):
    global_budget = snapshot(state, now, *limits["global"])
    providers = {name: snapshot(state["providers"][name], now, *limits[name]) for name in PROVIDERS}
    if global_budget["status"] != "ready":
        for provider in providers.values():
            if provider["status"] == "ready":
                provider["status"] = global_budget["status"]
    statuses = {row["status"] for row in providers.values()}
    status = (global_budget["status"] if global_budget["status"] != "ready" else
              "ready" if "ready" in statuses else
              next(s for s in ("credit_exhausted", "total_budget_exhausted", "budget_exhausted") if s in statuses))
    today = datetime.fromtimestamp(now, timezone.utc)
    return {"day": today.strftime("%Y-%m-%d"), "providers": providers, "status": status,
            # One-release compatibility: the old counters are provider sums.
            **{key + "_usd": round(sum(row[key] for row in providers.values()), 9)
               for key in ("daily_limit", "daily_spent", "daily_remaining",
                           "lifetime_limit", "lifetime_spent", "lifetime_remaining")},
            "global": global_budget,
            "resets_at": (today.replace(hour=0, minute=0, second=0, microsecond=0)
                          + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}


def transition(state: dict, action: str, data: dict, *, now: float, budget: str,
               total_budget: str = "20", provider_budgets: dict | None = None,
               reset_id: str = "", password_secret: str = "") -> tuple[dict, int]:
    # Authentication cannot reserve, reconcile, reset or inspect spending.
    if action == "authenticate":
        return authenticate(state, data, now, password_secret)
    prune(state, now)
    if reset_id and reset_id != state.get("admin_reset_id"):
        # Only a deployment setting supplies this identifier. Public request
        # bodies cannot reset the ledger. Keep in-flight holds and today's spend.
        state["lifetime_nanos"] = sum(h.get("amount_nanos", money(h["amount"]))
                                      for h in state["holds"].values() if not h["settled"])
        state.pop("credit_exhausted", None)
        state.pop("lifetime_exhausted", None)
        for name, provider in state["providers"].items():
            provider["lifetime_nanos"] = sum(h.get("amount_nanos", money(h["amount"]))
                for h in state["holds"].values() if not h["settled"] and name in h["providers"])
            provider.pop("credit_exhausted", None)
            provider.pop("lifetime_exhausted", None)
        state["admin_reset_id"] = reset_id
    if action == "credit_exhausted":
        name = data.get("provider")
        if name is not None and name not in PROVIDERS:
            return {"error": "unavailable"}, 503
        target = state if name is None else state["providers"][name]
        target["credit_exhausted"] = True
        return {"ok": True}, 200
    try:
        configured = {"global": (budget, total_budget),
                      **{name: (provider_budgets or {}).get(name, ("30", "20")) for name in PROVIDERS}}
        limits = {}
        for name, pair in configured.items():
            values = [Decimal(str(v)) for v in pair]
            if len(values) != 2 or any(not v.is_finite() or v < 0 for v in values):
                raise ValueError
            limits[name] = tuple(money(v, ROUND_FLOOR) for v in values)
    except (ValueError, TypeError, InvalidOperation, OverflowError):
        return {"error": "unavailable"}, 503
    public = public_budget(state, now, limits)
    if action == "budget":
        return public, 200
    day = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    if action == "burst":
        if not data.get("ip"):
            return {"error": "unavailable"}, 503
        key = ip_key(state, data["ip"])
        row = state["bursts"].setdefault(key, {"times": [], "expires": now + 60})
        if row.get("blocked_until", 0) > now:
            return {"error": "slow_down"}, 429
        row["times"] = [t for t in row["times"] if t > now - 60]
        row["times"].append(now)
        row["expires"] = now + 60
        if len(row["times"]) > 30:
            row["blocked_until"] = row["expires"] = now + 600
            return {"error": "slow_down"}, 429
        return {"ok": True}, 200
    if action == "rate":
        if not data.get("ip"):
            return {"error": "unavailable"}, 503
        # No raw IP or user text in storage. The HMAC bucket expires after ten
        # minutes, including across UTC midnight; an alarm also erases it.
        key = ip_key(state, data["ip"])
        row = state["rates"].setdefault(key, {"count": 0, "expires": now + 600})
        if row["count"] >= 5:
            return {"error": "rate_limited", "retry_after": math.ceil(row["expires"] - now)}, 429
        if len(state["site_runs"]) >= 20:
            return {"error": "busy"}, 429
        row["count"] += 1
        state["site_runs"].append(now)
        return {"ok": True}, 200
    if action == "reserve":
        name = data.get("provider", "baseten")
        if name not in PROVIDERS:
            return {"error": "unavailable"}, 503
        status = public["providers"][name]["status"]
        if status != "ready":
            return {"error": status, "budget": public}, 429 if status == "budget_exhausted" else 503
        amount = data.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount <= 0:
            return {"error": "unavailable"}, 503
        if not isinstance(data.get("id"), str) or data["id"] in state["holds"]:
            return {"error": "unavailable"}, 503
        # Integer nano-USD, rounded up for holds / down for the configured cap.
        # Floating-point accumulation must never create extra spending room.
        nanos = money(amount)
        scopes = ((state["providers"][name], limits[name]), (state, limits["global"]))
        # Check both scopes before changing either: a rejected hold spends zero.
        for scope, (daily_limit, total_limit) in scopes:
            spent = scope["days"].get(day, {}).get("amount_nanos", 0)
            if scope["lifetime_nanos"] + nanos > total_limit:
                scope["lifetime_exhausted"] = True
                return {"error": "total_budget_exhausted", "budget": public_budget(state, now, limits)}, 503
            if spent + nanos > daily_limit:
                if scope is not state:
                    # No more calls on this provider today when its next hold
                    # cannot fit. Keep the true spend; the pause resets at UTC
                    # midnight. A global rejection can still leave room for a
                    # cheaper comparison member on another provider.
                    row = scope["days"].setdefault(day, {"amount": 0.0, "amount_nanos": 0, "expires": now + 172800})
                    row["daily_exhausted"] = True
                return {"error": "budget_exhausted", "budget": public_budget(state, now, limits)}, 429
        for scope, (_, total_limit) in scopes:
            row = scope["days"].setdefault(day, {"amount_nanos": 0, "expires": now + 172800})
            row["amount_nanos"] += nanos
            row["amount"] = row["amount_nanos"] / NANOS
            row["expires"] = max(row["expires"], now + 172800)
            scope["lifetime_nanos"] += nanos
            if scope["lifetime_nanos"] >= total_limit:
                scope["lifetime_exhausted"] = True
        state["holds"][data["id"]] = {"day": day, "amount": amount, "amount_nanos": nanos,
                                     "providers": [name],
                                     "settled": False, "expires": now + 172800}
        return {"ok": True}, 200
    if action == "settle":
        hold = state["holds"].get(data.get("id"))
        if not hold:
            return {"error": "unavailable"}, 503
        if "provider" in data and data["provider"] not in hold["providers"]:
            return {"error": "unavailable"}, 503
        if hold["settled"]:
            return {"ok": True}, 200  # idempotent; never refund twice
        amount = data.get("amount")
        if amount is None:
            amount = hold["amount"]  # timeout / absent usage keeps the entire hold
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount < 0:
            amount = hold["amount"]
        reserved = hold.get("amount_nanos", money(hold["amount"]))
        delta = money(amount) - reserved
        for name in [*hold["providers"], "global"]:
            scope = state if name == "global" else state["providers"][name]
            row = scope["days"][hold["day"]]
            total_limit = limits[name][1]
            row["amount_nanos"] += delta
            scope["lifetime_nanos"] += delta
            # The affected provider fails closed; other providers can still
            # run unless the actual aggregate spend reaches the sum guard.
            if amount > hold["amount"] and name != "global":
                scope["lifetime_exhausted"] = True
            if scope["lifetime_nanos"] >= total_limit:
                scope["lifetime_exhausted"] = True
            row["amount"] = row["amount_nanos"] / NANOS
        hold["settled"] = True
        return {"ok": True}, 200
    return {"error": "unavailable"}, 503
