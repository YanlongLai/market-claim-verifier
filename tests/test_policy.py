import copy
import json
import pytest
from claimcheck.edgar import EdgarClient
from claimcheck.policy import VerificationPolicy, policy_html
from claimcheck.release import ReleaseService
from claimcheck.release_fetch import ReleaseError
from claimcheck.cli import _parser
from test_edgar import synthetic_client
from test_release import RecordedEdgar, offline_client


def facts():
    common = {'start': '2024-04-01', 'end': '2024-06-30', 'form': '10-Q', 'fy': 2024, 'fp': 'Q2', 'frame': 'CY2024Q2'}
    return {'us-gaap': {'RevenueFromContractWithCustomerExcludingAssessedTax': {'units': {'USD': [
        {**common, 'val': 100e6, 'filed': '2024-07-31', 'accn': '0000000001-24-000001'},
        {**common, 'val': 110e6, 'filed': '2025-07-31', 'accn': '0000000001-25-000001'},
    ]}}}}


def test_cutoff_precedes_selection_and_does_not_mutate_cache(tmp_path):
    latest = synthetic_client(tmp_path, facts())
    original = (tmp_path / 'companyfacts-CIK0001326801.json').read_bytes()
    historical = EdgarClient(tmp_path, as_of='2024-07-31')
    before = EdgarClient(tmp_path, as_of='2024-07-30')
    assert latest.lookup_fact('META', 'revenue', '2024Q2')['value'] == 110e6
    result = historical.lookup_fact('META', 'revenue', '2024Q2')
    assert result['value'] == 100e6
    assert result['filed'] == '2024-07-31'
    assert not result['provenance']['restated']
    assert result['verification_policy']['as_of'] == '2024-07-31'
    assert historical.lookup_fact('META', 'revenue', 'latest')['value'] == 100e6
    assert 'error' in before.lookup_fact('META', 'revenue', '2024Q2')
    assert before.list_periods('META', 'revenue') != ['2024Q2']
    assert (tmp_path / 'companyfacts-CIK0001326801.json').read_bytes() == original
    assert latest.lookup_fact('META', 'revenue', '2024Q2')['value'] == 110e6


def test_undated_and_invalid_dates_fail_closed(tmp_path):
    data = facts()
    rows = data['us-gaap']['RevenueFromContractWithCustomerExcludingAssessedTax']['units']['USD']
    rows[0].pop('filed')
    rows[1]['filed'] = '2024-02-30'
    synthetic_client(tmp_path, data)
    client = EdgarClient(tmp_path, as_of='2025-12-31')
    assert 'error' in client.lookup_fact('META', 'revenue', '2024Q2')


def test_release_cutoff_and_quote_recheck():
    edgar = RecordedEdgar()
    edgar.policy = VerificationPolicy(as_of='2025-07-29')
    service = ReleaseService(edgar, offline_client())
    assert not service.find('META', 'revenue', 'FY2025Q3', 'guidance')['candidates']
    edgar.policy = VerificationPolicy(as_of='2025-07-30')
    service = ReleaseService(edgar, offline_client())
    candidate = service.find('META', 'revenue', 'FY2025Q3', 'guidance')['candidates'][0]
    assert service.quote(candidate['candidate_id'], candidate['start'], candidate['end'])['span_verified']
    service.candidates[candidate['candidate_id']]['filed'] = '2025-07-31'
    with pytest.raises(ReleaseError, match='as_of'):
        service.quote(candidate['candidate_id'], candidate['start'], candidate['end'])


@pytest.mark.parametrize('value', ['2025-02-30', '20250730', '', '2025-7-3', '2025-07-30T12:00:00'])
def test_invalid_cutoffs_rejected(value):
    with pytest.raises(ValueError):
        VerificationPolicy(as_of=value)
    with pytest.raises(SystemExit):
        _parser().parse_args(['edgar', 'META', 'revenue', '2024Q2', '--as-of', value])


def test_policy_identity_and_report_label():
    first = VerificationPolicy(as_of='2025-07-30')
    assert first.to_dict() == VerificationPolicy(as_of='2025-07-30').to_dict()
    assert first.to_dict()['policy_id'] != VerificationPolicy().to_dict()['policy_id']
    assert 'not recorded' in policy_html({})
    assert '2025-07-30' in policy_html({'verification_policy': first.to_dict()})
    with pytest.raises(ValueError):
        VerificationPolicy(version='loose')


def test_derivations_and_history_cannot_use_later_filings(tmp_path):
    from test_edgar import fixture_client
    fixture_client(tmp_path)
    client = EdgarClient(tmp_path, as_of='2025-07-31')
    assert 'error' in client.lookup_fact('META', 'revenue', '2025Q4')
    history = client.history_rank('META', 'revenue', '2025Q2')
    assert 'error' not in history
    assert history['periods_considered']['last'] <= '2025Q2'
    for item in history['periods']:
        assert not item.get('filed') or item['filed'] <= '2025-07-31'


def test_cutoff_is_recorded_even_on_early_abstention(tmp_path):
    from claimcheck.agent import verify_claim
    from claimcheck.budget import Ledger
    from claimcheck.trace import TraceRecorder
    edgar = EdgarClient(tmp_path, as_of='2025-07-30')
    trace = TraceRecorder('META revenue was $100 billion.', 'muse-spark-1.3')
    result = verify_claim('META revenue was $100 billion.', None, edgar,
                          Ledger(tmp_path / 'ledger'), 'muse-spark-1.3', trace=trace)
    assert result['verification_policy']['as_of'] == '2025-07-30'
    assert trace.as_dict()['verification_policy'] == result['verification_policy']
    assert trace.model_calls == 0
