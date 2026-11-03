"""Real-world compiler, active v010 timings and saved Apple trace; no paid/media calls."""
from copy import deepcopy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from agent_trace import REPORT, compile_trace
from build import Builder
import motion_v3 as v3
import motion_media
import media
from motion_cues import sentence_subtitles
from pipeline import BuildError, file_hash, read_json, write_json
import realworld as rw
from test_review_v007 import LENGTHS, pauses

STORY = yaml.safe_load((v3.ROOT/v3.STORY).read_text())


def fixture_run(repo, *, phase='original', run_id='synthetic-original'):
    """Temporary synthetic records exercise arithmetic, not demonstration claims."""
    folder = repo/'docs/evidence'/('real-world-'+run_id)
    sources = []
    for name in ('news', 'threads'):
        items = []
        for i, (status, cost, seconds) in enumerate([
                ('completed', .02, 2.), ('completed', .04, 8.), ('provider_error', .03, 3.)]):
            stem = f'{name}-{i}'
            source = dict(url='https://www.threads.net/@synthetic_user/post/test',
                          text='Synthetic claim: 12.5 dollars; source says 10 dollars.')
            claim = dict(index=1, status='verified', quote=source['text'],
                         verdict='contradicted' if i == 0 else 'insufficient_evidence',
                         program_checks=[dict(claim_type='value', actual_value=10, stated_value=12.5,
                                              evidence_valid=True, program_verdict='contradicted',
                                              evidence_ids=['E1'], gap=dict(gap_kind='relative', gap=.25))],
                         evidence=[dict(id='E1', value=10, unit='USD', period='FY2025', metric='revenue',
                                        form='10-K', tier='L1')])
            report = dict(status=status, claims=[claim] if i < 2 else [],
                          cost_usd=cost, wall_clock_s=seconds)
            write_json(folder/(stem+'-input.json'), source)
            write_json(folder/(stem+'-report.json'), report)
            items.append(dict(id=stem, input=stem+'-input.json', report=stem+'-report.json'))
        if name == 'threads':
            items[0]['examples'] = [dict(claim_index=1, paraphrase='Synthetic: 12.5 claimed; source says 10.')]
        sources.append(dict(id=name, items=items))
    descriptor = dict(schema_version=1, run_id=run_id, phase=phase, sources=sources)
    if phase != 'original':
        descriptor['rechecks_run'] = 'synthetic-original'
        # Failed known-case recheck stays visible separately.
        descriptor['sources'] = [sources[1]]
    path = folder/'demo-shot.json'
    write_json(path, descriptor)
    return path


def test_missing_evidence_fails_and_pending_snapshot_has_no_invented_results(tmp_path):
    write_json(tmp_path/rw.OUTPUT, rw.PENDING)
    before = (tmp_path/rw.OUTPUT).read_bytes()
    with pytest.raises(BuildError, match='Missing real-world evidence.*No metrics or narration'):
        rw.compile_evidence(tmp_path)
    assert (tmp_path/rw.OUTPUT).read_bytes() == before
    assert rw.load_snapshot(tmp_path) == rw.PENDING
    with pytest.raises(BuildError, match='evidence pending'):
        rw.load_snapshot(tmp_path, require_ready=True)
    if not list((v3.ROOT/'docs/evidence').glob('real-world-*/demo-shot.json')):
        assert rw.load_snapshot(v3.ROOT) == rw.PENDING


