#!/usr/bin/env python3
"""Copy the four real story-A inputs and derive previews without model calls."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, tempfile, array
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/assets/examples-v5'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def prepare(source):
    OUT.mkdir(parents=True,exist_ok=True)
    commands=[];inputs=[]
    for ext in ('png','pdf','mp3','mp4','txt'):
        src=source/f'a.{ext}';dst=OUT/src.name
        if dst.exists() and sha(dst)!=sha(src):raise SystemExit('Different source already retained; use a new asset revision.')
        if not dst.exists():shutil.copyfile(src,dst)
        inputs.append(dict(path=dst.relative_to(ROOT).as_posix(),source=str(src),sha256=sha(dst),bytes=dst.stat().st_size))
    def run(command):
        subprocess.run(command,check=True,capture_output=True);commands.append([str(x) for x in command])
    pdf=OUT/'a.pdf';preview=OUT/'a-pdf-page1.png'
    if shutil.which('pdftoppm'):
        run(['pdftoppm','-f','1','-singlefile','-scale-to','1400','-png',str(pdf),str(preview.with_suffix(''))])
    else:
        # macOS ImageIO reads page 1. This is a raster of a.pdf, never a substitute image.
        run(['/usr/bin/sips','-s','format','png',str(pdf),'--out',str(preview)])
    run(['ffmpeg','-v','error','-y','-ss','1','-i',str(OUT/'a.mp4'),'-frames:v','1',str(OUT/'a-video-frame.png')])
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(OUT/'a.mp3'),'-f','s16le','-ac','1','-ar','8000','pipe:1'])
    samples=array.array('h',raw);count=64;chunk=max(1,len(samples)//count)
    peaks=[max(map(abs,samples[i*chunk:(i+1)*chunk]),default=0) for i in range(count)]
    waveform=[round(v/max(peaks),6) for v in peaks]
    (OUT/'a-waveform.json').write_text(json.dumps({'source':'a.mp3','source_sha256':sha(OUT/'a.mp3'),'sample_rate':8000,'channels':1,'bins':waveform},indent=2)+'\n')
    receipt=dict(inputs=inputs,derived=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in (preview,OUT/'a-video-frame.png',OUT/'a-waveform.json')],commands=commands,waveform_command=['ffmpeg','-v','error','-i','a.mp3','-f','s16le','-ac','1','-ar','8000','pipe:1'],note='Real story A files; previews only. No new OCR or ASR execution.')
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS four copied inputs and three source-derived previews')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,default=Path('/Users/yan/git/market-claim-verifier/docs/examples'))
    prepare(parser.parse_args().source)
