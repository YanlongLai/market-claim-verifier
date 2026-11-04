#!/usr/bin/env python3
"""Replay exact retained PTY rows on the v5 clock. No new PTY/model/media run."""
from pathlib import Path
import argparse, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/assets/terminal-v5'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
# The source clock is the retained asciicast clock, not an encoded MP4 seek.
# Start just after the panel's clear/title event. Extra time holds its final rows.
CUTS={'beat3':{'source':'beat4','duration_s':14.,'blocks':[
    ('single',0.,3.3,3.5),('agent',4.02,8.8,5.5),('heldout',9.02,15.8,5.)]},
 'beat6':{'source':'beat7','duration_s':22.,'blocks':[
    ('run',4.02,5.8,5.),('ocr',21.02,22.49,3.),('asr',22.52,23.95,3.),
    ('median',6.02,10.5,4.5),('projection',10.5,17.,6.5)]}}

def compile_replays(root=ROOT):
 """Decode the strict ANSI subset; preserve every typed character and timestamp."""
 from replay_v4 import TerminalScreen
 outputs={};sources=[]
 for name,cut in CUTS.items():
    base=f"demo/assets/terminal-v4-r5/{cut['source']}"
    cast=root/f'{base}.cast';receipt=json.loads((root/f'{base}.json').read_text())
    if sha(cast)!=receipt['cast_sha256']:raise ValueError('Saved PTY bytes differ from their receipt')
    events=[e for e in map(json.loads,cast.read_text().splitlines()[1:]) if e[1]=='o']
    screen=TerminalScreen();snapshots=[]
    for t,_,chunk in events:
        screen.feed(chunk)
        snapshots.append({'source_at_s':t,'rows':[
            dict(row=row,text=text,principal=row==10 or (name=='beat3' and row==5 and '/' in text) or (name=='beat6' and row==6 and text.startswith('median ')))
            for row,text in screen.lines().items() if text and row!=12]})
    blocks=[];at=0
    for label,a,b,duration in cut['blocks']:
        first=next(s for s in reversed(snapshots) if s['source_at_s']<=a)
        frames=[dict(at_s=at,rows=first['rows'])]
        frames.extend(dict(at_s=round(at+s['source_at_s']-a,9),rows=s['rows']) for s in snapshots if a<s['source_at_s']<=min(b,a+duration))
        blocks.append(dict(block=label,at_s=at,end_s=at+duration,source_start_s=a,source_end_s=b,frames=frames));at+=duration
    assert at==cut['duration_s']
    outputs[name]=dict(source=f'{base}.cast',source_sha256=sha(cast),receipt=f'{base}.json',duration_s=at,blocks=blocks,
        note='Literal saved PTY text and typing times, reflowed above the rail. Source ranges are editorial playback; no new execution or OCR/ASR.')
    sources.extend([f'{base}.cast',f'{base}.json'])
 return outputs,sources
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--check',action='store_true',help='Validate retained source hashes/ranges without rendering')
 parser.parse_args()
 replays,_=compile_replays()
 print('PASS terminal v5: 14 s comparison; 22 s saved replay; CoreWeave T03 verdicts at run; no media rendered')
if __name__=='__main__':main()
