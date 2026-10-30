"""Offline report of real webcast probes; token presence is not semantic accuracy."""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,re,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/evidence/real-av-v1';DATA=ROOT/'eval/real-av-v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in ('src','href') and v)
def main():
    manifest=read(DATA/'manifest.json');targets=Counter(str(t['value']) for t in manifest['reference_targets']);rows=[];errors=[];accounted={}
    for item in manifest['inputs']:
        if sha(ROOT/item['path'])!=item['sha256']:errors.append('input mismatch: '+item['path'])
    freeze=read(OUT/'freeze.json')
    with zipfile.ZipFile(OUT/'frozen-source.zip') as z:
        for name,digest in freeze['sha256'].items():
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:errors.append('source archive mismatch: '+name)
    for provider in ('meta','baseten','fireworks'):
        for fmt in ('wav','mp4'):
            p=OUT/provider/fmt/'ingest.json'
            if not p.exists():errors.append('missing case: '+str(p));continue
            r=read(p);chs=r['channels']
            input_row=next(x for x in manifest['inputs'] if x['path'].endswith('.'+fmt))
            if r['input']['sha256']!=input_row['sha256']:errors.append('case input differs: '+str(p))
            for ch in chs:
                for key in ('audio','image'):
                    if ch.get(key):
                        media=p.parent/ch[key]
                        if not media.exists():errors.append('missing decoded media: '+str(media));continue
                        expected=ch.get(key+'_sha256') or ch.get('image_info',{}).get('sha256')
                        if expected and sha(media)!=expected:errors.append('decoded media changed: '+str(media))
            audio=[c for c in chs if c['kind']=='transcript'];text='\n'.join(c.get('normalized_text','') for c in audio)
            nums=Counter(re.findall(r'\d+(?:\.\d+)?',text.replace(',','')))
            claims=[c for ch in chs for c in ch.get('claims',[])];verdicts=Counter(c.get('verdict') or c.get('status','unknown') for c in claims)
            rows.append({'provider':provider,'format':fmt,'status':r['status'],'audio_reference_numeric_tokens_found':sum((nums&targets).values()),'reference_numeric_tokens':sum(targets.values()),'numeric_tokens_missing':list((targets-nums).elements()),'channels':[{'id':c['id'],'kind':c['kind'],'claims':len(c.get('claims',[])),'error':c.get('error'),'sample_ms':c.get('sample_ms')} for c in chs], 'coverage':r['coverage'],'verdicts':dict(verdicts),'estimated_cost_usd':r['cost_usd'],'seconds':r['wall_clock_s'],'report':str(p.relative_to(OUT))})
            for rid,record in r['cost_breakdown']['attempts'].items():
                if rid in accounted:errors.append('duplicate cost reservation: '+rid)
                accounted[rid]=record['estimated_usd']
            if r['status']=='running':errors.append('unfinished case: '+str(p))
    latest={};reserve=set()
    for line in (OUT/'ledger.jsonl').read_text().splitlines():
        e=json.loads(line)
        # Same ledger event schema as the paired benchmark.
        rid=e['reservation_id'];latest[rid]=e
        if e.get('event')=='reserve':reserve.add(rid)
    if set(accounted)!=reserve:errors.append('case/ledger reservation IDs differ')
    for rid,cost in accounted.items():
        if rid not in latest or abs(cost-latest[rid]['amount'])>1e-8:errors.append('case/ledger cost differs: '+rid)
    raw_ids=set()
    def collect(obj):
        if isinstance(obj,dict):
            if obj.get('reservation_id'):raw_ids.add(obj['reservation_id'])
            for v in obj.values():collect(v)
        elif isinstance(obj,list):
            for v in obj:collect(v)
    for p in OUT.rglob('*.json'):
        if 'calls' in p.parts or 'traces' in p.parts:collect(read(p))
    if raw_ids!=reserve:errors.append('raw request/ledger reservation IDs differ')
    spend=read(OUT/'spend.json')
    for provider,cost in spend['estimated_or_reserved_usd'].items():
        if abs(sum(e['amount'] for e in latest.values() if e['provider']==provider)-cost)>1e-8:errors.append('spend/ledger total differs: '+provider)
    prior=read(ROOT/'docs/evidence/fair-multimodal-v1/task-spend.json')['total_task_estimated_or_reserved_usd']
    combined={p:round(prior[p]+v,8) for p,v in spend['estimated_or_reserved_usd'].items()}
    if any(v>40 for v in combined.values()):errors.append('combined authorization exceeded')
    links=0
    for p in OUT.rglob('*.html'):
        parser=Links();parser.feed(p.read_text())
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            links+=1
            if not (p.parent/unquote(u.path)).exists():errors.append('broken HTML link: '+str(p)+' '+link)
    summary={'cases':rows,'new_spend':spend,'combined_task_estimated_or_reserved_usd':combined,'numeric_metric_note':'Multiset numeric-token presence against publisher-caption reference; not word error rate, metric/period alignment, verdict accuracy, or independent gold. WAV and MP4 share one scene.','audit_errors':errors,'local_html_links_checked':links,'raw_request_reservations':len(raw_ids)}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Real Microsoft webcast audio/video results','','One genuine CFO segment, 60 seconds (source 18:14–19:14), tested as WAV and MP4 across three text routes. Audio and visuals originate in the official webcast; no synthetic narration or replacement slides. This is a six-run **smoke test on one scene**, not six independent examples or a provider accuracy ranking.','','[Inputs and preregistered protocol](../../../eval/real-av-v1/README.md) · [Exact media/source manifest](../../../eval/real-av-v1/manifest.json) · [Publisher caption reference](../../../eval/real-av-v1/caption-reference.json) · [Machine results](summary.json)','','| Route / format | Pipeline | Caption numeric tokens found* | Proposed / program-checked | Recorded outcomes | Cost USD |','| --- | --- | ---: | ---: | --- | ---: |']
    for r in rows:
        c=r['coverage'];lines.append(f"| [{r['provider']} / {r['format']}]({r['provider']}/{r['format']}/ingest.html) | {r['status']} | {r['audio_reference_numeric_tokens_found']}/11 | {c['proposed_claims']} / {c['program_checked_claims']} | {r['verdicts']} | {r['estimated_cost_usd']:.6f} |")
    lines+=['','*Numeric presence checks 11 reference occurrences including repeated values; it does not prove the number belongs to the correct metric, period or accounting basis. Captions are publisher reference material, not independently reviewed gold. No word error rate or financial accuracy score is claimed.','','## What this exercises','','- Each case makes fresh Meta ASR calls; MP4 also uses three sampled Meta OCR frames. Raw media requests/responses, normalized text and model/tool traces are retained under each case. Fresh preprocessing may vary, so this does not isolate verifier differences like the earlier frozen-preprocessing benchmark.','- One source scene becomes two encodings. The clip has genuine speech over financial slides, not fast-moving footage or multiple visible speakers. It does not measure long-call recall, speaker identity, or audio/video synchronization.','- Four proposals per extraction window/channel are selected; bounded extraction cannot promise all eleven spoken numeric mentions are checked. Failed, rejected and insufficient results remain public.','- One Baseten WAV model narrative claims the operating margin is contradicted using other periods, but the final program verdict is insufficient_evidence with unchecked_other_claim. That narrative is not a validated correction; see the retained result and Chinese diagnosis.',
        '- The speaker discusses adjusted EPS $4.89 while the displayed GAAP table shows $4.92. Those differing bases are not automatically a contradiction. The current pipeline checks audio and frames separately; it does not reconcile them.','- The audio says “this quarter”; the source FY27 Q1 label is preserved as metadata but not injected into the transcript. Missing explicit periods must fail closed. Video frames contain their own period headers.','- Frozen SEC evidence is used without network fetching. Missing release, constant-currency or adjusted-metric evidence is an expected product limitation; this suite does not prove those claims false.','','## Cost and reuse','','All amounts are estimates/reservations, not invoices or remaining account balances. Shared preprocessing is charged to Meta. Costs include recorded failures and transient retries. New caps are Meta $3, Baseten $2, Fireworks $2; combined task totals remain under $40 each.','','| Platform | New suite USD | Combined task USD |','| --- | ---: | ---: |']
    for p,v in spend['estimated_or_reserved_usd'].items():lines.append(f'| {p} | {v:.8f} | {combined[p]:.8f} |')
    lines+=['','Run `python3 scripts/report_real_av.py` to rebuild this report offline. Do not rerun the paid runner merely to inspect results. Each original clip offset is 1094 seconds: add it to the per-clip ASR/frame times to find the source-webcast location. ASR timestamps describe turns, not verified word timestamps.','','The original short media files and all decoded media used by the pipeline are retained. Microsoft retains rights to webcast/slide content; media excerpts are not relicensed under MIT. No signed player URLs or credentials are needed to inspect committed inputs.','','[Meta stock summary](meta/summary/stock-review.html) · [Baseten stock summary](baseten/summary/stock-review.html) · [Fireworks stock summary](fireworks/summary/stock-review.html)','','See [Chinese findings and next steps](ANALYSIS.zh-TW.md) for the completed case diagnosis.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'cases':len(rows),'errors':errors,'spend':spend,'combined':combined},indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
