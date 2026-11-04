"""Director timing, evidence-derived numbers and real-shell replay contracts."""
import hashlib
import json
from pathlib import Path
import re
import statistics
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest
import yaml
from PIL import Image

import motion_build
import motion_v4
from pipeline import BuildError
from replay_v4 import COLS, ROWS, FOOTERS, FOOTER_ROW, KEY_ROW, money, pages
import phone_v4
from scale_v4 import compile_scale

ROOT=Path(__file__).resolve().parents[2]
STORY=yaml.safe_load((ROOT/'demo/storyboard-v4.yaml').read_text())


def test_director_nine_beats_and_two_exact_placeholders():
    motion_v4.validate(STORY)
    assert [s['target_s'] for s in STORY['scenes']]==[9,13,12,16,16,58,24,16,14]
    assert sum(s['target_s'] for s in STORY['scenes'])==178.0
    assert [(s['id'],s['target_s']) for s in STORY['scenes'] if s.get('placeholder') or s.get('recording')]==[('v406',58),('v409',14)]
    assert (ROOT/'demo/NARRATION-v4.txt').read_text().strip().split('\n\n')==[s['narration'] for s in STORY['scenes']]
    for s in STORY['scenes']:
        assert ' '.join(' '.join(s['subtitle_cues']).split())==' '.join(s['narration'].split())
        for cue in s['subtitle_cues']:
            assert 1<=len(cue.splitlines())<=3
            assert all(len(line)<=42 for line in cue.splitlines())
        assert all((ROOT/p).is_file() for p in s['evidence'])
    v3=yaml.safe_load((ROOT/'demo/storyboard-v3.yaml').read_text())
    assert STORY['voice']==v3['voice']
    assert STORY['music']==v3['music']
    assert STORY['scenes'][0]['narration'].startswith('DappGo existed before this hackathon.')


def test_scale_is_rebuildable_with_all_sources_retained_and_no_parallel_projection():
    saved=json.loads((ROOT/'demo/data/scale-v4.json').read_text())
    assert compile_scale(ROOT)==saved
    for source in saved['sources']:
        path=ROOT/source['path']
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
    g=saved['cohorts'][saved['selected_cohort']]
    rows=[json.loads((ROOT/p).read_text()) for p in g['sources']]
    assert len(rows)==78
    assert statistics.median(r['wall_seconds'] for r in rows)==pytest.approx(6.764814)
    assert g['recorded_batch']['wall_seconds']==pytest.approx(874.614749)
    assert saved['projection']['sequential_hours_at_median']==pytest.approx(6.764814*1000/3600)
    assert saved['projection']['measured'] is False
    assert saved['projection']['parallel_1000_posts'] is None
    assert motion_v4.scale_narration(saved) in STORY['scenes'][6]['narration']
    assert STORY['scenes'][6]['narration'].endswith('At that median, a thousand posts take about two hours on one worker.')
    assert STORY['scenes'][5]['narration']==('Live, on the site. Paste the post and run it. '
        'Muse Spark calls the SEC tools — every call is on the record. Contradicted, with the filing. '
        'Here is the corrected draft; cost and time are on the receipt.')
    assert saved['cohorts']['news/baseten/post']['items']==80
    assert saved['recorded_parallel_batches']['threads']['workers']==3
    assert saved['eval_v2']['median_completed_latency_seconds']==pytest.approx(10.012793354457244)


def test_comparison_recomputes_original_scores_and_media_replay_retains_limits():
    sources={};comparison=pages('beat4',sources)
    text='\n'.join(line for b in comparison for line in b.lines)
    for token in ('74/357','20.7%','323/357','90.5%','240/266','90.2%','corrected gold','includes dev'):
        assert token in text
    assert comparison[-1].lines[-1]=='240/266 held-out · 90.2%'
    assert len(sources)==715
    sources={};batch=pages('beat7',sources)
    text='\n'.join(line for b in batch for line in [b.title,*b.lines])
    for token in ('lookup_fact','Program verdicts','muse-spark-1.3','muse-voice-transcribe-1.0',
                  'frozen synthetic','3 of 5','$2.29B → $229M'):
        assert token in text
    assert [b.group for b in batch]==['post','claims','tools','verdicts','scale','batch','image','audio']
    assert len(batch[1].lines)==3 and len(batch[2].lines)==5
    assert len(batch[5].lines)==6
    assert sum('FAILED' in line for line in batch[5].lines)==1
    assert batch[4].lines[-2:] == ['median 6.8 s/post','1,000 posts ≈ 2 h · 1 worker']
    # The actual final keystroke is 0.78 s into the block; both numbers precede
    # the retained voice's scale sentence at 8.6 s by more than one second.
    assert sum(b.seconds for b in batch[:4])+.78 <= 8.6-1
    assert sum(b.seconds for b in batch[:5])>=16.8
    assert '2290000000.0' not in text
    for kind,blocks,seconds in [('beat4',comparison,16),('beat7',batch,24)]:
        assert sum(b.seconds for b in blocks)==seconds
        assert all(len(b.lines)+2<=8 and all(len(line)<=COLS-4 for line in b.lines) for b in blocks)


