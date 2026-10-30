import json
from pathlib import Path
import pytest
from claimcheck.event_context import validate_event_context, bind_event_period
from claimcheck.post import screen_claims
from claimcheck.period_context import missing_period_reason
from claimcheck.program_summary import program_summary

CONTEXT={'ticker':'MSFT','period':'2027Q1','basis':'fiscal','source_url':'https://www.microsoft.com/en-us/Investor/events/fy-2027/earnings-fy-2027-q1','source_quote':'Microsoft Fiscal Year 2027 First Quarter Earnings Conference Call','reviewed':True}

def proposal(quote,claim=None,ticker='MSFT',kind='reported_fact'):
    return {'quote':quote,'claim':claim or quote,'ticker':ticker,'kind':kind}


def test_event_period_is_conditional_and_never_added_to_quote():
    q='This quarter, Microsoft revenue was $92.3 billion.'
    c=screen_claims(q,[proposal(q)],event_context=CONTEXT)[0]
    assert c['quote']==q and c['span']==[0,len(q)]
    assert 'fiscal Q1 2027' in c['claim'] and missing_period_reason(c['claim']) is None
    assert c['event_period_context']['conditional_on_context'] is True
    assert c['event_period_context']['authenticated'] is False
    assert c['extracted_claim']==q


@pytest.mark.parametrize('quote,ticker,kind',[
 ('Last quarter revenue was $1 billion.','MSFT','reported_fact'),
 ('This quarter revenue was $1 billion.','AAPL','reported_fact'),
 ('This quarter revenue will be $1 billion.','MSFT','issuer_guidance'),
 ('This quarter revenue was $1 billion; last year it was $2 billion.','MSFT','reported_fact'),
 ('This quarter revenue was $1 billion in 2026.','MSFT','reported_fact'),
 ('Revenue was $1 billion.','MSFT','reported_fact')])
def test_context_does_not_override_or_guess(quote,ticker,kind):
    c=screen_claims(quote,[proposal(quote,ticker=ticker,kind=kind)],event_context=CONTEXT)[0]
    assert not c.get('event_period_context') and '2027' not in c['claim']


@pytest.mark.parametrize('changes',[{'reviewed':False},{'ticker':'AAPL'},{'period':'2026Q1'},{'source_quote':'FY2027 Q1 and FY2026 Q1'},{'basis':'calendar','source_quote':'fiscal Q1 2027'},{'source_url':'file:///secret'}])
def test_context_validation_rejects_conflicts(changes):
    with pytest.raises(ValueError):validate_event_context({**CONTEXT,**changes},'MSFT')


def test_short_fy_header_needs_explicit_anchor_and_preserves_offsets():
    post='FY27 Q1\nRevenue $92.3 billion'
    row='Revenue $92.3 billion';claim='Microsoft revenue was $92.3 billion in FY27 Q1.'
    assert screen_claims(post,[proposal(row,claim)])[0]['status']=='rejected'
    c=screen_claims(post,[proposal(row,claim)],event_context=CONTEXT)[0]
    assert c['status']=='to_verify' and 'fiscal Q1 2027' in c['claim']
    assert c['quote']==row and c['header_period_bindings'][0]['header_spans']==[[0,7]]
    assert c['header_period_bindings'][0]['column_alignment_verified'] is False


def test_year_exemption_is_not_permission_to_invent_financial_number():
    post='FY27 Q1\nRevenue $92.3 billion'
    c=screen_claims(post,[proposal('Revenue $92.3 billion','Microsoft revenue was $27 billion in FY27 Q1.')],event_context=CONTEXT)[0]
    assert c['status']=='rejected'


def test_wrong_header_period_or_other_issuer_does_not_use_event_anchor():
    for context,ticker in [(CONTEXT,'AAPL'),({**CONTEXT,'period':'2027Q2','source_quote':'FY2027 Q2'},'MSFT')]:
        c=screen_claims('FY27 Q1\nRevenue $92.3 billion',[proposal('Revenue $92.3 billion','Revenue $92.3 billion in FY27 Q1',ticker)],event_context=context)[0]
        assert c['status']=='rejected'


def test_model_narrative_cannot_override_program_result():
    root=Path(__file__).resolve().parents[1]
    r=json.loads((root/'docs/evidence/real-av-v1/baseten/wav/ingest.json').read_text())
    c=r['channels'][0]['claims'][-1]
    assert 'contradicted' in c['summary'] and c['verdict']=='insufficient_evidence'
    safe=program_summary(c['verdict'],c['program_checks'])
    assert 'no correction is validated' in safe and 'FY2026' not in safe


def test_real_retained_proposals_replay_with_context():
    root=Path(__file__).resolve().parents[1]
    r=json.loads((root/'docs/evidence/real-av-v1/baseten/mp4/ingest.json').read_text())
    frame=next(ch for ch in r['channels'] if ch['id']=='frame-1')
    proposals=[proposal(c['quote'],c.get('extracted_claim',c['claim']),c['ticker'],c['kind']) for c in frame['claims']]
    before=screen_claims(frame['normalized_text'],proposals)
    after=screen_claims(frame['normalized_text'],proposals,event_context=CONTEXT)
    assert all(c['status']=='rejected' for c in before)
    assert all(c['status']=='to_verify' for c in after)
    assert all(c['quote']==p['quote'] for c,p in zip(after,proposals))


def test_ingest_records_and_propagates_context(tmp_path,monkeypatch):
    from claimcheck.ingest import ingest_file
    from claimcheck.budget import Ledger
    monkeypatch.setattr('claimcheck.post.extract_claims',lambda text,**kw:[])
    p=tmp_path/'a.txt';p.write_text('This quarter revenue was $1 billion.')
    r=ingest_file(p,client=object(),edgar=None,ledger=Ledger(tmp_path/'ledger'),model='muse-spark-1.3',provider='meta',out_dir=tmp_path/'out',source_ticker='MSFT',event_context=CONTEXT)
    assert r['event_context']==CONTEXT
    child=json.loads((tmp_path/'out/checks/text/report.json').read_text())
    assert child['event_context']==CONTEXT


def test_old_ingest_render_does_not_present_unsafe_model_narrative():
    from claimcheck.ingest import render_html
    root=Path(__file__).resolve().parents[1]
    r=json.loads((root/'docs/evidence/real-av-v1/baseten/wav/ingest.json').read_text())
    html=render_html(r)
    assert 'The 50% level is contradicted' not in html
    assert 'no correction is validated' in html
    assert 'The 50% level is contradicted' in r['channels'][0]['claims'][-1]['summary']


def test_queue_context_identity_cannot_change_on_resume(tmp_path):
    from claimcheck.job_queue import run_queue
    cache=tmp_path/'cache';cache.mkdir();(cache/'company_tickers.json').write_text('{}')
    source=tmp_path/'a.txt';source.write_text('this quarter')
    config={'budget_usd':1,'per_job_budget_usd':1,'event_context':CONTEXT}
    run_queue([source],cache,tmp_path/'q',config,lambda *a:{'status':'completed','cost_usd':0})
    with pytest.raises(ValueError):
        run_queue([source],cache,tmp_path/'q',{**config,'event_context':{**CONTEXT,'period':'2026Q1'}},lambda *a:pytest.fail('must not run'))


def test_fiscal_year_words_cannot_be_declared_calendar():
    with pytest.raises(ValueError,match='basis'):
        validate_event_context({**CONTEXT,'basis':'calendar'},'MSFT')
