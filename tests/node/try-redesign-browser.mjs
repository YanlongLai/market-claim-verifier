// Optional real-browser regression. All APIs are fixtures; external requests are blocked.
// SITE_URL=http://127.0.0.1:8769 PLAYWRIGHT_MODULE=/path/to/playwright-core/index.mjs CHROME_PATH=/path/to/chrome node tests/node/try-redesign-browser.mjs
import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const base = process.env.SITE_URL || 'http://127.0.0.1:8769';
const runId = new Date().toISOString().replace(/[:.]/g, '-');
const output = new URL(process.env.BROWSER_RECORDS || `../../docs/plans/try-redesign-20261104-records/final-implementation/browser-${runId}/`, import.meta.url);
await mkdir(output, { recursive: true });
const saved = JSON.parse(await readFile(new URL('../../docs/site/data/examples/text.json', import.meta.url), 'utf8'));
const models = { meta: 'muse-spark-1.3', baseten: 'meta-models/muse-spark-open-1026', fireworks: 'accounts/fireworks/models/muse-spark-open' };
let browser;
const results = [];
try {
  for (const width of [375, 768, 1440]) for (const language of ['en', 'zh']) for (const colorScheme of ['light', 'dark']) {
    const label = `${width}-${language}-${colorScheme}`;
    browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
    const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [], blocked = [];
    page.on('pageerror', error => errors.push(error.message));
    const rows = Array.from({ length: 50 }, (_, i) => ({ id: String(i + 1).padStart(32, '0'),
      at: new Date(Date.now() - (i + 5) * 60000).toISOString(), story: ['a', 'b', 'c'][i % 3], kind: 'text',
      provider: ['baseten', 'fireworks', 'meta'][i % 3], model: models[['baseten', 'fireworks', 'meta'][i % 3]],
      verdict: i % 3 === 1 ? null : i % 3 === 2 ? 'supported' : 'contradicted', error: i % 3 === 1 ? 'provider_error' : null,
      device: 'macOS / desktop', browser: 'Chrome', latency_ms: 15700, cost_usd: .02, input_text: saved.input.text_read }));
    const budget = { status: 'ready', day: '2026-11-04', resets_at: '2099-11-05T00:00:00Z', providers: Object.fromEntries(Object.keys(models).map(provider => [provider,
      { status: 'ready', daily_limit: 30, daily_remaining: 27.88, daily_spent: 2.12, lifetime_limit: 80, lifetime_remaining: 77.88, lifetime_spent: 2.12 }])) };
    const envelope = { ...saved, mode: 'live', receipt: { provider: 'baseten', model: models.baseten, latency_ms: 9700, cost_usd: .01, preprocessing: null } };
    let release, posted = false;
    const hold = new Promise(resolve => { release = resolve; });
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== new URL(base).origin) { blocked.push(url.origin); return route.abort(); }
      if (url.pathname === '/api/budget') return route.fulfill({ json: budget });
      if (url.pathname === '/api/history') return route.fulfill({ json: { rows } });
      if (url.pathname.startsWith('/api/history/')) return route.fulfill({ json: { ...rows[0], envelope: saved } });
      if (url.pathname.startsWith('/api/progress/')) {
        const all = [{ t_s: 0, text: 'start  baseten  text' }, { t_s: .05, text: 'model  running  step=1' },
          { t_s: 2.06, text: 'tool_call  lookup_fact  AMZN revenue Q3 2023' },
          { t_s: 2.41, text: 'tool_result  E1  143,083,000,000 USD' }, { t_s: 2.42, text: 'model  running  step=2' }];
        return route.fulfill({ json: { lines: all.slice(Number(url.searchParams.get('after'))), done: false, next: all.length } });
      }
      if (['/api/check', '/api/check-example'].includes(url.pathname)) { posted = true; await hold; return route.fulfill({ json: envelope }); }
      if (url.pathname.startsWith('/api/')) throw Error(`Unexpected API call: ${url.pathname}`);
      return route.continue();
    });
    await page.goto(base + (language === 'zh' ? '/zh/' : '/'));
    await page.locator('#live-submit:not(:disabled)').waitFor();
    await page.locator('[data-history-row]').first().waitFor();
    const checkOverflow = async state => {
      const geometry = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth,
        tryWidth: document.querySelector('#live-check').scrollWidth, tryClient: document.querySelector('#live-check').clientWidth }));
      if (width === 375) assert.ok(geometry.page <= geometry.viewport, `${label} ${state}: page overflow ${JSON.stringify(geometry)}`);
      assert.ok(geometry.tryWidth <= geometry.tryClient, `${label} ${state}: Try overflow`);
    };
    let minContrast = Infinity;
    const checkContrast = async () => {
      const measured = await page.evaluate(() => {
        const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        const rgba = value => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = value; ctx.fillRect(0, 0, 1, 1); const pixel = ctx.getImageData(0, 0, 1, 1).data; return [...pixel.slice(0, 3), pixel[3] / 255]; };
        const blend = (front, back) => front.slice(0, 3).map((v, i) => v * front[3] + back[i] * (1 - front[3]));
        const luminance = rgb => rgb.map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
        return [...document.querySelectorAll('.try-subtitle,.story-expected,.provider-name,.provider-budget,.provider-model,.history-line-two,.history-verdict,.now-idle,.terminal-status,.terminal-metrics span,.terminal-time')]
          .filter(el => el.checkVisibility() && el.textContent.trim()).map(el => {
            const chain = []; for (let parent = el; parent; parent = parent.parentElement) chain.unshift(parent);
            let background = [255, 255, 255];
            for (const parent of chain) background = blend(rgba(getComputedStyle(parent).backgroundColor), background);
            const foreground = blend(rgba(getComputedStyle(el).color), background), fg = luminance(foreground), bg = luminance(background);
            return { text: el.textContent.slice(0, 60), ratio: (Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05) };
          });
      });
      assert.ok(measured.every(item => item.ratio >= 4.5), `${label} low contrast ${JSON.stringify(measured.filter(item => item.ratio < 4.5))}`);
      minContrast = Math.min(minContrast, ...measured.map(item => item.ratio));
    };
    await checkOverflow('idle'); await checkContrast();
    await page.locator('.live-rules summary').click();
    await checkOverflow('privacy-details');
    assert.equal(await page.locator('#live-privacy').isVisible(), true);
    await page.locator('.live-rules summary').click();
    assert.equal(await page.locator('#live-idle').isVisible(), true);
    assert.equal(await page.locator('#live-idle .terminal-stages > span').count(), 6);
    assert.equal(await page.locator('[data-history-row]').count(), 6);
    assert.equal(await page.locator('.history-line-one').first().textContent(), language === 'zh' ? '故事 A · 文字' : 'Story A · Text');
    assert.ok((await page.locator('.history-when').first().textContent()).includes(language === 'zh' ? '5 分鐘前' : '5 min ago'));
    await page.locator('#history-more').click(); assert.equal(await page.locator('[data-history-row]').count(), 16);
    const targets = await page.locator('.try-layout').evaluate(el => [...el.querySelectorAll('button, summary, a, input, small[tabindex]')]
      .filter(target => target.checkVisibility()).map(target => ({ element: target.matches('input[type=radio], input[type=checkbox]') ? target.closest('label') : target, tag: target.tagName }))
      .filter(target => target.tag !== 'SMALL').map(({ element }) => ({ name: element.getAttribute('id') || element.textContent.trim(), height: element.getBoundingClientRect().height })));
    assert.ok(targets.every(target => target.height >= 44), `${label} short targets ${JSON.stringify(targets.filter(target => target.height < 44))}`);
    const chevron = await page.locator('.history-row').first().evaluate(row => { const r = row.getBoundingClientRect(), c = row.querySelector('.history-chevron').getBoundingClientRect(); return { left: c.left, right: c.right, width: c.width, rowLeft: r.left, rowRight: r.right }; });
    assert.ok(chevron.width > 0 && chevron.left >= chevron.rowLeft && chevron.right <= chevron.rowRight, `${label} chevron outside row`);
    await page.locator('#live-check').scrollIntoViewIfNeeded();
    await page.locator('.try-layout').screenshot({ path: new URL(`${label}-idle.png`, output).pathname });
    for (const kind of ['image', 'pdf', 'audio', 'video', 'text']) { await page.locator(`.input-tabs [data-input-kind=${kind}]`).click(); await checkOverflow(kind); }
    await page.locator('#live-password').fill('offline-test-password');
    await page.locator('#live-submit').click();
    await page.waitForFunction(() => document.querySelector('.terminal-lines')?.textContent.includes('step=2'));
    assert.equal(posted, true);
    assert.equal(await page.locator('.terminal-header h3').textContent(), language === 'zh' ? '執行中' : 'Running');
    assert.match(await page.locator('.terminal-clock').textContent(), /^\d+:\d{2}$/);
    assert.equal(await page.locator('#live-submit').textContent(), language === 'zh' ? '查核中…' : 'Checking…');
    assert.equal(await page.locator('.history-row.is-mine').count(), 1);
    await checkOverflow('running'); await checkContrast();
    if (width < 960) {
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await page.locator('#live-running-bar').waitFor({ state: 'visible' });
      await page.locator('#live-running-bar').click();
      await page.locator('#live-running-bar').waitFor({ state: 'hidden' });
    }
    await page.locator('#live-now').screenshot({ path: new URL(`${label}-running.png`, output).pathname });
    release();
    await page.locator('#live-form[aria-busy=false]').waitFor();
    assert.equal(await page.locator('.terminal-log').evaluate(el => el.open), false);
    assert.equal(await page.locator('.terminal-metrics > div').count(), 3);
    assert.equal(await page.locator('.terminal-stages [data-done=true]').count(), 6);
    assert.equal(await page.locator('.history-row.is-mine').count(), 0);
    assert.equal(await page.locator('#live-running-bar').isVisible(), false);
    await checkOverflow('done'); await checkContrast();
    await page.locator('#live-now').screenshot({ path: new URL(`${label}-done.png`, output).pathname });
    await page.locator('[data-history-row]').first().focus();
    await page.keyboard.press('Enter');
    await page.locator('#history-dialog-content:not([hidden])').waitFor();
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('[data-history-row]').first().evaluate(el => el === document.activeElement), true);
    assert.deepEqual(errors, []); assert.deepEqual(blocked, []);
    results.push({ width, language, colorScheme, states: ['idle', 'running', 'done'], tryNoHorizontalOverflow: true, phonePageNoHorizontalOverflow: width === 375 ? true : null, minContrast, minTarget: Math.min(...targets.map(target => target.height)), errors });
    await writeFile(new URL('results.json', output), JSON.stringify(results, null, 2) + '\n');
    await context.close(); await browser.close(); browser = null;
  }
  await writeFile(new URL('results.json', output), JSON.stringify(results, null, 2) + '\n');
  console.log(`PASS ${results.length} browser cases: EN/ZH × light/dark × 375/768/1440; Try bounds, 375 px page bounds, states, history, keyboard, contrast and touch targets`);
} finally { await browser?.close(); }
