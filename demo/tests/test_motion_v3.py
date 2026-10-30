"""v007 data, timing and host handoff contracts; no browser, TTS or video render."""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
from types import SimpleNamespace

import pytest
import yaml

import motion_build
import motion_v3 as v3
import media
import motion_media
from motion_cues import review_frame_plan, sentence_subtitles
from pipeline import BuildError, file_hash, read_json, write_json
from motion_timing import motiontest_window, next_beat
from PIL import ImageFont

ROOT=v3.ROOT
STORY=yaml.safe_load((ROOT/v3.STORY).read_text())


@pytest.fixture(scope='module')
def data():
    return v3.compile_data(ROOT,STORY)


def test_v007_preview_artifacts_rebuild_exactly_without_local_media(data):
    for relative, expected in v3.artifacts(ROOT,STORY,data).items():
        assert (ROOT/relative).read_text()==expected, relative
    assert 'narration unmeasured' in data['timing']['source']
    assert all('voice_s' not in shot for shot in data['timing']['shots'])


def test_script_shotlist_and_storyboard_retain_owner_approved_edits():
    rows=[line for line in (ROOT/'demo/SHOTLIST-v3.md').read_text().splitlines() if re.match(r'\| \d+ \|',line)]
    assert len(rows)==len(STORY['scenes'])==12
    for row,scene in zip(rows,STORY['scenes']):
        cells=row.strip('|').split('|')
        assert cells[3].strip()==scene['narration']
        assert cells[2].strip()==scene['director_notes']
        clock=lambda t:f'{int(t)//60}:{int(t)%60:02d}'
        assert cells[1].strip()==clock(scene['target_start_s'])+'–'+clock(scene['target_end_s'])
        for source in scene['evidence']:
            assert (ROOT/source).is_file()
    assert (ROOT/'demo/NARRATION-v007.txt').read_text().strip().split('\n\n')==[s['narration'] for s in STORY['scenes']]
    disclosure=(ROOT/'demo/JUDGE_INTRO.md').read_text().split('> ',1)[1].split('\n',1)[0]
    assert STORY['scenes'][0]['on_screen']==disclosure==v3.evidence_data(ROOT)['disclosure']
    assert STORY['scenes'][0]['narration']=='Built entirely during the Meta hackathon. Nothing here pre-existed.'
    assert [(s['target_start_s'],s['target_end_s'],s['target_s']) for s in STORY['scenes'][:4]]==[
        (0,6,6),(6,20,14),(20,32,12),(32,60,28)]
    assert STORY['scenes'][10]['narration']==(
        'These are saved runs, not a guarantee. The text, screenshot and audio checks all catch the same error. '
        'Long-call recall and speaker identity remain limited. L4 is a regression test.')


def test_voice_and_music_keep_owner_lock_and_detected_grid(data):
    baseline=yaml.safe_load((ROOT/'demo/storyboard.yaml').read_text())
    assert STORY['voice']==baseline['voice']
    assert STORY['music']==baseline['music']
    assert STORY['voice']['mode']=='clone'
    assert STORY['voice']['ref_text']==(ROOT/'demo/assets/voice/narrator-ref.txt').read_text().strip()
    assert sum(s['target_s'] for s in STORY['scenes'])==STORY['target_total_s']==178
    assert 170<=data['timing']['duration']<=180
    beats=data['beats']['beats_s']
    assert all(s['start'] in beats and s['end'] in beats for s in data['timing']['shots'])
    assert all(a['end']==b['start'] for a,b in zip(data['timing']['shots'],data['timing']['shots'][1:]))
    assert all(t in beats for t,age in data['hover_anchors'])
    assert all(a[0]<b[0] and a[1]<b[1] for a,b in zip(data['hover_anchors'],data['hover_anchors'][1:]))


