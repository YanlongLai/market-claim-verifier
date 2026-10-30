"""Delayed v3 speech shares one origin across cuts, cues, captions and the mix."""
from copy import deepcopy
import cmath
import math
from pathlib import Path
import struct
from types import SimpleNamespace
import wave

import pytest
import yaml

from build import Builder, parser
import media
from motion_cues import cue_document, map_sentences, sentence_subtitles
import motion_media
from motion_timing import narration_start, next_beat, presentation_timing, video_beats
import motion_v3 as v3
from pipeline import BuildError, read_json, receipt, write_json

STORY = yaml.safe_load((v3.ROOT/v3.STORY).read_text())
_, BEATS = video_beats(read_json(v3.ROOT/STORY['music']['beats']))


@pytest.mark.parametrize('bad', [-1, float('nan'), float('inf'), True, '9', None])
def test_invalid_lead_fails_story_validation_before_synthesis(bad):
    story = deepcopy(STORY)
    story['scenes'][3]['narration_lead_s'] = bad
    with pytest.raises(BuildError, match='narration_lead_s'):
        Builder.validate_story(SimpleNamespace(story=story))


def test_lead_snaps_voice_and_cut_to_first_eligible_beats_without_speedup():
    scenes = [dict(id='lead', target_s=3, narration_lead_s=1.1), dict(id='default', target_s=3)]
    beats = [i*.5 for i in range(20)]
    timing = presentation_timing(scenes, dict(lead=2, default=1), beats)
    first, second = timing['shots']
    assert first['voice_start'] == 1.5
    assert first['voice_end'] == 3.5
    assert first['voice_s'] == 2
    assert first['end'] == second['start'] == 4
    assert second['voice_end'] == 5
    assert second['end'] == 6  # Absolute target hold is preserved.
    assert narration_start(dict(id='default'), 4, beats) == 4
    assert narration_start(dict(id='zero', narration_lead_s=0), 4, beats) == 4
    scenes[0]['narration_lead_s'] = 100
    with pytest.raises(BuildError, match='beat grid'):
        presentation_timing(scenes, dict(lead=2, default=1), beats)


def test_lead_edit_reuses_cached_clip_in_host_voice_step(tmp_path, monkeypatch):
    demo = tmp_path/'demo'
    demo.mkdir()
    story = deepcopy(STORY)
    story['scenes'] = [story['scenes'][3]]
    scene = story['scenes'][0]
    scene.pop('narration_lead_s')
    story['voice']['ref_audio'] = 'demo/ref.wav'
    (demo/'ref.wav').write_bytes(b'synthetic hash fixture; no licensed audio')
    (demo/'storyboard.yaml').write_text(yaml.safe_dump(story))
    builder = Builder(parser().parse_args(['voice']), demo)
    monkeypatch.setattr(builder, 'engine', lambda: 'breeze-tts-2')
    _, key, folder = builder.voice_spec(builder.scenes[0])
    files = dict(audio=folder/'clip.wav', engine_receipt=folder/'source.wav.json')
    files['audio'].write_bytes(b'synthetic cached clip fixture')
    write_json(files['engine_receipt'], dict(status='ok'))
    receipt(folder/'receipt.json', key, files, voice_s=11.04)
    prepared = []
    monkeypatch.setattr(builder, 'prepare_motion', lambda: prepared.append(True))
    monkeypatch.setattr(media, 'command', lambda *a, **k: pytest.fail('Cached voice must not invoke TTS'))
    builder.scenes[0]['narration_lead_s'] = 9
    assert builder.voice_spec(builder.scenes[0])[1] == key
    builder.voice()
    assert prepared == [True]
    assert builder.require_voice(builder.scenes[0])['voice_s'] == 11.04


