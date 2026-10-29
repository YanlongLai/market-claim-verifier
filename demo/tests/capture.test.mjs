/** Shot-contract tests only: no browser, network, screenshots, or real capture artifacts. */
import assert from 'node:assert/strict';
import test from 'node:test';
import {prepare, perform} from '../capture/common.mjs';

function shotPage(t, {barCount = 3, bottom = 548} = {}) {
  let now = 0;
  t.mock.method(performance, 'now', () => now);
  const events = [];
  const page = {
    events,
    viewportSize: () => ({width:1280, height:720}),
    async waitForTimeout(ms) { events.push({wait:ms}); now += ms; },
    async evaluate(fn, args) {
      if (args.selector) {
        events.push({scroll:args.selector, container:args.container});
        now += args.duration;
      } else events.push({focus:args.focus, emphasis:args.emphasis});
    },
    locator(selector) {
      const locator = {
        first() { return locator; },
        async waitFor() {},
        async count() { return barCount; },
        async evaluateAll(fn) {
          if (selector.includes('.bar-fill')) {
            const line = {classList:{add:className => events.push({highlight:selector, className})}};
            return fn(Array.from({length:barCount}, () => ({closest:() => line})));
          }
          return fn([{getBoundingClientRect:() => ({x:106,y:128,width:1068,height:bottom-128})}]);
        }
      };
      return locator;
    }
  };
  return page;
}

test('s02 holds the chart and boxes only the without-tools bars', async t => {
  const page = shotPage(t);
  const config = {focus:'#chart', emphasis:'without'};
  await prepare(page, config);
  await perform(page, config, 10);
  assert.deepEqual(page.events.filter(e => e.scroll).map(e => e.scroll), ['#chart']);
  const highlights = page.events.filter(e => e.highlight);
  assert.equal(highlights.length, 3);
  assert.ok(highlights.every(e => e.highlight === '#chart .bar-fill.is-without'));
});

test('s08 holds the green chart bars, then scrolls to the post-hoc rerun', async t => {
  const page = shotPage(t);
  const config = {focus:'#results', emphasis:'with-checks'};
  await prepare(page, config);
  const start = page.events.length;
  await perform(page, config, 10);
  assert.deepEqual(page.events.filter(e => e.scroll).map(e => e.scroll), ['#chart','#posthoc-rerun']);
  assert.ok(page.events.filter(e => e.highlight).every(e => e.highlight === '#chart .bar-fill.is-with-checks'));
  assert.ok(Math.abs(page.events[start].wait - 6800) < .001);
  assert.ok(Math.abs(page.events.at(-1).wait - 2200) < .001);
});

test('a missing provider bar fails instead of recording an incomplete chart', async t => {
  const page = shotPage(t, {barCount:2});
  await assert.rejects(prepare(page, {focus:'#chart', emphasis:'without'}), /one highlighted bar per provider/);
});

test('a chart extending into subtitles fails its framing check', async t => {
  const page = shotPage(t, {bottom:650});
  await assert.rejects(prepare(page, {focus:'#chart', emphasis:'without'}), /does not fit between the captions/);
});