def terminal_screen(stream):
    """Interpret emitted ANSI positions/styles and check every intermediate screen."""
    grid={};writes=[];row=col=1;style=();index=0
    while index<len(stream):
        if stream[index]=='\x1b':
            match=re.match(r'\x1b\[([0-9;?]*)([A-Za-z])',stream[index:])
            assert match,repr(stream[index:index+30])
            args,command=match.groups();index+=len(match[0])
            if command=='H':
                row,col=map(int,(args or '1;1').split(';'))
            elif command=='m':
                style=tuple(map(int,args.split(';')))
            continue
        char=stream[index];index+=1
        assert 1<=row<=ROWS and 1<=col<=COLS
        grid[row,col]=(char,style);writes.append((row,char,style));col+=1
        visible={r for (r,c),(char,_) in grid.items() if char.strip()}
        assert len(visible)<=8
    return grid,writes


def test_recorded_terminal_artifacts_and_immutable_source_snapshot():
    folder=ROOT/'demo/assets/terminal-v4-r5'
    for kind,duration in [('beat4',16),('beat7',24)]:
        receipt=json.loads((folder/f'{kind}.json').read_text())
        assert receipt['exit_code']==0
        assert receipt['status']=='rendered-real-terminal-recording'
        assert receipt['resolution']==[1920,1080] and receipt['label_font_px']>=56
        assert receipt['principal_font_px']>=96
        assert receipt['font']=='Menlo'
        assert receipt['footers']==FOOTERS and receipt['footer_row']==FOOTER_ROW
        assert receipt['footer_bottom_limit_px']<=receipt['caption_zone_top_px']==880
        assert receipt['max_visible_lines']==8 and receipt['key_typed_last'] is True
        assert receipt['duration_s']==duration
        assert receipt['replay_script_sha256']==hashlib.sha256((ROOT/'demo/replay_v4.py').read_bytes()).hexdigest()
        for ext,key in [('cast','cast_sha256'),('mp4','mp4_sha256')]:
            assert hashlib.sha256((folder/f'{kind}.{ext}').read_bytes()).hexdigest()==receipt[key]
        events=list(map(json.loads,(folder/f'{kind}.cast').read_text().splitlines()))
        assert events[0]['version']==2 and events[0]['width']==COLS and events[0]['height']==ROWS
        assert events[1][0]==0
        assert events[-1][0]==pytest.approx(duration,abs=.15)
        assert all(b[0]>=a[0] for a,b in zip(events[1:],events[2:]))
        streams=''.join(e[2] for e in events[1:]).split('\x1b[2J')
        assert streams[0]==''
        blocks=pages(kind,{})
        assert len(streams[1:])==len(blocks)
        for stream,block in zip(streams[1:],blocks):
            grid,writes=terminal_screen(stream)
            actual=[''.join(grid.get((r,c),(' ',()))[0] for c in range(1,COLS+1)).strip() for r in range(1,ROWS+1)]
            assert [line for line in actual if line]==[block.title,*block.lines,block.footer]
            assert actual[-1]==block.footer and actual.count(block.footer)==1
            assert all(grid[FOOTER_ROW,c][1]==(1,37) for c in range(3,3+len(block.footer)))
            key=block.lines[-1]
            assert writes[-len(key):]==[(KEY_ROW,c,(1,33)) for c in key]
        assert 'OCR/ASR is not retested' in '\n'.join(receipt['limits'])
        previous=ROOT/'demo/assets/terminal-v4'
        old=json.loads((previous/f'{kind}.json').read_text())
        assert hashlib.sha256((previous/f'{kind}.mp4').read_bytes()).hexdigest()==old['mp4_sha256']
        for source,digest in receipt['sources'].items():
            raw=(ROOT/source).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=digest:
                snapshots=json.loads((previous/'source-snapshots.json').read_text())
                record=snapshots[source]
                assert record['sha256_at_recording']==digest
                assert hashlib.sha256((ROOT/record['snapshot']).read_bytes()).hexdigest()==digest


