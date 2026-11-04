"""Sentence/cue synthesis and lossless assembly for the retimed v5 scenes."""
from pathlib import Path
import array, json, math, sys, wave
from pipeline import BuildError, cache_key, cached, file_hash, receipt

def units(scene):
    return [dict(id=f"{scene['id']}-{e['event']}",narration=e['narration'],visual={'kind':'motion'}) for e in scene.get('cue_events',[])]

def measure_unit(path):
    """Measure the outer speech envelope of ONE sentence, never infer internal words.

    TTS is clean PCM. Use 5 ms RMS windows at -50 dBFS, requiring two adjacent
    active windows to exclude isolated clicks. Internal pauses remain in the unit.
    Bounds include the entire first/last active window (5 ms resolution). Listening
    remains a separate acceptance gate; this is acoustic measurement, not ASR.
    """
    with wave.open(str(path)) as wav:
        channels,width,rate,count=wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes()
        if width!=2 or wav.getcomptype()!='NONE':raise BuildError('Sentence measurement requires 16-bit PCM WAV')
        pcm=array.array('h',wav.readframes(count))
    if sys.byteorder!='little':pcm.byteswap()
    window=max(1,round(rate*.005));active=[];threshold=32768*10**(-50/20)
    for a in range(0,count,window):
        chunk=pcm[a*channels:min(count,a+window)*channels]
        active.append(math.sqrt(sum(x*x for x in chunk)/len(chunk))>=threshold)
    pairs=[i for i in range(len(active)-1) if active[i] and active[i+1]]
    if not pairs:raise BuildError('Sentence source contains no measurable speech')
    start=pairs[0]*window;end=min(count,(pairs[-1]+2)*window)
    return dict(method='measured PCM speech bounds',audio_sha256=file_hash(path),sample_rate=rate,
        window_frames=window,threshold_dbfs=-50,onset_frame=start,end_frame=end,
        speech_start_s=start/rate,speech_end_s=end/rate)

def synthesize(builder):
    original=(builder.story,builder.scenes,builder.only)
    selected=builder.selected()
    jobs=[]
    for scene in selected:
        if scene.get('voice_cache_scene'):
            # Read-only: unchanged caches are never invalidated, even with --force.
            builder.require_voice(scene)
        else:jobs.extend(units(scene) or [scene])
    if jobs:
        try:
            builder.story={**builder.story,'version':1,'motion_variant':'v5-voice-units'}
            builder.scenes=jobs;builder.only={s['id'] for s in jobs}
            builder.voice(_v5_units=True)
        finally:builder.story,builder.scenes,builder.only=original
    builder.prepare_motion()

def require(builder,scene):
    sources=[builder.require_voice(unit) for unit in units(scene)]
    key=cache_key('v5-measured-sentence-assembly-r3',[(e['event'],s['key']) for e,s in zip(scene['cue_events'],sources)])
    folder=builder.stage_dir('voice',scene['id'],key)
    audio=folder/'clip.wav';meta=folder/'cues.json'
    found=cached(folder/'receipt.json',key,{'audio':audio,'cue_sources':meta})
    if found:return found
    # New v5 composite only. Every source speech sample is retained at its native rate.
    frames=[];spans=[];samples=0;params=None
    for spec,source in zip(scene['cue_events'],sources):
        path=Path(source['artifacts']['audio']['path'])
        with wave.open(str(path)) as wav:
            current=(wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getcomptype())
            if params is None:params=current
            if params!=current:raise BuildError('V5 cue voices must share the locked PCM format')
            start=samples/params[2];n=wav.getnframes();frames.append(wav.readframes(n));samples+=n
            measurement=measure_unit(path)
            spans.append(dict(event=spec['event'],narration=spec['narration'],source_start_s=start,source_end_s=samples/params[2],
                audio_sha256=file_hash(path),voice_key=source['key'],measurement=measurement,
                speech_start_s=measurement['speech_start_s'],speech_end_s=measurement['speech_end_s']))
    with wave.open(str(audio),'wb') as wav:
        wav.setnchannels(params[0]);wav.setsampwidth(params[1]);wav.setframerate(params[2]);wav.writeframes(b''.join(frames))
    meta.write_text(json.dumps(spans,indent=2)+'\n')
    receipt(folder/'receipt.json',key,{'audio':audio,'cue_sources':meta},scene_id=scene['id'],engine=sources[0]['engine'],voice_s=samples/params[2],cue_spans=spans,draft_only=any(s.get('draft_only') for s in sources),narration=scene['narration'],assembly='Lossless concatenation; placement is receipt/visual-bound in timing.json')
    return json.loads((folder/'receipt.json').read_text())
