"""Preregistered paired multimodal benchmark. Each provider has a $40 authorization;
$35 admission ceilings leave reconciliation margin. All stages share one ledger.
"""
from __future__ import annotations
import argparse,base64,copy,hashlib,json,mimetypes,os,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(DATA))
import httpx
from claimcheck.budget import Ledger,BudgetExceeded
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.ingest import _InputLedger,prepare_text,attach_locations,coverage_summary,channel_stages,aggregate_stages,render_html
from claimcheck.ingest_media import decode,read_image,transcribe,write_json,sha256,OCR_PROMPT
from claimcheck.post import check_post
from claimcheck.providers import create_client,get_provider,default_model
from claimcheck.release_fetch import ReleaseClient
from score import score
PROVIDERS=('meta','baseten','fireworks')
OUT=ROOT/'docs/evidence/fair-multimodal-v1'
CACHE=ROOT/'.cache/sec-refresh-2026-10-30'
LOCKS={};LOCK_GUARD=threading.Lock()


def offline(url):raise RuntimeError('SEC source missing from frozen snapshot; no live fetch permitted')
def stamp():return datetime.now(timezone.utc).isoformat()
def digest_text(text):return hashlib.sha256(text.encode()).hexdigest()
def own_lock(key):
    with LOCK_GUARD:return LOCKS.setdefault(key,threading.Lock())


def freeze():
    manifest=json.loads((DATA/'manifest.json').read_text());gold=json.loads((DATA/'gold.json').read_text())
    if sha256(DATA/'gold.json')!=manifest['gold_sha256']:raise ValueError('gold changed')
    for case in manifest['cases']:
        if sha256(ROOT/case['path'])!=case['sha256']:raise ValueError('input changed')
    if sha256(ROOT/manifest['source_manifest'])!=manifest['source_manifest_sha256']:raise ValueError('evidence manifest changed')
    evidence=json.loads((ROOT/manifest['source_manifest']).read_text())
    for item in evidence['files']:
        if sha256(CACHE/item['file'])!=item['sha256']:raise ValueError('SEC snapshot changed')
    files=[DATA/'manifest.json',DATA/'gold.json',*DATA.glob('*.py'),*sorted((ROOT/'src/claimcheck').glob('*.py')),*sorted((ROOT/'prompts').glob('*.md')),ROOT/'uv.lock']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for path in files:
        rel=str(path.relative_to(ROOT));committed=subprocess.run(['git','show',f'{revision}:{rel}'],cwd=ROOT,capture_output=True)
        if committed.returncode or committed.stdout!=path.read_bytes():raise ValueError(f'commit frozen code/data before spending: {rel}')
        hashes[rel]=sha256(path)
    proof={'revision':revision,'sha256':hashes,'input_manifest_sha256':sha256(DATA/'manifest.json'),'evidence_manifest_sha256':sha256(ROOT/manifest['source_manifest'])}
    if (OUT/'freeze.json').exists():
        old=json.loads((OUT/'freeze.json').read_text())
        if old['sha256']!=hashes:raise ValueError('frozen code changed; no resumed spend')
    else:write_json(OUT/'freeze.json',proof)
    return manifest,{d['id']:d for d in gold}


def ledger():return Ledger(OUT/'ledger.jsonl',budget_usd=105,provider_budgets={p:35 for p in PROVIDERS})
def settings(provider):
    s=load_settings(provider=provider)
    if not s.model_api_key:raise ValueError(f'{provider} key missing')
    return s

def prepare(case):
    dest=OUT/'prepared'/case['id'];target=dest/'prepared.json'
    if target.exists():return json.loads(target.read_text())
    if dest.exists():raise ValueError(f'unknown preprocessing outcome: {case["id"]}')
    dest.mkdir(parents=True);account=_InputLedger(ledger());start=time.perf_counter()
    state={'case':case,'status':'running','started_at':stamp(),'channels':[],'errors':[]}
    write_json(target,state)
    try:
        kind,channels=decode(ROOT/case['path'],dest/'media');state['kind']=kind
        meta=settings('meta');client=create_client('meta',meta.model_api_key).with_options(max_retries=0,timeout=120)
        with httpx.Client(timeout=120) as http:
          for channel in channels:
            try:
              if not channel['decoded']:state['channels'].append(channel);continue
              if channel['kind']=='transcript':
                account.stage='asr';channel['segments'],_=transcribe(channel,http=http,api_key=meta.model_api_key,ledger=account,record=dest/'calls'/f"{channel['id']}.json")
              elif channel['kind'] in ('ocr','frame'):
                account.stage='ocr';channel['segments'],_=read_image(channel,client=client,ledger=account,record=dest/'calls'/f"{channel['id']}.json",secrets=[meta.model_api_key])
              prepare_text(channel)
            except Exception as exc:channel['error']=f'{type(exc).__name__}: {str(exc)[:300]}'
            state['channels'].append(channel);write_json(target,state,[meta.model_api_key])
        state['status']='partial' if any(ch.get('error') for ch in state['channels']) else 'completed'
    except Exception as exc:state.update(status='failed',errors=[f'{type(exc).__name__}: {str(exc)[:300]}'])
    state.update(cost_usd=account.spent_total,cost_breakdown=account.cost_summary(),wall_clock_s=round(time.perf_counter()-start,3),finished_at=stamp())
    # Derived WAVs/frames are retained locally and referenced by hash; original inputs are committed.
    for ch in state['channels']:
        for key in ('audio','image'):
            if ch.get(key):
                path=Path(ch[key]);ch[key+'_sha256']=sha256(path);ch[key]=str(path.relative_to(ROOT))
    write_json(target,state,[settings('meta').model_api_key]);print('prepared',case['id'],state['status'],flush=True);return state