def test_all_attempts_feed_coverage_cost_verdicts_and_p50(tmp_path):
    fixture_run(tmp_path)
    data = rw.compile_evidence(tmp_path)
    for row in data['sources']:
        assert row['items_tested'] == 3
        assert row['items_checked'] == 2 and row['items_with_errors'] == 1
        assert row['coverage_percent'] == 66.7
        assert row['verdict_counts'] == dict(supported=0, contradicted=1, insufficient_evidence=1)
        assert row['cost_usd'] == pytest.approx(.09)
        assert row['cost_per_item_usd'] == pytest.approx(.03)
        assert row['p50_latency_s'] == 3  # Includes the failed item, not just completed latencies.
    assert data['narration'] == rw.NARRATION_TEMPLATE.format(news=3, threads=3)
    assert len(data['narration'].split()) <= 22
    assert all(file_hash(tmp_path/p) == h for p,h in data['provenance'].items())
    example, = data['examples']
    assert example['handle'] == '@synthetic_user'
    assert example['verdict'] == 'contradicted'
    assert example['primary'] == dict(check_index=0, claim_type='value', verdict='contradicted',
                                      value=10, stated_value=12.5, unit='USD', period='FY2025', metric='revenue',
                                      source_label='10-K', source_tier='L1', evidence_ids=['E1'],
                                      gap=dict(gap_kind='relative', gap=.25))
    assert example['comparisons'] == []
    assert 'https://' not in json.dumps(example)
    write_json(tmp_path/rw.OUTPUT, data)
    assert rw.load_snapshot(tmp_path, require_ready=True) == data
    path = tmp_path/example['input']
    path.write_text(path.read_text()+'\n')
    with pytest.raises(BuildError, match='Stale real-world snapshot'):
        rw.load_snapshot(tmp_path, require_ready=True)


@pytest.mark.parametrize('field', ['actual_value', 'stated_value', 'evidence_ids', 'evidence_valid', 'program_verdict',
                                 'source', 'unit', 'period', 'metric', 'form', 'tier', 'source_value'])
def test_selected_example_fails_without_recorded_checked_value_or_source(tmp_path, field):
    descriptor = fixture_run(tmp_path)
    item = read_json(descriptor)['sources'][1]['items'][0]
    path = descriptor.parent/item['report']
    report = read_json(path)
    claim = report['claims'][0]
    if field == 'source':
        claim['evidence'] = []
    elif field == 'source_value':
        claim['evidence'][0]['value'] = 999
    elif field in ('unit', 'period', 'metric', 'form', 'tier'):
        del claim['evidence'][0][field]
    else:
        del claim['program_checks'][0][field]
    write_json(path, report)
    with pytest.raises(BuildError, match='example lacks recorded checked evidence'):
        rw.compile_evidence(tmp_path)


def test_example_copies_recorded_differences_and_source_label_without_arithmetic(tmp_path):
    descriptor = fixture_run(tmp_path)
    item = read_json(descriptor)['sources'][1]['items'][0]
    path = descriptor.parent/item['report']
    report = read_json(path)
    claim = report['claims'][0]
    check = claim['program_checks'][0]
    # Intentionally arbitrary recorded values prove this compiler does not calculate a ratio or gap.
    check.update(ratio=7.12345, difference=19.23456)
    check['gap']['gap'] = .87654321
    claim['evidence'][0].update(form='8-K', exhibit='99.1', tier='L4')
    write_json(path, report)
    example, = rw.compile_evidence(tmp_path)['examples']
    assert example['primary']['ratio'] == check['ratio']
    assert example['primary']['difference'] == check['difference']
    assert example['primary']['gap'] == check['gap']
    assert example['primary']['source_label'] == '8-K Ex 99.1'
    assert example['primary']['source_tier'] == 'L4'


def test_real_examples_bind_values_and_growth_to_the_selected_recorded_claim():
    data = rw.compile_evidence(v3.ROOT)
    core, sandisk = data['examples']
    assert (core['item_id'], core['claim_index'], core['verdict']) == ('T03', 2, 'contradicted')
    assert (core['primary']['value'], core['primary']['unit'], core['primary']['period'],
            core['primary']['source_label'], core['primary']['source_tier']) == (
                229000000., 'USD', 'FY2023', '10-K', 'L1')
    assert core['primary']['gap']['gap'] == 9.
    assert (sandisk['item_id'], sandisk['claim_index'], sandisk['verdict']) == ('T09', 1, 'contradicted')
    assert (sandisk['primary']['value'], sandisk['primary']['unit'], sandisk['primary']['period'],
            sandisk['primary']['source_label'], sandisk['primary']['source_tier'],
            sandisk['primary']['verdict']) == (11031000000., 'USD', 'FY2027Q1', '10-Q', 'L2', 'supported')
    growth, = sandisk['comparisons']
    assert (growth['value'], growth['unit'], growth['verdict']) == (377.946273830156, '%', 'contradicted')
    assert growth['gap'] == dict(gap_kind='points', gap=354.946273830156, direction_wrong=False,
                               severity='severe', score=0.)
    for example in data['examples']:
        report = read_json(v3.ROOT/example['report'])
        claim = next(c for c in report['claims'] if c['index'] == example['claim_index'])
        for value in [example['primary'], *example['comparisons']]:
            recorded = claim['program_checks'][value['check_index']]
            assert value['value'] == recorded['actual_value']
            assert value['stated_value'] == recorded['stated_value']
            assert value['gap'] == recorded['gap']
            assert value['evidence_ids'] == recorded['evidence_ids']
        assert data['provenance'][example['report']] == file_hash(v3.ROOT/example['report'])


