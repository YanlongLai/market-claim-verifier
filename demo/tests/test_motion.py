"""No browser / TTS model. Numerical contracts and real synthetic-audio media checks."""
import json
import math
import re
import shutil
import struct
import subprocess
import wave
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from PIL import Image

import build
import media
import motion_build
import motion_media
from build import Builder, parser
from motion_cues import map_sentences
from motion_data import decode_text, product_data
from motion_timing import (keyframe_times, motiontest_window, narration_timing, next_beat,
                           target_timing, video_beats)
from pipeline import BuildError, Subtitle, file_hash, read_json, to_srt, voice_key, write_json
from voicecheck import compare_clips, pcm

DEMO=build.DEMO
STORY=yaml.safe_load((DEMO/'storyboard.yaml').read_text())
GRID=read_json(DEMO/'assets/beats-seed92.json')
OFFSET,BEATS=video_beats(GRID)


def tone(path, frequency=230, seconds=.5, amplitude=.5):
    rate=16000
    samples=[int(32767*amplitude*(.75*math.sin(2*math.pi*frequency*i/rate)+.15*math.sin(4*math.pi*frequency*i/rate)))
             for i in range(round(seconds*rate))]
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,rate,0,'NONE','not compressed')); w.writeframes(struct.pack('<'+'h'*len(samples),*samples))


def test_storyboard_is_exactly_the_ten_approved_shots_and_locked_clone():
    lines=[line for line in (DEMO/'SHOTLIST-v2.md').read_text().splitlines() if re.match(r'\| \d+ \|',line)]
    assert len(STORY['scenes'])==len(lines)==10 and STORY['version']==2
    for scene,line in zip(STORY['scenes'],lines):
        cells=[s.strip() for s in line.strip('|').split('|')]
        assert scene['narration']==cells[4][1:-1]
        assert scene['director_notes']==cells[3]
        assert scene['on_screen']==cells[5].replace('**','')
        assert scene['visual']=={'kind':'motion'}
    voice=STORY['voice']
    assert voice['engine']=='breeze-tts-2' and voice['mode']=='clone' and voice['seed']==2026
    assert 'instruction' not in voice
    assert voice['ref_text']==(DEMO/'assets/voice/narrator-ref.txt').read_text().strip()
    assert voice['ref_audio']=='demo/assets/voice/narrator-ref.wav'
    assert yaml.safe_load((DEMO/'storyboard-v1.yaml').read_text())['version']==1
    assert STORY['music']['music_offset_s']==GRID['beats_s'][0]


def test_v2b_narration_matches_the_brief():
    scenes={s['id']:s for s in STORY['scenes']}
    assert scenes['m05-verdicts']['narration']==(
        'An agent looks up SEC data for each one. Amazon, 143.1 billion: true. '
        'NVIDIA, more than double: true. Apple, 416 billion in one quarter: false. '
        "That's the whole year. The quarter was 102.5 billion.")
    assert scenes['m02-spread']['narration']==(
        'Finance posts move fast. Some numbers are right, some are quietly wrong, and almost nobody checks.')
    assert scenes['m04-extract']['narration']==(
        'Paste a post. Muse Spark pulls out each checkable claim with its exact quote. '
        'Forecasts and opinions are labeled, not judged.')


def test_clone_cache_changes_with_reference_bytes_transcript_seed_and_narration(tmp_path):
    ref=tmp_path/'ref.wav';tone(ref)
    args=dict(engine='breeze-tts-2',instruction='',seed=2026,text='Check the number.',mode='clone',
              ref_audio_sha256=file_hash(ref),ref_text='The reference transcript.')
    key=voice_key(**args)
    for name,value in [('ref_audio_sha256','a'*64),('ref_text','Other reference.'),('seed',7),('text','Other narration.')]:
        changed=dict(args);changed[name]=value;assert voice_key(**changed)!=key
    tone(ref,frequency=440);args['ref_audio_sha256']=file_hash(ref);assert voice_key(**args)!=key
    assert key!=voice_key('breeze-tts-2','',2026,'Check the number.')
    with pytest.raises(BuildError,match='reference'):
        voice_key('breeze-tts-2','',2026,'Test',mode='clone')