def text_check(provider,profile,text):
    key=digest_text(provider+'\n'+profile+'\n'+text);dest=OUT/'text-cache'/provider/key
    with own_lock(provider+key):
        result_path=dest/'record.json'
        if result_path.exists():
            old=json.loads(result_path.read_text());return old,True
        if dest.exists():return {'status':'unknown_previous_outcome','claims':[],'cost_usd':0,'wall_clock_s':0,'path':str(dest.relative_to(OUT))},True
        dest.mkdir(parents=True);s=settings(provider);client=create_client(provider,s.model_api_key).with_options(max_retries=0,timeout=120)
        account=_InputLedger(ledger());started=time.perf_counter()
        try:
            result=check_post(text,client=client,edgar=EdgarClient(CACHE,fetcher=offline,as_of='2026-10-30'),ledger=account,
                model=s.model,provider=provider,out_dir=dest,max_claims=8,max_output_tokens=4000,extraction_max_output_tokens=4000,
                reasoning_effort=None if profile=='default' else 'low',release_client=ReleaseClient(CACHE,fetcher=offline),
                secrets=[s.model_api_key],allow_long_input=True)
            status='completed' if not any(c.get('status')=='failed' for c in result['claims']) else 'partial'
        except Exception as exc:result={'claims':[],'error':f'{type(exc).__name__}: {str(exc)[:300]}'};status='failed'
        record={'status':status,'claims':result.get('claims',[]),'error':result.get('error'),'cost_usd':account.spent_total,
                'wall_clock_s':round(time.perf_counter()-started,3),'cost_breakdown':account.cost_summary(),
                'path':str(dest.relative_to(OUT)),'text_sha256':digest_text(text),'provider':provider,'profile':profile,
                'model':s.model,'text':text}
        write_json(result_path,record,[s.model_api_key]);return record,False


def run_case(case,provider,profile,phase,gold):
    dest=OUT/phase/provider/profile/case['id'];target=dest/'ingest.json'
    if target.exists():return json.loads(target.read_text())
    prepared=json.loads((OUT/'prepared'/case['id']/'prepared.json').read_text())
    if prepared['status']=='running':raise ValueError('preprocessing not finished')
    dest.mkdir(parents=True,exist_ok=True);start=time.perf_counter();channels=copy.deepcopy(prepared['channels']);fresh=0.;logical=0.;reuse=[]
    for channel in channels:
        if channel.get('error') or not channel.get('normalized_text'):continue
        record,cached=text_check(provider,profile,channel['normalized_text']);channel['claims']=copy.deepcopy(record['claims'])
        attach_locations(channel,channel['claims']);channel['text_record']=record['path']+'/record.json'
        channel['post_report']=os.path.relpath(OUT/record['path']/'report.html',dest)
        channel['text_reused']=cached;logical+=record['cost_usd'];fresh+=0 if cached else record['cost_usd']
        if record['status']!='completed':channel['error']=record.get('error') or record['status']
        reuse.append({'path':record['path'],'reused':cached,'cost_usd':record['cost_usd'],'seconds':record['wall_clock_s']})
    for ch in channels:ch['stages']=channel_stages(ch)
    state={'schema_version':1,'case_id':case['id'],'input':{'file':case['path'],'kind':prepared.get('kind'),'sha256':case['sha256']},
           'provider':provider,'model':default_model(provider),'profile':profile,'channels':channels,'errors':prepared['errors'],
           'status':'partial' if any(ch.get('error') for ch in channels) or prepared['errors'] else 'completed',
           'coverage':coverage_summary(channels),'stages':aggregate_stages(channels,'; '.join(prepared['errors']),prepared.get('kind')),
           'cost_usd':fresh,'shared_preprocessing_usd':prepared['cost_usd'],'replay_text_unit_cost_usd':logical,
           'workflow_unit_cost_usd':logical+prepared['cost_usd'],'wall_clock_s':round(time.perf_counter()-start,3),
           'shared_preprocessing_seconds':prepared['wall_clock_s'],'text_reuse':reuse,'score':score(gold,channels),
           'limitations':['Shared frozen Meta preprocessing; not native provider audio/video.','Fresh text calls and reused text records are distinguished.','Format encodings repeat the same underlying claims.']}
    write_json(target,state)
    # Use the standard renderer's expected top-level policy/cost fields where optional.
    rendered=render_html(state)
    for channel in channels:
        if channel.get('text_record'):
            prefix=os.path.relpath((OUT/channel['text_record']).parent,dest)
            rendered=rendered.replace(f"checks/{channel['id']}/",prefix+'/')
    (dest/'ingest.html').write_text(rendered)
    print(phase,provider,profile,case['id'],state['score']['correct'],'/',len(gold),flush=True);return state