def test_recorded_host_durations_delay_only_hover_and_preserve_all_scene_cuts():
    # Clip lengths from the failed host pass; no licensed audio/cache is required.
    lengths = [4.16, 7.68, 7.12, 11.04, 10, 6.64, 19.44, 9.84, 9.84, 12, 12, 8.16]
    voices = [dict(voice_s=n, key=s['id']) for s, n in zip(STORY['scenes'], lengths)]
    durations = dict(zip((s['id'] for s in STORY['scenes']), lengths))
    baseline = deepcopy(STORY['scenes'])
    baseline[3].pop('narration_lead_s')
    old = presentation_timing(baseline, durations, BEATS)
    data = v3.compile_data(v3.ROOT, STORY, voices=voices)
    local = {s['id']: map_sentences(s['narration'], n, []) for s, n in zip(baseline, lengths)}
    old_cues = cue_document(baseline, old, local, {}, BEATS)
    hover = data['timing']['shots'][3]
    assert hover['voice_start'] == next_beat(BEATS, hover['start']+9)
    delta = hover['voice_start']-hover['start']
    for before, after in zip(old['shots'], data['timing']['shots']):
        assert (before['start'], before['end']) == (after['start'], after['end'])
        assert after['voice_s'] == before['voice_s']
        if after['id'] != hover['id']:
            assert before == {k: v for k, v in after.items() if k != 'voice_start'}
            assert data['cues'][after['id']] == old_cues[after['id']]
            assert data['cues']['_events'][after['id']] == old_cues['_events'][after['id']]
    assert hover['voice_end'] == pytest.approx(old['shots'][3]['voice_end']+delta)
    for before, after in zip(old_cues[hover['id']], data['cues'][hover['id']]):
        assert after['start'] == pytest.approx(before['start']+delta)
        assert after['end'] == pytest.approx(before['end']+delta)
    for before, after in zip(old_cues['_events'][hover['id']], data['cues']['_events'][hover['id']]):
        assert after['cue_start'] == pytest.approx(before['cue_start']+delta)
        assert after['cue_end'] == pytest.approx(before['cue_end']+delta)
        assert after['t'] == next_beat(BEATS, after['cue_start']-.1)
    captions = sentence_subtitles(STORY['scenes'], data['timing'], data['cues'])
    first = next(c for c in captions if c.text.startswith('Watch Hover'))
    assert hover['voice_start']-1/30-.001 < first.start <= hover['voice_start']
    assert all(c.end <= hover['start']+1/30 or c.start >= first.start for c in captions)


def test_regression_recorded_hover_find_collided_with_reach_until_lead_added():
    # Host anchors (rounded to milliseconds): 32.067, 33.019, 34.412, 41.819, 60.209.
    # Select the exact recorded beats, rather than inventing an evenly spaced grid.
    nearest = lambda t: min(BEATS, key=lambda b: abs(b-t))
    shot = dict(id='v304-hover', start=nearest(32.067), end=nearest(60.209))
    events = dict(find=nearest(33.019), compare=nearest(34.412), strike=nearest(41.819))
    assert next_beat(BEATS, shot['start']+.9) == events['find']  # Old 1500 ms anchor.
    with pytest.raises(BuildError, match='Hover narration cues'):
        v3.hover_anchors(shot, events, BEATS)
    shot['voice_start'] = narration_start(dict(id=shot['id'], narration_lead_s=9), shot['start'], BEATS)
    delta = shot['voice_start']-shot['start']
    shifted = {k: next_beat(BEATS, t+delta) for k, t in events.items()}
    anchors = v3.hover_anchors(shot, shifted, BEATS)
    poses = dict((age, t) for t, age in anchors)
    assert shot['start'] < poses[700] < poses[1500] < poses[2300] < shot['voice_start']
    assert (poses[2900], poses[3700], poses[4800]) == (shifted['find'], shifted['compare'], shifted['strike'])
    assert all(a[0] < b[0] and a[1] < b[1] for a, b in zip(anchors, anchors[1:]))
    assert all(t in BEATS for t, _ in anchors)


def test_sparse_hover_beats_reserve_distinct_poses_instead_of_colliding():
    beats = [0, 4, 4.1, 4.2, 9, 10, 11, 12, 13, 14]
    shot = dict(start=0, voice_start=9, end=14)
    anchors = v3.hover_anchors(shot, dict(find=9, compare=10, strike=12), beats)
    assert [t for t, _ in anchors] == beats


