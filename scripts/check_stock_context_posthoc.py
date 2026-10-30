"""Paid post-hoc product check; frozen OCR reused, primary benchmark unchanged."""
import argparse,copy,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from claimcheck.budget import Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.release_fetch import ReleaseClient
from claimcheck.providers import create_client
from claimcheck.post import check_post
from claimcheck.ingest import _InputLedger,attach_locations,coverage_summary,channel_stages,aggregate_stages,render_html
from claimcheck.ingest_media import write_json,sha256
from claimcheck.stock_review import build_stock_review
OUT=ROOT/'docs/evidence/stock-context-posthoc-2026-10-30'
def offline(url):raise RuntimeError('No live SEC fetching in this post-hoc check')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence-cache',type=Path,required=True);args=parser.parse_args()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=[*sorted((ROOT/'src/claimcheck').glob('*.py')),Path(__file__).resolve(),ROOT/'docs/STOCK_DOCUMENT_CONTEXT.md']
    hashes={}
    for path in files:
        rel=str(path.relative_to(ROOT));blob=subprocess.run(['git','show',f'{revision}:{rel}'],cwd=ROOT,capture_output=True)
        if blob.returncode or blob.stdout!=path.read_bytes():raise ValueError('commit new product code/protocol before calls: '+rel)
        hashes[rel]=sha256(path)
    source_manifest=ROOT/'docs/evidence/sec-refresh-2026-10-30/manifest.json'
    for item in json.loads(source_manifest.read_text())['files']:
        if sha256(args.evidence_cache/item['file'])!=item['sha256']:raise ValueError('SEC snapshot mismatch')
    prepared=[ROOT/'docs/evidence/fair-multimodal-v1/prepared'/f'REAL-TSLA-{n}'/'prepared.json' for n in (4,5,23)]
    hashes.update({str(p.relative_to(ROOT)):sha256(p) for p in prepared})
    freeze=OUT/'freeze.json'
    proof={'revision':revision,'sha256':hashes,'provider':'baseten','ticker_hint':'TSLA','max_proposals_per_window':4,'max_output_tokens':4000,'extraction_reasoning_effort':'low','verification_reasoning_effort':'low','budget_usd':1,'scope':'Post-hoc product smoke check on known failures. Frozen Meta OCR reused; no new OCR/ASR and no independent accuracy claim. Primary benchmark unchanged.'}
    if freeze.exists():
        if json.loads(freeze.read_text())['sha256']!=hashes:raise ValueError('post-hoc frozen source changed')
    else:write_json(freeze,proof)
    s=load_settings(provider='baseten')
    if not s.model_api_key:raise ValueError('Baseten key missing')
    client=create_client('baseten',s.model_api_key).with_options(max_retries=0,timeout=120)
    ledger=Ledger(OUT/'ledger.jsonl',budget_usd=1,provider_budgets={'baseten':1})
    reports=[]
    for path in prepared:
        source=json.loads(path.read_text());dest=OUT/source['case']['id'];target=dest/'ingest.json';reports.append(target)
        if target.exists():continue
        if dest.exists():raise ValueError('unknown previous outcome; no automatic retry')
        dest.mkdir(parents=True);account=_InputLedger(ledger);start=time.perf_counter();channels=copy.deepcopy(source['channels']);errors=[]
        for ch in channels:
            if not ch.get('normalized_text') or ch.get('error'):continue
            post_dir=dest/'checks'/ch['id']
            try:
                r=check_post(ch['normalized_text'],client=client,edgar=EdgarClient(args.evidence_cache,fetcher=offline,as_of='2026-10-30'),release_client=ReleaseClient(args.evidence_cache,fetcher=offline),ledger=account,model=s.model,provider='baseten',out_dir=post_dir,max_claims=4,max_output_tokens=4000,extraction_max_output_tokens=4000,reasoning_effort='low',extraction_reasoning_effort='low',source_ticker='TSLA',bounded_extraction=True,allow_long_input=True,secrets=[s.model_api_key])
                ch.update(claims=r['claims'],extraction_scope=r['extraction_scope'],source_context=r['source_context'],post_report=str((post_dir/'report.html').relative_to(dest)))
                attach_locations(ch,ch['claims'])
                if any(c.get('status')=='failed' for c in ch['claims']):ch['error']='one or more claims failed'
            except Exception as exc:ch['error']=f'{type(exc).__name__}: {str(exc)[:500]}'
            ch['stages']=channel_stages(ch)
        r={'schema_version':1,'input':{'file':source['case']['path'],'kind':source['kind'],'sha256':source['case']['sha256']},'provider':'baseten','model':s.model,'source_context':{'ticker_hint':'TSLA','authenticated':False},'channels':channels,'errors':errors,'status':'partial' if any(c.get('error') for c in channels) else 'completed','cost_usd':account.spent_total,'cost_breakdown':account.cost_summary(),'wall_clock_s':round(time.perf_counter()-start,3),'coverage':coverage_summary(channels),'stages':aggregate_stages(channels,'',source['kind']),'limitations':['Post-hoc known-failure product check; no independent accuracy denominator.','Reuses frozen Meta OCR; this does not retest OCR or ASR.','User-supplied TSLA context is not issuer authentication.','Bounded extraction selects at most four claims per window; unselected content remains unchecked.']}
        write_json(target,r,[s.model_api_key]);(dest/'ingest.html').write_text(render_html(r));print(source['case']['id'],r['status'],r['coverage'],flush=True)
    if not (OUT/'summary/stock-review.json').exists():build_stock_review('TSLA',reports,OUT/'summary')
    write_json(OUT/'spend.json',{'baseten_estimated_or_reserved_usd':ledger.spent_for_provider('baseten'),'posthoc_cap_usd':1,'combined_admission_caps_usd':{'primary_baseten':35,'posthoc_baseten':1},'owner_total_baseten_cap_usd':40,'billed_usd':None})
if __name__=='__main__':main()