def test_l4_examples_match_raw_checks_and_retain_release_provenance(data):
    assert [r['id'] for r in data['product']['releases']]==['L4-01','L4-27']
    for row in data['product']['releases']:
        trace=json.loads((ROOT/row['source']).read_text())
        source=row['excerpt']['source_evidence']
        assert row['checks']==trace['program_checks']
        assert row['verdict']==trace['final_verdict']['verdict']=='supported'
        assert source['provenance']['tier']=='L4'
        assert source['provenance']['furnished'] and source['provenance']['unaudited']
        assert source['period']=='FY2025Q3'
    assert data['product']['releases'][0]['checks'][0]['actual_range']==[47.5e9,50.5e9]
    assert data['product']['releases'][1]['checks'][0]['actual_value']==5.31


def test_input_examples_use_new_recorded_runs_and_self_made_fixture_bytes(data):
    for kind in ('text','screenshot','audio'):
        row=data['product']['inputs'][kind]
        assert row['source'].startswith((v3.RECALL if kind=='text' else v3.MM)+'/')
        assert row['verdict']==row['check']['program_verdict']=='contradicted'
        assert (row['check']['stated_value_used'],row['check']['actual_value'])==(1.67,1.57)
        assert 'fiscal Q3 2025' in row['check']['text']
        report=json.loads((ROOT/row['source']).read_text())
        assert any(row['check'] in c['program_checks'] and row['quote']==c['quote'] for c in report['claims'])
        assert row['evidence'] and all(e['filing_url'].startswith('https://www.sec.gov/') for e in row['evidence'])
        assert (ROOT/row['ingest_source']).is_file() and (ROOT/row['trace_source']).is_file()
    audio=data['product']['inputs']['audio']
    assert audio['display_quote'] in audio['quote']
    assert any('speaker' in s for s in audio['segments'])
    assert data['product']['waveform']==v3.waveform(ROOT/'tests/fixtures/multimodal/release-reading.wav')
    assert len(data['product']['waveform'])==64


def test_recall_limits_come_from_30b_report_data_and_retain_source_links(data):
    recall=data['product']['recall']
    comparison=json.loads((ROOT/recall['source']).read_text())
    assert recall['source']==v3.RECALL+'/before-after.json'
    assert recall['policy']==comparison['policy']
    for label,run,channel,expected in [('live','long-call-r2','audio',44),
                                       ('frozen_asr','long-call-frozen','text',50)]:
        row=recall['coverage'][label]
        counts=comparison['runs'][run]['after']['channels'][channel]['recall']
        assert row['guarded']==counts['accepted']==row['program_checked']==counts['program_checked']==expected
        assert row['expected']==counts['expected']==60
        assert row['channel']==channel
        assert row['source']==f'{v3.RECALL}/{run}/ingest.json'
        assert file_hash(ROOT/row['source'])==data['product']['provenance'][row['source']]
    speaker=recall['speaker_identity']
    assert speaker['verified'] is False
    assert speaker['limitation'] in json.loads((ROOT/speaker['source']).read_text())['limitations']


def test_compiler_reads_coverage_values_instead_of_baking_in_screen_numbers(monkeypatch):
    original=v3.read_json
    def changed(path):
        data=deepcopy(original(path))
        if str(path).endswith('/before-after.json'):
            counts=data['runs']['long-call-r2']['after']['channels']['audio']['recall']
            counts['accepted']=counts['program_checked']=42
        return data
    monkeypatch.setattr(v3,'read_json',changed)
    assert v3.evidence_data(ROOT)['recall']['coverage']['live']['program_checked']==42


@pytest.mark.parametrize('corruption', ['text_verdict','text_value','coverage','speaker'])
def test_stale_text_verdict_and_inconsistent_recall_evidence_fail_closed(monkeypatch,corruption):
    original=v3.read_json
    def corrupt(path):
        data=deepcopy(original(path))
        if str(path).endswith('/multimodal-2026-10-30b/text/checks/text/report.json'):
            claim=next(c for c in data['claims'] if c['verdict']=='contradicted')
            if corruption=='text_verdict':claim['verdict']='insufficient_evidence'
            if corruption=='text_value':claim['program_checks'][0]['actual_value']=1.67
        if corruption=='coverage' and str(path).endswith('/before-after.json'):
            data['runs']['long-call-r2']['after']['channels']['audio']['recall']['accepted']=61
        if corruption=='speaker' and str(path).endswith('/long-call-r2/ingest.json'):
            data['limitations']=[]
        return data
    monkeypatch.setattr(v3,'read_json',corrupt)
    with pytest.raises(BuildError,match='EPS verdict|EPS values|coverage is inconsistent|speaker-label limitation'):
        v3.evidence_data(ROOT)


