/** All footage comes from the live public site. Selectors are checked before recording actions. */
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {launch, restrictNetwork, isPublicProjectURL, playwright} from './browser.mjs';

const cursorCSS = `
  html, #filing-dialog-body {scroll-behavior:auto!important;}
  #demo-cursor {position:fixed;width:20px;height:20px;border-radius:50%;background:#3ddc97;
    box-shadow:0 0 0 4px #111a2090,0 0 0 7px #fff9;pointer-events:none;z-index:2147483647;
    left:-100px;top:-100px;transform:translate(-50%,-50%);}
  #demo-cursor.click {animation:demo-click .5s ease-out;}
  @keyframes demo-click {0% {box-shadow:0 0 0 4px #111a2090,0 0 0 8px #3ddc97;}
    100% {box-shadow:0 0 0 4px #111a2090,0 0 0 30px #3ddc9700;}}
  .demo-emphasis {outline:5px solid #ff6b6b!important;outline-offset:8px;
    box-shadow:0 0 0 15px #ff6b6b14!important;transition:outline-color .4s,box-shadow .4s;}
  .demo-claim-current {outline:2px solid #7bd1a499;outline-offset:4px;}
  /* Fit all three providers between the top label and the bottom subtitles. */
  html:is([data-demo-focus="#chart"], [data-demo-focus="#results"]) #chart {
    max-width:none;margin-top:0;gap:18px;}
  html:is([data-demo-focus="#chart"], [data-demo-focus="#results"]) .chart-row {padding:14px 20px;}
  html:is([data-demo-focus="#chart"], [data-demo-focus="#results"]) .chart-provider {margin-bottom:10px;}
  html:is([data-demo-focus="#chart"], [data-demo-focus="#results"]) .chart-bar-line {
    grid-template-columns:225px minmax(120px,1fr) 52px;}
  html:is([data-demo-focus="#chart"], [data-demo-focus="#results"]) .chart-bar-line + .chart-bar-line {margin-top:12px;}
  .demo-chart-emphasis {outline:2px solid #9abac180;outline-offset:5px;border-radius:2px;}
  html[data-demo-emphasis="with-checks"] .demo-chart-emphasis {outline-color:#7bd1a499;}
  html[data-demo-focus="#results"] #posthoc-rerun {max-width:none;}
  /* Give the three verdicts the full content width, preserving their live text. */
  html:is([data-demo-focus="verdicts-en"], [data-demo-focus="filing-modal"]) .example-grid {
    grid-template-columns:minmax(0,1fr);}
  html:is([data-demo-focus="verdicts-en"], [data-demo-focus="filing-modal"]) .post-panel {display:none;}
  html:is([data-demo-focus="verdicts-en"], [data-demo-focus="filing-modal"]) .claim-card {padding:16px 22px;}
  html:is([data-demo-focus="verdicts-en"], [data-demo-focus="filing-modal"]) .claim-text {max-width:none;font-size:1.125rem;}
  html:is([data-demo-focus="verdicts-en"], [data-demo-focus="filing-modal"]) .claim-source {max-width:none;font-size:1rem;}
  /* The modal's row and highlighted value fill the safe central band. */
  html[data-demo-focus="filing-modal"] #filing-dialog {
    width:min(1100px,calc(100% - 128px));max-width:none;
    height:calc(100dvh - 260px);max-height:none;margin:120px auto 140px;}
  html[data-demo-focus="filing-modal"] .filing-dialog-shell {height:100%;max-height:100%;}
  html[data-demo-focus="filing-modal"] .filing-dialog-head {padding:14px 22px;}
  html[data-demo-focus="filing-modal"] .filing-dialog-head h2 {max-width:none;font-size:1.4rem;}
  html[data-demo-focus="filing-modal"] #filing-dialog-body {padding:14px 22px 20px;gap:14px;}
  html[data-demo-focus="filing-modal"] .filing-excerpt-table {font-size:1rem;}
  html[data-demo-focus="filing-modal"] .filing-excerpt-table td.is-fact strong {font-size:1.35rem;}
`;

