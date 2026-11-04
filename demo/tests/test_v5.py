"""V5 source, provenance, timing and recorder contracts; never invokes a model."""
import copy,json,wave
from pathlib import Path
import pytest,yaml
from build import Builder,parser
from motion_build import motion_folder,renderer_args
from motion_v5 import BOUNDARIES,LIVE_PHASES,ROOT,CJK,artifacts,compile_data,cue_spans,validate
from pipeline import BuildError,file_hash,read_json
import record_v5 as recorder

@pytest.fixture(scope='module')
def story(v5_story):return v5_story
@pytest.fixture(scope='module')
def data(story):return compile_data(story=story,preview=True)

@pytest.mark.parametrize('i',range(10))
def test_binding_scene_table(story,i):
    s=story['scenes'][i]
    assert s['id']==f'v50{i}'
    assert [s['target_start_s'],s['target_end_s'],s['target_s']]==[BOUNDARIES[i],BOUNDARIES[i+1],BOUNDARIES[i+1]-BOUNDARIES[i]]

def test_chapter_durations_and_safe_lane(story):
    bar=story['chapter_bar'];assert sum(s['duration_s'] for s in bar['segments'])==178
    assert [s['label'] for s in bar['segments']]==['Intro','Post','Inputs','Why','How','Live','Batch','Results','Fix','DappGo']
    assert bar['height_px']==12 and bar['label_font_px']>=32
    assert bar['top_px']+bar['height_px']<=bar['caption_zone_top_px']==880

def test_phase_coverage_and_real_receipt_clock(story):
    scene=story['scenes'][5]
    assert tuple(dict.fromkeys(e['receipt_phase'] for e in scene['cue_events']))==LIVE_PHASES
    receipt=read_json(Path(scene['recording']['receipt']))
    receipt=recorder.with_phase_aliases(receipt)
    bases={t['phase']:t['at_s'] for t in receipt['timings']}
    events=recorder.live_cue_events(scene,receipt)
    from live_terminal_v5 import read_server_log
    rows=read_server_log(receipt,ROOT)
    assert [e['at_scene_s'] for e in events]==[bases[e['receipt_phase']]+e.get('offset_s',0)+
        (next(r['at_s'] for r in rows if r['event']==e['log_event']) if e.get('log_event') else 0) for e in events]
    by_name={e['event']:e for e in events}
    assert by_name['trace']['receipt_phase']=='tool_call_2_reveal'
    assert by_name['each']['receipt_phase']=='tool_call_4_reveal'
    assert by_name['program']['receipt_phase']=='program_verdict_reveal'
    receipt['timings']=[t for t in receipt['timings'] if t['phase']!='hover_receipt']
    with pytest.raises(recorder.RecordingError):recorder.live_cue_events(scene,receipt)

def synthetic_voices(story):
    voices=[]
    for scene in story['scenes']:
        spans=[]
        for i,event in enumerate(scene['cue_events']):
            m=dict(method='measured PCM speech bounds',audio_sha256='f'*64,sample_rate=24000,window_frames=120,threshold_dbfs=-50,onset_frame=2400,end_frame=19200,speech_start_s=.1,speech_end_s=.8)
            spans.append(dict(event=event['event'],narration=event['narration'],source_start_s=i,source_end_s=i+1,speech_start_s=.1,speech_end_s=.8,audio_sha256='f'*64,voice_key=event['event'],measurement=m))
        voices.append(dict(voice_s=len(spans),key=scene['id'],artifacts={'audio':{'sha256':'f'*64}},cue_spans=spans))
    return voices

@pytest.fixture(scope='module')
def measured_data(story):return compile_data(story=story,voices=synthetic_voices(story))

def test_picture_leads_every_measured_unit_without_hiding_previous_speech(measured_data):
    for scene in measured_data['scenes']:
        previous_end=-1
        for event in measured_data['cues']['_events'][scene['id']]:
            assert .1-1e-7<=event['cue_start']-event['picture_start']<=.3+1e-7
            assert event['picture_start']>=previous_end-1e-7
            assert event['alignment']=='measured PCM speech bounds'
            previous_end=event['cue_end']
    assert len(measured_data['cues']['_events']['v505'])==15

