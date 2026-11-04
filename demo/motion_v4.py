#!/usr/bin/env python3
"""Isolated v4 timeline compiler. No writes under motion/v3; no live API imports."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import math
from html.parser import HTMLParser

import yaml

from motion_cues import cue_document, detect_silences, map_sentences, sentence_subtitles, split_phrases
from pipeline import BuildError, Subtitle, subtitle_chunks, file_hash, read_json, to_srt, write_json
from scale_v4 import compile_scale

ROOT=Path(__file__).resolve().parent.parent
OUT='demo/motion/v4'
BOUNDARIES=[0.0,9.0,22.0,34.0,50.0,66.0,124.0,148.0,164.0,178.0]


class HeroSection(HTMLParser):
    """Keep the worktree's exact hero markup, without its navigation or scripts."""
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source=source
        self.offsets=[0]+[i+1 for i,c in enumerate(source) if c=='\n']
        self.depth=0
        self.markup=None
        self.feed(source)

    def source_offset(self):
        line,column=self.getpos()
        return self.offsets[line-1]+column

    def handle_starttag(self, tag, attrs):
        if tag!='section':return
        if self.depth:
            self.depth+=1
        elif dict(attrs).get('id')=='top' and 'hero' in dict(attrs).get('class','').split():
            self.start=self.source_offset()
            self.depth=1

    def handle_endtag(self, tag):
        if tag=='section' and self.depth:
            self.depth-=1
            if not self.depth:
                self.markup=self.source[self.start:self.source.index('>',self.source_offset())+1]


def site_hero(root=ROOT):
    sources=('docs/site/index.html','docs/site/styles.css')
    hero=HeroSection((root/sources[0]).read_text()).markup
    if not hero or '<script' in hero.lower():
        raise BuildError('Current local site needs one script-free #top hero section.')
    css=(root/sources[1]).read_text()
    html=('<!doctype html><html lang="en"><head><meta charset="utf-8">'
          '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
          f'<style>{css}\nhtml,body{{margin:0;height:100%;overflow:hidden;scroll-behavior:auto}}'
          'body{min-width:0}main{margin:0}.hero{min-height:100vh}</style>'
          f'</head><body><main>{hero}</main></body></html>')
    return dict(html=html,sources={p:file_hash(root/p) for p in sources})


def scale_narration(scale):
    median=scale['cohorts'][scale['selected_cohort']]['median_wall_seconds']
    if round(scale['projection']['sequential_hours_at_median'])!=2:
        raise BuildError('Rounded two-hour narration no longer matches the saved projection.')
    return (f'On saved Threads posts, the median was {median:.1f} seconds. '
            'At that median, a thousand posts take about two hours on one worker.')


def validate(story):
    scenes=story['scenes']
    if [s['id'] for s in scenes] != [f'v40{i}' for i in range(1,10)]:
        raise BuildError('v4 requires the nine director scenes v401…v409 in order.')
    if story['motion_variant']!='v4' or story['version']!=2:
        raise BuildError('v4 keeps the storyboard-v3 build.py version 2 motion contract.')
    for i,s in enumerate(scenes):
        if (s['target_start_s'],s['target_end_s'],s['target_s']) != (BOUNDARIES[i],BOUNDARIES[i+1],BOUNDARIES[i+1]-BOUNDARIES[i]):
            raise BuildError(f"{s['id']}: director timing changed")
        if ' '.join(s['narration'].split())!=' '.join(' '.join(s['subtitle_cues']).split()):
            raise BuildError(f"{s['id']}: subtitle cues differ from locked narration")
        if any(len(c.splitlines())>3 or max(map(len,c.splitlines()))>42 for c in s['subtitle_cues']):
            raise BuildError(f"{s['id']}: cue exceeds 3 x 42 characters")
    for s in scenes:
        if s['id'] in ('v406','v409'):
            if bool(s.get('placeholder')) == bool(s.get('recording')):
                raise BuildError('Each live scene requires either a pending placeholder or a retained recording.')
        elif s.get('placeholder') or s.get('recording'):
            raise BuildError('Only beats 6 and 9 accept site recordings.')
    if sum(s['target_s'] for s in scenes)>178 or story['max_total_s']>178:
        raise BuildError('v4 must remain <=178.0 seconds.')