def test_voice_passes_clone_flags_and_reuses_cache(tmp_path,monkeypatch):
    demo=tmp_path/'demo'; demo.mkdir(); ref=demo/'ref.wav';tone(ref)
    data=deepcopy(STORY); data['scenes']=data['scenes'][:1];data['voice']['ref_audio']='demo/ref.wav'
    (demo/'storyboard.yaml').write_text(yaml.safe_dump(data))
    b=Builder(parser().parse_args(['voice']),demo)
    monkeypatch.setattr(b,'engine',lambda:'breeze-tts-2')
    prepared=[]; monkeypatch.setattr(b,'prepare_motion',lambda:prepared.append(True))
    commands=[]
    def command(args,log=None):
        commands.append(args)
        jobs=read_json(Path(args[args.index('--jobs')+1]))
        for job in jobs:
            out=Path(job['out']);tone(out);write_json(out.with_suffix('.wav.json'),{'status':'ok','ref_audio':str(ref)})
    monkeypatch.setattr(media,'command',command)
    def normalize(src,dest):
        shutil.copy2(src,dest);return .5
    monkeypatch.setattr(media,'normalize_voice',normalize)
    b.voice();b.voice()
    assert len(commands)==1 and len(prepared)==2
    cmd=commands[0]
    assert '--instruction' not in cmd
    assert Path(cmd[cmd.index('--ref-audio')+1])==ref
    assert cmd[cmd.index('--ref-text')+1]==data['voice']['ref_text']
    assert cmd[cmd.index('--seed')+1]=='2026'
    assert b.require_voice(data['scenes'][0])['voice_s']==.5


@pytest.mark.parametrize('bad',[[1,1],[2,1],[float('nan')],[-1]])
def test_invalid_detected_beats_are_rejected(bad):
    with pytest.raises(BuildError):video_beats({'beats_s':bad})


def test_narration_cuts_use_first_eligible_beat_without_overlap_or_speech_loss():
    durations={s['id']:s['target_s']-.8 for s in STORY['scenes']}
    t=narration_timing(STORY['scenes'],durations,BEATS)
    start=0
    for shot in t['shots']:
        assert shot['start']==start
        assert shot['end']==next(b for b in BEATS if b>=shot['voice_end']+.3-1e-9)
        assert shot['end']>=shot['voice_end']+.3-1e-9
        start=shot['end']
    assert t['duration']==t['shots'][-1]['end']
    assert OFFSET==9.4041 and OFFSET!=GRID['first_beat_s']
    with pytest.raises(BuildError,match='grid'):next_beat(BEATS,1000)
    with pytest.raises(BuildError,match='positive'):narration_timing(STORY['scenes'],{**durations,'m01-open':0},BEATS)


def test_python_and_node_timing_and_motion_window_are_identical():
    durations={s['id']:s['target_s']-.8 for s in STORY['scenes']}
    timing=narration_timing(STORY['scenes'],durations,BEATS)
    script="""const fs=require('fs'),L=require(process.argv[1]),x=JSON.parse(fs.readFileSync(0,'utf8'));
    const t=L.narrationTiming(x.scenes,x.durations,x.beats);
    console.log(JSON.stringify({timing:t,window:L.testWindow(t,x.beats,'m05',2)}));"""
    result=subprocess.run(['node','-e',script,str(DEMO/'motion/logic.js')],input=json.dumps(dict(scenes=STORY['scenes'],durations=durations,beats=BEATS)),text=True,capture_output=True,check=True)
    actual=json.loads(result.stdout)
    assert actual['timing']==timing
    assert actual['window']==motiontest_window(timing,BEATS)
    assert keyframe_times(target_timing(STORY['scenes']),STORY['scenes'])==[3,65,155]
    remapped=keyframe_times(timing,STORY['scenes'])
    for t,i in zip(remapped,[0,4,9]):assert timing['shots'][i]['start']<=t<timing['shots'][i]['end']


