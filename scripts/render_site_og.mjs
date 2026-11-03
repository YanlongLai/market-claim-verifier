#!/usr/bin/env node
// Run scripts/serve_site.py first. Requires playwright-core and installed Chrome.
// PLAYWRIGHT_MODULE=/tmp/og-tools/node_modules/playwright-core/index.mjs node scripts/render_site_og.mjs
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { statSync } from 'node:fs';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true
});
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, colorScheme: 'light', deviceScaleFactor: 1 });
  await page.addInitScript(() => localStorage.setItem('market-claim-verifier-language', 'en'));
  const base = process.env.SITE_URL || 'http://127.0.0.1:8765';
  // Only local site resources may be requested; no providers, SEC, or other hosts.
  await page.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
  await page.goto(`${base}/?stamp-t=49.5#top`);
  await page.waitForFunction(() => window.__stampScene?.getState().seconds === 49.5);
  await page.addStyleTag({ url: `${base}/img/og/render-og.css` });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll('.stamp-stage img')]
      .filter(img => img.src && img.getClientRects().length)
      .map(img => img.decode().catch(() => {})));
    window.__stampScene.seek(49.5);
  });
  const path = fileURLToPath(new URL('../docs/site/img/og/og-image.png', import.meta.url));
  await page.screenshot({ path, clip: { x: 0, y: 0, width: 1200, height: 630 } });
  // Reduce channel precision only as much as needed; keep far more colors than
  // an indexed palette so the existing robot artwork retains its shading.
  execFileSync('uv', ['run', '--no-project', '--with', 'pillow==11.3.0', 'python', '-c',
    `from PIL import Image
from io import BytesIO
import sys
p=sys.argv[1]
im=Image.open(p).convert("RGB")
for step in (2, 4, 8, 16):
    data=BytesIO()
    im.point(lambda v: v//step*step).save(data, format="PNG", optimize=True)
    if data.tell() <= 300000:
        with open(p, "wb") as output: output.write(data.getvalue())
        break
else:
    raise SystemExit("PNG still exceeds 300 KB")
`, path]);
  const bytes = statSync(path).size;
  if (bytes > 300000) throw new Error(`OG image exceeds 300 KB: ${bytes} bytes`);
  console.log(`Captured real site hero at 49.5s: docs/site/img/og/og-image.png (1200×630; ${bytes} bytes)`);
} finally {
  await browser.close();
}
