"""Real pod-log and local PTY projections. No receipt-event substitute or execution."""
from __future__ import annotations

import json
import math
import re
import shlex
from pathlib import Path
from pipeline import BuildError, file_hash

LIVE = re.compile(r'\blive id=([0-9a-f]{32}) \+([0-9.]+)s event=(\w+)(.*)$')
CLI = re.compile(r'cli \+([0-9.]+)s event=(\w+)([^\r\n]*)')


def trace_events(events):
    """Retained only for the site's native trace/call-count audit, never terminal rows."""
    out=[]
    for event in events:
        item={k:event[k] for k in ('kind','at_ms','name','arguments','verdict') if k in event}
        if event['kind']=='tool_result':
            item['result']={k:event['result'][k] for k in ('evidence_id','error') if k in event['result']}
        out.append(item)
    return out


def fields(text):
    return dict(token.split('=',1) for token in shlex.split(text) if '=' in token)


def condensed(at, event, args):
    """Keep the public progress semantics; never expose raw model reasoning."""
    time=f'+{at:.1f} s  '
    if event in ('tool_call','tool_result'):
        period=args.get('period','')
        if args.get('base_period'):period+=f" vs {args['base_period']}"
        text='  '.join(x for x in (time.rstrip(),args.get('name',event),args.get('ticker',''),args.get('metric',''),period) if x)
        if args.get('evidence_id'):text+=f"  → {args['evidence_id']}"
        return 'result' if event=='tool_result' else 'call',text.rstrip()
    if event=='model' and args.get('phase')=='running':
        return 'reasoning',f"{time}model"+(f" · step {args['step']}" if 'step' in args else '')
    if event=='start':
        # The captured runner logs a placeholder chars=0 before preprocessing.
        # Do not replace it with a guessed input length or a fictitious CLI command.
        return 'request',f"{time}request  POST /api/check · {args.get('kind','text')} · {args['provider']}"
    if event=='verdict':
        cost=args.get('cost',args.get('cost_usd','0')).lstrip('$')
        return 'verdict',f"verdict  {args['verdict']}  {at:.1f} s  ${float(cost):.4f}"
    details=' · '.join(v for k,v in args.items() if k not in ('cost_is_bound','model'))
    return 'status',f'{time}{event:<14}  {details}'.rstrip()


