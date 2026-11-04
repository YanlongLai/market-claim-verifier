"""Frozen trace and PCM scheduling checks; no browser, synthesis or SEC request."""
import copy,json
from pathlib import Path

import pytest

from live_terminal_v5 import compile_live_terminal,trace_events
from motion_v5 import compile_data,cue_spans
from pipeline import BuildError
from record_v5 import live_cue_events,RecordingError

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture
def receipt():
    return json.loads((ROOT/'demo/motion/v5/inputs.json').read_text())['recordings']['v505']['receipt']


def test_live_trace_rebuild_uses_actual_times_arguments_and_matched_evidence(receipt):
    before=copy.deepcopy(receipt);trace=compile_live_terminal(receipt)
    assert trace['command']=='$ claimcheck post post.txt --provider baseten --budget 1'
    assert trace['typing_start_scene_s']==pytest.approx(trace['start_scene_s']-.6)
    assert [c['evidence_id'] for c in trace['calls']]==['E1','E2','E3','E6']
    assert [c['at_s'] for c in trace['calls']]==pytest.approx([2.129651,2.400641,2.701321,6.8446])
    assert [c['arguments']['ticker'] for c in trace['calls']]==['AMZN','NVDA','AAPL','NVDA']
    assert 'FY2024 vs FY2023  → E6' in trace['calls'][-1]['text']
    assert trace['reasoning_at_s']==pytest.approx(7.334576)
    assert trace['verdict']['at_s']==pytest.approx(16.412355)
    assert trace['verdict_text']=='verdict  contradicted   16.4 s   $0.02'
    assert receipt==before


def test_later_take_rebinds_clock_rows_evidence_cost_and_provider(receipt):
    receipt['result'].update(provider='meta',cost_usd=.034,verdict='supported')
    for event in receipt['result']['events']:
        event['at_ms']+=100
        if event['kind']=='tool_result':event['result']['evidence_id']='E99'
        if event['kind']=='tool_call':event['arguments']['ticker']='MSFT'
        if event['kind']=='verdict':event['verdict']='supported'
    trace=compile_live_terminal(receipt)
    assert '--provider meta' in trace['command']
    assert all('MSFT' in c['text'] and c['text'].endswith('→ E99') for c in trace['calls'])
    assert trace['verdict_text']=='verdict  supported   16.5 s   $0.03'
    assert compile_live_terminal(dict(receipt,result={**receipt['result'],'events':trace_events(receipt['result']['events'])}))==trace


@pytest.mark.parametrize('mutation',[
    lambda r:r['result']['events'].pop(),
    lambda r:r['result']['events'][2]['result'].pop('evidence_id'),
    lambda r:r['result']['events'][2].update(name='unmatched_tool'),
    lambda r:r['result']['events'][1].update(at_ms=-1),
    lambda r:r['result']['events'][0].update(at_ms=-.5),
    lambda r:r['result']['events'][-1].update(verdict='supported'),
    lambda r:r['result'].update(cost_is_bound=True),
    lambda r:r['result']['events'][-1].update(at_ms=999999),
])
def test_incomplete_or_mismatched_trace_is_refused(receipt,mutation):
    mutation(receipt)
    with pytest.raises(BuildError):compile_live_terminal(receipt)


def unit(event,start,duration=1,leading=.1):
    return dict(event=event,narration='A sentence.',source_start_s=start,source_end_s=start+duration,
        speech_start_s=leading,speech_end_s=duration-.1,audio_sha256='a'*64,
        measurement=dict(method='measured PCM speech bounds',audio_sha256='a'*64))


def test_phase_local_sentences_queue_whole_pcm_and_measure_independent_onsets():
    events=[dict(event=name,narration='A sentence.',receipt_phase=phase,at_scene_s=at,offset_s=offset)
        for name,phase,at,offset in [('tools','check_against_sec',0,0),('claims','check_against_sec',.8,.8),('verdict','verdict_reveal',6,0)]]
    scene=dict(id='v505',target_s=10,cue_events=events)
    resolved=live_cue_events(scene,{'timings':[dict(phase='check_against_sec',at_s=0),dict(phase='verdict_reveal',at_s=6)]})
    assert [e['at_scene_s'] for e in resolved]==[0,.8,6]
    voice={'cue_spans':[unit('tools',0,2.4),unit('claims',2.4),unit('verdict',3.4)]}
    spans=list(cue_spans(scene,voice))
    _,first,length,_=spans[0];_,second,_,_=spans[1]
    assert first==pytest.approx(.1) and length==2.4
    assert second>=first+length+.06-1e-9
    assert second+spans[1][3]['speech_start_s']>events[1]['at_scene_s']


def test_even_a_fitting_phase_sentence_must_leave_point_four_seconds_before_verdict():
    scene=dict(id='v505',target_s=8,cue_events=[
        dict(event='tools',narration='A sentence.',receipt_phase='check_against_sec',at_scene_s=0),
        dict(event='verdict',narration='A sentence.',receipt_phase='verdict_reveal',at_scene_s=4)])
    voice={'cue_spans':[unit('tools',0,3.5),unit('verdict',3.5)]}
    list(cue_spans(scene,voice))  # Ends exactly at 3.6 s; all PCM is retained.
    voice['cue_spans'][0]=unit('tools',0,3.51)
    with pytest.raises(BuildError,match='0.4 s margin'):list(cue_spans(scene,voice))


@pytest.mark.parametrize('offset',[float('nan'),float('inf'),-1,True,6])
def test_phase_offsets_cannot_be_invalid_or_cross_the_verdict(offset):
    scene=dict(target_s=10,cue_events=[dict(event='tools',receipt_phase='check_against_sec',offset_s=offset)])
    with pytest.raises(RecordingError):live_cue_events(scene,{'timings':[
        dict(phase='check_against_sec',at_s=0),dict(phase='verdict_reveal',at_s=6)]})


def test_compiled_voice_status_is_honest_and_other_scenes_keep_measurements():
    data=compile_data()
    if data['portable_inputs']['voices'][5] is None:
        assert data['cues']['_methods']['v505']=='target preview; unmeasured'
        assert not any(e['measured'] for e in data['cues']['v505'])
    assert all(data['cues']['_methods'][f'v50{i}']=='measured PCM speech bounds per sentence/phrase' for i in range(10) if i!=5)
    assert any(f['cue']=='terminal verdict and stopped clock' for f in data['keyframes'])