@pytest.mark.parametrize('change,events', [
    ({'voice_start': 3}, {}),  # Only two beats for the three lead poses.
    ({}, {'compare': 5}),  # Lock and compare coincide.
    ({}, {'strike': 8}),  # No windup beat after compare.
    ({'end': 12}, {}),  # No recovery beat before the cut.
])
def test_genuinely_impossible_hover_windows_still_fail(change, events):
    with pytest.raises(BuildError, match='Hover narration cues'):
        v3.hover_anchors({**dict(start=0, voice_start=4, end=14), **change},
                         dict(find=5, compare=7, strike=11) | events, list(range(15)))


@pytest.mark.parametrize('start,length', [(0,18),(10,3),(12.25,2),(4,3),(15,2)])
def test_mix_and_ducking_use_voice_origin_in_full_and_music_only_windows(
        tmp_path, monkeypatch, start, length):
    calls = []
    monkeypatch.setattr(media, 'ffmpeg', lambda args, log: calls.append(args))
    voice, bed = Path('voice.wav'), Path('bed.wav')
    shot = dict(start=2, end=18, voice_start=11.5, voice_end=14.5)
    motion_media.mix_audio([voice], [shot], bed, -22, tmp_path/'mix.wav', offset=.5,
                           timeline_duration=18, start=start, length=length)
    args, = calls
    graph = args[args.index('-filter_complex')+1]
    assert '[voice]asplit=2[narration][sidechain]' in graph
    assert '[bed][sidechain]sidechaincompress=' in graph
    # Retain the full absolute voice/sidechain history even in a music-only
    # preview; seeking the inputs changes compressor attack/release at the cut.
    assert args[:4] == ['-t','3.000000000','-i',voice]
    assert 'adelay=552000S:all=1' in graph
    index = args.index(bed)
    assert args[index-5:index] == ['-ss','0.500000000','-t','18.000000000','-i']
    assert '[1:a]aresample=48000' in graph
    trim=f'[mixed]atrim=start={start:.9f}:duration={length:.9f},asetpts=PTS-STARTPTS[out]'
    assert graph.endswith(trim)


@pytest.mark.skipif(not media.FFMPEG.exists(), reason='Homebrew ffmpeg required')
def test_synthetic_audio_is_music_only_during_lead_and_ducks_when_voice_starts(tmp_path):
    def tone(path, seconds, frequency, amplitude):
        rate = 24000
        with wave.open(str(path), 'wb') as audio:
            audio.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
            audio.writeframes(b''.join(struct.pack('<h', round(32767*amplitude*math.sin(2*math.pi*frequency*i/rate)))
                                       for i in range(round(rate*seconds))))

    def amplitude(path, start, frequency):
        with wave.open(str(path)) as audio:
            rate, width, channels = audio.getframerate(), audio.getsampwidth(), audio.getnchannels()
            audio.setpos(round(start*rate))
            raw = audio.readframes(round(.2*rate))
        values = [int.from_bytes(raw[i:i+width], 'little', signed=True)/2**(8*width-1)
                  for i in range(0, len(raw), width*channels)]
        return 2*abs(sum(v*cmath.exp(-2j*math.pi*frequency*i/rate) for i, v in enumerate(values)))/len(values)

    voice, bed = tmp_path/'voice.wav', tmp_path/'bed.wav'
    tone(voice, 1, 230, .5)
    tone(bed, 6, 110, .15)
    shot = dict(start=0, end=6, voice_start=2, voice_end=3)
    mixed = tmp_path/'mixed.wav'
    motion_media.mix_audio([voice], [shot], bed, 0, mixed, offset=0, timeline_duration=6)
    assert amplitude(mixed, 1, 230) < .001
    assert amplitude(mixed, 2.5, 230) > .3
    assert amplitude(mixed, 2.5, 110) < amplitude(mixed, 1, 110)*.5
    window = tmp_path/'lead-only.wav'
    motion_media.mix_audio([voice], [shot], bed, 0, window, offset=0, timeline_duration=6, start=.5, length=.5)
    assert amplitude(window, .1, 110) == pytest.approx(amplitude(mixed, 1, 110), abs=.001)
