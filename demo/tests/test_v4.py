"""Director timing, evidence-derived numbers and real-shell replay contracts."""
import hashlib
import json
from pathlib import Path
import statistics
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest
import yaml

import motion_build
import motion_v4
from pipeline import BuildError
from replay_v4 import pages
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
    assert saved['narration_sentence'] in STORY['scenes'][6]['narration']
    assert saved['cohorts']['news/baseten/post']['items']==80
    assert saved['recorded_parallel_batches']['threads']['workers']==3
    assert saved['eval_v2']['median_completed_latency_seconds']==pytest.approx(10.012793354457244)


def test_comparison_recomputes_original_scores_and_media_replay_retains_limits():
    sources={};comparison=pages('beat4',sources)
    text='\n'.join(line for _,lines in comparison for line in lines)
    for token in ('74/357','20.7%','323/357','90.5%','240/266','90.2%','RECORDED 2026-10-27','corrected gold'):
        assert token in text
    assert len(sources)==715
    sources={};batch=pages('beat7',sources)
    text='\n'.join(line for _,lines in batch for line in lines)
    for token in ('lookup_fact','PROGRAM VERDICT','muse-spark-1.3','muse-voice-transcribe-1.0',
                  'FROZEN preprocessing','OCR/ASR is not being retested','synthetic fixture'):
        assert token in text
    assert len(batch)==4
    assert all(len(lines)<=22 and all(len(line)<=96 for line in lines) for _,lines in batch)


def test_recorded_terminal_artifacts_and_immutable_source_snapshot():
    folder=ROOT/'demo/assets/terminal-v4'
    snapshots=json.loads((folder/'source-snapshots.json').read_text())
    for kind,duration in [('beat4',16),('beat7',24)]:
        receipt=json.loads((folder/f'{kind}.json').read_text())
        assert receipt['exit_code']==0
        assert receipt['status']=='rendered-real-terminal-recording'
        assert receipt['resolution']==[1920,1080] and receipt['font_px']>=28
        assert receipt['duration_s']==duration
        for ext,key in [('cast','cast_sha256'),('mp4','mp4_sha256')]:
            assert hashlib.sha256((folder/f'{kind}.{ext}').read_bytes()).hexdigest()==receipt[key]
        events=list(map(json.loads,(folder/f'{kind}.cast').read_text().splitlines()))
        assert events[0]['version']==2 and events[0]['width']==96
        assert all(b[0]>=a[0] for a,b in zip(events[1:],events[2:]))
        assert any('REPLAY' in e[2] for e in events[1:])
        for source,digest in receipt['sources'].items():
            raw=(ROOT/source).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=digest:
                record=snapshots[source]
                assert record['sha256_at_recording']==digest
                assert hashlib.sha256((ROOT/record['snapshot']).read_bytes()).hexdigest()==digest


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