def test_scores_are_original_corrected_gold_counts_not_posthoc(data):
    assert [(s['alone']['correct'],s['checked']['correct']) for s in data['product']['scores']]==[(158,297),(74,323),(71,323)]
    assert [s['checked']['percent'] for s in data['product']['scores']]==[83.2,90.5,90.5]
    assert all(s['checked']['total']==s['alone']['total']==357 for s in data['product']['scores'])
    assert not any('r2-posthoc' in p for p in data['product']['provenance'])


def test_every_input_and_asset_hash_matches_recorded_source(data):
    assert all(file_hash(ROOT/p)==digest for p,digest in data['product']['provenance'].items())
    adapted=(ROOT/'demo/motion/v3/hover-source.js').read_text()
    assert adapted==v3.hover_source(ROOT)
    for expression in ['const transitions = canCheck ?', 'const dip = sinceStrike',
                       'const bob = 4 * Math.sin', 'const filingAlpha = enabled']:
        assert expression in adapted and expression in (ROOT/'docs/site/script.js').read_text()


def test_wrong_values_and_release_spans_fail_closed(monkeypatch):
    original=v3.read_json
    def corrupt(path):
        data=deepcopy(original(path))
        if str(path).endswith('/screenshot/checks/image/report.json'):
            data['claims'][1]['program_checks'][0]['actual_value']=1.67
        return data
    monkeypatch.setattr(v3,'read_json',corrupt)
    with pytest.raises(BuildError,match='retained EPS values changed'):
        v3.evidence_data(ROOT)
    def mismatched(path):
        data=deepcopy(original(path))
        if str(path).endswith('/site/data/site.json'):
            next(c for c in data['stamp_cards'] if c.get('claim_id')=='L4-01')['excerpt']['source_evidence']['low']=0
        return data
    monkeypatch.setattr(v3,'read_json',mismatched)
    with pytest.raises(BuildError,match='differs from its raw trace'):
        v3.evidence_data(ROOT)


def test_measured_narration_replaces_preview_without_speedup_and_refuses_overrun(data):
    voices=[dict(voice_s=s['target_s']-s.get('narration_lead_s',0)-.6,key='locked-'+s['id'])
            for s in STORY['scenes']]
    measured=v3.compile_data(ROOT,STORY,voices=voices)
    assert measured['timing']['source']=='narration'
    for shot,voice in zip(measured['timing']['shots'],voices):
        assert shot['voice_s']==voice['voice_s']
        assert shot['end']>=shot['voice_end']+.3-1e-9
        assert measured['timing']['voice_keys'][shot['id']]==voice['key']
    voices[-1]['voice_s']=100
    with pytest.raises(BuildError,match='beat grid|170–180'):
        v3.compile_data(ROOT,STORY,voices=voices)


