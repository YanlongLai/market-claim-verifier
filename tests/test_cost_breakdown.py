import pytest
from claimcheck.budget import Ledger
from claimcheck.ingest import _InputLedger


def test_usage_estimates_and_retained_reservations_are_distinct(tmp_path):
    parent = Ledger(tmp_path / 'ledger', budget_usd=10)
    ledger = _InputLedger(parent)
    ledger.stage = 'claim_extraction'
    first = ledger.reserve({'input': 'test'}, model='muse-spark-1.3', max_output_tokens=100)
    ledger.reconcile(first, {'input_tokens': 10, 'output_tokens': 5})
    ledger.stage = 'claim_verification'
    second = ledger.reserve({'input': 'test'}, model='muse-spark-1.3', max_output_tokens=100)
    ledger.reconcile(second, None)
    ledger.stage = 'asr'
    third = ledger.reserve_audio(60)
    result = ledger.cost_summary()
    assert result['billed_usd'] is None
    assert result['attempts'][first.reservation_id]['basis'] == 'usage_estimate'
    assert result['attempts'][second.reservation_id]['basis'] == 'retained_reservation'
    assert result['attempts'][third.reservation_id]['stage'] == 'asr'
    assert sum(result['by_stage_usd'].values()) == pytest.approx(ledger.spent_total)
    assert result['original_reservations_usd'] >= ledger.spent_total