def test_product_data_matches_reports_and_full_preregistered_eval():
    d=product_data(DEMO.parent)
    assert [(r['alone'],r['checked']) for r in d['providers']]==[(44,83),(21,90.5),(20,90.5)]
    assert d['claim_count']==357
    assert len(d['english_claims'])==4
    assert [c['ticker'] for c in d['english_claims']]==['AMZN','NVDA','AAPL','NVDA']
    assert [c['kind'] for c in d['english_claims']]==['reported_fact']*3+['opinion']
    assert [c['verdict'] for c in d['english_claims'][:3]]==['supported','supported','contradicted']
    assert d['english_claims'][3]['quote']=='NVDA at 30x sales is still cheap.'
    assert d['english_claims'][3]['status']=='not_checked' and d['english_claims'][3]['verdict'] is None
    assert d['filing']['values']==['143,083','158,877','404,824','450,167']
    assert d['filing']['years']==['2023','2024','2023','2024']
    assert d['apple']==dict(claimed_b=416.2,quarter_b=102.466,full_year_b=416.161,
                            quarter_period='FY2025Q4',quarter_start='2025-06-29',quarter_end='2025-09-27',
                            verdict='contradicted')
    assert d['chinese_claim']['verdict']=='contradicted'
    assert d['chinese_claim']['program_checks'][0]['program_verdict']=='contradicted'
    assert d['chinese_claim']['ticker']=='KO' and d['chinese_claim']['index']==3
    assert d['chinese_claim']['quote']=='可口可樂 2024 年營收突破 500 億美元。'
    assert len(d['chinese_claim']['program_checks'])==1
    assert d['chinese_claim']['program_checks'][0]['comparator']=='gt'
    assert d['chinese_claim']['evidence'][0]['value']==47_061_000_000
    assert d['claim_numbers']==dict(amazon_b=143.1,precision_b=.05,nvidia_multiplier=2,
                                   chinese_yi=500,chinese_b=50.,chinese_filed_b=47.061)
    assert d['max_gain_points']==70.5
    assert d['filing']['url'].endswith('/amzn-20240930.htm#f-212')
    assert len(d['provenance'])==7
    snapshot=read_json(DEMO/'data/demo-thread.json')
    assert snapshot['sources']['report']['path']=='docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json'
    assert snapshot['sources']['post']['path']=='examples/posts/demo-thread.txt'
    assert snapshot['provider']=='baseten'
    assert d['english_post']==snapshot['post']
    assert d['english_post'].startswith('Big Tech earnings recap 🧵')
    assert d['provenance']['demo/data/demo-thread.json']==file_hash(DEMO/'data/demo-thread.json')
    for source in snapshot['sources'].values():
        assert d['provenance'][source['path']]==source['sha256']
        assert re.fullmatch('[a-f0-9]{64}',source['sha256'])
    assert snapshot['claims'][0]['program_checks'][0]['actual_value']==143083000000
    assert snapshot['claims'][1]['program_checks'][0]['actual_value']==60922000000
    assert snapshot['claims'][1]['program_checks'][1]['actual_value']==pytest.approx(125.85452658115221)
    assert snapshot['claims'][2]['evidence'][0]['value']==102466000000
    assert snapshot['claims'][2]['evidence'][0]['derived'] is True
    assert snapshot['claims'][2]['evidence'][0]['tier']=='L3'
    assert snapshot['apple_full_year']['value']==416161000000
    assert snapshot['apple_full_year']['source_field']=='claims[2].summary'


def test_source_entities_are_decoded_once_at_data_load(monkeypatch):
    import motion_data
    original=motion_data.read_json
    def encoded(path):
        value=original(path)
        if str(path).endswith('demo-thread.json'):
            value['claims'][0]['quote']="Amazon&#39;s Q3 2023 &amp; its $143.1 billion."
            value['claims'][1]['quote']='A literal &amp;#39; stays encoded after one pass.'
        return value
    monkeypatch.setattr(motion_data,'read_json',encoded)
    data=motion_data.product_data(DEMO.parent)
    assert data['english_claims'][0]['quote']=="Amazon's Q3 2023 & its $143.1 billion."
    assert data['english_claims'][1]['quote']=='A literal &#39; stays encoded after one pass.'
    assert decode_text({'nested': ['&lt;b&gt;', 47.061, None]})=={'nested': ['<b>',47.061,None]}


def preview_builder(tmp_path, durations=None):
    demo=tmp_path/'demo';(demo/'motion').mkdir(parents=True)
    shutil.copy2(DEMO/'motion/qr.json',demo/'motion/qr.json')
    audio=demo/'fixture.wav';tone(audio)
    def voice(scene):
        if durations is None:raise BuildError('Voice not generated yet')
        return {'voice_s':durations[scene['id']],'key':'test-'+scene['id'],
                'artifacts':{'audio':{'path':str(audio)}}}
    story=deepcopy(STORY)
    # Synthetic reference for unit tests; the licensed narrator WAV stays local.
    story['voice']['ref_audio']=str(audio)
    return SimpleNamespace(story=story,storyboard=DEMO/'storyboard.yaml',repo=DEMO.parent,
                           demo=demo,scenes=STORY['scenes'],pad=.3,require_voice=voice)


