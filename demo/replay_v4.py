#!/usr/bin/env python3
"""Real-shell PTY/asciicast recordings of saved evidence; no inference or SEC access."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import shlex
import struct
import subprocess
import sys
import termios
import textwrap
import time

ROOT=Path(__file__).resolve().parent.parent
EVAL='docs/evidence/eval-v2-2026-10-27'
FAIR='docs/evidence/fair-multimodal-v1'
THREADS='docs/evidence/real-world-2026-11-02/threads'
OUT=ROOT/'demo/assets/terminal-v4'


def read(path, sources):
    raw=(ROOT/path).read_bytes()
    sources[path]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def comparison(sources):
    gold={r['id']:r for r in map(json.loads,(ROOT/'eval/v2/claims-v2-corrected.jsonl').read_text().splitlines())}
    sources['eval/v2/claims-v2-corrected.jsonl']=hashlib.sha256((ROOT/'eval/v2/claims-v2-corrected.jsonl').read_bytes()).hexdigest()
    stats={}
    for method in ('single_shot','agent'):
        rows=[read(p.relative_to(ROOT).as_posix(),sources)
              for p in sorted((ROOT/EVAL).glob(f'*--{method}@baseten.json'))]
        assert len(rows)==357
        good=lambda r:r['status']=='completed' and r['verdict']==gold[r['id']]['gold_verdict']
        test=[r for r in rows if r['split']=='test']
        stats[method]=dict(correct=sum(map(good,rows)),n=len(rows),
            test_correct=sum(map(good,test)),test_n=len(test))
    single,agent=stats['single_shot'],stats['agent']
    yield 'SAME MODEL / NO TOOLS',[
        'RECORDED 2026-10-27 (America/Los_Angeles) | Baseten Muse Spark Open',
        '', 'Same 357 claims. Corrected reference labels. Failures count as wrong.',
        'Full set includes development claims; it is not all held out.', '',
        'SYSTEM                        CORRECT          ACCURACY',
        f"single-shot / no tools         {single['correct']}/{single['n']}           {100*single['correct']/single['n']:.1f}%",
        '', 'Reading saved per-claim JSON, not executing the model.',
        'Source: docs/evidence/eval-v2-2026-10-27/*--single_shot@baseten.json']
    yield 'SEC TOOLS + PYTHON VERDICT',[
        'RECORDED 2026-10-27 (America/Los_Angeles) | Same Baseten model',
        '', 'SYSTEM                        CORRECT          ACCURACY',
        f"single-shot / no tools         {single['correct']}/{single['n']}           {100*single['correct']/single['n']:.1f}%",
        f"agent / SEC + Python          {agent['correct']}/{agent['n']}           {100*agent['correct']/agent['n']:.1f}%",
        '', 'All 357: includes dev claims and corrected gold.', '',
        f"HELD-OUT ONLY                 {agent['test_correct']}/{agent['test_n']}          {100*agent['test_correct']/agent['test_n']:.1f}%",
        '', 'Source: docs/evidence/eval-v2-2026-10-27/',
        'Reference: eval/v2/claims-v2-corrected.jsonl',
        'Saved workflow comparison; not a hosting-only causal experiment.']


def scale_pages(sources):
    folder=f'{THREADS}/baseten/post/T03'
    report=read(folder+'/report.json',sources)
    result=read(folder+'/result.json',sources)
    claims=report['claims']
    lines=[f"Recorded post T03 | {result['started_at']}",
           f"extract -> {report['proposed_count']} proposed claims | Muse Spark Open",
           'Recorded model-selected tool calls (arguments read from raw traces):','']
    for c in claims:
        if c.get('trace_path'):
            trace=read(folder+'/'+c['trace_path'],sources)
            for tool in trace['tool_calls'][:2]:
                args=', '.join(f'{k}={v}' for k,v in tool['arguments'].items())
                lines.extend(textwrap.wrap(f"{tool['name']}({args})",90))
    yield 'BATCH / EXTRACT -> TOOLS',lines[:17]+['','Saved trace stream; playback timing is editorial, not runtime.']
    scale=read('demo/data/scale-v4.json',sources)
    g=scale['cohorts'][scale['selected_cohort']]
    lines=['T03 | PROGRAM VERDICT TABLE (all extracted claims)',
           'TICKER   VERDICT                   STATED -> FILED']
    for c in claims:
        checks=c.get('program_checks',[])
        values=''
        if checks:
            k=checks[0];values=f"{k.get('stated_value_used')} -> {k.get('actual_value')}"
        lines.append(f"{c.get('ticker','-'):<8} {c.get('verdict',c['status']):<25} {values}")
    lines+=['',f"Saved Threads batch | Baseten/post | {g['items']} posts",
            f"Median {g['median_wall_seconds']:.3f} s/post | elapsed {g['recorded_batch']['wall_seconds']:.3f} s",
            f"1,000 posts ~= {scale['projection']['sequential_hours_at_median']:.1f} h sequential at median (projection)",
            'No measured same-model parallel 1,000-post batch.','',
            'Recorded batch results (includes unsuccessful/unchecked items):']
    for path in g['sources'][:4]:
        r=read(path,sources)
        lines.append(f"{r['started_at'][11:19]} {r['id']:<5} {r['status']:<11} {r['verdict']}")
    yield 'BATCH / PROGRAM VERDICTS',lines
    for name,title,call_name in [('META-webp','SCREENSHOT / MUSE OCR','image'),
                                  ('MSFT-wav','AUDIO / MUSE VOICE TRANSCRIBE','audio')]:
        ingest=read(f'{FAIR}/test/baseten/low/{name}/ingest.json',sources)
        call=read(f'{FAIR}/prepared/{name}/calls/{call_name}.json',sources)
        c=ingest['channels'][0]
        prepared=read(f'{FAIR}/prepared/{name}/prepared.json',sources)
        # Shared pre-processing, cached text verification and synthetic inputs
        # remain explicitly labeled. This does not retest OCR/ASR.
        lines=[f"fair-multimodal-v1 | {name} | controlled synthetic fixture",
               f"Input: {ingest['input']['file']}",f"Recorded preprocessing model: {call['model']}",
               'Shared FROZEN preprocessing; text re-use is recorded separately.',
               f"Cached text verification reused: {c['text_reused']}",
               'REPLAY ONLY: OCR/ASR is not being retested.','',
               'EXTRACTED CLAIMS -> SEC TOOLS -> PROGRAM VERDICT']
        record=read(FAIR+'/'+c['text_record'],sources)
        record_folder=Path(FAIR)/Path(c['text_record']).parent
        for claim in c['claims']:
            if claim.get('trace_path'):
                trace=read((record_folder/claim['trace_path']).as_posix(),sources)
                tools=','.join(dict.fromkeys(t['name'] for t in trace['tool_calls']))
            else:
                tools='-'
            lines.append(f"{claim.get('ticker','-'):<6} {tools[:30]:<30} {claim.get('verdict',claim['status'])}")
        segment=c['segments'][0]
        lines+=['','Saved OCR/ASR text (verbatim excerpt):']+textwrap.wrap(segment['text'][:175],90)
        if call_name=='audio':
            lines.append('ASR source timestamps retained; speaker identities unverified.')
        lines+=['Source: docs/evidence/fair-multimodal-v1/test/baseten/low/'+name]
        yield title,lines


def pages(kind, sources):
    return list(comparison(sources) if kind=='beat4' else scale_pages(sources))


def play(kind):
    # No provider or product CLI imports. This is the explicit saved-trace
    # fallback because the product CLI has no offline inference replay flag.
    sources={}; content=pages(kind,sources)
    duration=16 if kind=='beat4' else 24
    start=time.monotonic()
    for i,(title,lines) in enumerate(content):
        if len(lines)>22 or any(len(line)>96 for line in lines):
            raise ValueError(f'Terminal page overflows: {title}')
        print('\033[2J\033[H\033[?25l',end='')
        print('\033[1;36mREPLAY | '+title+'\033[0m')
        print('Saved evidence only | no model calls | no SEC requests | playback != original speed')
        print('-'*94)
        print('\n'.join(lines),flush=True)
        time.sleep(max(0,start+(i+1)*duration/len(content)-time.monotonic()))
    print('\033[?25h',end='',flush=True)


def record(kind, agg):
    OUT.mkdir(parents=True,exist_ok=True)
    cast=OUT/f'{kind}.cast'
    if cast.exists():
        raise SystemExit(f'{cast} exists; retain it and choose a new take directory before recording again.')
    master,slave=pty.openpty()
    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',25,96,1920,1080))
    argv=[sys.executable,str(Path(__file__).resolve()),'play',kind]
    shell=['/bin/zsh','-f','-c','exec '+shlex.join(argv)]
    env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('TOKEN','SECRET','API_KEY','PASSWORD'))}
    env.update(TERM='xterm-256color',COLUMNS='96',LINES='25',PYTHONUNBUFFERED='1')
    start=time.monotonic()
    with cast.open('w') as output:
        output.write(json.dumps(dict(version=2,width=96,height=25,
            title='v4 '+kind+' | SAVED EVIDENCE REPLAY',
            env={'TERM':'xterm-256color','SHELL':'/bin/zsh'}))+'\n')
        child=subprocess.Popen(shell,cwd=ROOT,env=env,stdin=slave,stdout=slave,stderr=slave)
        os.close(slave)
        while True:
            ready,_,_=select.select([master],[],[],.2)
            if ready:
                try: raw=os.read(master,65536)
                except OSError: break
                if not raw: break
                output.write(json.dumps([time.monotonic()-start,'o',raw.decode('utf-8')])+'\n')
            elif child.poll() is not None:
                break
    os.close(master)
    code=child.wait()
    sources={};pages(kind,sources)
    receipt=dict(kind=kind,command=shell,recording='real zsh subprocess attached to a PTY, asciicast v2',
        exit_code=code,cols=96,rows=25,font_px=32,font='Menlo',theme='github-dark',
        resolution=[1920,1080],duration_s=16 if kind=='beat4' else 24,
        speed='editorial playback; never a runtime measurement',sources=sources,
        cast_sha256=hashlib.sha256(cast.read_bytes()).hexdigest(),status='cast-recorded')
    target=OUT/f'{kind}.json'
    target.write_text(json.dumps(receipt,indent=2)+'\n')
    if code: raise SystemExit(f'Real replay process failed ({code}); partial take retained.')
    if agg:
        gif=OUT/f'{kind}.gif'
        command=[agg,'--font-family','Menlo','--font-size','32','--line-height','1.2',
                 '--theme','github-dark','--idle-time-limit','100','--last-frame-duration','0',str(cast),str(gif)]
        subprocess.run(command,check=True)
        dims=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(gif)]))['streams'][0]
        if dims['width']>1920 or dims['height']>1080:
            raise SystemExit('Terminal exceeds 1920x1080; keep font >=28, adjust cols/rows in a new take.')
        mp4=OUT/f'{kind}.mp4'
        encode=['ffmpeg','-v','error','-y','-i',str(gif),'-vf',
                'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0d1117,fps=30',
                '-t',str(receipt['duration_s']),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(mp4)]
        subprocess.run(encode,check=True)
        receipt.update(status='rendered-real-terminal-recording',render_command=command,
            encode_command=encode,mp4_sha256=hashlib.sha256(mp4.read_bytes()).hexdigest(),
            terminal_raster=[dims['width'],dims['height']])
        target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(target.relative_to(ROOT))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command',choices=['play','record','check'])
    cli.add_argument('kind',choices=['beat4','beat7'])
    cli.add_argument('--agg',help='Path to an existing agg executable; never installs a package')
    args=cli.parse_args()
    if args.command=='play':play(args.kind)
    elif args.command=='record':record(args.kind,args.agg)
    else:
        sources={};result=pages(args.kind,sources)
        for title,lines in result:
            assert len(lines)<=22,(title,len(lines))
            assert max(map(len,lines))<=96,(title,max(map(len,lines)))
        print(f'PASS {args.kind}: {len(result)} saved-evidence pages, {len(sources)} source files')
