"""Evidence-linked, single-stock summaries of retained ingestion reports.

No model calls: aggregate recorded checks without inventing investment ratings.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re


def build_stock_review(ticker: str, reports: list[Path], out: Path, *, pending_documents: list[dict] | None = None) -> dict:
    ticker=ticker.strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,9}',ticker):
        raise ValueError('provide a valid US ticker')
    if not reports and not pending_documents: raise ValueError('provide at least one retained ingestion report')
    if (out/'stock-review.json').exists(): raise ValueError('summary already exists; choose a new output directory')
    documents=[];claims=[];others=[];unassigned=[];seen=set()
    for source in reports:
        raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest in seen: raise ValueError('duplicate report content; each source must be supplied once')
        seen.add(digest);report=json.loads(raw)
        if not isinstance(report.get('channels'),list):raise ValueError('expected an ingestion report with channels')
        doc_id=f'D{len(documents)+1:03d}'
        documents.append({'id':doc_id,'input':report.get('input',{}),'status':report.get('status','unknown'),
                          'report_sha256':digest,'report':os.path.relpath(source.resolve(),out.resolve()),
                          'html':os.path.relpath(source.with_suffix('.html').resolve(),out.resolve()) if source.with_suffix('.html').exists() else None,
                          'provider':report.get('provider'),'model':report.get('model'),
                          'coverage':report.get('coverage',{}),'errors':report.get('errors',[]),
                          'channel_errors':[{'id':ch.get('id'),'error':ch.get('error')} for ch in report['channels'] if ch.get('error')],
                          'verification_policy':report.get('verification_policy'),
                          'estimated_or_reserved_usd':report.get('cost_usd')})
        for ch in report['channels']:
            for index,c in enumerate(ch.get('claims',[]),1):
                checks=c.get('program_checks') or []
                verdict=c.get('verdict') if checks and c.get('status')=='verified' else 'unchecked'
                if verdict not in ('supported','contradicted','insufficient_evidence'):verdict='unchecked'
                item={'id':f'{doc_id}:{ch.get("id","channel")}:{index}','document_id':doc_id,
                      'channel_id':ch.get('id'),'ticker':c.get('ticker'),'claim':c.get('claim',''),
                      'quote':c.get('quote',''),'source_locations':c.get('source_locations',[]),
                      'verdict':verdict,'recorded_status':c.get('status'),'screen_reason':c.get('screen_reason'),
                      'program_checks':checks,'evidence':c.get('evidence',[]),'corrections':[]}
                for check in checks:
                    actual=check.get('actual_value')
                    if check.get('program_verdict')=='contradicted' and check.get('evidence_valid') and type(actual) in (int,float) and math.isfinite(actual):
                        ids=check.get('evidence_ids',[])
                        referenced=[e for e in item['evidence'] if e.get('id') in ids]
                        if not referenced: continue
                        item['corrections'].append({'stated_value':check.get('stated_value'),
                            'actual_value':actual,'text':check.get('text'),'reason':check.get('reason'),
                            'evidence_ids':ids,'evidence':referenced})
                owner=str(c.get('ticker') or '').upper()
                (claims if owner==ticker else others if owner else unassigned).append(item)
    for pending in pending_documents or []:
        documents.append({'id':f'D{len(documents)+1:03d}', 'input':pending['input'], 'status':pending['status'], 'report':None, 'html':None, 'channel_errors':[], 'reason':pending.get('reason')})
    counts=dict(Counter(c['verdict'] for c in claims))
    groups={}
    for c in claims:
        key=re.sub(r'\s+',' ',c['claim']).strip().casefold()
        groups.setdefault(key,[]).append(c)
    grouped=[{'claim':v[0]['claim'],'occurrences':[c['id'] for c in v],
              'verdicts':sorted({c['verdict'] for c in v}),
              'conflicting_recorded_verdicts':len({c['verdict'] for c in v})>1} for v in groups.values()]
    result={'schema_version':1,'ticker':ticker,'summary_kind':'deterministic aggregation of retained checks; no new model inference',
            'documents':documents,'claims':claims,'other_ticker_claims':others,'unassigned_claims':unassigned,
            'groups':grouped,'counts':counts,'document_count':len(documents),
            'incomplete_documents':sum(d['status']!='completed' or bool(d['channel_errors']) for d in documents),
            'summary':f"{ticker}: {len(documents)} input reports; {len(claims)} extracted target-company claim occurrences. "
                      f"Supported {counts.get('supported',0)}; contradicted {counts.get('contradicted',0)}; "
                      f"insufficient evidence {counts.get('insufficient_evidence',0)}; unchecked {counts.get('unchecked',0)}.",
            'limitations':['Counts are extracted occurrences, not full-content recall or an investment rating.',
                'An unchanged or unchecked file is not evidence that every statement is true.',
                'Other-company and unassigned claims remain separate; a ticker label does not establish identity.',
                'Corrections reproduce numeric program checks and their original units/periods; they are not AI forecasts.',
                'Inputs may use different evidence vintages/policies; inspect each document before comparing.',
                'No new authentication of supplied report JSON is performed; hashes identify the exact reports summarized.'],
            'incremental_api_cost_usd':0}
    out.mkdir(parents=True,exist_ok=True)
    (out/'stock-review.json').write_text(json.dumps(result,indent=2)+'\n')
    esc=lambda x:html.escape(str(x))
    doc_rows=''.join(f'<tr><td>{esc(d["id"])}</td><td>{esc(d["input"].get("file","unknown"))}</td><td>{esc(d["status"])}</td><td><a href="{esc(d["html"] or d["report"] or "#")}">Original report</a></td></tr>' for d in documents)
    def cards(items):
        return ''.join(f'<article id="{esc(c["id"])}"><h3>{esc(c["id"])} · {esc(c["verdict"])}</h3><p>{esc(c["claim"])}</p><blockquote>{esc(c["quote"])}</blockquote>'
            + ''.join('<p><strong>Correction from program evidence:</strong> '+esc(x['stated_value'])+' → '+esc(x['actual_value'])+'; '+esc(x['reason'])+'</p>' for x in c['corrections'])
            + '<details><summary>Source locations, units, periods and checks</summary><pre>'+esc(json.dumps({'locations':c['source_locations'],'checks':c['program_checks'],'evidence':c['evidence']},indent=2))+'</pre></details></article>' for c in items) or '<p>No extracted claim rows.</p>'
    body=f'<h1>{esc(ticker)} · document review</h1><p>{esc(result["summary"])}</p><p>Incomplete documents: {result["incomplete_documents"]}. Incremental summary API cost: $0.</p><h2>Documents</h2><table><tr><th>ID</th><th>Input</th><th>Status</th><th>Evidence</th></tr>{doc_rows}</table><h2>Target-company findings</h2>{cards(claims)}<h2>Other companies</h2>{cards(others)}<h2>Unassigned claims</h2>{cards(unassigned)}<h2>Repeated statements</h2><pre>{esc(json.dumps(grouped,indent=2))}</pre><h2>Limits</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in result['limitations'])+'</ul>'
    (out/'stock-review.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+esc(ticker)+' document review</title><style>body{font:16px/1.55 system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#17242e}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}article{padding:18px 0;border-bottom:1px solid #ddd}pre{white-space:pre-wrap;overflow-wrap:anywhere}blockquote{border-left:3px solid #aaa;padding-left:16px}</style>'+body+'</html>')
    return result
