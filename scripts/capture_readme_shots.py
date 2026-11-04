#!/usr/bin/env python3
"""Capture English README screenshots from the local Pages preview.

No API credentials, model calls, synthesis or SEC requests. Playwright renders
committed saved data. Requires Node, Playwright/Chromium and Pillow (uv sync).

Host commands:
  npm install --prefix /tmp/mcv-readme-browser --cache /tmp/mcv-readme-npm playwright
  /tmp/mcv-readme-browser/node_modules/.bin/playwright install chromium
  PLAYWRIGHT_MODULE=/tmp/mcv-readme-browser/node_modules/playwright/index.mjs \
    uv run python scripts/capture_readme_shots.py

Use CHROME_PATH for an existing Chromium executable. A failed browser launch
leaves a failure receipt and exits nonzero; it never creates placeholder PNGs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import uuid
from http.server import ThreadingHTTPServer

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r"""
const { pathToFileURL } = require('node:url');
const { isAbsolute } = require('node:path');
const fs = require('node:fs');
(async () => {
  const name = process.env.PLAYWRIGHT_MODULE || 'playwright';
  let pw;
  try { pw = await import(isAbsolute(name) ? pathToFileURL(name).href : name); }
  catch { throw Error('Playwright unavailable; follow the host commands in scripts/capture_readme_shots.py.'); }
  const chromium = pw.chromium || pw.default?.chromium;
  const [url, directory] = process.argv.slice(1);
  const browser = await chromium.launch({headless:true,
    ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
  const blocked = [], errors = [];
  try {
    const page = await browser.newPage({viewport:{width:1600,height:1100},deviceScaleFactor:1,
      colorScheme:'light',reducedMotion:'reduce'});
    page.on('pageerror', e => errors.push(e.message));
    const origin = new URL(url).origin;
    await page.route('**/*', route => {
      const target = new URL(route.request().url());
      if (target.origin !== origin) { blocked.push(target.origin); return route.abort(); }
      // Read-only budget/history come through the preview proxy; every check route is refused.
      if (target.pathname === '/api/budget' || target.pathname === '/api/history') return route.continue();
      if (target.pathname.startsWith('/api/')) return route.fulfill({status:503,
        contentType:'application/json',body:'{"error":"offline_capture"}'});
      return route.continue();
    });
    await page.goto(url, {waitUntil:'networkidle'});
    await page.evaluate(() => document.fonts.ready);
    const storyA = page.locator('[data-story-slot="0"]');
    await storyA.click();
    await page.locator('#example-saved').waitFor({state:'visible'});
    await page.waitForFunction(() => document.querySelector('#example-saved')?.disabled === false);
    if (await storyA.getAttribute('aria-pressed') !== 'true') throw Error('Story A is not selected');
    // Capture the real section at the 1600 px viewport; no DOM/CSS restyling.
    await page.locator('#live-check').screenshot({path:`${directory}/try-story-a.png`,animations:'disabled'});
    await page.locator('#example-saved').click();
    const result = page.locator('#live-result');
    await result.waitFor({state:'visible'});
    await result.locator('del').first().waitFor({state:'visible'});
    const text = await result.innerText();
    if (!text.includes('416.2') || !text.includes('102.5')) throw Error('Expected retained Apple correction is absent');
    if (!await result.locator('a[href^="https://www.sec.gov/"]').count()) throw Error('SEC citations are absent');
    // Include the result and its context, keeping the viewport's exact width.
    const box = await result.boundingBox();
    const scrollY = await page.evaluate(() => window.scrollY);
    await page.screenshot({path:`${directory}/corrected-draft.png`,animations:'disabled',fullPage:true,
      clip:{x:0,y:box.y+scrollY,width:1600,height:Math.min(box.height,1500)}});
    if (errors.length) throw Error(`Browser errors: ${errors.join('; ')}`);
    fs.writeFileSync(`${directory}/browser.json`,JSON.stringify({viewport:[1600,1100],
      story:'A',kind:'text',provider:'baseten',mode:'recorded',api:'blocked with 503',
      externalRequests:'blocked',blockedOrigins:[...new Set(blocked)],pageErrors:errors,
      savedResult:'/data/examples/text.json',browserVersion:browser.version()},null,2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack || error.message); process.exitCode=1; });
"""


def optimize(source: Path, target: Path) -> dict:
    """Lossless PNG first; use a palette only when the byte cap requires it."""
    with Image.open(source) as image:
        image = image.convert('RGB')
        if image.width != 1600:
            raise ValueError(f'Capture width must be 1600, got {image.width}')
        image.save(target, optimize=True)
        palette = None
        for colors in (256, 192, 128, 96, 64):
            if target.stat().st_size <= 400_000:
                break
            image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).save(target, optimize=True)
            palette = colors
        if target.stat().st_size > 400_000:
            raise ValueError(f'PNG exceeds 400 KB: {target}')
        return {'path': str(target.relative_to(ROOT)), 'width': image.width, 'height': image.height,
                'bytes': target.stat().st_size, 'palette_colors': palette,
                'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-dir', type=Path,
                        default=ROOT / 'docs/evidence/readme-v3-2026-11-04/screenshots')
    args = parser.parse_args()
    records = args.record_dir / (datetime.now(timezone.utc).strftime('run-%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    records.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='mcv-readme-shots-') as temp:
        spec = importlib.util.spec_from_file_location('preview', ROOT / 'scripts/serve_site.py')
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        server = ThreadingHTTPServer(('127.0.0.1', 0), preview.Handler)
        # Budget and public history come from the production API so the captured Try
        # section shows what a judge sees; saved results still render from retained data.
        server.docs_root, server.proxy_api = preview.ROOT, os.environ.get('README_SHOT_API', 'https://hackathon.dappgo.com')
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            result = subprocess.run(['node', '-e', DRIVER, f'http://127.0.0.1:{server.server_port}/', temp],
                                    cwd=ROOT, env=os.environ.copy(), capture_output=True, text=True)
        finally:
            server.shutdown()
            server.server_close()
        (records / 'capture.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            (records / 'failure.json').write_text(json.dumps({
                'status': 'failed', 'exit_code': result.returncode,
                'host_commands': 'See scripts/capture_readme_shots.py; no screenshots fabricated.'}, indent=2)+'\n')
            print(result.stderr.strip().splitlines()[0])
            print(f'Failure retained in {records}')
            return result.returncode
        output = ROOT / 'docs/site/img/readme'
        output.mkdir(parents=True, exist_ok=True)
        images = [optimize(Path(temp) / name, output / name)
                  for name in ('try-story-a.png', 'corrected-draft.png')]
        receipt = json.loads((Path(temp) / 'browser.json').read_text())
        receipt['images'] = images
        receipt['saved_result_sha256'] = hashlib.sha256((ROOT / 'docs/site/data/examples/text.json').read_bytes()).hexdigest()
        (records / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        for readme in ('README.md', 'README.zh-TW.md'):
            path = ROOT / readme
            text = path.read_text()
            for name in ('try-story-a', 'corrected-draft'):
                marker = f'<!-- readme-shot:{name} -->'
                if marker not in text:
                    raise ValueError(f'Missing screenshot marker in {readme}: {name}')
                before, after = text.split(marker, 1)
                caption = ({'try-story-a': 'Try section with story A selected',
                            'corrected-draft': 'Rendered saved result with the corrected draft and filing citations'}
                           if readme == 'README.md' else
                           {'try-story-a': '選取故事 A 的試用區',
                            'corrected-draft': '已儲存結果的修正版草稿與申報引用'})[name]
                after = after.split('\n', 2)
                text = before + marker + '\n' + f'![{caption}](docs/site/img/readme/{name}.png)' + '\n' + after[2]
            text = text.replace('The host captures will render retained data locally; they do not run a new production check.',
                                'The screenshots show local rendering of retained data, not a new production run.')
            text = text.replace('主機截圖會在本機呈現保留資料，不會執行新的正式環境查核。',
                                '截圖是保留資料的本機呈現，不是新的正式環境執行。')
            path.write_text(text)
        for image in images:
            print(f"PASS {image['path']}: {image['width']} px, {image['bytes']} bytes")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