def place_live_voice(scene, mapped, duration, *, measured):
    """Move four intact spans of the new v406 take onto its receipt phase clock."""
    cues, method = mapped
    events = scene['cue_events']
    if ' '.join(e['narration'] for e in events) != scene['narration'] or len(events) != 4:
        raise BuildError('v406 requires four complete narration cue events.')
    if not measured:
        # Source-only captions are a labelled layout preview, with no audio claim.
        placed=[]
        for i,event in enumerate(events):
            onset=event['at_scene_s']
            limit=events[i+1]['at_scene_s'] if i+1<len(events) else scene['target_s']-.3
            estimate=min(len(event['narration'])/14,limit-onset)
            if estimate<=0:raise BuildError('Live receipt cue onsets must increase.')
            placed.extend(map_sentences(event['narration'],estimate,[],offset=onset)[0])
        return (placed,'target preview / four receipt cues'), []
    starts, index = [], 0
    for event in events:
        starts.append(cues[index]['start'])
        # map_sentences already splits these exact sentences, including decimals.
        count = len(split_phrases(event['narration']))
        if ' '.join(c['text'] for c in cues[index:index+count]) != event['narration']:
            raise BuildError('v406 voice spans differ from the four narration cues.')
        index += count
    starts[0] = 0  # Keep leading silence as well as every recorded speech sample.
    ends = starts[1:] + [duration]
    placed, segments = [], []
    for i,(event,a,b) in enumerate(zip(events,starts,ends)):
        onset = event['at_scene_s']
        limit = events[i+1]['at_scene_s'] if i+1 < len(events) else scene['target_s']-.3
        if onset+b-a > limit+1e-8:
            raise BuildError(f"v406 {event['event']}: voice span {b-a:.3f}s exceeds its {limit-onset:.3f}s cue budget. "
                             'Retain the host take; exact receipt onsets prohibit overlap, truncation or faster speech.')
        segments.append(dict(source_start_s=a,source_end_s=b,at_s=scene['target_start_s']+onset,
                             event=event['event']))
        count = len(split_phrases(event['narration']))
        # Source cues and audio use the same piecewise translation.
        group = cues[sum(len(split_phrases(e['narration'])) for e in events[:i]):][:count]
        placed.extend({**c,'start':c['start']-a+onset,'end':c['end']-a+onset} for c in group)
    return (placed,method+' / four receipt-placed spans'), segments


def merge_caption_fragments(captions):
    """Reflow the preceding line with the two short orphans, preserving 2×42."""
    result=[]
    for caption in captions:
        if caption.text in ('November 4.','run.') and result:
            previous=result.pop()
            lines=previous.text.splitlines()
            if len(lines)==2:
                split=previous.start+(previous.end-previous.start)*len(lines[0])/len(previous.text)
                result.append(Subtitle(previous.start,split,lines[0]))
                text=lines[1]+' '+caption.text
                start=split
            else:
                text=previous.text+' '+caption.text
                start=previous.start
            chunks=subtitle_chunks(text)
            if len(chunks)!=1:raise BuildError('Orphan merge exceeds 2×42 characters.')
            result.append(Subtitle(start,caption.end,chunks[0]))
        else:result.append(caption)
    return result


