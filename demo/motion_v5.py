#!/usr/bin/env python3
"""Compile the binding 178-second v5 timeline, reusing retained measured metadata offline."""
from __future__ import annotations
import argparse,copy,json,math,re
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml
from motion_cues import sentence_subtitles,split_phrases
from pipeline import BuildError,file_hash,read_json,to_srt,subtitle_chunks
ROOT=Path(__file__).resolve().parents[1]
OUT='demo/motion/v5'
BOUNDARIES=[0.,8.,20.,32.,46.,58.,116.,138.,154.,170.,178.]
LIVE_PHASES=('live_workspace_reveal','use_apple_example','check_against_sec','verdict_reveal','draft_reveal','evidence_reveal','tool_call_2_reveal','tool_call_4_reveal','program_verdict_reveal','hover_receipt')
CJK=re.compile('[\u2e80-\u9fff\uac00-\ud7af\uf900-\ufaff\U00020000-\U000323af]')

def english_only(text,label):
    if CJK.search(text):raise BuildError(f'{label}: non-English glyph in film source')

def validate(story):
    scenes=story['scenes']
    if story.get('version')!=2 or story.get('motion_variant')!='v5' or [s['id'] for s in scenes]!=[f'v50{i}' for i in range(10)]:
        raise BuildError('v5 requires scenes v500 through v509 in order')
    for i,s in enumerate(scenes):
        if [s['target_start_s'],s['target_end_s'],s['target_s']]!=[BOUNDARIES[i],BOUNDARIES[i+1],BOUNDARIES[i+1]-BOUNDARIES[i]]:raise BuildError('Binding scene table changed')
        if ' '.join(s['narration'].split())!=' '.join(' '.join(s['subtitle_cues']).split()):raise BuildError('Captions differ from locked narration')
        if any(len(c.splitlines())>2 or any(len(line)>42 for line in c.splitlines()) for c in s['subtitle_cues']):raise BuildError('Captions exceed 2 x 42')
        if s['cue_events'] and s['narration']!=' '.join(e['narration'] for e in s['cue_events']):raise BuildError('Cue words differ from locked narration')
        if not s['cue_events'] or s.get('voice_cache_scene') or any(len(split_phrases(e['narration']))!=1 or len(subtitle_chunks(e['narration']))!=1 for e in s['cue_events']):
            raise BuildError('Every v5 sentence/phrase requires its own voice unit; multi-sentence cache aliases are forbidden')
        if i in (5,8) and bool(s.get('placeholder'))==bool(s.get('recording')):raise BuildError('Live scene must be pending or recorded')
        if i not in (5,8) and (s.get('placeholder') or s.get('recording')):raise BuildError('Only live scenes accept recordings')
    live_events=scenes[5]['cue_events']
    if tuple(dict.fromkeys(e.get('receipt_phase') for e in live_events))!=LIVE_PHASES:
        raise BuildError('Live sentence cues must cover the recorded picture phases, in order')
    previous_phase=-1;previous_offset=-1
    for event in live_events:
        phase=LIVE_PHASES.index(event['receipt_phase']);offset=event.get('offset_s',0)
        if (type(offset) not in (int,float) or not math.isfinite(offset) or offset<0 or phase<previous_phase
            or phase==previous_phase and offset<=previous_offset):
            raise BuildError('Live phase offsets must be finite, nonnegative and ordered')
        previous_phase,previous_offset=phase,offset
    chapter=story['chapter_bar'];segments=chapter['segments']
    if len(segments)!=10 or sum(s['duration_s'] for s in segments)!=178:raise BuildError('Chapter segments must total 178 seconds')
    for i,s in enumerate(segments):
        if s['scene']!=scenes[i]['id'] or [s['start_s'],s['end_s'],s['duration_s']]!=[BOUNDARIES[i],BOUNDARIES[i+1],scenes[i]['target_s']]:raise BuildError('Chapter segments differ from cuts')
    if (chapter['height_px']!=12 or chapter['label_font_px']<32 or chapter['top_px']+12>chapter['caption_zone_top_px'] or chapter['caption_zone_top_px']<880):raise BuildError('Chapter bar overlaps caption lane')
    if story['max_total_s']!=178 or story['target_total_s']!=178:raise BuildError('Binding duration is 178 seconds')
    english_only(json.dumps(story,ensure_ascii=False),'storyboard')

