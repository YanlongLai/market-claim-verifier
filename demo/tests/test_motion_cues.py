"""Cue alignment, event snapping, presentation holds and the host review command."""
import math
import re
import struct
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import media
import motion_build
from build import parser
from motion_cues import (cue_document, detect_silences, map_sentences, parse_silences,
                         phrase_cue, review_frame_plan, sentence_subtitles, snap_event, split_phrases)
from motion_timing import presentation_timing
from pipeline import BuildError, read_json, write_json


def test_sentence_splitting_keeps_decimal_numbers_and_capitalised_company_clauses():
    text = 'Amazon made 143.1 billion: true. It rose, NVIDIA doubled! Apple? 102.5 billion.'
    assert split_phrases(text) == ['Amazon made 143.1 billion:', 'true.', 'It rose,',
                                   'NVIDIA doubled!', 'Apple?', '102.5 billion.']
    with pytest.raises(BuildError, match='text'):
        split_phrases('   ')


def test_silence_mapping_ignores_edge_pauses_and_uses_absolute_video_time():
    cues, method = map_sentences('Amazon grew. Apple fell.', 2.5,
                                 [(0., .2), (.8, 1.1), (2., 2.5)], offset=12.)
    assert method == 'silence'
    assert cues == [dict(text='Amazon grew.', start=12.2, end=12.8),
                    dict(text='Apple fell.', start=13.1, end=14.)]


def test_mismatched_pause_count_falls_back_to_character_weights_across_the_clip():
    cues, method = map_sentences('A. BBBBBB!', 9., [(1., 2.), (3., 4.)], offset=20.)
    assert method == 'proportional'
    assert cues == [dict(text='A.', start=20., end=22.), dict(text='BBBBBB!', start=22., end=29.)]
    assert map_sentences('A. BBBBBB!', 9., [])[1] == 'proportional'


def test_silencedetect_parser_handles_leading_trailing_and_unclosed_silence():
    log = ('silence_start: -0.01\nsilence_end: 0.2 | silence_duration: 0.21\n'
           'silence_start: 1.1\nsilence_end: 1.3\nsilence_start: 2.8\n')
    assert parse_silences(log, 3.) == [(0., .2), (1.1, 1.3), (2.8, 3.)]


@pytest.mark.parametrize('duration,pauses', [
    (0, []), (float('nan'), []), (2, [(1, .5)]), (2, [(0, 3)]),
    (2, [(.5, 1), (.8, 1.2)]), (2, [(0, 2)]),
])
def test_bad_alignment_inputs_and_fully_silent_clips_are_rejected(duration, pauses):
    with pytest.raises(BuildError):
        map_sentences('A sentence.', duration, pauses)


def test_phrase_lookup_preserves_sentence_onsets_and_locates_words_by_character_count():
    cues = [dict(text='Apple is false.', start=10., end=25.)]
    assert phrase_cue(cues, 'Apple')['start'] == 10.
    found = phrase_cue(cues, 'false')
    assert found['start'] == 19. and found['end'] == 24.
    assert found['alignment'] == 'character-offset'
    for phrase in ['missing', '']:
        with pytest.raises(BuildError):
            phrase_cue(cues, phrase)
    with pytest.raises(BuildError, match='exactly one'):
        phrase_cue(cues + cues, 'Apple')


def test_events_snap_forward_from_the_100ms_lead_and_stay_inside_the_shot():
    beats = [0., .5, 1., 1.5, 2.]
    assert snap_event(.6, beats, 0, 2) == .5
    assert snap_event(.61, beats, 0, 2) == 1.
    assert snap_event(.02, beats, 0, 2) == 0.
    assert snap_event(.5, beats, .5, 2) == .5
    with pytest.raises(BuildError, match='shot'):
        snap_event(1.9, beats, 0, 2)
    with pytest.raises(BuildError, match='grid'):
        snap_event(5, beats, 0, 6)


def test_cue_document_links_phrase_events_to_absolute_sentence_times():
    scenes = [dict(id='s', cue_events=[dict(event='flips.0', cue='Apple')])]
    timing = dict(shots=[dict(id='s', start=10., end=15.)])
    doc = cue_document(scenes, timing, {'s': ([dict(text='Apple.', start=.6, end=2.)], 'silence')},
                       {'s': {}}, [10., 10.5, 11., 11.5, 12.])
    assert doc['s'] == [dict(text='Apple.', start=10.6, end=12.)]
    assert doc['_methods']['s'] == 'silence'
    assert doc['_events']['s'][0]['t'] == 10.5
    assert doc['_events']['s'][0]['cue_start'] == 10.6


