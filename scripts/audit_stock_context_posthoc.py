"""Offline audit of both retained stock-context attempts and their one shared cap."""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/stock-context-posthoc-2026-10-30'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in ('href','src') and v)
def main():
    errors=[];accounts={};requests=set();attempts=[]
    for folder in (BASE,BASE/'attempt-2'):
        proof=read(folder/'freeze.json')
        with zipfile.ZipFile(folder/'frozen-source.zip') as archive:
            for name,digest in proof['sha256'].items():
                if name not in archive.namelist() or hashlib.sha256(archive.read(name)).hexdigest()!=digest:errors.append('frozen source mismatch: '+name)
        count=Counter();cost=0.
        for n in (4,5,23):
            source=read(ROOT/f'docs/evidence/fair-multimodal-v1/prepared/REAL-TSLA-{n}/prepared.json')
            r=read(folder/f'REAL-TSLA-{n}/ingest.json');cost+=r['cost_usd']
            if r['status']=='running':errors.append('unknown outcome: '+str(folder))
            if [c.get('normalized_text') for c in r['channels']]!=[c.get('normalized_text') for c in source['channels']]:errors.append('reused text differs')
            for ch in r['channels']:
                for c in ch.get('claims',[]):count[c.get('verdict') or c.get('status','unknown')]+=1
            for rid,record in r['cost_breakdown']['attempts'].items():
                if rid in accounts:errors.append('duplicate reservation accounting: '+rid)
                accounts[rid]=record['estimated_usd']
        for trace in folder.glob('REAL-TSLA-*/checks/*/traces/*.json'):
            requests.update(r['reservation']['reservation_id'] for r in read(trace)['requests'])
        attempts.append({'attempt':1 if folder==BASE else 2,'cost_usd':cost,'claim_occurrences':dict(count),'source_revision':proof['revision']})
    events=[json.loads(line) for line in (BASE/'ledger.jsonl').read_text().splitlines()]
    latest={r['reservation_id']:r for r in events};total=sum(r['amount'] for r in latest.values())
    if set(latest)!=set(accounts) or set(latest)!=requests:errors.append('ledger/account/raw-request IDs differ')
    for rid,amount in accounts.items():
        if rid not in latest or abs(amount-latest[rid]['amount'])>1e-8:errors.append('cost mismatch: '+rid)
    if any(r['provider']!='baseten' for r in events):errors.append('unexpected provider')
    if total>1:errors.append('post-hoc cap exceeded')
    links=0
    for path in BASE.rglob('*.html'):
        parser=Links();parser.feed(path.read_text())
        for link in parser.links:
            url=urlsplit(link)
            if url.scheme or url.netloc or not url.path:continue
            links+=1
            if not (path.parent/unquote(url.path)).exists():errors.append('broken HTML link: '+str(path)+' -> '+link)
    result={'errors':errors,'attempts':attempts,'total_baseten_estimated_or_reserved_usd':total,'shared_posthoc_cap_usd':1,'primary_plus_posthoc_admission_caps_usd':36,'owner_baseten_cap_usd':40,'raw_recorded_requests':len(requests),'local_html_links_checked':links,'note':'Post-hoc known-failure checks; no independent accuracy estimate. Shared OCR was reused, not rerun.'}
    (BASE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    inventory=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(BASE.rglob('*')) if p.is_file() and p.name not in ('inventory.json','audit.json','audit.log')]
    (BASE/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');print(json.dumps(result,indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