def test_every_boundary_and_phase_has_keyframe(data):
    frames=data['keyframes']
    assert {f['t'] for f in frames}>={float(t) for t in BOUNDARIES[:-1]}
    for e in data['cues']['_events']['v505']:assert any(f['shot']=='v505' and f['t']==e['t']+.15 for f in frames)
    assert sum(f['cue']=='chapter sample' for f in frames)==5

def test_sentence_ledger_covers_every_phrase_with_start_and_end_evidence(measured_data):
    data=measured_data
    from sync_v5 import ledger_rows
    index=[dict(shot=f['shot'],t=f['t'],captioned_file=f"captioned/{i:04}.png") for i,f in enumerate(data['keyframes'])]
    for frame in index:
        events=[e for e in data['cues']['_events'][frame['shot']] if e['cue_start']-1e-7<=frame['t']<=e['cue_end']+1e-7]
        frame['frame_audit']=[dict(scene=frame['shot'],event=e['event'],at_s=frame['t'],status='pass',measured=True,elements=[{'name':'synthetic native proof'}]) for e in events]
        for check in frame['frame_audit']:
            if check['scene']=='v505' and check['event']=='verdict':check.update(referents=['verdict','filing'],filings=[{'form':'10-K'},{'form':'10-Q'}])
            if check['scene']=='v505' and check['event'] in ('tools','claims','lookups','evidence_ids','thinking','decide'):
                check.update(referents=['terminal window','recorded log events'],elements=[{'name':'.live-terminal'}],semantic={'status':'pass'})
    rows=ledger_rows(data['timing'],data['cues'],index)
    expected=sum(len(data['cues'][s['id']]) for s in data['scenes'])
    assert len(rows)==expected
    assert all(r['status']=='pending' and r['verified_frame'] is None for r in rows)
    assert {r['cue_unit'] for r in rows if r['scene']=='v505'}=={'live','paste','tools','claims','lookups','evidence_ids','thinking','decide','verdict','draft','evidence','trace','each','program','receipt'}
    assert all(r['measured_onset'] and r['actual_sentence_start_s']==r['cue_start_s'] and r['cue_start_s']<r['cue_end_s'] and r['required_visual'] for r in rows)
    bad=copy.deepcopy(index);[f.pop('frame_audit') for f in bad]
    with pytest.raises(BuildError,match='actual-frame'):ledger_rows(data['timing'],data['cues'],bad)
    with pytest.raises(BuildError):ledger_rows(data['timing'],data['cues'],[])
    bad=copy.deepcopy(index)
    for f in bad:
        for check in f['frame_audit']:
            if check['scene']=='v505' and check['event']=='verdict':check.pop('referents')
    with pytest.raises(BuildError,match='both verdict and filing'):ledger_rows(data['timing'],data['cues'],bad)
    assert '10-K fiscal 2025 annual' in next(r for r in rows if r['cue_unit']=='verdict' and r['scene']=='v505')['required_visual']
    bad=copy.deepcopy(index)
    for f in bad:
        for check in f['frame_audit']:
            if check['scene']=='v505' and check['event']=='thinking':check.pop('referents')
    with pytest.raises(BuildError,match='named real log events'):ledger_rows(data['timing'],data['cues'],bad)

def test_english_only_templates_data_and_captions(data):
    for p in (ROOT/'demo/motion/v5').iterdir():
        if p.suffix in {'.js','.mjs','.css','.html','.srt','.json'}:assert not CJK.search(p.read_text()),p
    assert not CJK.search(json.dumps(data,ensure_ascii=False))
    for cue in data['subtitles']:
        assert len(cue['text'].splitlines())<=2
        assert max(map(len,cue['text'].splitlines()))<=42
        assert 0<=cue['start']<cue['end']<=178
    with pytest.raises(BuildError):
        changed=copy.deepcopy(data['scenes'][0]);changed['narration']='\u4e2d';s=yaml.safe_load((ROOT/'demo/storyboard-v5.yaml').read_text());s['scenes'][0]=changed;validate(s)