def test_phone_still_retains_entire_post_and_large_type_without_a_counter():
    path=ROOT/phone_v4.ASSET
    assert path.read_text()==phone_v4.svg()
    svg=ET.parse(path).getroot();ns='{http://www.w3.org/2000/svg}'
    assert (svg.get('width'),svg.get('height'))==('1080','1920')
    assert any(e.get('id')=='phone-outline' for e in svg.iter())
    texts=svg.findall(f'.//{ns}text')
    assert all(float(t.get('font-size'))>=56 for t in texts)
    assert texts[0].text=='saved post · 28 Oct 2026'
    post=json.loads((ROOT/phone_v4.SOURCE).read_text())['post']
    assert ' '.join(' '.join(t.itertext()) for t in texts[1:])==' '.join(post.split())
    metadata=json.loads(svg.find(f'{ns}metadata').text)
    assert metadata['source_sha256']==hashlib.sha256((ROOT/phone_v4.SOURCE).read_bytes()).hexdigest()
    assert metadata['post_sha256']==hashlib.sha256(post.encode()).hexdigest()
    assert 'reposts' not in {e.get('id') for e in svg.iter()}
    assert '2290000000.0' not in path.read_text()
    assert money(2290000000.0)=='$2.29B' and money(229000000.0)=='$229M'
    assert money(416200000000)=='$416.2B'
    with Image.open(path.with_suffix('.png')) as image:
        assert image.size==(1080,1920)


def test_motion_compiler_keeps_v3_host_outputs_and_rejects_voice_overrun():
    protected=list((ROOT/'demo/motion/v3').glob('*'))
    before={str(p):p.read_bytes() for p in protected if p.is_file()}
    data=motion_v4.compile_data()
    assert before=={str(p):p.read_bytes() for p in protected if p.is_file()}
    assert data['timing']['duration']==178
    assert 'unmeasured' in data['timing']['source']
    assert data['metrics']['heldout_correct']==240
    assert data['metrics']['false_support']==1
    assert data['metrics']['negative_n']==139
    assert data['phone_post']['path']==phone_v4.ASSET
    assert data['phone_post']['sha256']==hashlib.sha256((ROOT/phone_v4.ASSET).read_bytes()).hexdigest()
    for frame in data['keyframes']:
        scene=next(s for s in STORY['scenes'] if s['id']==frame['shot'])
        assert scene['target_start_s']<=frame['t']<scene['target_end_s']
    assert all(len(c['text'].splitlines())<=2 and max(map(len,c['text'].splitlines()))<=42 for c in data['subtitles'])
    assert not any(c['text'] in ('November 4.','run.') for c in data['subtitles'])
    assert all(a['end']<=b['start'] for a,b in zip(data['subtitles'],data['subtitles'][1:]))
    # Host preparation replaces target cue timing with measured voice timing.
    # Both forms must keep the evidence current and all saved outputs consistent.
    saved=json.loads((ROOT/'demo/motion/v4/data.js').read_text().removeprefix('window.MOTION_DATA = ').removesuffix(';\n'))
    for key in ('scenes','provenance','hero','metrics','phone_post'):
        assert saved[key]==data[key]
    assert [s['end'] for s in saved['timing']['shots']]==motion_v4.BOUNDARIES[1:]
    for relative,content in motion_v4.artifacts(saved).items():
        actual=(ROOT/relative).read_text()
        if relative.endswith('.json'):
            assert json.loads(actual)==json.loads(content)
        else:
            assert actual==content
    builder=SimpleNamespace(demo=ROOT/'demo',story=STORY)
    assert motion_build.motion_folder(builder)==ROOT/'demo/motion/v4'
    assert motion_build.renderer_args(builder)==['--entry','v4/index.html']
    with pytest.raises(BuildError,match='never sped up or cut'):
        motion_v4.compile_data(voices=[{'voice_s':9}]*9)


def test_r3_measured_cues_fit_the_director_reallocation_without_changing_later_cuts(tmp_path, monkeypatch):
    audit=json.loads((ROOT/'demo/prep/v4/voice-timing-r3.json').read_text())
    assert audit['status']=='measured-all-fit' and audit['other_overruns']==[]
    assert [r['voice_s'] for r in audit['records']]==[8.24,10.64,7.44,12.24,13.84,20.64,16.8,12.8,4.88]
    assert audit['director_change']['total_s']==178
    audio=tmp_path/'offline-audio-hash-fixture.wav';audio.write_bytes(b'not decoded: detector stubbed')
    monkeypatch.setattr(motion_v4,'detect_silences',lambda *_args:[])
    voices=[]
    for scene,row in zip(STORY['scenes'],audit['records']):
        assert row['scene_id']==scene['id'] and row['narration_matches']
        assert row['voice_s']+STORY['pad_s']<=scene['target_s']
        voices.append(dict(voice_s=row['voice_s'],key='offline-fixture',artifacts={'audio':{'path':str(audio)}}))
    # Historical v406 remains retained but is no longer valid for the new copy.
    # A short synthetic span fixture verifies the fixed-cut compiler offline.
    voices[5]['voice_s']=4
    timing=motion_v4.compile_data(voices=voices)['timing']
    assert timing['shots'][0]['voice_end']==8.24 and timing['shots'][0]['end']==9
    assert timing['shots'][1]['start']==9 and timing['shots'][1]['end']==22
    assert [shot['end'] for shot in timing['shots'][1:]]==[22,34,50,66,124,148,164,178]