def metrics(root):
    folder='docs/evidence/eval-v2-2026-10-27'
    rows=[read_json(p) for p in sorted((root/folder).glob('*--agent@baseten.json'))]
    gold_path='eval/v2/claims-v2-corrected.jsonl'
    gold={r['id']:r['gold_verdict'] for r in map(json.loads,(root/gold_path).read_text().splitlines())}
    test=[r for r in rows if r['split']=='test'];neg=[r for r in test if gold[r['id']]!='supported']
    completed=[r for r in test if r['status']=='completed']
    from scale_v4 import compile_scale
    scale=compile_scale(root)
    return dict(heldout_correct=sum(r['status']=='completed' and r['verdict']==gold[r['id']] for r in test),heldout_n=len(test),false_support=sum(r['status']=='completed' and r['verdict']=='supported' for r in neg),negative_n=len(neg),mean_cost_usd=sum(r['cost_usd'] for r in completed)/len(completed),median_claim_seconds=scale['eval_v2']['median_completed_latency_seconds']),[gold_path,*[p.relative_to(root).as_posix() for p in sorted((root/folder).glob('*--agent@baseten.json'))]]

def cue_spans(scene,voice=None):
    events=scene['cue_events']
    if not events:return []
    spans=[]
    if voice:
        spans=voice.get('cue_spans',[])
        if [s['event'] for s in spans]!=[s['event'] for s in events]:raise BuildError(f"{scene['id']}: measured cue sources missing or stale")
    previous_end=0.;previous_speech_end=-1.
    for i,event in enumerate(events):
        floor=event['at_scene_s'];live=bool(event.get('receipt_phase'))
        # Several independently measured sentences can share one stationary native
        # phase. Their offsets are earliest starts; retain all PCM and queue safely.
        next_phase=next((e for e in events[i+1:] if e.get('receipt_phase')!=event.get('receipt_phase')),None) if live else None
        limit=next_phase['at_scene_s'] if next_phase else scene['target_s']-.15
        if not live:limit=scene['target_s']-.15
        if not math.isfinite(floor) or floor<0 or limit<=floor:raise BuildError('Cue onsets must increase inside the scene')
        source=spans[i] if voice else None
        if source:
            if (source.get('narration')!=event['narration'] or source.get('measurement',{}).get('method')!='measured PCM speech bounds'
                or not source.get('audio_sha256') or source['measurement'].get('audio_sha256')!=source['audio_sha256']):
                raise BuildError(f"{scene['id']} / {event['event']}: measured sentence onset missing or stale; run voice on the host")
            leading=source['speech_start_s'];duration=source['source_end_s']-source['source_start_s']
            if not 0<=leading<source['speech_end_s']<=duration:raise BuildError('Invalid measured speech bounds')
        else:
            leading=0.;duration=min(len(event['narration'])/16,max(.1,limit-floor-.35))
        # Web states follow the measured speech clock. Live phases are fixed by
        # the continuous take; other sentences may move later to retain every sample.
        # A phase's original zero-offset cue keeps its existing 0.2 s picture
        # lead. Added offsets specify earliest speech onsets on that phase clock.
        onset=max(.2,floor+(.2 if live and not event.get('offset_s') else 0),leading)
        if voice and not i and not live and onset>.3:
            raise BuildError(f"{scene['id']}: leading silence would expose the first picture more than 0.3 s before speech")
        a=onset-leading
        same_phase=live and i>0 and events[i-1].get('receipt_phase')==event['receipt_phase']
        if not live or same_phase:a=max(a,previous_end+(.06 if i else 0),previous_speech_end+.2-leading)
        if live and event['receipt_phase']=='check_against_sec' and a+duration>limit-.4+1e-8:
            raise BuildError(f"{scene['id']} / {event['event']}: measured voice needs 0.4 s margin before verdict_reveal; retain the take and repair narration")
        if duration<=0 or a+duration>limit+1e-8 or (live and a<previous_end-1e-8):
            raise BuildError(f"{scene['id']} / {event['event']}: measured voice {duration:.3f} s exceeds {limit-a:.3f} s visual budget. Retain the take; no speech is cut or accelerated.")
        previous_end=a+duration
        previous_speech_end=a+(source['speech_end_s'] if source else duration)
        yield event,a,duration,source

