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
from replay_v4 import COLS, ROWS, FOOTER, money, pages
import phone_v4
from scale_v4 import compile_scale

ROOT=Path(__file__).resolve().parents[2]
STORY=yaml.safe_load((ROOT/'demo/storyboard-v4.yaml').read_text())


def test_director_nine_beats_and_two_exact_placeholders():
    motion_v4.validate(STORY)
    assert [s['target_s'] for s in STORY['scenes']]==[6,20,14,16,16,50,24,16,16]
    assert sum(s['target_s'] for s in STORY['scenes'])==178.0
    assert [(s['id'],s['target_s']) for s in STORY['scenes'] if s.get('placeholder')]==[('v406',50),('v409',16)]
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
    assert 'About a cent. Under ten seconds.' in STORY['scenes'][5]['narration']
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
    assert [b.group for b in batch]==['post','claims','tools','verdicts','batch','image','audio','scale']
    assert len(batch[1].lines)==3 and len(batch[2].lines)==2
    assert len(batch[4].lines)==6
    assert sum('FAILED' in line for line in batch[4].lines)==1
    assert len(batch[5].lines)==len(batch[6].lines)==2
    assert batch[-1].lines[-1]=='median 6.8 s/post · 1,000 posts ≈ 2 h, one worker'
    assert '2290000000.0' not in text
    for kind,blocks,seconds in [('beat4',comparison,16),('beat7',batch,24)]:
        assert sum(b.seconds for b in blocks)==seconds
        assert all(len(b.lines)+2<=8 and all(len(line)<=COLS-4 for line in b.lines) for b in blocks)
        assert all(len(b.lines)<=3 for b in blocks if b.group!='batch')


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
    folder=ROOT/'demo/assets/terminal-v4'
    snapshots=json.loads((folder/'source-snapshots.json').read_text())
    for kind,duration in [('beat4',16),('beat7',24)]:
        receipt=json.loads((folder/f'{kind}.json').read_text())
        assert receipt['exit_code']==0
        assert receipt['status']=='rendered-real-terminal-recording'
        assert receipt['resolution']==[1920,1080] and receipt['font_px']>=40
        assert receipt['font']=='Menlo'
        assert receipt['footer']==FOOTER and receipt['footer_row']==ROWS
        assert receipt['max_visible_lines']==8 and receipt['key_typed_last'] is True
        assert receipt['duration_s']==duration
        assert receipt['replay_script_sha256']==hashlib.sha256((ROOT/'demo/replay_v4.py').read_bytes()).hexdigest()
        for ext,key in [('cast','cast_sha256'),('gif','gif_sha256'),('mp4','mp4_sha256')]:
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
            assert [line for line in actual if line]==[block.title,*block.lines,FOOTER]
            assert actual[-1]==FOOTER and actual.count(FOOTER)==1
            assert all(grid[ROWS,c][1]==(2,90) for c in range(3,3+len(FOOTER)))
            key=block.lines[-1];key_row=5+2*(len(block.lines)-1)
            assert writes[-len(key):]==[(key_row,c,(1,33)) for c in key]
        assert 'OCR/ASR is not retested' in '\n'.join(receipt['limits'])
        previous=ROOT/receipt['previous_take']
        old=json.loads((previous/f'{kind}.json').read_text())
        assert hashlib.sha256((previous/f'{kind}.mp4').read_bytes()).hexdigest()==old['mp4_sha256']
        for source,digest in receipt['sources'].items():
            raw=(ROOT/source).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=digest:
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
    assert all(len(c['text'].splitlines())<=3 and max(map(len,c['text'].splitlines()))<=42 for c in data['subtitles'])
    for relative,content in motion_v4.artifacts(data).items():
        assert (ROOT/relative).read_text()==content
    builder=SimpleNamespace(demo=ROOT/'demo',story=STORY)
    assert motion_build.motion_folder(builder)==ROOT/'demo/motion/v4'
    assert motion_build.renderer_args(builder)==['--entry','v4/index.html']
    with pytest.raises(BuildError,match='never sped up or cut'):
        motion_v4.compile_data(voices=[{'voice_s':7}]*9)


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
