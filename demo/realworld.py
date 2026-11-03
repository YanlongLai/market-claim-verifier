"""Offline compiler for the v010 real-world shot; absent evidence is an error.

Each real-world-* run exposes demo-shot.json (see data/REALWORLD.md). Reports,
inputs, failures and selected examples remain in the evidence directory. Nothing
here calls a model, downloads a post, or assigns gold/accuracy labels.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import re
from statistics import median
import sys
from urllib.parse import unquote, urlparse

from pipeline import BuildError, file_hash, read_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = 'demo/data/realworld.json'
SCENE = 'v311b-realworld'
VERDICTS = ('supported', 'contradicted', 'insufficient_evidence')
NARRATION_TEMPLATE = 'Saved real-world runs: {news} news items, {threads} Threads posts. Coverage is not accuracy.'
MAX_VOICE_S = 10.
PENDING = dict(schema_version=1, status='awaiting_evidence',
               reason='News and Threads real-world run records have not been committed.',
               sources=[], examples=[], narration=None, provenance={})


def encoded(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def number(value, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise BuildError(f'Real-world {name} must be a recorded nonnegative finite number.')
    return value


def record_path(repo: Path, folder: Path, relative: str) -> Path:
    path = (folder / relative).resolve()
    evidence = (repo / 'docs/evidence').resolve()
    if (not path.is_relative_to(evidence) or
            not path.relative_to(evidence).parts[0].startswith('real-world-') or not path.is_file()):
        raise BuildError(f'Real-world evidence path is missing or outside real-world-*: {relative}')
    return path


def handle(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('www.threads.net', 'threads.net',
                                                          'www.threads.com', 'threads.com'):
        return None
    match = re.match(r'/@([A-Za-z0-9_.]{1,30})(?:/|$)', unquote(parsed.path))
    return '@' + match[1] if match else None


def numeric_tokens(text: str) -> set[str]:
    # Preserve decimal magnitudes: 1.144 cannot be supplied by a 114.4 source.
    return set(re.findall(r'(?<![\w.])-?\d[\d,]*(?:\.\d+)?', text))


def item_input(path: Path, item_id: str) -> dict:
    """Select the retained source row without copying or rewriting frozen inputs."""
    if path.suffix != '.jsonl':
        return read_json(path)
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    matches = [row for row in rows if row.get('id') == item_id]
    if len(matches) != 1:
        raise BuildError(f'{path}: expected exactly one input row for {item_id}.')
    return matches[0]


def checked_values(claim: dict, report: str) -> dict:
    """Bind recorded program values to their cited source metadata; never rerun a check."""
    def fail(detail):
        raise BuildError(f'{report}: example lacks recorded checked evidence: {detail}.')

    def finite(value, field):
        if type(value) not in (int, float) or not math.isfinite(value):
            fail(field)
        return value

    values = []
    for index, check in enumerate(claim['program_checks']):
        kind = check.get('claim_type')
        if (kind not in ('value', 'change_pct') or check.get('evidence_valid') is not True or
                check.get('program_verdict') not in VERDICTS):
            fail(f'program check {index} type/validity/verdict')
        ids = check.get('evidence_ids')
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids):
            fail(f'program check {index} evidence IDs')
        evidence = claim.get('evidence', [])
        if any(not any(e.get('id') == identifier for e in evidence) for identifier in ids):
            fail(f'program check {index} missing cited evidence')
        # Change checks can cite the same ID for current and comparison periods.
        current = [e for e in evidence if e.get('id') in ids and e.get('role') != 'comparison']
        if len(current) != 1:
            fail(f'program check {index} ambiguous/missing primary source')
        source, = current
        for field in ('unit', 'period', 'metric', 'form', 'tier'):
            if not isinstance(source.get(field), str) or not source[field].strip():
                fail(f'program check {index} source {field}')
        if source['tier'] not in ('L1', 'L2', 'L3', 'L4'):
            fail(f'program check {index} source tier')
        value = finite(check.get('actual_value'), f'program check {index} actual_value')
        if kind == 'value' and value != finite(source.get('value'), 'primary source value'):
            fail(f'program check {index} value does not match its cited source')
        label = source['form']
        if source.get('exhibit'):
            label += ' Ex ' + str(source['exhibit'])
        compiled = dict(check_index=index, claim_type=kind, verdict=check['program_verdict'],
                        value=value, unit='%' if kind == 'change_pct' else source['unit'],
                        period=source['period'], metric=source['metric'],
                        source_label=label, source_tier=source['tier'], evidence_ids=deepcopy(ids))
        if kind == 'change_pct':
            text = check.get('text', '')
            if not isinstance(text, str) or not text.strip():
                fail(f'program check {index} change description')
            compiled['text'] = text
        if 'gap' in check:
            gap = check['gap']
            if not isinstance(gap, dict) or gap.get('gap_kind') not in ('relative', 'points', 'absolute'):
                fail(f'program check {index} gap kind')
            finite(gap.get('gap'), f'program check {index} gap')
            compiled['gap'] = deepcopy(gap)
        for field in ('ratio', 'difference'):
            if field in check:
                compiled[field] = finite(check[field], f'program check {index} {field}')
        values.append(compiled)
    primary = [v for v in values if v['claim_type'] == 'value']
    if len(primary) != 1:
        fail('exactly one checked primary value required')
    return dict(primary=primary[0], comparisons=[v for v in values if v is not primary[0]])


def compile_evidence(repo: Path) -> dict:
    folders = sorted(p for p in (repo / 'docs/evidence').glob('real-world-*') if p.is_dir())
    if not folders:
        raise BuildError('Missing real-world evidence: expected docs/evidence/real-world-*/demo-shot.json '
                         'with News + Threads item reports. No metrics or narration were generated.')
    missing = [p.name for p in folders if not (p/'demo-shot.json').is_file()]
    if missing:
        raise BuildError('Unindexed real-world evidence: '+', '.join(missing)+
                         '. Every original/post-hoc run requires demo-shot.json; rechecks cannot be ignored.')
    descriptors = [p/'demo-shot.json' for p in folders]
    provenance, runs, examples, run_ids = {}, [], [], set()

    def retain(path):
        relative = path.relative_to(repo).as_posix()
        provenance[relative] = file_hash(path)
        return relative

    for descriptor in descriptors:
        config = read_json(descriptor)
        run_id, phase = config['run_id'], config['phase']
        if (config.get('schema_version') != 1 or run_id in run_ids or
                phase not in ('original', 'posthoc_frozen_text_recheck')):
            raise BuildError(f'{descriptor}: invalid/duplicate run or phase.')
        run_ids.add(run_id)
        retain(descriptor)
        source_rows = []
        for source in config['sources']:
            source_id = source['id']
            if source_id not in ('news', 'threads') or any(r['id'] == source_id for r in source_rows):
                raise BuildError(f'{run_id}: expected unique news/threads sources.')
            items = source['items']
            if not items:
                raise BuildError(f'{run_id}/{source_id}: no retained attempts.')
            totals = dict.fromkeys(VERDICTS, 0)
            checked, errors, costs, latencies, seen = 0, 0, [], [], set()
            for item in items:
                if item['id'] in seen:
                    raise BuildError(f'{run_id}: duplicate item {item["id"]}.')
                seen.add(item['id'])
                input_path = record_path(repo, descriptor.parent, item['input'])
                original = item_input(input_path, item['id'])
                input_source = retain(input_path)
                report_path = (record_path(repo, descriptor.parent, item['report'])
                               if item.get('report') else None)
                report = read_json(report_path) if report_path else {}
                report_source = retain(report_path) if report_path else None
                accounting = report
                latency_key = 'wall_clock_s'
                if item.get('result'):
                    receipt_path = record_path(repo, descriptor.parent, item['result'])
                    accounting = read_json(receipt_path)
                    receipt_source = retain(receipt_path)
                    if (accounting.get('id') != item['id'] or
                            not all(config.get(k) and accounting.get(k) == config[k]
                                    for k in ('provider', 'path')) or
                            any(report.get(k) != accounting.get(k) for k in ('provider', 'model')
                                if k in report)):
                        raise BuildError(f'{receipt_source}: item/provider/path/model does not match selection.')
                    latency_key = 'wall_seconds'
                    # Failed CLI attempts can retain only their extraction trace, without a report.
                    for trace_path in sorted((receipt_path.parent/'traces').glob('*.json')):
                        retain(record_path(repo, receipt_path.parent, 'traces/'+trace_path.name))
                    report_source = report_source or receipt_source
                # Includes partial/failed items: a missing spend/latency receipt is not zero.
                costs.append(number(accounting.get('cost_usd'), 'cost_usd'))
                latencies.append(number(accounting.get(latency_key), latency_key))
                status = accounting.get('status', 'completed')
                if status not in ('completed', 'partial', 'failed', 'error', 'provider_error'):
                    raise BuildError(f'{report_source}: unrecognized recorded status {status!r}.')
                if not report_path and status == 'completed':
                    raise BuildError(f'{report_source}: completed receipt requires its post report.')
                claims = report.get('claims', [])
                errors += bool(status != 'completed' or accounting.get('error') or report.get('error') or
                               any(c.get('status') in ('failed', 'error', 'provider_error') for c in claims))
                # Trace files stay in evidence; bind them into the snapshot receipt too.
                trace_paths = [report.get('extraction_trace')] + [c.get('trace_path') for c in claims]
                for trace_path in trace_paths:
                    if trace_path:
                        retain(record_path(repo, report_path.parent, trace_path))
                verified = [c for c in claims if c.get('status') == 'verified']
                for claim in verified:
                    if claim.get('verdict') not in VERDICTS:
                        raise BuildError(f'{report_source}: unknown recorded verdict.')
                    totals[claim['verdict']] += 1
                program_checked = [c for c in verified if c.get('program_checks')]
                checked += bool(program_checked)
                for example in item.get('examples', []):
                    claim = next((c for c in verified if c['index'] == example['claim_index']), None)
                    if not claim or not claim.get('program_checks'):
                        raise BuildError(f'{report_source}: example lacks a recorded program check.')
                    text = example['paraphrase']
                    # Curated paraphrases are retained alongside raw evidence, never authored by this compiler.
                    if (not isinstance(text, str) or not text.strip() or len(text) > 100 or
                            '\n' in text or re.search(r'https?://|@[\w.]', text)):
                        raise BuildError('Real-world example must be a short paraphrase without a URL/handle.')
                    evidence_text = json.dumps([original, claim], ensure_ascii=False)
                    if not numeric_tokens(text) <= numeric_tokens(evidence_text):
                        raise BuildError(f'{report_source}: example contains a number absent from its evidence.')
                    author = handle(original.get('url', '')) if source_id == 'threads' else None
                    if source_id == 'threads' and not author:
                        raise BuildError(f'{input_source}: Threads example needs its retained public URL.')
                    examples.append(dict(run_id=run_id, phase=phase, source_id=source_id,
                                         item_id=item['id'], handle=author, paraphrase=text,
                                         verdict=claim['verdict'], report=report_source, input=input_source,
                                         claim_index=claim['index'], **checked_values(claim, report_source)))
            count = len(items)
            source_rows.append(dict(id=source_id, label={'news': 'DappGo News', 'threads': 'Threads'}[source_id],
                                    items_tested=count, items_checked=checked, items_with_errors=errors,
                                    coverage_percent=round(100*checked/count, 1), verdict_counts=totals,
                                    cost_usd=sum(costs), cost_per_item_usd=sum(costs)/count,
                                    p50_latency_s=median(latencies)))
        if phase == 'original' and {r['id'] for r in source_rows} != {'news', 'threads'}:
            raise BuildError('Original real-world run must contain both News and Threads results.')
        if phase != 'original' and not config.get('rechecks_run'):
            raise BuildError('Post-hoc run must name the original run it rechecks.')
        runs.append(dict(id=run_id, phase=phase, rechecks_run=config.get('rechecks_run'), sources=source_rows,
                         **{k: config[k] for k in ('provider', 'path', 'selection_note') if k in config}))
    originals = [r for r in runs if r['phase'] == 'original']
    if len(originals) != 1:
        raise BuildError('Real-world shot needs exactly one original run; disambiguate its demo-shot.json.')
    for run in runs:
        if run['phase'] != 'original' and run['rechecks_run'] != originals[0]['id']:
            raise BuildError('Post-hoc recheck does not reference the retained original run.')
    runs.sort(key=lambda r: (r['phase'] != 'original', r['id']))
    if len(examples) > 3:
        raise BuildError('Real-world shot supports at most three explicitly selected examples.')
    sources = sorted(originals[0]['sources'], key=lambda r: r['id'])
    counts = {r['id']: r['items_tested'] for r in sources}
    narration = NARRATION_TEMPLATE.format(**counts)
    if len(narration.split()) > 22:
        raise BuildError('Real-world narration exceeds the ten-second template word budget.')
    return dict(schema_version=1, status='ready', sources=sources, runs=runs, examples=examples,
                coverage_definition='Items with at least one program-checked claim / all attempted items; '
                                    'coverage is not accuracy. Verdict counts are claims, not items.',
                latency_definition='Median item wall time, including retained partial/failed attempts.',
                cost_definition='Recorded item receipts (or legacy report estimates/reservations), '
                                'including all retained item attempts; '
                                'not provider invoices.',
                recheck_note='Post-hoc frozen-text rechecks do not retest OCR/ASR or establish fresh accuracy.',
                narration=narration, narration_template=NARRATION_TEMPLATE, max_voice_s=MAX_VOICE_S,
                provenance=dict(sorted(provenance.items())))


def load_snapshot(repo: Path, *, require_ready=False) -> dict:
    data = read_json(repo / OUTPUT)
    if data == PENDING:
        if require_ready:
            raise BuildError('Real-world evidence pending. Run demo/realworld.py after committing News + Threads '
                             'records; do not synthesize the placeholder or render this preview.')
        return data
    expected = compile_evidence(repo)
    if data != expected:
        raise BuildError('Stale real-world snapshot. Run uv run --project demo python demo/realworld.py.')
    return data


def resolve_story(repo: Path, story: dict, *, require_ready=False) -> dict:
    story = deepcopy(story)
    scenes = [s for s in story['scenes'] if s.get('data_source') == OUTPUT]
    if not scenes:
        return story
    data = load_snapshot(repo, require_ready=require_ready)
    for scene in scenes:
        scene['narration'] = data['narration'] or 'Real-world evidence pending.'
        scene['evidence_pending'] = data['status'] != 'ready'
    return story


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--check', action='store_true')
    args = cli.parse_args()
    try:
        data = compile_evidence(ROOT)
        target = ROOT / OUTPUT
        if args.check:
            if not target.is_file() or target.read_text() != encoded(data):
                raise BuildError('Stale real-world snapshot; run demo/realworld.py.')
        else:
            target.write_text(encoded(data))
        print(f'Real-world {"checked" if args.check else "compiled"}: {len(data["sources"])} sources; '
              f'narration ≤ {MAX_VOICE_S:g} s must be measured with the locked voice.')
        return 0
    except (BuildError, KeyError, TypeError, ValueError, OSError) as error:
        print(f'ERROR: real-world compiler: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