def test_all_spoken_words_have_wrapped_subtitles_and_review_cues(data):
    data=v3.compile_data(ROOT,STORY,voices=[
        dict(voice_s=s['target_s']-s.get('narration_lead_s',0)-.6,key=s['id']) for s in STORY['scenes']])
    captions=sentence_subtitles(STORY['scenes'],data['timing'],data['cues'])
    assert ' '.join(c.text.replace('\n',' ') for c in captions)==' '.join(s['narration'] for s in STORY['scenes'])
    assert all(0<=c.start<c.end<=data['timing']['duration'] for c in captions)
    assert all(len(c.text.splitlines())<=2 and max(map(len,c.text.splitlines()))<=42 for c in captions)
    font=ImageFont.truetype(str(media.font_path()),56)
    for caption in captions:
        lines=caption.text.splitlines()
        assert max(font.getlength(line) for line in lines)<=1664
        # Actual glyphs are centered in 60 px line boxes: 2*60+16 =136 px.
        assert all(font.getbbox(line)[3]-font.getbbox(line)[1]<=60 for line in lines)
    frames=review_frame_plan(data['timing'],data['cues']['_events'])
    assert len({f['shot'] for f in frames})==12
    for row in data['cues']['_events'].values():
        for event in row:
            assert event['t'] in data['beats']['beats_s']
            assert event['t']>=event['cue_start']-.1-1e-9
    window=motiontest_window(data['timing'],data['beats']['beats_s'],'v304-hover',2,
                            cue_events=data['cues']['_events'])
    strike=next(e['t'] for e in data['cues']['_events']['v304-hover'] if e['event']=='strike')
    assert window['event']==strike
    assert window['from']<strike<window['to']


def test_keyframe_manifest_and_host_routing(data):
    frames=json.loads((ROOT/'demo/motion/v3/keyframes.json').read_text())
    assert frames==data['keyframes']
    assert len(frames)==36
    revision=(ROOT/'demo/REVISION-v007.md').read_text()
    for shot in data['timing']['shots']:
        selected=[f for f in frames if f['shot']==shot['id']]
        assert len(selected)==3 and all(shot['start']<f['t']<shot['end'] for f in selected)
        assert all(f'{f["t"]:.3f}' in revision for f in selected)
    builder=SimpleNamespace(story=STORY,demo=ROOT/'demo')
    assert motion_build.motion_folder(builder)==ROOT/'demo/motion/v3'
    assert motion_build.renderer_args(builder)==['--entry','v3/index.html']
    assert data['qr']['url']==STORY['site_url']=='https://hackathon.dappgo.com/'


