#!/usr/bin/env python3
"""Check the encoded 154 s cut: outgoing Results, then three native-page frames."""
import argparse,json,subprocess
from pathlib import Path

from PIL import Image,ImageChops,ImageStat
from pipeline import BuildError,file_hash

FRAMES=(4619,4620,4621,4622)
PROOF=(180,80,1740,550)  # Above the ending card, chapter band and captions.
TOLERANCE=12.0


def image_error(a,b):
    return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3


def audit_cut_frames(encoded,native,*,outgoing=None):
    if len(encoded)!=4 or len(native)!=3:
        raise BuildError('Ending cut check requires encoded frames 4619–4622 and native frames 0–2')
    def proof(path):
        with Image.open(path) as image:
            if image.size!=(1920,1080):raise BuildError('Ending cut images must stay 1920x1080')
            return image.convert('RGB').crop(PROOF)
    actual=[proof(p) for p in encoded];expected=[proof(p) for p in native]
    rows=[]
    before_error=image_error(actual[0],proof(outgoing)) if outgoing else None
    separation=image_error(actual[0],expected[0])
    rows.append(dict(frame=4619,role='outgoing Results; fixed cut has not occurred',
        expected_native_page=False,native_page=separation<=TOLERANCE,reference_error=before_error,native_difference=separation,
        status='pass' if separation>40 and (before_error is None or before_error<=TOLERANCE) else 'fail'))
    for i,(picture,source) in enumerate(zip(actual[1:],expected)):
        histogram=source.convert('L').histogram();light_fraction=sum(histogram[181:])/sum(histogram)
        error=image_error(picture,source)
        present=error<=TOLERANCE and light_fraction>.55
        rows.append(dict(frame=4620+i,role='native corrected draft and SEC filing page',expected_native_page=True,native_page=present,
            native_source_frame=i,reference_error=error,source_light_fraction=light_fraction,
            status='pass' if present else 'fail'))
    return dict(status='pass' if all(r['status']=='pass' for r in rows) else 'fail',
        scope='Actual encoded frames, compared with decoded native take; no OCR/ASR or new check',
        proof_region=list(PROOF),mean_rgb_error_limit=TOLERANCE,frames=rows)


def check_ending_cut(film,native_take,out,*,outgoing=None):
    import media
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    def extract(source,first,last,prefix):
        subprocess.run([str(media.FFMPEG),'-nostdin','-hide_banner','-loglevel','error','-n','-i',str(source),
            '-vf',f'select=between(n\\,{first}\\,{last})','-fps_mode','passthrough',str(out/f'{prefix}-%02d.png')],check=True,capture_output=True)
        return sorted(out.glob(f'{prefix}-*.png'))
    encoded=extract(film,4619,4622,'encoded')
    native=extract(native_take,0,2,'native')
    report=audit_cut_frames(encoded,native,outgoing=outgoing)
    report['inputs']={str(p):file_hash(p) for p in (Path(film),Path(native_take),*([Path(outgoing)] if outgoing else []))}
    for row,path in zip(report['frames'],encoded):row.update(file=path.name,sha256=file_hash(path))
    report['native_references']=[dict(file=p.name,sha256=file_hash(p)) for p in native]
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['status']!='pass':raise BuildError(f'Encoded ending cut failed; retained frames and report: {out}')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--film',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--storyboard',type=Path,default=Path(__file__).with_name('storyboard-v5.yaml'))
    args=parser.parse_args()
    import yaml
    story=yaml.safe_load(args.storyboard.read_text());root=Path(__file__).resolve().parents[1]
    take=next(s for s in story['scenes'] if s['id']=='v508')['recording']['asset']
    check_ending_cut(args.film,root/take,args.out)
    print('PASS encoded ending cut: 4619 Results; 4620–4622 native page, including the first frame at 154.000 s')


if __name__=='__main__':main()
