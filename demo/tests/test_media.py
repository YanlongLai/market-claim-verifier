"""Short, real ffmpeg integration test. Synthetic fixtures are NEVER demo footage."""
import math
import struct
import wave

import pytest
from PIL import Image

import media
from pipeline import BuildError, scene_timings


def tone(path, seconds, frequency):
    rate = 24000
    samples = []
    for i in range(round(seconds*rate)):
        t = i/rate
        envelope = min(1,t/.04,(seconds-t)/.08) * (.65+.35*math.sin(2*math.pi*2.7*t)**2)
        samples.append(round(6500*envelope*math.sin(2*math.pi*frequency*t)))
    with wave.open(str(path),'wb') as stream:
        stream.setparams((1,2,rate,0,'NONE','not compressed'))
        stream.writeframes(struct.pack('<'+'h'*len(samples),*samples))


@pytest.mark.skipif(not media.FFMPEG.exists(), reason='Homebrew ffmpeg is required for the integration smoke test')
def test_real_h264_aac_1080p_crossfades_burned_captions_and_ducked_music(tmp_path):
    scenes = [{"id":f"fixture-{i}", "target_s":3, "narration":"This is synthetic test audio. Check the number.",
               "on_screen":f"Integration fixture {i}"} for i in range(2)]
    timings = scene_timings(scenes, {s['id']:2 for s in scenes})
    voices, clips = [], []
    for i,(scene,timing) in enumerate(zip(scenes,timings)):
        folder = tmp_path / scene['id']; folder.mkdir()
        image = folder / 'fixture.png'; Image.new('RGB',(1920,1080),'#14252e' if i==0 else '#293b38').save(image)
        voice = folder / 'test-tone.wav'; tone(voice,2,240+i*120); voices.append(voice)
        clip = folder / 'clip.mp4'; media.render_scene(image,'image',scene,timing,clip); clips.append(clip)
    total = timings[-1].start_s+timings[-1].final_s
    picture, mixed, exported = tmp_path/'picture.mp4', tmp_path/'mix.wav', tmp_path/'synthetic-test-only.mp4'
    music = tmp_path/'test-music.wav'; tone(music,1.1,110) # Forces the loop path.
    media.join_visuals(clips,timings,picture)
    media.mix_audio(voices,timings,music,-22,mixed)
    levels = media.master(picture,mixed,exported,total)
    verified = media.validate_export(exported,total)
    assert verified['duration_s'] == pytest.approx(4.8,abs=.04)
    assert levels['measured_lufs'] == pytest.approx(-14,abs=.5)
    assert levels['true_peak_dbtp'] <= -1
    assert verified['video_codec']=='h264' and verified['audio_codec']=='aac'
    media.ffmpeg(['-ss','0.8','-i',exported,'-frames:v','1','-update','1',tmp_path/'burned-captions.png'])
    with Image.open(tmp_path/'burned-captions.png') as frame:
        # Check the encoded result: mint label edge at (64,64), subtitles below the picture.
        def near(point, expected):
            return all(abs(a-b) < 24 for a,b in zip(frame.getpixel(point)[:3], expected))
        assert near((66,100), (61,220,151))
        assert near((960,938), (17,26,32))
        assert near((100,780), (20,37,46))  # The former lower-third position is clear.
    media.mix_audio(voices,timings,None,-22,tmp_path/'voice-only.wav')
    assert media.duration(tmp_path/'voice-only.wav') == pytest.approx(total,abs=.001)


def test_zero_length_say_output_is_rejected(tmp_path):
    empty = tmp_path/'empty.wav'
    with wave.open(str(empty),'wb') as stream:
        stream.setparams((1,2,24000,0,'NONE','not compressed'))
    with pytest.raises(BuildError, match='zero-length'):
        media.duration(empty)


@pytest.mark.skipif(not media.FFMPEG.exists(), reason='Homebrew ffmpeg is required for capture normalization testing')
def test_capture_normalization_25fps_source_and_short_capture_rejection(tmp_path):
    source = tmp_path/'synthetic-recording-fixture.webm'
    media.ffmpeg(['-f','lavfi','-i','testsrc2=size=1920x1080:rate=25:duration=1.8',
                  '-an','-c:v','libvpx-vp9','-deadline','realtime','-cpu-used','8','-b:v','2M','-threads','2',source])
    webm, mp4 = tmp_path/'trimmed-fixture.webm',tmp_path/'normalized-fixture.mp4'
    media.normalize_capture(source,webm,mp4,1.2,.4)
    info = media.probe(mp4)
    assert info['streams'][0]['avg_frame_rate']=='30/1'
    assert info['streams'][0]['codec_name']=='h264'
    assert media.duration(mp4)==pytest.approx(1.2,abs=.034)
    assert media.duration(webm)==pytest.approx(1.2,abs=.04)
    with pytest.raises(BuildError,match='Capture ended early'):
        media.normalize_capture(source,tmp_path/'never.webm',tmp_path/'never.mp4',3,.4)
    assert not (tmp_path/'never.webm').exists()