def test_real_input_bytes_and_derived_previews(data):
    receipt=json.loads((ROOT/'demo/assets/examples-v5/receipt.json').read_text())
    assert {Path(r['path']).suffix for r in receipt['inputs']}>={'.png','.pdf','.mp3','.mp4'}
    for item in receipt['inputs']+receipt['derived']:assert file_hash(ROOT/item['path'])==item['sha256']
    assert [i['label'] for i in data['inputs']]==['Screenshot','PDF','Audio','Video']
    assert data['inputs'][1]['preview'].endswith('a-pdf-page1.png')
    assert len(data['waveform'])==64 and max(data['waveform'])==1
    assert 'Apple pulled in $416.2 billion' in data['post_text']

def test_terminal_blocks_match_narrated_clauses(story,data):
    receipt=data['terminal_replays']['beat6']
    assert receipt['duration_s']==22
    blocks={b['block']:b['at_s'] for b in receipt['blocks']}
    for e in data['scenes'][6]['cue_events']:
        assert blocks[e['event']]==pytest.approx(e['picture_at_scene_s'])
    assert [b['block'] for b in receipt['blocks']]==['run','ocr','asr','median','projection']
    comparison=data['terminal_replays']['beat3'];assert comparison['duration_s']==14
    starts={b['block']:b['at_s'] for b in comparison['blocks']}
    for e in data['scenes'][3]['cue_events']:
        assert starts[e['terminal_block']]==pytest.approx(e['picture_at_scene_s'])

def test_legacy_take_preserved_but_cannot_enter_final_film(story,data):
    retained=read_json(ROOT/'demo/prep/v5/r3/inputs-before.json')
    assert retained['recordings']['v505']['receipt']['capture_version']==7
    assert data['portable_inputs']['recordings']['v505']['receipt']['capture_version']==9
    assert recorder.CAPTURE_VERSION==9
    pending=copy.deepcopy(story)
    for scene in pending['scenes']:
        if scene['id'] in recorder.BEATS:scene.pop('recording',None);scene['placeholder']=True
    with pytest.raises(recorder.RecordingError,match='live take missing'):recorder.check_recordings(pending)
    assert recorder.BEATS=={'v505':('beat6',58.),'v508':('beat9',16.)}
    for scene in story['scenes']:
        if scene['id'] in recorder.BEATS:assert bool(scene.get('placeholder'))!=bool(scene.get('recording'))

def proof():
    events=[{'kind':'model'}]+[e for _ in range(4) for e in ({'kind':'tool_call'},{'kind':'tool_result'})]+[{'kind':'verdict'}]
    phases=list(dict.fromkeys([*LIVE_PHASES,'agent_trace_expand','tool_call_6_reveal','tool_call_8_reveal']))
    timings=[dict(phase=phase,at_s=i+1) for i,phase in enumerate(phases)]
    rect=dict(name='native referent',left=180,right=800,top=180,bottom=400)
    return dict(capture_version=recorder.CAPTURE_VERSION,zoom=1.95,live_checks=1,result={'events':events},timings=timings,
        startup_cover=dict(injected_before_content=True,colour='#f7f5ef',cover_present=True,cover_opaque=True,layout_installed=True,zoom=1.95,release_geometry_index=0,released_at_s=-.1,workspace_framed_before_release=True,decoded_workspace_start=True,workspace_rect=dict(left=180,right=1740,top=180,bottom=480),source_start_s=1.1,first_native_frame_s=1.,source_cover_release_s=.95,video_clock_offset_s=.05),
        named_element_checks=[dict(t,elements=[dict(rect)],visible_until_s=t['at_s']+1,overlay_band='bottom',card_edge_audit=dict(status='pass',band=dict(left=80,right=1840,top=558,bottom=790),lines=[dict(rect)],controls=[],input_charge=dict(rect,top=-80,bottom=-1),corrected_heading=dict(rect,top=600,bottom=660))) for t in timings],
        ending_frame={'both_links':2,'visible_together':True,'named_elements':[dict(rect),dict(rect),dict(rect)]},
        geometry_checks=[{'at_s':-.2,'zoom':1.95,'source_width':1560,'left_margin':180,'right_margin':180,'horizontal_overflow':0}],
        language_checks=[{'text_nodes':0,'attributes':0,'language_switches':0}],choreography={'trace_details_open':True,'apple_inspect_open':True,'program_verdict_shown':True,'after_click_s':50,'beat6_actions_end_s':55,'trace_steps_shown':[{'index':i,'kind':e['kind'],'visible':True,'hold_ms':700} for i,e in enumerate(events) if e['kind'] in ('tool_call','verdict')],'apple_derivation':{'annual':416161000000,'nine_months':313695000000,'quarter':102466000000,'hold_ms':2000}})

