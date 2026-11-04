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
def receipt(v5_story):
    return json.loads(Path(v5_story['scenes'][5]['recording']['receipt']).read_text())


def test_terminal_uses_pod_elapsed_not_arrival_or_response_events(receipt):
    before=copy.deepcopy(receipt);trace=compile_live_terminal(receipt)
    assert trace['title']=='Online · hackathon.dappgo.com'
    assert trace['honesty_label']=='live request 00000000 · pod log'
    assert trace['typing_start_scene_s']==pytest.approx(trace['start_scene_s'])
    assert 'command' not in trace and trace['rows'][0]['kind']=='request'
    assert trace['rows'][2]['at_s']==2.13 # JSONL host arrivals are all after +100 s.
    assert trace['rows'][3]['text'].endswith('2023Q3  → E1')
    assert trace['rows'][-1]['text']=='verdict  contradicted  16.4 s  $0.0215'
    assert trace['verdict']['at_s']==16.41
    assert receipt==before
    receipt['result']['events']=[]
    assert compile_live_terminal(receipt)==trace # Never reconstruct a log from receipt events.


@pytest.mark.parametrize('change', ['missing','hash','id','cost','verdict','reveal'])
def test_missing_or_mismatched_real_logs_fail_closed(receipt,change):
    if change=='missing':receipt.pop('server_log')
    if change=='hash':receipt['server_log']['sha256']='f'*64
    if change=='id':receipt['server_log']['request_id']='1'*32
    if change=='cost':receipt['result']['cost_is_bound']=True
    if change=='verdict':receipt['result']['verdict']='supported'
    if change=='reveal':
        next(t for t in receipt['timings'] if t['phase']=='verdict_reveal')['at_s']=0
    with pytest.raises(BuildError):compile_live_terminal(receipt)


def test_local_cli_is_byte_identical_and_final_receipt_is_real():
    from live_terminal_v5 import compile_local_terminal
    from pipeline import file_hash
    trace=compile_local_terminal(ROOT)
    session=json.loads((ROOT/'demo/assets/cli-v5/local-cli.json').read_text())
    assert trace['session_sha256']==file_hash(ROOT/'demo/assets/cli-v5/local-cli.json')
    assert trace['source_duration_s']==38.571843 and not session['dry_run']
    assert all(len(f['rows'])<=5 and all(len(r['text'])<=98 for r in f['rows']) for f in trace['frames'])
    assert len(trace['rows'])==12
    assert not any('screen_reason' in r['text'] or 'event=' in r['text'] for f in trace['frames'] for r in f['rows'])
    assert 'uv run python -m claimcheck post docs/examples/post.txt' in trace['command']
    assert trace['frames'][-1]['rows'][-1]['text']=='verdict  2 supported · 1 contradicted  38.6 s  $0.0611'
    arrivals={c['t_rel_s'] for c in session['chunks']}
    assert all(f['at_s'] in arrivals for f in trace['frames'])
    assert len([r for r in trace['rows'] if len(r['source_event_indices'])==2])==5
    assert trace['rows'][-1]['source_elapsed_s']==38.32
    assert trace['rows'][2]['text']=='+9.8 s  lookup_fact  AMZN  revenue  2023Q3  → E1'
    assert trace['rows'][3]['args']['phase']=='completed' and trace['rows'][3]['args']['count']=='2'
    assert trace['rows'][3]['text']=='+15.8 s  model · step 2'


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


def test_compiled_voice_status_is_honest_and_other_scenes_keep_measurements(v5_story):
    data=compile_data(story=v5_story,preview=True)
    if data['portable_inputs']['voices'][5] is None:
        assert data['cues']['_methods']['v505']=='target preview; unmeasured'
        assert not any(e['measured'] for e in data['cues']['v505'])
    assert all(data['cues']['_methods'][f'v50{i}']=='measured PCM speech bounds per sentence/phrase' for i in range(10) if i not in (5,6))
    assert any(f['cue']=='terminal verdict and stopped clock' for f in data['keyframes'])


def test_jsonl_absence_is_not_repaired_by_a_portable_response_trace(receipt):
    receipt['server_log']['path']='demo/cache/live-takes/v5/nonexistent-r6-server-log.jsonl'
    with pytest.raises(BuildError,match='JSONL missing'):compile_live_terminal(receipt)


@pytest.mark.parametrize('change',['order','other_id','no_verdict','bounded'])
def test_invalid_captured_log_is_rejected_even_with_a_matching_file_hash(receipt,tmp_path,change):
    from pipeline import file_hash
    rows=[json.loads(line) for line in (ROOT/receipt['server_log']['path']).read_text().splitlines()]
    if change=='order':rows[2],rows[3]=rows[3],rows[2]
    if change=='other_id':rows[3]['line']=rows[3]['line'].replace('0'*32,'1'*32)
    if change=='no_verdict':rows.pop()
    if change=='bounded':rows[-1]['line']=rows[-1]['line'].replace('cost_is_bound=false','cost_is_bound=true')
    path=tmp_path/'captured.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    receipt['server_log'].update(path=path.name,sha256=file_hash(path))
    with pytest.raises(BuildError):compile_live_terminal(receipt,tmp_path)
