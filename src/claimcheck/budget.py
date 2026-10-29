"""Persistent, conservative token-cost ledger for model calls."""

from __future__ import annotations

import json
import math
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:  # pragma: no cover - the fallback is for non-POSIX development hosts.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

from .providers import (
    BASETEN_DEFAULT_MODEL,
    BASETEN_PRICING,
    BASETEN_PROVIDER,
    FIREWORKS_DEFAULT_MODEL,
    FIREWORKS_PRICING,
    FIREWORKS_PROVIDER,
)


MODEL_PRICES = {
    ("meta", "muse-spark-1.3"): {
        "input": 1.25 / 1_000_000,
        "cached_input": 0.15 / 1_000_000,
        "output": 4.25 / 1_000_000,
    },
    ("meta", "muse-wonder-1.0"): {
        "input": 4.00 / 1_000_000,
        "cached_input": 0.20 / 1_000_000,
        "output": 20.00 / 1_000_000,
    },
    (BASETEN_PROVIDER, BASETEN_DEFAULT_MODEL): BASETEN_PRICING,
    (FIREWORKS_PROVIDER, FIREWORKS_DEFAULT_MODEL): FIREWORKS_PRICING,
}


class UnknownModel(ValueError):
    """Raised before a request when the model price is not known."""


class BudgetExceeded(RuntimeError):
    """Raised before a model call that would exceed the configured budget."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return None
    try:
        return value.model_dump()  # type: ignore[no-any-return]
    except AttributeError:
        return None


def _get(value: Any, key: str, default: Any = None) -> Any:
    mapping = _as_mapping(value)
    if mapping is not None:
        return mapping.get(key, default)
    return getattr(value, key, default)


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    provider: str
    model: str
    estimated_input_tokens: int
    max_output_tokens: int
    amount: float
    payload_chars: int
    context_chars: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "provider": self.provider,
            "model": self.model,
            "estimated_input_tokens": self.estimated_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "amount": self.amount,
            "payload_chars": self.payload_chars,
            "context_chars": self.context_chars,
        }


def _json_chars(value: Any) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str))
    except (TypeError, ValueError):
        return len(str(value))


class Ledger:
    """Append-only budget ledger with reservation/reconciliation semantics."""

    def __init__(
        self,
        path: str | Path = "runs/ledger.jsonl",
        *,
        budget_usd: float = 0.50,
        model_prices: Mapping[Any, Mapping[str, float]] | None = None,
        persist: bool = True,
        provider: str = "meta",
        provider_budgets: Mapping[str, float] | None = None,
    ) -> None:
        self.path = Path(path)
        self.budget_usd = float(budget_usd)
        self.model_prices = dict(model_prices or MODEL_PRICES)
        self.persist = persist
        self.provider = str(provider)
        self.provider_budgets = {
            str(key): float(value) for key, value in (provider_budgets or {}).items()
        }

    def price(self, model: str, *, provider: str | None = None) -> Mapping[str, float]:
        selected_provider = str(provider or self.provider)
        candidates = (
            (selected_provider, model),
            model,
        )
        for key in candidates:
            try:
                return self.model_prices[key]
            except KeyError:
                continue
        raise UnknownModel(f"unknown model for provider {selected_provider}: {model}")

    def _events(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    events.append(value)
        return events

    @contextmanager
    def _file_lock(self):
        """Serialize ledger read/check/append transactions across processes."""

        if not self.persist or fcntl is None:
            yield
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(self.path.name + ".lock")
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    def _spent_for_provider_unlocked(self, provider: str | None) -> float:
        events = self._events()
        reconciled: dict[str, float] = {}
        reservations: dict[str, float] = {}
        for event in events:
            if provider is not None and str(event.get("provider", "meta")) != str(provider):
                continue
            event_type = event.get("event")
            rid = event.get("reservation_id")
            if not isinstance(rid, str):
                continue
            if event_type == "reserve":
                reservations[rid] = float(event.get("amount", 0.0))
            elif event_type == "reconcile":
                reconciled[rid] = float(event.get("amount", 0.0))
        return sum(reconciled.values()) + sum(
            amount for rid, amount in reservations.items() if rid not in reconciled
        )

    @property
    def spent_total(self) -> float:
        return self.spent_for_provider(None)

    def spent_for_provider(self, provider: str | None) -> float:
        with self._file_lock():
            return self._spent_for_provider_unlocked(provider)

    def budget_for_provider(self, provider: str | None = None) -> float:
        selected_provider = str(provider or self.provider)
        return self.provider_budgets.get(selected_provider, self.budget_usd)

    def estimate(
        self,
        payload: Any,
        *,
        model: str,
        max_output_tokens: int,
        previous_context: Any = None,
        provider: str | None = None,
    ) -> Reservation:
        selected_provider = str(provider or self.provider)
        prices = self.price(model, provider=selected_provider)
        payload_chars = _json_chars(payload)
        context_chars = _json_chars(previous_context) if previous_context is not None else 0
        input_tokens = max(1, math.ceil((payload_chars + context_chars) / 3))
        output_tokens = max(0, int(max_output_tokens))
        amount = input_tokens * prices["input"] + output_tokens * prices["output"]
        return Reservation(
            reservation_id=uuid.uuid4().hex,
            provider=selected_provider,
            model=model,
            estimated_input_tokens=input_tokens,
            max_output_tokens=output_tokens,
            amount=amount,
            payload_chars=payload_chars,
            context_chars=context_chars,
        )

    def preview(
        self,
        payload: Any,
        *,
        model: str,
        max_output_tokens: int,
        previous_context: Any = None,
        provider: str | None = None,
    ) -> Reservation:
        """Estimate and budget-check without appending a reservation."""

        reservation = self.estimate(
            payload,
            model=model,
            max_output_tokens=max_output_tokens,
            previous_context=previous_context,
            provider=provider,
        )
        selected_provider = reservation.provider
        with self._file_lock():
            spent = self._spent_for_provider_unlocked(selected_provider)
            budget = self.budget_for_provider(selected_provider)
            if spent + reservation.amount > budget:
                raise BudgetExceeded(
                    f"{selected_provider} budget ${budget:.4f} would be exceeded by reservation "
                    f"${reservation.amount:.4f} (spent ${spent:.4f})"
                )
        return reservation

    def reserve(
        self,
        payload: Any,
        *,
        model: str,
        max_output_tokens: int,
        previous_context: Any = None,
        provider: str | None = None,
    ) -> Reservation:
        """Reserve worst-case cost, refusing before the caller invokes a model."""

        reservation = self.estimate(
            payload,
            model=model,
            max_output_tokens=max_output_tokens,
            previous_context=previous_context,
            provider=provider,
        )
        selected_provider = reservation.provider
        with self._file_lock():
            spent = self._spent_for_provider_unlocked(selected_provider)
            budget = self.budget_for_provider(selected_provider)
            if spent + reservation.amount > budget:
                raise BudgetExceeded(
                    f"{selected_provider} budget ${budget:.4f} would be exceeded by reservation "
                    f"${reservation.amount:.4f} (spent ${spent:.4f})"
                )
            self._append_unlocked(
                {
                    "event": "reserve",
                    "timestamp": _now(),
                    **reservation.as_dict(),
                }
            )
        return reservation

    def reserve_audio(self, duration_s: float) -> Reservation:
        """Reserve Meta ASR's rounded-second charge before upload (no retries).

        File ASR has no token usage. Keep this fixed reservation on failure as
        a conservative charge bound; successful requests cost the same amount.
        """
        if not math.isfinite(duration_s) or not 0 < duration_s <= 600:
            raise ValueError("ASR duration must be greater than zero and at most 600 seconds")
        seconds = math.ceil(duration_s)
        reservation = Reservation(uuid.uuid4().hex, "meta", "muse-voice-transcribe-1.0",
                                  0, 0, seconds * .18 / 3600, 0, 0)
        with self._file_lock():
            spent = self._spent_for_provider_unlocked("meta")
            if spent + reservation.amount > self.budget_for_provider("meta"):
                raise BudgetExceeded("Meta budget would be exceeded by audio reservation")
            self._append_unlocked({"event": "reserve", "timestamp": _now(), **reservation.as_dict(),
                                   "billing_unit": "audio_second", "billable_units": seconds})
        return reservation

    def _append(self, event: dict[str, Any]) -> None:
        if not self.persist:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._file_lock():
            self._append_unlocked(event)

    def _append_unlocked(self, event: dict[str, Any]) -> None:
        if not self.persist:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")

    def reconcile(
        self,
        reservation: Reservation,
        usage: Any = None,
    ) -> float:
        """Replace a reservation with actual usage, or keep it if usage is absent."""

        prices = self.price(reservation.model, provider=reservation.provider)
        input_tokens = _get(usage, "input_tokens")
        output_tokens = _get(usage, "output_tokens")
        if input_tokens is None:
            input_tokens = _get(usage, "input")
        if input_tokens is None:
            input_tokens = _get(usage, "prompt_tokens")
        if output_tokens is None:
            output_tokens = _get(usage, "output")
        if output_tokens is None:
            output_tokens = _get(usage, "completion_tokens")
        details = _get(usage, "input_tokens_details")
        cached_tokens = _get(details, "cached_tokens", None)
        if cached_tokens is None:
            cached_tokens = _get(usage, "cached", 0)
        if not cached_tokens:
            cached_details = _get(usage, "prompt_tokens_details")
            cached_tokens = _get(cached_details, "cached_tokens", 0)
        cached_tokens = cached_tokens or 0
        try:
            if input_tokens is None or output_tokens is None:
                raise ValueError
            input_tokens = max(0, int(input_tokens))
            output_tokens = max(0, int(output_tokens))
            cached_tokens = min(input_tokens, max(0, int(cached_tokens)))
            amount = (
                (input_tokens - cached_tokens) * prices["input"]
                + cached_tokens * prices["cached_input"]
                + output_tokens * prices["output"]
            )
            usage_missing = False
        except (TypeError, ValueError):
            amount = reservation.amount
            usage_missing = True

        self._append(
            {
                "event": "reconcile",
                "timestamp": _now(),
                "reservation_id": reservation.reservation_id,
                "provider": reservation.provider,
                "amount": amount,
                "usage_missing": usage_missing,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cached_tokens": cached_tokens,
                },
            }
        )
        return amount
