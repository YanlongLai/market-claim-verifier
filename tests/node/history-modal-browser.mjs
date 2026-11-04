// Browser regression for the saved-check modal. All API responses are fixtures.
// SITE_URL=http://127.0.0.1:8767 PLAYWRIGHT_MODULE=/path/to/playwright-core/index.mjs node tests/node/history-modal-browser.mjs
import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const base = process.env.SITE_URL || 'http://127.0.0.1:8767';
const out = new URL('./history-modal-records/browser/', import.meta.url);
await mkdir(out, { recursive: true });
const saved = JSON.parse(await readFile(new URL('../../docs/site/data/examples/text.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
const results = [];
try {
  for (const width of [375, 768, 1440]) for (const language of ['en', 'zh']) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const record = { id: 'a'.repeat(32), at: '2026-11-03T17:05:00.000Z', device: 'macOS / desktop', browser: 'Chrome', story: 'a', kind: 'text',
      provider: 'baseten', model: 'meta-models/muse-spark-open-1026', verdict: 'contradicted', input_text: saved.input.text_read, cost_usd: .01, latency_ms: 1200 };
    let hold = null, detailReads = 0;
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (path === '/api/history') return route.fulfill({ json: { rows: [record] } });
      if (path === `/api/history/${record.id}`) {
        detailReads++;
        if (hold) await hold;
        return route.fulfill({ json: { ...record, envelope: saved } });
      }
      if (path === '/api/budget') return route.fulfill({ json: { status: 'unavailable' } });
      throw Error(`Unexpected API call: ${path}`);
    });
    await page.goto(base + (language === 'zh' ? '/zh/' : '/'));
    const row = page.locator('[data-history-row]');
    await row.waitFor();
    await row.focus();
    let release;
    hold = new Promise(resolve => release = resolve);
    await row.press('Space');
    const dialog = page.locator('#history-dialog');
    await dialog.waitFor({ state: 'visible' });
    assert.equal(await page.locator('#history-dialog-close').evaluate(el => el === document.activeElement), true);
    assert.equal(await page.locator('#history-dialog-edit').isDisabled(), true);
    assert.equal(await page.evaluate(() => document.body.style.overflow), 'hidden');
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.locator('#history-dialog-close').evaluate(el => el === document.activeElement), true);
    release(); hold = null;
    await page.locator('#history-dialog-result .live-proof').waitFor();
    assert.equal(await page.locator('#history-dialog-input').textContent(), saved.input.text_read);
    for (const selector of ['.trace-verdict', '.live-corrections', '.live-proof', '.live-receipt']) assert.equal(await dialog.locator(selector).count(), 1, selector);
    await page.locator('#history-dialog-close').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('#history-dialog-input').evaluate(el => el === document.activeElement), true);
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.locator('#history-dialog-close').evaluate(el => el === document.activeElement), true);
    const geometry = await dialog.evaluate(el => {
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height, screenWidth: innerWidth, screenHeight: innerHeight,
        overflow: el.scrollWidth > el.clientWidth, targets: [...el.querySelectorAll('footer button')].map(button => button.getBoundingClientRect().height) };
    });
    assert.equal(geometry.overflow, false);assert.ok(geometry.targets.every(height => height >= 44));
    if (width === 375) { assert.equal(geometry.width, width); assert.equal(geometry.height, 900);assert.equal(geometry.x, 0);assert.equal(geometry.y, 0); }
    await page.screenshot({ path: new URL(`${width}-${language}.png`, out).pathname });
    await page.keyboard.press('Escape');
    assert.equal(await dialog.isVisible(), false);
    assert.equal(await row.evaluate(el => el === document.activeElement), true);
    assert.equal(await page.evaluate(() => document.body.style.overflow), '');
    await row.press('Enter');await page.locator('#history-dialog-result .live-proof').waitFor();
    if (width !== 375) {
      await page.mouse.click(2, 2);assert.equal(await dialog.isVisible(), false);
      assert.equal(await row.evaluate(el => el === document.activeElement), true);
      await row.click();await page.locator('#history-dialog-result .live-proof').waitFor();
    }
    await page.locator('#history-dialog-edit').click();
    assert.equal(await dialog.isVisible(), false);
    assert.equal(await page.locator('#live-input').inputValue(), saved.input.text_read);
    assert.equal(await page.locator('#live-input').evaluate(el => el === document.activeElement), true);
    assert.ok(detailReads >= 2);assert.deepEqual(errors, []);
    results.push({ width, language, detailReads, geometry, errors });
    await context.close();
  }
  await writeFile(new URL('results.json', out), JSON.stringify(results, null, 2) + '\n');
  console.log(`PASS native dialog, keyboard/focus, backdrop, scroll lock, edit, renderer and geometry: ${results.length} EN/zh viewport cases`);
} finally { await browser.close(); }
