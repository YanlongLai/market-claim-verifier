"""Real pod-log and local PTY projections. No receipt-event substitute or execution."""
from __future__ import annotations

import json
import math
import re
import shlex
from pathlib import Path
from pipeline import BuildError, file_hash

LIVE = re.compile(r'\blive id=([0-9a-f]{32}) \+([0-9.]+)s event=(\w+)(.*)$')


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
    time=f'+{at:4.1f} s  '
    if event in ('tool_call','tool_result'):
        period=args.get('period','')
        if args.get('base_period'):period+=f" vs {args['base_period']}"
        text=(f"{time}{args.get('name',event):<14}  {args.get('ticker',''):<4}  "
              f"{args.get('metric',''):<7}  {period}")
        if args.get('evidence_id'):text+=f"  → {args['evidence_id']}"
        return 'call',text.rstrip()
    if event=='model' and args.get('phase')=='running':
        return 'reasoning',f"{time}… model reasoning (Muse Spark)"+(f" · step {args['step']}" if 'step' in args else '')
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
    return dict(start_scene_s=start,typing_start_scene_s=start-.6,end_scene_s=end,
        title='Online · hackathon.dappgo.com · server log',
        command=f"$ claimcheck post post.txt --provider {result['provider']} --budget 1",
        rows=rows,verdict=dict(at_s=verdict['at_s'],verdict=args['verdict']),cost_usd=cost,
        honesty_label=f"live request {receipt['server_log']['request_id'][:8]} · pod log")


def compile_local_terminal(root):
    path=root/'demo/assets/cli-v5/local-cli.json';receipt=json.loads((path.parent/'receipt.json').read_text())
    if file_hash(path)!=receipt['sha256'] or receipt['copy_sha256']!=receipt['sha256']:
        raise BuildError('Local CLI session differs from its original receipt hash')
    session=json.loads(path.read_text())
    if session['dry_run'] or session['exit_code']!=0 or session['interrupted'] or not session['receipt_summary']['available']:
        raise BuildError('Local terminal requires a completed real CLI recording')
    frames=[];content='';previous=-1.
    for chunk in session['chunks']:
        at=chunk['t_rel_s']
        if type(at) not in (int,float) or not math.isfinite(at) or at<previous:raise BuildError('Local chunks must retain ordered timestamps')
        previous=at;content+=chunk['text']
        # This recording is plain PTY text. Reflow every chunk, including partial
        # lines and the final report JSON; never replace it with a saved replay.
        lines=content.replace('\r\n','\n').replace('\r','').split('\n')
        if lines[-1]=='':lines.pop()
        wrapped=[part for line in lines for part in ([line[a:a+98] for a in range(0,len(line),98)] or [''])]
        rows=[dict(kind='verdict' if 'event=verdict' in text or 'event=receipt' in text else 'output',text=text) for text in wrapped[-5:]]
        frames.append(dict(at_s=at,rows=rows))
    summary=session['receipt_summary'];v=summary['verdicts'];cost=summary['cost_usd']
    frames[-1]['rows']=(frames[-1]['rows']+[dict(kind='verdict',
        text=f"verdict  {v['supported']} supported · {v['contradicted']} contradicted  ${cost:.4f}")])[-5:]
    # Wrap the literal shell command with continuation characters, never shrink it.
    command=shlex.join(session['command']);parts=[];line='$ '
    for token in shlex.split(command):
        word=shlex.quote(token)
        if len(line)+len(word)>94:parts.append(line.rstrip()+' \\');line='  '
        line+=word+' '
    parts.append(line.rstrip())
    return dict(title='Local · CLI · recorded 2026-11-04',command='\n'.join(parts),frames=frames,
        source_duration_s=session['duration_s'],session_sha256=file_hash(path),cost_usd=cost,
        note='Every original PTY chunk, including partial lines and report JSON, reflowed to 98 columns; final counts/cost from the session receipt.')
