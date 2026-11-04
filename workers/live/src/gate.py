"""Pure state transition used by the SQLite Durable Object and offline tests."""
from __future__ import annotations

import hashlib
import hmac
import math
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR

NANOS = 1_000_000_000
AUTH_WINDOW = 15 * 60
AUTH_FAILURES = 5


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
        return {"error": "auth_rate_limited", "retry_after": math.ceil(row["locked_until"] - now)}, 429
    if password_matches(data.get("password"), secret):
        return {"ok": True}, 200
    row = failures.setdefault(key, {"count": 0, "expires": now + AUTH_WINDOW})
    row["count"] += 1
    if row["count"] >= AUTH_FAILURES:
        row["locked_until"] = row["expires"] = now + AUTH_WINDOW
    return {"error": "unauthorized"}, 401


def money(value, rounding=ROUND_CEILING):
    return int((Decimal(str(value)) * NANOS).to_integral_value(rounding=rounding))


def snapshot(state, now, daily_limit, total_limit):
    today = datetime.fromtimestamp(now, timezone.utc)
    day = today.strftime("%Y-%m-%d")
    spent = state["days"].get(day, {}).get("amount_nanos", 0)
    if state["lifetime_nanos"] >= total_limit:
        state["lifetime_exhausted"] = True
    status = ("credit_exhausted" if state.get("credit_exhausted") else
              "total_budget_exhausted" if state.get("lifetime_exhausted") else
              "budget_exhausted" if spent >= daily_limit else "ready")
    return {"day": day, "daily_limit_usd": daily_limit / NANOS,
            "daily_spent_usd": spent / NANOS,
            "daily_remaining_usd": max(0, daily_limit - spent) / NANOS,
            "resets_at": (today.replace(hour=0, minute=0, second=0, microsecond=0)
                          + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": status}


def prune(state: dict, now: float):
    state["auth_failures"] = {k: v for k, v in state.get("auth_failures", {}).items() if v["expires"] > now}
    state["rates"] = {k: v for k, v in state.get("rates", {}).items() if v["expires"] > now}
    state["holds"] = {k: v for k, v in state.get("holds", {}).items() if v["expires"] > now}
    state["days"] = {k: v for k, v in state.get("days", {}).items() if v["expires"] > now}


def transition(state: dict, action: str, data: dict, *, now: float, budget: str,
               total_budget: str = "20", reset_id: str = "", password_secret: str = "") -> tuple[dict, int]:
    # Authentication cannot reserve, reconcile, reset or inspect spending.
    if action == "authenticate":
        return authenticate(state, data, now, password_secret)
    # Adopt all retained spending from the v1 ledger before pruning old days.
    # Lifetime spend and stop flags never expire, even when alarms prune holds.
    for row in state.get("days", {}).values():
        row.setdefault("amount_nanos", money(row["amount"]))
    state.setdefault("lifetime_nanos", sum(r["amount_nanos"] for r in state.get("days", {}).values()))
    prune(state, now)
    if reset_id and reset_id != state.get("admin_reset_id"):
        # Only a deployment setting supplies this identifier. Public request
        # bodies cannot reset the ledger. Keep in-flight holds and today's spend.
        state["lifetime_nanos"] = sum(h.get("amount_nanos", money(h["amount"]))
                                      for h in state["holds"].values() if not h["settled"])
        state.pop("credit_exhausted", None)
        state.pop("lifetime_exhausted", None)
        state["admin_reset_id"] = reset_id
    if action == "credit_exhausted":
        state["credit_exhausted"] = True
        return {"ok": True}, 200
    try:
        limits = [Decimal(str(v)) for v in (budget, total_budget)]
        if any(not v.is_finite() or v < 0 for v in limits):
            raise ValueError
        daily_limit, total_limit = [money(v, ROUND_FLOOR) for v in limits]
    except (ValueError, TypeError, InvalidOperation):
        return {"error": "unavailable"}, 503
    public = snapshot(state, now, daily_limit, total_limit)
    if action == "budget":
        return public, 200
    day = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    if action == "rate":
        if not data.get("ip"):
            return {"error": "unavailable"}, 503
        # No raw IP or user text in storage. The HMAC bucket expires after ten
        # minutes, including across UTC midnight; an alarm also erases it.
        key = ip_key(state, data["ip"])
        row = state["rates"].setdefault(key, {"count": 0, "expires": now + 600})
        if row["count"] >= 5:
            return {"error": "rate_limited", "retry_after": math.ceil(row["expires"] - now)}, 429
        row["count"] += 1
        return {"ok": True}, 200
    if action == "reserve":
        if public["status"] != "ready":
            return {"error": public["status"], "budget": public}, 429 if public["status"] == "budget_exhausted" else 503
        amount = data.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount <= 0:
            return {"error": "unavailable"}, 503
        if not isinstance(data.get("id"), str) or data["id"] in state["holds"]:
            return {"error": "unavailable"}, 503
        row = state["days"].setdefault(day, {"amount": 0.0, "expires": now + 172800})
        # Integer nano-USD, rounded up for holds / down for the configured cap.
        # Floating-point accumulation must never create extra spending room.
        spent = row.setdefault("amount_nanos", money(row["amount"]))
        nanos = money(amount)
        if state["lifetime_nanos"] + nanos > total_limit:
            state["lifetime_exhausted"] = True
            return {"error": "total_budget_exhausted",
                    "budget": snapshot(state, now, daily_limit, total_limit)}, 503
        if spent + nanos > daily_limit:
            return {"error": "budget_exhausted", "budget": public}, 429
        row["amount_nanos"] = spent + nanos
        row["amount"] = row["amount_nanos"] / NANOS
        state["lifetime_nanos"] += nanos
        if state["lifetime_nanos"] >= total_limit:
            state["lifetime_exhausted"] = True
        state["holds"][data["id"]] = {"day": day, "amount": amount, "amount_nanos": nanos,
                                     "settled": False, "expires": now + 172800}
        row["expires"] = max(row["expires"], now + 172800)
        return {"ok": True}, 200
    if action == "settle":
        hold = state["holds"].get(data.get("id"))
        if not hold:
            return {"error": "unavailable"}, 503
        if hold["settled"]:
            return {"ok": True}, 200  # idempotent; never refund twice
        amount = data.get("amount")
        if amount is None:
            amount = hold["amount"]  # timeout / absent usage keeps the entire hold
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount < 0:
            amount = hold["amount"]
        row = state["days"][hold["day"]]
        spent = row.setdefault("amount_nanos", money(row["amount"]))
        reserved = hold.get("amount_nanos", money(hold["amount"]))
        delta = money(amount) - reserved
        row["amount_nanos"] = spent + delta
        state["lifetime_nanos"] += delta
        if amount > hold["amount"]:
            # Unexpected usage or a changed provider contract fails closed.
            row["amount_nanos"] = max(row["amount_nanos"], daily_limit)
            state["lifetime_exhausted"] = True
        if state["lifetime_nanos"] >= total_limit:
            state["lifetime_exhausted"] = True
        row["amount"] = row["amount_nanos"] / NANOS
        hold["settled"] = True
        return {"ok": True}, 200
    return {"error": "unavailable"}, 503