def test_recorder_validates_actual_raw_apple_values():recorder.check_choreography(proof())
@pytest.mark.parametrize('mutation',[
 lambda p:p['geometry_checks'][0].update(source_width=1499),
 lambda p:p['geometry_checks'][0].update(left_margin=185),
 lambda p:p['geometry_checks'][0].update(right_margin=59),
 lambda p:p['language_checks'][0].update(text_nodes=1),
 lambda p:p['language_checks'][0].update(language_switches=1),
 lambda p:p['choreography'].update(trace_details_open=False),
 lambda p:p['choreography']['apple_derivation'].update(quarter=102500000000),
 lambda p:p['choreography']['trace_steps_shown'].pop(1),
 lambda p:p.update(live_checks=2),
 lambda p:p['ending_frame'].update(both_links=1),
 lambda p:p.update(capture_version=6),
 lambda p:p.pop('startup_cover'),
 lambda p:p['startup_cover'].update(injected_before_content=False),
 lambda p:p['startup_cover'].update(released_at_s=.8),
 lambda p:p['startup_cover'].update(release_geometry_index=1),
 lambda p:p['geometry_checks'][0].update(zoom=1),
 lambda p:p['named_element_checks'].pop(),
 lambda p:p['named_element_checks'][0].update(at_s=0),
 lambda p:p['named_element_checks'][0]['elements'][0].update(bottom=559),
 lambda p:p['named_element_checks'][0].pop('card_edge_audit'),
 lambda p:p['named_element_checks'][0]['card_edge_audit']['lines'][0].update(top=530,bottom=590),
 lambda p:p['named_element_checks'][0]['card_edge_audit']['controls'].append(dict(left=180,right=500,top=540,bottom=600)),
 lambda p:p['named_element_checks'][3]['card_edge_audit']['input_charge'].update(bottom=1),
 lambda p:p['named_element_checks'][3]['card_edge_audit']['corrected_heading'].update(top=540,bottom=610),
])
def test_capture_failures_are_rejected(mutation):
    receipt=proof();mutation(receipt)
    with pytest.raises(recorder.RecordingError):recorder.check_choreography(receipt)

def test_no_early_or_overrunning_voice(story):
    scene=copy.deepcopy(story['scenes'][5]);voice=synthetic_voices(story)[5]
    placed=list(cue_spans(scene,voice));assert placed[0][1]==pytest.approx(.1)
    bad=copy.deepcopy(voice);bad['cue_spans'][0].pop('measurement')
    with pytest.raises(BuildError,match='measured sentence onset'):list(cue_spans(scene,bad))
    voice['cue_spans'][0]['source_end_s']=scene['target_s']
    with pytest.raises(BuildError,match='no speech is cut or accelerated'):list(cue_spans(scene,voice))

