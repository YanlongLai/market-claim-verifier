#!/usr/bin/env python3
"""Prepare the sentence sync ledger from measured cues and actual review PNGs.

This records evidence for review; it never declares picture/speech acceptance.
Intra-unit phrase boundaries remain proportional estimates until a reviewer listens.
"""
import argparse,json
from pathlib import Path
from motion_v5 import ROOT
from pipeline import BuildError,file_hash

VISUALS={
 'v500':'DappGo, Market Claim Verifier and the complete build disclosure',
 'v501':'The original earnings post and its HTML cascade; wrong-period headline',
 'v502':'The four real Screenshot, PDF, Audio and Video previews',
 'v503':{'single':'Single-shot result: 74/357 (20.7%)',
         'agent':'Same model with SEC tools and program verdict: 323/357 (90.5%)',
         'heldout':'Held-out text result: 240/266 (90.2%)'},
 'v504':{'model':'Muse Spark node, claim extraction and SEC lookup path',
         'program':'Python arithmetic and verdict nodes',
         'principle':'Model proposes; program decides.'},
 'v505':{'paste':'The real English post in the centred live workspace',
         'tools':'A real in-progress check against SEC; live status visible',
         'verdict':'The native CONTRADICTED verdict',
         'draft':'The native corrected draft; $416.2B to $102.5B overlay',
         'evidence':'The native SEC filing evidence; annual minus nine-month equation',
         'trace':'Expanded native agent trace; four actual tool calls, model and program verdict',
         'receipt':'The actual native receipt; measured cost and elapsed time'},
 'v506':{'run':'Saved CoreWeave T03 excerpt: SUPPORTED / CONTRADICTED $51.31B to $5.131B / CONTRADICTED',
         'ocr':'Saved Muse OCR terminal block',
         'asr':'Saved Muse Voice Transcribe terminal block',
         'median':'Measured 6.8-second saved Threads-post median',
         'projection':'Sequential 1,000-post projection, about two hours on one worker'},
 'v507':'The four sourced results: 90.2%, 1/139, $0.02 and 10 seconds',
 'v508':'The corrected result and both native SEC component filing links, continuously held',
 'v509':'Site robot stamp motion, hackathon.dappgo.com, Meta Muse Spark, Baseten and the DappGo wordmark',
}

def ledger_rows(timing,cues,index):
    rows=[]
    def frame(shot,t):
        matches=[f for f in index if f['shot']==shot and abs(f['t']-t)<1e-7]
        if not matches:raise BuildError(f'Missing sentence review frame: {shot} at {t:.9f}')
        return matches[0]['captioned_file']
    for shot in timing['shots']:
        sid=shot['id'];events=cues['_events'][sid]
        for i,phrase in enumerate(cues[sid]):
            event=next((e for e in events if e['cue_start']-1e-7<=phrase['start']<e['cue_end']),None)
            visual=VISUALS[sid]
            if isinstance(visual,dict):
                if not event:raise BuildError(f'Missing visual binding: {sid} phrase {i+1}')
                visual=visual[event['event']]
            end=max(phrase['start'],phrase['end']-1/30)
            rows.append(dict(id=f'{sid}-{i+1:02}',scene=sid,sentence=phrase['text'],
                cue_start_s=phrase['start'],cue_end_s=phrase['end'],cue_unit=event['event'] if event else None,
                required_visual=visual,onset_frame=frame(sid,phrase['start']),end_frame=frame(sid,end),
                verified_frame=None,actual_sentence_start_s=None,actual_sentence_end_s=None,
                visual_visible_from_s=None,visual_visible_until_s=None,status='pending',reviewer=None))
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames',type=Path,default=ROOT/'demo/out/review-v5')
    args=parser.parse_args();folder=ROOT/'demo/motion/v5'
    timing=json.loads((folder/'timing.json').read_text());cues=json.loads((folder/'cues.json').read_text())
    if any('preview' in m for m in cues['_methods'].values()):
        raise BuildError('Synthesize changed cues and compile --measured before making the sync ledger')
    index=json.loads((args.frames/'index.json').read_text());rows=ledger_rows(timing,cues,index)
    for row in rows:
        for field in ('onset_frame','end_frame'):
            row[field+'_sha256']=file_hash(args.frames/row[field])
    out=args.frames/'sync-ledger.json'
    if out.exists():raise BuildError('Retain the prior sync ledger before regenerating; review entries are never overwritten')
    report=dict(status='pending human listening and full-duration picture review',
        timing_note='Cue units use measured WAV durations and live receipt phases. Intra-unit sentence/phrase boundaries are proportional estimates, not forced alignment. Correct actual_sentence_start_s/end_s from the rendered MP4.',
        acceptance='Every sentence referent must remain visible throughout actual speech; picture may lead speech by at most 0.5 s and must never follow it. Supply verified_frame, actual times, visual visibility interval, reviewer and pass/blocker status for every row. Inspect silent holds too.',
        inputs={name:file_hash(folder/name) for name in ('timing.json','cues.json','data.js')},
        review_index_sha256=file_hash(args.frames/'index.json'),rows=rows)
    out.write_text(json.dumps(report,indent=2)+'\n')
    lines=['# V5 sentence sync ledger','',report['timing_note'],'',report['acceptance'],'',
        '| Sentence / cue phrase | Cue start–end (s) | Required visual | Review frames | Verified frame |',
        '| --- | --- | --- | --- | --- |']
    for row in rows:
        lines.append(f"| {row['id']}: {row['sentence']} | {row['cue_start_s']:.3f}–{row['cue_end_s']:.3f} | {row['required_visual']} | [start]({row['onset_frame']}) · [end]({row['end_frame']}) | Pending |")
    out.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(f'Sync ledger: {len(rows)} sentence/phrase rows; every row requires actual-film verification: {out}')

if __name__=='__main__':main()