def test_v3_full_render_and_motiontest_share_measured_audio_master_and_caption_timeline(tmp_path,monkeypatch):
    """Exercise orchestration with measured synthetic durations, without host artifacts/browser."""
    demo=tmp_path/'demo';motion=demo/'motion/v3';motion.mkdir(parents=True)
    for name in ('motion_build.py','motion_media.py','motion_cues.py','motion_timing.py',
                 'media.py','pipeline.py','motion_v3.py'):
        shutil.copy2(ROOT/'demo'/name,demo/name)
    storyboard=demo/'storyboard-v3.yaml';storyboard.write_text(yaml.safe_dump(STORY))
    voice=demo/'synthetic-voice.wav';voice.write_bytes(b'synthetic narration, never licensed host audio')
    music=demo/'bed-seed92.wav';music.write_bytes(b'synthetic stand-in for the locked bed')
    voices=[dict(voice_s=s['target_s']-s.get('narration_lead_s',0)-.6,key=s['id'],engine='fixture',
                 artifacts=dict(audio=dict(path=str(voice),sha256=file_hash(voice)))) for s in STORY['scenes']]
    data=v3.compile_data(ROOT,STORY,voices=voices)
    timing=data['timing']
    write_json(motion/'timing.json',timing);write_json(motion/'beats.json',data['beats'])
    write_json(motion/'cues.json',data['cues'])
    def stage_dir(*parts):
        folder=demo.joinpath('cache',*parts);folder.mkdir(parents=True,exist_ok=True);return folder
    def alias(source,destination):
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    builder=SimpleNamespace(demo=demo,repo=ROOT,story=STORY,storyboard=storyboard,scenes=STORY['scenes'],
                            args=SimpleNamespace(out=None,force=False,shot='v304-hover',len=2),
                            require_voice=lambda scene:next(v for v in voices if v['key']==scene['id']),
                            music=lambda:music,stage_dir=stage_dir,alias=alias,
                            versions=lambda:dict(ffmpeg='synthetic fixture'),rel=lambda path:str(path))
    monkeypatch.setattr(motion_build,'prepare',lambda b,**options:timing)
    monkeypatch.setattr(media,'duration',lambda p:200)
    renders=[];burns=[];mixes=[];normalizations=[];masters=[]
    monkeypatch.setattr(media,'command',lambda args,*a:renders.append(args))
    monkeypatch.setattr(motion_media,'encode_frames',lambda *a:None)
    monkeypatch.setattr(motion_media,'burn_captions',lambda *a,**k:burns.append((a,k)))
    def mix(*args,**options):
        mixes.append((args,options));args[4].write_bytes(b'full mix')
    def normalize(source,destination,seconds):
        normalizations.append(seconds);destination.write_bytes(b'full normalized PCM')
        destination.with_suffix('.m4a').write_bytes(b'full verified AAC')
        return dict(integrated_gate=True,measured_lufs=-14,true_peak_dbtp=-1.5)
    def master(video,audio,destination,seconds,**options):
        masters.append((audio,seconds,options));destination.write_bytes(b'synthetic movie fixture')
        return dict(integrated_gate=not options['preview'],measured_lufs=-16.03 if options['preview'] else -14,
                    true_peak_dbtp=-2.1,momentary_max_lufs=-15.8,short_term_max_lufs=None)
    monkeypatch.setattr(motion_media,'mix_audio',mix)
    monkeypatch.setattr(media,'prepare_audio_master',normalize)
    monkeypatch.setattr(media,'master',master)
    monkeypatch.setattr(media,'validate_export',lambda path,seconds:dict(duration_s=seconds))
    full=motion_build.render(builder)
    preview=motion_build.render(builder,test=True)
    assert len(mixes)==len(normalizations)==1  # Same cache, not two separately normalized mixes.
    assert full['audio_master_cache_key']==preview['audio_master_cache_key']
    assert masters[0][0]==masters[1][0]
    assert masters[0][2]==dict(start_s=0,preview=False,reference=masters[1][2]['reference'])
    assert masters[1][2]['start_s']==preview['window']['from'] and masters[1][2]['preview'] is True
    assert full['loudness']['integrated_gate'] is True and preview['loudness']['integrated_gate'] is False
    assert full['storyboard']['path']==str(storyboard) and full['storyboard_version']==2
    for args in renders:
        assert args[args.index('--entry')+1]=='v3/index.html'
    assert float(renders[0][renders[0].index('--from')+1])==0
    assert float(renders[0][renders[0].index('--to')+1])==timing['duration']
    mix_args,mix_options=mixes[0]
    assert mix_args[1]==timing['shots'] and mix_args[2]==music and mix_args[3]==-22
    assert mix_options==dict(offset=9.4041,timeline_duration=timing['duration'])
    hover=next(s for s in timing['shots'] if s['id']=='v304-hover')
    lead=next(s['narration_lead_s'] for s in STORY['scenes'] if s['id']==hover['id'])
    assert hover['voice_start']==next_beat(data['beats']['beats_s'],hover['start']+lead)
    assert data['cues'][hover['id']][0]['start']>=hover['voice_start']
    captions=burns[0][0][1]
    assert ' '.join(c.text.replace('\n',' ') for c in captions)==' '.join(s['narration'] for s in STORY['scenes'])
    assert all(len(c.text.splitlines())<=2 and max(map(len,c.text.splitlines()))<=42 for c in captions)
    assert all(options==dict(font_size=56) for _,options in burns)
    assert Path(full['subtitles']['path']).read_text().count(' --> ')==len(captions)
    assert read_json(demo/'out/motiontest-v304-hover.json')['loudness']['measured_lufs']==-16.03


def test_v3_two_line_caption_canvas_stays_in_bottom_zone_with_64_px_clearance(tmp_path):
    canvas=motion_media.caption_canvas('The fiscal quarter is checked.\nThe exact filing stays attached.',tmp_path/'panel.png',font_size=56)
    left,top,right,bottom=canvas.getbbox()
    assert top==880 and bottom==1080-64
    assert left>=64 and right<=1920-64
