from pathlib import Path
import json
import pytest
from claimcheck.stock_review import build_stock_review


def fixture(path, claims, status='completed'):
    path.write_text(json.dumps({'status':status,'input':{'file':'input.png'},'channels':[{'id':'image','claims':claims}]}))
    return path


def test_review_isolates_tickers_preserves_unchecked_and_corrections(tmp_path):
    check={'program_verdict':'contradicted','evidence_valid':True,'actual_value':10,'stated_value':20,'evidence_ids':['E1']}
    claims=[{'ticker':'TSLA','claim':'Revenue 20','quote':'<script>20</script>','status':'verified','verdict':'contradicted','program_checks':[check],'evidence':[{'id':'E1','value':10,'unit':'USD','period':'FY2026Q3'}]},
            {'ticker':'AAPL','claim':'other','status':'verified','verdict':'supported','program_checks':[{'program_verdict':'supported'}]},
            {'ticker':None,'claim':'unknown'},
            {'ticker':'TSLA','claim':'unverified','status':'verified','verdict':'supported','program_checks':[]}]
    src=fixture(tmp_path/'input.json',claims,'partial')
    result=build_stock_review('tsla',[src],tmp_path/'out',pending_documents=[{'input':{'file':'pending.mp3'},'status':'pending'}])
    assert result['counts']=={'contradicted':1,'unchecked':1}
    assert result['document_count']==2 and result['incomplete_documents']==2
    assert len(result['other_ticker_claims'])==len(result['unassigned_claims'])==1
    assert result['claims'][0]['corrections'][0]['evidence'][0]['unit']=='USD'
    assert '<script>' not in (tmp_path/'out/stock-review.html').read_text()
    assert result['incremental_api_cost_usd']==0
    with pytest.raises(ValueError,match='already exists'):build_stock_review('TSLA',[src],tmp_path/'out')


def test_conflicting_duplicates_are_visible_and_missing_evidence_not_corrected(tmp_path):
    a={'ticker':'TSLA','claim':'same claim','status':'verified','verdict':'supported','program_checks':[{'program_verdict':'supported'}]}
    b={**a,'verdict':'contradicted','program_checks':[{'program_verdict':'contradicted','evidence_valid':True,'actual_value':7,'evidence_ids':['missing']}]}
    result=build_stock_review('TSLA',[fixture(tmp_path/'a.json',[a,b])],tmp_path/'out')
    assert result['groups'][0]['conflicting_recorded_verdicts']
    assert len(result['groups'][0]['occurrences'])==2
    assert result['claims'][1]['corrections']==[]


def test_duplicate_reports_refused_before_output(tmp_path):
    src=fixture(tmp_path/'a.json',[])
    with pytest.raises(ValueError,match='duplicate'):build_stock_review('TSLA',[src,src],tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_review_stock_cli_resumes_queue_and_preserves_pending_summary(tmp_path, monkeypatch):
    from claimcheck import cli, job_queue
    from claimcheck.config import load_settings
    settings=load_settings(read_key=False,provider='meta')
    monkeypatch.setattr(cli,'load_settings',lambda **kwargs:settings)
    cache=tmp_path/'cache';cache.mkdir();(cache/'company_tickers.json').write_text('{}')
    inputs=[tmp_path/'a.txt',tmp_path/'b.txt']
    for i,p in enumerate(inputs):p.write_text(f'input {i}')
    calls=[]
    def worker(source,target,frozen,cap):
        calls.append(source.name)
        target.mkdir(parents=True,exist_ok=True)
        result={'status':'completed','cost_usd':0,'input':{'file':str(source)},'channels':[]}
        (target/'ingest.json').write_text(json.dumps(result))
        return result
    monkeypatch.setattr(job_queue,'cli_worker',lambda *args:worker)
    out=tmp_path/'review'
    args=['review-stock','TSLA',*[str(p) for p in inputs],'--out',str(out),'--evidence-cache',str(cache),'--budget','2','--per-job-budget','1','--max-jobs','1']
    assert cli.main(args)==1
    first=json.loads((out/'summary-001/stock-review.json').read_text())
    assert first['document_count']==2 and first['incomplete_documents']==1
    original=(out/'summary-001/stock-review.json').read_bytes()
    assert cli.main(args)==0
    second=json.loads((out/'summary-002/stock-review.json').read_text())
    assert second['document_count']==2 and second['incomplete_documents']==0
    assert len(calls)==2 and (out/'summary-001/stock-review.json').read_bytes()==original


def test_stock_summary_cli_never_reads_credentials(tmp_path,monkeypatch):
    from claimcheck import cli
    from claimcheck.config import load_settings
    def settings(**kwargs):
        assert kwargs['read_key'] is False
        return load_settings(read_key=False)
    monkeypatch.setattr(cli,'load_settings',settings)
    src=fixture(tmp_path/'source.json',[])
    assert cli.main(['stock-summary','TSLA',str(src),'--out',str(tmp_path/'out')])==0