def test_unchanged_voice_cache_aliases_and_renderer(tmp_path,story):
    # The disposable verifier does not need the private narrator reference.
    demo=tmp_path/'demo';(demo/'assets/voice').mkdir(parents=True)
    with wave.open(str(demo/'assets/voice/narrator-ref.wav'),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000);wav.writeframes(b'\0\0'*2400)
    (demo/'storyboard-v4.yaml').write_bytes((ROOT/'demo/storyboard-v4.yaml').read_bytes())
    (demo/'storyboard-v5.yaml').write_text(yaml.safe_dump(story))
    b=Builder(parser().parse_args(['keyframes','--storyboard',str(demo/'storyboard-v5.yaml')]),demo=demo)
    assert motion_folder(b)==demo/'motion/v5' and renderer_args(b)==['--entry','v5/index.html']
    for s in b.scenes:
        if s.get('voice_cache_scene'):
            _,_,folder=b.voice_spec(s);assert folder.parent.name==s['voice_cache_scene']

def test_synthetic_compile_is_deterministic_and_production_has_no_log_fallback(data):
    assert artifacts(data)==artifacts(copy.deepcopy(data))
    actual=yaml.safe_load((ROOT/'demo/storyboard-v5.yaml').read_text())
    saved=read_json(ROOT/'demo/motion/v5/inputs.json')['recordings']['v505']['receipt']
    if not saved.get('server_log'):
        with pytest.raises(BuildError,match='server-log JSONL required'):compile_data(story=actual,preview=True)

def test_rendered_on_screen_is_the_storyboard_copy(story,data):
    import xml.etree.ElementTree as ET
    from motion_v5 import architecture
    heading=ET.fromstring(data['architecture_svg']).find('.//*[@data-on-screen="v504"]')
    assert heading.text==story['scenes'][4]['on_screen']
    changed='Model & program: <a different storyboard headline>.'
    assert ET.fromstring(architecture(ROOT,changed)).find('.//*[@data-on-screen="v504"]').text==changed
    assert 'disclosure' not in data['brand']  # One source: v500.on_screen, exercised in the JS renderer test.

def test_portable_measured_metadata_rebuilds_without_private_media(story,measured_data,monkeypatch):
    import motion_v5
    data=measured_data
    read=motion_v5.read_json
    monkeypatch.setattr(motion_v5,'read_json',lambda p:data['portable_inputs'] if p==ROOT/'demo/motion/v5/inputs.json' else read(p))
    original=Path.is_file
    monkeypatch.setattr(Path,'is_file',lambda p:False if 'cache/live-takes/' in p.as_posix() else original(p))
    assert compile_data(story=story)==data
    assert data['asset_status']['voice']=='measured'

def test_batch_run_is_real_cli_and_old_saved_run_is_empty(data):
    run=data['terminal_replays']['beat6']['blocks'][0]
    assert run['block']=='run' and run['at_s']==0
    assert all(not frame['rows'] for frame in run['frames'])
    trace=data['local_terminal'];window=trace['end_scene_s']-trace['start_scene_s']
    assert trace['source_duration_s']/trace['speed']<window
    assert trace['speed']==3 and trace['honesty_label']=='replayed at 3× · 38.6 s run'
    assert trace['end_scene_s']==22
    assert 'CoreWeave' not in trace['command']
    assert data['batch_labels']['median']=='78 attempts · 72 completed · median 6.8 s'


def test_every_new_named_element_onset_has_an_exact_review_frame(data):
    for check in data['live_named_elements']:
        assert any(f['shot']=='v505' and f['t']==58+check['at_s'] for f in data['keyframes'])
    assert {170.,170.3,170.6,171.1,171.6}<={f['t'] for f in data['keyframes'] if f['shot']=='v509'}

def test_legacy_originals_are_retained_and_demo_text_has_no_literal_cjk():
    archive=ROOT/'docs/evidence/demo-language-history/2026-11-04'
    records=read_json(archive/'manifest.json')['records']
    assert len(records)==17
    for record in records:
        assert file_hash(ROOT/record['original'])==record['original_sha256']
        assert file_hash(ROOT/record['path'])==record['source_sha256']
    for path in (ROOT/'demo').rglob('*'):
        if set(path.relative_to(ROOT/'demo').parts)&{'cache','out','.venv','.cache','__pycache__','.pytest_cache'}:continue
        if path.is_file() and path.suffix in {'.py','.js','.mjs','.json','.yaml','.md','.txt','.html','.css','.srt','.log'}:
            assert not CJK.search(path.read_text()),path

