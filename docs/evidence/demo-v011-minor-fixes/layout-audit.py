"""Offline source-box/font audit; this is not a browser screenshot or encoded-film review."""
import json
from pathlib import Path
import subprocess

from PIL import ImageFont

folder = Path(__file__).resolve().parent
pages = json.loads(subprocess.check_output(['node',str(folder/'layout-audit.mjs')], text=True))
fonts = ['/System/Library/Fonts/SFNS.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf']
rows = []
for page in pages:
    for box in page['boxes']:
        assert box['size'] >= 56, box
        assert box['x'] >= 64 and box['x']+box['w'] <= 1856, box
        assert box['y'] >= 64 and box['y']+box['h'] <= 816, box
        assert box['size']*1.2 <= box['h'], box
        for path in fonts:
            font = ImageFont.truetype(path,box['size'])
            width = font.getlength(box['text'])
            assert width <= box['w'], (box,path,width)
            rows.append(dict(t=page['t'],text=box['text'],font=Path(path).name,
                size_px=box['size'],text_width_px=round(width,3),box_width_px=box['w'],
                bottom_px=box['y']+box['h'],playback_480_size_px=box['size']/4))
record = dict(method='Actual motion.js boxes; Pillow SFNS/Arial advances and CSS line-height. '
              'No browser/encoded-film or caption-compositor review.',
              pages=pages, font_checks=rows, passed=True)
(folder/'layout-audit.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
print(f'PASS {len(pages)} aggregate pages, {len(rows)} font/box checks; labels >=14 px at 480 px playback; boxes end <=816.')