def fixture_runner_receipts(repo):
    descriptor = fixture_run(repo)
    config = read_json(descriptor)
    config.update(provider='baseten', path='post', selection_note='One synthetic fixed route.')
    for source in config['sources']:
        rows = []
        for item in source['items']:
            original = read_json(descriptor.parent/item['input'])
            rows.append(dict(id=item['id'], **original))
            item['input'] = source['id']+'.jsonl'
            report_path = descriptor.parent/item['report']
            report = read_json(report_path)
            receipt = dict(id=item['id'], provider='baseten', path='post', model='synthetic-open',
                           status=report['status'], cost_usd=report['cost_usd'],
                           wall_seconds=report['wall_clock_s'])
            item['result'] = item['id']+'/result.json'
            write_json(descriptor.parent/item['result'], receipt)
            if receipt['status'] == 'completed':
                # The runner's ledger/wall receipt takes precedence over the inner CLI report.
                report.update(provider='baseten', model='synthetic-open', cost_usd=999, wall_clock_s=999)
                write_json(report_path, report)
            else:
                report_path.unlink()
                del item['report']
                write_json(descriptor.parent/item['id']/'traces/extraction.json', dict(error='synthetic'))
        (descriptor.parent/(source['id']+'.jsonl')).write_text(
            ''.join(json.dumps(row)+'\n' for row in rows))
    write_json(descriptor, config)
    return descriptor


def test_runner_receipts_preserve_failed_cost_latency_and_extraction_traces(tmp_path):
    descriptor = fixture_runner_receipts(tmp_path)
    data = rw.compile_evidence(tmp_path)
    for row in data['sources']:
        assert row['items_tested'] == 3 and row['items_checked'] == 2
        assert row['items_with_errors'] == 1 and row['coverage_percent'] == 66.7
        assert row['cost_usd'] == pytest.approx(.09) and row['p50_latency_s'] == 3
    run, = data['runs']
    assert (run['provider'], run['path'], run['selection_note']) == (
        'baseten', 'post', 'One synthetic fixed route.')
    for source in ('news', 'threads'):
        for relative in (source+'.jsonl', source+'-2/result.json', source+'-2/traces/extraction.json'):
            path = descriptor.parent/relative
            assert data['provenance'][path.relative_to(tmp_path).as_posix()] == file_hash(path)
    assert data['examples'][0]['handle'] == '@synthetic_user'


@pytest.mark.parametrize('corruption,match', [
    ('cost_usd', 'recorded nonnegative'), ('wall_seconds', 'recorded nonnegative'),
    ('id', 'does not match selection'), ('provider', 'does not match selection'),
    ('path', 'does not match selection'), ('model', 'does not match selection'),
    ('completed_without_report', 'completed receipt requires'),
    ('missing_input', 'exactly one input row'), ('duplicate_input', 'exactly one input row')])
def test_runner_adapter_rejects_missing_receipts_or_mismatched_evidence(tmp_path, corruption, match):
    descriptor = fixture_runner_receipts(tmp_path)
    config = read_json(descriptor)
    item = config['sources'][0]['items'][0]
    receipt_path = descriptor.parent/item['result']
    receipt = read_json(receipt_path)
    if corruption in ('cost_usd', 'wall_seconds'):
        del receipt[corruption]  # Never fall back to the legacy report's 999.
    elif corruption in ('id', 'provider', 'path', 'model'):
        receipt[corruption] = 'other'
    elif corruption == 'completed_without_report':
        del item['report']
    else:
        input_path = descriptor.parent/item['input']
        rows = input_path.read_text().splitlines()
        input_path.write_text('\n'.join(rows[1:] if corruption == 'missing_input' else rows+[rows[0]])+'\n')
    write_json(receipt_path, receipt)
    write_json(descriptor, config)
    with pytest.raises(BuildError, match=match):
        rw.compile_evidence(tmp_path)


