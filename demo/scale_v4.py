#!/usr/bin/env python3
"""Compile saved timing evidence. Reads files only; never imports the live CLI."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent.parent
BASE = 'docs/evidence/real-world-2026-11-02'
EVAL = 'docs/evidence/eval-v2-2026-10-27'
OUTPUT = 'demo/data/scale-v4.json'


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def compile_scale(root=ROOT):
    sources = {}

    def read(path):
        raw = (root / path).read_bytes()
        sources[path] = dict(path=path, sha256=hashlib.sha256(raw).hexdigest())
        return json.loads(raw)

    def span(rows):
        start = min(timestamp(r['started_at']) for r in rows)
        end = max(timestamp(r['finished_at']) for r in rows)
        return dict(started_at=start.isoformat(), finished_at=end.isoformat(),
                    wall_seconds=(end-start).total_seconds())

    cohorts, parallel = {}, {}
    for label, folder in [('news', BASE), ('threads', BASE+'/threads')]:
        all_rows = []
        for provider in ('baseten', 'fireworks', 'meta'):
            for path in sorted((root/folder/provider).glob('*/**/result.json')):
                relative = path.relative_to(root).as_posix()
                row = read(relative)
                if row.get('status') == 'budget_stopped' or 'wall_seconds' not in row:
                    continue
                all_rows.append(row)
                if row.get('path') != 'post':
                    continue
                key = f'{label}/{provider}/post'
                cohorts.setdefault(key, []).append(dict(row, source=relative))
        # Three different provider comparisons ran concurrently, each serial within
        # its own worker. This envelope includes agent/post/media work, NOT a
        # same-model three-worker speedup of the post path.
        summaries = [read(f'{folder}/{p}/execution-summary.json')
                     for p in ('baseten', 'fireworks', 'meta')]
        envelope = span(all_rows)
        finished = max(timestamp(s['finished_at']) for s in summaries)
        envelope['finished_at'] = finished.isoformat()
        envelope['wall_seconds'] = (finished-timestamp(envelope['started_at'])).total_seconds()
        parallel[label] = dict(**envelope, workers=3, jobs=len(all_rows),
            sources=[f'{folder}/{p}/execution-summary.json' for p in ('baseten','fireworks','meta')],
            worker_basis=f'{BASE}/REPORT.md',
            scope='Observed envelope of three provider comparison workers, including agent/post/media; '
                  'not throughput of one model on 1,000 distinct posts.')

    groups = {}
    for name, rows in sorted(cohorts.items()):
        values = [r['wall_seconds'] for r in rows]
        intervals = sorted((timestamp(r['started_at']), timestamp(r['finished_at'])) for r in rows)
        groups[name] = dict(items=len(rows), statuses=dict(Counter(r['status'] for r in rows)),
            model_calls=sum(r['model_calls'] for r in rows),
            zero_call_items=sum(r['model_calls'] == 0 for r in rows),
            median_wall_seconds=statistics.median(values),
            sum_item_wall_seconds=sum(values), recorded_batch=span(rows),
            serial_item_intervals=all(a[1] <= b[0] for a,b in zip(intervals, intervals[1:])),
            sources=[r['source'] for r in rows])

    # Latency of one benchmark CLAIM is not latency of a multi-claim POST.
    eval_rows = [read(p.relative_to(root).as_posix())
                 for p in sorted((root/EVAL).glob('*--agent@baseten.json'))]
    heldout = [r for r in eval_rows if r['split']=='test']
    completed = [r for r in heldout if r['status']=='completed']
    manifest = read(EVAL+'/manifest.json')
    read(EVAL+'/summary.json')
    eval_timing = dict(unit='claim', provider='baseten', split='test',
        items=len(heldout), completed=len(completed),
        median_completed_latency_seconds=statistics.median(r['latency_ms']/1000 for r in completed),
        all_result_timestamp_envelope=span(eval_rows),
        manifest_wall_clock_s=manifest['wall_clock_s'],
        declared_concurrency=manifest['concurrency'],
        limitation='The manifest wall_clock_s is a resumed invocation, not the complete result envelope. '
                   'Neither is a measured 1,000-post batch. Do not derive parallel post throughput from it.')
    selected = groups['threads/baseten/post']
    seconds = selected['median_wall_seconds']
    hours = 1000*seconds/3600
    sentence = (f'On saved Threads posts, the median was {seconds:.1f} seconds: '
                f'a thousand posts would take about {hours:.1f} hours sequentially at that median.')
    return dict(schema_version=1, evidence_only=True,
        formulas=dict(median='statistics.median(result.wall_seconds), all attempted posts including failures',
            batch_wall='max(result.finished_at) - min(result.started_at)',
            parallel_wall='max(provider execution-summary.finished_at) - min(attempted result.started_at)',
            sum_item_wall='sum(result.wall_seconds); distinct from elapsed batch wall time',
            thousand_sequential_hours='1000 * selected.median_wall_seconds / 3600'),
        selected_cohort='threads/baseten/post', cohorts=groups,
        projection=dict(posts=1000, sequential_hours_at_median=hours,
            measured=False, parallel_1000_posts=None,
            limitation='Median-based arithmetic illustration, not measured throughput. '
                       'No same-model parallel post batch was recorded; do not divide by worker count.'),
        recorded_parallel_batches=parallel, eval_v2=eval_timing,
        narration_sentence=sentence,
        limits=['Saved paraphrased inputs; shared preseeded SEC cache; startup, transport, tools and failures included.',
                'Provider workers and validation overlapped. Timing is not an isolated API benchmark.',
                'Coverage is not accuracy; text timings do not measure OCR/ASR or full article recall.'],
        sources=[sources[k] for k in sorted(sources)])


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--check', action='store_true')
    args=cli.parse_args()
    result=compile_scale()
    content=json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n'
    target=ROOT/OUTPUT
    if args.check:
        if target.read_text()!=content:
            raise SystemExit('scale-v4.json is stale; run demo/scale_v4.py')
    else:
        target.write_text(content)
    print(result['narration_sentence'])
    for name, group in result['cohorts'].items():
        print(f"{name}: n={group['items']}, median={group['median_wall_seconds']:.6f}s, "
              f"batch={group['recorded_batch']['wall_seconds']:.6f}s")
    print('PASS scale-v4 sources, formulas and deterministic rebuild')


if __name__=='__main__':
    main()