def test_prepare_inlines_json_for_file_protocol_and_replaces_targets_after_voice(tmp_path,monkeypatch):
    monkeypatch.setattr(motion_build,'detect_silences',lambda *args:[])
    b=preview_builder(tmp_path)
    t=motion_build.prepare(b);assert t['source']=='targets' and t['duration']==160
    assert (b.demo/'motion/data.js').read_text().startswith('// Generated by build.py;')
    assert read_json(b.demo/'motion/beats.json')['beats_s'][0]==0
    assert read_json(b.demo/'motion/timing.json')['music_offset_s']==9.4041
    durations={s['id']:s['target_s']*.5 for s in b.scenes}
    b.require_voice=lambda s:dict(voice_s=durations[s['id']],key='test-'+s['id'],
                                 artifacts={'audio':{'path':str(b.demo/'fixture.wav')}})
    t=motion_build.prepare(b,require_voice=True)
    assert t['source']=='narration' and 160<=t['duration']<161
    assert t['presentation_holds']
    assert len(t['voice_keys'])==10


def test_prepare_rejects_fitted_offset_and_missing_required_voice(tmp_path):
    b=preview_builder(tmp_path)
    with pytest.raises(BuildError,match='Voice'):motion_build.prepare(b,require_voice=True)
    b.story['music']['music_offset_s']=GRID['first_beat_s']
    with pytest.raises(BuildError,match='FIRST detected'):motion_build.prepare(b)


def test_voicecheck_synthetic_same_speaker_proxy_and_different_timbre(tmp_path):
    a,b,c=[tmp_path/(name+'.wav') for name in 'abc']
    tone(a);tone(b,amplitude=.25);tone(c,frequency=2300)
    same=compare_clips([a,b],threshold=.99,backend='python')
    assert same['passed'] and same['min_pairwise_similarity']>.99
    different=compare_clips([a,b,c],threshold=.99,backend='python')
    assert not different['passed'] and len(different['pairs'])==3
    assert different['min_pairwise_similarity']==min(p['similarity'] for p in different['pairs'])
    with pytest.raises(BuildError,match='at least two'):compare_clips([a])
    with pytest.raises(BuildError,match='threshold'):compare_clips([a,b],threshold=2)
    tone(c,amplitude=0)
    with pytest.raises(BuildError,match='non-silent'):pcm(c)


