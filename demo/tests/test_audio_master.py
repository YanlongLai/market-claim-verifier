"""Full-timeline audio gains, excerpt metering and delivery gates; no host narration."""
from pathlib import Path
from types import SimpleNamespace
import math
import re
import struct
import wave

import pytest

import media
import motion_build
import motion_media
from pipeline import BuildError


def measurement(integrated=-14, peak=-1.5):
    return dict(input_i=str(integrated),input_tp=str(peak),input_lra='2',input_thresh='-24',target_offset='0')


@pytest.mark.parametrize('seconds,preview,reference',[(2,True,True),(12,True,True),(9.99,False,True),(2,False,False)])
def test_excerpts_keep_master_gains_and_never_apply_the_integrated_gate(tmp_path,monkeypatch,seconds,preview,reference):
    calls=[]
    monkeypatch.setattr(media,'ffmpeg',lambda args,*a,**k:calls.append(args))
    monkeypatch.setattr(media,'prepare_audio_master',lambda *a:pytest.fail('excerpt normalized independently'))
    monkeypatch.setattr(media,'loudness',lambda *a:pytest.fail('excerpt hit delivery gate'))
    monkeypatch.setattr(media,'loudness_report',lambda *a:dict(measured_lufs=-16.03,true_peak_dbtp=-2.1,
                                                           momentary_max_lufs=-15.8,short_term_max_lufs=None))
    full=dict(integrated_gate=True,measured_lufs=-14,true_peak_dbtp=-1.5) if reference else None
    audio=tmp_path/'full-master.wav'
    result=media.master(tmp_path/'picture.mp4',audio,tmp_path/'clip.mp4',seconds,
                        start_s=32.5,preview=preview,reference=full)
    assert result['measured_lufs']==-16.03 and result['true_peak_dbtp']==-2.1
    assert result['integrated_gate'] is False and result['reference']==full
    assert result['normalization']==('full_timeline_master' if reference else 'source_gain')
    args=calls[0]
    assert args[args.index('-ss')+1]=='32.500000000'
    assert audio in args and audio.with_suffix('.m4a') not in args
    assert '-af' not in args and '-filter_complex' not in args  # No clip gain/limiter/loudnorm.
    assert args[args.index('-c:a')+1]=='aac'


@pytest.mark.parametrize('integrated,peak,ok',[(-14,-1.5,True),(-15,-1,True),(-13,-1,True),
                                             (-16.03,-2.1,False),(-14,-.99,False),(-12.99,-2,False)])
def test_full_delivery_copies_certified_aac_and_checks_the_muxed_file(tmp_path,monkeypatch,integrated,peak,ok):
    calls=[]
    monkeypatch.setattr(media,'ffmpeg',lambda args,*a,**k:calls.append(args))
    monkeypatch.setattr(media,'loudness',lambda *a:measurement(integrated,peak))
    monkeypatch.setattr(media,'loudness_report',lambda *a:pytest.fail('full render used the preview policy'))
    audio=tmp_path/'master.wav'
    def export():
        return media.master(tmp_path/'picture.mp4',audio,tmp_path/'film.mp4',178,
                            reference=dict(target_lufs=-14,integrated_gate=True))
    if ok:
        report=export()
        assert report['integrated_gate'] is True
        assert report['measured_lufs']==integrated and report['true_peak_dbtp']==peak
    else:
        with pytest.raises(BuildError,match='Encoded audio failed loudness verification'):
            export()
    assert calls[0][calls[0].index('-c:a')+1]=='copy'
    assert audio.with_suffix('.m4a') in calls[0]


@pytest.mark.parametrize('first,expected_i,expected_tp',[
    (measurement(-16.03,-2.1),-11.97,-1.5), (measurement(-14,-.8),-14,-1.9)])
def test_normalization_retries_correct_loudness_and_aac_peak_separately(tmp_path,monkeypatch,first,expected_i,expected_tp):
    checks=iter([first,measurement()]);scans=[];filters=[]
    def scan(path,log,target_tp=-1.5,target_i=-14):
        scans.append((path,target_i,target_tp))
        return next(checks) if path.suffix=='.m4a' else measurement(-20,-6)
    monkeypatch.setattr(media,'loudness',scan)
    def encode(args,*a,**k):
        if '-af' in args:
            filters.append(args[args.index('-af')+1])
    monkeypatch.setattr(media,'ffmpeg',encode)
    report=media.prepare_audio_master(tmp_path/'mix.wav',tmp_path/'master.wav',178)
    assert report['integrated_gate'] is True and report['attempts']==2
    normalizers=[row for row in scans if row[0].suffix=='.wav']
    assert normalizers[1][1:]==pytest.approx((expected_i,expected_tp))
    assert float(re.search(r'loudnorm=I=([^:]+)',filters[1])[1])==pytest.approx(expected_i)
    assert 'measured_I=-20' in filters[1] and filters[1].endswith(',apad')