def test_posthoc_recheck_is_separate_and_never_replaces_original(tmp_path):
    fixture_run(tmp_path)
    original = rw.compile_evidence(tmp_path)
    fixture_run(tmp_path, phase='posthoc_frozen_text_recheck', run_id='synthetic-fix')
    data = rw.compile_evidence(tmp_path)
    assert data['sources'] == original['sources']
    assert data['narration'] == original['narration']
    assert data['runs'][0]['phase'] == 'original'
    fix = next(r for r in data['runs'] if r['phase'] != 'original')
    assert fix['rechecks_run'] == 'synthetic-original'
    assert fix['sources'][0]['items_with_errors'] == 1
    assert 'do not retest OCR/ASR' in data['recheck_note']


def test_present_but_unindexed_recheck_cannot_be_silently_omitted(tmp_path):
    fixture_run(tmp_path)
    write_json(tmp_path/'docs/evidence/real-world-posthoc/report.json', dict(status='partial'))
    with pytest.raises(BuildError, match='Unindexed real-world evidence.*rechecks cannot be ignored'):
        rw.compile_evidence(tmp_path)


@pytest.mark.parametrize('corruption,match', [
    ('cost', 'recorded nonnegative'), ('latency', 'recorded nonnegative'),
    ('magnitude', 'number absent'), ('url', 'retained public URL'),
    ('verdict', 'unknown recorded verdict'), ('outside', 'outside real-world'),
    ('claim', 'lacks a recorded program check'), ('count', 'at most three'),
    ('phase', 'invalid/duplicate run or phase')])
def test_bad_sources_cannot_create_plausible_screen_numbers(tmp_path, corruption, match):
    descriptor = fixture_run(tmp_path)
    config = read_json(descriptor)
    item = config['sources'][1]['items'][0]
    report_path = descriptor.parent/item['report']
    report = read_json(report_path)
    input_path = descriptor.parent/item['input']
    if corruption == 'cost':
        del report['cost_usd']
    elif corruption == 'latency':
        report['wall_clock_s'] = float('nan')
    elif corruption == 'magnitude':
        item['examples'][0]['paraphrase'] = 'Synthetic: 125 claimed.'
    elif corruption == 'url':
        write_json(input_path, dict(url='https://unrelated.example/@fake', text='12.5 10'))
    elif corruption == 'verdict':
        report['claims'][0]['verdict'] = 'accuracy'
    elif corruption == 'outside':
        item['report'] = '../../../../outside.json'
    elif corruption == 'claim':
        report['claims'][0]['program_checks'] = []
    elif corruption == 'count':
        item['examples'] *= 4
    elif corruption == 'phase':
        config['phase'] = 'fresh_accuracy'
    # Deliberately retain malformed JSON number for parser/validation regression.
    report_path.write_text(json.dumps(report))
    write_json(descriptor, config)
    with pytest.raises(BuildError, match=match):
        rw.compile_evidence(tmp_path)


def test_pending_voice_fails_before_engine_or_synthesis():
    scene = next(s for s in STORY['scenes'] if s['id'] == rw.SCENE)
    builder = SimpleNamespace(repo=v3.ROOT, engine=lambda: pytest.fail('Do not synthesize pending narration'))
    if rw.load_snapshot(v3.ROOT)['status'] != 'ready':
        with pytest.raises(BuildError, match='evidence pending'):
            Builder.voice_spec(builder, scene)
        with pytest.raises(BuildError, match='evidence pending'):
            v3.compile_data(v3.ROOT, STORY, voices=[dict(voice_s=1, key=s['id']) for s in STORY['scenes']])


