"""Offline, post-hoc admission replay; never produces new financial verdicts."""
from pathlib import Path
import hashlib,html,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from claimcheck.event_context import validate_event_context
from claimcheck.period_context import missing_period_reason
from claimcheck.post import screen_claims
from claimcheck.program_summary import program_summary
OUT=ROOT/'docs/evidence/real-av-context-posthoc';BASE=ROOT/'docs/evidence/real-av-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    context=validate_event_context(json.loads((OUT/'event-context.json').read_text()),'MSFT')
    cases=[];sources={}
    for p in sorted(BASE.glob('*/*/ingest.json')):
        r=json.loads(p.read_text());sources[str(p.relative_to(ROOT))]=sha(p)
        for ch in r['channels']:
            proposals=[{'quote':c['quote'],'claim':c.get('extracted_claim',c['claim']),'ticker':c['ticker'],'kind':c['kind']} for c in ch.get('claims',[])]
            if not proposals:continue
            before=screen_claims(ch['normalized_text'],proposals)
            after=screen_claims(ch['normalized_text'],proposals,event_context=context)
            cases.append({'provider':r['provider'],'format':p.parent.name,'channel':ch['id'],
                'archived_report':str(p.relative_to(ROOT)),
                'before_rejected':sum(c['status']=='rejected' for c in before),
                'after_rejected':sum(c['status']=='rejected' for c in after),
                'event_bound':sum(bool(c.get('event_period_context')) for c in after),
                'header_bound':sum(bool(c.get('header_period_bindings')) for c in after),
                'after':after,'new_financial_verdicts':None})
    r=json.loads((BASE/'baseten/wav/ingest.json').read_text());c=r['channels'][0]['claims'][-1]
    data={'kind':'post-hoc deterministic admission replay; not verification or accuracy','new_api_cost_usd':0,
        'sources_sha256':sources,'context':context,'cases':cases,
        'summary_example':{'original_model_text':c['summary'],'program_verdict':c['verdict'],'safe_summary':program_summary(c['verdict'],c['program_checks'])},
        'implementation_sha256':{name:sha(ROOT/name) for name in ('src/claimcheck/event_context.py','src/claimcheck/program_summary.py','src/claimcheck/post.py','src/claimcheck/agent.py','src/claimcheck/ingest.py','src/claimcheck/job_queue.py','src/claimcheck/cli.py','src/claimcheck/stock_review.py','scripts/replay_event_context.py')}}
    (OUT/'replay.json').write_text(json.dumps(data,indent=2)+'\n')
    esc=html.escape
    rows=''.join(f"<tr><td>{esc(c['provider'])} / {esc(c['format'])} / {esc(c['channel'])}</td><td>{c['before_rejected']} → {c['after_rejected']}</td><td>{c['event_bound']}</td><td>{c['header_bound']}</td></tr>" for c in cases)
    body='<h1>Real AV: period context admission replay</h1><p>Offline known-failure replay. No new financial verdicts and no API spend. Admission to verification is not proof that a claim is correct. Original records remain unchanged.</p><table><tr><th>Case</th><th>Rejected before → after</th><th>Event period bindings</th><th>Header bindings</th></tr>'+rows+'</table><h2>Final explanation from program checks</h2><p>'+esc(data['summary_example']['safe_summary'])+'</p><details><summary>Archived model narrative — unvalidated, not the final conclusion</summary><pre>'+esc(c['summary'])+'</pre></details>'
    body+='<p>Context is reviewed metadata, not authenticated issuer evidence. Header presence does not prove column alignment. Other-company, wrong-period, invented-number and unanchored-century cases remain guarded.</p><p><a href="replay.json">Inputs, preserved quotations, context provenance and source hashes</a> · <a href="REPORT.md">Methodology and next steps</a></p>'
    (OUT/'replay.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Period context replay</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:32px auto;padding:20px}td,th{padding:8px;border-bottom:1px solid #ccc}pre{white-space:pre-wrap}</style>'+body+'</html>')
    print(json.dumps({'cases':len(cases),'rejected_before':sum(c['before_rejected'] for c in cases),'rejected_after':sum(c['after_rejected'] for c in cases),'event_bindings':sum(c['event_bound'] for c in cases),'header_bindings':sum(c['header_bound'] for c in cases),'new_financial_verdicts':0}))
if __name__=='__main__':main()