def test_failed_full_normalization_and_short_normalization_are_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(media,'loudness',lambda *a:measurement(-16.03,-2.1))
    monkeypatch.setattr(media,'ffmpeg',lambda *a,**k:None)
    with pytest.raises(BuildError,match='at least 10 s'):
        media.prepare_audio_master(tmp_path/'mix.wav',tmp_path/'master.wav',2)
    with pytest.raises(BuildError,match='-16.03 LUFS, -2.1 dBTP'):
        media.prepare_audio_master(tmp_path/'mix.wav',tmp_path/'master.wav',178)


@pytest.mark.parametrize('momentary,short_term,peak,expected',[
    ('-120.691','-120.691','-inf',(None,None,None)),
    ('-15.25','-120.691','-2.1',(-15.25,None,-2.1)),
    ('-15.25','-16.03','-2.1',(-15.25,-16.03,-2.1))])
def test_r128_report_has_null_for_windows_the_excerpt_cannot_fill(tmp_path,monkeypatch,momentary,short_term,peak,expected):
    stderr=(f'lavfi.r128.M=-120.691\nlavfi.r128.M={momentary}\nlavfi.r128.S={short_term}\n'
            f'Integrated loudness:\n    I: -16.03 LUFS\nTrue peak:\n    Peak: {peak} dBFS\n')
    calls=[]
    def scan(args,*a,**k):
        calls.append(args);return SimpleNamespace(stderr=stderr)
    monkeypatch.setattr(media,'ffmpeg',scan)
    report=media.loudness_report(tmp_path/'clip.mp4',tmp_path/'report.log')
    assert (report['momentary_max_lufs'],report['short_term_max_lufs'],report['true_peak_dbtp'])==expected
    assert calls[0][calls[0].index('-af')+1]=='ebur128=peak=true:metadata=1,ametadata=print'


def test_audio_master_cache_is_shared_hash_checked_and_invalidated_by_timeline_gain_and_sources(tmp_path,monkeypatch):
    audio=tmp_path/'voice.wav';audio.write_bytes(b'synthetic voice')
    music=tmp_path/'bed.wav';music.write_bytes(b'synthetic music')
    for name in ('motion_media.py','media.py'):
        (tmp_path/name).write_bytes((Path(media.__file__).parent/name).read_bytes())
    def stage_dir(*parts):
        folder=tmp_path.joinpath('cache',*parts);folder.mkdir(parents=True,exist_ok=True);return folder
    builder=SimpleNamespace(demo=tmp_path,story=dict(music=dict(gain_db=-22)),
                            args=SimpleNamespace(force=False),versions=lambda:dict(ffmpeg='fixture'),stage_dir=stage_dir)
    voices=[dict(key='voice',artifacts=dict(audio=dict(path=str(audio))))]
    timing=dict(duration=178,shots=[dict(start=32,voice_start=36,voice_end=42,end=60)],music_offset_s=9.4041)
    mixes=[];normalized=[]
    def mix(*args,**kwargs):
        mixes.append(kwargs);args[4].write_bytes(b'full mix')
    def normalize(source,destination,seconds):
        normalized.append(seconds);destination.write_bytes(b'normalized full PCM')
        destination.with_suffix('.m4a').write_bytes(b'certified full AAC')
        return dict(integrated_gate=True,measured_lufs=-14,true_peak_dbtp=-1.5)
    monkeypatch.setattr(motion_media,'mix_audio',mix)
    monkeypatch.setattr(media,'prepare_audio_master',normalize)
    first=motion_build.audio_master(builder,timing,voices,music)
    assert motion_build.audio_master(builder,timing,voices,music)==first
    assert len(mixes)==1 and mixes[0]==dict(offset=9.4041,timeline_duration=178)
    assert normalized==[178]
    first[0].write_bytes(b'damaged PCM')
    assert motion_build.audio_master(builder,timing,voices,music)==first and len(mixes)==2
    keys={first[2]}
    for change in ('lead','gain','music','narration'):
        if change=='lead':timing['shots'][0]['voice_start']+=.5
        if change=='gain':builder.story['music']['gain_db']=-20
        if change=='music':music.write_bytes(b'different music')
        if change=='narration':audio.write_bytes(b'different narration')
        keys.add(motion_build.audio_master(builder,timing,voices,music)[2])
    assert len(keys)==5 and len(mixes)==6