def voice_input(story):
    return dict(voice=story['voice'],scenes=[dict(id=s['id'],narration=s['narration'],cue_events=[
        dict(event=e['event'],narration=e['narration']) for e in s['cue_events']]) for s in story['scenes']])

def measured_metadata(voices):
    if not voices:return None
    return [dict(voice_s=v['voice_s'],key=v['key'],artifacts={'audio':{'sha256':v['artifacts']['audio']['sha256']}},
        **({'cue_spans':copy.deepcopy(v['cue_spans'])} if v.get('cue_spans') else {})) if v else None for v in voices]

def architecture(root,on_screen):
    """Reuse the diagram, with its rendered headline bound to the storyboard."""
    ET.register_namespace('','http://www.w3.org/2000/svg')
    svg=ET.fromstring((root/'demo/assets/architecture-v4.svg').read_text())
    ns={'s':'http://www.w3.org/2000/svg'}
    svg.find('s:title',ns).text=on_screen
    svg.find('s:desc',ns).text='Post, Muse Spark, SEC facts, Python verdict and corrected draft. Twelve seconds.'
    heading=next(el for el in svg.findall('.//s:text',ns) if el.get('y')=='192')
    heading.text=on_screen;heading.set('data-on-screen','v504')
    next(el for el in svg.findall('.//s:text',ns) if el.get('y')=='780').set('y','750')
    return ET.tostring(svg,encoding='unicode')