/** Browser options are derived from the storyboard job, with no capture defaults here. */
export function captureContextOptions(config) {
  const {viewport, scale, color_scheme} = config.capture;
  const dimensions = {width:viewport[0], height:viewport[1]};
  return {viewport:dimensions, screen:{...dimensions}, deviceScaleFactor:scale, colorScheme:color_scheme,
    reducedMotion:'no-preference', serviceWorkers:'block',
    recordVideo:{dir:path.join(path.dirname(config.output), 'raw'),
      size:{width:config.resolution[0], height:config.resolution[1]}}};
}

/** The only scroll primitive: a deterministic eased animation, including the dialog scroller. */
async function scrollTo(page, selector, duration = 1300, container = null, offset = 118) {
  await page.locator(selector).first().waitFor({state: 'visible'});
  await page.evaluate(async ({selector, duration, container, offset}) => {
    const target = document.querySelector(selector);
    const scroller = container ? document.querySelector(container) : document.scrollingElement;
    if (!target || !scroller) throw new Error(`Missing scroll target ${selector}`);
    const start = scroller.scrollTop;
    const bounds = scroller.getBoundingClientRect();
    const top = target.getBoundingClientRect().top;
    const requested = start + top - (container ? bounds.top : 0) - offset;
    const finish = Math.max(0, Math.min(requested, scroller.scrollHeight-scroller.clientHeight));
    const began = performance.now();
    await new Promise(resolve => {
      function frame(now) {
        const t = Math.min(1, (now-began)/duration);
        const eased = t < .5 ? 4*t*t*t : 1-Math.pow(-2*t+2, 3)/2;
        scroller.scrollTop = start + (finish-start)*eased;
        if (t < 1) requestAnimationFrame(frame); else resolve();
      }
      requestAnimationFrame(frame);
    });
  }, {selector, duration, container, offset});
}

async function click(page, locator) {
  await locator.waitFor({state: 'visible'});
  const box = await locator.boundingBox();
  const viewport = page.viewportSize();
  if (!box || box.x < 0 || box.x + box.width > viewport.width || box.y < 0 || box.y + box.height > viewport.height) {
    throw new Error('Click target must already be on screen; use an eased scroll first.');
  }
  const x = box.x+box.width/2, y = box.y+box.height/2;
  await page.mouse.move(x, y, {steps: 18});
  await page.evaluate(({x,y}) => {
    const dot = document.querySelector('#demo-cursor');
    dot.style.left = `${x}px`; dot.style.top = `${y}px`;
    dot.classList.remove('click'); void dot.offsetWidth; dot.classList.add('click');
  }, {x,y});
  await page.mouse.click(x, y);
  await page.waitForLoadState('networkidle');
}

async function ready(page, focus) {
  await page.waitForFunction(() => document.documentElement.lang === 'en');
  await page.waitForFunction(() => document.querySelectorAll('#claim-list .claim-card').length === 6);
  await page.locator('#post-text mark').first().waitFor({state:'visible'});
  if (focus === '#chart' || focus === '#results') {
    await page.waitForFunction(() => document.querySelectorAll('#chart .chart-row').length === 3);
  }
  if (focus === '#results') {
    await page.locator('#posthoc-rerun').waitFor({state:'visible'});
    await page.waitForFunction(() => document.querySelectorAll('#posthoc-rows tr').length === 3);
  }
}

/** Fail before saving a shot whose key content would sit under captions or outside the frame. */
async function assertFramed(page, selector) {
  const boxes = await page.locator(selector).evaluateAll(nodes => nodes.map(node => {
    const {x,y,width,height} = node.getBoundingClientRect();
    return {x,y,width,height};
  }));
  const viewport = page.viewportSize();
  if (!boxes.length || boxes.some(box => box.width <= 0 || box.height <= 0 || box.x < 32
      || box.x + box.width > viewport.width - 32 || box.y < 112 || box.y + box.height > viewport.height - 140)) {
    throw new Error(`Capture focus does not fit between the captions: ${selector}`);
  }
}

