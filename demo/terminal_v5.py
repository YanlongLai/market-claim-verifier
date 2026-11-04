#!/usr/bin/env python3
"""Re-cut retained r5 terminal footage to the v5 narration blocks. No new PTY/model run."""
from pathlib import Path
import argparse, hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/assets/terminal-v5'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
# Each source range includes the real typed key line. Extra time is a last-frame hold.
CUTS={'beat3':{'source':'beat4','duration_s':14.,'blocks':[
    ('single',0.,3.3,3.5),('agent',4.,8.8,5.5),('heldout',9.,15.8,5.)]},
 'beat6':{'source':'beat7','duration_s':22.,'blocks':[
    ('post',0.,.9,.9),('claims',1.,2.,1.),('calls',2.5,3.8,1.3),('verdicts',4.,5.8,1.8),
    ('ocr',21.,22.5,3.),('asr',22.5,23.95,3.),
    ('median',6.,10.5,4.5),('projection',10.5,17.,6.5)]}}
def build():
 OUT.mkdir(parents=True,exist_ok=True)
 for name,cut in CUTS.items():
    src=ROOT/f"demo/assets/terminal-v4-r5/{cut['source']}.mp4";target=OUT/f'{name}.mp4';receipt=OUT/f'{name}.json'
    source_hash=sha(src)
    if target.exists():
        if not receipt.is_file():raise SystemExit('Unreceipted terminal output exists; retain it before rebuilding.')
        prior=json.loads(receipt.read_text())
        if prior['source_sha256']==source_hash and prior['cuts']==[list(x) for x in cut['blocks']] and prior['sha256']==sha(target):continue
        raise SystemExit('Terminal output differs; retain this revision before rebuilding.')
    filters=[];blocks=[];at=0
    for i,(label,a,b,duration) in enumerate(cut['blocks']):
        filters.append(f'[0:v]trim=start={a}:end={min(b,a+duration)},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},fps=30[v{i}]')
        blocks.append(dict(block=label,at_s=round(at,6),end_s=round(at+duration,6),source_start_s=a,source_end_s=min(b,a+duration),freeze_padding_s=max(0,duration-(b-a))));at+=duration
    assert round(at,6)==cut['duration_s']
    filters.append(''.join(f'[v{i}]' for i in range(len(blocks)))+f'concat=n={len(blocks)}:v=1:a=0[out]')
    command=['ffmpeg','-v','error','-n','-i',str(src),'-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(target)]
    subprocess.run(command,check=True,capture_output=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(target)]))['streams'][0]
    assert [probe['width'],probe['height']]==[1920,1080] and probe['r_frame_rate']=='30/1'
    assert int(probe['nb_frames'])==int(cut['duration_s']*30)
    receipt.write_text(json.dumps(dict(source=src.relative_to(ROOT).as_posix(),source_sha256=source_hash,path=target.relative_to(ROOT).as_posix(),sha256=sha(target),duration_s=cut['duration_s'],cuts=cut['blocks'],blocks=blocks,command=command,note='Re-cut of saved evidence playback; literal retained terminal pixels. No new OCR/ASR, inference or batch run.'),indent=2)+'\n')
 print('PASS terminal v5: 14 s comparison, 22 s sentence-bound batch; source takes untouched')
if __name__=='__main__':build()