@pytest.mark.skipif(not media.FFMPEG.exists(), reason='Homebrew ffmpeg required')
def test_real_ffmpeg_detects_two_speech_runs_in_a_synthetic_audio_fixture(tmp_path):
    rate = 16000
    samples = []
    for seconds, voiced in [(.2, False), (.4, True), (.2, False), (.4, True), (.2, False)]:
        samples += [int(12000*math.sin(2*math.pi*230*i/rate)) if voiced else 0
                    for i in range(round(seconds*rate))]
    audio = tmp_path/'two-phrases.wav'
    with wave.open(str(audio), 'wb') as stream:
        stream.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        stream.writeframes(struct.pack('<'+'h'*len(samples), *samples))
    pauses = detect_silences(audio, 1.4, tmp_path/'silencedetect.log')
    cues, method = map_sentences('First. Second.', 1.4, pauses)
    assert method == 'silence' and len(pauses) == 3
    assert [c['start'] for c in cues] == pytest.approx([.2, .8], abs=.01)
    assert [c['end'] for c in cues] == pytest.approx([.6, 1.2], abs=.01)


def test_presentation_holds_preserve_keyframes_and_finish_the_half_speed_push():
    scenes = [dict(id='intro', target_s=5), dict(id='extract', target_s=15),
              dict(id='apple', target_s=20), dict(id='cta', target_s=10)]
    beats = [i*.5 for i in range(121)]
    durations = dict(intro=2., extract=4., apple=10., cta=3.)
    focus = dict(shot='apple', cue_start=6., t=30., settle_s=.24, push_s=8.)
    timing = presentation_timing(scenes, durations, beats, focus)
    intro, extract, apple, cta = timing['shots']
    assert intro['start'] <= 3 < intro['end']
    assert extract['end'] == apple['start'] == 15.5  # Latest feasible detected beat.
    assert apple['start'] <= 30 < apple['end']
    assert snap_event(apple['start']+6., beats, apple['start'], apple['end']) + .24 + 8 <= 30
    assert cta['start'] <= 45 < cta['end']
    assert all(s['end'] in beats and s['end'] >= s['voice_end']+.3 for s in timing['shots'])
    with pytest.raises(BuildError, match='cannot fit'):
        presentation_timing(scenes, {**durations, 'extract': 20}, beats, focus)


def test_review_plan_has_each_midpoint_and_every_event_plus_300ms():
    timing = dict(shots=[dict(id='s', start=2., end=8.)])
    events = {'s': [dict(event='flips.0', cue='Amazon', t=3.), dict(event='fake', cue='rejects', t=6.)]}
    assert review_frame_plan(timing, events) == [dict(shot='s', t=5., cue='midpoint'),
                                               dict(shot='s', t=3.3, cue='Amazon', event='flips.0'),
                                               dict(shot='s', t=6.3, cue='rejects', event='fake')]
    with pytest.raises(BuildError, match='crosses'):
        review_frame_plan(timing, {'s': [dict(event='fake', cue='rejects', t=7.8)]})


def test_apple_correction_review_includes_the_exact_spoken_onsets():
    timing = dict(shots=[dict(id='s', start=2., end=8.)])
    events = {'s': [dict(event='appleYear', cue="That's the whole year", t=3.,
                         cue_start=2.95, review_at_start=True)]}
    plan = review_frame_plan(timing, events)
    assert plan[1] == dict(shot='s', t=2.95, cue="That's the whole year",
                          event='appleYear', sample='spoken-cue-start')
    assert plan[2]['t'] == 3.3


