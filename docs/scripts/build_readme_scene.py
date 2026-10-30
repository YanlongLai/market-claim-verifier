"""Capture the actual website review scene as a GitHub-compatible GIF.

uv run --with playwright python docs/scripts/build_readme_scene.py
Requires Chrome (or: uv run --with playwright playwright install chromium,
then pass --channel chromium). Uses the website dark color scheme and local saved evidence; no model API calls.
"""
import argparse
import functools
import http.server
import io
from pathlib import Path
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', default='chrome')
    args = parser.parse_args()
    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT / 'docs/site')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    frames = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=args.channel, headless=True)
            page = browser.new_page(viewport={'width': 1100, 'height': 1000}, device_scale_factor=1, color_scheme='dark')
            page.goto(f'http://127.0.0.1:{server.server_port}/?stamp-t=0')
            page.wait_for_function('!!window.__stampScene')
            page.evaluate('document.fonts.ready')
            scene = page.locator('#stamp-scene')
            scene.scroll_into_view_if_needed()
            page.evaluate('document.querySelectorAll("#stamp-scene img").forEach(i => i.loading = "eager")')
            page.wait_for_function('Array.from(document.querySelectorAll("#stamp-scene img")).every(i => i.complete)')
            # Opening saved examples, including the input, evidence and verdict.
            for index in range(128):
                page.evaluate('(t) => window.__stampScene.seek(t)', index / 8)
                frames.append(Image.open(io.BytesIO(scene.screenshot())).convert('RGB'))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    # Shared palette preserves stable text and colors across all frames.
    palette_sheet = Image.new('RGB', (frames[0].width, frames[0].height * 8))
    for index, frame in enumerate(frames[::16]):
        palette_sheet.paste(frame, (0, index * frame.height))
    palette = palette_sheet.quantize(colors=256)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    output = ROOT / 'docs/figures/review-process-dark-v1.gif'
    indexed[0].save(output, save_all=True, append_images=indexed[1:],
                    duration=[120, 130] * 64, loop=0, optimize=True)
    with Image.open(output) as gif:
        assert gif.n_frames > 100 and gif.info['loop'] == 0
        duration = 0
        for i in range(gif.n_frames):
            gif.seek(i)
            duration += gif.info['duration']
        assert duration == 16000
        print(f'{output.relative_to(ROOT)}: {gif.size}, {gif.n_frames} frames, {output.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