def test_escaped_legacy_source_retains_decoded_values_and_cache_identity():
    from pipeline import escape_cjk_source,cache_key
    value={'quote':'\u4e2d\u6587','non_bmp':'\U00020000','latin':'café'}
    source=escape_cjk_source(json.dumps(value,ensure_ascii=False))
    assert not CJK.search(source)
    assert json.loads(source)==value
    assert cache_key(json.loads(source))==cache_key(value)
    assert 'café' in source

def test_headline_metrics_from_frozen_reference(data):
    m=data['metrics'];assert (m['heldout_correct'],m['heldout_n'],m['false_support'],m['negative_n'])==(240,266,1,139)
    assert round(m['mean_cost_usd'],2)==.02 and round(m['median_claim_seconds'])==10

def test_local_ocr_selection_covers_twenty_frames_and_all_states(data):
    from review_v5 import select
    index=[dict(f,captioned_file=f"captioned/{i}.png") for i,f in enumerate(data['keyframes'])]
    chosen=select(index)
    assert len(chosen)>=24 and {f['shot'] for f in chosen}=={f'v50{i}' for i in range(10)}
    assert {f.get('event') or f.get('cue') for f in chosen if f['shot']=='v505'}>={'claims','lookups','evidence_ids','thinking','decide'}
    assert {e['event'] for e in data['scenes'][5]['cue_events']}<={f['cue'] for f in chosen if f['shot']=='v505'}

