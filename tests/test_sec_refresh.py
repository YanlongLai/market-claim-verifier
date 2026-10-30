import importlib.util
import gzip
import hashlib
import json
from pathlib import Path
import pytest


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).parents[1]/'scripts'/f'{name}.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_cutoff_uses_filing_date_not_period_end():
    m=module('refresh_sec_snapshot')
    doc={'facts':{'us-gaap':{'Revenue':{'units':{'USD':[
        {'filed':'2026-10-30','end':'2026-09-30'},
        {'filed':'2026-10-31','end':'2026-09-30'}]}}}}}
    assert m.summarize_facts(doc,'2026-10-30')=={'latest_fact_filed':'2026-10-30','latest_period_end':'2026-09-30','eligible_fact_rows':1}
    submissions={'filings':{'recent':{'form':['4','10-Q','10-Q'],'filingDate':['2026-10-30','2026-10-31','2026-10-30'],'accessionNumber':['a','b','c'],'primaryDocument':['a','b','c']}}}
    assert [r['accessionNumber'] for r in m.summarize_filings(submissions,'2026-10-30')]==['c']


def test_restore_preserves_bytes_and_refuses_overwrite_or_tampering(tmp_path):
    m=module('restore_sec_snapshot');records=tmp_path/'records';(records/'snapshots').mkdir(parents=True)
    raw=b'{"facts": {}}\n';name='companyfacts-CIK0000000001.json';archive='snapshots/'+name+'.gz'
    item={'file':name,'archive':archive,'sha256':hashlib.sha256(raw).hexdigest(),'url':'https://data.sec.gov/example','fetched_at':'2026-10-30T00:00:00Z'}
    (records/'manifest.json').write_text(json.dumps({'files':[item],'errors':[]}));(records/archive).write_bytes(gzip.compress(raw,mtime=0))
    assert m.restore(records,tmp_path/'cache')==1
    assert (tmp_path/'cache'/name).read_bytes()==raw
    with pytest.raises(ValueError,match='already exists'):m.restore(records,tmp_path/'cache')
    (records/archive).write_bytes(gzip.compress(b'{}'))
    with pytest.raises(ValueError,match='hash mismatch'):m.restore(records,tmp_path/'bad-cache')
    assert not (tmp_path/'bad-cache').exists()
