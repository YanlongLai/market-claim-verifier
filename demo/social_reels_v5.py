"""9:16 punch-in Reels cut from the final 16:9 master: per-shot crops, headline band, two-line captions."""
import subprocess, sys, os, textwrap
from PIL import Image, ImageDraw, ImageFont
src, out, srt = sys.argv[1:4]
W,H=1080,1920; ZW,ZH=1080,780; ZY=470; INK='0x111a20'
work=os.path.join(os.path.dirname(out),'reels-overlays'); os.makedirs(work,exist_ok=True)
# (film_t0, film_t1, crop x, y, w, h, headline)
shots=[(8,20, 20,60,860,620, 'A real number. The wrong period.'),
       (46,58, 0,0,1920,786, 'Model proposes. Program decides.'),
       (58,65.8, 60,0,1800,786, 'Live on the site'),
       (65.8,83.38, 'terminal', 'Real server log · this request'),
       (83.38,85.37, 80,56,1000,722, 'Contradicted, with the filing'),
       (85.37,88.13, 60,56,1120,722, 'Corrected draft'),
       (88.13,96, 130,0,1660,786, 'Annual − nine months = quarter'),
       (138,154, 40,40,1720,740, 'Held-out results'),
       (170,178, 40,20,1800,740, 'hackathon.dappgo.com')]
def font(sz,bold=False):
    for p in ('/System/Library/Fonts/HelveticaNeue.ttc','/System/Library/Fonts/Helvetica.ttc'):
        try: return ImageFont.truetype(p,sz,index=1 if bold else 0)
        except Exception: pass
def plate(lines,path,h):
    img=Image.new('RGBA',(W,h),(0,0,0,0)); d=ImageDraw.Draw(img); y=0
    for txt,f,col,gap in lines:
        w=d.textlength(txt,font=f); d.text(((W-w)/2,y),txt,font=f,fill=col); y+=gap
    img.save(path)
inputs=['-i',src]; fc=[]; vparts=[]; aparts=[]; overlays=[]; t_out=0.0
for i,s in enumerate(shots):
    t0,t1=s[0],s[1]; dur=t1-t0
    if s[2]=='terminal':
        head=s[3]
        fc.append(f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,split=2[tr{i}][tc{i}];"
                  f"[tr{i}]crop=1160:194:80:598,scale=1080:-2[rows{i}];"
                  f"[tc{i}]crop=136:38:1702:561,scale=384:-2[clk{i}];"
                  f"color=c={INK}:s={ZW}x{ZH}:r=30:d={dur}[bg{i}];"
                  f"[bg{i}][rows{i}]overlay=0:330[b{i}];[b{i}][clk{i}]overlay=W-w-40:170[v{i}]")
        term_label=(t_out,t_out+dur)
    else:
        x,y,w,h,head=s[2],s[3],s[4],s[5],s[6]
        fc.append(f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},"
                  f"scale='if(gt(a,{ZW/ZH:.4f}),{ZW},-2)':'if(gt(a,{ZW/ZH:.4f}),-2,{ZH})',"
                  f"pad={ZW}:{ZH}:(ow-iw)/2:(oh-ih)/2:color={INK},setsar=1[v{i}]")
    fc.append(f"[0:a]atrim={t0}:{t1},asetpts=PTS-STARTPTS[a{i}]")
    vparts.append(f"[v{i}]"); aparts.append(f"[a{i}]")
    p=f'{work}/head{i}.png'
    plate([('Market Claim Verifier',font(40),(141,218,184),64),(head,font(62,True),(247,245,239),80)],p,170)
    overlays.append((t_out,t_out+dur,p,270)); t_out+=dur
n=len(shots)
lp=f'{work}/termlabel.png'
img=Image.new('RGBA',(W,140),(0,0,0,0)); dd=ImageDraw.Draw(img)
dd.text((40,10),'live request 145a6982 · pod log',font=font(36),fill=(182,198,202))
dd.text((40,62),'Request elapsed',font=font(48,True),fill=(199,208,209))
img.save(lp); overlays.append((term_label[0],term_label[1],lp,ZY+165))
fc.append(''.join(f"{vparts[k]}{aparts[k]}" for k in range(n))+f"concat=n={n}:v=1:a=1[strip][aud]")
fc.append(f"color=c={INK}:s={W}x{H}:r=30:d={t_out}[canvas];[canvas][strip]overlay=0:{ZY}:shortest=1[c0]")
def t(s_): h,m,rest=s_.split(':'); sec,ms=rest.split(','); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
for k,blk in enumerate(open(srt).read().strip().split('\n\n')):
    L=blk.split('\n')
    if len(L)<3: continue
    a,b=[t(x.strip()) for x in L[1].split('-->')]; text=' '.join(L[2:])
    f=font(46); lines=textwrap.wrap(text,width=36)
    if len(lines)>2: f=font(40); lines=textwrap.wrap(text,width=42)[:2]
    p=f'{work}/cap{k:02d}.png'; plate([(ln,f,(247,245,239),58) for ln in lines],p,130)
    overlays.append((a,b,p,1310))
for _,_,p,_ in overlays: inputs+=['-i',p]
prev='c0'
for k,(a,b,p,yy) in enumerate(overlays):
    nxt=f'o{k}'; fc.append(f"[{prev}][{k+1}:v]overlay=0:{yy}:enable='gte(t,{a:.3f})*lt(t,{b:.3f})'[{nxt}]"); prev=nxt
cmd=['ffmpeg','-v','error','-y']+inputs+['-filter_complex',';'.join(fc),'-map',f'[{prev}]','-map','[aud]',
     '-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-movflags','+faststart',out]
r=subprocess.run(cmd,capture_output=True,text=True)
print(r.stderr[-600:] if r.returncode else f'encoded {t_out:.1f}s, {len(overlays)} overlays')
