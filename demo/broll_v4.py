#!/usr/bin/env python3
"""Prepare two 480-test Wan accents; generate only on the existing local MPS engine."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent.parent
ENGINE=Path.home()/'ml-engines/wan'
MANIFEST=ROOT/'demo/prompts/broll/prompts-r4.json'
DEST=ROOT/'demo/assets/broll-v4'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    folder=MANIFEST.parent/'v4';folder.mkdir(parents=True,exist_ok=True)
    for name in ('cards-fanning-out','numbers-raining-into-filing'):
        image=Image.new('RGB',(480,480),'#111a20');draw=ImageDraw.Draw(image)
        if name=='cards-fanning-out':
            for x,y in [(108,120),(128,142),(148,164)]:
                draw.rounded_rectangle((x,y,x+190,y+220),radius=14,fill='#f7f5ef',outline='#8ddab8',width=4)
                for yy,w in [(44,128),(78,96),(112,125),(146,85)]:
                    draw.rounded_rectangle((x+24,y+yy,x+24+w,y+yy+9),radius=4,fill='#718e94')
        else:
            draw.rounded_rectangle((106,176,374,422),radius=12,fill='#f7f5ef')
            draw.polygon([(326,176),(374,224),(326,224)],fill='#8ddab8')
            for y in range(245,390,28):draw.rectangle((136,y,338,y+5),fill='#718e94')
            font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',36)
            for x,y,d in [(112,48,'7'),(216,83,'2'),(302,29,'9'),(344,121,'4')]:
                draw.text((x,y),d,font=font,fill='#8ddab8')
        image.save(folder/f'{name}.png')
    approved=json.loads((ROOT/'demo/prompts/broll/manifest.json').read_text())
    reference=approved['clips'][0]
    params={k:reference['params'][k] for k in ('frames','fps','size','steps','guidance','background',
             'subject_scale','device','dtype','offload','max_sequence_length','vae_dtype','attention','vae_tiling')}
    prompts={
      'cards-fanning-out':'Three ivory finance-post cards on a dark blue charcoal background. '
        'Starting from the conditioning image, the cards fan outward in one smooth, controlled motion, '
        'revealing their mint borders and abstract short grey lines. The cards remain separate, rigid and fully in frame. '
        'A small arc of mint light follows the fan. Premium editorial motion, soft studio lighting, stationary camera. '
        'Blank abstract cards, no logos and no readable claims.',
      'numbers-raining-into-filing':'An ivory financial filing on a dark blue charcoal background. '
        'Starting from the conditioning image, a few mint numeric glyphs rain gently downward into the open filing, '
        'then settle into clean grey rows. The sheet stays rigid, stable and fully in frame. '
        'Premium editorial motion, soft studio lighting, stationary camera, smooth falling motion. '
        'Abstract illustrative numbers only, no financial facts, company names, logos or real filing identifiers.',
    }
    shots=[]
    for i,(name,prompt) in enumerate(prompts.items()):
        image=folder/f'{name}.png'
        shots.append(dict(id=name,beat=2 if i==0 else 7,prompt=prompt,
            negative='watermark, logo, company name, legible financial claims, extra objects, distorted cards, '
                     'morphing, melting, jitter, flicker, sudden cuts, blur, low quality',
            image=image.relative_to(ROOT).as_posix(),image_sha256=digest(image),
            params=dict(params,seed=11 if i==0 else 29),
            source_frames=49,source_duration_s=49/16,editorial_duration_s=3.,
            expected_output=f'demo/assets/broll-v4/{name}.mp4',status='pending-host-MPS',attempts=[]))
    data=dict(schema_version=1,quality='480 test only; no final-quality approval claimed',
        engine='~/ml-engines/wan/gen_i2v.py',model=reference['model'],
        reference_manifest='demo/prompts/broll/manifest.json',reference_sha256=digest(ROOT/'demo/prompts/broll/manifest.json'),
        parameter_reference_clip=reference['id'],
        pipeline='WanImageToVideoPipeline, Wan2.2 TI2V-5B; conditioning drawings are code-native abstract shapes',
        shots=shots,approved_reuse_available=[dict(id=c['id'],source=c['source'],sha256=digest(ROOT/c['source'])) for c in approved['clips']])
    if MANIFEST.exists():
        existing=json.loads(MANIFEST.read_text())
        if any(s['attempts'] for s in existing['shots']):
            raise SystemExit('Existing attempts are retained. Do not replace prompts-r4.json with --prepare.')
    MANIFEST.write_text(json.dumps(data,indent=2)+'\n')


def command(shot,out):
    p=shot['params']
    return [str(ENGINE/'.venv/bin/python'),'-B',str(ENGINE/'gen_i2v.py'),
        '--image',str(ROOT/shot['image']),'--prompt',shot['prompt'],'--negative',shot['negative'],
        '--frames',str(p['frames']),'--fps',str(p['fps']),'--size','480x480',
        '--steps',str(p['steps']),'--guidance',str(p['guidance']),'--seed',str(p['seed']),
        '--background',p['background'],'--subject-scale',str(p['subject_scale']),
        '--device',p['device'],'--dtype',p['dtype'],'--offload',p['offload'],
        '--max-sequence-length',str(p['max_sequence_length']),'--out',str(out)]


def generate():
    data=json.loads(MANIFEST.read_text());stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt_dir=MANIFEST.parent/'v4/receipts';receipt_dir.mkdir(parents=True,exist_ok=True)
    probe_cmd=[str(ENGINE/'.venv/bin/python'),'-B','-c',
        'import json,torch; print(json.dumps(dict(torch=torch.__version__,mps_built=torch.backends.mps.is_built(),mps_available=torch.backends.mps.is_available())))']
    probe=subprocess.run(probe_cmd,capture_output=True,text=True)
    result=json.loads(probe.stdout) if probe.returncode==0 else {}
    receipt=dict(at=stamp,command=probe_cmd,exit_code=probe.returncode,stdout=probe.stdout,stderr=probe.stderr,
                 status='ready' if result.get('mps_available') else 'blocked-MPS-unavailable',
                 model_loaded=False,model_calls=0,sec_requests=0)
    probe_file=receipt_dir/f'{stamp}-preflight.json';probe_file.write_text(json.dumps(receipt,indent=2)+'\n')
    for shot in data['shots']:
        shot['attempts'].append(dict(receipt=probe_file.relative_to(ROOT).as_posix(),status=receipt['status']))
    MANIFEST.write_text(json.dumps(data,indent=2)+'\n')
    if not result.get('mps_available'):
        raise SystemExit('Wan generation needs host MPS. Preflight retained; no CPU substitute or new clip created.')
    # The original generator restricts output to its own workspace. On the host,
    # keep its raw MP4/JSON/log, then copy the three-second test accent into demo.
    work=ENGINE/'round4'/stamp
    for shot in data['shots']:
        if (ROOT/shot['expected_output']).exists():
            raise SystemExit('Keep existing output; create a separately named take before retrying.')
        out=work/(shot['id']+'.mp4');args=command(shot,out)
        completed=subprocess.run(args,capture_output=True,text=True)
        run_file=receipt_dir/f"{stamp}-{shot['id']}.json"
        run=dict(command=args,exit_code=completed.returncode,stdout=completed.stdout,stderr=completed.stderr)
        if out.with_suffix('.json').exists():run['wan_receipt']=json.loads(out.with_suffix('.json').read_text())
        run_file.write_text(json.dumps(run,indent=2)+'\n')
        shot['attempts'].append(dict(receipt=run_file.relative_to(ROOT).as_posix(),status='generated' if completed.returncode==0 else 'failed'))
        shot['status']='generated' if completed.returncode==0 else 'failed'
        if completed.returncode==0:
            DEST.mkdir(parents=True,exist_ok=True)
            final=ROOT/shot['expected_output']
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(out),'-t','3','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(final)],check=True)
            shot['output_sha256']=digest(final)
        MANIFEST.write_text(json.dumps(data,indent=2)+'\n')
        if completed.returncode:raise SystemExit('Wan attempt failed; receipt retained. Run on host and inspect the receipt.')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--prepare',action='store_true')
    cli.add_argument('--generate',action='store_true')
    args=cli.parse_args()
    if args.prepare:prepare()
    if args.generate:generate()
    if not args.prepare and not args.generate:cli.error('Choose --prepare or --generate')
