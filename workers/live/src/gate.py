"""Pure state transition used by the SQLite Durable Object and offline tests."""
from __future__ import annotations

import hashlib
import hmac
import math
import secrets
from datetime import datetime, timezone


def prune(state: dict, now: float):
    state["rates"] = {k: v for k, v in state.get("rates", {}).items() if v["expires"] > now}
    state["holds"] = {k: v for k, v in state.get("holds", {}).items() if v["expires"] > now}
    state["days"] = {k: v for k, v in state.get("days", {}).items() if v["expires"] > now}


def transition(state: dict, action: str, data: dict, *, now: float, budget: str) -> tuple[dict, int]:
    prune(state, now)
    try:
        limit = float(budget)
        if not math.isfinite(limit) or limit < 0:
            raise ValueError
    except (ValueError, TypeError):
        return {"error": "unavailable"}, 503
    day = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    if action == "rate":
        if not data.get("ip"):
            return {"error": "unavailable"}, 503
        # No raw IP or user text in storage. The HMAC bucket expires after ten
        # minutes, including across UTC midnight; an alarm also erases it.
        if "salt" not in state:
            state["salt"] = secrets.token_hex(32)
        key = hmac.new(state["salt"].encode(), str(data["ip"]).encode(), hashlib.sha256).hexdigest()
        row = state["rates"].setdefault(key, {"count": 0, "expires": now + 600})
        if row["count"] >= 5:
            return {"error": "rate_limited", "retry_after": math.ceil(row["expires"] - now)}, 429
        row["count"] += 1
        return {"ok": True}, 200
    if action == "reserve":
        amount = data.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount <= 0:
            return {"error": "unavailable"}, 503
        if not isinstance(data.get("id"), str) or data["id"] in state["holds"]:
            return {"error": "unavailable"}, 503
        row = state["days"].setdefault(day, {"amount": 0.0, "expires": now + 172800})
        # Integer nano-USD, rounded up for holds / down for the configured cap.
        # Floating-point accumulation must never create extra spending room.
        spent = row.setdefault("amount_nanos", math.ceil(row["amount"] * 1_000_000_000))
        nanos = math.ceil(amount * 1_000_000_000)
        if spent + nanos > math.floor(limit * 1_000_000_000):
            return {"error": "budget_exhausted"}, 429
        row["amount_nanos"] = spent + nanos
        row["amount"] = row["amount_nanos"] / 1_000_000_000
        state["holds"][data["id"]] = {"day": day, "amount": amount, "amount_nanos": nanos,
                                     "settled": False, "expires": now + 172800}
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
        spent = row.setdefault("amount_nanos", math.ceil(row["amount"] * 1_000_000_000))
        reserved = hold.get("amount_nanos", math.ceil(hold["amount"] * 1_000_000_000))
        row["amount_nanos"] = spent + math.ceil(amount * 1_000_000_000) - reserved
        if amount > hold["amount"]:
            # Unexpected usage or a changed provider contract fails closed.
            row["amount_nanos"] = max(row["amount_nanos"], math.ceil(limit * 1_000_000_000))
        row["amount"] = row["amount_nanos"] / 1_000_000_000
        hold["settled"] = True
        return {"ok": True}, 200
    return {"error": "unavailable"}, 503