def compile_data(root=ROOT,story=None,voices=None,*,preview=False):
    story=copy.deepcopy(story or yaml.safe_load((root/'demo/storyboard-v5.yaml').read_text()));validate(story)
    saved=read_json(root/OUT/'inputs.json') if (root/OUT/'inputs.json').is_file() else {}
    if preview and voices is None and saved.get('voices') and saved.get('voice_input',{}).get('voice')==story['voice']:
        # Keep unchanged scenes' measured clocks. A changed scene is explicitly
        # unmeasured until host synthesis; never invent PCM bounds for new words.
        old={s['id']:(s,v) for s,v in zip(saved['voice_input']['scenes'],saved['voices'])}
        voices=[old[s['id']][1] if old.get(s['id'],(None,None))[0]==s else None for s in voice_input(story)['scenes']]
    if not preview and voices is None and saved.get('voices'):
        if saved.get('voice_input')!=voice_input(story):raise BuildError('Measured voice metadata is stale for the narration; host voice/measured step required')
        voices=saved['voices']
    portable=dict(version=1,voice_input=voice_input(story),voices=measured_metadata(voices),recordings={})
    baseline=yaml.safe_load((root/'demo/storyboard-v4.yaml').read_text())
    if story['voice']!=baseline['voice'] or story['music']!=baseline['music']:raise BuildError('Locked voice/music changed')
    live=story['scenes'][5];live_receipt=None
    from record_v5 import live_cue_events,RecordingError,check_recordings,apple_filing_citations,with_phase_aliases
    try:check_recordings(story,root,required=False)
    except RecordingError as e:raise BuildError(str(e)) from e
    if live.get('recording'):
        recording=live['recording'];path=root/recording['receipt']
        retained=saved.get('recordings',{}).get(live['id'],{})
        if path.is_file():
            if file_hash(path)!=recording['receipt_sha256']:raise BuildError('Wired live receipt changed')
            live_receipt=with_phase_aliases(read_json(path))
        elif retained.get('recording')==recording:live_receipt=with_phase_aliases(retained['receipt'])
        else:raise BuildError('Wired live receipt missing; no matching portable metadata')
        resolved=live_cue_events(live,live_receipt)
        if resolved!=live['cue_events']:raise BuildError('Live cues are stale for their receipt; rewire on host')
    else:
        for event in live['cue_events']:event['at_scene_s']=event['preview_at_scene_s']
    for scene in story['scenes']:
        if not scene.get('recording'):continue
        recording=scene['recording'];path=root/recording['receipt']
        if path.is_file():
            if file_hash(path)!=recording['receipt_sha256']:raise BuildError('Wired live receipt changed')
            receipt=read_json(path)
            fields=('capture_version','timings','geometry_checks','startup_cover','named_element_checks','ending_frame','server_log')
            summary={k:receipt[k] for k in fields if k in receipt}
            summary['result']={k:receipt['result'][k] for k in ('cost_usd','cost_is_bound','latency_ms','model','provider','verdict','request_id') if k in receipt['result']}
            from live_terminal_v5 import trace_events
            summary['result']['events']=trace_events(receipt['result']['events'])
            # Retain the exact source objects for offline citation rebuilding.
            summary['result']['evidence']=[e for e in receipt['result']['evidence'] if e.get('evidence_id')=='E3']
            summary['result']['corrections']={'edits':[e for e in receipt['result']['corrections']['edits'] if 'E3' in e.get('evidence_ids',[])]}
            portable['recordings'][scene['id']]=dict(recording=recording,asset_sha256=receipt['mp4']['sha256'],receipt=summary)
        else:
            retained=saved.get('recordings',{}).get(scene['id'],{})
            if retained.get('recording')!=recording:raise BuildError('Live preview metadata differs from storyboard wiring')
            portable['recordings'][scene['id']]=retained
    filing_citations=apple_filing_citations(live_receipt['result']) if live_receipt else []
    shots=[];cues={'_version':2,'_methods':{},'_analysis':{},'_events':{}}
    for i,scene in enumerate(story['scenes']):
        voice=voices[i] if voices else None
        duration=voice['voice_s'] if voice else scene['target_s']-.3
        if not math.isfinite(duration) or duration<=0:raise BuildError('Invalid voice duration')
        shot=dict(id=scene['id'],start=scene['target_start_s'],end=scene['target_end_s'],voice_start=scene['target_start_s'],voice_end=scene['target_start_s']+duration,voice_s=duration)
        local=[];events=[];segments=[]
        if scene['cue_events']:
            previous_speech_end=None
            for event,at,length,source in cue_spans(scene,voice):
                onset=at+(source['speech_start_s'] if source else 0)
                end=at+(source['speech_end_s'] if source else length)
                # Lead the sentence by 0.2 s, but never take the picture from the previous
                # sentence before its last word (+0.05 s); the lead then shrinks to the gap.
                picture=max(0,onset-.2)
                if previous_speech_end is not None:
                    picture=max(picture,min(onset-.1,previous_speech_end+.05))
                previous_speech_end=end
                event['picture_at_scene_s']=picture
                native=next((c for c in (live_receipt or {}).get('named_element_checks',[]) if c['phase']==event.get('receipt_phase')),None)
                if voice and native and (onset<native['at_s'] or end>native.get('visible_until_s',-1)):
                    raise BuildError(f"{scene['id']} / {event['event']}: named native element is not held through the measured last word; retain and repair the take")
                local.append(dict(text=event['narration'],start=onset,end=end,event=event['event'],measured=bool(source),measurement=source['measurement'] if source else None))
                events.append(dict(event=event['event'],cue=subtitle_chunks(event['narration'])[0].splitlines()[0],narration=event['narration'],t=shot['start']+picture,picture_start=shot['start']+picture,cue_start=shot['start']+onset,cue_end=shot['start']+end,receipt_phase=event.get('receipt_phase'),terminal_block=event.get('terminal_block'),alignment='measured PCM speech bounds' if voice else 'target preview',measured=bool(source),measurement=source['measurement'] if source else None,native_check=native,review_at_start=True))
                if source:segments.append(dict(source_start_s=source['source_start_s'],source_end_s=source['source_end_s'],at_s=shot['start']+at,event=event['event']))
            shot['voice_end']=shot['start']+local[-1]['end']
            if voice:shot['voice_segments']=segments
        cues[scene['id']]=[{**c,'start':shot['start']+c['start'],'end':shot['start']+c['end']} for c in local]
        cues['_events'][scene['id']]=events;cues['_methods'][scene['id']]='measured PCM speech bounds per sentence/phrase' if voice else 'target preview; unmeasured'
        cues['_analysis'][scene['id']]={'voice_key':voice['key'],'audio_sha256':voice['artifacts']['audio']['sha256']} if voice else {'source':'target preview; not synthesized'}
        shots.append(shot)
    timing=dict(version=2,source=('measured cue sources / binding cuts' if all(voices) else 'mixed measured scenes / changed scene unmeasured / binding cuts') if voices else 'director targets; voice and new live capture pending',duration=178.,shots=shots,music_offset_s=story['music']['music_offset_s'],cut_rule='Fixed section 10 cuts; receipt-bound narration and overlays; no speech acceleration or truncation',placeholders=[s['id'] for s in story['scenes'] if s.get('placeholder')])
    captions=sentence_subtitles(story['scenes'],timing,cues)
    if any(len(c.text.splitlines())>2 or any(len(line)>42 for line in c.text.splitlines()) for c in captions):raise BuildError('Compiled captions exceed 2 x 42')
    values,metric_sources=metrics(root)
    asset_receipt=read_json(root/'demo/assets/examples-v5/receipt.json')
    for item in asset_receipt['inputs']+asset_receipt['derived']:
        if file_hash(root/item['path'])!=item['sha256']:raise BuildError('Copied example/preview changed since receipt')
    waveform=read_json(root/'demo/assets/examples-v5/a-waveform.json')['bins']
    inputs=[dict(type=ext,label=label,source=f'a.{ext}',preview=f'demo/assets/examples-v5/{preview}') for ext,label,preview in [('png','Screenshot','a.png'),('pdf','PDF','a-pdf-page1.png'),('audio','Audio','a-waveform.json'),('mp4','Video','a-video-frame.png')]]
    inputs[2]['source']='a.mp3'
    sources=set(metric_sources+['demo/storyboard-v5.yaml','demo/storyboard-v4.yaml','demo/assets/architecture-v4.svg','demo/assets/examples-v5/receipt.json','demo/assets/examples-v5/a.txt','demo/data/scale-v4.json',story['music']['beats']])
    for s in story['scenes']:sources.update(s['evidence'])
    for item in asset_receipt['inputs']+asset_receipt['derived']:sources.add(item['path'])
    from terminal_v5 import compile_replays,bind_replays
    terminal,terminal_sources=compile_replays(root);sources.update(terminal_sources)
    terminal=bind_replays(terminal,story['scenes'],cues)
    sources.update(story['brand_motion']['poses'].values());sources.add(story['brand_motion']['source_script'])
    provenance={p:file_hash(root/p) for p in sorted(sources)}
    for retained in portable['recordings'].values():
        recording=retained['recording']
        provenance[recording['receipt']]=recording['receipt_sha256'];provenance[recording['asset']]=retained['asset_sha256']
    keyframes=[dict(t=t,shot=f'v50{i}',cue='beat boundary') for i,t in enumerate(BOUNDARIES[:-1])]
    keyframes.extend(dict(t=s['start']+(s['end']-s['start'])/2,shot=s['id'],cue='midpoint') for s in shots)
    keyframes.extend(dict(t=e['t']+.15,shot=s['id'],cue=e['event']) for s in shots for e in cues['_events'][s['id']])
    keyframes.extend(dict(t=e['t'],shot=s['id'],cue=e['event']+' onset') for s in shots for e in cues['_events'][s['id']])
    if live_receipt:keyframes.extend(dict(t=58+c['at_s'],shot='v505',cue=c['phase']+' named element audit') for c in live_receipt.get('named_element_checks',[]))
    keyframes.extend(dict(t=170+t,shot='v509',cue='hero stamp motion') for t in (0,.3,.6,1.1,1.6))
    for shot in shots:
        for n,cue in enumerate(cues[shot['id']]):
            keyframes.append(dict(t=cue['start'],shot=shot['id'],cue=f'sentence {n+1} start'))
            keyframes.append(dict(t=max(cue['start'],cue['end']-1/30),shot=shot['id'],cue=f'sentence {n+1} end'))
            keyframes.append(dict(t=cues['_events'][shot['id']][n]['picture_start'],shot=shot['id'],cue=f'sentence {n+1} picture ready'))
    stamp_at=next(e['picture_start'] for e in cues['_events']['v509'] if e['event']=='wordmark')
    if stamp_at+story['brand_motion']['duration_s']>176.8:raise BuildError('Robot stamp must complete before the sign-off fade')
    keyframes.extend(dict(t=stamp_at+t,shot='v509',cue='sentence-bound completed stamp') for t in (0,.3,.6,1.1,1.6))
    keyframes.append(dict(t=178-1/30,shot='v509',cue='last encoded frame'))
    for index in (0,2,5,7,9):keyframes.append(dict(t=BOUNDARIES[index]+1,shot=f'v50{index}',cue='chapter sample'))
    data=dict(timing=timing,cues=cues,beats={'beats_s':[t-story['music']['music_offset_s'] for t in read_json(root/story['music']['beats'])['beats_s'] if t>=story['music']['music_offset_s']]},scenes=story['scenes'],chapter_bar=story['chapter_bar'],brand=story['brand'],brand_motion=story['brand_motion'],keyframes=sorted(keyframes,key=lambda f:f['t']),subtitles=[dict(start=c.start,end=c.end,text=c.text) for c in captions],metrics=values,post_text=(root/'demo/assets/examples-v5/a.txt').read_text().strip(),inputs=inputs,waveform=waveform,architecture_svg=architecture(root,story['scenes'][4]['on_screen']),live_receipt=dict(cost_usd=live_receipt['result']['cost_usd'],latency_ms=live_receipt['result']['latency_ms'],model=live_receipt['result']['model'],tool_calls=len([e for e in live_receipt['result']['events'] if e['kind']=='tool_call'])) if live_receipt else None,terminal_replays=terminal,batch_labels=story['terminal_captions'],live_named_elements=live_receipt.get('named_element_checks',[]) if live_receipt else [],ending_named_elements=portable['recordings'].get('v508',{}).get('receipt',{}).get('ending_frame',{}).get('named_elements',[]),portable_inputs=portable,provenance=provenance,asset_status={'live':('new v7 capture wired' if live_receipt.get('capture_version')==7 else 'host re-record required: legacy take has no audited startup cover') if live_receipt else 'host capture pending','voice':('measured' if all(voices) else 'partially measured; changed scene needs host synthesis') if voices else 'unmeasured layout preview','terminal':'literal saved PTY ranges; no new OCR/ASR','broll':'none'})
    data['live_filing_citations']=filing_citations
    from live_terminal_v5 import compile_live_terminal,compile_local_terminal
    data['live_terminal']=compile_live_terminal(live_receipt,root) if live_receipt else None
    data['local_terminal']=compile_local_terminal(root)
    data['trace_format']=2
    data['asset_status']['terminal']='Real pod log + recorded local CLI; OCR/ASR remain labelled saved replays'
    local_block=next(b for b in terminal['beat6']['blocks'] if b['block']=='run')
    local_trace=data['local_terminal']
    # Retain time for typing and a readable final receipt; compression is explicit.
    window=local_block['end_s']-local_block['at_s']
    if window<=1:raise BuildError('Local CLI block needs room for typing, replay and final receipt hold')
    speed=max(1,math.ceil(local_trace['source_duration_s']/(window-1.0)))
    local_trace.update(start_scene_s=local_block['at_s']+.6,typing_start_scene_s=local_block['at_s'],
        end_scene_s=local_block['end_s'],speed=speed,honesty_label=f'replayed at {speed}×' if speed>1 else 'recorded local CLI · real time')
    for path in ('demo/assets/cli-v5/local-cli.json','demo/assets/cli-v5/receipt.json'):
        data['provenance'][path]=file_hash(root/path)
    if data['live_terminal']:
        trace=data['live_terminal'];start=58+trace['start_scene_s']
        keyframes.extend(dict(t=t,shot='v505',cue=cue) for t,cue in [
            (58+trace['typing_start_scene_s'],'terminal command starts'),
            (start,'terminal stopwatch starts'),
            *[(start+r['at_s'],f"server log {r['event']}") for r in trace['rows']],
            (start+trace['verdict']['at_s'],'terminal verdict and stopped clock'),
            (58+trace['end_scene_s']-1/30,'terminal final hold')])
        data['keyframes']=sorted(keyframes,key=lambda f:f['t'])
        data['provenance'][live_receipt['server_log']['path']]=live_receipt['server_log']['sha256']
    keyframes.extend(dict(t=116+local_trace['start_scene_s']+r['at_s']/speed,shot='v506',cue='local CLI chunk') for r in local_trace['frames'])
    # Whole-composite checks include the silent spaces, both gutters and mask changes.
    keyframes.extend(dict(t=t,shot='v505',cue='whole composite continuity') for t in range(58,116))
    keyframes.extend(dict(t=e['t']+delta,shot='v505',cue='composite cue edge') for e in cues['_events']['v505'] for delta in (-1/30,0,1/30) if 58<=e['t']+delta<116)
    data['keyframes']=sorted(keyframes,key=lambda f:f['t'])
    data['asset_status']['live']=('v9 capture with native text line audit wired' if (live_receipt or {}).get('capture_version')==9
        else 'host re-record required: retained take lacks the v9 card-edge audit')
    english_only(json.dumps(data,ensure_ascii=False),'compiled motion data')
    return data