def test_pure_node_suite_without_launching_browser():
    result=subprocess.run(['node','--test',str(DEMO/'tests/motion.test.mjs'),str(DEMO/'tests/layout.test.mjs')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_window_subtitles_clip_without_changing_spoken_text():
    cues=[Subtitle(0,1,'Before.'),Subtitle(1,3,'The exact spoken line.'),Subtitle(3,5,'After.')]
    clipped=motion_media.window_subtitles(cues,1.5,2)
    assert clipped==[Subtitle(0,1.5,'The exact spoken line.'),Subtitle(1.5,2,'After.')]
    assert '00:00:00,000 --> 00:00:01,500' in to_srt(clipped)


@pytest.mark.skipif(not media.FFMPEG.exists(),reason='Homebrew ffmpeg required')
def test_v2_synthetic_caption_burn_and_absolute_audio_window(tmp_path):
    # This is a tiny TEST fixture; never a film export or browser rendering.
    picture=tmp_path/'synthetic-picture.mp4'
    media.ffmpeg(['-f','lavfi','-i','color=c=0x111a20:s=1920x1080:r=30:d=2','-an',*media.video_encoder(),picture])
    captioned=tmp_path/'captioned.mp4'
    motion_media.burn_captions(picture,[Subtitle(.5,1.5,'Synthetic subtitle test.')],captioned,2)
    media.ffmpeg(['-ss','1','-i',captioned,'-frames:v','1','-update','1',tmp_path/'caption.png'])
    media.ffmpeg(['-ss','0.2','-i',captioned,'-frames:v','1','-update','1',tmp_path/'blank.png'])
    with Image.open(tmp_path/'caption.png') as shown,Image.open(tmp_path/'blank.png') as blank:
        # Count bright subtitle glyphs only in the reserved bottom band.
        count=lambda img:sum(1 for r,g,b in img.convert('RGB').crop((400,900,1520,1020)).get_flattened_data() if min(r,g,b)>180)
        assert count(shown)>100 and count(blank)==0
    voice=tmp_path/'voice.wav';bed=tmp_path/'bed.wav';tone(voice,seconds=4);tone(bed,frequency=110,seconds=8,amplitude=.15)
    shots=[dict(id='fixture',start=1,end=5.3,voice_s=4,voice_end=5)]
    mix=tmp_path/'mix.wav'
    motion_media.mix_audio([voice],shots,bed,-22,mix,offset=.5,timeline_duration=5.3,start=2,length=2)
    assert media.duration(mix)==pytest.approx(2,abs=.001)
    exported=tmp_path/'fixture-only.mp4'
    levels=media.master(captioned,mix,exported,2)
    assert media.validate_export(exported,2)['video_codec']=='h264'
    assert levels['measured_lufs']==pytest.approx(-14,abs=.5)


def test_keyframes_map_to_current_shots_and_only_request_three_stills(tmp_path,monkeypatch):
    b=preview_builder(tmp_path,{s['id']:s['target_s']*.5 for s in STORY['scenes']})
    b.args=parser().parse_args(['keyframes']);b.cache=b.demo/'cache';b.cache.mkdir()
    requests=[]
    monkeypatch.setattr(motion_build,'detect_silences',lambda *args:[])
    monkeypatch.setattr(media,'command',lambda args,log=None:requests.append(args))
    motion_build.keyframes(b)
    args=requests[0]
    assert args.count('--t')==3 and '--from' not in args and '--to' not in args
    expected=keyframe_times(read_json(b.demo/'motion/timing.json'),b.scenes)
    assert [float(args[i+1]) for i,a in enumerate(args) if a=='--t']==pytest.approx(expected)
    assert str(args[1]).endswith('/motion/render.mjs')
    assert not (b.demo/'out/demo-v002.mp4').exists()


def test_motiontest_renders_only_flip_window_and_mixes_matching_absolute_times(tmp_path,monkeypatch):
    b=preview_builder(tmp_path)
    timing=target_timing(b.scenes)
    for s in timing['shots']:
        s.update(voice_s=s['end']-s['start']-.5,voice_end=s['end']-.5)
    timing['music_offset_s']=OFFSET
    write_json(b.demo/'motion/beats.json',dict(beats_s=BEATS))
    write_json(b.demo/'motion/cues.json',{
        **{scene['id']:map_sentences(scene['narration'],shot['voice_s'],[],shot['start'])[0]
           for scene,shot in zip(b.scenes,timing['shots'])},
        '_events':{s['id']:[] for s in b.scenes}})
    monkeypatch.setattr(motion_build,'prepare',lambda *a,**k:timing)
    for name in ['motion_build.py','motion_media.py','motion_cues.py','motion_timing.py','media.py','pipeline.py']:
        shutil.copy2(DEMO/name,b.demo/name)
    audio=b.demo/'test.wav';tone(audio)
    b.require_voice=lambda s:dict(key=s['id'],artifacts={'audio':{'path':str(audio)}},engine='fixture')
    b.music=lambda:audio
    b.args=parser().parse_args(['motiontest','--shot','m05','--len','2'])
    b.cache=b.demo/'cache';b.cache.mkdir()
    def stage_dir(*parts):
        p=b.cache/Path(*parts);p.mkdir(parents=True,exist_ok=True);return p
    b.stage_dir=stage_dir
    def alias(src,dest):
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    b.alias=alias
    monkeypatch.setattr(media,'duration',lambda p:190)
    calls=[]
    monkeypatch.setattr(media,'command',lambda args,log=None:calls.append(args))
    monkeypatch.setattr(motion_media,'encode_frames',lambda *a,**k:None)
    monkeypatch.setattr(motion_media,'burn_captions',lambda *a,**k:None)
    mixes=[]
    monkeypatch.setattr(motion_media,'mix_audio',lambda *a,**k:mixes.append(k))
    def master(video,audio,dest,length):
        dest.write_bytes(b'fixture test only');return {'measured_lufs':-14,'true_peak_dbtp':-2}
    monkeypatch.setattr(media,'master',master)
    monkeypatch.setattr(media,'validate_export',lambda p,length:{'duration_s':length})
    report=motion_build.render(b,test=True)
    args=calls[0]
    start=float(args[args.index('--from')+1]);end=float(args[args.index('--to')+1])
    assert end-start==pytest.approx(2)
    assert start<report['window']['event']<end
    assert mixes[0]['start']==start and mixes[0]['length']==2 and mixes[0]['offset']==OFFSET
    assert (b.demo/'out/motiontest-m05-verdicts.mp4').exists()
    assert not list((b.demo/'out').glob('demo-v*.mp4'))
    assert not (b.demo/'runs').exists()


def test_v2_all_and_assemble_cannot_accidentally_run_legacy_full_pipeline(tmp_path,monkeypatch):
    # assemble rejects v2 before requiring any voice/capture; CLI `all` uses the same guard.
    data=deepcopy(STORY);demo=tmp_path/'demo';demo.mkdir()
    ref=demo/'ref.wav';tone(ref);data['voice']['ref_audio']='demo/ref.wav'
    (demo/'storyboard.yaml').write_text(yaml.safe_dump(data))
    b=Builder(parser().parse_args(['assemble']),demo)
    with pytest.raises(BuildError,match='v2 uses render'):b.assemble()
    assert not (demo/'out').exists()
