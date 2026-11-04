#!/usr/bin/env python3
"""Audit every encoded live frame's side gutters and password-mask extension."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from pipeline import BuildError,file_hash

COLOUR=(17,26,32)

def update_review_encode(review,video,loudness,validation,run_receipt):
    """Update only the measured-encode disclosure after all export gates pass."""
    text=review.read_text()
    note=(f"<!-- actual-encode:start -->\nActual r6 encode: **{video.stem}**, "
          f"{validation['duration_s']:.3f} s; **{loudness['measured_lufs']:.2f} LUFS integrated**, "
          f"**{loudness['true_peak_dbtp']:.2f} dBTP**.\n"
          f"Measured from `{video.name}`; SHA-256 `{file_hash(video)}`.\n"
          f"[Export and measurement receipt](runs/{run_receipt.name}).\n<!-- actual-encode:end -->")
    changed,count=re.subn(r'<!-- actual-encode:start -->[\s\S]*?<!-- actual-encode:end -->',lambda _:note,text)
    if count!=1:raise BuildError('REVIEW-v5.md requires one actual-encode disclosure block')
    review.write_text(changed)

def mask_pixels(image):
    delta=ImageChops.difference(image.convert('RGB'),Image.new('RGB',image.size,COLOUR))
    # Small H.264/YUV rounding is expected, readable native glyphs are not.
    # H.264 YUV rounding renders #111a20 about +2 in green everywhere; glyph rows measure >100.
    return max(ImageStat.Stat(delta).mean)<=4 and max(v[1] for v in delta.getextrema())<=16

def check_composite(video,data,out):
    out.mkdir(parents=True,exist_ok=True)
    start=data['live_terminal']['start_scene_s']
    checks=[]
    # Ignore two boundary pixels to allow chroma filtering at the inset border.
    # Keep clear of the inset card's 1 px border row (chroma smear) and of the
    # backplate's password->normal switch frame (seek rounding): 4 px / 0.4 s.
    regions=[('left gutter',58.,58.,(72,220,0,566)),
             ('right gutter',58.,58.,(72,220,1848,566)),
             ('password extension',58.,max(0.,start-.4),(1920,20,0,534))]
    for name,at,duration,(width,height,x,y) in regions:
        command=['/opt/homebrew/bin/ffmpeg','-nostdin','-v','error','-ss',str(at),'-i',str(video),
            '-t',str(duration),'-vf',f'fps=30,crop={width}:{height}:{x}:{y}',
            '-pix_fmt','rgb24','-f','rawvideo','-']
        frame_size=width*height*3;count=0;failures=[]
        with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as process:
            while True:
                raw=process.stdout.read(frame_size)
                if not raw:break
                if len(raw)!=frame_size:raise BuildError('Incomplete decoded composite frame')
                if not mask_pixels(Image.frombytes('RGB',(width,height),raw)):
                    failures.append(round(at+count/30,6))
                count+=1
            process.communicate()
            if process.returncode:raise BuildError('Composite decode failed')
        checks.append(dict(region=name,frames=count,expected_frames=round(duration*30),failures=failures,
            status='pass' if count>=int(duration*30) and not failures else 'fail'))
    report=dict(status='pass' if all(c['status']=='pass' for c in checks) else 'fail',
        scope='Every encoded frame in the 58–116 s live scene, including silent holds and cue transitions; gutters and password helper paragraph mask',
        video_sha256=file_hash(video),checks=checks)
    (out/'composite.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['status']!='pass':raise BuildError('Encoded whole-composite mask audit failed; retained composite.json')
    return report
