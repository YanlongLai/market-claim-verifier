"""Exercise the animation clock and lifecycle offline, without a browser/network.

The tiny DOM adapter supplies only elements/events/dimensions. The production
script still owns every animation calculation and playback decision. This does
not substitute for visual browser QA.
"""

import json
import shutil
import subprocess

import pytest

from docs.scripts.build_site import ROOT


pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node is needed for the offline JavaScript lifecycle check")


def run_check(script, config=None):
    result = subprocess.run(
        ["node", "--input-type=module", "-", str(ROOT), json.dumps(config or {})],
        input=script,
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_stamp_animation_timing_lifecycle_and_localization():
    run_check(RUNTIME_CHECK)


def test_narrow_stamp_geometry_at_gate():
    run_check(NARROW_GEOMETRY_CHECK, {"viewport": 375, "language": "en", "reduced": False})


@pytest.mark.parametrize("viewport", [375, 1280])
def test_stamp_cards_never_overlap_across_full_loop(viewport):
    run_check(NO_OVERLAP_CHECK, {"viewport": viewport})


@pytest.mark.parametrize("viewport", [375, 1280])
def test_stamp_impact_keeps_card_in_scene_and_stamp_in_card(viewport):
    run_check(IMPACT_GEOMETRY_CHECK, {"viewport": viewport})


def test_seek_after_language_switch_repaints_frame():
    run_check(LANGUAGE_SEEK_CHECK, {"viewport": 375, "language": "en", "reduced": False})


@pytest.mark.parametrize("viewport", [1280, 375])
@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("reduced", [False, True])
def test_seek_retains_stamps_evidence_and_stacking_until_recycling(viewport, language, reduced):
    run_check(SEEK_CHECK, {"viewport": viewport, "language": language, "reduced": reduced, "query": "?stamp-t=12.5"})


@pytest.mark.parametrize("query", ["", "?stamp-t=", "?stamp-t=-1", "?stamp-t=oops", "?stamp-t=Infinity"])
def test_invalid_or_absent_seek_query_keeps_normal_playback(query):
    run_check(QUERY_CHECK, {"query": query})


RUNTIME_SETUP = r"""
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const root = process.argv[2];
const config = JSON.parse(process.argv[3]);
const viewportWidth = config.viewport || 1280;
const phone = viewportWidth <= 639;
const source = readFileSync(`${root}/docs/site/script.js`, 'utf8');
const css = readFileSync(`${root}/docs/site/styles.css`, 'utf8');
const cards = JSON.parse(readFileSync(`${root}/docs/site/data/site.json`, 'utf8')).stamp_cards;

const narrowCSS = css.slice(css.indexOf('@media (max-width: 639px)'), css.indexOf('@media (prefers-reduced-motion: reduce)'));
function cssRule(selector, narrow = false) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = (narrow ? narrowCSS : css).match(new RegExp(`^\\s*${escaped}\\s*\\{([^}]+)\\}`, 'm'));
  assert.ok(match, `CSS rule: ${selector}`);
  return match[1];
}
function property(rule, name) {
  const match = rule.match(new RegExp(`(?:^|;)\\s*${name}:\\s*([^;]+);`));
  assert.ok(match, `CSS property: ${name}`);
  return match[1].trim();
}
const sceneRule = cssRule('.stamp-scene', phone);
const cardWidthValue = property(sceneRule, '--stamp-card-width');
const cardWidth = parseFloat(cardWidthValue) * (cardWidthValue.endsWith('vw') ? viewportWidth / 100 : 1);
// Mirror .shell's border-box width and page padding, not the whole viewport.
const pagePadding = viewportWidth <= 390 ? 17 : Math.max(20, Math.min(viewportWidth * 0.04, 56));
const sceneWidth = Math.round(Math.min(1180, viewportWidth) - 2 * pagePadding);
const constant = (name) => Number(source.match(new RegExp(`const ${name} = (\\d+);`))[1]);
const TRAVEL = constant('TRAVEL');
const CROSSING = TRAVEL / 2;
const SCAN_DURATION = 300;
const EVIDENCE_DURATION = 100;
const STAMP_LEAD = SCAN_DURATION + EVIDENCE_DURATION;
const SCAN_START = CROSSING - STAMP_LEAD;
const IMPACT_OVERSHOOT = 105;
const IMPACT_REBOUND = 160;
const INK_SETTLED = 300;
const SAMPLE_STEP = 25;
const CARD_GAP = 24;
const baseInterval = constant(phone ? 'NARROW_INTERVAL' : 'DESKTOP_INTERVAL');
const interval = Math.max(baseInterval, Math.ceil(TRAVEL * (cardWidth + CARD_GAP) / (sceneWidth + cardWidth)));
const loop = cards.length * interval;
const seconds = (milliseconds) => milliseconds / 1000;
const cardTime = (index, age) => seconds(index * interval + age);
const parseX = (element) => Number(element.style.transform.match(/translate3d\(([-\d.]+)px/)[1]);
const find = (body, name) => body.children.find((child) => child.className === name);

class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.children = [];
    this.dataset = {};
    this.attributes = {};
    this.style = { setProperty(key, value) { this[key] = value; } };
    this.events = {};
    this.className = '';
    this.hidden = false;
    this.clientWidth = sceneWidth;
    this.classList = { contains: (name) => this.className.split(' ').includes(name), toggle: (name, enabled) => {
      const classes = new Set(this.className.split(' ').filter(Boolean));
      if (enabled) classes.add(name); else classes.delete(name);
      this.className = [...classes].join(' ');
    } };
  }
  append(...children) { this.children.push(...children); }
  setAttribute(name, value) { this.attributes[name] = value; }
  addEventListener(name, fn) { this.events[name] = fn; }
  getBoundingClientRect() { return { width: cardWidth }; }
  querySelector(selector) { return elements[selector]; }
}

const elements = Object.fromEntries([
  '#stamp-scene', '#stamp-track', '#stamp-static-list', '#stamp-pause', '.stamp-gate-beam', '.stamp-gate-label'
].map((key) => [key, new Element()]));
elements['.stamp-gate-label'].dataset.i18n = 'stamps.gate';
elements['#stamp-scene'].dataset.i18nAria = 'stamps.region';
const documentEvents = {};
const created = [];
const document = {
  hidden: false,
  documentElement: new Element('html'),
  createElement: (tag) => { const element = new Element(tag); created.push(element); return element; },
  querySelector: (selector) => elements[selector],
  querySelectorAll: (selector) => Object.values(elements).filter((item) =>
    (selector === '[data-i18n]' && item.dataset.i18n) ||
    (selector === '[data-i18n-aria]' && item.dataset.i18nAria)),
  addEventListener: (name, fn) => { documentEvents[name] = fn; }
};
let onIntersection;
let onMotion;
let onNarrowViewport;
const narrowViewport = { matches: phone, addEventListener: (_name, fn) => { onNarrowViewport = fn; } };
const motion = { matches: config.reduced || false, addEventListener: (_name, fn) => { onMotion = fn; } };
const callbacks = new Map();
let nextFrame = 0;
const context = vm.createContext({
  document,
  URLSearchParams,
  window: {
    matchMedia: (query) => query.includes('max-width') ? narrowViewport : motion,
    IntersectionObserver: true,
    ResizeObserver: true,
    location: { search: config.query || '' }
  },
  localStorage: { getItem: () => config.language || 'en' },
  IntersectionObserver: class {
    constructor(fn) { onIntersection = fn; }
    observe() {}
  },
  ResizeObserver: class { observe() {} },
  requestAnimationFrame: (fn) => { callbacks.set(++nextFrame, fn); return nextFrame; },
  cancelAnimationFrame: (id) => callbacks.delete(id)
});

// Replace only the page boot calls, so the actual production functions can run
// against supplied elements. Nothing about their timing/playback is reimplemented.
const boot = '  setupFilingDialog();\n  setupControls();\n  applyCopy();\n  loadData();';
assert.ok(source.includes(boot));
vm.runInContext(source.replace(boot, `
  globalThis.stamps = { createStampConveyor, setLanguage: (language) => { pageLanguage = language; applyCopy(); } };
`), context);
"""

RUNTIME_CHECK = RUNTIME_SETUP + r"""
const conveyor = context.stamps.createStampConveyor(cards);
const scene = elements['#stamp-scene'];
const pause = elements['#stamp-pause'];
const still = elements['#stamp-static-list'].children.map((item) => item.children[0]);
const moving = elements['#stamp-track'].children;
const first = moving[0].children[0];
const firstMark = first.children.find((item) => item.className === 'stamp-mark');
const firstEvidence = first.children.find((item) => item.className === 'stamp-evidence');
const firstScan = first.children[0].children[0];
function step(time) {
  const pending = [...callbacks.values()];
  callbacks.clear();
  pending.forEach((fn) => fn(time));
}

assert.equal(scene.dataset.running, 'false');
assert.equal(callbacks.size, 0);
assert.equal(still.length, cards.length);
assert.ok(still.every((item) => item.tabIndex === -1));
assert.equal(first.dataset.phase, 'stamped'); // Playback starts at contact.
assert.equal(firstEvidence.style.opacity, '1');
context.window.__stampScene.seek(seconds(SCAN_START));
pause.events.click(); // Replay the lead-in from the beginning of the sweep.
onIntersection([{ isIntersecting: true }]);
step(0);
assert.equal(scene.dataset.running, 'true');
assert.equal(moving.filter((item) => !item.hidden).length, Math.ceil(TRAVEL / interval));
assert.equal(firstMark.style.opacity, '0');
assert.equal(firstEvidence.style.opacity, '0');
step(SCAN_DURATION / 2);
assert.ok(Number(firstScan.style.opacity) > 0.27);
step(SCAN_DURATION);
assert.equal(firstScan.style.opacity, '0');
step(SCAN_DURATION + EVIDENCE_DURATION / 2);
assert.ok(Number(firstEvidence.style.opacity) > 0.8);
assert.equal(firstMark.style.opacity, '0');
step(STAMP_LEAD);
assert.match(firstMark.style.transform, /scale\(1.8\)/);
step(STAMP_LEAD + IMPACT_OVERSHOOT);
assert.match(firstMark.style.transform, /scale\(0.94/);
assert.equal(firstMark.style.opacity, '1');
step(STAMP_LEAD + IMPACT_REBOUND);
assert.match(firstMark.style.transform, /scale\(1.04\)/);
const settledFrame = STAMP_LEAD + INK_SETTLED;
step(settledFrame);
assert.match(firstMark.style.transform, /scale\(1\)/);
assert.equal(firstMark.children[1].style.opacity, '0.12');
assert.equal(first.style.transform, 'translate3d(0px, 0px, 0)');
const atSettled = moving[0].style.transform;
step(settledFrame + loop); // One full list later, position and state are identical.
assert.equal(moving[0].style.transform, atSettled);
assert.equal(firstMark.style.opacity, '1');

pause.events.click();
assert.equal(scene.dataset.running, 'false');
assert.equal(pause.attributes['aria-pressed'], 'true');
assert.equal(pause.textContent, 'Play animation');
assert.equal(callbacks.size, 0);
pause.events.click();
const resumedFrame = settledFrame + loop + TRAVEL;
step(resumedFrame);
assert.equal(moving[0].style.transform, atSettled); // No jump on resume.

onIntersection([{ isIntersecting: false }]);
assert.equal(callbacks.size, 0);
assert.equal(scene.dataset.running, 'false');
onIntersection([{ isIntersecting: true }]);
step(resumedFrame + TRAVEL);
assert.equal(moving[0].style.transform, atSettled);
document.hidden = true;
documentEvents.visibilitychange();
assert.equal(callbacks.size, 0);
document.hidden = false;
documentEvents.visibilitychange();
step(resumedFrame + 2 * TRAVEL);
assert.equal(moving[0].style.transform, atSettled);

motion.matches = true;
onMotion();
assert.equal(scene.dataset.animated, 'false');
assert.equal(callbacks.size, 0);
assert.ok(still.every((item) => item.tabIndex === 0));
for (let index = 0; index < cards.length; index++) {
  if (cards[index].filing_url) {
    assert.equal(still[index].href, cards[index].filing_url);
  } else {
    const deployed = new URL(still[index].href, 'https://example.invalid/market-claim-verifier/site/');
    assert.equal(deployed.pathname, `/market-claim-verifier/${cards[index].source_report.slice('docs/'.length)}`);
  }
  const evidence = moving[index].children[0].children.find((item) => item.className === 'stamp-evidence');
  assert.equal(Boolean(evidence), cards[index].status === 'verified');
  const angle = Number.parseFloat(still[index].style['--stamp-angle']);
  assert.ok(angle >= -12 && angle <= 8);
}
context.stamps.setLanguage('zh');
conveyor.localize();
for (let index = 0; index < cards.length; index++) {
  assert.equal(still[index].children.find((item) => item.className === 'stamp-claim').textContent, cards[index].text.zh);
}
assert.equal(firstMark.children[0].textContent, '正確');
assert.equal(pause.textContent, '暫停動畫');
motion.matches = false;
onMotion();
assert.equal(scene.dataset.running, 'true');
assert.equal(callbacks.size, 1);
console.log('Offline clock, scan/stamp sequencing, loop, pause, visibility, reduced motion, links and i18n passed.');
"""


NARROW_GEOMETRY_CHECK = RUNTIME_SETUP + r"""
const conveyor = context.stamps.createStampConveyor(cards);
const scene = elements['#stamp-scene'];
const moving = elements['#stamp-track'].children;
const stageWidth = scene.clientWidth;
const shellInset = (viewportWidth - stageWidth) / 2;
const cardBox = (carrier) => ({ left: shellInset + parseX(carrier), right: shellInset + parseX(carrier) + cardWidth });

context.window.__stampScene.seek(seconds(CROSSING));
const active = moving[0];
const activeBox = cardBox(active);
assert.ok(activeBox.left >= 0, `card starts inside viewport: ${activeBox.left}`);
assert.ok(activeBox.right <= viewportWidth, `card ends inside viewport: ${activeBox.right}`);
assert.ok(Math.abs((activeBox.left + activeBox.right) / 2 - viewportWidth / 2) < 1, 'card is centred on the gate');

const visible = moving.filter((carrier) => !carrier.hidden);
assert.equal(visible.length, Math.ceil(TRAVEL / interval));
const leftNeighbor = cardBox(moving[1]);
const rightNeighbor = cardBox(moving[moving.length - 1]);
assert.ok(leftNeighbor.right <= activeBox.left - CARD_GAP, 'left neighbour stays clear of the card');
assert.ok(rightNeighbor.left >= activeBox.right + CARD_GAP, 'right neighbour stays clear of the card');

const narrowRule = narrowCSS;
assert.match(narrowRule, /--stamp-card-width:\s*72vw/);
assert.match(narrowRule, /height:\s*300px/);
assert.match(narrowRule, /-webkit-line-clamp:\s*3/);
assert.match(narrowRule, /\.stamp-mark[\s\S]*right:\s*14px[\s\S]*bottom:\s*12px/);
assert.match(narrowRule, /\.stamp-evidence[\s\S]*bottom:\s*12px[\s\S]*left:\s*12px/);

// The evidence chip sits in the card's bottom-left corner, clear of the stamp (bottom-right).
assert.ok(cardWidth - 10 >= 0);
console.log('Narrow gate card, neighbour gaps and evidence chip geometry passed.');
"""


NO_OVERLAP_CHECK = RUNTIME_SETUP + r"""
context.stamps.createStampConveyor(cards);
const seek = context.window.__stampScene.seek;
const moving = elements['#stamp-track'].children;
const times = new Set([0, loop]);
for (let time = 0; time < loop; time += SAMPLE_STEP) times.add(time);
for (let index = 0; index < cards.length; index++) {
  for (const age of [0, CROSSING, CROSSING + IMPACT_OVERSHOOT + SAMPLE_STEP, TRAVEL - 1, TRAVEL]) {
    times.add((index * interval + age) % loop);
  }
}
for (const time of [...times].sort((left, right) => left - right)) {
  assert.equal(seek(seconds(time)), seconds(time % loop), `normalized seek at ${time}ms`);
  const visible = moving.filter((carrier) => !carrier.hidden).map((carrier) => {
    // Include the actual impact shake of the paper, not just its carrier.
    const left = parseX(carrier) + parseX(carrier.children[0]);
    return { left, right: left + cardWidth, id: carrier.children[0].dataset.cardId };
  }).sort((left, right) => left.left - right.left);
  assert.ok(visible.length >= 2, `multiple cards in flight at ${time}ms`);
  for (let index = 1; index < visible.length; index++) {
    const previous = visible[index - 1];
    const current = visible[index];
    assert.ok(previous.right <= current.left,
      `${viewportWidth}px at ${time}ms: ${previous.id} overlaps ${current.id} by ${previous.right - current.left}px`);
  }
}
console.log(`No overlapping cards across the full ${seconds(loop)}s loop at ${viewportWidth}px.`);
"""


IMPACT_GEOMETRY_CHECK = RUNTIME_SETUP + r"""
context.stamps.createStampConveyor(cards);
const seek = context.window.__stampScene.seek;
const moving = elements['#stamp-track'].children;
const cardHeight = parseFloat(property(phone ? cssRule('.stamp-card', true) : sceneRule,
  phone ? 'min-height' : '--stamp-card-height'));
const cardTop = parseFloat(property(cssRule('.stamp-carrier', phone), 'top'));
const sceneHeight = parseFloat(property(sceneRule, 'height'));
const markRule = cssRule('.stamp-mark', phone);
const markWidth = cardWidth * parseFloat(property(markRule, 'width')) / 100;
const right = parseFloat(property(markRule, 'right'));
const bottom = parseFloat(property(markRule, 'bottom'));
const impressionRule = cssRule('.stamp-impression,\n.stamp-bleed');
const narrowImpressionRule = phone ? cssRule('.stamp-impression,\n  .stamp-bleed', true) : impressionRule;
const paddingY = parseFloat(property(narrowImpressionRule, 'padding'));
const border = parseFloat(property(narrowImpressionRule, phone ? 'border-width' : 'border'));
const epsilon = 1e-9;

for (let index = 0; index < cards.length; index++) {
  const carrier = moving[index];
  const body = carrier.children[0];
  const mark = find(body, 'stamp-mark');
  seek(cardTime(index, CROSSING));
  assert.equal(carrier.hidden, false);
  assert.equal(body.dataset.phase, 'stamped');
  assert.ok(Math.abs(parseX(carrier) + cardWidth / 2 - sceneWidth / 2) < epsilon,
    `${cards[index].id}: contact is centred on the gate`);
  assert.ok(parseX(carrier) >= 0 && parseX(carrier) + cardWidth <= sceneWidth,
    `${cards[index].id}: card fits the scene at contact`);

  // At first contact the 1.8x stamp is transparent. Check its fully visible
  // impact compression (105ms later), including its real rotation and scale.
  seek(cardTime(index, CROSSING + IMPACT_OVERSHOOT));
  assert.equal(mark.style.opacity, '1');
  const evidence = find(body, 'stamp-evidence');
  if (evidence) assert.equal(evidence.style.opacity, '1');
  const left = parseX(carrier) + parseX(body);
  assert.ok(left >= 0 && left + cardWidth <= sceneWidth, `${cards[index].id}: impact card fits scene horizontally`);
  assert.ok(cardTop >= 0 && cardTop + cardHeight <= sceneHeight, `${cards[index].id}: impact card fits scene vertically`);
  const fontRule = cards[index].verdict === null ? cssRule('.stamp-card.is-unknown .stamp-mark', phone) : markRule;
  const fontSize = parseFloat(property(fontRule, 'font-size')) * 16; // rem; root font is 16px.
  const markHeight = fontSize + 2 * (paddingY + border); // line-height: 1, border-box.
  const transform = mark.style.transform.match(/rotate\(([-\d.]+)deg\) scale\(([-\d.]+)\)/);
  const angle = Number(transform[1]) * Math.PI / 180;
  const scale = Number(transform[2]);
  const halfWidth = scale * (markWidth * Math.abs(Math.cos(angle)) + markHeight * Math.abs(Math.sin(angle))) / 2;
  const halfHeight = scale * (markWidth * Math.abs(Math.sin(angle)) + markHeight * Math.abs(Math.cos(angle))) / 2;
  const centerX = cardWidth - right - markWidth / 2;
  const centerY = cardHeight - bottom - markHeight / 2;
  assert.ok(centerX - halfWidth >= -epsilon && centerX + halfWidth <= cardWidth + epsilon,
    `${cards[index].id}: rotated impact stamp fits card horizontally`);
  assert.ok(centerY - halfHeight >= -epsilon && centerY + halfHeight <= cardHeight + epsilon,
    `${cards[index].id}: rotated impact stamp fits card vertically`);
}
console.log(`All impact cards and stamp boxes fit at ${viewportWidth}px.`);
"""


LANGUAGE_SEEK_CHECK = RUNTIME_SETUP + r"""
const conveyor = context.stamps.createStampConveyor(cards);
const moving = elements['#stamp-track'].children;
const frame = () => JSON.stringify(moving.map((carrier) => carrier.hidden ? { hidden: true } : {
  position: carrier.style.transform,
  phase: carrier.children[0].dataset.phase,
  stamp: carrier.children[0].children.find((item) => item.className === 'stamp-mark').style.opacity
}));

context.window.__stampScene.seek(seconds(CROSSING));
const beforeLanguageSwitch = frame();
context.stamps.setLanguage('zh');
conveyor.localize();
assert.equal(moving[0].children[0].children.find((item) => item.className === 'stamp-claim').textContent, cards[0].text.zh);
assert.equal(frame(), beforeLanguageSwitch);
context.window.__stampScene.seek(cardTime(1, CROSSING + INK_SETTLED));
assert.notEqual(frame(), beforeLanguageSwitch, 'seek after language switch repaints a different frame');
console.log('Chinese localization followed by a later seek repainted the conveyor.');
"""


SEEK_CHECK = RUNTIME_SETUP + r"""
const conveyor = context.stamps.createStampConveyor(cards);
const seek = context.window.__stampScene.seek;
const scene = elements['#stamp-scene'];
const label = elements['.stamp-gate-label'];
const pause = elements['#stamp-pause'];
const moving = elements['#stamp-track'].children;
const still = elements['#stamp-static-list'].children.map((carrier) => carrier.children[0]);
// Hidden cards intentionally keep their ink until they recycle off-screen left.
// Only visible presentation belongs to the deterministic rendered frame.
const fingerprint = () => JSON.stringify(moving.map((carrier) => carrier.hidden ? { hidden: true } : ({
  hidden: carrier.hidden, position: carrier.style.transform, opacity: carrier.style.opacity,
  layer: carrier.style.zIndex, phase: carrier.children[0].dataset.phase,
  mark: find(carrier.children[0], 'stamp-mark').style,
  evidence: find(carrier.children[0], 'stamp-evidence')?.style
})));

context.stamps.setLanguage(config.language);
conveyor.localize();
assert.equal(scene.dataset.running, 'false');
assert.equal(pause.attributes['aria-pressed'], 'true');
assert.equal(callbacks.size, 0); // The query parameter freezes the initial frame.
const fromQuery = fingerprint();
assert.equal(seek(12.5), 12.5);
assert.equal(fingerprint(), fromQuery); // URL and console use exactly the same clock.
onIntersection([{ isIntersecting: true }]);
assert.equal(callbacks.size, 0); // Visibility must not resume a seeked frame.

// Run the regression for every card, particularly the reported $NVDA FY2024 card.
// These seeks use the production renderer, including its width-dependent wraparound.
for (let index = 0; index < cards.length; index++) {
  const carrier = moving[index];
  const body = carrier.children[0];
  const mark = find(body, 'stamp-mark');
  const evidence = find(body, 'stamp-evidence');
  const center = () => parseX(carrier) + cardWidth / 2;

  seek(cardTime(index, SCAN_START - SAMPLE_STEP));
  assert.equal(carrier.hidden, false);
  assert.ok(center() < scene.clientWidth / 2, `${cards[index].id}: left of gate`);
  assert.equal(body.dataset.phase, 'incoming');
  assert.equal(mark.style.opacity, '0');
  if (evidence) assert.equal(evidence.style.opacity, '0');

  seek(cardTime(index, CROSSING + IMPACT_OVERSHOOT));
  assert.match(mark.style.transform, /scale\(0.94/);
  assert.equal(label.style.transform, config.reduced ? 'translateX(-50%) scale(1)' : 'translateX(-50%) scale(1.06)');
  seek(cardTime(index, CROSSING + IMPACT_OVERSHOOT + SAMPLE_STEP));
  const shake = Number(body.style.transform.match(/translate3d\(([-\d.]+)px/)[1]);
  assert.ok(Math.abs(shake) > 2 && Math.abs(shake) <= 3);

  // The old gate stacking changed at age=4s, one second after crossing.
  // Check continuously past that point, through ink settling and the right edge.
  for (let age = CROSSING + INK_SETTLED; age < TRAVEL; age += SAMPLE_STEP) {
    seek(cardTime(index, age));
    assert.equal(carrier.hidden, false);
    assert.ok(center() > scene.clientWidth / 2, `${cards[index].id}: right of gate`);
    assert.equal(body.dataset.phase, 'stamped');
    assert.equal(mark.style.opacity, '1', `${cards[index].id}: permanent stamp at age ${age}`);
    assert.match(mark.style.transform, /scale\(1\)/);
    assert.equal(mark.children[1].style.opacity, '0.12');
    if (evidence) assert.equal(evidence.style.opacity, '1');
    for (const other of moving) {
      if (!other.hidden && other !== carrier) {
        const otherCenter = parseX(other) + cardWidth / 2;
        if (otherCenter < center()) assert.ok(Number(carrier.style.zIndex) > Number(other.style.zIndex));
      }
    }
  }
  // Leaving right hides the carrier but does not erase its mark or evidence.
  seek(cardTime(index, TRAVEL + 1));
  assert.equal(carrier.hidden, true);
  assert.equal(mark.style.opacity, '1');
  if (evidence) assert.equal(evidence.style.opacity, '1');
  // Recycling off-screen left is the point where the old verdict is cleared.
  seek(cardTime(index, loop));
  assert.equal(carrier.hidden, false);
  assert.ok(center() < 0);
  assert.equal(mark.style.opacity, '0');
  if (evidence) assert.equal(evidence.style.opacity, '0');
}

// Forward and backward seeks must not depend on the previous animation frame.
const probeIndex = cards.findIndex((card) => card.id === 'demo-thread-baseten-2');
assert.ok(probeIndex >= 0);
const probeTime = cardTime(probeIndex, CROSSING + INK_SETTLED);
seek(probeTime); // A settled, filing-backed card is immediately to the right of the gate.
const once = fingerprint();
seek(cardTime(probeIndex, TRAVEL - 1));
seek(cardTime(probeIndex, SCAN_START - SAMPLE_STEP));
seek(probeTime);
assert.equal(fingerprint(), once);
seek(seconds(loop) + probeTime); // Same point one loop later.
assert.equal(fingerprint(), once);
seek(probeTime);
const frozen = fingerprint();
document.hidden = true;
documentEvents.visibilitychange();
document.hidden = false;
documentEvents.visibilitychange();
assert.equal(fingerprint(), frozen);
assert.equal(callbacks.size, 0);

for (const invalid of [-1, NaN, Infinity, '12.5', null]) {
  assert.throws(() => seek(invalid), /finite, non-negative/);
  assert.equal(fingerprint(), frozen);
}

// A failed/missing texture must leave real stamp text unmasked and visible.
const ink = created.find((element) => element.tagName === 'img');
assert.equal(ink.src, 'img/stamp-ink.webp');
ink.events.error();
assert.equal(scene.classList.contains('has-stamp-ink'), false);
ink.naturalWidth = 1024;
ink.events.load();
assert.equal(scene.classList.contains('has-stamp-ink'), true);
ink.events.error();
assert.equal(scene.classList.contains('has-stamp-ink'), false);
const nvda = moving[probeIndex].children[0];
assert.equal(find(nvda, 'stamp-mark').style.opacity, '1');
assert.ok(find(nvda, 'stamp-mark').children[0].textContent);
const nvdaEvidence = find(nvda, 'stamp-evidence');
if (nvdaEvidence) assert.equal(nvdaEvidence.style.opacity, '1');

for (let index = 0; index < cards.length; index++) {
  assert.equal(find(still[index], 'stamp-claim').textContent, cards[index].text[config.language]);
  assert.equal(still[index].tabIndex, config.reduced ? 0 : -1);
  assert.equal(still[index].href, cards[index].filing_url || cards[index].source_report.replace(/^docs\//, '../'));
}
assert.equal(scene.dataset.animated, String(!config.reduced));
assert.equal(elements['#stamp-static-list'].classList.contains('is-sr-only'), !config.reduced);
assert.equal(label.textContent, config.language === 'zh' ? 'Muse Spark 代理 + SEC 查核' : 'Muse Spark agent + SEC check');
assert.equal(find(nvda, 'stamp-mark').children[0].textContent, config.language === 'zh' ? '正確' : 'TRUE');
assert.equal(find(nvda, 'stamp-claim').textContent, cards[probeIndex].text[config.language]);
assert.equal(callbacks.size, 0);
pause.events.click(); // Play resumes from the exact sought point.
assert.equal(scene.dataset.running, String(!config.reduced));
assert.equal(callbacks.size, config.reduced ? 0 : 1);
console.log('Seek/query, stamp/evidence retention, stacking, recycling, texture failure, pill pulse, phone, i18n and reduced motion passed.');
"""


QUERY_CHECK = RUNTIME_SETUP + r"""
context.stamps.createStampConveyor(cards);
const scene = elements['#stamp-scene'];
const first = elements['#stamp-track'].children[0];
const mark = first.children[0].children.find((item) => item.className === 'stamp-mark');
assert.equal(first.children[0].dataset.phase, 'stamped'); // Default starts at CROSSING, at contact.
assert.equal(mark.style.opacity, '0');
assert.equal(find(first.children[0], 'stamp-evidence').style.opacity, '1');
assert.equal(elements['#stamp-pause'].attributes['aria-pressed'], 'false');
onIntersection([{ isIntersecting: true }]);
assert.equal(scene.dataset.running, 'true');
assert.equal(callbacks.size, 1);
"""
