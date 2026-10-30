"""v007 data, timing and host handoff contracts; no browser, TTS or video render."""
from copy import deepcopy
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest
import yaml

import motion_build
import motion_v3 as v3
import media
from motion_cues import review_frame_plan, sentence_subtitles
from pipeline import BuildError, file_hash
from motion_timing import motiontest_window
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


def test_script_shotlist_and_storyboard_are_the_same_proposal():
    rows=[line for line in (ROOT/'demo/SHOTLIST-v3.md').read_text().splitlines() if re.match(r'\| \d+ \|',line)]
    assert len(rows)==len(STORY['scenes'])==12
    for row,scene in zip(rows,STORY['scenes']):
        cells=row.strip('|').split('|')
        assert cells[3].strip()==scene['narration']
        assert cells[2].strip()==scene['director_notes']
        for source in scene['evidence']:
            assert (ROOT/source).is_file()
    assert (ROOT/'demo/NARRATION-v007.txt').read_text().strip().split('\n\n')==[s['narration'] for s in STORY['scenes']]
    disclosure=(ROOT/'demo/JUDGE_INTRO.md').read_text().split('> ',1)[1].split('\n',1)[0]
    assert STORY['scenes'][0]['narration']==disclosure


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
    for kind in ('screenshot','audio'):
        row=data['product']['inputs'][kind]
        assert row['source'].startswith(v3.MM+'/')
        assert row['verdict']==row['check']['program_verdict']=='contradicted'
        assert (row['check']['stated_value_used'],row['check']['actual_value'])==(1.67,1.57)
        assert 'fiscal Q3 2025' in row['check']['text']
        report=json.loads((ROOT/row['source']).read_text())
        assert any(row['check'] in c['program_checks'] and row['quote']==c['quote'] for c in report['claims'])
    audio=data['product']['inputs']['audio']
    assert audio['display_quote'] in audio['quote']
    assert any('speaker' in s for s in audio['segments'])
    assert data['product']['inputs']['text']['verdict']=='insufficient_evidence'
    assert data['product']['inputs']['text']['check']['reason']=='release_quote_issuer_metric_kind_unit_or_period_mismatch'
    assert data['product']['waveform']==v3.waveform(ROOT/'tests/fixtures/multimodal/release-reading.wav')
    assert len(data['product']['waveform'])==64


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
    voices=[dict(voice_s=s['target_s']-.6,key='locked-'+s['id']) for s in STORY['scenes']]
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
    data=v3.compile_data(ROOT,STORY,voices=[dict(voice_s=s['target_s']-.6,key=s['id']) for s in STORY['scenes']])
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
