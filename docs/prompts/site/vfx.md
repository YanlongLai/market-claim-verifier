# Spotlight cinematic VFX textures

Generated on **2026-10-29** with the built-in **image_gen** tool, one generation
per requested texture. These seven AI-generated bitmap masters implement the
visual material described in [STAMP-V2-DESIGN.md §8.4](../../site/STAMP-V2-DESIGN.md#84-spotlight-owner-round-5-像探照燈要有電影的效果).
Generation was followed by local Pillow/NumPy crop, grayscale/levels, alpha,
seam treatment, resizing and WebP encoding. No site code, commit or push belongs
to this asset task. All project outputs are in `docs/site/img/fx/` and this file.

## Files and integration starting points

Opacity values below are **dark / light theme**, use ordinary CSS 0–1 opacity,
and are the actual values used in the comparison panels of
[contact.png](../../site/img/fx/contact.png). The light textures remain neutral:
mint and amber are applied at composition time, without separate tinted files.

| Texture | Pixels | Bytes | Blend | Dark opacity | Paper opacity |
|---|---:|---:|---|---:|---:|
| [beam-cone.webp](../../site/img/fx/beam-cone.webp) | 1024 × 384 | 7,658 | screen | .60 | .75 |
| [beam-pool.webp](../../site/img/fx/beam-pool.webp) | 512 × 256 | 3,388 | screen | .28 | .35 |
| [dust-motes.webp](../../site/img/fx/dust-motes.webp) | 512 × 512 | 6,112 | screen | .45 | .50 |
| [lens-flare.webp](../../site/img/fx/lens-flare.webp) | 768 × 128 | 1,122 | screen | .50 | .65 |
| [impact-burst.webp](../../site/img/fx/impact-burst.webp) | 512 × 512 | 26,414 | screen | .60 | .70 |
| [film-grain.webp](../../site/img/fx/film-grain.webp) | 256 × 256 | 15,946 | soft-light | .10 | .10 |
| [vignette.webp](../../site/img/fx/vignette.webp) | 1024 × 512 | 50,916 | normal / source-over | .45 | .50 |

The runtime textures total **111,556 bytes**. Every texture is under **60,000
bytes**, and grain is under **20,000 bytes**, using stricter decimal budgets.
`contact.png` is a **1440 × 2047**, **435,590-byte** review image, not a runtime
texture. It shows all seven textures on both backgrounds and two mock composites.
The grain row includes a labeled 2× crop with 4× contrast solely for inspection;
its main background uses the real 10% soft-light treatment.

- **Beam:** rotate/stretch from its left source, with the transform origin near
  **1.5% 50%** of the image. That is the approximate luminous origin after the
  black edge feather. The end is a diffuse open cone. Use one cone during Find
  and two instances at Compare. These are white RGB masters on opaque black.
- **Pool:** place the centered ellipse on the matching value/row. Use restrained
  opacity so the row stays legible; a short bloom can briefly increase it.
- **Dust:** repeat at its native 512 px size and clip/mask to the beam volume.
  Slow movement should follow the deterministic scene clock. The sheet exposes
  the dust across the panel for inspection; the mock clips it with cone luminance.
- **Flare:** center on the visor source. Its bright axis is at 50% 50%; keep the
  strip thin. The supplied texture has no vertical star ray or colored ghosts.
- **Impact:** a short stamp-strike accent, around 80 ms. Turn off the cones at
  the strike; place this burst locally around the stamp contact, not over text.
  A brief white flash is a separate scene layer, as specified in §8.4.
- **Grain:** repeat at 256 px, soft-light .06–.12; .10 is the preview starting
  point. Overlay is an alternative at .03–.06. The tile mean is 128.008/255 with
  standard deviation 5.530/255. Avoid scaling it up in the actual scene.
- **Vignette:** black RGBA with a genuinely transparent center; apply as a normal
  alpha overlay. The .45/.50 values show its effect clearly in the isolated
  previews. Use about **.24** when combined with an already dimmed stage, as in
  the mocks, to avoid excessive darkening.

Screen blending should happen above the dim overlay inside the stage's isolated
blend group. The five emissive RGB plates have **opaque black backgrounds**:
tint their luminance while keeping black at RGB 0, then screen them. If using
them as CSS masks, explicitly choose **luminance** masking; default alpha masking
would reveal the whole opaque rectangle. Grain and vignette use their own blend
modes, and should not be tinted. Keep real filing text above the decorative
light, preserve the scene's reduced-motion behavior, and make timing seekable.

The contact sheet uses dark **#111a20**, mint **#d6fff0**, and amber **#ffd59a**.
Paper is **#f7f5ef under a 45% black overlay**, retaining 55% RGB intensity:
**#888783**. Screen is computed in the image's sRGB channel values as
`base + opacity × luminance × tint × (1 - base)`, with all channels normalized
to 0–1. Source-over black vignette and W3C-style soft-light grain are composited
separately. Mocks also include 12 px letterbox bars, one point source, a filing
rectangle, cone-clipped motes and a pool. Their foreground bars stand in for
readable HTML, drawn after the light layers. Labels only exist in the contact
sheet; no words, logos or recognizable objects are baked into any texture.

## Exact built-in generation prompts

Each call used the exact prompt below. No reference images and no prior-image
inclusion were supplied. `transparent_background` was **false** for the first
six and **true** for `vignette`. All seven first-pass generations were selected;
there were no model edits or substitute procedural generations.

### beam-cone.webp

```text
Use case: stylized-concept; production cinematic VFX texture plate, not a scene. Create exactly one horizontal soft volumetric searchlight cone in neutral monochrome white on absolutely pure flat black #000000. Wide 8:3 canvas, intended final crop 1024x384. The tiny source is at x=3%, y=50%; the cone widens to the right and reaches its widest point near x=87%, spanning y=13% to y=87%, then fades smoothly to black by x=98%. The origin is narrow, gentle and not a starburst. Subtle long fine god-ray streaks run from that same source through faint smoky light volume; realistic scattering, broad silky falloff, understated film optics, restrained luminance, no blown white mass. Both outer edges are very soft and the far end is open diffuse light, never an outlined triangle or a closed solid wedge. Leave the top, bottom and rightmost margin completely black. The cone must read beautifully when screen-blended over dark slate #111a20 or a darkened paper stage; tint will be applied later in CSS. Neutral grayscale only, no baked color. No beam hardware, no spotlight fixture, no objects, no robot, no setting, no surface, no horizon, no visible dust particles, no text, no logo, no border, no transparency checkerboard. One standalone effect only, occupying the wide frame.
```

### beam-pool.webp

```text
Use case: stylized-concept; standalone cinematic VFX texture plate. Create a single soft elliptical pool of neutral-white light on an absolutely pure flat black #000000 background, wide 2:1 canvas, final target 512x256. Front-on abstract elliptical light footprint, centered at 50%/50%, longer axis horizontal, major diameter 78% of width and minor diameter 53% of height. Silky diffuse soft illumination inside, a delicate slightly brighter feathered elliptical rim, with all light falling gently to completely black well before the image edges. The rim must not become a hard neon ring or a hollow donut; keep an illuminated soft interior. Restrained photorealistic cinematic bloom and organic haze, subtle unevenness of real light, no perspective plane, no hard outline, no colored tint. Designed for mix-blend-mode screen over dark slate or darkened warm paper and for very small readable pools around a filing value. No object, no ground, no horizon, no scene, no spotlight fixture, no text, no logo, no border, no transparency checkerboard. Only the monochrome light texture on black.
```

### dust-motes.webp

```text
Use case: stylized-concept; seamless production cinematic VFX texture. A sparse distribution of tiny suspended neutral-white dust motes and extremely restrained out-of-focus bokeh specks on perfectly flat pure black #000000. Square canvas, final tile 512x512. Only about 45 to 65 visible motes in the entire tile, mostly pinprick-sized and very faint, a few soft defocused discs of varied small size, no large disc, no dense star field. Organic uneven spacing with generous truly black negative space, realistic lens focus variation, muted pearl-gray luminance, monochrome. Spatial density and black background remain uniform enough to tile; matching opposite edges and no vignette, no central cluster, no directional beam, no fog layer. Meant to drift subtly inside a masked searchlight cone using screen blending. No sparks, no meteor streaks, no stars with cross-shaped flares, no objects, no landscape, no setting, no text, no logos, no border, no transparency checkerboard.
```

### lens-flare.webp

```text
Use case: stylized-concept; standalone cinematic optical VFX plate, not a scene. Create one subtle neutral-white anamorphic horizontal lens flare streak on completely pure flat black #000000. Very wide strip, final target 768x128, central optical axis exactly at y=50%. A small softly glowing source at x=50%, long hairline horizontal streak fading gently to black by x=4% and x=96%, a very faint broad soft halo immediately around the center. Elegant real cinema lens scattering with a little fine horizontal optical variation. Monochrome neutral white only, low intensity except the tiny center, restrained and delicate. Keep all four margins black. Absolutely no vertical ray, no cross-shaped star, no explosion, no oversized white blob, no colored rainbow ghosts, no circular lens ghost shapes, no spotlight fixture, no objects, no background scene, no text, no logos, no border, no transparency checkerboard. One isolated flare only. If the canvas must be taller than 6:1, surround the very thin centered flare with pure black padding for a later centered 6:1 crop.
```

### impact-burst.webp

```text
Use case: stylized-concept; isolated cinematic stamp-strike VFX texture on absolutely pure flat black #000000. Square canvas, final target 512x512. Centered small radial ink-and-light shock burst, like one instant of a forceful rubber stamp striking paper, but with NO stamp, NO paper, NO real object and NO literal symbol. Neutral-white and soft gray radial dry-ink splinters, very fine irregular rays and a few ink-like white particulate flecks, mixed with a restrained soft flash of light in the small central 12% region. Organic printmaking character and cinematic impact, asymmetrical fine ray lengths and broken radial strokes, not a geometric star. The burst occupies only the central 75% of the square and falls entirely to pure black before all edges. Keep a generous black border. No circular shockwave ring, no massive smoke cloud, no fire, no fireworks, no dense shrapnel, no hard lens star, no big solid white blob. No color. No text, letters, logos, objects, setting, border or transparency checkerboard. Screen-blended for one very brief stamp-strike flash.
```

### film-grain.webp

```text
Use case: stylized-concept; production film-grain texture scan. Create a perfectly seamless square monochrome fine cinema film grain tile on an even middle-gray base, RGB approximately 128,128,128, final target 256x256. Extremely fine organic silver-halide grain: delicate random light and dark luminance variations with very low contrast, evenly distributed at every point, no directional bias, no pattern or seams. Flat front-on microscopic texture only, no lighting gradients, no vignette, no large fibers, no paper texture, no scratches, no stains, no dust clumps, no recognizable objects, no text, no logos, no borders. Monochrome and almost uniform mid-gray at normal viewing distance. Designed to repeat under soft-light or overlay blending at very low opacity, never to interfere with small readable type.
```

### vignette.webp

```text
Use case: stylized-concept; production transparent alpha overlay. Generate a single soft oval black cinematic vignette with REAL TRANSPARENCY, wide 2:1 canvas, final target 1024x512. The entire center of the oval is completely transparent and empty. Neutral pure-black pigment exists only in the outer edges and rounded corners, strongest near the outer perimeter and corners, smoothly fading inward to zero alpha with a very broad perfectly smooth feathered falloff. Center at x=50%, y=50%, the large clear oval spans roughly 65% of width and 60% of height. This is a flat 2D black overlay mask, not a scene and not a black solid canvas: transparent center, semitransparent soft black transition, opaque black corners. No visible ellipse outline, no white or gray pixels painted into the image, no checkerboard baked in, no texture, no grain, no objects, no text, no logos, no frame lines. Preserve real alpha so this can darken the edges of either slate or warm paper with ordinary source-over compositing.
```

## Source provenance

Original generated PNGs remain in the built-in tool's output directory, not in
the runtime asset folder:

```text
/Users/yan/.codex/generated_images/01a18858-d7de-7421-af00-97eeb2d29931/
```

The processor below maps each exact source filename. New generations will have
new filenames; update that map when reusing these prompts. Original PNG hashes:

| Texture | Original dimensions | Source SHA-256 |
|---|---:|---|
| beam-cone | 2048 × 768 | `5ad3c45fb84b3f6b19fd83977b2bcd981db9d9c5057b623c8ccaad3b34654f2a` |
| beam-pool | 1774 × 887 | `4deeacab7ef8faf52b8807d7a5dee862df79ff6d4bf592123059b604b9f511a1` |
| dust-motes | 1254 × 1254 | `b9b5a275cc4b726996523c4556e81dedb470451a3be933643cbbbbf82e6bd7cc` |
| lens-flare | 2172 × 724 | `212a4a017589c87a2ef9c82b62bca23efffad753e31e2655f433dfa312bd3abd` |
| impact-burst | 1254 × 1254 | `32717543012181ef33cd1594add6bb1d62e58bc3a094869f3369518636af1768` |
| film-grain | 1254 × 1254 | `6e4e5437442f3f30dc1e9ec0f29bb546765c17b3510292d946fd3fe3f8203838` |
| vignette | 1774 × 887 | `c98394b35a22e2c787385e743b0557f900bc7327dcc3427202738799d74bfc28` |

## Exact post-processing

Environment: **Pillow 13.0.0**, **NumPy 2.5.4**, WebP support enabled, through
the existing worktree `.venv/bin/python`. There were no dependency changes.
The snippets below are the actual local processing and contact-sheet scripts.
Save them outside the repository (for example `/private/tmp/`) and run with
`.venv/bin/python`. Adjust `ROOT` for a different checkout. The source map can
point to newly generated PNGs. Raw sources are not loaded by the site.

1. **Crop/resize:** Lanczos to the exact requested dimensions. All source aspects
   already matched except the flare, whose 2172 × 724 source was center-cropped
   to **(0, 181, 2172, 543)**, then resized to 768 × 128. Other images use their
   complete source frame.
2. **Emissive levels:** convert to grayscale. Apply
   `255 × clip((L - black)/(white - black), 0, 1)^gamma` using the table below.
   Five emissive masters stay neutral white, with black at RGB 0.
3. **Boundary treatment:** cone/pool/flare/impact get a smoothstep fade to exact
   black at the image boundary. The cone's side fade is 1.5% of width; the other
   three use 3.5%. Vertical fades use 5.5% of height. This removes visible frame
   edges during screen blending without repainting the generated light.
4. **Dust seams:** after levels, join matching opposite edges across 24 px
   bands. At each offset, blend the two opposing pixels toward their mean,
   using `1 - smoothstep(offset/(band - 1))`; leave the interior untouched.
5. **Film grain:** use generated luminance minus a Gaussian-blurred copy
   (radius 2.2 px), normalize the detail to standard deviation 5.2, join edges
   across 12 px bands, clip detail to ±20 around 128, and round its detail to
   multiples of 6. This preserves generated grain, keeps mid-gray neutral,
   removes broad lighting variation and fits a lossless tile under 20 KB.
6. **Vignette alpha:** preserve the AI-generated alpha, resize it with the image,
   smooth with Gaussian radius 3.0 px, normalize its maximum to 255, and set all
   RGB values to pure black. No magenta key was needed. A gentler 1.1 px smoothing
   pass exceeded the lossless byte budget; the selected 3.0 px pass yields the
   final smooth 50,916-byte overlay, with the generated oval unchanged in shape.
7. **WebP:** cone/pool/flare/impact use quality **91**, method **6**. Dust, grain
   and vignette use **lossless** WebP, method **6**, `exact=True`. No asset hit
   the script's lossy quality fallback. No metadata is attached.

| Emissive texture | Black point | White point | Gamma |
|---|---:|---:|---:|
| beam-cone | 2 | 238 | 1.04 |
| beam-pool | 2 | 248 | 1.06 |
| dust-motes | 1 | 190 | .86 |
| lens-flare | 1 | 220 | .94 |
| impact-burst | 2 | 245 | 1.04 |

<details>
<summary>Complete texture processor (Python)</summary>

```python
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np
import json, re, io, hashlib

ROOT = Path('/Users/yan/git/market-claim-verifier-stamp2')
OUT = ROOT / 'docs/site/img/fx'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE_ROOT = Path('/Users/yan/.codex/generated_images/01a18858-d7de-7421-af00-97eeb2d29931')
SOURCES = {
    'beam-cone': SOURCE_ROOT / 'exec-db8450ce-f3ed-454c-9f3f-7edbff38cd7e.png',
    'beam-pool': SOURCE_ROOT / 'exec-073bd866-903a-4312-a02e-5d13a8dc3cd7.png',
    'dust-motes': SOURCE_ROOT / 'exec-2261a38b-8286-4953-853a-b49853395565.png',
    'lens-flare': SOURCE_ROOT / 'exec-67d4dd77-2033-4021-ac53-ac4e76a3141e.png',
    'impact-burst': SOURCE_ROOT / 'exec-0260d6da-6edd-4ab4-8a1b-91a667d3a7f8.png',
    'film-grain': SOURCE_ROOT / 'exec-20e3e5ae-d28e-4e28-94dc-6e2bee86949c.png',
    'vignette': SOURCE_ROOT / 'exec-44308543-449f-459a-bf33-3b4e8ebe77d0.png',
}
SIZES = {'beam-cone': (1024,384), 'beam-pool': (512,256),
         'dust-motes': (512,512), 'lens-flare': (768,128),
         'impact-burst': (512,512), 'film-grain': (256,256),
         'vignette': (1024,512)}
LANCZOS = Image.Resampling.LANCZOS

def u8(a):
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)

def gray(a):
    return Image.fromarray(u8(a)).convert('RGB')

def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)

def join_edges(a, width):
    # Only adjust a narrow seam band; equal opposite pixels survive lossless WebP.
    a = a.astype(np.float64).copy()
    for axis in (0,1):
        b = np.moveaxis(a, axis, 0)
        for i in range(width):
            weight = 1 - smooth(i/(width-1))
            left, right = b[i].copy(), b[-1-i].copy()
            mean = (left+right)/2
            b[i] = left*(1-weight) + mean*weight
            b[-1-i] = right*(1-weight) + mean*weight
    return a

def black_edges(a, xfade=0.035, yfade=0.055):
    h,w = a.shape
    yy,xx = np.mgrid[0:h,0:w]
    x = np.minimum(xx,w-1-xx)/max(1,(w-1)*xfade)
    y = np.minimum(yy,h-1-yy)/max(1,(h-1)*yfade)
    return a*smooth(x)*smooth(y)

stats = {}
for name, size in SIZES.items():
    original = Image.open(SOURCES[name])
    crop = (0,0,*original.size)
    if name == 'lens-flare':
        # Tool supplied 3:1 with black padding. Crop the centered optical strip to 6:1.
        crop_h = round(original.width/6)
        top = (original.height-crop_h)//2
        crop = (0,top,original.width,top+crop_h)
    image = original.crop(crop).resize(size,LANCZOS)
    a = np.asarray(image.convert('L'),dtype=np.float64)
    lossless = name in ('dust-motes','film-grain','vignette')
    if name == 'film-grain':
        # Remove low frequency variation, preserve AI grain, recenter to neutral 128.
        blur = np.asarray(image.convert('L').filter(ImageFilter.GaussianBlur(2.2)),dtype=np.float64)
        fine = a-blur
        fine = (fine-fine.mean()) / max(fine.std(),1e-6) * 5.2
        fine = join_edges(fine,12)
        a = 128 + np.clip(fine,-20,20)
        # Six-value quantization keeps genuine small grain below the 20,000-byte cap.
        a = 128 + np.rint((a-128)/6)*6
        image = gray(a)
    elif name == 'vignette':
        # Preserve actual generated alpha; no color key or synthetic replacement.
        alpha = image.getchannel('A').filter(ImageFilter.GaussianBlur(3.0))
        aa = np.asarray(alpha,dtype=np.float64)
        aa = u8(aa*255/aa.max())
        image = Image.new('RGBA',size,(0,0,0,0))
        image.putalpha(Image.fromarray(aa))
    else:
        blackpoint, whitepoint, gamma = {
            'beam-cone': (2,238,1.04),
            'beam-pool': (2,248,1.06),
            'dust-motes': (1,190,0.86),
            'lens-flare': (1,220,0.94),
            'impact-burst': (2,245,1.04),
        }[name]
        a = 255*np.clip((a-blackpoint)/(whitepoint-blackpoint),0,1)**gamma
        if name == 'dust-motes':
            a = join_edges(a,24)
        else:
            a = black_edges(a,0.015 if name=='beam-cone' else 0.035,0.055)
        image = gray(a)
    path = OUT / (name+'.webp')
    quality = 91
    while True:
        image.save(path,'WEBP',lossless=lossless,quality=quality,method=6,exact=True)
        if path.stat().st_size <= (20000 if name=='film-grain' else 60000):
            break
        if lossless:
            raise RuntimeError(f'{name} lossless budget exceeded: {path.stat().st_size}')
        quality -= 3
        if quality < 55:
            raise RuntimeError(f'{name} cannot meet byte budget')
    dec = Image.open(path)
    stats[name] = dict(size=size, bytes=path.stat().st_size, mode=dec.mode,
        source=str(SOURCES[name]), source_size=original.size, crop=crop,
        source_sha256=hashlib.sha256(SOURCES[name].read_bytes()).hexdigest(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        lossless=lossless, quality=quality, method=6)
    print(name, size, path.stat().st_size, 'bytes', dec.mode,
          'lossless' if lossless else f'q{quality}')

Path('/private/tmp/stamp-vfx-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
```

</details>

<details>
<summary>Complete contact-sheet renderer (Python)</summary>

```python
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path('/Users/yan/git/market-claim-verifier-stamp2')
FX = ROOT/'docs/site/img/fx'
RESAMPLE = Image.Resampling.LANCZOS
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,size)
def array(im):
    return np.asarray(im.convert('RGB'),dtype=float)/255
def image(a):
    return Image.fromarray(np.uint8(np.rint(np.clip(a,0,1)*255)))
def screen(base,plate,opacity=1,tint=(255,255,255)):
    b=array(base)
    p=np.asarray(plate.convert('L'),dtype=float)[...,None]/255
    s=p*np.array(tint)/255
    return image(b+opacity*s*(1-b))
def softlight(base,plate,opacity):
    b=array(base); s=array(plate)
    d=np.where(b<=.25,((16*b-12)*b+4)*b,np.sqrt(b))
    mixed=np.where(s<=.5,b-(1-2*s)*b*(1-b),b+(2*s-1)*(d-b))
    return image(b*(1-opacity)+mixed*opacity)
def tile(im,size):
    result=Image.new(im.mode,size)
    for y in range(0,size[1],im.height):
        for x in range(0,size[0],im.width):
            result.paste(im,(x,y))
    return result
def over(base,plate,opacity):
    p=plate.convert('RGBA').copy()
    p.putalpha(p.getchannel('A').point(lambda a:round(a*opacity)))
    return Image.alpha_composite(base.convert('RGBA'),p).convert('RGB')

DARK=(17,26,32)
PAPER=tuple(round(c*.55) for c in (247,245,239))
MINT=(214,255,240)
AMBER=(255,213,154)
TEXT=(224,231,230)
MUTED=(148,164,168)
PLATES={name:Image.open(FX/(name+'.webp')).copy() for name in
    ('beam-cone','beam-pool','dust-motes','lens-flare','impact-burst','film-grain','vignette')}

W=1440
sheet=Image.new('RGB',(W,2090),(10,17,22))
draw=ImageDraw.Draw(sheet)
draw.text((40,30),'SPOTLIGHT / CINEMATIC VFX',font=font(34,True),fill=TEXT)
draw.text((42,80),'AI-generated neutral masters  /  actual WebP decodes  /  tint applied only in this preview',font=font(16),fill=MUTED)
draw.line((40,115,1400,115),fill=(42,55,61))
draw.text((240,133),'DARK  #111a20  +  mint-white light',font=font(17,True),fill=MINT)
draw.text((832,133),'PAPER  #f7f5ef  ×  55%  +  amber light',font=font(17,True),fill=AMBER)

rows=[
 ('beam-cone',206,'1024 × 384','screen  ·  .60 / .75',(.60,.75)),
 ('beam-pool',184,'512 × 256','screen  ·  .28 / .35',(.28,.35)),
 ('dust-motes',210,'512 × 512  ·  tile','screen  ·  .45 / .50',(.45,.50)),
 ('lens-flare',154,'768 × 128','screen  ·  .50 / .65',(.50,.65)),
 ('impact-burst',210,'512 × 512','screen  ·  .60 / .70',(.60,.70)),
 ('film-grain',178,'256 × 256  ·  tile','soft-light  ·  .10',(.10,.10)),
 ('vignette',210,'1024 × 512  ·  alpha','normal  ·  .45 / .50',(.45,.50)),
]
y=166
for index,(name,height,dimensions,mode,opacities) in enumerate(rows,1):
    draw.text((42,y+15),f'{index:02d}',font=font(13),fill=(101,127,134))
    draw.text((42,y+40),name,font=font(20,True),fill=TEXT)
    draw.text((42,y+73),dimensions,font=font(14),fill=MUTED)
    draw.text((42,y+96),mode,font=font(14),fill=MUTED)
    byte_count=(FX/(name+'.webp')).stat().st_size
    draw.text((42,y+119),f'{byte_count:,} bytes',font=font(13),fill=MUTED)
    for theme,(x,bg,tint,opacity) in enumerate(zip((240,832),(DARK,PAPER),(MINT,AMBER),opacities)):
        size=(568,height-14)
        panel=Image.new('RGB',size,bg)
        plate=PLATES[name]
        if name=='film-grain':
            panel=softlight(panel,tile(plate,size),opacity)
            # This additional crop makes the very subtle native grain inspectable.
            inset=plate.crop((64,64,128,128)).resize((128,128),Image.Resampling.NEAREST)
            enhanced=np.asarray(inset,dtype=float)
            enhanced=np.clip(128+(enhanced-128)*4,0,255)
            panel.paste(Image.fromarray(np.uint8(enhanced)),(size[0]-144,12))
            pd=ImageDraw.Draw(panel)
            pd.text((16,16),'Native tile at 10% soft-light',font=font(14),fill=(156,180,184) if theme==0 else (237,229,216))
            pd.text((size[0]-148,144),'2× crop · contrast ×4',font=font(11),fill=(156,180,184) if theme==0 else (237,229,216))
        else:
            if name=='dust-motes':
                # Repeat a native-sized tile; the panel includes a visible tile boundary.
                surface=tile(plate,size)
                panel=screen(panel,surface,opacity,tint)
            else:
                scale=min((size[0]-32)/plate.width,(size[1]-24)/plate.height)
                render=plate.resize((round(plate.width*scale),round(plate.height*scale)),RESAMPLE)
                pos=((size[0]-render.width)//2,(size[1]-render.height)//2)
                if name=='vignette':
                    overlay=Image.new('RGBA',size,(0,0,0,0)); overlay.paste(render,pos)
                    panel=over(panel,overlay,opacity)
                else:
                    surface=Image.new('RGB',size); surface.paste(render,pos)
                    panel=screen(panel,surface,opacity,tint)
        sheet.paste(panel,(x,y))
    y+=height

# Two simple review composites: one visor point, one filing rectangle, one pool.
y+=18
draw.text((42,y),'POINT → FILING ROW / COMPOSITE',font=font(23,True),fill=TEXT)
draw.text((42,y+36),'Cone + elliptical pool + masked motes + source flare + vignette + grain. 12 px letterbox.',font=font(15),fill=MUTED)
y+=72
def mock(bg,tint,warm=False):
    size=(668,362)
    canvas=Image.new('RGB',size,bg)
    d=ImageDraw.Draw(canvas)
    ink=(150,158,153) if warm else (55,74,81)
    d.rounded_rectangle((418,66,636,298),10,outline=ink,width=1)
    for yy in (88,113,244,269):
        d.line((438,yy,603 if yy!=113 else 560,yy),fill=ink,width=2)
    d.rounded_rectangle((431,166,622,211),5,outline=(185,169,139) if warm else (66,117,106),width=1)
    # Beam width 500; generated source lies near x=1.5%, aligns to the visor point.
    cone=PLATES['beam-cone'].resize((500,188),RESAMPLE)
    beam=Image.new('RGB',size); beam.paste(cone,(70,95))
    canvas=screen(canvas,beam,.75 if warm else .60,tint)
    # Tile at 1:1 and use the cone's intensity as a smooth spatial clipping mask.
    dust=np.asarray(tile(PLATES['dust-motes'],size).convert('L'),dtype=float)
    mask=np.asarray(beam.convert('L'),dtype=float)/255
    clipped=Image.fromarray(np.uint8(np.clip(dust*np.minimum(mask*3,1),0,255)))
    canvas=screen(canvas,clipped,.50 if warm else .45,tint)
    pool=PLATES['beam-pool'].resize((230,84),RESAMPLE)
    layer=Image.new('RGB',size); layer.paste(pool,(410,147))
    canvas=screen(canvas,layer,.35 if warm else .28,tint)
    flare=PLATES['lens-flare'].resize((176,30),RESAMPLE)
    layer=Image.new('RGB',size); layer.paste(flare,(-10,174))
    canvas=screen(canvas,layer,.65 if warm else .50,tint)
    canvas=softlight(canvas,tile(PLATES['film-grain'],size),.10)
    canvas=over(canvas,PLATES['vignette'].resize(size,RESAMPLE),.24)
    # Foreground marks stay above the light layers, standing in for readable HTML.
    d=ImageDraw.Draw(canvas)
    fg=(255,238,206) if warm else (216,244,232)
    d.line((450,187,507,187),fill=fg,width=3)
    d.line((526,187,601,187),fill=fg,width=3)
    d.rectangle((0,0,667,11),fill=(0,0,0))
    d.rectangle((0,350,667,361),fill=(0,0,0))
    d.text((24,316),'VISOR POINT',font=font(11,True),fill=fg)
    d.text((446,316),'MATCHING FILING ROW',font=font(11,True),fill=fg)
    return canvas
sheet.paste(mock(DARK,MINT),(40,y))
sheet.paste(mock(PAPER,AMBER,True),(732,y))
y+=382
draw.text((42,y),'Opacity notes use dark / paper order. Grain inset is an inspection aid; all other panels use the listed runtime opacities.',font=font(13),fill=MUTED)
draw.text((42,y+23),'No lettering is baked into the textures. This contact sheet is a review artifact, not a runtime asset.',font=font(13),fill=MUTED)
sheet=sheet.crop((0,0,W,y+57))
sheet.save(FX/'contact.png',optimize=True)
print('contact.png',sheet.size,(FX/'contact.png').stat().st_size,'bytes')
```

</details>

## Verification

Visually inspected the seven built-in outputs and the finished contact sheet.
Reopened every final WebP and checked decoded dimensions, mode, byte budget,
neutrality and boundary behavior. Dust and grain have **identical opposite
edges on both axes after decoding** (maximum per-channel difference: 0). All
four non-tiled emissive effects decode to exact **RGB 0 at every outer-border
pixel**. Lossy WebP channel differences inside the light are at most 1/255.
Vignette decodes as RGBA with all RGB values 0, center **(0, 0, 0, 0)**, maximum
alpha 255 and corner alpha 252–254. There is no baked matte or checkerboard.
The grain is a flat, fine, near-neutral tile, not a paper scan or a vignette.

All generated project files belong to the authorized asset/prompt paths; no
integration code, tracked pre-existing content, commit or push was changed by
this task. No application tests were needed for standalone decorative assets.

Final texture SHA-256 values:

| File | SHA-256 |
|---|---|
| beam-cone.webp | `11069cc82307c70417c707afa2a6587c19f02be079549c31626bc66324504eea` |
| beam-pool.webp | `32c517dea8f06c1aff761782e81259b331a52faa4e8b9cfb21458de08b865cff` |
| dust-motes.webp | `6d14efdc9bd505440763701cf3412e14c2b681af6d44d87981923907fb8daf45` |
| lens-flare.webp | `29706263cec22a41cdb3eebd938acda906bfe71514cce6ad040a9d54fae61d73` |
| impact-burst.webp | `cdd5a073eeb2808d6480def0ed4cd3b31e9f01c9f784789aa81d8e8849dee94a` |
| film-grain.webp | `0ce8046dd7a612a2c1b2c373067ea669fc745058be2f601a7b5e1191a36a0662` |
| vignette.webp | `ce93f148ae0f9365772b220dd2558b15b526ac15cdb177d8971b147f7f4b0e10` |
