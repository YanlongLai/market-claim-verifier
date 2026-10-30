"""Paid, bounded follow-up on frozen context-bound claims; no extraction rerun."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,sys,subprocess,zipfile,time
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from claimcheck.agent import verify_claim
from claimcheck.budget import Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.release_fetch import ReleaseClient
from claimcheck.providers import create_client
from claimcheck.trace import TraceRecorder,write_trace
from claimcheck.ingest_media import sha256,write_json
OUT=ROOT/'docs/evidence/real-av-context-live';CACHE=ROOT/'.cache/sec-refresh-2026-10-30'
def offline(url):raise RuntimeError('Source absent from frozen SEC/release cache; network disabled')
def main():
    if (OUT/'freeze.json').exists():raise ValueError('Already started; inspect retained results, no automatic resume/retry')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    paths=[*sorted((ROOT/'src/claimcheck').glob('*.py')),Path(__file__).resolve(),OUT/'cases.json',OUT/'PROTOCOL.md',ROOT/'uv.lock']
    hashes={str(p.relative_to(ROOT)):sha256(p) for p in paths}
    for name in hashes:
        blob=subprocess.check_output(['git','show',f'{revision}:{name}'],cwd=ROOT)
        if blob!=(ROOT/name).read_bytes():raise ValueError('Commit frozen code before paid calls: '+name)
    data=json.loads((OUT/'cases.json').read_text());assert sha256(ROOT/data['replay_source'])==data['replay_sha256']
    for c in data['cases']:
        assert sha256(ROOT/c['source_report'])==json.loads((ROOT/data['replay_source']).read_text())['sources_sha256'][c['source_report']]
    for row in json.loads((ROOT/'docs/evidence/sec-refresh-2026-10-30/manifest.json').read_text())['files']:
        assert sha256(CACHE/row['file'])==row['sha256']
    settings={p:load_settings(provider=p) for p in ('meta','baseten','fireworks')};secrets=[s.model_api_key for s in settings.values()];assert all(secrets)
    write_json(OUT/'freeze.json',{'revision':revision,'sha256':hashes,'started_at':datetime.now(timezone.utc).isoformat(),'provider_caps_usd':{p:2 for p in settings}})
    with zipfile.ZipFile(OUT/'frozen-source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in hashes:z.write(ROOT/name,name)
    def run(provider):
        s=settings[provider];dest=OUT/provider;dest.mkdir()
        client=create_client(provider,s.model_api_key).with_options(max_retries=0,timeout=120)
        ledger=Ledger(dest/'ledger.jsonl',budget_usd=2,provider=provider,provider_budgets={provider:2})
        edgar=EdgarClient(CACHE,fetcher=offline,as_of='2026-10-30');release=ReleaseClient(CACHE,fetcher=offline)
        for case in data['cases']:
            start=time.perf_counter();before=ledger.spent_total
            trace=TraceRecorder(case['input']['claim'],s.model,provider=provider,secrets=secrets)
            record={'case_id':case['id'],'provider':provider,'model':s.model,'input':case['input'],'source_report':case['source_report'],'status':'running'}
            target=dest/(case['id']+'.json');write_json(target,record,secrets)
            print('START',provider,case['id'],flush=True)
            try:
                result=verify_claim(case['input']['claim'],client,edgar,ledger,s.model,trace=trace,provider=provider,max_output_tokens=4000,reasoning_effort='low',release_client=release)
                record.update(status='completed',result=result)
            except Exception as exc:
                record.update(status='failed',error=type(exc).__name__)
                trace.finish({'verdict':'insufficient_evidence','summary':'Follow-up failed; see recorded response/error','error':type(exc).__name__})
            trace_path=write_trace(dest/'traces',trace)
            record.update(trace=str(trace_path.relative_to(OUT)),cost_usd=round(ledger.spent_total-before,8),seconds=round(time.perf_counter()-start,3))
            write_json(target,record,secrets)
            write_json(dest/'spend.json',{'provider':provider,'estimated_or_reserved_usd':ledger.spent_total,'cap_usd':2,'billed_usd':None})
            print('DONE',provider,case['id'],record['status'],record.get('result',{}).get('verdict'),record['cost_usd'],flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,settings))
    print('FINISHED',flush=True)
if __name__=='__main__':main()
