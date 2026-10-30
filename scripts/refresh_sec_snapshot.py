"""Fetch an immutable SEC snapshot for the existing evaluation company list.

No model calls. Does not overwrite the runtime cache or historical fixtures.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from claimcheck.sec_transport import sec_get


def summarize_facts(doc, as_of):
    rows=[r for namespace in doc.get('facts',{}).values() for concept in namespace.values()
          for values in concept.get('units',{}).values() for r in values
          if isinstance(r.get('filed'),str) and r['filed'] <= as_of]
    return {'latest_fact_filed':max((r['filed'] for r in rows),default=None),
            'latest_period_end':max((r.get('end','') for r in rows),default=None),
            'eligible_fact_rows':len(rows)}


def summarize_filings(doc, as_of):
    recent=doc.get('filings',{}).get('recent',{})
    rows=[{k:recent[k][i] for k in ('form','filingDate','accessionNumber','primaryDocument')}
          for i,form in enumerate(recent.get('form',[]))
          if form in ('10-K','10-Q','8-K','10-K/A','10-Q/A','8-K/A')
          and recent['filingDate'][i] <= as_of]
    return sorted(rows,key=lambda r:r['filingDate'],reverse=True)[:8]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--as-of',required=True,type=date.fromisoformat)
    p.add_argument('--cache-dir',required=True,type=Path)
    p.add_argument('--record-dir',required=True,type=Path)
    args=p.parse_args();cache=args.cache_dir.resolve();out=args.record_dir.resolve()
    if cache.exists() or (out/'manifest.json').exists():p.error('choose a fresh cache and record directory')
    cache.mkdir(parents=True);out.mkdir(parents=True,exist_ok=True);(out/'snapshots').mkdir()
    tickers=sorted(json.loads((ROOT/'eval/v2/MANIFEST.json').read_text())['counts']['by_company'])
    manifest={'as_of':args.as_of.isoformat(),'started_at':datetime.now(timezone.utc).isoformat(),
              'scope':'23 existing US-equity evaluation tickers; fresh companyfacts and recent submissions; no model calls',
              'cutoff_limit':'Fetched during the day, not a complete end-of-day archive. Raw SEC responses may contain later filings; summaries filter filingDate/filed to as_of. Historical submission shards and release exhibits are not fetched.',
              'cache_dir':str(cache.relative_to(ROOT)),'files':[],'companies':[],'errors':[]}
    def save(): (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    def fetch(filename,url):
        raw=sec_get(url,timeout=45);doc=json.loads(raw)
        digest=hashlib.sha256(raw).hexdigest();stamp=datetime.now(timezone.utc).isoformat()
        (cache/filename).write_bytes(raw)
        metadata={'url':url,'fetched_at':stamp,'sha256':digest}
        (cache/(filename+'.meta.json')).write_text(json.dumps(metadata,indent=2)+'\n')
        (out/'snapshots'/(filename+'.gz')).write_bytes(gzip.compress(raw,mtime=0))
        manifest['files'].append({'file':filename,'archive':'snapshots/'+filename+'.gz','bytes':len(raw),**metadata});save()
        return doc
    try:
        mapping=fetch('company_tickers.json','https://www.sec.gov/files/company_tickers.json')
    except Exception as exc:
        manifest['errors'].append({'stage':'ticker-map','error':str(exc)});save();return 1
    records={r['ticker']:r for r in mapping.values() if isinstance(r,dict) and 'ticker' in r}
    for ticker in tickers:
        record={'ticker':ticker}
        try:
            cik=f"{int(records[ticker]['cik_str']):010d}";record['cik']=cik
            for kind,url in [('companyfacts',f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'),('submissions',f'https://data.sec.gov/submissions/CIK{cik}.json')]:
                try:
                    d=fetch(f'{kind}-CIK{cik}.json',url)
                    record.update(summarize_facts(d,args.as_of.isoformat()) if kind=='companyfacts' else {'recent_financial_filings':summarize_filings(d,args.as_of.isoformat())})
                except Exception as exc:manifest['errors'].append({'ticker':ticker,'kind':kind,'error':str(exc)})
        except Exception as exc:manifest['errors'].append({'ticker':ticker,'error':str(exc)})
        manifest['companies'].append(record);save();print(ticker,record.get('latest_fact_filed'),flush=True)
    manifest['finished_at']=datetime.now(timezone.utc).isoformat();save()
    return 1 if manifest['errors'] else 0


if __name__=='__main__':raise SystemExit(main())