def run_pairs(cases,profiles,phase,docs):
    results=[]
    def provider_jobs(provider):
        jobs=[(c,p) for p in profiles[provider] for c in cases]
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(run_case,c,provider,p,phase,([] if c['split']=='diagnostic' else docs[c['document']]['gold'])) for c,p in jobs]
            return [f.result() for f in as_completed(futures)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for rows in pool.map(provider_jobs,PROVIDERS):results.extend(rows)
    return results


def native(case,provider,profile):
    target=OUT/'native-images'/provider/(case['id']+'.json')
    if target.exists():return
    s=settings(provider);client=create_client(provider,s.model_api_key).with_options(max_retries=0,timeout=120)
    path=ROOT/case['path'];mime=mimetypes.guess_type(path.name)[0];uri=f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()
    if provider=='meta':
        request={'model':s.model,'instructions':OCR_PROMPT,'input':[{'role':'user','content':[{'type':'input_text','text':'Read this image verbatim.'},{'type':'input_image','image_url':uri}]}],'max_output_tokens':3000}
        if profile=='low':request['reasoning']={'effort':'low'}
    else:
        request={'model':s.model,'messages':[{'role':'system','content':OCR_PROMPT},{'role':'user','content':[{'type':'text','text':'Read this image verbatim.'},{'type':'image_url','image_url':{'url':uri}}]}],'max_tokens':3000}
        if profile=='low':request['reasoning_effort']='low'
    account=_InputLedger(ledger());account.stage='native_image_reading';start=time.perf_counter()
    safe=json.loads(json.dumps(request).replace(uri,f'[media sha256={case["sha256"]}; path={case["path"]}]'))
    record={'case':case,'provider':provider,'profile':profile,'request':safe,'status':'running','started_at':stamp()};write_json(target,record)
    try:
        res=account.reserve(request,model=s.model,provider=provider,max_output_tokens=3000)
        result=get_provider(provider).call(client,request);account.reconcile(res,result.usage)
        raw=result.raw_response;raw=raw.model_dump(mode='json') if hasattr(raw,'model_dump') else raw
        record.update(status=result.status,text=result.text,response=raw,usage=result.usage)
    except Exception as exc:record.update(status='failed',error=f'{type(exc).__name__}: {str(exc)[:800]}')
    record.update(cost_usd=account.spent_total,cost_breakdown=account.cost_summary(),wall_clock_s=round(time.perf_counter()-start,3),finished_at=stamp())
    write_json(target,record,[s.model_api_key]);print('native',provider,case['id'],record['status'],flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','dev','test','native','diagnostic','all']);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);manifest,docs=freeze();cases=manifest['cases']
    if args.phase in ('prepare','all'):
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(prepare,[c for c in cases if c['split']!='dev' or c['format'] in ('txt','png')]))
    if args.phase in ('dev','all'):
        dev=[c for c in cases if c['split']=='dev' and c['format'] in ('txt','png')]
        results=run_pairs(dev,{p:['default','low'] for p in PROVIDERS},'dev',docs)
        selected={};details={}
        for provider in PROVIDERS:
            options={}
            for profile in ('default','low'):
                rows=[r for r in results if r['provider']==provider and r['profile']==profile]
                options[profile]={'correct':sum(r['score']['correct'] for r in rows),'false_supported':sum(r['score']['false_supported'] for r in rows),'unit_cost_usd':sum(r['workflow_unit_cost_usd'] for r in rows),'cases':len(rows)}
            selected[provider]=min(options,key=lambda p:(-options[p]['correct'],options[p]['false_supported'],options[p]['unit_cost_usd'],p));details[provider]=options
        write_json(OUT/'selected-profiles.json',{'selected':selected,'dev_results':details,'selected_at':stamp(),'rule':'correct desc, false-supported asc, cost asc, profile name; no test results used'})
    if args.phase in ('test','native','diagnostic','all'):
        profiles=json.loads((OUT/'selected-profiles.json').read_text())['selected']
        test=[c for c in cases if c['split']=='test']
        if args.phase in ('test','all'):run_pairs(test,{p:[profiles[p]] for p in PROVIDERS},'test',docs)
        if args.phase in ('diagnostic','all'):run_pairs([c for c in cases if c['split']=='diagnostic'],{p:[profiles[p]] for p in PROVIDERS},'diagnostic',docs)
        if args.phase in ('native','all'):
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures=[pool.submit(native,c,p,profiles[p]) for c in [*test,*[x for x in cases if x['split']=='diagnostic']] if c['format'] in ('png','jpg','webp') for p in PROVIDERS]
                for f in as_completed(futures):f.result()
    write_json(OUT/'spend.json',{'estimated_or_reserved_usd':{p:ledger().spent_for_provider(p) for p in PROVIDERS},'admission_ceiling_per_provider_usd':35,'owner_ceiling_per_provider_usd':40,'billed_usd':None})
if __name__=='__main__':main()