def test_active_preview_is_reproducible_and_preserves_all_host_outputs():
    paths = [v3.ROOT/v3.OUT/name for name in ('data.js','timing.json','keyframes.json','beats.json','cues.json')]
    before = {p:p.read_bytes() for p in paths if p.exists()}
    data = v3.compile_data(v3.ROOT, STORY)
    assert (v3.ROOT/v3.OUT/'preview-data.js').read_text() == v3.preview_artifact(data)
    assert len(data['scenes']) == 13
    assert data['timing']['duration'] == pytest.approx(177.2611)
    assert len([f for f in data['keyframes'] if f['position'].startswith('recorded-trace-step-')]) == 3
    assert before == {p:p.read_bytes() for p in before}
    if data['realworld']['status'] != 'ready':
        assert data['cues'][rw.SCENE] == []
    original = yaml.safe_load((v3.ROOT/'demo/tests/fixtures/storyboard-v007.yaml').read_text())
    assert [s['narration'] for s in STORY['scenes'] if s['id'] != rw.SCENE] == [s['narration'] for s in original['scenes']]
    assert STORY['voice'] == original['voice'] and STORY['music'] == original['music']
    for scene in STORY['scenes']:
        for source in scene['evidence']:
            assert (v3.ROOT/source).is_file()


def test_approved_trimmed_holds_fit_retained_voice_and_ten_second_new_line(tmp_path, monkeypatch):
    fixture_run(tmp_path)
    snapshot = rw.compile_evidence(tmp_path)
    monkeypatch.setattr(rw, 'load_snapshot', lambda *a, **k: snapshot)
    monkeypatch.setattr(v3, 'load_snapshot', lambda *a, **k: snapshot)
    lengths = LENGTHS[:-1]+[10., LENGTHS[-1]]
    voices = [dict(voice_s=n, key=s['id']) for s,n in zip(STORY['scenes'], lengths, strict=True)]
    data = v3.compile_data(v3.ROOT, STORY, voices=voices,
                           analyze=lambda scene, voice: pauses(scene['id'], voice['voice_s']))
    timing = data['timing']
    assert timing['duration'] == pytest.approx(177.2611) and timing['duration'] <= 180
    for shot, scene, voice in zip(timing['shots'], STORY['scenes'], voices, strict=True):
        assert (shot['start'],shot['end']) == pytest.approx((scene['target_start_s'],scene['target_end_s']))
        assert shot['voice_s'] == voice['voice_s'] and shot['hold_s'] >= .3
        assert shot['start'] in data['beats']['beats_s'] and shot['end'] in data['beats']['beats_s']
    reserve = next(s for s in timing['shots'] if s['id'] == rw.SCENE)
    assert reserve['end']-reserve['start'] == pytest.approx(11.3081)
    assert data['cues'][rw.SCENE][0]['text'].startswith('Saved real-world runs:')
    assert len([f for f in data['keyframes'] if f['position'].startswith('realworld-page-')]) == 2
    voices[-2]['voice_s'] = 10.01
    with pytest.raises(BuildError, match='must measure ≤ 10 s'):
        v3.compile_data(v3.ROOT, STORY, voices=voices)


def test_apple_ribbon_is_compiled_from_real_calls_costs_latencies_and_fact_ids():
    data = compile_trace(v3.ROOT)
    report = read_json(v3.ROOT/REPORT)
    apple = next(c for c in report['claims'] if c['ticker'] == 'AAPL')
    trace = read_json(v3.ROOT/data['source'])
    assert data['source'].endswith(apple['trace_path'])
    assert data['fact_ids'] == ['E1']
    assert [s['name'] for s in data['steps']] == ['lookup_fact','sub_claims','final_verdict']
    assert data['steps'][0]['tools'] == [trace['tool_calls'][0]['name']]
    assert data['cost_usd'] == pytest.approx(trace['cost_usd'])
    assert data['latency_s'] == pytest.approx(trace['latency_ms']/1000)
    for step, request in zip(data['steps'], trace['requests'], strict=True):
        assert step['cost_usd'] == request['cost']
        assert step['latency_s'] == request['latency_ms']/1000
    assert all(file_hash(v3.ROOT/p) == h for p,h in data['provenance'].items())


