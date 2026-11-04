"""Project one retained request's trace onto the film clock, without executing it."""
from __future__ import annotations

import math
from pipeline import BuildError


def trace_events(events):
    """Keep the event fields needed to rebuild the terminal in a media-free clone."""
    out=[]
    for event in events:
        item={k:event[k] for k in ('kind','at_ms','name','arguments','verdict') if k in event}
        if event['kind']=='tool_result':
            item['result']={k:event['result'][k] for k in ('evidence_id','error') if k in event['result']}
        out.append(item)
    return out


def compile_live_terminal(receipt):
    phases={t['phase']:t['at_s'] for t in receipt['timings']}
    start=phases['check_against_sec'];end=phases['verdict_reveal']
    result=receipt['result'];events=result['events']
    previous=-1.;pending=[];calls=[];verdict=None
    for event in events:
        at=event.get('at_ms')
        if type(at) not in (int,float) or not math.isfinite(at) or at<0 or at<previous:
            raise BuildError('Live terminal requires ordered, timed receipt events')
        previous=at
        if event['kind']=='tool_call':
            item=dict(at_s=at/1000,name=event['name'],arguments=event['arguments'])
            calls.append(item);pending.append(item)
        elif event['kind']=='tool_result':
            call=next((c for c in pending if c['name']==event['name']),None)
            if call is None:raise BuildError('Live terminal tool result has no matching call')
            pending.remove(call)
            evidence=event['result'].get('evidence_id')
            if not evidence:raise BuildError('Live terminal tool result has no recorded evidence ID')
            call.update(evidence_id=evidence,result_at_s=at/1000)
        elif event['kind']=='verdict':
            if verdict is not None:raise BuildError('Live terminal requires one final verdict event')
            verdict=dict(at_s=at/1000,verdict=event['verdict'])
    if pending or not calls or verdict is None or start+verdict['at_s']>=end:
        raise BuildError('Live terminal trace must complete before the recorded verdict reveal')
    if verdict['verdict']!=result['verdict'] or any(c['result_at_s']>verdict['at_s'] for c in calls):
        raise BuildError('Live terminal verdict differs from the recorded request')
    names=max(len(c['name']) for c in calls)
    for call in calls:
        args=call['arguments'];period=args.get('period','')
        if args.get('base_period'):period+=f" vs {args['base_period']}"
        call['text']=(f"+{call['at_s']:.1f} s  {call['name']:<{names}}  "
                      f"{args.get('ticker','')}  {args.get('metric','')}  {period}  → {call['evidence_id']}")
    cost=result['cost_usd']
    if type(cost) not in (int,float) or not math.isfinite(cost) or cost<0 or result.get('cost_is_bound'):
        raise BuildError('Live terminal requires a measured receipt cost')
    return dict(start_scene_s=start,typing_start_scene_s=start-.6,end_scene_s=end,
        command=f"$ claimcheck post post.txt --provider {result['provider']} --budget 1",
        calls=calls,reasoning_at_s=max(c['result_at_s'] for c in calls),
        reasoning_text='… model reasoning (Muse Spark)',verdict=verdict,
        verdict_text=f"verdict  {verdict['verdict']}   {verdict['at_s']:.1f} s   ${cost:.2f}",
        cost_usd=cost,honesty_label='recorded trace of this request')
