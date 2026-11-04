#!/usr/bin/env python3
"""Capture the local auditor scene with Playwright; no provider/SEC requests.

Host command (from the repo root, with Chromium installed for Playwright):
  PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
    uv run python scripts/capture_readme_gif.py

Omit PLAYWRIGHT_MODULE if Node can resolve playwright. The committed GIF is a
static placeholder until this command succeeds. Frames and a receipt are kept
under /tmp by default; --record-dir selects a persistent host record directory.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from http.server import ThreadingHTTPServer

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r"""
const {pathToFileURL} = require('node:url');
const {isAbsolute} = require('node:path');
const fs = require('node:fs');
(async () => {
  const name = process.env.PLAYWRIGHT_MODULE || 'playwright';
  let pw;
  try { pw = await import(isAbsolute(name) ? pathToFileURL(name).href : name); }
  catch { throw Error('Playwright unavailable. On the host set PLAYWRIGHT_MODULE to its index.mjs.'); }
  const chromium = pw.chromium || pw.default?.chromium;
  const [url, directory, countText] = process.argv.slice(1);
  const count = Number(countText);
  const installedChrome = process.env.CHROME_PATH ||
    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
     '/Applications/Chromium.app/Contents/MacOS/Chromium'].find(path => fs.existsSync(path));
  const browser = await chromium.launch({headless:true,
    ...(installedChrome ? {executablePath:installedChrome} : {})});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1,
      colorScheme:'light',reducedMotion:'no-preference'});
    const origin = new URL(url).origin;
    await page.route('**/*', route => {
      const request = route.request(), target = new URL(request.url());
      if (target.origin !== origin) return route.abort();
      if (target.pathname.startsWith('/api/')) return route.fulfill({status:503,
        contentType:'application/json',body:'{"error":"offline_capture"}'});
      return route.continue();
    });
    await page.goto(url+'?stamp-t=0', {waitUntil:'networkidle'});
    await page.waitForFunction(() => Boolean(window.__stampScene));
    await page.evaluate(() => document.fonts.ready);
    const scene = page.locator('#stamp-scene');
    const cycle = await page.evaluate(() => window.__stampScene.timing.checkable);
    for (let index=0; index<count; index++) {
      await page.evaluate(async seconds => {
        window.__stampScene.seek(seconds);
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        await Promise.all([...document.querySelectorAll('#stamp-scene img')]
          .filter(image => image.src).map(image => image.decode().catch(()=>{})));
      }, index/count*cycle);
      await scene.screenshot({path:`${directory}/frame-${String(index).padStart(3,'0')}.png`});
    }
    fs.writeFileSync(`${directory}/browser.json`,JSON.stringify({viewport:[1440,1000],
      frames:count,sceneCycleSeconds:cycle,acceleratedIntoSeconds:7,noExternalRequests:true},null,2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode=1; });
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/site/img/readme-robot.gif")
    parser.add_argument("--record-dir", type=Path)
    args = parser.parse_args()
    records = args.record_dir or Path(tempfile.mkdtemp(prefix="mcv-readme-gif-"))
    records.mkdir(parents=True, exist_ok=True)
    # Use the production Pages overlay rather than a plain docs/ HTTP server.
    spec = importlib.util.spec_from_file_location("site_preview", ROOT / "scripts/serve_site.py")
    preview = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preview)
    server = ThreadingHTTPServer(("127.0.0.1", 0), preview.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/"
    try:
        result = subprocess.run(["node", "-e", DRIVER, url, str(records.resolve()), "70"],
                                cwd=ROOT, env=os.environ.copy(), capture_output=True, text=True)
        (records / "capture.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise SystemExit(f"Capture unavailable; retained log: {records / 'capture.log'}\n{result.stderr.strip()}")
    finally:
        server.shutdown()
        server.server_close()
    frames = []
    for path in sorted(records.glob("frame-*.png")):
        with Image.open(path) as image:
            image = image.convert("RGB")
            frames.append(image.resize((720, round(image.height * 720 / image.width)), Image.Resampling.LANCZOS))
    if len(frames) != 70:
        raise SystemExit(f"Incomplete capture: {len(frames)} frames; retained {records}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    candidate = records / "candidate.gif"
    for colors in (128, 96, 64, 48, 32):
        palette = frames[0].quantize(colors=colors)
        indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
        indexed[0].save(candidate, save_all=True, append_images=indexed[1:],
                        duration=100, loop=0, optimize=True, disposal=2)
        if candidate.stat().st_size <= 3_000_000:
            break
    else:
        raise SystemExit(f"Capture exceeds 3 MB; frames retained at {records}")
    args.output.write_bytes(candidate.read_bytes())
    receipt = dict(width=720, duration_ms=7000, bytes=args.output.stat().st_size,
                   sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                   source_sha256=hashlib.sha256((ROOT / "docs/site/script.js").read_bytes()).hexdigest(),
                   method="Playwright screenshots of saved local scene; one 8 s scene cycle in a 7 s GIF",
                   no_model_or_sec_calls=True, frames=str(records))
    (records / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Captured {args.output}: 720 px, 7 s, {receipt['bytes']} bytes; record {records}")


if __name__ == "__main__":
    main()
