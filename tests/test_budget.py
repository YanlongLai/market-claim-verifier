from __future__ import annotations

from pathlib import Path

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger, UnknownModel
from claimcheck.edgar import EdgarClient


def test_budget_refuses_before_client_call(tmp_path: Path) -> None:
    class FakeResponses:
        calls = 0

        def create(self, **kwargs):
            self.calls += 1
            raise AssertionError("model must not be called")

    class FakeClient:
        responses = FakeResponses()

    fake = FakeClient()
    ledger = Ledger(tmp_path / "ledger.jsonl", budget_usd=0.000001)
    with pytest.raises(BudgetExceeded):
        verify_claim(
            "META revenue was $47.5B",
            fake,
            EdgarClient(tmp_path / "cache", fetcher=lambda _: b"{}"),
            ledger,
            "muse-spark-1.3",
        )
    assert fake.responses.calls == 0


def test_reconcile_uses_actual_and_cached_usage(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0)
    reservation = ledger.reserve(
        {"input": "claim"},
        model="muse-spark-1.3",
        max_output_tokens=100,
    )
    actual = ledger.reconcile(
        reservation,
        {
            "input_tokens": 100,
            "output_tokens": 20,
            "input_tokens_details": {"cached_tokens": 10},
        },
    )

    assert actual == pytest.approx((90 * 1.25 + 10 * 0.15 + 20 * 4.25) / 1_000_000)
    assert ledger.spent_total == pytest.approx(actual)


def test_missing_usage_keeps_worst_case_charge(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0)
    reservation = ledger.reserve(
        {"input": "claim"},
        model="muse-wonder-1.0",
        max_output_tokens=100,
    )
    assert ledger.reconcile(reservation, None) == reservation.amount
    assert ledger.spent_total == reservation.amount


def test_unknown_model_is_refused(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl", budget_usd=1.0)
    with pytest.raises(UnknownModel):
        ledger.reserve({}, model="unknown", max_output_tokens=1)