async function verdictCards(page) {
  const cards = page.locator('#claim-list .claim-card');
  const amazon = cards.filter({hasText: 'Amazon'}).first();
  const nvidia = cards.filter({hasText: '$60.9 billion'}).first();
  const tesla = cards.filter({hasText: /Tesla/}).first();
  for (const [name, locator] of [['amazon',amazon], ['nvidia',nvidia], ['tesla',tesla]]) {
    if (await locator.count() !== 1) throw new Error('Required Amazon / NVIDIA / Tesla claim is missing.');
    await locator.evaluate((node, name) => node.setAttribute(`data-demo-${name}`, ''), name);
  }
  return {amazon, nvidia, tesla};
}

export async function prepare(page, config) {
  const {focus, emphasis} = config;
  await page.evaluate(({focus, emphasis}) => {
    document.documentElement.setAttribute('data-demo-focus', focus);
    document.documentElement.setAttribute('data-demo-emphasis', emphasis || '');
  }, {focus, emphasis});
  if (focus === 'hero') await scrollTo(page, '#hero-title', 800, null, 128);
  if (focus === '#chart' || focus === '#results') {
    if (!['without', 'with-checks'].includes(emphasis)) throw new Error('A chart shot requires a bar emphasis.');
    const bars = page.locator(`#chart .bar-fill.is-${emphasis}`);
    if (await bars.count() !== 3) throw new Error('Expected one highlighted bar per provider.');
    await bars.evaluateAll(nodes => nodes.forEach(node => node.closest('.chart-bar-line').classList.add('demo-chart-emphasis')));
    await scrollTo(page, '#chart', 800, null, 128);
    await assertFramed(page, '#chart');
  }
  if (['example-en','example-zh'].includes(focus)) await scrollTo(page, '#example-title', 800, null, 128);
  if (focus === 'verdicts-en') {
    await verdictCards(page);
    await scrollTo(page, '[data-demo-amazon]', 800, null, 128);
    await assertFramed(page, '[data-demo-amazon], [data-demo-nvidia], [data-demo-tesla]');
  }
  if (focus === 'filing-modal') await scrollTo(page, '#claim-list .claim-card:first-child', 800, null, 128);
}

