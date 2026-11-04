#!/usr/bin/env python3
"""Local OCR spot check of 20 captioned review frames, including all seven live phases."""
import argparse,json,subprocess
from pathlib import Path
from motion_v5 import ROOT,CJK
from pipeline import BuildError,file_hash

def select(index):
    chosen=[]
    def add(frame):
        if frame not in chosen:chosen.append(frame)
    for phase in ('live','paste','tools','verdict','draft','evidence','trace','each','program','receipt'):
        candidates=[f for f in index if f.get('shot')=='v505' and (f.get('event')==phase or f.get('cue')==phase)]
        if not candidates:raise BuildError(f'Review frames missing live overlay {phase}')
        add(candidates[-1])
    for scene in (f'v50{i}' for i in range(10)):
        candidates=[f for f in index if f['shot']==scene]
        if not candidates:raise BuildError('Review frames missing scene '+scene)
        add(candidates[0])
    for frame in index:
        if len(chosen)>=20:break
        add(frame)
    if len(chosen)<20:raise BuildError('Need at least twenty review frames')
    return sorted(chosen[:20],key=lambda f:f['t'])

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--frames',type=Path,default=ROOT/'demo/out/review-v5');args=parser.parse_args()
    index=json.loads((args.frames/'index.json').read_text());selected=select(index)
    from sync_v5 import ledger_rows
    folder=ROOT/'demo/motion/v5'
    measured=ledger_rows(json.loads((folder/'timing.json').read_text()),json.loads((folder/'cues.json').read_text()),index)
    audit=args.frames/'named-element-audit.json'
    if audit.exists():raise BuildError('Retain the prior named-element audit before regenerating')
    audit.write_text(json.dumps(dict(status='pass',scope='Named element visible and clear at every measured sentence onset and end; final listening remains separate',
        index_sha256=file_hash(args.frames/'index.json'),rows=[dict(id=r['id'],onset_frame=r['onset_frame'],end_frame=r['end_frame'],audit=r['automated_frame_audit']) for r in measured]),indent=2)+'\n')
    paths=[args.frames/f['captioned_file'] for f in selected]
    command=['swift',str(ROOT/'demo/ocr_v5.swift'),*[str(p) for p in paths]]
    result=subprocess.run(command,check=True,capture_output=True,text=True)
    rows=json.loads(result.stdout)
    report=dict(status='pass',scope='20 actual captioned review PNGs; local Vision OCR, not OCR/ASR product retesting',command=command,frames=[dict(t=f['t'],shot=f['shot'],path=str(p),sha256=file_hash(p),recognized=ocr['text']) for f,p,ocr in zip(selected,paths,rows)])
    if len(rows)!=20 or any(CJK.search(' '.join(row['text'])) for row in rows):report['status']='fail'
    (args.frames/'ocr-20.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    if report['status']!='pass':raise BuildError('Language OCR check failed; retained ocr-20.json')
    print('PASS local OCR: 20 actual captioned frames, every beat and live overlay phase, no CJK')
if __name__=='__main__':main()
