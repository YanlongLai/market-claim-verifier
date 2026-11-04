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
def story():return yaml.safe_load((ROOT/'demo/storyboard-v5.yaml').read_text())
@pytest.fixture(scope='module')
def data():return compile_data()

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
    assert tuple(e['receipt_phase'] for e in scene['cue_events'])==LIVE_PHASES
    receipt={'timings':[{'phase':phase,'at_s':t} for phase,t in zip(LIVE_PHASES,[1,5,23,26,30,37,51])]}
    events=recorder.live_cue_events(scene,receipt)
    assert [e['at_scene_s'] for e in events]==[1,5,23,26,30,37,51]
    assert all(e.get('offset_s',0)==0 for e in events)
    receipt['timings'].pop()
    with pytest.raises((KeyError,recorder.RecordingError)):recorder.live_cue_events(scene,receipt)

def test_overlay_and_narration_have_identical_onsets(data):
    for scene in data['scenes']:
        for event in data['cues']['_events'][scene['id']]:
            assert event['t']==event['cue_start']
            assert event['cue_start']>=scene['target_start_s']
    assert len(data['cues']['_events']['v505'])==7

def test_every_boundary_and_phase_has_keyframe(data):
    frames=data['keyframes']
    assert {f['t'] for f in frames}>={float(t) for t in BOUNDARIES[:-1]}
    for e in data['cues']['_events']['v505']:assert any(f['shot']=='v505' and f['t']==e['t']+.15 for f in frames)
    assert sum(f['cue']=='chapter sample' for f in frames)==5

def test_sentence_ledger_covers_every_phrase_with_start_and_end_evidence(data):
    from sync_v5 import ledger_rows
    index=[dict(shot=f['shot'],t=f['t'],captioned_file=f"captioned/{i:04}.png") for i,f in enumerate(data['keyframes'])]
    rows=ledger_rows(data['timing'],data['cues'],index)
    expected=sum(len(data['cues'][s['id']]) for s in data['scenes'])
    assert len(rows)==expected
    assert all(r['status']=='pending' and r['verified_frame'] is None for r in rows)
    assert {r['cue_unit'] for r in rows if r['scene']=='v505'}=={'paste','tools','verdict','draft','evidence','trace','receipt'}
    assert all(r['cue_start_s']<r['cue_end_s'] and r['required_visual'] for r in rows)
    with pytest.raises(BuildError):ledger_rows(data['timing'],data['cues'],[])

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
    for e in story['scenes'][6]['cue_events']:
        assert blocks[e['event']]==e['at_scene_s']
    assert [b['block'] for b in receipt['blocks']]==['run','ocr','asr','median','projection']
    comparison=data['terminal_replays']['beat3'];assert comparison['duration_s']==14
    starts={b['block']:b['at_s'] for b in comparison['blocks']}
    for e in story['scenes'][3]['cue_events']:
        assert starts[e['terminal_block']]==e['at_scene_s']

def test_legacy_take_preserved_but_cannot_enter_final_film(story,data):
    if data['portable_inputs']['recordings']['v505']['receipt']['capture_version']<recorder.CAPTURE_VERSION:
        with pytest.raises(recorder.RecordingError,match='startup cover|does not exist'):recorder.check_recordings(story)
    assert recorder.BEATS=={'v505':('beat6',58.),'v508':('beat9',16.)}
    assert {s['id'] for s in story['scenes'] if s.get('recording')}=={'v505','v508'}

def proof():
    events=[{'kind':'tool_call'} for _ in range(4)]+[{'kind':'verdict'}]
    phases=[*LIVE_PHASES,*[f'tool_call_{i+1}_reveal' for i in range(4)],'program_verdict_reveal']
    timings=[{'phase':phase,'at_s':i+1} for i,phase in enumerate(phases)]
    rect=dict(name='native referent',left=180,right=800,top=180,bottom=400)
    return dict(capture_version=recorder.CAPTURE_VERSION,zoom=1.95,live_checks=1,result={'events':events},timings=timings,
        startup_cover=dict(injected_before_content=True,colour='#f7f5ef',cover_present=True,cover_opaque=True,layout_installed=True,zoom=1.95,release_geometry_index=0,released_at_s=.6),
        named_element_checks=[dict(t,elements=[dict(rect)]) for t in timings],
        ending_frame={'both_links':2,'visible_together':True,'named_elements':[dict(rect),dict(rect)]},
        geometry_checks=[{'at_s':.5,'zoom':1.95,'source_width':1560,'left_margin':180,'right_margin':180,'horizontal_overflow':0}],
        language_checks=[{'text_nodes':0,'attributes':0,'language_switches':0}],choreography={'trace_details_open':True,'apple_inspect_open':True,'program_verdict_shown':True,'after_click_s':50,'beat6_actions_end_s':55,'trace_steps_shown':[{'index':i,'kind':e['kind'],'visible':True,'hold_ms':700} for i,e in enumerate(events)],'apple_derivation':{'annual':416161000000,'nine_months':313695000000,'quarter':102466000000,'hold_ms':2000}})