def artifacts(data,root=ROOT):
    outputs={f'{OUT}/{k}.json':json.dumps(data[k],indent=2,ensure_ascii=False)+'\n' for k in ('timing','cues','beats','keyframes')}
    outputs[f'{OUT}/data.js']='window.MOTION_DATA = '+json.dumps(data,ensure_ascii=False,sort_keys=True).replace('</','<\\/')+';\n'
    outputs[f'{OUT}/inputs.json']=json.dumps(data['portable_inputs'],indent=2)+'\n'
    from pipeline import Subtitle
    outputs[f'{OUT}/subtitles.srt']=to_srt([Subtitle(**c) for c in data['subtitles']])
    scripts=[]
    for name in ('plan.js','chapters.js','video-frame.mjs','live-terminal.mjs','app.js'):
        text='\n'.join(line for line in (root/OUT/name).read_text().splitlines() if not line.startswith('import ')).replace('export ','')
        scripts.append(text)
    outputs[f'{OUT}/bundle.js']='// Generated by motion_v5.py for offline file rendering.\n'+'\n'.join(scripts)+'\n'
    for name,text in outputs.items():english_only(text,name)
    for p in (root/OUT).iterdir():
        if p.suffix in ('.js','.mjs','.html','.css'):english_only(p.read_text(),str(p))
    return outputs

