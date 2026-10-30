"""Execute the preregistered six real-webcast probes. Paid, bounded, no whole-case retry."""
from pathlib import Path
import sys,json,subprocess,time,zipfile
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import httpx
from claimcheck.budget import Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.ingest import ingest_file
from claimcheck.ingest_media import sha256,write_json
from claimcheck.providers import create_client
from claimcheck.release_fetch import ReleaseClient
from claimcheck.stock_review import build_stock_review
OUT=ROOT/'docs/evidence/real-av-v1';DATA=ROOT/'eval/real-av-v1';CACHE=ROOT/'.cache/sec-refresh-2026-10-30'
def offline(url):raise RuntimeError('No network evidence fetch in frozen real AV probe')
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    paths=[*sorted((ROOT/'src/claimcheck').glob('*.py')),Path(__file__).resolve(),DATA/'README.md',DATA/'manifest.json',DATA/'caption-reference.json',ROOT/'uv.lock']
    hashes={str(p.relative_to(ROOT)):sha256(p) for p in paths}
    for name in hashes:
        blob=subprocess.run(['git','show',f'{revision}:{name}'],cwd=ROOT,capture_output=True,check=True).stdout
        if blob!=(ROOT/name).read_bytes():raise ValueError('commit source before execution: '+name)
    for row in json.loads((DATA/'manifest.json').read_text())['inputs']:
        if sha256(ROOT/row['path'])!=row['sha256']:raise ValueError('input hash changed')
    for row in json.loads((ROOT/'docs/evidence/sec-refresh-2026-10-30/manifest.json').read_text())['files']:
        if sha256(CACHE/row['file'])!=row['sha256']:raise ValueError('SEC snapshot changed')
    freeze=OUT/'freeze.json'
    if freeze.exists():raise ValueError('suite already started; inspect retained outcomes, never automatic retry')
    write_json(freeze,{'revision':revision,'sha256':hashes,'started_at':datetime.now(timezone.utc).isoformat(),'new_provider_caps':{'meta':3,'baseten':2,'fireworks':2}})
    with zipfile.ZipFile(OUT/'frozen-source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in hashes:z.write(ROOT/name,name)
    ledger=Ledger(OUT/'ledger.jsonl',budget_usd=7,provider_budgets={'meta':3,'baseten':2,'fireworks':2})
    meta=load_settings(provider='meta');settings={p:load_settings(provider=p) for p in ('meta','baseten','fireworks')}
    secrets=[s.model_api_key for s in settings.values()];assert all(secrets)
    for provider,s in settings.items():
        client=create_client(provider,s.model_api_key).with_options(max_retries=0,timeout=120)
        vision=create_client('meta',meta.model_api_key).with_options(max_retries=0,timeout=120)
        reports=[]
        for fmt in ('wav','mp4'):
            dest=OUT/provider/fmt;path=DATA/'inputs'/f'msft-fy27q1-cfo-60s.{fmt}'
            print('START',provider,fmt,flush=True)
            with httpx.Client(timeout=120) as http:
                r=ingest_file(path,client=client,vision_client=vision,asr_http=http,meta_api_key=meta.model_api_key,
                    edgar=EdgarClient(CACHE,fetcher=offline,as_of='2026-10-30'),release_client=ReleaseClient(CACHE,fetcher=offline),
                    ledger=ledger,model=s.model,provider=provider,out_dir=dest,max_claims=4,max_output_tokens=4000,
                    reasoning_effort='low',source_ticker='MSFT',secrets=secrets)
            reports.append(dest/'ingest.json')
            print('DONE',provider,fmt,r['status'],r['coverage'],r['cost_usd'],flush=True)
            write_json(OUT/'spend.json',{'estimated_or_reserved_usd':{p:ledger.spent_for_provider(p) for p in settings},'billed_usd':None})
        build_stock_review('MSFT',reports,OUT/provider/'summary')
    print('FINISHED',flush=True)
if __name__=='__main__':main()
