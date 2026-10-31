"""Rebuild live follow-up report and audit offline; never calls a provider."""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,html,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/evidence/real-av-context-live';PROVIDERS=('meta','baseten','fireworks')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    data=read(OUT/'cases.json');cases=data['cases'];errors=[];records=[];costs={};counts={}
    if sha(ROOT/data['replay_source'])!=data['replay_sha256']:errors.append('replay source changed')
    proof=read(OUT/'freeze.json')
    with zipfile.ZipFile(OUT/'frozen-source.zip') as z:
        for name,digest in proof['sha256'].items():
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:errors.append('source archive changed: '+name)
    raw_ids=set();ledger_ids=set();request_count=0
    for provider in PROVIDERS:
        ledger=[json.loads(x) for x in (OUT/provider/'ledger.jsonl').read_text().splitlines()];latest={e['reservation_id']:e for e in ledger};ledger_ids.update(latest)
        cost=round(sum(e['amount'] for e in latest.values()),8);costs[provider]=cost
        if cost>2 or abs(read(OUT/provider/'spend.json')['estimated_or_reserved_usd']-cost)>1e-8:errors.append('provider budget/cost mismatch')
        outcomes=Counter();casecost=0
        for c in cases:
            p=OUT/provider/(c['id']+'.json')
            if not p.exists():errors.append('missing case '+str(p));continue
            r=read(p);casecost+=r['cost_usd']
            if r['input']!=c['input']:errors.append('case input differs: '+str(p))
            if r['status']=='running':errors.append('unfinished case: '+str(p))
            trace=read(OUT/r['trace'])
            for q in trace['requests']:
                request_count+=1;rid=q['reservation']['reservation_id'];raw_ids.add(rid)
                if rid not in latest or abs(q['cost']-latest[rid]['amount'])>1e-8:errors.append('trace/ledger mismatch: '+rid)
            result=r.get('result',{});verdict=result.get('verdict') if r['status']=='completed' else 'failed';outcomes[verdict]+=1
            checks=result.get('program_checks',[])
            if verdict=='supported' and (not checks or any(not q.get('evidence_valid') or q.get('program_verdict')!='supported' for q in checks)):
                errors.append('unsupported supported conclusion: '+str(p))
            records.append({'case':c['id'],'provider':provider,'status':r['status'],'verdict':verdict,'error':r.get('error'),
                'cost_usd':r['cost_usd'],'trace':r['trace'],'result':str(p.relative_to(OUT)),
                'checks':[{'text':q.get('text'),'actual_value':q.get('actual_value'),'evidence_ids':q.get('evidence_ids'),'evidence_valid':q.get('evidence_valid'),'verdict':q.get('program_verdict'),'reason':q.get('reason')} for q in checks]})
        counts[provider]=dict(outcomes)
        if abs(casecost-cost)>1e-8:errors.append('case cost totals differ: '+provider)
    if raw_ids!=ledger_ids:errors.append('raw trace/ledger reservation IDs differ')
    previous=read(ROOT/'docs/evidence/real-av-v1/summary.json')['combined_task_estimated_or_reserved_usd']
    total={p:round(previous[p]+costs[p],8) for p in PROVIDERS}
    if sum(costs.values())>30 or any(v>40 for v in total.values()):errors.append('authorization exceeded')
    summary={'kind':'posthoc same-input verification, not independent accuracy','cases':records,'outcomes':counts,'new_spend_usd':costs,'combined_task_estimated_or_reserved_usd':total,'raw_requests':request_count,'unique_reservations':len(raw_ids),'audit_errors':errors,'budget_note':'Latest owner reply sets $30 combined across all three platforms for this round, subject to prior platform credit ceilings. Execution stayed at $2/provider; combined tracked task totals also remain below the prior $40/provider task authorization. This is not an account balance.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Context-bound real AV: live verification results','','Same six retained claim inputs across three providers: four GAAP table values, event-bound revenue/growth, and an unchanged missing-period adjusted-EPS control. This is a **known-failure post-hoc verification**, not held-out accuracy or a fresh audio/video extraction study. No OCR/ASR was repeated.','','[Preregistered protocol](PROTOCOL.md) · [Frozen inputs and provenance](cases.json) · [Machine results](summary.json) · [Readable case details](results.html)','','| Case | Claim / context | Meta | Baseten | Fireworks |','| --- | --- | --- | --- | --- |']
    for c in cases:
        cells=[]
        for p in PROVIDERS:
            r=next(x for x in records if x['provider']==p and x['case']==c['id']);cells.append(f"[{r['verdict']}]({r['result']})")
        lines.append('| '+c['id']+' | '+c['input']['claim'].replace('|','/')+' | '+' | '.join(cells)+' |')
    lines+=['','Supported means valid program checks within the recorded evidence, period and tolerance. It remains conditional on the reviewed event context. It does not authenticate the speaker, certify the entire video, resolve every table column or validate adjusted EPS. Failures remain failures and are not scored as wrong financial answers. The six cases are not an independent gold accuracy denominator.','','## Spend (USD, estimated/reserved)','','| Platform | New follow-up | Combined task |','| --- | ---: | ---: |']
    for p in PROVIDERS:lines.append(f'| {p} | {costs[p]:.8f} | {total[p]:.8f} |')
    lines+=['','The latest owner reply sets $30 combined across all three platforms for this round, subject to prior platform credit ceilings; see budget-note.json. The execution caps remained $2 per platform. Failed attempts and unreconciled reservations remain counted. No invoice or account balance is inferred. Original real-AV and admission-replay records are unchanged.','','## Reuse','','Run `python3 scripts/report_event_context_live.py` for an offline report/audit rebuild. Do not rerun the paid runner to inspect results; it deliberately refuses an existing freeze marker. Every result links its full raw request/response/tool trace. Source code is archived in frozen-source.zip. [Chinese analysis](ANALYSIS.zh-TW.md) describes what improved and what still blocks verification.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    esc=lambda x:html.escape(str(x));cards=[]
    for c in cases:
        cards.append('<section><h2>'+c['id']+'</h2><blockquote>'+esc(c['input']['quote'])+'</blockquote><p>Checked as: '+esc(c['input']['claim'])+'</p><details><summary>Separate period provenance</summary><pre>'+esc(json.dumps(c['input'],indent=2))+'</pre></details>')
        for p in PROVIDERS:
            r=next(x for x in records if x['case']==c['id'] and x['provider']==p)
            original=read(OUT/r['result']);message=original.get('result',{}).get('summary') or original.get('error')
            cards.append('<h3>'+p+': '+esc(r['verdict'])+'</h3><p>'+esc(message)+'</p><a href="'+r['result']+'">Recorded result</a> · <a href="'+r['trace']+'">Full trace</a><pre>'+esc(json.dumps(r['checks'],indent=2))+'</pre>')
        cards.append('</section>')
    (OUT/'results.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Context-bound verification</title><style>body{max-width:1050px;margin:32px auto;padding:20px;font:16px/1.55 system-ui}pre{white-space:pre-wrap}section{border-top:1px solid #bbb;padding:20px 0}</style><h1>Context-bound real AV verification</h1><p>Post-hoc known-failure check. Conditional on separately reviewed event periods. No new audio/visual reading; not a whole-video certificate.</p>'+''.join(cards)+'</html>')
    print(json.dumps({'outcomes':counts,'costs':costs,'raw_requests':request_count,'errors':errors},indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
