"""Host orchestration for v2. Preparing data never opens Chromium or synthesizes voice."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import media
import motion_media
from motion_cues import (MIN_SILENCE_S, NOISE_DB, cue_document, detect_silences, map_sentences,
                         phrase_cue, review_frame_plan, sentence_subtitles, split_phrases)
from motion_data import product_data
from motion_timing import keyframe_times, motiontest_window, presentation_timing, target_timing, video_beats
from pipeline import (BuildError, append_build_log, cache_key, cached, file_hash, make_run_record,
                      next_version, previous_run, read_json, receipt, to_srt, write_json)


def require_v2(builder) -> None:
    if builder.story.get('version') != 2:
        raise BuildError('This command needs storyboard v2. The v1 capture/assemble path remains available.')


def motion_folder(builder) -> Path:
    return builder.demo / ('motion/v3' if builder.story.get('motion_variant') == 'v3' else 'motion')


def renderer_args(builder) -> list:
    return (['--entry', 'v3/index.html'] if builder.story.get('motion_variant') == 'v3' else [])


def prepare(builder, *, require_voice: bool = False) -> dict:
    require_v2(builder)
    if builder.story.get('motion_variant') == 'v3':
        from motion_v3 import prepare as prepare_v3
        return prepare_v3(builder, require_voice=require_voice)
    folder=builder.demo/'motion'; folder.mkdir(parents=True,exist_ok=True)
    config=builder.story['music']; source=builder.repo/config['beats']
    grid=read_json(source); offset,beats=video_beats(grid)
    if abs(float(config['music_offset_s'])-offset)>1e-9:
        raise BuildError(f'music_offset_s must equal the FIRST detected beat ({offset}), not the fitted first_beat_s.')
    reference=builder.repo/builder.story['voice']['ref_audio']
    identity=cache_key(file_hash(builder.storyboard),file_hash(source),file_hash(reference))
    voices=None
    try:
        voices=[builder.require_voice(s) for s in builder.scenes]
    except BuildError:
        if require_voice:
            raise
    local,analysis={},{}
    for i,scene in enumerate(builder.scenes):
        duration=voices[i]['voice_s'] if voices else float(scene['target_s'])
        silences=[]
        if voices:
            audio=Path(voices[i]['artifacts']['audio']['path'])
            digest=file_hash(audio)
            log=builder.demo/'cache/cues'/f'{scene["id"]}-{digest}.log'
            silences=detect_silences(audio,duration,log)
            analysis[scene['id']]=dict(audio_sha256=digest,noise_db=NOISE_DB,min_silence_s=MIN_SILENCE_S,
                                       detected_pauses=len(silences),phrases=len(split_phrases(scene['narration'])))
        else:
            analysis[scene['id']]=dict(source='target preview; narration audio unavailable')
        local[scene['id']]=map_sentences(scene['narration'],duration,silences)
        if not voices:
            local[scene['id']]=(local[scene['id']][0],'proportional')
    if voices:
        focus=builder.story.get('presentation_focus')
        if focus:
            focus={**focus,'cue_start':phrase_cue(local[focus['shot']][0],focus['cue'])['start']}
        timing=presentation_timing(builder.scenes,{s['id']:v['voice_s'] for s,v in zip(builder.scenes,voices)},
                                   beats,focus,builder.pad)
        timing['voice_keys']={s['id']:v['key'] for s,v in zip(builder.scenes,voices)}
    else:
        timing=target_timing(builder.scenes)
    if timing['duration']>float(builder.story.get('max_total_s',170)):
        raise BuildError(f"v2 duration {timing['duration']:.3f} s exceeds the 170 s limit. Review narration; no speech is accelerated.")
    timing.update(version=2,input_key=identity,music_offset_s=offset,
                  cut_rule='first detected beat >= max(narration end + 0.3 s, presentation hold); '
                           'preceding shot yields time for the approved Apple focus' if voices
                           else 'approved target layout; voice not measured yet')
    beat_data=dict(source=config['beats'],source_sha256=file_hash(source),music_offset_s=offset,
                   beats_s=beats,source_beats_s=grid['beats_s'])
    cues=cue_document(builder.scenes,timing,local,analysis,beats)
    data=dict(timing=timing,beats=beat_data,cues=cues,scenes=builder.scenes,
              presentation_focus=builder.story.get('presentation_focus'),
              product=product_data(builder.repo),qr=read_json(folder/'qr-v006.json'))
    if data['qr']['url']!=builder.story['site_url']:
        raise BuildError('Precomputed QR URL differs from the storyboard CTA. Regenerate its matrix locally.')
    write_json(folder/'timing.json',timing); write_json(folder/'beats.json',beat_data)
    write_json(folder/'cues.json',cues)
    summary=['# Narration cues — demo v004','',
             'Absolute video seconds. Events use the first detected beat at or after cue start − 0.10 s.',
             'Words inside a sentence use character offsets; this is pause alignment, not forced word alignment.',
             '', '| Shot | Cue method | Event times (seconds) |', '| --- | --- | --- |']
    for scene in builder.scenes:
        shot_id=scene['id']
        events='; '.join(f"{e['event']} · {e['cue']}: {e['t']:.4f}" for e in cues['_events'][shot_id]) or '—'
        summary.append(f"| {shot_id} | {cues['_methods'][shot_id]} | {events} |")
    (folder/'cue-summary.md').write_text('\n'.join(summary)+'\n')
    import json
    (folder/'data.js').write_text('// Generated by build.py; local script data keeps file:// offline.\nwindow.MOTION_DATA = '+
                                  json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False).replace('</','<\\/')+';\n')
    return timing


def output_path(builder, default: Path) -> Path:
    path=(builder.args.out or default).resolve()
    if not path.is_relative_to(builder.demo):
        raise BuildError('--out must stay inside demo/.')
    return path


def keyframes(builder) -> None:
    timing=prepare(builder,require_voice=True)
    if builder.story.get('motion_variant') == 'v3':
        times=builder.args.t or [f['t'] for f in read_json(motion_folder(builder)/'keyframes.json')]
    else:
        times=builder.args.t or keyframe_times(timing,builder.scenes)
    if any(not math.isfinite(t) or t<0 or t>timing['duration'] for t in times):
        raise BuildError('Keyframe time must be finite and within the timeline.')
    output=output_path(builder,builder.demo/('out/keyframes-v007' if builder.story.get('motion_variant')=='v3' else 'out/keyframes-v2'))
    args=['node',builder.demo/'motion/render.mjs',*renderer_args(builder)]
    for t in times:
        args += ['--t',f'{t:.9f}']
    print(f"keyframes: {timing['source']} timing; seconds {', '.join(f'{t:.3f}' for t in times)}",flush=True)
    media.command([*args,'--out',output],builder.cache/'keyframes-v2.log')
    print(f'Key frames: {output}. Review gate 3 before running motiontest.',flush=True)


def narration_subtitles(scenes: list[dict], timing: dict, cues: dict):
    return sentence_subtitles(scenes, timing, cues)


def review_frames(builder) -> None:
    timing=prepare(builder,require_voice=True)
    cues=read_json(motion_folder(builder)/'cues.json')
    output=output_path(builder,builder.demo/('out/review-v007' if builder.story.get('motion_variant')=='v3' else 'out/review-v4'))
    output.mkdir(parents=True,exist_ok=True)
    # An old completed index must not make a new plan or failed render look reviewed.
    (output/'index.json').unlink(missing_ok=True)
    (output/'evidence.json').unlink(missing_ok=True)
    plan=review_frame_plan(timing,cues['_events'],
                           include_boundaries=builder.story.get('motion_variant')=='v3')
    write_json(output/'plan.json',plan)
    subtitles=narration_subtitles(builder.scenes,timing,cues)
    srt=output/'subtitles.srt'
    srt.write_text(to_srt(subtitles))
    if builder.args.prepare_only:
        print(f'Review plan: {output}/plan.json ({len(plan)} stills); full-length SRT: {srt}. '
              'Host Chromium renders PNGs; the same command without --prepare-only adds captioned/ stills.',flush=True)
        return
    args=['node',builder.demo/'motion/render.mjs',*renderer_args(builder)]
    for frame in plan:
        args+=['--t',f"{frame['t']:.9f}"]
    media.command([*args,'--out',output],builder.cache/'review-v4.log')
    frames=read_json(output/'render.json')['frames']
    if len(frames)!=len(plan):
        raise BuildError('Review renderer returned an incomplete frame set.')
    index=[]
    for expected,actual in zip(plan,frames):
        if actual['shot']!=expected['shot'] or abs(actual['t']-expected['t'])>1e-8 or not (output/actual['file']).is_file():
            raise BuildError('Review frame time, shot or PNG differs from its plan.')
        captioned='captioned/'+actual['file']
        subtitle=motion_media.caption_review_frame(output/actual['file'],output/captioned,subtitles,actual['t'],
                                                  font_size=56 if builder.story.get('motion_variant')=='v3' else 50)
        index.append({**expected,'file':actual['file'],'captioned_file':captioned,'subtitle':subtitle})
    write_json(output/'index.json',index)
    write_json(output/'evidence.json',dict(status='rendered',duration=timing['duration'],
               subtitles=dict(file=srt.name,sha256=file_hash(srt)),
               inputs={p.relative_to(builder.demo).as_posix():file_hash(p) for p in (builder.demo/'motion').rglob('*')
                       if p.suffix in ('.js','.css','.html','.mjs','.json')},
               frames=[dict(file=row['file'],sha256=file_hash(output/row['file']),
                            captioned_file=row['captioned_file'],captioned_sha256=file_hash(output/row['captioned_file']))
                       for row in index]))
    print(f'Review frames: {output} ({len(index)} raw + {len(index)} captioned PNGs, index.json, evidence.json).',flush=True)


def audio_master(builder, timing: dict, voices: list[dict], music: Path) -> tuple[Path, dict, str]:
    """One full-timeline mix/master shared by motion tests and the final film."""
    paths = [Path(v['artifacts']['audio']['path']) for v in voices]
    duration = math.ceil(timing['duration']*media.FPS-1e-8)/media.FPS
    gain = builder.story['music']['gain_db']
    key = cache_key('motion-audio-master-v1', timing, [(v['key'],file_hash(p)) for v,p in zip(voices,paths)],
                    file_hash(music), gain, builder.versions()['ffmpeg'],
                    [file_hash(builder.demo/name) for name in ('motion_media.py','media.py')])
    folder = builder.stage_dir('audio', 'full', key)
    files = dict(mix=folder/'mix.wav', pcm=folder/'master.wav', aac=folder/'master.m4a')
    saved = cached(folder/'receipt.json', key, files)
    if builder.args.force or not saved:
        (folder/'receipt.json').unlink(missing_ok=True)
        motion_media.mix_audio(paths,timing['shots'],music,gain,files['mix'],offset=timing['music_offset_s'],
                               timeline_duration=timing['duration'])
        levels = media.prepare_audio_master(files['mix'],files['pcm'],duration)
        saved = receipt(folder/'receipt.json',key,files,loudness=levels)
    return files['pcm'], saved['loudness'], key


def render(builder, *, test: bool = False) -> dict:
    timing=prepare(builder,require_voice=True)
    voices=[builder.require_voice(s) for s in builder.scenes]
    music=builder.music()
    if music is None:
        raise BuildError('v2 requires the pinned beat-measured music bed.')
    if media.duration(music)+1e-8 < timing['music_offset_s']+timing['duration']:
        raise BuildError('Music ends before the detected timeline. No looping/extrapolated beats are substituted.')
    if test:
        window=motiontest_window(timing,read_json(motion_folder(builder)/'beats.json')['beats_s'],builder.args.shot,builder.args.len,
                                 cue_events=read_json(motion_folder(builder)/'cues.json')['_events'])
        start,end=window['from'],window['to']
        output=output_path(builder,builder.demo/'out'/f"motiontest-{window['shot']}.mp4")
    else:
        if builder.args.out:
            raise BuildError('Full render uses versioned demo/out/demo-vNNN.mp4; --out is for keyframes/motiontest.')
        start,end=0.,timing['duration']
    length=math.ceil((end-start)*30-1e-8)/30
    source_hashes={p.relative_to(builder.demo).as_posix():file_hash(p) for p in (builder.demo/'motion').rglob('*') if p.suffix in ('.js','.css','.html','.mjs','.json')}
    implementation={p.name:file_hash(p) for p in [builder.demo/'motion_build.py',builder.demo/'motion_media.py',
                                                builder.demo/'motion_cues.py',builder.demo/'motion_timing.py',
                                                builder.demo/'media.py',builder.demo/'pipeline.py']}
    if builder.story.get('motion_variant') == 'v3':
        from motion_v3 import evidence_data
        implementation['motion_v3.py']=file_hash(builder.demo/'motion_v3.py')
        evidence=evidence_data(builder.repo)['provenance']
    else:
        evidence=product_data(builder.repo)['provenance']
    key=cache_key('motion-v2',source_hashes,implementation,evidence,start,end,[v['key'] for v in voices],file_hash(music),builder.story['music']['gain_db'])
    folder=builder.stage_dir('motion','test' if test else 'full',key)
    audio,reference,audio_key=audio_master(builder,timing,voices,music)
    frames=folder/'frames'
    print(f"{'motiontest' if test else 'render'}: {start:.3f}–{end:.3f} s, host Chromium required",flush=True)
    # The renderer records its exact time/shot for every PNG. No screen recordings or v1 captures.
    media.command(['node',builder.demo/'motion/render.mjs',*renderer_args(builder),'--from',str(start),'--to',str(end),
                   '--fps','30','--out',frames],folder/'frames.log')
    motion_media.encode_frames(frames,folder/'picture.mp4',end-start)
    cues=narration_subtitles(builder.scenes,timing,read_json(motion_folder(builder)/'cues.json'))
    local=motion_media.window_subtitles(cues,start,length)
    motion_media.burn_captions(folder/'picture.mp4',local,folder/'captioned.mp4',length,
                              font_size=56 if builder.story.get('motion_variant')=='v3' else 50)
    loudness=media.master(folder/'captioned.mp4',audio,folder/'master.mp4',length,
                          start_s=start,preview=test,reference=reference)
    validation=media.validate_export(folder/'master.mp4',length)
    if test:
        builder.alias(folder/'master.mp4',output)
        output.with_suffix('.srt').write_text(to_srt(local))
        report=dict(window=window,length=length,validation=validation,loudness=loudness,sha256=file_hash(output),
                    cache_key=key,audio_master_cache_key=audio_key)
        write_json(output.with_suffix('.json'),report)
        print(f"Preview loudness (information only): momentary max {loudness['momentary_max_lufs']} LUFS; "
              f"short-term max {loudness['short_term_max_lufs']} LUFS (needs 3 s); "
              f"true peak {loudness['true_peak_dbtp']} dBTP. Full-film integrated gate is not applied to clips.",flush=True)
        print(f'Motion test: {output}. Review gate 4 before full render.',flush=True)
        return report
    out=builder.demo/'out'; out.mkdir(parents=True,exist_ok=True)
    version=next_version(builder.demo/'runs',out)
    output=out/f'demo-v{version:03}.mp4'; srt=output.with_suffix('.srt')
    builder.alias(folder/'master.mp4',output); srt.write_text(to_srt(cues))
    records=[dict(id=s['id'],target_s=s['target_s'],voice_s=shot['voice_s'],final_s=shot['end']-shot['start'],
                  start_s=shot['start'],over_budget_percent=((shot['end']-shot['start'])/s['target_s']-1)*100,
                  engine=v['engine'],cache_keys=dict(voice=v['key'],render=key))
             for s,shot,v in zip(builder.scenes,timing['shots'],voices)]
    run=make_run_record(version=version,storyboard=builder.storyboard,scenes=records,total_s=validation['duration_s'],
                        inputs=dict(motion=source_hashes,implementation=implementation,music={builder.rel(music):file_hash(music)},
                                    narration={v['artifacts']['audio']['path']:v['artifacts']['audio']['sha256'] for v in voices},
                                    evidence=evidence),
                        versions=builder.versions(),output=output,subtitles=srt,previous=previous_run(builder.demo/'runs'),
                        assembly_cache_key=key,audio_master_cache_key=audio_key,
                        loudness=loudness,validation=validation,storyboard_version=2,
                        music_offset_s=timing['music_offset_s'],draft_only=any(v.get('draft_only') for v in voices),
                        timing_notes=timing['cut_rule']+'; hard cuts; subtitles share cues.json sentence timing and character offsets.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    write_json(builder.demo/'runs'/f'{stamp}-v{version:03}.json',run); append_build_log(builder.demo/'BUILD_LOG.md',run)
    print(f'Built {output} ({length:.3f} s) and {srt}',flush=True)
    return run