def compile_data(root=ROOT, story=None, voices=None):
    story=copy.deepcopy(story or yaml.safe_load((root/'demo/storyboard-v4.yaml').read_text()))
    validate(story)
    from record_v4 import check_recordings, RecordingError
    try:
        check_recordings(story, root, required=False)
    except RecordingError as error:
        raise BuildError(str(error)) from error
    live=story['scenes'][5]
    live_receipt={'timings':live.get('recording',{}).get('timings',[])}
    if live.get('recording'):
        receipt_path=root/live['recording']['receipt']
        if receipt_path.is_file():
            from record_v4 import live_cue_events
            live_receipt=read_json(receipt_path)
            resolved=live_cue_events(live,live_receipt)
            if resolved!=live['cue_events']:
                raise BuildError('v406 cue times are stale for the wired receipt; rewire the recording.')
    scale=read_json(root/'demo/data/scale-v4.json')
    if scale!=compile_scale(root):
        raise BuildError('scale-v4.json is stale; rebuild it before motion preparation.')
    if scale_narration(scale) not in story['scenes'][6]['narration']:
        raise BuildError('Beat 7 narration no longer matches the measured scale evidence.')
    baseline=yaml.safe_load((root/'demo/storyboard-v3.yaml').read_text())
    if story['voice']!=baseline['voice'] or story['music']!=baseline['music']:
        raise BuildError('The v3 voice/music lock changed.')
    shots,local,analysis=[],{},{}
    for i,s in enumerate(story['scenes']):
        duration=voices[i]['voice_s'] if voices else s['target_s']-story['pad_s']
        if not math.isfinite(duration) or duration<=0 or duration+story['pad_s']>s['target_s']+1e-8:
            raise BuildError(f"{s['id']}: measured voice {duration:.3f}s plus pad exceeds locked {s['target_s']:.3f}s. "
                             'Retain the take; director must resolve the overrun. Speech is never sped up or cut.')
        shot=dict(id=s['id'],start=s['target_start_s'],end=s['target_end_s'],
                  voice_start=s['target_start_s'],voice_end=s['target_start_s']+duration)
        silences=[]
        if voices:
            shot['voice_s']=duration
            audio=Path(voices[i]['artifacts']['audio']['path'])
            silences=detect_silences(audio,duration,root/'demo/cache/cues'/f"v4-{s['id']}-{file_hash(audio)}.log")
            analysis[s['id']]=dict(audio_sha256=file_hash(audio),voice_key=voices[i]['key'])
        else:
            analysis[s['id']]=dict(source='target preview; narration not synthesized or measured')
        local[s['id']]=map_sentences(s['narration'],duration,silences)
        if s['id']=='v406':
            local[s['id']],segments=place_live_voice(s,local[s['id']],duration,measured=bool(voices))
            if voices:
                shot['voice_segments']=segments
                shot['voice_end']=max(e['at_s']+e['source_end_s']-e['source_start_s'] for e in segments)
            else:
                shot['voice_end']=s['target_start_s']+local[s['id']][0][-1]['end']
        shots.append(shot)
    config=story['music'];grid=read_json(root/config['beats'])
    beats=[round(t-config['music_offset_s'],9) for t in grid['beats_s'] if t>=config['music_offset_s']]
    timing=dict(source='measured voice / director cuts' if voices else 'director targets; narration unmeasured',
        version=2,duration=178.,shots=shots,music_offset_s=config['music_offset_s'],
        cut_rule='Fixed director boundaries; do not snap cuts to beats, trim or accelerate speech.',
        placeholders=['v406','v409'])
    cues=cue_document(story['scenes'],timing,local,analysis,beats)
    subtitles=merge_caption_fragments(sentence_subtitles(story['scenes'],timing,cues))
    # Build a complete claim record from the frozen reference and original results.
    from replay_v4 import comparison
    sources={};list(comparison(sources))
    eval_rows=[read_json(p) for p in sorted((root/'docs/evidence/eval-v2-2026-10-27').glob('*--agent@baseten.json'))]
    heldout=[r for r in eval_rows if r['split']=='test']
    gold={r['id']:r['gold_verdict'] for r in map(json.loads,(root/'eval/v2/claims-v2-corrected.jsonl').read_text().splitlines())}
    negative=[r for r in heldout if gold[r['id']]!='supported']
    false_support=sum(r['status']=='completed' and r['verdict']=='supported' for r in negative)
    costs=[r['cost_usd'] for r in heldout if r['status']=='completed']
    correct=sum(r['status']=='completed' and r['verdict']==gold[r['id']] for r in heldout)
    metrics=dict(heldout_correct=correct,heldout_n=len(heldout),false_support=false_support,negative_n=len(negative),
                 mean_cost_usd=sum(costs)/len(costs),median_claim_seconds=scale['eval_v2']['median_completed_latency_seconds'])
    product=read_json(root/'demo/data/demo-thread.json')
    from phone_v4 import ASSET, SOURCE, svg
    if (root/ASSET).read_text()!=svg(root):
        raise BuildError('Saved post still is stale; run demo/phone_v4.py')
    phone_post=dict(path=ASSET,sha256=file_hash(root/ASSET),source=SOURCE)
    inputs=[]
    for ext,label in [('webp','Screenshot · Muse OCR'),('pdf','PDF · native text'),('wav','Podcast · Muse Voice'),('mp4','Video · sampled frames + ASR')]:
        p=f'eval/multimodal-v1/inputs/{"META" if ext=="webp" else "MSFT"}/input.{ext}'
        item=dict(label=label,path=p,sha256=file_hash(root/p))
        if ext=='wav':
            import wave
            import array
            with wave.open(str(root/p)) as wav:
                if wav.getsampwidth()!=2:raise BuildError('Waveform expects the retained PCM16 fixture.')
                samples=array.array('h',wav.readframes(wav.getnframes()))
                chunk=max(1,len(samples)//75)
                peaks=[max(map(abs,samples[i*chunk:(i+1)*chunk]),default=0) for i in range(75)]
                item['waveform']=[round(v/max(peaks),5) for v in peaks]
        inputs.append(item)
    evidence=set(sources)
    for s in story['scenes']:evidence.update(s['evidence'])
    evidence.update(i['path'] for i in inputs)
    evidence.add('demo/assets/architecture-v4.svg')
    evidence.update((ASSET,SOURCE))
    hero=site_hero(root)
    evidence.update(hero['sources'])
    provenance={p:file_hash(root/p) for p in sorted(evidence)}
    keyframes=[dict(t=s['start']+min(2.,(s['end']-s['start'])/2),shot=s['id']) for s in shots]
    keyframes.extend([dict(t=BOUNDARIES[4]+t,shot='v405') for t in (0,3,6,9,12,14)])
    keyframes.extend(dict(t=t,shot=shot) for shot,times in (
        ('v401',(0,)),('v402',(9,17)),
        ('v406',tuple(BOUNDARIES[5]+t for t in (17,21,25,49))),
        ('v409',(BOUNDARIES[8],BOUNDARIES[9]-1/30)),
    ) for t in times)
    keyframes.extend(dict(t=66+e['at_s']+.3,shot='v406') for e in live_receipt['timings']
                     if e['phase'].endswith('_reveal') and 0<=e['at_s']<57.7)
    return dict(timing=timing,cues=cues,beats=dict(beats_s=beats,music_offset_s=config['music_offset_s']),
        scenes=story['scenes'],keyframes=sorted(keyframes,key=lambda f:f['t']),
        subtitles=[dict(start=c.start,end=c.end,text=c.text) for c in subtitles],
        architecture_svg=(root/'demo/assets/architecture-v4.svg').read_text(),
        product=product,phone_post=phone_post,hero=hero,metrics=metrics,inputs=inputs,provenance=provenance,
        scale=dict(median=scale['cohorts'][scale['selected_cohort']]['median_wall_seconds'],
                   hours=scale['projection']['sequential_hours_at_median']),
        asset_status=dict(site_footage='recorded r5 live takes' if all(s.get('recording',{}).get('capture_version')==5
                          for s in story['scenes'] if s['id'] in ('v406','v409')) else
                          'host r5 re-record required; prior takes retained',
                          terminal='real PTY recordings · 56px labels / 96px principal lines',broll='disabled'))


def artifacts(data, root=ROOT):
    result={f'{OUT}/{name}.json':json.dumps(data[name],indent=2,ensure_ascii=False)+'\n'
            for name in ('timing','cues','beats','keyframes')}
    result[f'{OUT}/data.js']='window.MOTION_DATA = '+json.dumps(data,ensure_ascii=False,sort_keys=True)+';\n'
    from pipeline import Subtitle
    result[f'{OUT}/subtitles.srt']=to_srt([Subtitle(**c) for c in data['subtitles']])
    # The offline renderer opens file://, which needs a classic-script entry.
    plan=(root/OUT/'plan.js').read_text().replace('export ','')
    app=(root/OUT/'app.js').read_text().split('\n',1)[1]
    result[f'{OUT}/bundle.js']='// Generated by motion_v4.py from plan.js + app.js for file:// rendering.\n'+plan+'\n'+app
    return result


def prepare(builder, *, require_voice=False):
    if require_voice:
        from record_v4 import check_recordings, RecordingError
        try:
            check_recordings(builder.story, builder.repo)
        except RecordingError as error:
            raise BuildError(str(error)) from error
    voices=None
    try:
        voices=[builder.require_voice(s) for s in builder.scenes]
    except BuildError:
        if require_voice:raise
    data=compile_data(builder.repo,builder.story,voices)
    for relative,content in artifacts(data,builder.repo).items():
        path=builder.repo/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    return data['timing']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    data=compile_data();outputs=artifacts(data)
    if args.check:
        for relative,content in outputs.items():
            if (ROOT/relative).read_text()!=content:
                raise SystemExit(f'{relative} is stale; run demo/motion_v4.py')
    else:
        for relative,content in outputs.items():
            path=ROOT/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    print('PASS v4: nine locked beats, 178.000 s, bounded cues, source hashes, live-take validation')
    print('Target preview only; measured voice timing is prepared separately on the host.')


if __name__=='__main__':main()