def read_server_log(receipt,root):
    asset=receipt.get('server_log')
    if not asset:raise BuildError('Real server-log JSONL required; record with log tail before the request')
    path=(root/asset['path']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise BuildError('Real server-log JSONL missing; receipt events are not a fallback')
    if file_hash(path)!=asset['sha256']:raise BuildError('Real server-log JSONL hash differs from capture receipt')
    records=[];previous=-1.;ids=set()
    for raw in path.read_text().splitlines():
        row=json.loads(raw)
        if set(row)!={'t_wall','t_rel_s','line'}:raise BuildError('Invalid server-log JSONL row')
        match=LIVE.search(row['line'])
        if not match:raise BuildError('Real server-log row lacks runner elapsed and request ID')
        rid,elapsed,event,tail=match.groups();at=float(elapsed)
        if not math.isfinite(at) or at<previous:raise BuildError('Server-log runner elapsed must be ordered')
        previous=at;ids.add(rid);args=fields(tail)
        kind,text=condensed(at,event,args)
        records.append(dict(at_s=at,event=event,kind=kind,text=text,args=args))
    if ids!={asset['request_id']} or receipt['result'].get('request_id',asset['request_id'])!=asset['request_id']:
        raise BuildError('Server log must contain only this live request ID')
    if not records or records[0]['event']!='start':raise BuildError('Real log must include the request start')
    return records


def compile_live_terminal(receipt,root=Path(__file__).resolve().parents[1]):
    phases={t['phase']:t['at_s'] for t in receipt['timings']}
    start=phases['check_against_sec'];end=phases['verdict_reveal']
    rows=read_server_log(receipt,root)
    final=[r for r in rows if r['event']=='verdict']
    if len(final)!=1 or rows[-1]!=final[0] or start+final[0]['at_s']>=end:
        raise BuildError('Real log must end with one verdict before the native verdict card')
    verdict=final[0];args=verdict['args'];result=receipt['result']
    cost=float(args.get('cost',args.get('cost_usd','0')).lstrip('$'))
    if (args.get('cost_is_bound')=='true' or result.get('cost_is_bound') or not math.isfinite(cost) or cost<0
        or args['verdict']!=result['verdict'] or f"{result['cost_usd']:.4f}"!=f'{cost:.4f}'):
        raise BuildError('Real log verdict/cost is incomplete or differs from the response')
    return dict(start_scene_s=start,typing_start_scene_s=start,end_scene_s=end,
        title='Online · hackathon.dappgo.com',
        rows=collapse_program_checks(rows),verdict=dict(at_s=verdict['at_s'],verdict=args['verdict']),cost_usd=cost,
        honesty_label=f"live request {receipt['server_log']['request_id'][:8]} · pod log")


def collapse_program_checks(rows):
    """One display row, with every contributing source index retained."""
    out=[]
    for index,row in enumerate(rows):
        row={**row,'source_indices':[index]}
        if row['event']=='program_check' and out and out[-1]['event']=='program_check' and out[-1]['at_s']==row['at_s']:
            out[-1]['source_indices'].append(index)
        else:out.append(row)
    for row in out:
        if row['event']=='program_check':
            row['text']=f"+{row['at_s']:.1f} s  program_check × {len(row['source_indices'])}"
    return out


def compile_local_terminal(root):
    path=root/'demo/assets/cli-v5/local-cli.json';receipt=json.loads((path.parent/'receipt.json').read_text())
    if file_hash(path)!=receipt['sha256'] or receipt['copy_sha256']!=receipt['sha256']:
        raise BuildError('Local CLI session differs from its original receipt hash')
    session=json.loads(path.read_text())
    if session['dry_run'] or session['exit_code']!=0 or session['interrupted'] or not session['receipt_summary']['available']:
        raise BuildError('Local terminal requires a completed real CLI recording')
    content='';previous=-1.;arrivals=[]
    for chunk in session['chunks']:
        at=chunk['t_rel_s']
        if type(at) not in (int,float) or not math.isfinite(at) or at<previous:raise BuildError('Local chunks must retain ordered timestamps')
        previous=at;content+=chunk['text'];arrivals.append((len(content),at))
    records=[]
    for index,match in enumerate(CLI.finditer(content)):
        elapsed,event,tail=match.groups();args=fields(tail)
        at=float(elapsed);kind,text=condensed(at,event,args)
        if event=='start':kind,text='status',f"+{at:.1f} s  start  {args.get('kind','text')} · {args['provider']}"
        if event=='verdict':text=f"+{at:.1f} s  verdict  {args['verdict']}  {args['cost']}"
        records.append(dict(at_s=next(t for n,t in arrivals if n>=match.end()),source_elapsed_s=at,
            event=event,kind=kind,text=text,args=args,source_event_indices=[index]))
    selected=[];pending=None
    for row in records:
        event=row['event']
        if event=='tool_call':pending=row
        elif event=='tool_result':
            if not pending or pending['args']['name']!=row['args']['name']:
                raise BuildError('Local tool result must match its recorded call')
            # One condensed pair appears only once its real result has arrived.
            _,pair_text=condensed(pending['source_elapsed_s'],'tool_result',row['args'])
            selected.append({**row,'text':pair_text,'source_call_elapsed_s':pending['source_elapsed_s'],
                'source_event_indices':pending['source_event_indices']+row['source_event_indices']})
            pending=None
        elif event in ('start','verdict'):selected.append(row)
        elif event=='model' and row['args'].get('phase')=='extraction':
            selected.append({**row,'kind':'reasoning','text':f"+{row['source_elapsed_s']:.1f} s  model · extraction"})
        elif (event=='model' and row['args'].get('phase')=='completed' and row['args'].get('count')=='2'
              and not any(r['event']=='verdict' for r in selected)):
            # The printed count is the source's completed step count, not an
            # invented ordinal for a later running notification.
            selected.append({**row,'kind':'status','text':f"+{row['source_elapsed_s']:.1f} s  model · step 2"})
        elif event=='receipt':selected.append(row)
    summary=session['receipt_summary'];v=summary['verdicts'];cost=summary['cost_usd']
    if not selected or selected[-1]['event']!='receipt' or len(selected)>12:
        raise BuildError('Local selection needs its real final receipt and at most twelve rows')
    final=selected[-1]
    if (int(final['args']['supported'])!=v['supported'] or int(final['args']['contradicted'])!=v['contradicted']
        or f"{cost:.4f}"!=final['args']['cost'].lstrip('$')):raise BuildError('Local receipt summary differs from the source event')
    final.update(kind='verdict',text=f"verdict  {v['supported']} supported · {v['contradicted']} contradicted  {session['duration_s']:.1f} s  ${cost:.4f}")
    frames=[dict(at_s=row['at_s'],rows=selected[max(0,i-4):i+1]) for i,row in enumerate(selected)]
    # Keep the actual command available verbatim. The long absolute --out path
    # is disclosed as an omitted argument, outside the recorded event rows.
    command='$ '+shlex.join(session['command'][:session['command'].index('--out')])+' …'
    return dict(title='Local · CLI · recorded 2026-11-04',command=command,full_command=shlex.join(session['command']),
        command_note='Command display omits the recorded --out path; full argv retained in the session.',frames=frames,
        rows=selected,receipt_source_elapsed_s=final['source_elapsed_s'],
        source_duration_s=session['duration_s'],session_sha256=file_hash(path),cost_usd=cost,
        note='Selected real events; each call/result pair shares one row at result arrival. Final row condenses the source receipt; duration is the retained session duration. Raw chunks and JSON remain unchanged.')