export async function perform(page, config, seconds) {
  const {focus} = config;
  const start = performance.now();
  const waitUntil = async fraction => {
    const remaining = fraction*seconds*1000-(performance.now()-start);
    if (remaining > 0) await page.waitForTimeout(remaining);
  };
  const smoothMs = Math.min(1800, seconds*1000*.10);
  if (focus === 'hero' || focus === '#chart') {
    // Prepared composition: let the narration explain it.
  } else if (focus === '#results') {
    await waitUntil(.68);
    await scrollTo(page, '#posthoc-rerun', smoothMs, null, 128);
    await assertFramed(page, '#posthoc-rerun');
  } else if (focus === 'example-en') {
    await waitUntil(.18);
    await scrollTo(page, '#post-text', smoothMs, null, 115);
    await waitUntil(.52);
    await scrollTo(page, '#post-text mark:last-child', smoothMs, null, 440);
    await waitUntil(.77);
    await scrollTo(page, '#claim-list .claim-card:nth-child(5)', smoothMs, null, 330);
  } else if (focus === 'verdicts-en') {
    const {amazon, nvidia, tesla} = await verdictCards(page);
    await amazon.evaluate(n => n.classList.add('demo-claim-current'));
    await waitUntil(.29);
    await amazon.evaluate(n => n.classList.remove('demo-claim-current'));
    await nvidia.evaluate(n => n.classList.add('demo-claim-current'));
    await waitUntil(.58);
    await nvidia.evaluate(n => n.classList.remove('demo-claim-current'));
    if (!await tesla.evaluate(n => n.classList.contains('is-false'))) throw new Error('Tesla must actually be contradicted.');
    await tesla.evaluate(n => n.classList.add('demo-emphasis'));
    await waitUntil(.88);
    await tesla.evaluate(n => n.classList.remove('demo-emphasis'));
  } else if (focus === 'filing-modal') {
    const amazon = page.locator('#claim-list .claim-card').filter({hasText:'Amazon'}).first();
    await amazon.evaluate(n => n.setAttribute('data-demo-amazon',''));
    await waitUntil(.12);
    await click(page, amazon.getByRole('button', {name:'See filing', exact:true}));
    await page.locator('#filing-dialog[open]').waitFor({state:'visible'});
    const highlighted = page.locator('#filing-dialog td.is-fact, #filing-dialog .filing-fact-highlight').first();
    await highlighted.waitFor({state:'visible'});
    await highlighted.evaluate(node => {
      node.setAttribute('data-demo-fact','');
      (node.closest('table') || node).setAttribute('data-demo-table','');
    });
    await scrollTo(page, '[data-demo-table]', smoothMs, '#filing-dialog-body', 16);
    await assertFramed(page, '[data-demo-table], [data-demo-fact]');
    await waitUntil(.70);
    await scrollTo(page, '#filing-dialog .filing-links', smoothMs, '#filing-dialog-body', 20);
    // The SEC links are shown, never followed: network stays on the allowed public project.
  } else if (focus === 'example-zh') {
    await scrollTo(page, '.site-header', smoothMs, null, 0);
    await waitUntil(.10);
    await click(page, page.locator('[data-language="zh"]'));
    await scrollTo(page, '#example-title', smoothMs);
    await click(page, page.locator('[data-example="zh"]'));
    await page.waitForFunction(() => document.querySelector('[data-example="zh"]').getAttribute('aria-selected') === 'true'
      && /[\u4e00-\u9fff]/.test(document.querySelector('#post-text').textContent));
    await waitUntil(.53);
    await scrollTo(page, '#post-text mark:last-child', smoothMs, null, 360);
  } else {
    throw new Error(`Unsupported storyboard focus: ${focus}`);
  }
  const elapsed = (performance.now()-start)/1000;
  if (elapsed > seconds+.15) throw new Error(`Actions exceeded the scene (${elapsed.toFixed(2)} > ${seconds.toFixed(2)} s).`);
  await waitUntil(1);
}

export async function main(sceneId) {
  const config = JSON.parse(await readFile(process.argv[2], 'utf8'));
  if (config.id !== sceneId || !isPublicProjectURL(config.url)) throw new Error('Scene id or allowed public URL mismatch.');
  if (!(config.duration_s > 0)) throw new Error('A positive scene duration is required.');
  await mkdir(path.dirname(config.output), {recursive:true});
  const browser = await launch();
  let context;
  const blocked = [];
  try {
    context = await browser.newContext(captureContextOptions(config));
    await restrictNetwork(context);
    await context.addInitScript(() => {try {localStorage.setItem('market-claim-verifier-language','en');} catch {}});
    const recordingStart = performance.now();
    const page = await context.newPage();
    page.on('requestfailed', request => blocked.push({url:request.url(), error:request.failure()?.errorText}));
    page.setDefaultTimeout(25000);
    await page.goto(config.url, {waitUntil:'networkidle'});
    await page.evaluate(() => document.fonts.ready);
    await ready(page, config.focus);
    await page.addStyleTag({content:cursorCSS});
    await page.evaluate(() => { const dot = document.createElement('div'); dot.id='demo-cursor'; document.body.append(dot); });
    await prepare(page, config);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(250);
    const lead_s = (performance.now()-recordingStart)/1000;
    const capturedAt = new Date().toISOString();
    await perform(page, config, config.duration_s);
    await page.waitForTimeout(350); // Enough real tail frames for exact frame rounding.
    const video = page.video();
    await context.close(); context = null;
    await video.saveAs(config.output);
    await writeFile(config.receipt, JSON.stringify({scene_id:sceneId,url:config.url,focus:config.focus,
      duration_s:config.duration_s,lead_s,captured_at:capturedAt,playwright:playwright().version,
      viewport:config.capture.viewport,scale:config.capture.scale,color_scheme:config.capture.color_scheme,
      resolution:config.resolution,emphasis:config.emphasis,blocked_requests:blocked},null,2)+'\n');
  } finally {
    if (context) await context.close();
    await browser.close();
  }
}
