#!/usr/bin/env python3
"""Build a ledger only from independently measured sentence units and frame audits.

Acoustic PCM bounds and real-frame checks do not replace final film listening.
"""
import argparse,json
from pathlib import Path
from motion_v5 import ROOT
from pipeline import BuildError,file_hash

VISUALS={
 'v500':{'disclosure_origin':'Complete DappGo / Market Claim Verifier title and origin disclosure','disclosure_build':'Complete October 27–November 4 build disclosure'},
 'v501':{'post':'Original earnings post, labelled Illustrative post','reposts':'Repost cascade inside the left 55% of the frame','question':'Is it right? headline','period':'Apple highlight band and enlarged $416.2 billion … fiscal Q4 2025 excerpt','stakes':'Numbers move money headline and held Apple focus'},
 'v502':{'formats':'All four real Screenshot, PDF, Audio and Video previews','screenshot':'Lit Screenshot tile','pdf':'Lit PDF tile','podcast':'Lit Audio tile','video':'Lit Video tile','question':'New How do you check all of them? headline'},
 'v503':{'single':'Single-shot result: 74/357 (20.7%)',
         'agent':'SEC tools + Python verdict heading; 357 claims · corrected gold · includes dev qualifier',
         'nine':'All-claim 323/357 · 90.5% (includes dev)',
         'heldout':'Held-out text result: 240/266 (90.2%)'},
 'v504':{'model':'Muse Spark node, claim extraction and SEC lookup path',
         'program':'Python arithmetic and verdict nodes',
         'principle':'Model proposes; program decides.'},
 'v505':{'live':'Centred native Try workspace', 'paste':'The real English post in the centred live workspace',
         'tools':'Terminal window: receipt-bound command, trace and clock; native in-progress SEC status clear above it',
         'claims':'Terminal window: recorded tool calls; native in-progress SEC status clear above it',
         'lookups':'Terminal window: recorded SEC calls and their evidence IDs; native status clear above it',
         'evidence_ids':'Terminal window: receipt-bound evidence IDs on filed-number rows; native status clear above it',
         'thinking':'Terminal window: running stopwatch and Muse Spark reasoning line; native status clear above it',
         'decide':'Terminal window: model clock and recorded trace held through the last word; native status clear above it',
         'verdict':'The native CONTRADICTED verdict + Apple SEC E3 component filings: 10-K fiscal 2025 annual; 10-Q nine months to 28 Jun 2025 (form and period, receipt-bound citations)',
         'draft':'The native corrected draft; $416.2B to $102.5B overlay',
         'evidence':'The native SEC filing evidence; annual minus nine-month equation',
         'trace':'First native SEC tool-call row', 'each':'Native tool-call walk', 'program':'Native program-verdict row',
         'receipt':'The actual native receipt; measured cost and elapsed time'},
 'v506':{'run':'Real local CLI session, recorded 2026-11-04; command, timestamped progress and final receipt; labelled replay speed',
         'ocr':'Saved Muse OCR terminal block',
         'asr':'Saved Muse Voice Transcribe terminal block',
         'median':'Measured 6.8-second saved Threads-post median',
         'projection':'Sequential 1,000-post projection, about two hours on one worker'},
 'v507':{'accuracy':'Lit 90.2% held-out result','false_support':'Lit 1/139 non-supported claims wrongly supported tile','cost_time':'Lit $0.02 and 10 s tiles','coverage':'New coverage ≠ accuracy line'},
 'v508':{'filing':'Native corrected edit, Cited changes title and both SEC component filing links, continuously held','url':'New hackathon.dappgo.com URL with the native correction still held'},
 'v509':{'credit':'Built with Meta Muse Spark · Baseten credit','wordmark':'New DappGo wordmark and robot stamp motion, followed by completed imprint'},
}

def ledger_rows(timing,cues,index):
    if any(m!='measured PCM speech bounds per sentence/phrase' for m in cues['_methods'].values()):
        raise BuildError('Every row requires a measured sentence onset; preview or inferred timing is forbidden')
    rows=[]
    def frame(shot,t,event):
        matches=[f for f in index if f['shot']==shot and abs(f['t']-t)<1e-7]
        if not matches:raise BuildError(f'Missing sentence review frame: {shot} at {t:.9f}')
        f=matches[0]
        checks=[c for c in f.get('frame_audit',[]) if c.get('scene')==shot and c.get('event')==event and abs(c.get('at_s',-1)-t)<1e-6]
        if len(checks)!=1 or checks[0].get('status')!='pass' or not checks[0].get('measured') or not checks[0].get('elements'):
            raise BuildError(f'Missing actual-frame named-element audit: {shot}/{event} at {t:.9f}')
        if shot=='v505' and event=='verdict' and (checks[0].get('referents')!=['verdict','filing']
            or {c.get('form') for c in checks[0].get('filings',[])}!={'10-K','10-Q'}):
            raise BuildError('Verdict sentence frame audit must name both verdict and filing referents')
        if shot=='v505' and event in ('tools','claims','lookups','evidence_ids','thinking','decide') and (
            checks[0].get('referents')!=['terminal window','native in-progress SEC status']
            or not checks[0].get('native',{}).get('elements')
            or not any(e.get('name')=='.live-terminal' for e in checks[0]['elements'])):
            raise BuildError('Live wait sentence frame audit must name the terminal window and clear native status')
        return f['captioned_file'],checks[0]
    for shot in timing['shots']:
        sid=shot['id'];events=cues['_events'][sid]
        for i,phrase in enumerate(cues[sid]):
            event=next((e for e in events if e['event']==phrase.get('event')),None)
            if (not phrase.get('measured') or not event or not event.get('measured')
                or event.get('alignment')!='measured PCM speech bounds'
                or phrase.get('measurement',{}).get('method')!='measured PCM speech bounds'
                or phrase['start']!=event['cue_start'] or phrase['end']!=event['cue_end']):
                raise BuildError(f'{sid} phrase {i+1}: measured sentence onset required; no inferred internal timing is accepted')
            lead=phrase['start']-event['picture_start']
            if not .1-1e-7<=lead<=.3+1e-7:raise BuildError('Sentence picture must arrive 0.1–0.3 s before measured speech')
            visual=VISUALS[sid]
            if isinstance(visual,dict):
                if not event:raise BuildError(f'Missing visual binding: {sid} phrase {i+1}')
                visual=visual[event['event']]
            end=max(phrase['start'],phrase['end']-1/30)
            onset_frame,onset_audit=frame(sid,phrase['start'],event['event'])
            end_frame,end_audit=frame(sid,end,event['event'])
            rows.append(dict(id=f'{sid}-{i+1:02}',scene=sid,sentence=phrase['text'],
                cue_start_s=phrase['start'],cue_end_s=phrase['end'],cue_unit=event['event'] if event else None,
                required_visual=visual,onset_frame=onset_frame,end_frame=end_frame,
                measured_onset=True,measurement=phrase['measurement'],planned_picture_from_s=event['picture_start'],
                automated_frame_audit=dict(status='pass',onset=onset_audit,end=end_audit),
                verified_frame=None,actual_sentence_start_s=phrase['start'],actual_sentence_end_s=phrase['end'],
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
        timing_note='Every row has one independent PCM WAV, measured acoustic onset/end and source hash. Pictures lead measured speech by 0.2 s. Actual Chromium onset/end frames passed named-element visibility and clearance; native proof uses capture rectangles over a recorded stationary interval. Final listening and continuous-picture review remain pending.',
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
    print(f'Sync ledger: {len(rows)} measured sentence/phrase rows; onset/end frame audits pass; final film review pending: {out}')

if __name__=='__main__':main()
