"""Compile the Apple ribbon from the same recorded trace as the on-screen check."""
from __future__ import annotations

import json
import math
from pathlib import Path

from pipeline import BuildError, file_hash, read_json

REPORT = 'docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json'


def compile_trace(repo: Path) -> dict:
    report = read_json(repo / REPORT)
    claim = next(c for c in report['claims'] if c['ticker'] == 'AAPL')
    path = (Path(REPORT).parent / claim['trace_path']).as_posix()
    trace = read_json(repo / path)
    if (trace['final_verdict']['verdict'] != claim['verdict'] or
            trace['program_checks'] != claim['program_checks']):
        raise BuildError('Apple ribbon trace differs from the saved post check.')
    calls = {c['call_id']: c for c in trace['tool_calls']}
    ids = [e['id'] for e in claim['evidence']]
    steps, elapsed, cost, used = [], 0., 0., set()
    for i, request in enumerate(trace['requests']):
        latency, amount = request['latency_ms'] / 1000, request['cost']
        if (request['status'] != 'completed' or
                any(not math.isfinite(n) or n < 0 for n in (latency, amount))):
            raise BuildError('Apple ribbon needs complete recorded request costs and latencies.')
        message = request['raw_response']['choices'][0]['message']
        tools, facts = [], []
        for call in message.get('tool_calls') or []:
            recorded = calls[call['id']]
            if (call['function']['name'] != recorded['name'] or
                    json.loads(call['function']['arguments']) != recorded['arguments']):
                raise BuildError('Apple trace tool response and recorded call disagree.')
            tools.append(recorded['name'])
            facts.append(recorded['result']['evidence_id'])
            used.add(call['id'])
        if tools:
            name = ' + '.join(tools)
        else:
            response = json.loads(message['content'])
            name = 'final_verdict' if 'verdict' in response else 'sub_claims'
            facts = sorted({e for c in response.get('sub_claims', []) for e in c.get('evidence_ids', [])})
            if name == 'final_verdict' and not facts:
                facts = ids
        if not facts or any(f not in ids for f in facts):
            raise BuildError('Apple trace ribbon has missing or unbound fact IDs.')
        steps.append(dict(index=i+1, name=name, tools=tools, fact_ids=facts,
                          start_s=elapsed, latency_s=latency, cost_usd=amount))
        elapsed += latency
        cost += amount
    if (used != set(calls) or not steps or elapsed <= 0 or
            not math.isclose(elapsed * 1000, trace['latency_ms'], abs_tol=.001) or
            not math.isclose(cost, trace['cost_usd'], abs_tol=1e-9)):
        raise BuildError('Apple trace totals or tool-call coverage disagree.')
    return dict(source=path, report=REPORT, provider=trace['provider'], model=trace['model'],
                fact_ids=ids, steps=steps, latency_s=elapsed, cost_usd=cost,
                timing_note='Recorded model-request latency; animation compresses the saved run.',
                provenance={p: file_hash(repo / p) for p in (REPORT, path)})
