"""Execute the production scene offline; check CSS boxes without Chromium.

The DOM adapter parses the shipped HTML and supplies events and layout boxes.
The production JS drives phases, fades, transforms, seeks and playback. These
are geometry envelopes, not browser measurements of fonts or visual approval.
"""

import json
import shutil
import subprocess

import pytest

from docs.scripts.build_site import ROOT

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node is required for the offline scene checks")


def run_check(script, **config):
    result = subprocess.run(
        ["node", "--input-type=module", "-", str(ROOT), json.dumps(config)],
        input=SETUP + script, text=True, capture_output=True, cwd=ROOT, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_exact_review_phases_and_120ms_robot_crossfades(viewport):
    run_check(PHASES, viewport=viewport)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_cant_check_skips_passage_and_meter_and_shrugs(language):
    run_check(CANT_CHECK, language=language)


def test_playback_freezes_offscreen_hidden_paused_and_reduced_motion():
    run_check(LIFECYCLE)


@pytest.mark.parametrize("viewport", [390, 768, 1280])
@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("reduced", [False, True])
def test_seek_is_deterministic_in_all_layouts_and_static_list_is_complete(viewport, language, reduced):
    run_check(SEEK, viewport=viewport, language=language, reduced=reduced, query="?stamp-t=12.94")


@pytest.mark.parametrize("query", ["", "?stamp-t=", "?stamp-t=-1", "?stamp-t=oops", "?stamp-t=Infinity"])
def test_invalid_seek_query_does_not_pause_playback(query):
    run_check(QUERY, query=query)


@pytest.mark.parametrize("viewport", [320, 375, 390, 639, 640, 768, 1023, 1024, 1280, 1440])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_fixed_panel_robot_stamp_and_strip_envelopes_at_every_breakpoint(viewport, language):
    run_check(GEOMETRY, viewport=viewport, language=language)


@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_fixed_filing_box_reveals_header_rows_and_staggered_ledger_then_fades(viewport):
    run_check(FILING, viewport=viewport)


def test_severity_meter_keeps_a_visible_marker_at_zero_and_static_scores():
    run_check(SEVERITY)


def test_scan_spotlight_meter_hover_strike_and_texture_fallback():
    run_check(DETAILS)


def test_new_pose_paths_fall_back_once_to_the_nearest_existing_pose():
    run_check(ASSETS)


@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_documented_apple_keyframes_match_live_scene_state(viewport):
    run_check(KEYFRAMES, viewport=viewport)


@pytest.mark.parametrize("viewport", [390, 768, 1280])
@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("reduced", [False, True])
def test_personas_dates_example_tags_and_repost_attribution_in_all_presentations(viewport, language, reduced):
    run_check(PERSONAS, viewport=viewport, language=language, reduced=reduced)


@pytest.mark.parametrize("viewport", [320, 375, 390, 639, 640, 768, 1023, 1024, 1280, 1440])
@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_spotlight_cones_protect_text_and_follow_mirrored_blended_visors(viewport, theme, language):
    run_check(SPOTLIGHT, viewport=viewport, theme=theme, language=language)


@pytest.mark.parametrize("viewport", [390, 768, 1440])
@pytest.mark.parametrize("reduced", [False, True])
def test_vfx_load_only_on_start_fail_independently_and_seek_from_one_clock(viewport, reduced):
    run_check(VFX, viewport=viewport, reduced=reduced)


@pytest.mark.parametrize("viewport", [390, 768, 1280])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_every_robot_caption_comes_from_the_active_card_in_both_languages(viewport, language):
    run_check(CAPTIONS, viewport=viewport, language=language)


@pytest.mark.parametrize("viewport", [320, 390])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_phone_uses_cached_intrinsic_maxima_and_single_row_controls(viewport, language):
    run_check(PHONE_MAXIMA, viewport=viewport, language=language,
              postHeights=[171.1, 212.2, 161, 198.4, 184, 207.9, 178, 198.2, 168.5, 217.3, 223.4],
              filingHeights=[137, 203.4, 0, 141.2, 148, 149, 0, 141.2, 142.8, 137, 142.8])


@pytest.mark.parametrize("viewport", [640, 768, 1024, 1440])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_desktop_meter_and_filed_comparison_share_a_baseline(viewport, language):
    run_check(BASELINES, viewport=viewport, language=language)


@pytest.mark.parametrize("viewport", [320, 375, 390, 639, 640, 768, 1023, 1024, 1100, 1101, 1280, 1440])
@pytest.mark.parametrize("source_kind", ["thread", "social", "article", "repost"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_each_publication_format_grows_the_panel_to_fit_its_intrinsic_geometry(viewport, source_kind, language):
    run_check(CARD_FITS, viewport=viewport, sourceKind=source_kind, language=language,
              postHeights=[174, 182, 168, 196, 171, 182, 178, 179, 170, 206, 211],
              filingHeights=[139, 196, 0, 139, 147, 155, 0, 139, 139, 139, 139])


@pytest.mark.parametrize("viewport", [390, 768, 1024])
@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("reduced", [False, True])
def test_polished_publication_formats_preserve_real_checks_and_label_fiction(viewport, language, reduced):
    run_check(POLISH, viewport=viewport, language=language, reduced=reduced)


@pytest.mark.parametrize("kind,payload,expected", [
    ("audio", {"timestamp": "00:12", "transcript": {"en": "Recorded transcript", "zh": "實際逐字稿"}, "waveform": [0.2, 0.7, 1, 0.4]}, "audio"),
    ("video", {"timestamp": "01:23", "thumbnail": "img/real-frame.webp"}, "video"),
    ("screenshot", {"thumbnail": "img/real-shot.webp"}, "screenshot"),
    ("audio", None, "text"),
    ("audio", {"timestamp": "00:12", "transcript": {"en": "Actual", "zh": "實際"}}, "text"),
    ("audio", {"timestamp": "00:12", "transcript": {"en": "Actual", "zh": "實際"}, "waveform": [0.1, 2]}, "text"),
    ("video", {"timestamp": "01:23", "thumbnail": "img/../invented.webp"}, "text"),
    ("video", {"thumbnail": "img/real-frame.webp"}, "text"),
])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_media_variants_require_actual_payload_and_keep_transcript_and_timestamp(kind, payload, expected, language):
    run_check(MEDIA, viewport=390, language=language, inputKind=kind, inputPayload=payload, expectedInput=expected)


@pytest.mark.parametrize("viewport", [390, 1280])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_reduced_motion_has_no_spotlight_dim_letterbox_dust_or_flash(viewport, theme):
    run_check(REDUCED_SPOTLIGHT, viewport=viewport, theme=theme, reduced=True)


@pytest.mark.parametrize("viewport", [390, 1280])
def test_swapped_pose_canvas_updates_the_visor_without_reprobing_phone_content(viewport):
    run_check(POSE_CANVAS, viewport=viewport)


@pytest.mark.parametrize("viewport", [390, 768, 1280])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_hover_layers_follow_nozzles_mirroring_clock_dip_burst_and_shadow(viewport, theme):
    run_check(HOVER, viewport=viewport, theme=theme)


SETUP = r"""
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const root = process.argv[2];
const config = JSON.parse(process.argv[3]);
const viewport = config.viewport || 1280;
const phone = viewport < 640;
const tablet = viewport >= 640 && viewport <= 1100;
const css = readFileSync(`${root}/docs/site/styles.css`, 'utf8');
const source = readFileSync(`${root}/docs/site/script.js`, 'utf8');
const html = readFileSync(`${root}/docs/site/index.html`, 'utf8');
const cards = JSON.parse(readFileSync(`${root}/docs/site/data/site.json`, 'utf8')).stamp_cards;
if (config.inputKind) { cards[0].input_kind=config.inputKind; cards[0].input_media=config.inputPayload; }
// Read the actual CSS cascade, including either side of both breakpoints.
const rules = [];
function mediaActive(query) {
  if (query.includes('prefers-reduced-motion')) return !!config.reduced;
  if (query.includes('prefers-color-scheme')) return config.theme === 'dark';
  const min = query.match(/min-width:\s*(\d+)px/), max = query.match(/max-width:\s*(\d+)px/);
  return (!min || viewport >= Number(min[1])) && (!max || viewport <= Number(max[1]));
}
function readRules(text) {
  text = text.replace(/\/\*[\s\S]*?\*\//g, '');
  let offset = 0;
  while (offset < text.length) {
    const open = text.indexOf('{', offset);
    if (open < 0) break;
    let close = open + 1, depth = 1;
    while (depth && close < text.length) { if (text[close] === '{') depth++; if (text[close] === '}') depth--; close++; }
    const selector = text.slice(offset, open).trim(), body = text.slice(open + 1, close - 1);
    if (selector.startsWith('@media')) { if (mediaActive(selector)) readRules(body); }
    else if (!selector.startsWith('@')) rules.push({ selectors: selector.split(',').map(x => x.trim()), body });
    offset = close;
  }
}
readRules(css);
function declarations(selector) {
  const found = rules.filter(rule => rule.selectors.includes(selector));
  assert.ok(found.length, `CSS rule ${selector}`);
  return Object.assign({}, ...found.map(rule => Object.fromEntries(rule.body.split(';').filter(x => x.includes(':')).map(x => {
    const at = x.indexOf(':'); return [x.slice(0, at).trim(), x.slice(at + 1).trim()];
  }))));
}
const rule = selector => Object.entries(declarations(selector)).map(([key,value]) => `${key}: ${value};`).join(' ');
function property(selector, key) {
  const value = declarations(selector)[key]; assert.notEqual(value, undefined, `${selector} ${key}`); return value;
}
const variables = declarations('.stamp-scene');
function length(value, basis = viewport) {
  let expression = value.replace(/var\((--[\w-]+)\)/g, (_all, name) => `(${length(variables[name], basis)})`)
    .replace(/([\d.]+)rem/g, '($1*16)').replace(/([\d.]+)vw/g, `($1*${viewport}/100)`)
    .replace(/([\d.]+)%/g, `($1*${basis}/100)`).replace(/px/g, '').replace(/calc\(/g, '(');
  return Function('min', 'max', 'clamp', `return (${expression});`)(Math.min, Math.max, (a,b,c) => Math.max(a,Math.min(b,c)));
}
const px = (selector, key, basis) => length(property(selector,key), basis);
const sceneWidth = px('.shell','width',viewport) - 2 * px('.shell','padding-inline');
const labelHeight = length(variables['--stamp-label-height']);
const letterboxHeight = length(variables['--stamp-letterbox-height']);
const robotWidth = length(variables['--stamp-robot-width']), robotHeight = length(variables['--stamp-robot-height']);
const columnGap = length(variables['--stamp-column-gap']);
const panelWidth = phone ? sceneWidth : (sceneWidth - robotWidth - 2 * columnGap) / 2;
let postHeight = px('.stamp-track','height'), filingHeight = px('.stamp-filing-box','height');
const stripHeight = length(variables['--stamp-strip-height']), stripGap = length(variables['--stamp-strip-gap']);
let stageHeight = px('.stamp-stage','height');
let sceneHeight = property('.stamp-scene','height') === 'auto' ? stageHeight+stripHeight+stripGap : px('.stamp-scene','height');
const stageTop = phone ? stripHeight : 0;
const postTop = stageTop + letterboxHeight + labelHeight;
const filingLeft = phone ? 0 : panelWidth + 2 * columnGap + robotWidth;
let filingTop, robotTop;
const robotLeft = phone ? 8 : panelWidth + columnGap;
function refreshBoxes() {
  postHeight=px('.stamp-track','height');filingHeight=px('.stamp-filing-box','height');
  stageHeight=px('.stamp-stage','height');
  sceneHeight=property('.stamp-scene','height')==='auto'?stageHeight+stripHeight+stripGap:px('.stamp-scene','height');
  filingTop=phone?postTop+postHeight+length(variables['--stamp-robot-band'])+labelHeight:letterboxHeight+labelHeight;
  robotTop=phone?postTop+postHeight+4:letterboxHeight+(stageHeight-2*letterboxHeight-robotHeight-6-px('.stamp-caption','min-height'))/2;
}
refreshBoxes();
const rect = (left, top, width, height) => ({left,top,right:left+width,bottom:top+height,width,height});
// Heterogeneous synthetic intrinsic boxes test the maximum-height algorithm.
// They exercise measured-size handling, not browser font metrics or screenshot approval.
let naturalPostHeights = config.postHeights || [174,182,168,196,171,182,178,179,170,206,211];
let naturalFilingHeights = config.filingHeights || [139,196,0,139,147,155,0,139,139,139,139];
let layoutReads = 0, intrinsicReads = 0;
const created = [];
function matches(node, selector) {
  const parts = selector.split(/\s+/);
  const simple = (item, pattern) => {
    if (item.tagName === '#text') return false;
    const tag = pattern.match(/^[\w-]+/); if (tag && item.tagName !== tag[0]) return false;
    for (const match of pattern.matchAll(/([.#])([\w-]+)/g)) {
      if (match[1] === '#' ? item.attributes.id !== match[2] : !item.classList.contains(match[2])) return false;
    }
    for (const match of pattern.matchAll(/\[([\w-]+)(?:="([^"]*)")?\]/g)) {
      if (!(match[1] in item.attributes) || match[2] !== undefined && item.attributes[match[1]] !== match[2]) return false;
    }
    return true;
  };
  if (!simple(node, parts.pop())) return false;
  for (let parent = node.parent; parts.length; parent = parent?.parent) {
    if (!parent) return false;
    if (simple(parent,parts[parts.length-1])) parts.pop();
  }
  return true;
}
class Element {
  constructor(tag = 'div') {
    this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.events = {};
    const owner=this;
    this.style = { setProperty(key,value) {
      this[key] = value;
      if(owner.attributes.id==='stamp-scene'&&key.startsWith('--')){variables[key]=value;refreshBoxes();}
    } };
    this.className = ''; this.hidden = false; this._text = '';
    const change = (name, enabled) => {
      const classes = new Set(this.className.split(' ').filter(Boolean));
      if (enabled) classes.add(name); else classes.delete(name); this.className = [...classes].join(' ');
    };
    this.classList = { contains: name => this.className.split(' ').includes(name), toggle: change, remove: name => change(name,false) };
  }
  set textContent(text) { this._text = String(text); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  append(...children) { for (const child of children) { child.parent = this; this.children.push(child); } }
  prepend(...children) { for (const child of children) child.parent = this; this.children.unshift(...children); }
  replaceChildren(...children) { this.children = []; this._text = ''; this.append(...children); }
  setAttribute(key,value) {
    this.attributes[key] = String(value);
    if (key === 'class') this.className = value;
    if (key === 'hidden') this.hidden = true;
    if (key.startsWith('data-')) this.dataset[key.slice(5).replace(/-([a-z])/g, (_all,c) => c.toUpperCase())] = value;
  }
  getAttribute(key) { return this.attributes[key] ?? null; }
  removeAttribute(key) { delete this.attributes[key]; }
  addEventListener(key,fn) {
    const previous=this.events[key];
    this.events[key]=previous?(...args)=>{previous(...args);fn(...args);}:fn;
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => [...(matches(child,selector)?[child]:[]), ...child.querySelectorAll(selector)]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  get clientWidth() { layoutReads++; return this.classList.contains('stamp-track') ? panelWidth : sceneWidth; }
  getBoundingClientRect() {
    layoutReads++;
    let paper=this,compare=this;
    while(paper&&!paper.dataset.cardId)paper=paper.parent;
    while(compare&&!compare.classList.contains('stamp-compare'))compare=compare.parent;
    const index=paper?cards.findIndex(card=>card.id===paper.dataset.cardId):0;
    const measuring=tree.querySelector('#stamp-scene')?.classList.contains('is-measuring');
    const padding=property('.stamp-filing-box','padding').split(' ').map(value=>length(value));
    const padY=padding[0],padX=padding[1]??padY;
    const passageTop=filingTop+padY+1, passageLeft=filingLeft+padX+1;
    const passageWidth=panelWidth-2*(padX+1), passageHeight=filingHeight-2*(padY+1);
    let passage=this;
    while(passage&&!passage.classList.contains('stamp-passage'))passage=passage.parent;
    const compareTop=phone?passageTop+142:passageTop+parseFloat(passage?.style['--stamp-compare-top']||'0');
    const compareHeight=cards[index]?.excerpt?.derivation?30:44;
    if(measuring&&this.classList.contains('stamp-card')){intrinsicReads++;return rect(0,postTop,panelWidth,naturalPostHeights[index]);}
    if(measuring&&this.classList.contains('stamp-passage')){intrinsicReads++;return rect(passageLeft,passageTop,passageWidth,naturalFilingHeights[index]);}
    if(measuring&&this.classList.contains('stamp-filing-state')){intrinsicReads++;return rect(filingLeft,filingTop,panelWidth,124);}
    if (this.classList.contains('stamp-stage')) return rect(0,stageTop,sceneWidth,stageHeight);
    if (this.classList.contains('stamp-panel-label')) {
      const filing=this.parent.classList.contains('stamp-filing-panel');
      return rect(filing?filingLeft:0,(filing?filingTop:postTop)-labelHeight,panelWidth,labelHeight);
    }
    if (this.classList.contains('stamp-caption')) return rect(phone?robotLeft+robotWidth+10:robotLeft,phone?robotTop+12:robotTop+robotHeight+6,phone?sceneWidth-robotWidth-26:robotWidth,px('.stamp-caption','height'));
    if (this.classList.contains('stamp-strip')) return rect(0,phone?0:stageTop+stageHeight+stripGap,sceneWidth,stripHeight);
    if (this.classList.contains('stamp-track')) return rect(0,postTop,panelWidth,postHeight);
    if (this.classList.contains('stamp-filing-box')) return rect(filingLeft,filingTop,panelWidth,filingHeight);
    if (this.classList.contains('stamp-filing-content')||this.classList.contains('stamp-passage'))return rect(passageLeft,passageTop,passageWidth,passageHeight);
    if (this.classList.contains('stamp-robot')) return rect(robotLeft,robotTop,robotWidth,robotHeight);
    if (this.classList.contains('stamp-number')) return rect(16+(this.testOffset||0),postTop+78,Math.min(panelWidth-32,this.textContent.length*14),28);
    if (this.classList.contains('stamp-mark')) return rect(panelWidth-100,postTop+postHeight-64,86,40);
    if (this.classList.contains('stamp-meter'))return rect(14,postTop+postHeight-40,panelWidth-150,phone?4:6);
    if (this.classList.contains('stamp-compare'))return rect(passageLeft,compareTop,passageWidth,compareHeight);
    if (this.classList.contains('stamp-compare-filed') || this.classList.contains('stamp-ledger-value'))
      return rect(filingLeft+panelWidth/2,compareTop+compareHeight-20,Math.min(panelWidth/2-14,90),16);
    if(this.classList.contains('stamp-passage-row'))return rect(passageLeft+(this.testOffset||0),passageTop+65,passageWidth,26);
    if(this.classList.contains('stamp-ledger-row')){
      const offset=this.parent.children.indexOf(this);
      return rect(passageLeft,compare?compareTop+offset*20:passageTop+99+offset*20,passageWidth,18);
    }
    return rect(0,postTop,panelWidth,postHeight);
  }
}
// Parse shipped markup instead of maintaining a second hand-written scene DOM.
const tree = new Element('document'), stack = [tree];
for (const match of html.matchAll(/<!--[\s\S]*?-->|<\/?[^>]+>|[^<]+/g)) {
  const token = match[0];
  if (token.startsWith('<!')) continue;
  if (token.startsWith('</')) { stack.pop(); continue; }
  if (token.startsWith('<')) {
    const tag = token.match(/^<([\w-]+)/)[1], node = new Element(tag);
    for (const attr of token.slice(tag.length+1,-1).matchAll(/([\w-]+)(?:="([^"]*)")?/g)) node.setAttribute(attr[1],attr[2]??'');
    stack[stack.length-1].append(node);
    if (!['meta','link','img','input','br','hr'].includes(tag) && !token.endsWith('/>')) stack.push(node);
  } else {
    const node = new Element('#text'); node.textContent = token; stack[stack.length-1].append(node);
  }
}
const documentEvents = {};
const document = {
  hidden: false, documentElement: tree.querySelector('html'),
  createElement: tag => { const node = new Element(tag); created.push(node); return node; },
  createElementNS: (_namespace,tag) => { const node = new Element(tag); created.push(node); return node; },
  createTextNode: text => { const node = new Element('#text'); node.textContent = text; return node; },
  querySelector: selector => tree.querySelector(selector), querySelectorAll: selector => tree.querySelectorAll(selector),
  addEventListener: (key,fn) => { documentEvents[key] = fn; }
};
let intersection, onMotion, onResize, onFonts;
document.fonts={ready:{then(fn){onFonts=fn;}}};
const motion = { matches: !!config.reduced, addEventListener: (_key,fn) => { onMotion = fn; } };
const narrow = { matches: phone, addEventListener() {} };
const callbacks = new Map(); let nextFrame = 0;
const context = vm.createContext({
  document, URLSearchParams,
  window: { matchMedia: query => query.includes('max-width') ? narrow : motion,
    IntersectionObserver: true, ResizeObserver: true, location: { search: config.query || '' } },
  localStorage: { getItem: () => config.language || 'en' },
  IntersectionObserver: class { constructor(fn) { intersection = fn; } observe() {} },
  ResizeObserver: class { constructor(fn) { onResize = fn; } observe() {} },
  requestAnimationFrame: fn => { callbacks.set(++nextFrame,fn); return nextFrame; }, cancelAnimationFrame: id => callbacks.delete(id)
});
const boot = '  setupFilingDialog();\n  setupControls();\n  applyCopy();\n  loadData();';
assert.ok(source.includes(boot));
vm.runInContext(source.replace(boot, `
  globalThis.stamps = { createStampConveyor, setLanguage: language => { pageLanguage = language; applyCopy(); } };
`), context);
const conveyor = context.stamps.createStampConveyor(cards);
context.stamps.setLanguage(config.language || 'en'); conveyor.localize();
const api = context.window.__stampScene, seek = seconds => api.seek(seconds);
const scene = tree.querySelector('#stamp-scene'), stage = tree.querySelector('.stamp-stage');
const robot = tree.querySelector('.stamp-robot'), pause = tree.querySelector('#stamp-pause');
const track = tree.querySelector('#stamp-track'), filingBox = tree.querySelector('.stamp-filing-box');
const filingContent = tree.querySelector('#stamp-filing-content');
const moving = track.children, still = tree.querySelector('#stamp-static-list').children;
const starts = [0,8,16,21.4,29.4,37.4,45.4,50.8,58.8,66.8,74.8];
const find = (node,name) => node.classList.contains(name) ? node : node.querySelector(`.${name}`);
const passage = index => filingContent.children.find(node => node.dataset.cardId === cards[index].id);
const parseX = node => Number(node.style.transform.match(/translate3d\(([-\d.]+)px/)[1]);
const scaleX = node => Number(node.style.transform.match(/scaleX\(([-\d.]+)\)/)[1]);
const snapshot = node => [node.className,node.hidden,node.textContent,node.style,node.dataset,node.attributes,node.tabIndex,node.children.map(snapshot)];
const fingerprint = () => JSON.stringify(snapshot(scene));
const step = time => { const pending = [...callbacks.values()]; callbacks.clear(); pending.forEach(fn => fn(time)); };
const near = (actual,expected) => assert.ok(Math.abs(actual-expected)<1e-8, `${actual} ≈ ${expected}`);
"""

PHASES = r"""
assert.equal(api.timing.checkable,8); assert.equal(api.timing.uncheckable,5.4);
assert.equal(cards.length,11); assert.equal(api.timing.loop,82.8); assert.equal(api.timing.crossfade,.12);
assert.deepEqual(Array.from(api.timing.starts),starts);
for (let index=0;index<cards.length;index++) {
  const can=cards[index].score!==null;
  const beats=can?[[0,'enter','idle',0],[.699,'enter','idle',0],[.7,'read','inspect',1],[1.499,'read','inspect',1],
    [1.5,'reach','reach',2],[2.299,'reach','reach',2],[2.3,'find','point',2],[3.699,'find','point',2],
    [3.7,'compare','think',3],[4.499,'compare','think',3],[4.5,'windup','stamp',4],[4.799,'windup','stamp',4],
    [4.8,'strike','stamp-down',4],[5.299,'strike','stamp-down',4],
    [5.3,'react',cards[index].verdict==='supported'?'approve':'concern',4],
    [6.399,'react',cards[index].verdict==='supported'?'approve':'concern',4],
    [6.4,'exit','idle',0],[7.199,'exit','idle',0],[7.2,'rest','idle',0],[7.999,'rest','idle',0]]:
    [[0,'enter','idle',0],[.7,'read','inspect',1],[1.499,'read','inspect',1],[1.5,'shrug','shrug',1],
     [2.999,'shrug','shrug',1],[3,'strike','shrug',4],[3.5,'react','shrug',4],[4.599,'react','shrug',4],[4.6,'exit','idle',0],[5.399,'exit','idle',0]];
  for (const [age,phase,pose,step] of beats) {
    seek(starts[index]+age);
    assert.equal(api.getState().phase,phase,`${cards[index].id} @ ${age}`);
    assert.equal(api.getState().pose,pose); assert.equal(api.getState().step,step);
    assert.equal(api.getState().cardId,cards[index].id); near(api.getState().localTime,age);
    assert.equal(moving[index].hidden,can&&age>=7.2);
    const active=scene.querySelectorAll('.stamp-progress li').filter(node=>node.classList.contains('is-active'));
    assert.equal(active.length,step?1:0);
    if(step)assert.equal(active[0].attributes['aria-current'],'step');
  }
  const held=can?[.7,1.4,1.5,2.3,3.7,4.8,6.399]:[.7,1.5,3,4.599];
  for(const age of held){ seek(starts[index]+age); near(parseX(moving[index]),0); }
  const fades=can?[[.7,'idle','inspect'],[1.5,'inspect','reach'],[2.3,'reach','point'],[3.7,'point','think'],
    [4.5,'think','stamp'],[4.8,'stamp','stamp-down'],[5.3,'stamp-down',cards[index].verdict==='supported'?'approve':'concern'],
    [6.4,cards[index].verdict==='supported'?'approve':'concern','idle']]:[[.7,'idle','inspect'],[1.5,'inspect','shrug'],[4.6,'shrug','idle']];
  for(const [age,from,to] of fades)for(const fraction of [0,.25,.5,.75,1]){
    seek(starts[index]+age+.12*fraction);
    for(const image of robot.querySelectorAll('.stamp-robot-pose')) near(Number(image.style.opacity),image.dataset.pose===to?fraction:image.dataset.pose===from?1-fraction:0);
    near(robot.querySelectorAll('.stamp-robot-pose').reduce((sum,image)=>sum+Number(image.style.opacity),0),1);
  }
}
seek(82.8);assert.equal(api.getState().cardId,cards[0].id);assert.equal(api.getState().phase,'enter');
assert.equal(property('.stamp-robot-pose[data-facing="post"]','transform'),'scaleX(-1)');
assert.equal(property('.stamp-robot-pose[data-facing="filing"]','transform'),'scaleX(1)');
for(const [time,facing] of [[1,'post'],[1.8,'filing'],[2.6,'filing'],[4,'front'],[4.6,'post'],[5,'post'],[5.6,'front']]){
  seek(time);assert.equal(api.getState().facing,facing);
}
"""

CANT_CHECK = r"""
for(let index=0;index<cards.length;index++)if(cards[index].score===null){
  assert.equal(passage(index),undefined);assert.equal(find(moving[index],'stamp-meter'),undefined);
  assert.equal(find(still[index],'stamp-passage'),undefined);assert.equal(find(still[index],'stamp-meter'),undefined);
  seek(starts[index]+1.499); assert.equal(filingBox.dataset.state,'waiting');
  seek(starts[index]+1.5); assert.equal(filingBox.dataset.state,'uncheckable');
  assert.equal(tree.querySelector('.stamp-filing-state-title').textContent,config.language==='zh'?'沒有可查核的 SEC 數字':'No SEC number to check');
  assert.equal(tree.querySelector('.stamp-filing-state-explanation').textContent,config.language==='zh'?'財報記錄已發生的結果，不包含看法或預測。':'Filings report results, not opinions or forecasts.');
  assert.equal(tree.querySelector('.stamp-filing-state-explanation').hidden,false);
  const kind=cards[index].kind==='opinion'?(config.language==='zh'?'看法':'Opinion'):(config.language==='zh'?'預測':'Forecast');
  assert.equal(tree.querySelector('.stamp-filing-state-kind').textContent,kind);
  assert.equal(tree.querySelector('.stamp-filing-state-kind').hidden,false);
  seek(starts[index]+2.4);
  assert.equal(scene.dataset.phase,'shrug');assert.equal(robot.dataset.pose,'shrug');assert.equal(robot.dataset.gesture,'shrug');
  assert.equal(robot.dataset.facing,'front'); assert.equal(find(moving[index],'stamp-filed').textContent,'');
  assert.equal(find(moving[index],'stamp-period').textContent,config.language==='zh'?'看法／預測 — 沒有財報數字':'Opinion / forecast — no filed number');
  assert.equal(find(moving[index],'stamp-mark').style.opacity,'0');
  assert.equal(tree.querySelector('.stamp-beam-post').style.opacity,'0');assert.equal(tree.querySelector('.stamp-beam-filing').style.opacity,'0');
  const skipped=scene.querySelectorAll('.stamp-progress li').filter(node=>node.classList.contains('is-skipped'));
  assert.deepEqual(skipped.map(node=>node.dataset.step),['2','3']);
  assert.ok(skipped.every(node=>!node.classList.contains('is-active')&&!node.attributes['aria-current']));
  assert.equal(property('.stamp-progress li.is-skipped','text-decoration'),'line-through');
  assert.equal(filingContent.children.filter(node=>!node.hidden).length,0);
  seek(starts[index]+3.14);assert.equal(find(moving[index],'stamp-mark').style.opacity,'1');
  assert.equal(find(moving[index],'stamp-impression').textContent,config.language==='zh'?'無法查核':"CAN'T CHECK");
  assert.ok(find(moving[index],'stamp-card').classList.contains('is-unknown'));
  assert.equal(property('.stamp-mark','color'),'var(--stamp-unknown)');
  seek(starts[index]+4.6);assert.equal(scene.dataset.phase,'exit');assert.equal(robot.dataset.pose,'idle');
  seek(starts[index]+5);assert.ok(Number(moving[index].style.opacity)<1);
  seek(starts[index]+5.4);assert.notEqual(api.getState().cardId,cards[index].id);
}
"""

LIFECYCLE = r"""
assert.equal(callbacks.size,0);assert.equal(created.filter(x=>x.src&&!x.classList.contains('stamp-avatar')&&!x.classList.contains('stamp-polish-art')).length,0);
intersection([{isIntersecting:true}]);assert.equal(callbacks.size,1);
assert.equal(created.filter(x=>x.src?.includes('/H/')&&x.classList.contains('stamp-robot-pose')).length,11);
const reads=layoutReads;
step(100);step(300);near(api.getState().seconds,.2);assert.equal(layoutReads,reads,'Animation frames perform no layout reads');
intersection([{isIntersecting:false}]);assert.equal(callbacks.size,0);
const frozen=api.getState().seconds;
intersection([{isIntersecting:true}]);step(100000);near(api.getState().seconds,frozen);
step(100100);near(api.getState().seconds,frozen+.1);
document.hidden=true;documentEvents.visibilitychange();assert.equal(callbacks.size,0);
document.hidden=false;documentEvents.visibilitychange();step(500000);near(api.getState().seconds,frozen+.1);
pause.events.click();assert.equal(callbacks.size,0);assert.equal(scene.dataset.running,'false');
pause.events.click();assert.equal(callbacks.size,1);
motion.matches=true;onMotion();assert.equal(callbacks.size,0);assert.equal(scene.dataset.animated,'false');
assert.ok(still.every(item=>item.children[0].tabIndex===0));
motion.matches=false;onMotion();assert.equal(callbacks.size,1);
assert.equal(created.filter(x=>x.src?.includes('/H/')&&x.classList.contains('stamp-robot-pose')).length,11);
onResize();assert.ok(layoutReads>reads);
"""

SEEK = r"""
assert.equal(api.getState().seconds,12.94);assert.equal(api.getState().phase,'strike');
assert.equal(pause.attributes['aria-pressed'],'true');
assert.equal(find(moving[1],'stamp-filed').textContent,config.language==='zh'?'財報: $102.5B':'Filed: $102.5B');
assert.equal(find(moving[1],'stamp-severity').textContent,config.language==='zh'?'嚴重':'Severe');
assert.equal(find(moving[1],'stamp-score').textContent,'0 / 100');
for(const time of [0,.76,1.56,2.36,2.95,3.76,4.56,4.86,5.36,6.46,7.2,9.05,10.95,12.1,12.94,13.6,17,18.4,19.14,29,45.4,48.54,69,79.74]){
  seek(time);const once=fingerprint();seek(40);seek(.1);seek(time);assert.equal(fingerprint(),once,`history-independent @ ${time}`);
  seek(time+82.8);assert.equal(fingerprint(),once,`wrap-independent @ ${time}`);
  onResize();assert.equal(fingerprint(),once,`resize-independent @ ${time}`);
}
seek(12.94);const frozen=fingerprint();
for(const invalid of [-1,NaN,Infinity,'12.5',null]){assert.throws(()=>seek(invalid),/finite, non-negative/);assert.equal(fingerprint(),frozen);}
for(let index=0;index<cards.length;index++){
  const card=cards[index], body=still[index].children[0];
  assert.equal(find(body,'stamp-claim').textContent,card.text[config.language]);
  assert.equal(find(body,'stamp-company').textContent,card.company);assert.equal(body.tabIndex,config.reduced?0:-1);
  assert.ok(body.href===card.filing_url||body.href===card.source_report.replace(/^docs\//,'../'));
  if(card.excerpt){
    const filing=find(body,'stamp-passage');
    for(const text of [card.excerpt.form,card.excerpt.filed,card.excerpt.company,card.excerpt.section_title,card.excerpt.value])assert.ok(filing.textContent.includes(text));
    assert.equal(find(body,'stamp-meter').attributes['aria-valuenow'],String(Math.round(card.score)));
    assert.equal(find(body,'stamp-score').textContent,`${Math.round(card.score)} / 100`);assert.ok(find(body,'stamp-filed').textContent);
    if(card.excerpt.derivation)assert.ok(filing.textContent.includes(card.excerpt.derivation.text[config.language]));
  }else assert.ok(find(body,'stamp-static-unavailable').textContent);
}
assert.equal(callbacks.size,0);assert.equal(scene.dataset.animated,String(!config.reduced));
assert.equal(tree.querySelector('#stamp-static-list').classList.contains('is-sr-only'),!config.reduced);
if(config.reduced){
  assert.equal(created.filter(x=>x.src&&!x.classList.contains('stamp-avatar')&&!x.classList.contains('stamp-polish-art')).length,0);
  assert.equal(property('.stamp-stage','display'),'none');assert.equal(property('.stamp-strip','display'),'none');
}
context.stamps.setLanguage(config.language==='zh'?'en':'zh');conveyor.localize();seek(12.94);
assert.equal(find(moving[1],'stamp-severity').textContent,config.language==='zh'?'Severe':'嚴重');
assert.equal(tree.querySelector('.stamp-panel-label').textContent,config.language==='zh'?'① Post under review':'① 待查核貼文');
"""

QUERY = r"""
assert.equal(api.getState().seconds,0);assert.equal(pause.attributes['aria-pressed'],'false');
intersection([{isIntersecting:true}]);assert.equal(scene.dataset.running,'true');assert.equal(callbacks.size,1);
"""

GEOMETRY = r"""
near(sceneHeight,phone?2*letterboxHeight+2*labelHeight+postHeight+56+filingHeight+32:tablet?444:420);
assert.ok(sceneHeight<=(phone?600:tablet?444:424));
near(sceneHeight,stageHeight+stripHeight+stripGap);
assert.equal(property('.stamp-carrier','position'),'absolute');
assert.equal(property('.stamp-passage','position'),'absolute');assert.equal(property('.stamp-passage','inset'),'0');
assert.equal(property('.stamp-track','overflow'),'hidden');
assert.ok(!rule('.stamp-passage').includes('transform'),'The fixed filing content never flies');
assert.ok(!html.includes('stamp-queue')&&!html.includes('stamp-desk'));
assert.equal(pause.parent,tree.querySelector('.stamp-strip'));
assert.ok(!rule('.stamp-pause').includes('position:'),'Playback occupies the strip');
assert.equal(property('.stamp-robot','width'),'var(--stamp-robot-width)');
assert.equal(property('.stamp-robot','height'),'var(--stamp-robot-height)');
near(robotWidth,phone?64:tablet?120:190);near(robotHeight,phone?48:tablet?165:260);
const post=track.getBoundingClientRect(), filed=filingBox.getBoundingClientRect();
for(const box of [post,filed]){
  assert.ok(box.left>=0&&box.right<=sceneWidth);assert.ok(box.top>=0&&box.bottom<=sceneHeight);
}
if(phone){
  assert.equal(property('.stamp-strip','order'),'-1');near(stripHeight,32);
  assert.equal(property('.stamp-strip','display'),'flex');assert.equal(property('.stamp-next','display'),'none');
  assert.equal(property('.stamp-pause-label','display'),'none');assert.equal(property('.stamp-pause-icon','display'),'inline');
  assert.ok(post.bottom<=robotTop);near(robotTop,post.bottom+4);near(robotLeft,8);
  near(filed.top-post.bottom,labelHeight+56);
  assert.ok(robotTop+robotHeight<=post.bottom+56,'The pose stays inside the compact phone band');
  assert.ok(sceneHeight<=600,`Phone stage envelope ${sceneHeight}`);
  near(postHeight,Math.max(...naturalPostHeights));
  assert.ok(filingHeight>=Math.max(...naturalFilingHeights));
}else{
  assert.ok(post.right+columnGap<=robotLeft);assert.ok(robotLeft+robotWidth+columnGap<=filed.left);
  near(post.top,filed.top);near(post.height,filed.height);
}
// Include the whole 3-degree lean, 4px bob and 8px dip in the scene envelope.
for(const angleDegrees of [-3,3]){
  const angle=angleDegrees*Math.PI/180;
  for(const dx of [-robotWidth/2,robotWidth/2])for(const dy of [-robotHeight,0]){
    const x=robotLeft+robotWidth/2+dx*Math.cos(angle)-dy*Math.sin(angle);
    const y=robotTop+robotHeight+dx*Math.sin(angle)+dy*Math.cos(angle);
    assert.ok(x>=0&&x<=sceneWidth,'Robot lean stays inside the stage');
    assert.ok(y-4>=stageTop&&y+12<=stageTop+stageHeight,'Float and strike dip stay inside the stage');
    if(!phone)assert.ok(x>post.right&&x<filed.left,'Robot motion clears both panels');
  }
}
// Header + two headline lines + lede + scene, with conservative 2-line lede.
const headline=px('h1','font-size');assert.ok(headline<=64);
if(viewport===1024||viewport===1440){
  const header=2*px('.site-header','padding-block')+44;
  const heroPadding=property('.hero','padding-block').split(/\s+(?![^()]*\))/).map(x=>length(x));
  const total=header+heroPadding[0]+2*headline*.98+px('.hero-lede','margin-top')+2*px('.hero-lede','font-size')*1.42+20+sceneHeight;
  assert.ok(total<=(viewport===1024?768:900),`First screen envelope ${total}`);
}
assert.equal(property('.stamp-static-list.is-sr-only .stamp-card','width'),'360px');
const padding=property('.stamp-card','padding').split(' ').map(x=>length(x));
const padY=padding[0],padX=padding[1]??padY;
const slot=Number(property('.stamp-review','grid-template-columns').match(/ (\d+)px$/)[1]);
const gap=px('.stamp-review','gap'), markWidth=px('.stamp-mark','width');
const markPadding=property('.stamp-impression','padding').split(' ').map(x=>length(x))[0];
const footerHeight=px('.stamp-review','min-height');
for(let index=0;index<cards.length;index++){
  const duration=cards[index].score===null?5.4:8;
  for(let ms=0;ms<duration*1000;ms+=25){
    seek(starts[index]+ms/1000);
    assert.ok(moving.filter(item=>!item.hidden).length<=1,'Only one post in the fixed panel, including wraparound');
    assert.ok(filingContent.children.filter(item=>!item.hidden).length<=1,'Only one filing in its fixed box');
    const mark=find(moving[index],'stamp-mark');if(Number(mark.style.opacity)===0)continue;
    const match=mark.style.transform.match(/rotate\(([-\d.]+)deg\) scale\(([-\d.]+)\)/);
    const angle=Math.abs(Number(match[1]))*Math.PI/180,scale=Number(match[2]);
    const font=cards[index].score===null?px('.stamp-card.is-unknown .stamp-mark','font-size'):px('.stamp-mark','font-size');
    const markHeight=font+2*markPadding+6;
    const halfWidth=(markWidth*Math.cos(angle)+markHeight*Math.sin(angle))*scale/2;
    const halfHeight=(markHeight*Math.cos(angle)+markWidth*Math.sin(angle))*scale/2;
    const markCenter=panelWidth-padX-slot/2;
    assert.ok(markCenter+halfWidth<=panelWidth,'Inflating stamp stays inside right paper edge');
    assert.ok(padY+footerHeight/2>=halfHeight,'Inflating stamp stays inside bottom paper edge');
    assert.ok(markCenter-halfWidth>panelWidth-padX-slot-gap,'Stamp clears the meter slot');
  }
  seek(starts[index]+1);
  near(parseX(moving[index]),0);assert.ok(panelWidth>0);
}
const first=tree.querySelector('.stamp-panel-label').textContent;
assert.equal(first,config.language==='zh'?'① 待查核貼文':'① Post under review');
const steps=scene.querySelectorAll('.stamp-progress li');
const expected=config.language==='zh'?['找出說法','打開財報','程式判定','蓋章']:['Find the claim','Open the filing','Code decides','Stamp'];
for(let i=0;i<4;i++)assert.equal(steps[i].children[1].textContent,expected[i]);
"""

FILING = r"""
assert.equal(api.timing.ledgerStagger,.2);
const carrier=moving[1], paper=passage(1), header=find(paper,'stamp-passage-header'), details=find(paper,'stamp-passage-details');
assert.equal(paper.parent,filingContent);assert.equal(find(carrier,'stamp-passage'),undefined);
const fixed=JSON.stringify(filingBox.getBoundingClientRect());
for(const time of [8,9,9.5,10.3,11,11.7,12.94,13.6,14.4,15.1]){
  seek(time);assert.equal(JSON.stringify(filingBox.getBoundingClientRect()),fixed);
  assert.equal(paper.style.transform,undefined,'Filing has no flight or fold transform');
}
seek(9.499);assert.equal(header.style.opacity,'0');assert.equal(details.style.opacity,'0');
assert.equal(tree.querySelector('.stamp-filing-state').style.opacity,'1');
seek(9.56);near(Number(header.style.opacity),.5);assert.equal(details.style.opacity,'0');
assert.match(header.style.transform,/translate3d\(0, [-\d.]+px, 0\)/);
seek(9.75);assert.equal(header.style.opacity,'1');assert.equal(tree.querySelector('.stamp-filing-state').style.opacity,'0');
assert.equal(tree.querySelector('.stamp-folder-tab'),undefined,'No stray folder tab overlaps the border');
seek(10.36);near(Number(details.style.opacity),.5);
const rows=paper.querySelectorAll('.stamp-ledger-row');assert.equal(rows.length,2);
seek(10.5);assert.equal(rows[0].style.opacity,'0');assert.equal(rows[1].style.opacity,'0');
seek(10.56);near(Number(rows[0].style.opacity),.5);assert.equal(rows[1].style.opacity,'0');
seek(10.7);assert.equal(rows[0].style.opacity,'1');assert.equal(rows[1].style.opacity,'0');
seek(10.76);near(Number(rows[1].style.opacity),.5);
seek(10.96);near(Number(find(paper,'stamp-passage-accession').style.opacity),.5);
seek(11.02);assert.equal(find(paper,'stamp-derivation').style.opacity,'1');
assert.equal(find(paper,'stamp-compare').style.opacity,'0');
seek(11.76);near(Number(find(paper,'stamp-compare').style.opacity),.5);assert.ok(find(paper,'stamp-compare').classList.contains('is-active'));
seek(13.6);assert.equal(paper.style.opacity,'1');assert.equal(details.style.opacity,'1');
seek(14.8);near(Number(paper.style.opacity),.5);assert.ok(Number(carrier.style.opacity)<1);
seek(15.2);assert.ok(paper.hidden);assert.ok(carrier.hidden);
seek(16);assert.equal(filingContent.children.filter(node=>!node.hidden).length,0,'The next uncheckable card clears the previous filing');
"""

SEVERITY = r"""
for(let index=0;index<cards.length;index++){
  const card=cards[index];if(card.score===null)continue;
  seek(starts[index]+4.5);
  for(const item of [moving[index],still[index]]){
    const body=find(item,'stamp-card'),marker=find(item,'stamp-meter-marker');
    assert.equal(body.dataset.severity,card.severity);assert.equal(marker.attributes['aria-hidden'],'true');
    assert.equal(marker.style.transform,`translate3d(${card.score}%, 0, 0)`);
    assert.ok(property(`.stamp-card[data-severity="${card.severity}"]`,'--stamp-severity').includes(`--severity-${card.severity}`));
  }
}
seek(12.94);const apple=moving[1];near(scaleX(find(apple,'stamp-meter-fill')),0);
assert.equal(find(apple,'stamp-meter-marker').style.transform,'translate3d(0%, 0, 0)');
assert.equal(find(apple,'stamp-gap').textContent,'306% off');assert.equal(find(apple,'stamp-assessment').style.opacity,'1');
assert.equal(property('.stamp-meter','background'),'var(--stamp-meter-track)');
assert.ok(!rule('.stamp-meter').includes('overflow: hidden'));
assert.equal(property('.stamp-meter-marker::after','width'),'4px');
assert.equal(property('.stamp-meter-fill','background'),'var(--stamp-severity)');
assert.equal(property('.stamp-score-summary','color'),'var(--stamp-severity)');assert.equal(property('.stamp-gap','color'),'var(--stamp-severity)');
"""

DETAILS = r"""
const first=moving[0],mark=find(first,'stamp-mark'),paper=passage(0),beam=tree.querySelector('.stamp-beam-post');
seek(1.05);assert.ok(Number(find(first,'stamp-scan-light').style.opacity)>0);assert.ok(Number(find(first,'stamp-number-glow').style.opacity)>0);
assert.equal(find(first,'stamp-period').textContent,'Claim: $143.1B · Q3 2023');
assert.equal(find(first,'stamp-assessment').style.opacity,'0');assert.equal(mark.style.opacity,'0');
seek(3);assert.ok(scaleX(find(paper,'stamp-amber-sweep'))>0&&scaleX(find(paper,'stamp-amber-sweep'))<1);assert.equal(beam.style.opacity,'0');
seek(3.56);near(scaleX(find(paper,'stamp-amber-sweep')),1);
assert.equal(find(first,'stamp-filed').style.opacity,'0');
seek(3.7);near(scaleX(find(first,'stamp-meter-fill')),0);assert.equal(mark.style.opacity,'0');
seek(3.76);near(Number(beam.style.opacity),.5);assert.equal(mark.style.opacity,'0');
assert.ok(beam.querySelector('.stamp-beam-cone').attributes.points.split(' ').length>=3);
seek(4.1);near(scaleX(find(first,'stamp-meter-fill')),.875);assert.equal(beam.style.opacity,'1');
seek(4.5);near(scaleX(find(first,'stamp-meter-fill')),1);assert.equal(robot.dataset.pose,'stamp');assert.equal(mark.style.opacity,'0');
seek(4.94);assert.equal(mark.style.opacity,'1');assert.equal(robot.dataset.pose,'stamp-down');
assert.notEqual(find(first,'stamp-card').style.transform,'translate3d(0px, 0px, 0)');
seek(5);assert.match(mark.style.transform,/scale\(1\)/);
seek(4.86);const y=Number(robot.style.transform.match(/translate3d\(0px, ([-\d.]+)px/)[1]);
const bob=4*Math.sin(4860/(api.timing.floatPeriod*1000)*Math.PI*2);near(y-bob,8);
seek(5.6);assert.equal(robot.dataset.pose,'approve');assert.equal(mark.style.opacity,'1');assert.equal(paper.style.opacity,'1');
const ink=created.find(item=>item.src==='img/stamp-ink.webp');
ink.naturalWidth=1024;ink.events.load();assert.ok(scene.classList.contains('has-stamp-ink'));
ink.events.error();assert.equal(scene.classList.contains('has-stamp-ink'),false);assert.ok(find(first,'stamp-impression').textContent);
seek(10.95);const apple=moving[1],applePaper=passage(1);
for(const text of ['Full year','Total net sales','416,161','313,695','= 102,466','0000320193-25-000079','Q4 = full year − nine months = $102.5B'])assert.ok(applePaper.textContent.includes(text),text);
seek(12.94);assert.equal(find(apple,'stamp-score').textContent,'0 / 100');near(scaleX(find(apple,'stamp-meter-fill')),0);
assert.equal(find(applePaper,'stamp-compare-stated').textContent,'$416.2B');assert.equal(find(applePaper,'stamp-compare-filed').textContent,'$102.5B');
seek(starts[4]+4.2);assert.ok(passage(4).textContent.includes('+3.0%'));assert.ok(passage(4).textContent.includes('−2.9%'));
seek(starts[8]+4.2);assert.ok(passage(8).textContent.includes('> $50.0B'));
for(const image of robot.querySelectorAll('img')){assert.equal(image.loading,'lazy');assert.equal(image.decoding,'async');assert.ok(image.src.includes('/H/'));}
"""

ASSETS = r"""
seek(9.05);
const expected={reach:'present',point:'present',think:'inspect','stamp-down':'stamp',approve:'idle',concern:'idle',shrug:'idle'};
assert.equal(robot.querySelectorAll('.stamp-robot-pose').length,11);
for(const image of robot.querySelectorAll('.stamp-robot-pose')){
  const name=image.dataset.pose;assert.equal(image.src,`img/auditor/H/${name}.webp`);
  if(expected[name]){
    image.events.error();assert.equal(image.src,`img/auditor/H/${expected[name]}.webp`);assert.equal(image.dataset.asset,expected[name]);
    const once=image.src;image.events.error();assert.equal(image.src,once,'No recursive retry when the fallback fails');
    assert.equal(image.dataset.pose,name,'Fallback artwork preserves the beat semantics');
  }
}
for(const time of [9.05,9.8,10.95,12.1,12.94,13.6,18.4]){
  seek(time);const once=fingerprint();seek(70);seek(time);assert.equal(fingerprint(),once);
}
"""

KEYFRAMES = r"""
const doc=readFileSync(`${root}/docs/site/STAMP-V2-KEYFRAMES.md`,'utf8');
for(const [time,phase,pose,step] of [[9.05,'read','inspect',1],[10.95,'find','point',2],[12.1,'compare','think',3],
  [12.94,'strike','stamp-down',4],[13.6,'react','concern',4]]){
  assert.ok(doc.includes(`?stamp-t=${time.toFixed(2)}`));seek(time);
  assert.equal(api.getState().cardId,'demo-thread-baseten-3');assert.equal(api.getState().phase,phase);
  assert.equal(api.getState().pose,pose);assert.equal(api.getState().step,step);
}
assert.ok(doc.includes('82.8 s'));assert.ok(doc.includes('8.0 s'));
"""

PERSONAS = r"""
assert.equal(px('.stamp-avatar','width'),phone?44:56);
assert.equal(px('.stamp-avatar','height'),phone?44:56);assert.equal(property('.stamp-avatar','border-radius'),'50%');
function check(language){
  for(let index=0;index<cards.length;index++){
    const card=cards[index];seek(starts[index]+(card.score===null?3.14:4.94));
    for(const carrier of [moving[index],still[index]]){
      const body=carrier.children[0];
      assert.equal(find(body,'stamp-author').textContent,card.persona.name[language]);assert.equal(find(body,'stamp-byline').textContent,card.persona.byline[language]);
      assert.equal(find(body,'stamp-followers').textContent,card.persona.follower_label[language]);
      assert.equal(find(body,'stamp-post-date').textContent,card.post_date);assert.equal(find(body,'stamp-post-date').dateTime,card.post_date);
      assert.equal(find(body,'stamp-example').textContent,language==='en'?'Example post':'示範貼文');
      assert.ok(find(body,'stamp-example').title.includes(language==='en'?'Fictional':'虛構'));
      const avatar=find(body,'stamp-avatar');assert.equal(avatar.src,card.persona.avatar);assert.equal(avatar.alt,'');
      assert.equal(avatar.loading,'lazy');assert.equal(avatar.decoding,'async');
      if(card.reposted_from)assert.equal(find(body,'stamp-reposted').textContent,`${language==='en'?'Reposted from':'轉貼自'} 美股懶人包`);
      if(card.source_kind==='article')assert.equal(find(body,'stamp-source').textContent,language==='en'?'Article':'新聞報導');
    }
    const tickers=scene.querySelectorAll('.stamp-next-chip').map(node=>node.textContent);
    const upcoming=[cards[(index+1)%cards.length],cards[(index+2)%cards.length]];
    const label=card=>card.kind==='reported_fact'?(language==='en'?'revenue':'營收'):card.kind==='opinion'?(language==='en'?'opinion':'看法'):(language==='en'?'forecast':'預測');
    assert.deepEqual(tickers,upcoming.map(card=>`$${card.ticker}${upcoming[0].ticker===upcoming[1].ticker?' '+label(card):''}`));
  }
}
check(config.language);
const other=config.language==='en'?'zh':'en';context.stamps.setLanguage(other);conveyor.localize();check(other);
"""

SPOTLIGHT = r"""
const light=scene.querySelector('.stamp-spotlight');
assert.equal(scene.querySelector('.stamp-connector'),undefined);
assert.equal(light.attributes['aria-hidden'],'true');assert.equal(property('.stamp-spotlight','pointer-events'),'none');
const tokens=declarations(':root');assert.equal(tokens['--stamp-light'],config.theme==='dark'?'#d9fff0':'#ffd59a');
assert.equal(tokens['--stamp-dim'],config.theme==='dark'?'#03090d':'#38210f');
const dimOpacity=Number(tokens['--stamp-dim-opacity']);near(dimOpacity,config.theme==='dark'?.45:.25);
const paperOpacity=Number(tokens['--stamp-paper-dim-opacity']);near(paperOpacity,config.theme==='dark'?.32:.25);
assert.equal(property('.stamp-paper-dim','fill'),'var(--stamp-paper-dim)');
assert.equal(property('.stamp-paper-dim','fill-opacity'),'var(--stamp-paper-dim-opacity)');
assert.equal(light.querySelector('.stamp-stage-dim').attributes.mask,'url(#stamp-stage-mask)');
assert.equal(light.querySelector('.stamp-fx-atmosphere').attributes.mask,'url(#stamp-stage-mask)');
assert.equal(property('.stamp-stage-dim','fill'),'var(--stamp-dim)');
assert.equal(property('.stamp-stage-dim','fill-opacity'),'var(--stamp-dim-opacity)');
assert.equal(property('#stamp-filing-vignette stop','stop-color'),'var(--stamp-paper-dim)');
near(Number(tokens['--stamp-cone-opacity']),config.theme==='dark'?.6:.75);
near(Number(tokens['--stamp-beam-haze']),config.theme==='dark'?.22:.3);
for(const name of ['post','filing']){
  const beam=light.querySelector(`.stamp-beam-${name}`),gradient=light.querySelector(`#stamp-light-${name}`);
  assert.equal(gradient.attributes.gradientUnits,'userSpaceOnUse');assert.equal(gradient.children.length,3);
  assert.equal(beam.parent.attributes.mask,'url(#stamp-ink-mask)');
  assert.equal(beam.querySelector('.stamp-beam-cone').attributes.fill,`url(#stamp-light-${name})`);
}
assert.ok(!light.querySelectorAll('filter').length&&!rule('.stamp-spotlight').includes('filter'));
assert.equal(property('.stamp-filing-dim','fill'),'url(#stamp-filing-vignette)');
assert.ok(Number(light.querySelector('#stamp-filing-vignette').attributes.r)>0);
const boxOf=node=>{const a=node.attributes;return {x:Number(a.x),y:Number(a.y),width:Number(a.width),height:Number(a.height)};};
const local=node=>{const a=node.getBoundingClientRect();return {x:a.left,y:a.top-stageTop,width:a.width,height:a.height};};
function contains(polygon,box){
  const points=polygon.attributes.points.split(' ').map(pair=>pair.split(',').map(Number));
  assert.ok(points.length>=3);assert.ok(points.flat().every(Number.isFinite));
  for(const [x,y] of [[box.x,box.y],[box.x+box.width,box.y],[box.x+box.width,box.y+box.height],[box.x,box.y+box.height]]){
    const sides=points.map(([ax,ay],i)=>{const [bx,by]=points[(i+1)%points.length];return (bx-ax)*(y-ay)-(by-ay)*(x-ax);});
    assert.ok(sides.every(v=>v>=-1e-7)||sides.every(v=>v<=1e-7),'Cone includes all four target corners');
  }
}
for(let index=0;index<cards.length;index++)if(cards[index].score!==null){
  for(const age of [2.35,2.55,2.75,3,3.76,4.1,4.6]){
    seek(starts[index]+age);
    const names=age>=3.7?['post','row','compare']:['row'];
    for(const name of names){
      const ink=boxOf(light.querySelector(`.stamp-ink-hole-${name}`));
      const dim=boxOf(light.querySelector(`.stamp-dim-hole-${name}`));
      near(dim.x,ink.x-6);near(dim.y,ink.y-6);near(dim.width,ink.width+12);near(dim.height,ink.height+12);
      contains(light.querySelector(`.stamp-beam-${name==='post'?'post':'filing'} .stamp-beam-cone`),ink);
      if(age>=3){
        const rows=passage(index).querySelectorAll('.stamp-ledger-row');
        const expected=local(name==='post'?find(moving[index],'stamp-number'):name==='row'&&age>=3.7&&cards[index].excerpt.derivation?
          rows[rows.length-1]:find(passage(index),name==='row'?'stamp-passage-row':'stamp-compare'));
        for(const key of ['x','y','width','height'])near(ink[key],expected[key]);
      }
    }
    for(const name of ['post','filing']){
      const gradient=light.querySelector(`#stamp-light-${name}`);
      near(Number(gradient.attributes.x1),Number(robot.dataset.visorX));near(Number(gradient.attributes.y1),Number(robot.dataset.visorY));
    }
    if(phone&&age>=3.7){
      const up=light.querySelector('#stamp-light-post').attributes,down=light.querySelector('#stamp-light-filing').attributes;
      assert.ok(Number(up.y2)<Number(up.y1));assert.ok(Number(down.y2)>Number(down.y1));
    }
    const year=light.querySelector('.stamp-beam-year'),yearHole=boxOf(light.querySelector('.stamp-ink-hole-year'));
    if(cards[index].excerpt.derivation&&age>=3.7&&age<4.5){
      near(Number(year.style.opacity),.28*Math.min(1,(age-3.7)/.12));
      const annual=local(find(passage(index),'stamp-passage-row')),post=local(find(moving[index],'stamp-number'));
      assert.equal(find(passage(index),'stamp-fact').textContent,'416,161');
      assert.ok(passage(index).querySelectorAll('.stamp-ledger-row').at(-1).textContent.includes('102,466'));
      assert.deepEqual(yearHole,annual);contains(year.querySelector('.stamp-beam-cone'),annual);
      const link=light.querySelector('#stamp-light-year').attributes;
      near(Number(link.x1),post.x+post.width/2);near(Number(link.y1),post.y+post.height/2);
    }else{assert.equal(year.style.opacity,'0');near(yearHole.width,0);}
  }
}
// The source follows contain-fit artwork, CSS mirroring, pose cross-fades,
// lean and bob, rather than the center of the robot's containing column.
for(const [time,anchors] of [[1.05,[[414/704,304/744,'post',1]]],[2.95,[[421/704,280/744,'filing',1]]],
  [3.76,[[421/704,280/744,'filing',.5],[416/704,270/744,'front',.5]]],[4.7,[[412/704,300/744,'post',1]]]]){
  seek(time);const transform=robot.style.transform;
  const ty=Number(transform.match(/translate3d\(0px, ([-\d.]+)px/)[1]);
  const angle=Number(transform.match(/rotate\(([-\d.]+)deg\)/)[1])*Math.PI/180;
  const scale=Math.min(robotWidth/704,robotHeight/744),drawWidth=704*scale,drawHeight=744*scale;
  let x=0,y=0;
  for(const [ax,ay,facing,weight] of anchors){
    x+=((robotWidth-drawWidth)/2+(facing==='post'?1-ax:ax)*drawWidth-robotWidth/2)*weight;
    y+=(ay-1)*drawHeight*weight;
  }
  near(Number(robot.dataset.visorX),robotLeft+robotWidth/2+x*Math.cos(angle)-y*Math.sin(angle));
  near(Number(robot.dataset.visorY),robotTop-stageTop+robotHeight+x*Math.sin(angle)+y*Math.cos(angle)+ty);
}
seek(2.4);const searching=boxOf(light.querySelector('.stamp-ink-hole-row'));
seek(2.9);const locked=boxOf(light.querySelector('.stamp-ink-hole-row'));
assert.notEqual(searching.y,locked.y);near(locked.y,local(find(passage(0),'stamp-passage-row')).y);
near(Number(light.querySelector('#stamp-filing-vignette').attributes.cy),locked.y+locked.height/2);
assert.equal(find(passage(0),'stamp-amber-sweep').style.transform,'scaleX(0)');
seek(2.99);assert.ok(Number(find(passage(0),'stamp-fact').style['--stamp-bloom'])>.99);
seek(3.56);near(scaleX(find(passage(0),'stamp-amber-sweep')),1);
seek(3.5);assert.equal(light.querySelector('.stamp-stage-dim').style.opacity,'0');near(Number(light.querySelector('.stamp-filing-dim').style.opacity)*dimOpacity,dimOpacity);
seek(4.1);near(Number(light.querySelector('.stamp-stage-dim').style.opacity)*dimOpacity,dimOpacity);assert.equal(light.querySelector('.stamp-filing-dim').style.opacity,'0');
near(Number(light.querySelector('.stamp-paper-dim').style.opacity),1);
assert.deepEqual(boxOf(light.querySelector('.stamp-paper-dim')),local(filingBox));
assert.deepEqual(boxOf(light.querySelector('.stamp-stage-hole-paper')),local(filingBox));
for(const bar of light.querySelectorAll('.stamp-letterbox rect'))near(Number(bar.attributes.height),letterboxHeight);
assert.equal(light.querySelector('.stamp-letterbox').style.opacity,'1');
// CSS padding reserves the matching bars outside every text-bearing region.
near(px('.stamp-stage','padding-block'),letterboxHeight);
const textEnvelope=[...scene.querySelectorAll('.stamp-panel-label'),track,filingBox,
  scene.querySelector('.stamp-caption'),scene.querySelector('.stamp-strip')].map(local);
assert.equal(property('.stamp-spotlight','overflow'),'hidden');
function intersects(a,b){return a.width>0&&a.height>0&&a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;}
for(const time of [3.701,3.76,3.95,4.1,4.8,5.3,5.4,5.549]){
  seek(time);
  for(const bar of light.querySelectorAll('.stamp-letterbox rect')){
    const envelope=boxOf(bar),dy=Number(bar.style.transform.match(/, ([-\d.]+)px/)[1]);envelope.y+=dy;
    // Sliding portions outside the SVG viewport are clipped, including above
    // the phone strip and below the tablet's 10px strip gap.
    const bottom=Math.min(stageHeight,envelope.y+envelope.height);envelope.y=Math.max(0,envelope.y);
    envelope.height=Math.max(0,bottom-envelope.y);
    for(const text of textEnvelope)assert.ok(!intersects(envelope,text),`Letterbox clears labels, panels, caption and controls @ ${viewport}px / ${time}s`);
  }
}
seek(4.1);
const motes=light.querySelectorAll('.stamp-dust');assert.equal(motes.length,6);assert.ok(motes.every(mote=>Number(mote.style.opacity)>0));
const dustOnce=JSON.stringify(motes.map(snapshot));seek(4.2);assert.notEqual(JSON.stringify(motes.map(snapshot)),dustOnce);seek(4.1);assert.equal(JSON.stringify(motes.map(snapshot)),dustOnce);
seek(4.799);assert.equal(light.querySelector('.stamp-beam-post').style.opacity,'1');
seek(4.8);assert.equal(light.querySelector('.stamp-beam-post').style.opacity,'0');assert.equal(light.querySelector('.stamp-beam-filing').style.opacity,'0');near(Number(light.querySelector('.stamp-impact-flash').style.opacity),.7);
seek(4.84);near(Number(light.querySelector('.stamp-impact-flash').style.opacity),.35);
seek(4.88);assert.equal(light.querySelector('.stamp-impact-flash').style.opacity,'0');
seek(5.05);near(Number(light.querySelector('.stamp-stage-dim').style.opacity),0);assert.equal(light.querySelector('.stamp-letterbox').style.opacity,'1');
seek(5.55);assert.equal(light.querySelector('.stamp-letterbox').style.opacity,'0');
seek(4.1);intersection([{isIntersecting:true}]);pause.events.click();const reads=layoutReads;
step(1000);step(1016);step(1032);step(1048);assert.equal(layoutReads,reads,'Clock frames never read layout');
"""

VFX = r"""
const light=scene.querySelector('.stamp-spotlight');
const preloads=()=>created.filter(node=>node.classList.contains('stamp-fx-preload'));
const sources=light.querySelectorAll('image[data-texture]');
assert.equal(preloads().length,0,'Offscreen initialization never fetches VFX');
assert.ok(sources.length>7);assert.ok(sources.every(node=>!node.attributes.href));
seek(4.1);
if(config.reduced){
  assert.equal(preloads().length,0);assert.ok(sources.every(node=>!node.attributes.href));
  assert.equal(property('.stamp-spotlight','display'),'none');
}else{
  assert.deepEqual(preloads().map(node=>node.dataset.texture).sort(),
    ['beam-cone','beam-pool','dust-motes','film-grain','impact-burst','lens-flare','vignette']);
  for(const image of preloads()){
    assert.equal(image.src,`img/fx/${image.dataset.texture}.webp`);
    image.events.error();
    assert.equal(light.querySelector('.stamp-beam-post').style.opacity,'1','Flat fallback stays lit even if every texture fails');
    assert.equal(light.querySelector('.stamp-beam-filing').style.opacity,'1');
    assert.ok(sources.filter(node=>node.dataset.texture===image.dataset.texture).every(node=>!node.attributes.href));
  }
  for(const image of preloads())image.events.load();
  assert.ok(sources.every(node=>node.attributes.href===`img/fx/${node.dataset.texture}.webp`));
  assert.ok(!sources.some(node=>node.attributes.href.includes('contact.png')));
  const dust=preloads().find(node=>node.dataset.texture==='dust-motes');dust.events.error();
  assert.ok(sources.filter(node=>node.dataset.texture==='dust-motes').every(node=>!node.attributes.href));
  assert.ok(sources.filter(node=>node.dataset.texture!=='dust-motes').every(node=>node.attributes.href),'A failed plate leaves all other textures intact');
  dust.events.load();
  assert.equal(preloads().length,7);
  assert.equal(property('.stamp-fx-screen','mix-blend-mode'),'screen');
  assert.equal(property('.stamp-fx-grain','mix-blend-mode'),'soft-light');
  for(const name of ['post','filing','year']){
    assert.equal(light.querySelector(`#stamp-fx-cone-${name}`).attributes['mask-type'],'luminance');
    assert.equal(light.querySelector(`#stamp-fx-dust-${name}`).attributes['mask-type'],'luminance');
    assert.equal(light.querySelector(`#stamp-fx-dust-${name}-tile`).attributes.width,'512');
    assert.equal(light.querySelector(`#stamp-fx-clip-${name} polygon`).attributes.points,
      light.querySelector(`.stamp-beam-${name} .stamp-beam-cone`).attributes.points);
  }
  assert.equal(light.querySelector('#stamp-fx-grain-tile').attributes.width,'256');
  const grain=light.querySelector('.stamp-fx-grain'),vignette=light.querySelector('.stamp-fx-vignette');
  const flare=light.querySelector('.stamp-fx-flare-wrap'),burst=light.querySelector('.stamp-fx-burst-wrap');
  const burstSource=light.querySelector('#stamp-fx-burst image');
  assert.equal(grain.parent.parent.attributes.mask,'url(#stamp-dim-mask)');
  assert.equal(vignette.parent,grain.parent,'Atmosphere preserves the lit targets\' paper colour');
  seek(2.2);assert.equal(grain.style.opacity,'0');assert.equal(vignette.style.opacity,'0');
  seek(2.95);near(Number(grain.style.opacity),.1);near(Number(vignette.style.opacity),.24);
  near(Number(grain.attributes.width),filingBox.getBoundingClientRect().width);assert.equal(flare.style.opacity,'1');
  seek(4.1);near(Number(grain.attributes.width),sceneWidth);near(Number(vignette.attributes.height),stageHeight);
  const locked=fingerprint();seek(4.2);assert.notEqual(fingerprint(),locked);seek(4.1);assert.equal(fingerprint(),locked);
  for(let index=0;index<cards.length;index++){
    const strike=starts[index]+(cards[index].score===null?3:4.8);
    seek(strike-.001);assert.equal(burst.style.opacity,'0');
    seek(strike);assert.equal(burst.style.opacity,'1');near(Number(burstSource.attributes.width),0);
    assert.equal(flare.style.opacity,'0');
    for(const name of ['post','filing','year'])assert.equal(light.querySelector(`.stamp-beam-${name}`).style.opacity,'0');
    seek(strike+.055);near(Number(burstSource.attributes.width),140);near(Number(burst.style.opacity),.8625);
    const growing=fingerprint();seek(0);seek(strike+.055);assert.equal(fingerprint(),growing);
    seek(strike+.11);near(Number(burstSource.attributes.width),160);
    seek(strike+.2);near(Number(burst.style.opacity),.5);
    seek(strike+.4);assert.equal(burst.style.opacity,'0');assert.equal(grain.style.opacity,'0');assert.equal(vignette.style.opacity,'0');
  }
  seek(4.1);motion.matches=true;onMotion();
}
for(const name of ['post','filing','year'])assert.equal(light.querySelector(`.stamp-beam-${name}`).style.opacity,'0');
for(const name of ['flare','burst'])assert.equal(light.querySelector(`.stamp-fx-${name}-wrap`).style.opacity,'0');
for(const name of ['grain','vignette'])assert.equal(light.querySelector(`.stamp-fx-${name}`).style.opacity,'0');
"""

CAPTIONS = r"""
const beat=scene.querySelector('.stamp-caption-beat'),word=scene.querySelector('.stamp-caption-verdict');
const bubble=scene.querySelector('.stamp-caption'),band=scene.querySelector('.stamp-robot-band');
assert.equal(bubble.parent,band);assert.equal(robot.parent,band);
assert.equal(property('.stamp-caption','height'),property('.stamp-caption','min-height'),'Caption changes cannot move the measured visor');
const compact=value=>value.replace(/-?\d+\.\d+/,number=>Number(number).toFixed(1));
function check(language){
  for(let index=0;index<cards.length;index++){
    const card=cards[index],can=card.score!==null;
    const kind=card.kind==='opinion'?(language==='en'?'Opinion':'看法'):(language==='en'?'Forecast':'預測');
    const verdict=language==='en'?(card.verdict==='supported'?'TRUE':can?'FALSE':"CAN'T CHECK"):(card.verdict==='supported'?'正確':can?'錯誤':'無法查核');
    const examples=can?[[1.05,language==='en'?'Reading the post…':'正在讀貼文⋯'],
      [1.8,language==='en'?`Opening the ${card.excerpt.form}…`:`正在打開 ${card.excerpt.form}⋯`],
      [2.95,language==='en'?`Found it: ${card.excerpt.value}`:`找到了：${card.excerpt.value}`],
      [4.1,card.excerpt.derivation?(language==='en'?"That's the full year":"那是全年數字"):
        language==='en'?`${compact(card.filed_value_display)} filed vs ${compact(card.stated_value_display)} posted`:`財報 ${compact(card.filed_value_display)} vs 貼文 ${compact(card.stated_value_display)}`],
      [4.94,verdict],[5.6,verdict]]:[[1.05,language==='en'?'Reading the post…':'正在讀貼文⋯'],
      [2.4,language==='en'?`${kind} — not in any filing`:`${kind} — 不在任何財報中`],[3.14,verdict],[4,verdict]];
    for(const [age,expected] of examples){
      seek(starts[index]+age);assert.equal(beat.textContent,expected,`${card.id} @ ${age}`);
      assert.equal(word.textContent,verdict);assert.equal(word.hidden,!phone||age!==4.1);
    }
  }
}
check(config.language);const other=config.language==='en'?'zh':'en';context.stamps.setLanguage(other);conveyor.localize();check(other);
"""

PHONE_MAXIMA = r"""
assert.ok(phone);assert.ok(intrinsicReads>0);
const expectedPost=Math.ceil(Math.max(...naturalPostHeights));
const expectedFiling=Math.ceil(Math.max(124,...naturalFilingHeights.map(h=>h+14)));
near(postHeight,expectedPost);near(filingHeight,expectedFiling);
const once=intrinsicReads,heights=[postHeight,filingHeight,stageHeight,sceneHeight];
for(let index=0;index<cards.length;index++)for(const age of [.1,1.05,2.4,3.14,4.1]){
  seek(starts[index]+age);assert.deepEqual([postHeight,filingHeight,stageHeight,sceneHeight],heights);
}
onResize();onResize();assert.equal(intrinsicReads,once,'Seeks and observer echoes never remeasure the card set');
assert.equal(property('.stamp-strip','display'),'flex');assert.equal(property('.stamp-progress','display'),'flex');
near(stripHeight,32);assert.equal(property('.stamp-next','display'),'none');
assert.equal(property('.stamp-pause-label','display'),'none');assert.equal(property('.stamp-pause-icon','display'),'inline');
const hiddenLabel='.stamp-progress li:not(.is-active) > [data-i18n]';
assert.equal(property(hiddenLabel,'position'),'absolute');assert.equal(property(hiddenLabel,'clip-path'),'inset(50%)');
assert.equal(property('.stamp-progress li.is-active','flex'),'1');
assert.ok(!html.includes('stamp-desk')&&!html.includes('stamp-folder-tab'));
seek(4.1);const label=config.language==='en'?'Play':'播放';assert.equal(pause.attributes['aria-label'],label);
assert.equal(scene.querySelector('.stamp-pause-label').textContent,label);assert.equal(scene.querySelector('.stamp-pause-icon').attributes['aria-hidden'],'true');
pause.events.click();assert.equal(pause.attributes['aria-label'],config.language==='en'?'Pause':'暫停');
naturalPostHeights[3]=245.6;naturalFilingHeights[1]=211.1;
seek(1);assert.equal(intrinsicReads,once);near(postHeight,expectedPost);
onFonts();assert.ok(intrinsicReads>once,'A completed font load invalidates intrinsic maxima');near(postHeight,246);near(filingHeight,226);
const afterFont=intrinsicReads;onResize();seek(12.1);assert.equal(intrinsicReads,afterFont);
context.stamps.setLanguage(config.language==='en'?'zh':'en');conveyor.localize();assert.ok(intrinsicReads>afterFont);
assert.equal(scene.classList.contains('is-measuring'),false);assert.ok(sceneHeight<=600);
"""

CARD_FITS = r"""
// Feed actual measurement responses to the production sizing path. Each source
// kind must be able to determine the maximum, including a tall desktop repost.
const selected=cards.map((card,index)=>card.source_kind===config.sourceKind?index:-1).filter(i=>i>=0);
assert.ok(selected.length);
selected.forEach(index=>{naturalPostHeights[index]=phone?250.2:442.2;
  if(cards[index].excerpt)naturalFilingHeights[index]=phone?196.2:270.2;});
onFonts();
const inset=2*(length(property('.stamp-filing-box','padding').split(' ')[0])+1);
for(const index of selected){
  seek(starts[index]+(cards[index].score===null?3.14:4.1));
  assert.ok(postHeight>=Math.ceil(naturalPostHeights[index]),`${cards[index].id}: post fits`);
  if(cards[index].excerpt)assert.ok(filingHeight>=Math.ceil(naturalFilingHeights[index]+inset),`${cards[index].id}: paper fits`);
  const body=moving[index].children[0];
  assert.ok(find(body,'stamp-review'));
  if(cards[index].source_kind==='repost')assert.ok(find(body,'stamp-gap').textContent.includes('6.2%'));
}
const reads=intrinsicReads,heights=[postHeight,filingHeight,sceneHeight];
for(const index of selected)for(const age of [.1,2.5,4.1])seek(starts[index]+age);
onResize();assert.equal(intrinsicReads,reads);assert.deepEqual([postHeight,filingHeight,sceneHeight],heights);
assert.equal(property('.stamp-claim','font-family'),'var(--font)');
assert.equal(property('.stamp-card[data-source-kind="article"] .stamp-claim','font-family'),'var(--font-document)');
assert.equal(property('.stamp-number','font-weight'),'800');
assert.equal(px('.stamp-avatar','width'),phone?44:56);
assert.equal(property('.stamp-filing-box','overflow'),'hidden');
assert.equal(property('.stamp-stack-edge','bottom'),'0');
assert.ok(!property('.stamp-filing-box::after','inset').includes('-'));
if(phone){
  assert.ok(sceneHeight<=600,`${config.sourceKind}: phone scene ${sceneHeight}`);
  assert.equal(property('.stamp-review','margin-top'),'auto','Review stays at the bottom of the phone card');
  assert.equal(property('.stamp-filing-authority','white-space'),'nowrap');
  assert.equal(property('.stamp-passage-section','display'),'none');
  assert.equal(property('.stamp-period','display'),'table','The compact period avoids a body-sized line box');
  assert.equal(property('.stamp-filing-content .stamp-derivation','display'),'none','The ledger shows all operands without a repeated footnote');
}
"""

BASELINES = r"""
assert.ok(!phone);
for(let index=0;index<cards.length;index++)if(cards[index].score!==null){
  seek(starts[index]+4.1);
  const paper=passage(index),compare=find(paper,'stamp-compare');
  const value=find(paper,'stamp-compare-filed')||compare.querySelector('.is-result .stamp-ledger-value');
  const filed=value.getBoundingClientRect(),meter=find(moving[index],'stamp-meter').getBoundingClientRect();
  near(filed.bottom,meter.top+meter.height/2);
  assert.ok(compare.getBoundingClientRect().top>=find(paper,'stamp-passage-row').getBoundingClientRect().bottom);
  assert.ok(compare.getBoundingClientRect().bottom<filingBox.getBoundingClientRect().bottom-12);
  assert.ok(Number.isFinite(parseFloat(paper.style['--stamp-compare-top'])));
}
"""

REDUCED_SPOTLIGHT = r"""
assert.equal(property('.stamp-spotlight','display'),'none');
for(const time of [2.4,2.99,4.1,4.8,4.84,5.3,12.1,18.4,49]){
  seek(time);
  for(const name of ['stamp-stage-dim','stamp-paper-dim','stamp-filing-dim','stamp-beam-post','stamp-beam-filing','stamp-impact-flash','stamp-letterbox'])
    assert.equal(scene.querySelector(`.${name}`).style.opacity,'0',`${name} @ ${time}`);
  assert.ok(scene.querySelectorAll('.stamp-dust').every(mote=>mote.style.opacity==='0'));
}
assert.ok(still.every(item=>item.children[0].tabIndex===0));assert.equal(callbacks.size,0);
assert.equal(created.filter(node=>node.src?.includes('/auditor/')).length,0);
"""

POSE_CANVAS = r"""
seek(3);const image=robot.querySelectorAll('.stamp-robot-pose').find(node=>node.dataset.pose==='point');
const before=Number(robot.dataset.visorY),reads=intrinsicReads;
image.naturalWidth=1152;image.naturalHeight=512;image.events.load();
assert.notEqual(Number(robot.dataset.visorY),before,'Contain-fit follows the newly loaded canvas');
assert.equal(intrinsicReads,reads,'Artwork loads never remeasure phone content maxima');
near(Number(scene.querySelector('#stamp-light-filing').attributes.y1),Number(robot.dataset.visorY));
const loaded=fingerprint();seek(13);seek(3);assert.equal(fingerprint(),loaded);
image.events.error();assert.equal(image.src,'img/auditor/H/present.webp');assert.equal(robot.dataset.pose,'point');
assert.equal(intrinsicReads,reads);assert.notEqual(fingerprint(),loaded,'Fallback artwork uses its own visor anchor');
"""

HOVER = r"""
seek(1.05);
const layers=robot.querySelectorAll('.stamp-thruster');
const shadow=scene.querySelector('.stamp-floor-shadow');
assert.equal(layers.length,2);assert.equal(robot.dataset.character,'H');
assert.equal(property('.stamp-thruster','z-index'),'0');assert.equal(property('.stamp-robot-pose','z-index'),'1');
assert.equal(property('.stamp-floor-shadow','position'),'absolute');
const urls=new Set(created.filter(node=>node.src?.includes('/auditor/')).map(node=>node.src));
assert.equal(urls.size,18);assert.ok([...urls].every(url=>url.includes('/H/')));
for(const time of [1.05,1.56,2.95,3.76,4.799,4.8,4.86,4.94,5.049,5.05,5.3,19.06]){
  seek(time);
  const once=fingerprint();seek(70);seek(time);assert.equal(fingerprint(),once);
  const scale=Math.min(robotWidth/704,robotHeight/744);
  const nozzleX=robotWidth/2,nozzleY=robotHeight-(744-520)*scale;
  for(const layer of layers){
    near(Number(layer.dataset.nozzleX),nozzleX);near(Number(layer.dataset.nozzleY),nozzleY);
    assert.ok(layer.style.transform.includes(`scaleX(${layer.dataset.facing==='post'?-1:1})`));
    const visible=layer.querySelectorAll('.stamp-thruster-frame').filter(image=>image.style.opacity==='1');
    assert.equal(visible.length,1);assert.equal(visible[0].dataset.frame,robot.dataset.thruster);
    const age=api.getState().localTime,strike=cards[starts.findLastIndex(at=>time>=at)].score===null?3:4.8;
    const burst=age>=strike&&age<strike+.25;
    near(Number(layer.dataset.scale),burst?1.6:1);
    if(burst)assert.equal(layer.dataset.frame,'burst');
    else assert.equal(layer.dataset.frame,String(Math.floor(time*1000/80)%6));
  }
}
seek(4.86);near(Number(robot.dataset.dip),8);
for(const layer of layers)near(Number(layer.style.opacity),.5);
seek(4.799);near(Number(robot.dataset.dip),0);assert.notEqual(robot.dataset.thruster,'burst');
seek(5.02);near(Number(robot.dataset.dip),0);assert.equal(robot.dataset.thruster,'burst');
seek(5.05);assert.notEqual(robot.dataset.thruster,'burst');
seek(api.timing.floatPeriod/4);assert.ok(Math.abs(Number(robot.dataset.bob)-4)<.001);const down=Number(shadow.dataset.scale),floor=shadow.style.transform.split(' scale(')[0];
seek(api.timing.floatPeriod*3/4);assert.ok(Math.abs(Number(robot.dataset.bob)+4)<.001);assert.ok(Number(shadow.dataset.scale)<down);
assert.equal(shadow.style.transform.split(' scale(')[0],floor,'Floor remains stationary while body floats');
// Check the actual exported jet alpha bounds at every strike, including the
// worst bob phase. The phone has only a 96px band around its 88px robot box.
const art=JSON.parse(readFileSync(`${root}/docs/site/img/auditor/H/manifest.json`,'utf8'));
if(phone)for(let index=0;index<cards.length;index++)for(const offset of [0,.02,.06,.10,.14,.22,.249,.25]){
  const strike=cards[index].score===null?3:4.8;
  seek(starts[index]+strike+offset);
  const bodyScale=Math.min(robotWidth/704,robotHeight/744);
  const angle=Number(robot.style.transform.match(/rotate\(([-\d.]+)deg\)/)[1])*Math.PI/180;
  const ty=Number(robot.dataset.bob)+Number(robot.dataset.dip);
  const bandBottom=track.getBoundingClientRect().bottom+96;
  for(const layer of layers){
    const bounds=art.thruster.frames[`thruster-${layer.dataset.frame}`].bbox;
    const factor=Number(layer.dataset.scale),mirror=layer.dataset.facing==='post'?-1:1;
    for(const ax of [bounds[0],bounds[2]])for(const ay of [bounds[1],bounds[3]]){
      const x=Number(layer.dataset.nozzleX)+(ax-80)*bodyScale*factor*mirror-robotWidth/2;
      const y=Number(layer.dataset.nozzleY)+(ay-20)*bodyScale*factor-robotHeight;
      const bottom=robotTop+robotHeight+x*Math.sin(angle)+y*Math.cos(angle)+ty;
      assert.ok(bottom<=bandBottom,`Jet clears filing label @ ${index}/${offset}: ${bottom} <= ${bandBottom}`);
    }
  }
}
seek(4.94);
for(const layer of layers){layer.querySelectorAll('.stamp-thruster-frame').find(image=>image.dataset.frame==='burst').events.error();}
assert.equal(robot.dataset.pose,'stamp-down');assert.ok(layers.every(layer=>layer.dataset.frame==='0'));
assert.ok(robot.querySelectorAll('.stamp-robot-pose').every(image=>image.src.includes('/H/')));
"""

POLISH = r"""
for (let i=0;i<cards.length;i++) {
  const card=cards[i];
  for(const group of [moving,still]) {
    const body=find(group[i],'stamp-card');
    assert.equal(body.dataset.sourceKind,card.source_kind);
    assert.equal(find(body,'stamp-example').textContent,config.language==='zh'?'示範貼文':'Example post');
    assert.equal(find(body,'stamp-input-badge').textContent,config.language==='zh'?'文字':'Text');
    assert.equal(find(body,'stamp-input-badge').dataset.inputKind,'text');
    for(const name of ['stamp-waveform','stamp-frame','stamp-transcript'])assert.equal(body.querySelectorAll('.'+name).length,0);
    for(const avatar of body.querySelectorAll('.stamp-avatar')) {
      assert.ok(avatar.src.endsWith('-256.webp'));assert.equal(avatar.loading,'lazy');
    }
    assert.equal(find(body,'stamp-claim').textContent,card.text[config.language||'en']);
    if(card.source_kind==='thread')assert.equal(find(body,'stamp-thread-index').textContent,card.thread_index);
    const actions=find(body,'stamp-actions');
    if(card.source_kind!=='article') {
      assert.equal(actions.querySelectorAll('svg').length,4);
      for(const count of Object.values(card.example_activity))assert.ok(actions.textContent.includes(count.toLocaleString('en-US')));
      assert.equal(find(actions,'stamp-activity-label').textContent,config.language==='zh'?'示範互動':'Example activity');
    }
    if(card.source_kind==='social')assert.equal(body.querySelectorAll('.stamp-audience svg').length,1);
    if(card.source_kind==='repost') {
      const original=cards.find(c=>c.id===card.same_claim_as),quote=find(body,'stamp-quote-card');
      assert.ok(quote.querySelector('.stamp-quote-header'));
      assert.equal(find(quote,'stamp-original-author').textContent,original.persona.name[config.language||'en']);
      assert.equal(find(quote,'stamp-post-date').textContent,original.post_date);
      assert.equal(find(quote,'stamp-claim').textContent,original.text[config.language||'en']);
    }
    if(card.source_kind==='article') {
      assert.equal(find(body,'stamp-article-lead').textContent,card.article.lead[config.language||'en']);
      const masthead=find(body,'stamp-masthead');assert.equal(masthead.loading,'lazy');
      assert.equal(masthead.dataset.src,'img/polish/banana-masthead.webp');
      assert.equal(body.querySelectorAll('.stamp-article-picture').length,2);
      masthead.events.error();assert.ok(find(body,'stamp-identity').classList.contains('masthead-unavailable'));
      assert.equal(find(body,'stamp-author').textContent,card.persona.name[config.language||'en']);
    }
  }
  const paper=passage(i);
  if(paper) {
    assert.equal(find(paper,'stamp-filing-authority').textContent,'UNITED STATES SECURITIES AND EXCHANGE COMMISSION');
    assert.equal(find(paper,'stamp-passage-meta').textContent,'FORM '+card.excerpt.form);
    const time=find(paper,'stamp-filing-date').querySelector('time');
    assert.equal(time.dateTime,card.excerpt.filed);assert.ok(time.textContent.endsWith(card.excerpt.filed));
  }
}
for(const art of created.filter(n=>n.classList.contains('stamp-polish-art'))) {
  assert.equal(art.loading,'lazy');assert.equal(art.decoding,'async');assert.equal(art.alt,'');
}
if(!config.reduced) {
  seek(3.8);
  const number=find(moving[0],'stamp-number'),row=find(passage(0),'stamp-passage-row');
  number.testOffset=21;row.testOffset=13;
  layoutReads=0;find(passage(0),'stamp-date-ring').events.load();
  assert.ok(layoutReads>0,'Artwork completion invalidates cached light geometry');
  seek(3.8);
  const target=number.getBoundingClientRect(),origin=stage.getBoundingClientRect();
  near(Number(scene.querySelector('.stamp-pool-post').attributes.cx),target.left-origin.left+target.width/2);
  const fact=row.getBoundingClientRect();
  near(Number(scene.querySelector('.stamp-pool-row').attributes.cx),fact.left-origin.left+fact.width/2);
  intersection([{isIntersecting:true}]);pause.events.click();
  layoutReads=0;step(0);step(16);assert.equal(layoutReads,0,'The scene clock never reads layout');
}
"""

MEDIA = r"""
const expected=config.expectedInput,labels=config.language==='zh'?{text:'文字',audio:'音訊',video:'影片',screenshot:'截圖'}:
  {text:'Text',audio:'Audio',video:'Video',screenshot:'Screenshot'};
for(const group of [moving,still]) {
  const body=find(group[0],'stamp-card'),badge=find(body,'stamp-input-badge');
  assert.equal(badge.dataset.inputKind,expected);assert.equal(badge.textContent,labels[expected]);
  const media=find(body,'stamp-input-media');
  if(expected==='text'){assert.equal(media,undefined);continue;}
  assert.ok(media);
  if(expected==='audio') {
    assert.equal(find(media,'stamp-waveform').children.length,config.inputPayload.waveform.length);
    assert.deepEqual(find(media,'stamp-waveform').children.map(n=>Number(n.style['--sample'])),config.inputPayload.waveform);
    assert.equal(find(media,'stamp-transcript').textContent,config.inputPayload.transcript[config.language||'en']);
    assert.equal(find(media,'stamp-media-time').textContent,config.inputPayload.timestamp);
  } else {
    assert.equal(find(media,'stamp-frame').dataset.src,config.inputPayload.thumbnail);
    if(expected==='video')assert.equal(find(media,'stamp-media-time').textContent,config.inputPayload.timestamp);
    else assert.equal(find(media,'stamp-media-time'),undefined);
  }
}
const before=fingerprint();seek(2);seek(3);seek(2);const first=fingerprint();seek(1);seek(2);assert.equal(fingerprint(),first);
"""