def prepare(builder,*,require_voice=False):
    if require_voice:
        from record_v5 import check_recordings,RecordingError
        try:check_recordings(builder.story,builder.repo)
        except RecordingError as e:raise BuildError(str(e)) from e
    voices=None
    try:voices=[builder.require_voice(s) for s in builder.scenes]
    except BuildError:
        if require_voice:raise
    data=compile_data(builder.repo,builder.story,voices)
    for name,content in artifacts(data,builder.repo).items():(builder.repo/name).write_text(content)
    return data['timing']

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');mode=parser.add_mutually_exclusive_group();mode.add_argument('--measured',action='store_true');mode.add_argument('--preview',action='store_true',help='Discard obsolete measured metadata for layout only; sync/export refuse previews');args=parser.parse_args()
    if args.measured:
        from build import Builder,parser as build_parser
        builder=Builder(build_parser().parse_args(['keyframes','--storyboard',str(ROOT/'demo/storyboard-v5.yaml')]))
        data=compile_data(ROOT,builder.story,[builder.require_voice(s) for s in builder.scenes])
    else:data=compile_data(preview=args.preview)
    for name,content in artifacts(data).items():
        if args.check:
            if (ROOT/name).read_text()!=content:raise SystemExit(f'{name} stale; compile with the same timing mode')
        else:(ROOT/name).write_text(content)
    print(f"PASS v5: 10 cuts / 178 s; one source per sentence/phrase; English captions <=2 x 42; {data['asset_status']['voice']}")
if __name__=='__main__':main()
