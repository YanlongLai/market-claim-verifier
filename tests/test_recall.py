"""Occurrence recall, budgeted long extraction and the recorded text EPS miss."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from types import SimpleNamespace

import pytest

from claimcheck.budget import Ledger
from claimcheck.checks import evaluate_sub_claim
from claimcheck.ingest import attach_locations, prepare_text
from claimcheck.post import LONG_EXTRACTION_CHARS, PostError, check_post, extract_claims, extraction_windows, locate_quote, numbers_preserved, screen_claims
from claimcheck.trace import TraceRecorder
from test_ingest import ROOT
from test_ingest_hardening import SequenceClient, completed


def fact(quote, claim=None, **extra):
    return dict(quote=quote, claim=claim or quote, ticker='AAPL', kind='reported_fact', **extra)


def fake_verification(claim, *args, **kwargs):
    return dict(verdict='supported', summary='offline test', evidence_strength='medium', flags=[],
                program_checks=[dict(text=claim, evidence_ids=[], program_verdict='supported')])


def test_distinct_quotes_survive_and_identical_rewrites_share_one_check(monkeypatch, tmp_path):
    one = 'Apple EPS grew 12% for fiscal Q3 2025.'
    two = 'For fiscal Q3 2025, Apple EPS grew 12%.'
    post = one + '\n\n' + two
    proposed = [fact(one), fact(two, one), fact(one)]
    monkeypatch.setattr('claimcheck.post.extract_claims', lambda *a, **k: proposed)
    calls = []
    def verify(claim, *args, **kwargs):
        calls.append(claim)
        return fake_verification(claim)
    monkeypatch.setattr('claimcheck.post.verify_claim', verify)
    result = check_post(post, client=None, edgar=None, ledger=Ledger(tmp_path / 'ledger'),
                        model='muse-spark-1.3', provider='meta', out_dir=tmp_path / 'out', max_claims=1)
    assert len(result['claims']) == 2 and calls == [one]
    assert result['claims'][1]['verification_reused_from'] == 1
    assert result['claims'][1]['cost_usd'] == 0
    assert all(c['status'] == 'verified' for c in result['claims'])


def test_window_dedup_preserves_occurrences_and_period_scope():
    quote = 'Apple EPS grew 12%.'
    post = f'Fiscal Q3 2024. {quote}\n\nFiscal Q3 2025. {quote}'
    a, b = post.index(quote), post.rindex(quote)
    first = fact(quote, 'Apple EPS grew 12% for fiscal Q3 2024.', source_window=[0, b], extraction_window=0)
    second = fact(quote, 'Apple EPS grew 12% for fiscal Q3 2025.', source_window=[b, len(post)], extraction_window=1)
    claims = screen_claims(post, [first, first, second])
    assert len(claims) == 2
    assert [c['quote_spans'] for c in claims] == [[[a, a + len(quote)]], [[b, b + len(quote)]]]
    channel = dict(kind='text', segments=[dict(id='turn', text=post)])
    prepare_text(channel)
    attach_locations(channel, claims)
    assert [c['source_locations'][0]['raw_span'][0] for c in claims] == [a, b]


def test_rejected_overlap_proposal_cannot_hide_a_later_exact_quote():
    quote = 'Apple EPS grew 12% for fiscal Q3 2025.'
    post = 'Nonfinancial introduction.\n\n' + quote
    invalid = fact(quote, source_window=[0, 10], extraction_window=0)
    valid = fact(quote, source_window=[10, len(post)], extraction_window=1)
    claims = screen_claims(post, [invalid, valid, valid])
    assert [c['status'] for c in claims] == ['rejected', 'to_verify']
    assert claims[1]['quote_spans'] == [[post.index(quote), len(post)]]


def test_frozen_transcript_preserves_heard_text_and_asr_provenance():
    folder = ROOT / 'docs/evidence/multimodal-2026-10-30b'
    provenance = json.loads((folder / 'frozen-transcript.json').read_text())
    frozen = (folder / provenance['text_file']).read_bytes()
    assert hashlib.sha256(frozen).hexdigest() == provenance['text_sha256']
    source = json.loads((folder / 'long-call-r2/ingest.json').read_text())['channels'][0]
    assert frozen.decode() == source['raw_text']
    assert hashlib.sha256((folder / provenance['source_asr_record']).read_bytes()).hexdigest() == provenance['source_asr_record_sha256']
    projection = json.loads((folder / 'long-call-frozen/ingest.json').read_text())['channels'][0]
    assert projection['normalized_text'] == source['normalized_text']
    assert projection['kind'] == 'text' and not projection.get('media_call')


def test_report_does_not_credit_unextracted_repeats_outside_source_window(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts/multimodal'))
    from build_hardening_report import claim_recall
    from build_report import financial_numbers
    quote = 'Apple EPS grew 12% for fiscal Q3 2025.'
    post = quote + '\n\n' + quote
    claim = screen_claims(post, [fact(quote, source_window=[0, len(quote)], extraction_window=0)])[0]
    claim.update(status='verified', program_checks=[{'program_verdict': 'supported'}])
    observed = financial_numbers(post)
    assert len(observed) == 2
    result = claim_recall(dict(normalized_text=post, claims=[claim]),
                          dict(expected=[n['canonical_value'] for n in observed], observed=observed))
    assert result['accepted'] == result['program_checked'] == 1


def test_context_year_with_trailing_comma_keeps_number_and_date_guard():
    quote = 'Apple diluted EPS was $1.67, up 12% year over year.'
    context = 'Apple fiscal 2025 Q3 ended June 28, 2025. ' + quote
    claim = 'Apple diluted EPS was $1.67 in fiscal Q3 2025, up 12% year over year.'
    assert numbers_preserved(claim, quote, context)[0]
    assert not numbers_preserved(claim.replace('2025,', '2024,'), quote, context)[0]
    assert not numbers_preserved('Apple EPS was $1.67 on June 28, 2025.', quote, context)[0]
    assert not numbers_preserved(claim.replace('$1.67', '$1.97'), quote, context)[0]


def test_long_windows_partition_claim_cap_keep_tail_and_context(monkeypatch, tmp_path):
    # Twelve distinct turns exceed the old global cap. Each extraction also
    # sees overlap; duplicate occurrences must not spend a second verification.
    post = '\n\n'.join(f'Fiscal Q3 2025. Apple revenue was ${n} billion. ' + 'Narration. ' * 44
                       for n in range(10, 22))
    windows = extraction_windows(post, max_chars=LONG_EXTRACTION_CHARS)
    assert len(post) > 6000 and len(windows) > 8
    requests, calls = [], []
    def extract(text, **kwargs):
        assert kwargs['reasoning_effort'] == 'low'
        requests.append((text, kwargs['source_period']))
        return [fact(m[0], m[0][:-1] + ' for fiscal Q3 2025.')
                for m in re.finditer(r'Apple revenue was \$\d+ billion\.', text)]
    def verify(claim, *args, **kwargs):
        calls.append(claim)
        return fake_verification(claim)
    monkeypatch.setattr('claimcheck.post.extract_claims', extract)
    monkeypatch.setattr('claimcheck.post.verify_claim', verify)
    result = check_post(post, client=None, edgar=None, ledger=Ledger(tmp_path / 'ledger'),
        model='muse-spark-1.3', provider='meta', out_dir=tmp_path / 'out', max_claims=1, allow_long_input=True)
    assert len(requests) == len(windows)
    assert all('Q3 2025' in text or 'Q3 2025' in (context or '') for text, context in requests)
    assert len(calls) == 12 and '$21 billion' in calls[-1]
    assert all(c['status'] == 'verified' for c in result['claims'])
    assert result['claim_limit']['per'] == 'extraction_window'
    assert max(Counter(c['extraction_windows'][0] for c in result['claims']).values()) <= 1


def test_overfull_first_window_does_not_starve_later_windows(monkeypatch, tmp_path):
    rows = ['Apple revenue was $10 billion. Apple revenue was $11 billion.']
    rows += [f'Apple revenue was ${n} billion.' for n in range(20, 32)]
    post = '\n\n'.join('Fiscal Q3 2025. ' + row + ' Narration.' * 48 for row in rows)
    monkeypatch.setattr('claimcheck.post.extract_claims', lambda text, **k: [
        fact(m[0], m[0][:-1] + ' for fiscal Q3 2025.')
        for m in re.finditer(r'Apple revenue was \$\d+ billion\.', text)])
    monkeypatch.setattr('claimcheck.post.verify_claim', fake_verification)
    result = check_post(post, client=None, edgar=None, ledger=Ledger(tmp_path / 'ledger'),
        model='muse-spark-1.3', provider='meta', out_dir=tmp_path / 'out', max_claims=1, allow_long_input=True)
    assert [(c['claim'], c['status']) for c in result['claims'] if c['status'] == 'not_checked'] == [
        ('Apple revenue was $11 billion for fiscal Q3 2025.', 'not_checked')]
    assert result['claims'][-1]['status'] == 'verified' and '$31 billion' in result['claims'][-1]['claim']


def test_financial_clause_across_turn_boundary_keeps_both_source_turns(monkeypatch, tmp_path):
    head = 'Apple diluted earnings per share were'
    tail = '$1.67 for fiscal Q3 2025, up 12% year over year.'
    paragraphs = ['Fiscal Q3 2025. ' + 'Narration. ' * 44 + head, tail + ' Narration.' * 44]
    paragraphs += ['Nonfinancial narration. ' * 24] * 12
    post = '\n\n'.join(paragraphs)
    quote = head + '\n\n' + tail
    def extract(text, **kwargs):
        return [fact(quote, 'Apple diluted EPS was $1.67 for fiscal Q3 2025, up 12% year over year.')] if locate_quote(text, quote) else []
    monkeypatch.setattr('claimcheck.post.extract_claims', extract)
    monkeypatch.setattr('claimcheck.post.verify_claim', fake_verification)
    result = check_post(post, client=None, edgar=None, ledger=Ledger(tmp_path / 'ledger'),
        model='muse-spark-1.3', provider='meta', out_dir=tmp_path / 'out', allow_long_input=True)
    assert len(result['claims']) == 1 and result['claims'][0]['status'] == 'verified'
    channel = dict(kind='transcript', segments=[dict(id=str(i), text=p) for i, p in enumerate(paragraphs)])
    prepare_text(channel)
    attach_locations(channel, result['claims'])
    locations = result['claims'][0]['source_locations']
    assert len(locations) == 1 and [s['id'] for s in locations[0]['sources']] == ['0', '1']


@pytest.mark.parametrize('change', ['period', 'metric', 'issuer', 'unit', 'growth', 'mixed_growth', 'guidance', 'non_gaap', 'missing_fact'])
def test_eps_fallback_cannot_bypass_evidence_checks(change):
    folder = ROOT / 'docs/evidence/multimodal-2026-10-30/text'
    saved = json.loads((folder / 'ingest.json').read_text())['channels'][0]['claims'][1]
    trace = json.loads((folder / 'checks/text' / saved['trace_path']).read_text())
    evidence = {c['result']['evidence_id']: copy.deepcopy(c['result']) for c in trace['tool_calls']}
    kinds = {c['result']['evidence_id']: c['name'] for c in trace['tool_calls']}
    text = saved['claim']
    if change == 'period':
        text = text.replace('fiscal', 'calendar')
    elif change == 'metric':
        evidence['E2']['metric'] = 'eps_basic'
    elif change == 'issuer':
        text = text.replace('Apple', 'Microsoft')
    elif change == 'unit':
        evidence['E2']['unit'] = 'USD'
    elif change == 'growth':
        text = 'Apple diluted EPS grew 12% for fiscal Q3 2025.'
    elif change == 'mixed_growth':
        text = 'Apple diluted EPS was $1.67, up 12% year over year for fiscal Q3 2025.'
    elif change == 'guidance':
        text = text.replace('reported', 'expects')
    elif change == 'non_gaap':
        text = text.replace('diluted', 'adjusted diluted')
    else:
        evidence['E2'] = {'error': 'insufficient_evidence'}
    sub = dict(text=text, original_claim=text, stated_text='$1.67', stated_value=1.67,
               comparator='eq', evidence_ids=['E1', 'E2'], interpretations=[],
               claim_type='reported_in_release', verdict='contradicted')
    if change in {'growth', 'mixed_growth'}:
        sub.update(stated_text='12%', stated_value=12)
    result = evaluate_sub_claim(sub, SimpleNamespace(evidence=evidence, evidence_kind=kinds))
    assert result['program_verdict'] == 'insufficient_evidence'


@pytest.mark.parametrize('provider', ['meta', 'baseten'])
def test_extraction_reasoning_setting_and_incomplete_trace(provider, tmp_path):
    model = 'muse-spark-1.3' if provider == 'meta' else 'meta-models/muse-spark-open-1026'
    response = completed('{"claims": []}') if provider == 'meta' else {
        'id': 'test', 'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': '{"claims": []}'}}],
        'usage': {'prompt_tokens': 10, 'completion_tokens': 20}}
    client = SequenceClient([response])
    recorder = TraceRecorder('test', model, provider=provider)
    assert extract_claims('Apple fiscal Q3 2025.', client=client, ledger=Ledger(tmp_path / 'ledger'),
                          model=model, provider=provider, recorder=recorder, reasoning_effort='low', source_period='fiscal Q3 2025') == []
    request = client.requests[0]
    assert (request['reasoning']['effort'] if provider == 'meta' else request['reasoning_effort']) == 'low'
    instructions = request['instructions'] if provider == 'meta' else request['messages'][0]['content']
    content = request['input'][0]['content'] if provider == 'meta' else request['messages'][1]['content']
    assert 'context only, outside the quoted post' in instructions and 'never prepend' in instructions
    assert content == 'Apple fiscal Q3 2025.'
    # A length stop remains a failure even if a response has parsable JSON.
    if provider == 'meta':
        response['status'] = 'incomplete'
    else:
        response['choices'][0]['finish_reason'] = 'length'
    client.queue.append(response)
    with pytest.raises(PostError, match='incomplete'):
        extract_claims('Apple fiscal Q3 2025.', client=client, ledger=Ledger(tmp_path / 'ledger'),
                       model=model, provider=provider, recorder=recorder)
    assert recorder.as_dict()['requests'][-1]['status'] == 'incomplete'
    assert recorder.summary()['cost_usd'] > 0