def test_reading_holds_fit_retained_audio_and_approved_reserve(tmp_path, monkeypatch):
    lengths = LENGTHS[:-1]+[6.64, LENGTHS[-1]]
    voices = [dict(voice_s=n, key=s['id']) for s,n in zip(STORY['scenes'], lengths, strict=True)]
    data = v3.compile_data(v3.ROOT, STORY, voices=voices,
                           analyze=lambda scene, voice: pauses(scene['id'], voice['voice_s']))
    extract = next(s for s in data['timing']['shots'] if s['id'] == 'v303-extract')
    event, = data['cues']['_events'][extract['id']]
    # N5: the unchanged 7.12 s extraction clip moves 1.05 s into its former hold.
    original = deepcopy(STORY)
    next(s for s in original['scenes'] if s['id'] == extract['id']).pop('narration_offset_s')
    before = v3.compile_data(v3.ROOT, original, voices=voices,
                            analyze=lambda scene, voice: pauses(scene['id'], voice['voice_s']))
    old_extract = next(s for s in before['timing']['shots'] if s['id'] == extract['id'])
    assert [(s['start'], s['end']) for s in data['timing']['shots']] == [
        (s['start'], s['end']) for s in before['timing']['shots']]
    assert extract['voice_s'] == old_extract['voice_s'] == 7.12
    assert extract['voice_start'] == pytest.approx(old_extract['voice_start']+1.05)
    assert extract['voice_end'] == pytest.approx(old_extract['voice_end']+1.05)
    assert extract['hold_s'] == pytest.approx(old_extract['hold_s']-1.05)
    assert extract['hold_s'] == pytest.approx(1.5127)
    assert event['t'] == before['cues']['_events'][extract['id']][0]['t'] == 22.7555
    reveal_frame = math.ceil(event['t']*30)/30
    assert reveal_frame == pytest.approx(22.766666667)
    assert event['cue_start'] == pytest.approx(22.770308257)
    assert event['cue_start'] >= reveal_frame-.1, 'Opinion audio precedes the opinion reveal'
    captions = sentence_subtitles(data['scenes'], data['timing'], data['cues'])
    opinion = next(c for c in captions if 'Forecasts and opinions' in c.text)
    assert opinion.start == 22.766
    assert opinion.start >= reveal_frame-.1, 'Opinion SRT precedes the opinion reveal'
    assert data['timing']['voice_keys'] == before['timing']['voice_keys']
    for shot in data['timing']['shots']:
        if shot['id'] != extract['id']:
            assert data['cues'][shot['id']] == before['cues'][shot['id']]
    # Exercise the real mix planner without FFmpeg or licensed narration.
    calls = []
    monkeypatch.setattr(media, 'ffmpeg', lambda args, log: calls.append(args))
    voice, bed = tmp_path/'existing-clip.wav', tmp_path/'existing-bed.wav'
    motion_media.mix_audio([voice], [extract], bed, -22, tmp_path/'mix.wav',
                           offset=data['timing']['music_offset_s'], timeline_duration=177.2611)
    args, = calls
    assert args[:4] == ['-t', '7.120000000', '-i', voice]
    graph = args[args.index('-filter_complex')+1]
    assert f'adelay={round(extract["voice_start"]*48000)}S:all=1' in graph
    assert 'atempo' not in graph
    assert event['t'] in data['beats']['beats_s']
    assert extract['end']-event['t'] >= 2.5
    assert {f['position'] for f in data['keyframes'] if f['position'].startswith('extract-')} == {
        'extract-amazon', 'extract-nvidia'}
    hover = next(s for s in data['timing']['shots'] if s['id'] == 'v304-hover')
    receipt, = [f for f in data['keyframes'] if f['position'] == 'recorded-trace-receipt']
    assert receipt['t'] == pytest.approx(hover['voice_start']-1.25, abs=1e-6)
    pages = [f for f in data['keyframes'] if f['position'].startswith('realworld-page-')]
    assert len(pages) == 4
    assert all(b['t']-a['t'] >= 2.5 for a,b in zip(pages, pages[1:]))
    assert data['timing']['duration'] == 177.2611
    overcrowded = deepcopy(data['realworld'])
    overcrowded['examples'].append(deepcopy(overcrowded['examples'][0]))
    with pytest.raises(BuildError, match='at least 2.5 s'):
        v3.keyframes(data['timing'], data['hover_anchors'], realworld=overcrowded)