def test_live_audio_spans_keep_every_sample_and_reject_overlapping_receipt_cues():
    scene=STORY['scenes'][5]
    mapped=motion_v4.map_sentences(scene['narration'],4,[])
    (_,method),segments=motion_v4.place_live_voice(scene,mapped,4,measured=True)
    assert segments[0]['source_start_s']==0 and segments[-1]['source_end_s']==4
    assert all(a['source_end_s']==b['source_start_s'] for a,b in zip(segments,segments[1:]))
    assert [s['at_s'] for s in segments]==[66+e['at_scene_s'] for e in scene['cue_events']]
    assert 'receipt' in method
    with pytest.raises(BuildError,match='cue budget'):
        motion_v4.place_live_voice(scene,motion_v4.map_sentences(scene['narration'],20,[]),20,measured=True)


def test_segmented_mix_places_intact_synthetic_speech_spans_at_four_onsets(tmp_path):
    import array
    import math
    import wave
    import media
    import motion_media
    if not media.FFMPEG.exists():pytest.skip('Homebrew FFmpeg required')
    def wav(path,seconds,amplitude):
        with wave.open(str(path),'wb') as out:
            out.setparams((1,2,48000,0,'NONE','not compressed'))
            out.writeframes(array.array('h',(int(amplitude*math.sin(2*math.pi*440*i/48000))
                                            for i in range(round(seconds*48000)))).tobytes())
    source,bed=tmp_path/'speech.wav',tmp_path/'silent-bed.wav'
    wav(source,.8,12000);wav(bed,4,0)
    segments=[dict(source_start_s=i*.2,source_end_s=(i+1)*.2,at_s=i+.1) for i in range(4)]
    shot=dict(start=0,end=4,voice_start=0,voice_end=3.3,voice_segments=segments)
    mixed=tmp_path/'mix.wav'
    motion_media.mix_audio([source],[shot],bed,-22,mixed,offset=0,timeline_duration=4)
    # Decode the actual mix, then compare RMS in each speech hold and preceding gap.
    decoded=tmp_path/'decoded.wav'
    media.ffmpeg(['-i',mixed,'-c:a','pcm_s16le','-ac','1',decoded])
    with wave.open(str(decoded)) as inp:samples=array.array('h',inp.readframes(inp.getnframes()))
    def rms(a,b):
        values=samples[round(a*48000):round(b*48000)]
        return math.sqrt(sum(v*v for v in values)/len(values))
    for i in range(4):
        # FFmpeg's mono→stereo conversion applies sqrt(1/2) to each channel.
        assert 5900<rms(i+.13,i+.27)<6100
        assert rms(i+.01,i+.08)<2


def test_opening_iframe_uses_only_the_current_worktree_hero_without_navigation_or_scripts():
    hero=motion_v4.site_hero(ROOT)
    body=hero['html'].split('</head>',1)[1]
    assert 'Paste a finance post.' in body
    assert 'Every number is checked against SEC filings' in body
    assert body.count('<section ')==1
    assert '<nav' not in body and '<header' not in body and '<script' not in hero['html']
    assert 'What it can check' not in body and 'robot' not in body.lower()
    assert 'overflow:hidden' in hero['html']
    for path,digest in hero['sources'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    source='<section class="hero" id="top"><section>nested</section></section><nav>excluded</nav>'
    assert motion_v4.HeroSection(source).markup==source.split('<nav>')[0]


def test_architecture_svg_size_legibility_and_wan_quality_lock():
    svg=ET.parse(ROOT/'demo/assets/architecture-v4.svg').getroot()
    assert (svg.get('width'),svg.get('height'))==('1920','1080')
    assert all(float(e.get('font-size'))>=56 for e in svg.iter('{http://www.w3.org/2000/svg}text'))
    assert {f'node-{i}' for i in range(5)} <= {e.get('id') for e in svg.iter()}
    wan=json.loads((ROOT/'demo/prompts/broll/prompts-r4.json').read_text())
    approved=json.loads((ROOT/wan['reference_manifest']).read_text())
    ref=next(c for c in approved['clips'] if c['id']==wan['parameter_reference_clip'])
    assert [s['beat'] for s in wan['shots']]==[2,7]
    for shot in wan['shots']:
        for key,value in shot['params'].items():
            if key!='seed':assert value==ref['params'][key]
        assert shot['params']['size']==[480,480]
        assert hashlib.sha256((ROOT/shot['image']).read_bytes()).hexdigest()==shot['image_sha256']
        assert all((ROOT/a['receipt']).is_file() for a in shot['attempts'])
