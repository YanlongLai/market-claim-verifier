"""AI2 regressions use recorded speech intervals, without narration or rendering."""
from types import SimpleNamespace
import math

import pytest
import yaml

import media
import motion_build
import motion_v3 as v3
from motion_cues import review_frame_plan, snap_event
from pipeline import BuildError, read_json, write_json

STORY = yaml.safe_load((v3.ROOT/v3.STORY).read_text())
LENGTHS = [4.16, 7.68, 7.12, 11.04, 10, 6.64, 19.44, 9.84, 9.84, 12, 12, 8.16]
# Retained pause-aligned host intervals reviewed by AI2; no word-alignment claim.
SPEECH = {
    'v304-hover': [(41.3547, 43.074492), (43.487617, 44.485992),
                   (45.02395, 47.741658), (48.292617, 50.451742), (50.912158, 52.188033)],
    'v307-l4': [(87.0516, 89.848892), (90.386933, 95.550267),
                (96.207308, 100.416267), (101.02185, 103.640767), (104.06335, 106.218725)],
}


def pauses(identifier, duration):
    if identifier not in SPEECH:
        return []
    speech = SPEECH[identifier]
    origin = speech[0][0]
    return [(a[1]-origin, b[0]-origin) for a, b in zip(speech, speech[1:])] + [
        (speech[-1][1]-origin, duration)]


@pytest.fixture
def recorded():
    voices = [dict(voice_s=n, key=s['id']) for s, n in zip(STORY['scenes'], LENGTHS)]
    return v3.compile_data(v3.ROOT, STORY, voices=voices,
                           analyze=lambda scene, voice: pauses(scene['id'], voice['voice_s']))


def test_hover_finishes_search_and_comparison_before_the_spoken_false_strike(recorded):
    events = {e['event']:e for e in recorded['cues']['_events']['v304-hover']}
    poses = {age:t for t, age in recorded['hover_anchors']}
    strike, ratio = events['strike'], events['ratio']
    assert strike['cue'] == 'Apple is false'
    assert strike['cue_start'] <= strike['t'] < strike['cue_end']
    assert strike['t'] == poses[4800] == pytest.approx(43.7232)
    assert poses[2300] < poses[2900] == events['find']['t'] == 41.3547
    assert poses[3700] == events['compare']['t'] == pytest.approx(42.2835)
    assert poses[3700] < poses[4500] < strike['cue_start']
    assert ratio['cue'] == 'Four times too high'
    assert strike['t'] < ratio['cue_start'] <= ratio['t'] < ratio['cue_end']
    assert ratio['t'] == pytest.approx(51.2)


def test_strict_phrase_beats_do_not_snap_early_or_escape_the_phrase():
    beats = [0., 2., 2.5, 3.]
    assert snap_event(2.01, beats, 0., 4.) == 2.
    assert snap_event(2.01, beats, 0., 4., cue_end=2.6) == 2.5
    with pytest.raises(BuildError, match='inside the cue phrase'):
        snap_event(2.01, beats, 0., 4., cue_end=2.4)


def test_review_plan_covers_opening_meta_future_caveat_and_last_encoded_frame(recorded):
    timing, events = recorded['timing'], recorded['cues']['_events']
    plan = review_frame_plan(timing, events, include_boundaries=True)
    assert plan[0] == dict(shot='v301-disclosure', t=0., cue='frame zero')
    assert 0 < plan[1]['t'] <= 3
    guidance = next(f for f in plan if f.get('event') == 'guidance')
    assert guidance['shot'] == 'v307-l4' and 90 <= guidance['t'] <= 95
    future = [f for f in plan if f.get('event') == 'future']
    assert len(future) == 2 and all(104 <= f['t'] <= 106 for f in future)
    assert future[0]['sample'] == 'spoken-cue-start'
    last = plan[-1]
    assert last['shot'] == 'v312-cta' and last['cue'] == 'last encoded frame'
    assert last['t'] == (math.ceil(timing['duration']*media.FPS-1e-8)-1)/media.FPS
    assert 0 < timing['duration']-last['t'] <= 1/media.FPS
    for shot in timing['shots']:
        assert any(f['shot'] == shot['id'] and f['cue'] == 'midpoint' for f in plan)
        for event in events[shot['id']]:
            assert any(f.get('event') == event['event'] and f['shot'] == shot['id']
                       and f['t'] == round(event['t']+.3, 9) for f in plan)


def test_review_command_wires_the_extra_samples_without_rendering(tmp_path, monkeypatch, recorded):
    demo = tmp_path/'demo'
    write_json(demo/'motion/v3/cues.json', recorded['cues'])
    monkeypatch.setattr(motion_build, 'prepare', lambda *a, **k: recorded['timing'])
    monkeypatch.setattr(media, 'command', lambda *a, **k: pytest.fail('Preparation must not render'))
    builder = SimpleNamespace(demo=demo, story=STORY, scenes=STORY['scenes'],
                              args=SimpleNamespace(out=None, prepare_only=True))
    motion_build.review_frames(builder)
    output = demo/'out/review-v007'
    assert read_json(output/'plan.json') == review_frame_plan(
        recorded['timing'], recorded['cues']['_events'], include_boundaries=True)
    assert 'Matching guidance does not verify the future.' in ' '.join((output/'subtitles.srt').read_text().split())
    assert not (output/'index.json').exists()