@pytest.mark.parametrize('prepare_only', [False, True])
def test_review_command_requests_only_stills_and_writes_an_index_after_rendering(tmp_path, monkeypatch, prepare_only):
    demo = tmp_path/'demo'
    (demo/'motion').mkdir(parents=True)
    timing = dict(duration=8., shots=[dict(id='s', start=2., end=8., voice_s=4., voice_end=6.)])
    write_json(demo/'motion/cues.json', {'s': [dict(text='Apple, 102.5 billion.', start=2., end=6.)],
                                       '_events': {'s': [dict(event='flips.0', cue='Apple', t=3.)]}})
    monkeypatch.setattr(motion_build, 'prepare', lambda *args, **kwargs: timing)
    args = parser().parse_args(['review-frames'] + (['--prepare-only'] if prepare_only else []))
    builder = SimpleNamespace(demo=demo, cache=demo/'cache', args=args,
                              scenes=[dict(id='s', narration='Apple, 102.5 billion.')])
    output = demo/'out/review-v4'
    write_json(output/'index.json', [dict(shot='stale', t=0, cue='old render')])
    requests = []
    def render(command, log):
        requests.append(command)
        assert '--from' not in command and '--to' not in command
        times = [float(command[i+1]) for i, flag in enumerate(command) if flag == '--t']
        assert times == [5., 3.3]
        output = Path(command[-1])
        frames = [dict(file=f'frame-{i}.png', shot='s', t=t) for i, t in enumerate(times)]
        for frame in frames:
            Image.new('RGB',(1920,1080),(17,26,32)).save(output/frame['file'])
        write_json(output/'render.json', dict(frames=frames))
    monkeypatch.setattr(media, 'command', render)
    motion_build.review_frames(builder)
    output = demo/'out/review-v4'
    plan = read_json(output/'plan.json')
    assert len(plan) == 2
    assert 'Apple, 102.5 billion.' in (output/'subtitles.srt').read_text()
    if prepare_only:
        assert not requests and not (output/'index.json').exists()
    else:
        index = read_json(output/'index.json')
        assert [{k: row[k] for k in ('shot', 't', 'cue')} for row in index] == [
            dict(shot='s', t=5., cue='midpoint'), dict(shot='s', t=3.3, cue='Apple')]
        assert all((output/row['file']).is_file() for row in index)
        assert all((output/row['captioned_file']).is_file() for row in index)
        assert all(row['subtitle']=='Apple, 102.5 billion.' for row in index)
        assert read_json(output/'evidence.json')['status']=='rendered'


@pytest.mark.parametrize('fault', ['missing-png', 'wrong-shot', 'wrong-time', 'incomplete'])
def test_failed_review_render_never_publishes_a_completed_index(tmp_path, monkeypatch, fault):
    demo = tmp_path/'demo'
    (demo/'motion').mkdir(parents=True)
    timing = dict(duration=8., shots=[dict(id='s', start=2., end=8., voice_s=4., voice_end=6.)])
    write_json(demo/'motion/cues.json', {'s': [dict(text='Apple, 102.5 billion.', start=2., end=6.)],
                                       '_events': {'s': []}})
    monkeypatch.setattr(motion_build, 'prepare', lambda *args, **kwargs: timing)
    builder = SimpleNamespace(demo=demo, cache=demo/'cache', args=parser().parse_args(['review-frames']),
                              scenes=[dict(id='s', narration='Apple, 102.5 billion.')])
    output = demo/'out/review-v4'
    write_json(output/'index.json', [dict(shot='stale', t=0, cue='old render')])
    def render(command, log):
        frame = dict(file='fixture.png', shot='other' if fault == 'wrong-shot' else 's',
                     t=5.1 if fault == 'wrong-time' else 5.)
        if fault != 'missing-png':
            (output/'fixture.png').write_bytes(b'fixture PNG')
        write_json(output/'render.json', dict(frames=[] if fault == 'incomplete' else [frame]))
    monkeypatch.setattr(media, 'command', render)
    with pytest.raises(BuildError, match='frame'):
        motion_build.review_frames(builder)
    assert not (output/'index.json').exists()


def test_captioned_review_still_matches_movie_caption_placement_and_frame_boundaries(tmp_path):
    import motion_media
    from pipeline import Subtitle
    cues = [Subtitle(.01, .1, 'Exact spoken line.'), Subtitle(.1, .3, 'Next line.')]
    assert motion_media.caption_at(cues, .02) is None
    assert motion_media.caption_at(cues, 1/30)=='Exact spoken line.'
    assert motion_media.caption_at(cues, .1)=='Next line.'
    assert motion_media.caption_at(cues, .3) is None
    source=tmp_path/'raw.png'
    Image.new('RGB',media.SIZE,(17,26,32)).save(source)
    shown=tmp_path/'captioned/shown.png'
    assert motion_media.caption_review_frame(source,shown,cues,1/30)=='Exact spoken line.'
    from PIL import ImageChops
    with Image.open(source) as raw, Image.open(shown) as captioned:
        bounds=ImageChops.difference(raw,captioned).getbbox()
        assert bounds and bounds[1]>=880 and bounds[3]<=1080
        overlay=motion_media.caption_canvas('Exact spoken line.',tmp_path/'panel.png')
        expected=raw.convert('RGBA');expected.alpha_composite(overlay)
        assert ImageChops.difference(expected.convert('RGB'),captioned).getbbox() is None
    silent=tmp_path/'captioned/silent.png'
    assert motion_media.caption_review_frame(source,silent,cues,.3) is None
    with Image.open(source) as raw, Image.open(silent) as same:
        assert ImageChops.difference(raw,same).getbbox() is None
    Image.new('RGB',(960,540)).save(source)
    with pytest.raises(BuildError,match='1920'):
        motion_media.caption_review_frame(source,shown,cues,.1)


