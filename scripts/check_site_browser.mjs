#!/usr/bin/env node
// Browser QA for the Pages preview. Requires playwright-core + installed Chrome.
// SITE_URL=http://127.0.0.1:8765 SHOTS_DIR=/tmp/site-shots PLAYWRIGHT_MODULE=/tmp/og-tools/node_modules/playwright-core/index.mjs node scripts/check_site_browser.mjs
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const base = process.env.SITE_URL || 'http://127.0.0.1:8765';
const out = resolve(process.env.SHOTS_DIR || '/tmp/hk-polish-shots');
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
const allowed = new Set([new URL(base).origin, 'https://fonts.googleapis.com', 'https://fonts.gstatic.com', 'https://static.cloudflareinsights.com', 'https://cloudflareinsights.com']);

// Installed before page scripts: measure the first painted scene and actual text,
// accounting for hidden ancestors, opacity, viewport clipping, and nonempty content.
function monitor(language) {
  localStorage.setItem('market-claim-verifier-language', language);
  window.__qa = { timing: {}, violations: [], firstScene: null };
  addEventListener('securitypolicyviolation', e => {
    const violation = { directive: e.effectiveDirective, blocked: e.blockedURI };
    window.__qa.violations.push(violation);
    window.__recordCSP(violation);
  });
  function visible(el) {
    if (!el?.textContent.trim()) return false;
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) < .1) return false;
    }
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight;
  }
  function tick() {
    const post = [...document.querySelectorAll('#stamp-track .stamp-claim')].some(visible);
    const filing = [...document.querySelectorAll('.stamp-filing-content .stamp-passage-details')].some(visible);
    for (const [key, shown] of Object.entries({ post, filing })) if (!window.__qa.timing[key] && shown) window.__qa.timing[key] = Math.round(performance.now());
    if (!window.__qa.firstScene && document.querySelector('#stamp-scene')?.hidden === false) window.__qa.firstScene = { ms: Math.round(performance.now()), post, filing };
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

async function targets(page) {
  return page.evaluate(() => [...document.querySelectorAll('a[href],button,summary,input,select')].filter(el => {
    if (el.closest('.is-sr-only,[inert]') || !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 && !el.classList.contains('skip-link');
  }).map(el => ({ text: (el.textContent || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 70), height: Math.round(el.getBoundingClientRect().height * 100) / 100 })));
}

async function run(width, language, explorer) {
  const label = `${explorer ? 'explorer' : 'home'}-${width}-${language}`;
  const ctx = await browser.newContext({ viewport: { width, height: width === 375 ? 812 : 900 }, colorScheme: 'light', deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = [], failed = [], violations = [], resources = new Set();
  await page.exposeFunction('__recordCSP', violation => violations.push(violation));
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('requestfailed', r => failed.push({ url: r.url(), error: r.failure()?.errorText }));
  page.on('response', r => { if (r.status() >= 400) errors.push(`HTTP ${r.status()} ${r.url()}`); });
  page.on('request', r => resources.add(`${r.resourceType()} ${new URL(r.url()).origin}`));
  await page.route('**/*', route => allowed.has(new URL(route.request().url()).origin) ? route.continue() : route.abort());
  await page.addInitScript(monitor, language);
  const path = explorer ? `/explorer/${language === 'zh' ? 'index.zh.html' : ''}` : '/';
  const response = await page.goto(base + path, { waitUntil: 'domcontentloaded' });
  assert.ok(response.headers()['content-security-policy']?.includes("frame-ancestors 'none'"));
  if (explorer) await page.waitForFunction(() => document.querySelector('#count')?.textContent.includes('357'));
  else await page.waitForFunction(() => window.__qa.firstScene);
  const first = await page.evaluate(() => ({ ...window.__qa, overflow: document.documentElement.scrollWidth > innerWidth }));
  await page.screenshot({ path: `${out}/${label}-first.png` });
  await page.waitForTimeout(Math.max(0, 8000 - await page.evaluate(() => performance.now())));
  await page.screenshot({ path: `${out}/${label}-8s.png` });
  await page.screenshot({ path: `${out}/${label}-full.png`, fullPage: true });
  const result = { label, first, after8s: await page.evaluate(() => ({ ...window.__qa, overflow: document.documentElement.scrollWidth > innerWidth, inlineScripts: document.querySelectorAll('script:not([src])').length, inlineStyles: document.querySelectorAll('style').length, styleAttributes: document.querySelectorAll('[style]').length })), resources: [...resources].sort(), errors, failed };
  result.localRoutes = await page.evaluate(() => [...new Set([...document.querySelectorAll('[href],[src]')].flatMap(el => ['href', 'src'].flatMap(attr => {
    const raw = el.getAttribute(attr);
    if (!raw || raw.startsWith('#')) return [];
    const url = new URL(raw, location.href);
    return url.origin === location.origin ? [url.pathname] : [];
  })))].sort());
  const routeChecks = await Promise.allSettled(result.localRoutes.map(async path => {
    const response = await ctx.request.head(base + path);
    assert.equal(response.status(), 200, `${label} real route ${path}`);
  }));
  for (const item of routeChecks) if (item.status === 'rejected') throw item.reason;
  assert.equal(first.overflow, false, `${label} first overflow`);
  assert.equal(result.after8s.overflow, false, `${label} overflow`);
  if (width === 375) {
    const sizes = await targets(page);
    result.targets = { count: sizes.length, minHeight: Math.min(...sizes.map(x => x.height)), small: sizes.filter(x => x.height < 43.99) };
    assert.deepEqual(result.targets.small, [], `${label} small targets`);
  }
  if (!explorer) {
    assert.ok(first.firstScene.post && first.firstScene.filing, `${label} first scene is populated`);
    for (let step = 1; step <= 4; step++) {
      await page.locator('.stamp-step').nth(step - 1).click();
      assert.equal(await page.evaluate(() => window.__stampScene.getState().step), step);
      assert.equal(await page.locator('#stamp-pause').getAttribute('aria-pressed'), 'true');
    }
    await page.locator('#stamp-pause').click();
    assert.equal(await page.locator('#stamp-scene').getAttribute('data-running'), 'true');
    await page.locator('#stamp-pause').click();
    const paused = await page.evaluate(() => window.__stampScene.getState().seconds);
    await page.waitForTimeout(100);
    assert.equal(await page.evaluate(() => window.__stampScene.getState().seconds), paused);
    await page.locator('.claim-filing-trigger').first().click();
    assert.equal(await page.locator('#filing-dialog').evaluate(el => el.open), true);
    assert.ok((await page.locator('#filing-dialog-title').textContent()).trim());
    if (width === 375) {
      result.dialogSmallTargets = (await targets(page)).filter(x => x.height < 43.99);
      assert.deepEqual(result.dialogSmallTargets, []);
    }
    await page.locator('#filing-dialog-close').click();
    for (const seconds of [0, 12.94, 25.5, 33.5, 49.5]) {
      await page.goto(`${base}/?stamp-t=${seconds}#top`, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(t => window.__stampScene?.getState().seconds === t, seconds);
      assert.equal(await page.locator('#stamp-pause').getAttribute('aria-pressed'), 'true');
    }
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.waitForFunction(() => document.querySelector('#stamp-scene').dataset.animated === 'false');
    assert.equal(await page.locator('.stamp-stage').isVisible(), false);
    assert.equal(await page.locator('#stamp-static-list').isVisible(), true);
    result.reducedMotion = 'static list visible; decorative stage hidden';
    if (width === 375) {
      result.reducedMotionSmallTargets = (await targets(page)).filter(x => x.height < 43.99);
      assert.deepEqual(result.reducedMotionSmallTargets, []);
    }
    await page.emulateMedia({ reducedMotion: 'no-preference', colorScheme: 'dark' });
    await page.screenshot({ path: `${out}/${label}-dark-seek.png` });
    result.seekAndPlayback = 'steps 1–4, pause/resume, and 0/12.94/25.5/33.5/49.5s seek passed';
    const other = language === 'en' ? 'zh' : 'en';
    await page.locator(`[data-language="${other}"]`).click();
    assert.equal(await page.title(), other === 'en' ? 'Market claim verifier · DappGo' : '財經說法查核 · DappGo');
  } else {
    await page.locator('#f-q').fill('G0119');
    await page.waitForFunction(() => document.querySelector('#count').textContent.startsWith('1 / 357'));
    await page.locator('#f-q').fill('');
    await page.waitForFunction(() => document.querySelector('#count').textContent.startsWith('357 / 357'));
    result.filtering = 'claim search narrows to 1 / 357 and restores all 357';
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.screenshot({ path: `${out}/${label}-dark.png` });
  }
  result.allViolations = violations;
  assert.deepEqual(result.after8s.violations, [], `${label} CSP`);
  assert.deepEqual(result.allViolations, [], `${label} interaction CSP`);
  assert.deepEqual(errors, [], `${label} console errors`);
  assert.deepEqual(failed, [], `${label} failed requests`);
  await ctx.close();
  return result;
}

const results = [];
try {
  // Two concurrent pages keep measurements repeatable and avoid stressing the
  // local server with four copies of the complete robot asset set at once.
  for (const explorer of [false, true]) for (const width of [1440, 375]) {
    const batch = await Promise.allSettled(['en', 'zh'].map(lang => run(width, lang, explorer)));
    for (let i = 0; i < batch.length; i++) {
      const item = batch[i];
      if (item.status === 'fulfilled') {
        results.push(item.value);
        console.log(`PASS ${item.value.label}: first + 8s screenshots; no overflow, CSP violations, console errors, or failed requests${item.value.targets ? `; targets ≥${item.value.targets.minHeight}px` : ''}`);
      } else {
        results.push({ width, language: ['en', 'zh'][i], explorer, error: item.reason.stack });
        console.error(item.reason.stack);
        process.exitCode = 1;
      }
    }
  }
  const ctx = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 375, height: 812 } });
  const page = await ctx.newPage();
  await page.goto(base);
  assert.equal(await page.locator('#stamp-scene').isVisible(), false);
  assert.equal(await page.locator('[data-ui]:visible').count(), 0);
  assert.ok((await page.locator('#filing-dialog-title').textContent()).trim());
  await page.screenshot({ path: `${out}/home-375-noscript.png` });
  await ctx.close();
  const check = await browser.newContext();
  const missing = await check.request.get(`${base}/missing-page`);
  assert.equal(missing.status(), 404);
  assert.ok((await missing.text()).includes('Page not found.'));
  await check.close();
  console.log('PASS no-JS progressive enhancement, static dialog heading, and real HTTP 404');
} finally {
  await writeFile(`${out}/browser-results.json`, JSON.stringify(results, null, 2) + '\n');
  await browser.close();
}