def test_recorder_validates_actual_raw_apple_values():recorder.check_choreography(proof())
@pytest.mark.parametrize('mutation',[
 lambda p:p['geometry_checks'][0].update(source_width=1499),
 lambda p:p['geometry_checks'][0].update(left_margin=185),
 lambda p:p['geometry_checks'][0].update(right_margin=59),
 lambda p:p['language_checks'][0].update(text_nodes=1),
 lambda p:p['language_checks'][0].update(language_switches=1),
 lambda p:p['choreography'].update(trace_details_open=False),
 lambda p:p['choreography'].update(apple_inspect_open=False),
 lambda p:p['choreography']['trace_steps_shown'].pop(1),
 lambda p:p.update(live_checks=2),
 lambda p:p['ending_frame'].update(both_links=1),
 lambda p:p.update(capture_version=6),
 lambda p:p.pop('startup_cover'),
 lambda p:p['startup_cover'].update(injected_before_content=False),
 lambda p:p['startup_cover'].update(released_at_s=.4),
 lambda p:p['startup_cover'].update(release_geometry_index=1),
 lambda p:p['geometry_checks'][0].update(zoom=1),
 lambda p:p['named_element_checks'].pop(),
 lambda p:p['named_element_checks'][0].update(at_s=0),
 lambda p:p['named_element_checks'][0]['elements'][0].update(bottom=559),
])
def test_capture_failures_are_rejected(mutation):
    receipt=proof();mutation(receipt)
    with pytest.raises(recorder.RecordingError):recorder.check_choreography(receipt)

def test_no_early_or_overrunning_voice(data):
    scene=copy.deepcopy(data['scenes'][5]);spans=[]
    for event in scene['cue_events']:spans.append({'event':event['event'],'source_start_s':0,'source_end_s':1})
    placed=list(cue_spans(scene,{'cue_spans':spans}));assert placed[0][1]==scene['cue_events'][0]['at_scene_s']
    spans[0]['source_end_s']=scene['target_s']
    with pytest.raises(BuildError,match='no speech is cut or accelerated'):list(cue_spans(scene,{'cue_spans':spans}))

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

def test_generated_files_current(data):
    for name,content in artifacts(data).items():assert (ROOT/name).read_text()==content,name

def test_rendered_on_screen_is_the_storyboard_copy(story,data):
    import xml.etree.ElementTree as ET
    from motion_v5 import architecture
    heading=ET.fromstring(data['architecture_svg']).find('.//*[@data-on-screen="v504"]')
    assert heading.text==story['scenes'][4]['on_screen']
    changed='Model & program: <a different storyboard headline>.'
    assert ET.fromstring(architecture(ROOT,changed)).find('.//*[@data-on-screen="v504"]').text==changed
    assert 'disclosure' not in data['brand']  # One source: v500.on_screen, exercised in the JS renderer test.

def test_portable_measured_metadata_rebuilds_without_private_media(data,monkeypatch):
    original=Path.is_file
    monkeypatch.setattr(Path,'is_file',lambda p:False if 'cache/live-takes/' in p.as_posix() else original(p))
    assert compile_data()==data
    assert data['asset_status']['voice']=='measured'

def test_batch_run_uses_exact_saved_three_verdict_rows(data):
    run=data['terminal_replays']['beat6']['blocks'][0]
    assert run['block']=='run' and run['at_s']==0 and run['end_s']==5
    assert 4.01<run['source_start_s']<run['source_end_s']<6
    for frame in run['frames']:
        text='\n'.join(r['text'] for r in frame['rows'])
        assert 'FY2024 · SUPPORTED · $1.915B → $1.915B' in text
        assert 'FY2025 · CONTRADICTED · $51.31B → $5.131B' in text
        assert 'FY2023 · CONTRADICTED' in text
        assert not any(word in text for word in ('FAILED','INSUFFICIENT','UNCHECKED'))
        assert all(r['row']!=12 for r in frame['rows'])
    assert '$2.29B → $229M' in '\n'.join(r['text'] for r in run['frames'][-1]['rows'])

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
    assert len(chosen)==20 and {f['shot'] for f in chosen}=={f'v50{i}' for i in range(10)}
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