def test_prepared_subtitles_cover_unchanged_narration_with_unchanged_voice_keys():
    import yaml
    from build import DEMO
    from pipeline import to_srt
    story=yaml.safe_load((DEMO/'storyboard.yaml').read_text())
    timing=read_json(DEMO/'motion/timing.json')
    run=read_json(DEMO/'runs/20261029T034926032314Z-v002.json')
    document=read_json(DEMO/'motion/cues.json')
    cues=motion_build.narration_subtitles(story['scenes'],timing,document)
    assert to_srt(cues)==(DEMO/'tests/fixtures/review-v4-subtitles.srt').read_text()
    for scene,shot,previous in zip(story['scenes'],timing['shots'],run['scenes']):
        assert shot['start']==previous['start_s']
        assert timing['voice_keys'][shot['id']]==previous['cache_keys']['voice']
        spoken=[c.text for c in cues if c.end>shot['start'] and c.start<shot['voice_end']]
        assert ' '.join(' '.join(spoken).split())==' '.join(scene['narration'].split())
    assert all(len(c.text.splitlines())<=2 and all(len(line)<=42 for line in c.text.splitlines()) for c in cues)
    assert cues[-1].end<=timing['duration']
    assert all(a.end<=b.start for a,b in zip(cues,cues[1:]))


def parse_srt(text):
    from pipeline import Subtitle
    def seconds(stamp):
        h,m,s,ms=map(int,re.split('[:,]',stamp))
        return h*3600+m*60+s+ms/1000
    entries=[]
    for block in text.strip().split('\n\n'):
        _,interval,*lines=block.splitlines()
        a,b=interval.split(' --> ')
        entries.append(Subtitle(seconds(a),seconds(b),'\n'.join(lines)))
    return entries


def test_every_motion_cue_is_inside_the_exported_srt_entry_containing_its_phrase():
    import motion_media
    from build import DEMO
    document=read_json(DEMO/'motion/cues.json')
    subtitles=parse_srt((DEMO/'tests/fixtures/review-v4-subtitles.srt').read_text())
    checked=0
    for shot,events in document['_events'].items():
        for event in events:
            phrase=event['cue'].casefold()
            # Test the actual SRT, not only pre-serialization floating timestamps.
            for time in (event['cue_start'],event['cue_end']-1e-6,event['t']+.3):
                active=[s for s in subtitles if s.start<=time<s.end]
                assert len(active)==1,(shot,phrase,time)
                assert phrase in ' '.join(active[0].text.split()).casefold(),(shot,phrase,time,active)
                rendered=motion_media.caption_at(subtitles,time)
                assert rendered and phrase in ' '.join(rendered.split()).casefold(),(shot,phrase,time,rendered)
            checked+=1
    assert checked==37


@pytest.mark.parametrize('phrase',["Amazon","Apple","That's the whole year","The quarter was 102.5 billion"])
def test_review_regression_phrases_are_active_at_their_exact_onsets(phrase):
    import motion_media
    from build import DEMO
    event=next(e for e in read_json(DEMO/'motion/cues.json')['_events']['m05-verdicts'] if e['cue']==phrase)
    subtitles=parse_srt((DEMO/'tests/fixtures/review-v4-subtitles.srt').read_text())
    assert phrase in ' '.join(motion_media.caption_at(subtitles,event['cue_start']).split())


def test_chinese_subtitle_survives_the_late_beat_and_300ms_review_sample():
    import motion_media
    from build import DEMO
    event=next(e for e in read_json(DEMO/'motion/cues.json')['_events']['m09-chinese'] if e['cue']=='too')
    subtitles=parse_srt((DEMO/'tests/fixtures/review-v4-subtitles.srt').read_text())
    assert motion_media.caption_at(subtitles,event['t']+.3)=='It works in Chinese too.'


def test_long_sentence_wrap_keeps_the_entire_fiscal_cue_in_one_entry():
    text=('Code re-reads the number and its precision, checks fiscal and calendar years, '
          'and rejects any evidence the model made up.')
    phrase='checks fiscal and calendar years'
    document={'s':[dict(text=text,start=10.,end=22.1)],
              '_events':{'s':[dict(cue=phrase,t=14.5)]}}
    captions=sentence_subtitles([dict(id='s')],dict(shots=[dict(end=24.,voice_end=22.1)]),document)
    assert len(captions)==2
    assert any(phrase in ' '.join(c.text.split()) for c in captions)
    # The second chunk follows its character offset inside the aligned sentence.
    second_offset=text.index('checks')
    assert 10.+12.1*second_offset/len(text)-1/30-.001<=captions[1].start<=10.+12.1*second_offset/len(text)+1e-8
    assert ' '.join(' '.join(c.text.split()) for c in captions)==text
