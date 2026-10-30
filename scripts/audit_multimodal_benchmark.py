"""Offline artifact integrity/coverage audit; no secrets or network needed."""
from pathlib import Path
import hashlib,json,sys,subprocess,zipfile
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/evidence/fair-multimodal-v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links.extend(v for k,v in attrs if k in ('href','src') and v)
def main():
    manifest=read(ROOT/'eval/multimodal-v1/manifest.json');freeze=read(OUT/'freeze.json');profiles=read(OUT/'selected-profiles.json')['selected']
    errors=[];historical_sources=[]
    for name,digest in freeze['sha256'].items():
        path=ROOT/name
        if path.exists() and sha(path)==digest:continue
        if name.startswith('src/claimcheck/'):
            if (OUT/'frozen-source.zip').exists():
                with zipfile.ZipFile(OUT/'frozen-source.zip') as archive:
                    if name in archive.namelist() and hashlib.sha256(archive.read(name)).hexdigest()==digest:
                        historical_sources.append(name)
                        continue
            blob=subprocess.run(['git','show',f"{freeze['revision']}:{name}"],cwd=ROOT,capture_output=True)
            if blob.returncode==0 and hashlib.sha256(blob.stdout).hexdigest()==digest:
                historical_sources.append(name)
                continue
        errors.append('frozen file unavailable or changed: '+name)
    if (OUT/'source-archive.json').exists():
        archive_info=read(OUT/'source-archive.json')
        if sha(OUT/archive_info['archive'])!=archive_info['sha256']:errors.append('source archive hash mismatch')
        with zipfile.ZipFile(OUT/archive_info['archive']) as archive:
            for name,digest in freeze['sha256'].items():
                if name not in archive.namelist() or hashlib.sha256(archive.read(name)).hexdigest()!=digest:errors.append('source archive member mismatch: '+name)
    for case in manifest['cases']:
        if sha(ROOT/case['path'])!=case['sha256']:errors.append('input changed: '+case['id'])
    expected=[]
    for case in manifest['cases']:
        if case['split']=='dev' and case['format'] not in ('txt','png'):continue
        expected.append(OUT/'prepared'/case['id']/'prepared.json')
        for provider in ('meta','baseten','fireworks'):
            choices=('default','low') if case['split']=='dev' else (profiles[provider],)
            expected.extend(OUT/case['split']/provider/profile/case['id']/'ingest.json' for profile in choices)
            if case['split']!='dev' and case['format'] in ('png','jpg','webp'):
                expected.append(OUT/'native-images'/provider/(case['id']+'.json'))
    for p in expected:
        if not p.exists():errors.append('missing planned result: '+str(p.relative_to(OUT)))
        elif read(p).get('status')=='running':errors.append('unknown outcome: '+str(p.relative_to(OUT)))
    ledger=[json.loads(x) for x in (OUT/'ledger.jsonl').read_text().splitlines()]
    reservations={r['reservation_id']:r for r in ledger if r['event']=='reserve'}
    reconciled={r['reservation_id'] for r in ledger if r['event']=='reconcile'}
    unmatched=[r for k,r in reservations.items() if k not in reconciled]
    for p in OUT.glob('prepared/*/prepared.json'):
        for ch in read(p).get('channels',[]):
            for key in ('image','audio'):
                if ch.get(key) and ch.get(key+'_sha256'):
                    source=ROOT/ch[key]
                    if not source.exists() or sha(source)!=ch[key+'_sha256']:errors.append('missing/changed derived media: '+str(source))
    html_links=0
    for path in OUT.rglob('*.html'):
        parser=Links();parser.feed(path.read_text())
        for link in parser.links:
            url=urlsplit(link)
            if url.scheme or url.netloc or not url.path:continue
            html_links+=1
            if not (path.parent/unquote(url.path)).exists():errors.append('broken HTML link: '+str(path.relative_to(OUT))+' -> '+link)
    accounted={};stage_totals={p:{'preprocessing':0.,'text_jobs':0.,'native_images':0.} for p in ('meta','baseten','fireworks')}
    for stage,pattern in [('preprocessing','prepared/*/prepared.json'),('text_jobs','text-cache/*/*/record.json'),('native_images','native-images/*/*.json')]:
        for path in OUT.glob(pattern):
            for rid,attempt in read(path).get('cost_breakdown',{}).get('attempts',{}).items():
                if rid in accounted:errors.append('duplicate accounted reservation: '+rid)
                accounted[rid]=attempt
                stage_totals[attempt['provider']][stage]+=attempt['estimated_usd']
    if set(accounted)!=set(reservations):errors.append('record/ledger reservation IDs differ')
    latest={}
    for event in ledger:latest[event['reservation_id']]=event['amount']
    for rid,attempt in accounted.items():
        if rid not in latest or abs(attempt['estimated_usd']-latest[rid])>1e-8:errors.append('record/ledger cost differs: '+rid)
    summary=read(OUT/'summary.json')
    for provider,cost in summary['actual_estimated_or_reserved_spend_usd'].items():
        if cost>40:errors.append('authorization exceeded: '+provider)
        if abs(sum(stage_totals[provider].values())-cost)>1e-8:errors.append('summary/record costs differ: '+provider)
    inventory=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('inventory.json','audit.json','audit.log')]
    (OUT/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    result={'errors':errors,'historical_source_files_verified_from_archive_or_git':historical_sources,'planned_result_files':len(expected),'local_html_links_checked':html_links,'artifact_files':len(inventory),'artifact_bytes':sum(i['bytes'] for i in inventory),'costs_by_stage_and_provider':stage_totals,'reserved_calls':len(reservations),'reconciled_calls':len(reconciled),'unreconciled_reservations':unmatched,'note':'Unreconciled reservations remain in estimated spend. Inventory excludes itself and audit output; regenerate after final documentation changes.'}
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='unreconciled_reservations'},indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