def test_cue_audio_assembly_retains_every_sample_and_receipts(tmp_path):
    import struct
    from types import SimpleNamespace
    from voice_v5 import require
    rows={};contents=[]
    for i in range(2):
        path=tmp_path/f'unit-{i}.wav';raw=struct.pack('<h',1000+i)*2400;contents.append(raw)
        with wave.open(str(path),'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000);wav.writeframes(raw)
        rows[f'v505-{i}']={'key':str(i),'engine':'breeze-tts-2','artifacts':{'audio':{'path':str(path),'sha256':file_hash(path)}}}
    def stage(*parts):
        path=tmp_path.joinpath(*parts);path.mkdir(parents=True,exist_ok=True);return path
    builder=SimpleNamespace(require_voice=lambda s:rows[s['id']],stage_dir=stage)
    scene={'id':'v505','narration':'First. Second.','cue_events':[{'event':str(i),'narration':text} for i,text in enumerate(['First.','Second.'])]}
    voice=require(builder,scene)
    with wave.open(voice['artifacts']['audio']['path']) as wav:assert wav.readframes(wav.getnframes())==b''.join(contents)
    assert voice['voice_s']==.2
    assert [s['source_start_s'] for s in voice['cue_spans']]==[0,.1]
    assert [s['source_end_s'] for s in voice['cue_spans']]==[.1,.2]
    assert require(builder,scene)==voice

def test_every_sentence_has_a_private_unit_and_no_multi_sentence_alias(story):
    from voice_v5 import units
    assert sum(len(s['cue_events']) for s in story['scenes'])==48
    for scene in story['scenes']:
        assert not scene.get('voice_cache_scene')
        assert [u['narration'] for u in units(scene)]==[e['narration'] for e in scene['cue_events']]
        for unit in units(scene):assert unit['id'].startswith(scene['id']+'-')
    for mutation in ('remove','merge','alias'):
        changed=copy.deepcopy(story);scene=changed['scenes'][1]
        if mutation=='remove':scene['cue_events']=[]
        elif mutation=='merge':scene['cue_events'][0]['narration']+=' Another sentence.'
        else:scene['voice_cache_scene']='v402'
        with pytest.raises(BuildError):validate(changed)


def test_pcm_bounds_measure_leading_trailing_silence_and_keep_internal_pause(tmp_path):
    import struct
    from voice_v5 import measure_unit
    path=tmp_path/'sentence.wav';rate=24000
    # 0.20 s silence / 0.30 s speech / 0.25 s internal pause /
    # 0.40 s speech / 0.15 s silence. A single click is not speech.
    samples=[0]*4800+[1000]*7200+[0]*6000+[1500]*9600+[0]*3600
    samples[300]=30000
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
        wav.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    m=measure_unit(path)
    assert m['speech_start_s']==pytest.approx(.2)
    assert m['speech_end_s']==pytest.approx(1.15)
    assert m['audio_sha256']==file_hash(path)
    assert m['onset_frame']==4800 and m['end_frame']==27600


def test_sync_refuses_any_unmeasured_row_even_with_real_frame_names(data):
    from sync_v5 import ledger_rows
    data=copy.deepcopy(data)
    data['cues']['_methods']['v505']='target preview; unmeasured'
    index=[dict(shot=f['shot'],t=f['t'],captioned_file=f'{i}.png') for i,f in enumerate(data['keyframes'])]
    with pytest.raises(BuildError,match='measured sentence onset'):ledger_rows(data['timing'],data['cues'],index)


def test_compiler_does_not_abandon_native_evidence_mid_sentence(story):
    import record_v5
    from unittest.mock import patch
    changed=copy.deepcopy(story)
    changed['scenes'][5].pop('placeholder',None);changed['scenes'][5]['recording']={'asset':'absent.mp4','receipt':'absent.json','receipt_sha256':'a'*64,'offset_s':0}
    receipt=read_json(Path(story['scenes'][5]['recording']['receipt']))
    for check in receipt['named_element_checks']:check['visible_until_s']=check['at_s']+.3
    changed['scenes'][5].pop('native_holds',None)
    # Inject a retained capture summary, never an accepted take. The compiler must
    # reject its inadequate hold even though the audio and reveal clocks are valid.
    import motion_v5
    saved=copy.deepcopy(read_json(ROOT/'demo/motion/v5/inputs.json'))
    receipt['result']=saved['recordings']['v505']['receipt']['result']
    receipt['result'].pop('request_id',None)
    saved['recordings']['v505']={'recording':changed['scenes'][5]['recording'],'receipt':receipt}
    read=motion_v5.read_json
    with patch.object(motion_v5,'read_json',side_effect=lambda p:saved if p==ROOT/'demo/motion/v5/inputs.json' else read(p)):
        with pytest.raises(BuildError,match='not held through'):compile_data(story=changed,voices=synthetic_voices(changed))


def test_decoded_workspace_start_rejects_paper_black_and_premature_content():
    size=96*54
    paper=bytes([247])*size;black=bytes(size)
    workspace=(bytes([250,30])*((size+1)//2))[:size]
    frames=black*3+paper*27+workspace*8
    assert recorder.workspace_start(frames,1)==pytest.approx(1.1)
    for raw,released in ((paper*40,1),(black*40,1),(workspace*8,2)):
        with pytest.raises(recorder.RecordingError):recorder.workspace_start(raw,released)


def test_cover_edge_calibrates_every_phase_against_the_video_clock():
    # Page release at 0.95 s; first native video frame at 1.00 s. Selection starts
    # at 1.10 s. The 50 ms encoder offset must be applied to all later phases.
    session=dict(startup_cover={'released_at_s':.95},beat6_actions_end_s=55,
        timings=[dict(phase='live_workspace_reveal',at_s=.951),dict(phase='evidence_reveal',at_s=30)],
        geometry_checks=[dict(at_s=.9)],language_checks=[dict(at_s=.9)],
        named_element_checks=[dict(phase='evidence_reveal',at_s=30,visible_until_s=38)])
    selected=recorder.workspace_clock(session,1.1)
    assert selected['timings'][0]['at_s']==0
    assert selected['timings'][1]['at_s']==pytest.approx(28.95)
    assert selected['named_element_checks'][0]['visible_until_s']==pytest.approx(36.95)
    assert selected['startup_cover']['video_clock_offset_s']==pytest.approx(.05)
    assert selected['startup_cover']['released_at_s']==pytest.approx(-.1)
    assert session['timings'][1]['at_s']==30  # Raw audit is retained verbatim.