def test_absolute_mix_preserves_lead_ducking_and_end_card_fade_before_any_trim(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(media,'ffmpeg',lambda args,*a,**k:calls.append(args))
    motion_media.mix_audio([tmp_path/'voice.wav'],[dict(start=32,voice_start=36,voice_end=42,end=60)],
                           tmp_path/'seed92.wav',-22,tmp_path/'mix.wav',offset=9.4041,
                           timeline_duration=178,start=177,length=1)
    args=calls[0];filters=args[args.index('-filter_complex')+1]
    assert args.count('-ss')==1 and args[args.index('-ss')+1]=='9.404100000'
    assert f'adelay={36*48000}S:all=1' in filters
    assert 'volume=-22dB' in filters and 'sidechaincompress=threshold=0.025:ratio=6:attack=30:release=400' in filters
    assert 'afade=t=out:st=176.000000000:d=2.000000000' in filters
    assert filters.index('sidechaincompress')<filters.index('[mixed]atrim=start=177.000000000')
    assert 'normalize=0' in filters and 'atempo' not in filters


def tone(path,seconds,frequency=230,amplitude=.25):
    rate=24000
    samples=[round(32767*amplitude*math.sin(2*math.pi*frequency*i/rate)) for i in range(round(seconds*rate))]
    with wave.open(str(path),'wb') as stream:
        stream.setparams((1,2,rate,0,'NONE','not compressed'))
        stream.writeframes(struct.pack('<'+'h'*len(samples),*samples))


@pytest.mark.skipif(not media.FFMPEG.exists(),reason='Homebrew ffmpeg required')
def test_real_mix_windows_are_sample_identical_to_full_mix_including_ducking_history_and_partial_fade(tmp_path):
    voice=tmp_path/'voice.wav';music=tmp_path/'music.wav'
    tone(voice,4);tone(music,14,110,.1)
    shots=[dict(start=1,voice_start=2,voice_end=6,end=12)]
    full=tmp_path/'full.wav'
    motion_media.mix_audio([voice],shots,music,-22,full,offset=.5,timeline_duration=12)
    with wave.open(str(full),'rb') as stream:
        assert (stream.getframerate(),stream.getnchannels(),stream.getsampwidth())==(48000,2,3)
        full_pcm=stream.readframes(stream.getnframes())
    for start,length in [(0,1),(2.1,2),(6.1,.5),(10.5,1.5)]:
        clip=tmp_path/f'window-{start}.wav'
        motion_media.mix_audio([voice],shots,music,-22,clip,offset=.5,timeline_duration=12,start=start,length=length)
        with wave.open(str(clip),'rb') as stream:
            assert stream.readframes(stream.getnframes())==full_pcm[round(start*48000)*6:round((start+length)*48000)*6]


@pytest.mark.skipif(not media.FFMPEG.exists(),reason='Homebrew ffmpeg required')
def test_real_full_master_passes_encoded_delivery_gate_and_excerpt_keeps_its_pcm_gains(tmp_path):
    # Tiny synthetic picture and tones exercise AAC/normalization without Chromium.
    music=tmp_path/'music.wav';voice=tmp_path/'voice.wav'
    tone(music,14,110,.1);tone(voice,4,230,.4)
    mixed=tmp_path/'mix.wav'
    motion_media.mix_audio([voice],[dict(start=1,voice_start=2,voice_end=6,end=12)],music,-22,mixed,
                           offset=.5,timeline_duration=12)
    picture=tmp_path/'picture.mp4';short=tmp_path/'short.mp4'
    for seconds,path in [(12,picture),(2,short)]:
        media.ffmpeg(['-f','lavfi','-i',f'color=c=0x111a20:s=160x90:r=30:d={seconds}',
                      '-an',*media.video_encoder(),path])
    full=media.master(picture,mixed,tmp_path/'film.mp4',12)
    assert full['integrated_gate'] is True
    assert abs(full['measured_lufs']+14)<=1 and full['true_peak_dbtp']<=-1
    pcm=tmp_path/'audio-master.wav'
    preview=media.master(short,pcm,tmp_path/'clip.mp4',2,start_s=8,preview=True,reference=full)
    assert preview['integrated_gate'] is False and preview['normalization']=='full_timeline_master'
    assert preview['short_term_max_lufs'] is None and preview['momentary_max_lufs'] is not None
    assert abs(preview['measured_lufs']+14)>1  # Music-only window is intentionally quieter.
    # Independently encode the same PCM slice: no new clip gain may have been applied.
    expected=tmp_path/'expected.m4a'
    media.ffmpeg(['-ss','8','-i',pcm,'-t','2','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',expected])
    decoded=[]
    for index,path in enumerate([tmp_path/'clip.mp4',expected]):
        raw=tmp_path/f'decoded-{index}.s16le'
        media.ffmpeg(['-i',path,'-vn','-f','s16le','-c:a','pcm_s16le',raw])
        decoded.append(raw.read_bytes())
    assert decoded[0]==decoded[1]


@pytest.mark.parametrize('text',['a'*43,'one\ntwo\nthree'])
def test_caption_limits_are_enforced_in_the_actual_burn_in_path(tmp_path,text):
    with pytest.raises(BuildError,match='2 lines of 42'):
        motion_media.caption_canvas(text,tmp_path/'invalid.png',font_size=56)
