"""Execute shipped form/trace JS in the existing offline DOM adapter."""
import json
import subprocess

import pytest

from claimcheck.correction import build_corrections
from test_site_stamps_runtime import ROOT, run_check as run_scene_check


def run_check(script, **config):
    config.setdefault("page", "docs/site/index.html")
    run_scene_check(script, **config)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_homepage_boot_leaves_legacy_anchors_and_historical_data_on_evidence_page(language):
    run_check(HOMEPAGE_BOOT, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_saved_trace_has_ordered_public_steps_sec_row_and_safe_text(language, viewport):
    run_check(RENDER, language=language, viewport=viewport)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_saved_post_renders_one_cited_edit_reasons_and_result_section_order(language, viewport):
    page = "docs/zh/index.html" if language == "zh" else "docs/site/index.html"
    run_check(POST_RENDER, page=page, language=language, viewport=viewport)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_default_post_example_saved_selection_and_hero_entry(language):
    page = "docs/zh/index.html" if language == "zh" else "docs/site/index.html"
    run_check(DEFAULT_POST, page=page, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_live_submit_busy_success_failure_and_language_switch(language):
    run_check(FORM, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("blocked", [False, True])
def test_password_session_storage_errors_and_public_demo(language, blocked):
    run_check(PASSWORD, language=language, blocked=blocked)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("remembered", [False, True])
def test_password_restores_only_from_current_tab_session(language, remembered):
    run_check(RESTORE_PASSWORD, language=language, remembered=remembered)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1440])
def test_budget_remaining_progress_low_warning_midnight_and_stops(language, viewport):
    run_check(BUDGET, language=language, viewport=viewport)


def test_pages_boundary_without_provider_key_or_network():
    result = subprocess.run(["node", "--test", "tests/node/live-boundary.test.mjs"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


HOMEPAGE_BOOT = r"""
const ids=['post-text','claim-list','chart','posthoc-rerun','research-list'];
const labels=ids.map(id=>tree.querySelector('#'+id).textContent);
const requests=[];
context.fetch=async url=>{
  requests.push(url);
  return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/site.json','utf8'))};
};
context.window.addEventListener=()=>{};
context.window.location.hash='';
context.liveTest.setupControls();
await context.liveTest.loadData();
assert.deepEqual(requests,[], 'the homepage must not load the historical chart dataset');
assert.deepEqual(ids.map(id=>tree.querySelector('#'+id).textContent),labels);
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
for(const id of ids)assert.ok(tree.querySelector('#'+id).children.every(child=>child.tagName==='#text'));
const saved=tree.querySelector('#saved-check-details');
assert.ok(!saved.open);
tree.querySelector('a[href="#recorded-run"]').events.click();
assert.equal(saved.open,true);
"""


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 1280])
def test_corrected_draft_keeps_hostile_original_text_and_cites_all_components(language, viewport):
    source = ROOT / "docs/evidence/posts-2026-10-28/demo-thread-baseten"
    record = json.loads((source / "report.json").read_text())["claims"][2]
    trace = json.loads((source / record["trace_path"]).read_text())
    text = '🧵 <img src=x onerror=alert(1)>\nApple revenue in fiscal Q4 2025 was $416.2B.\nFirst ever <script>alert(1)</script>.'
    unchecked = {"text": "First ever <script>alert(1)</script>.", "program_verdict": "unchecked"}
    corrections = build_corrections(text, [*record["program_checks"], unchecked], [trace["tool_calls"][0]["result"]])
    assert len(corrections["edits"]) == 1
    run_check(CORRECTIONS, language=language, viewport=viewport, corrections=corrections)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_correction_deletions_and_insertions_have_aa_text_contrast(theme):
    run_check(CORRECTION_CONTRAST, theme=theme)


CORRECTION_CONTRAST = r"""
const tokens=declarations(':root');
const resolveColor=value=>value.replace(/var\((--[\w-]+)\)/g,(_,name)=>tokens[name]);
const luminance=color=>{
  assert.match(color,/^#[\da-f]{6}$/i);
  return [1,3,5].map(i=>parseInt(color.slice(i,i+2),16)/255)
    .map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4)
    .reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
};
const background=luminance(resolveColor(property('.trace-result','background')));
for(const selector of ['.corrected-draft-text del','.corrected-draft-text strong',
                       '.correction-changes del','.correction-changes strong']){
  const foreground=luminance(resolveColor(property(selector,'color')));
  const contrast=(Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05);
  assert.ok(contrast>=4.5,`${config.theme} ${selector}: ${contrast}`);
}
"""


CORRECTIONS = r"""
context.URL=URL;
const target=tree.querySelector('#live-result');
const result={mode:'live',verdict:'contradicted',events:[],claims:[],evidence:[],corrections:config.corrections};
context.liveTest.renderLiveTrace(result,target);
const section=target.querySelector('.live-corrections'),draft=section.querySelector('.corrected-draft-text');
assert.ok(section.textContent.includes(config.language==='zh'?'修正版草稿——僅核對列出的主張':'Corrected draft — only listed assertions checked'));
assert.ok(section.textContent.includes(config.language==='zh'?'未修正':'Not corrected'));
assert.ok(section.textContent.includes(config.language==='zh'?'此主張未評判':'This assertion was not judged'));
assert.equal(section.querySelector('.correction-scope').textContent,config.language==='zh'?
  '僅核對下方列出的主張；文中其餘內容均未經查證。':
  'Only the assertions listed below were checked; nothing else in the text was verified.');
assert.equal(draft.querySelector('del').textContent,'$416.2B');
assert.equal(draft.querySelector('strong').textContent,'$102.5B');
assert.equal(draft.textContent,config.corrections.original_text.replace('$416.2B','$416.2B → $102.5B'));
assert.equal(section.querySelectorAll('a').length,2);
for(const link of section.querySelectorAll('a'))assert.ok(link.href.startsWith('https://www.sec.gov/Archives/edgar/data/320193/'));
assert.equal(section.querySelectorAll('img').length,0);assert.equal(section.querySelectorAll('script').length,0);
assert.ok(section.textContent.includes('<img src=x onerror=alert(1)>'));
assert.ok(section.textContent.includes('<script>alert(1)</script>'));
assert.ok(section.textContent.includes('416,161,000,000'));assert.ok(section.textContent.includes('313,695,000,000'));
// Even a malformed/hostile origin payload cannot create markup or active URLs.
const unsafe=JSON.parse(JSON.stringify(result));
unsafe.corrections.edits[0].replacement='<img src=x onerror=alert(1)>';
unsafe.corrections.edits[0].citations.push({url:'javascript:alert(1)',form:'<svg onload=alert(1)>'},
  {url:'https://www.sec.gov.evil.test/Archives/edgar/data/1/file'},
  {url:'https://evil@www.sec.gov/Archives/edgar/data/1/file'},
  {url:'https://www.sec.gov:444/Archives/edgar/data/1/file'});
context.liveTest.renderLiveTrace(unsafe,target);
assert.equal(target.querySelectorAll('a').length,2);assert.equal(target.querySelectorAll('img').length,0);
assert.equal(target.querySelectorAll('svg').length,0);assert.equal(target.querySelectorAll('script').length,0);
unsafe.corrections.edits[0].start=0;
context.liveTest.renderLiveTrace(unsafe,target);
assert.equal(target.querySelector('.corrected-draft-text').textContent,config.corrections.original_text);
assert.equal(target.querySelectorAll('del').length,0);
// Exercise the same envelope through the form and a subsequent language switch.
context.AbortController=AbortController;context.setTimeout=()=>0;context.clearTimeout=()=>{};
context.fetch=async url=>({ok:true,json:async()=>url==='/api/check'?result:url==='/api/budget'?
  {day:'2026-11-03',daily_limit_usd:3,daily_remaining_usd:3,resets_at:'2099-11-04T00:00:00Z',status:'ready'}:
  JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'))});
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
tree.querySelector('#live-input').value=config.corrections.original_text;
tree.querySelector('#live-password').value='offline-only';
await tree.querySelector('#live-form').events.submit({preventDefault(){}});
assert.equal(target.querySelector('.corrected-draft-text').querySelector('strong').textContent,'$102.5B');
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.ok(target.textContent.includes(config.language==='zh'?'Corrected draft — only listed assertions checked':'修正版草稿——僅核對列出的主張'));
assert.ok(target.textContent.includes(config.language==='zh'?'This assertion was not judged':'此主張未評判'));
"""


POST_RENDER = r"""
context.URL=URL;
const demo=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
const target=tree.querySelector('#recorded-trace');
context.liveTest.renderLiveTrace(demo,target);
const verify=language=>{
  const head=target.querySelector('.trace-head'),corrections=target.querySelector('.live-corrections');
  const evidence=target.querySelector('.live-proof'),trace=target.querySelector('.live-trace');
  assert.deepEqual(target.children.map(node=>node.className),['live-input-read','trace-head','live-corrections','live-proof','live-trace']);
  assert.equal(head.querySelector('.trace-verdict').textContent,language==='zh'?'證據矛盾':'Contradicted');
  assert.equal(evidence.querySelector('.live-claims').querySelectorAll('li').length,5);
  const draft=corrections.querySelector('.corrected-draft-text');
  assert.equal(draft.querySelectorAll('del').length,1);
  assert.equal(draft.querySelectorAll('strong').length,1);
  assert.equal(draft.querySelector('del').textContent,'$416.2 billion');
  assert.equal(draft.querySelector('strong').textContent,'$102.5 billion');
  assert.equal(corrections.querySelector('.correction-changes').children.length,1);
  const links=corrections.querySelectorAll('a');
  assert.equal(links.length,2);
  assert.ok(links[0].href.endsWith('/000032019325000079/'));
  assert.ok(links[1].href.endsWith('/000032019326000020/'));
  assert.ok(corrections.textContent.includes('10-K'));
  assert.ok(corrections.textContent.includes('10-Q'));
  const unchanged=corrections.querySelector('.correction-unchanged');
  assert.equal(unchanged.children.length,4);
  assert.ok(unchanged.textContent.includes(language==='zh'?'程式支持此主張，無須修改。':'The program supports this assertion; no edit needed.'));
  assert.ok(unchanged.textContent.includes(language==='zh'?'此主張未評判（意見或超出範圍）。':'This assertion was not judged (opinion or out of scope).'));
  assert.ok(unchanged.textContent.includes('NVDA at 30x sales is still cheap.'));
  assert.equal(target.querySelectorAll('.trace-step').length,demo.events.length);
};
verify(config.language);
const other=config.language==='zh'?'en':'zh';
context.stamps.setLanguage(other);
context.liveTest.renderLiveTrace(demo,target);
verify(other);
"""

DEFAULT_POST = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
context.window.addEventListener=()=>{};context.window.location.hash='';
const post=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
const claim=JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'));
const original=JSON.parse(readFileSync(root+'/docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json','utf8')).post;
const requests=[];
context.fetch=async url=>{
  requests.push(url);assert.notEqual(url,'/api/check');
  if(url==='/api/budget')return {ok:true,json:async()=>({day:'2026-11-03',daily_limit_usd:3,daily_remaining_usd:3,
    resets_at:'2099-11-04T00:00:00Z',status:'ready'})};
  assert.ok(['/data/live-demo-post.json','/data/live-demo.json'].includes(url));
  return {ok:true,json:async()=>url==='/data/live-demo-post.json'?post:claim};
};
context.liveTest.setupLive();context.liveTest.setupControls();
await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input'),target=tree.querySelector('#recorded-trace');
const postButton=tree.querySelector('[data-saved-demo="post"]'),claimButton=tree.querySelector('[data-saved-demo="claim"]');
input.focus=()=>{};
assert.equal(input.getAttribute('placeholder'),original);assert.ok(Array.from(original).length<=600);
tree.querySelector('#live-example').events.click();assert.equal(input.value,original);
assert.equal(tree.querySelector('#live-count').textContent,Array.from(original).length+' / 600');
assert.equal(context.liveTest.state().savedLiveDemo.input,original);
assert.equal(postButton.getAttribute('aria-pressed'),'true');
assert.equal(claimButton.getAttribute('aria-pressed'),'false');
assert.ok(postButton.textContent.includes(config.language==='zh'?'熱傳貼文':'Saved check · viral post · 28 Oct 2026'));
assert.equal(requests.filter(url=>url==='/data/live-demo.json').length,0);
await claimButton.events.click();
assert.equal(context.liveTest.state().savedLiveDemo.input,claim.input);
assert.equal(claimButton.getAttribute('aria-pressed'),'true');
assert.equal(target.querySelector('.corrected-draft-text').querySelectorAll('del').length,0);
tree.querySelector('#live-example').events.click();assert.equal(input.value,original);
tree.querySelector('a[href="#recorded-run"]').events.click();
assert.equal(tree.querySelector('#saved-check-details').open,true);
assert.equal(context.liveTest.state().savedLiveDemo.input,original);
assert.equal(postButton.getAttribute('aria-pressed'),'true');
assert.equal(target.querySelector('.corrected-draft-text').querySelectorAll('del').length,1);
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.equal(target.querySelector('.corrected-draft-text').querySelectorAll('del').length,1);
assert.equal(context.liveTest.state().savedLiveDemo.input,original);
"""

RENDER = r"""
context.URL=URL;
const demo=JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'));
const target=tree.querySelector('#recorded-trace');
context.liveTest.renderLiveTrace(demo,target);
const corrections=target.querySelector('.live-corrections');
assert.ok(corrections);
assert.equal(corrections.querySelector('.corrected-draft-text').textContent,demo.input);
assert.ok(corrections.querySelector('.correction-unchanged').textContent.includes(config.language==='zh'?
  '程式支持此主張，無須修改。':'The program supports this assertion; no edit needed.'));
assert.ok(corrections.querySelector('.correction-scope').textContent.includes(config.language==='zh'?
  '文中其餘內容均未經查證':'nothing else in the text was verified'));
assert.equal(target.querySelectorAll('.trace-step').length,7);
assert.equal(target.querySelectorAll('.trace-model').length,3);
assert.ok(target.textContent.includes('109,417,000,000'));
assert.ok(target.textContent.includes('FY2026Q3'));
assert.ok(target.textContent.includes('0000320193-26-000020'));
assert.ok(target.textContent.includes('0.01222'));
assert.equal(target.querySelectorAll('a').length,2);
assert.ok(target.textContent.includes('2026-10-28T06:12:13'));
const unsafe=JSON.parse(JSON.stringify(demo));
unsafe.claims[0].text='<img src=x onerror=alert(1)>';
unsafe.evidence[0].filing_url='javascript:alert(1)';
context.liveTest.renderLiveTrace(unsafe,target);
assert.equal(target.querySelectorAll('img').length,0);
assert.ok(target.textContent.includes('<img src=x onerror=alert(1)>'));
assert.equal(target.querySelectorAll('a').length,1);
"""

FORM = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=setTimeout;context.clearTimeout=clearTimeout;
const demo=JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'));
let finish, requests=[];
let remaining=3,budgetReads=0;
const budget=()=>({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:remaining,daily_spent_usd:3-remaining,
  resets_at:'2099-11-03T00:00:00Z',status:remaining===0?'budget_exhausted':'ready'});
// Keep rollover timers inert in this DOM test; the real browser owns them.
context.setTimeout=(fn,ms)=>ms>32000?0:setTimeout(fn,ms);context.clearTimeout=clearTimeout;
context.fetch=async (url,opts)=>{
  if(url==='/data/examples/index.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/examples/index.json','utf8'))};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'))};
  if(url==='/api/budget'){budgetReads++;assert.equal(opts.cache,'no-store');return {ok:true,json:async()=>budget()};}
  requests.push({url,opts});
  return new Promise(resolve=>{finish=resolve;});
};
context.liveTest.setupLive();
await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input'),form=tree.querySelector('#live-form'),submit=tree.querySelector('#live-submit');
input.value=demo.input;
tree.querySelector('#live-password').value='offline-password';
const pending=form.events.submit({preventDefault(){}});
assert.equal(submit.disabled,true);assert.equal(form.getAttribute('aria-busy'),'true');
assert.equal(requests.length,1);assert.equal(requests[0].url,'/api/check');
assert.deepEqual(JSON.parse(requests[0].opts.body),{text:demo.input,password:'offline-password'});
remaining=2.41;
finish({ok:true,json:async()=>({...demo,mode:'live'})});await pending;
assert.equal(budgetReads,2);
assert.ok(tree.querySelector('#live-budget-text').textContent.includes('$2.41'));
assert.equal(submit.disabled,false);assert.equal(form.getAttribute('aria-busy'),'false');
assert.equal(tree.querySelector('#live-result').hidden,false);
assert.equal(tree.querySelector('#live-result').querySelectorAll('.trace-step').length,7);
const failed=form.events.submit({preventDefault(){}});
remaining=0;
finish({ok:false,json:async()=>({error:'budget_exhausted'})});await failed;
assert.equal(budgetReads,3);assert.equal(input.disabled,true);assert.equal(submit.disabled,true);
assert.equal(tree.querySelector('#live-result').hidden,true);
assert.ok(tree.querySelector('#recorded-trace').textContent.includes('FY2025Q4'));
context.stamps.setLanguage('zh');
assert.ok(tree.querySelector('#live-status').textContent.includes('重設'));
context.stamps.setLanguage('en');
assert.ok(tree.querySelector('#live-status').textContent.includes('00:00 UTC'));
await form.events.submit({preventDefault(){}});assert.equal(requests.length,2);
"""

PASSWORD = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
const demo=JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'));
const key='claimcheck.livePassword',credential='offline-password-marker';
const saved=new Map(),writes=[];
context.sessionStorage={
  getItem(key){if(config.blocked)throw new Error('blocked');return saved.get(key)||null;},
  setItem(key,value){if(config.blocked)throw new Error('blocked');writes.push({key,value});saved.set(key,value);},
  removeItem(key){if(config.blocked)throw new Error('blocked');saved.delete(key);}
};
context.localStorage.setItem=()=>assert.fail('password must never enter localStorage');
let requests=[],finish;
context.fetch=async (url,opts)=>{
  if(url==='/data/examples/index.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/examples/index.json','utf8'))};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'))};
  if(url==='/api/budget'){
    assert.ok(!JSON.stringify(opts).includes(credential));
    return {ok:true,json:async()=>({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:3,
      resets_at:'2099-11-03T00:00:00Z',status:'ready'})};
  }
  requests.push({url,opts});
  return new Promise(resolve=>{finish=resolve;});
};
const password=tree.querySelector('#live-password'),form=tree.querySelector('#live-form');
password.value='';password.focus=()=>{};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input');input.value=demo.input;
assert.equal(password.value,'');assert.equal(password.getAttribute('type'),'password');
assert.equal(password.getAttribute('autocomplete'),'off');assert.equal(form.getAttribute('method'),'post');
assert.ok(tree.querySelector('#recorded-trace').textContent.includes('FY2025Q4'));
assert.ok(tree.querySelector('#live-budget-text').textContent.includes('$3.00'));
assert.ok(/submission notes|需要密碼/.test(tree.querySelector('#live-password-note').textContent));
await form.events.submit({preventDefault(){}});assert.equal(requests.length,0);
password.value=credential;
const denied=form.events.submit({preventDefault(){}});
assert.equal(password.disabled,true);assert.equal(writes.length,0);
finish({ok:false,status:401,json:async()=>({error:'unauthorized'})});await denied;
assert.equal(writes.length,0);assert.equal(saved.size,0);assert.equal(password.value,'');
password.value=credential;
const locked=form.events.submit({preventDefault(){}});
finish({ok:false,status:429,json:async()=>({error:'auth_rate_limited'})});await locked;
assert.equal(writes.length,0);assert.ok(tree.querySelector('#live-status').textContent.includes('15'));
const success=form.events.submit({preventDefault(){}});
assert.equal(writes.length,0);
finish({ok:true,status:200,json:async()=>({...demo,mode:'live'})});await success;
assert.equal(password.disabled,false);
assert.deepEqual(writes,config.blocked?[]:[{key,value:credential}]);
for(const {url,opts} of requests){
  assert.equal(url,'/api/check');assert.ok(!JSON.stringify(opts.headers).includes(credential));
  assert.deepEqual(JSON.parse(opts.body),{text:demo.input,password:credential});
}
assert.ok(!JSON.stringify(context.liveTest.state()).includes(credential));
assert.ok(!tree.textContent.includes(credential));
if(!config.blocked){
  // Rotation clears a previously remembered password on the next 401.
  const rotated=form.events.submit({preventDefault(){}});
  finish({ok:false,status:401,json:async()=>({error:'unauthorized'})});await rotated;
  assert.equal(saved.size,0);assert.equal(password.value,'');
}
"""

RESTORE_PASSWORD = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
context.sessionStorage={
  getItem(key){assert.equal(key,'claimcheck.livePassword');return config.remembered?'session-only-marker':null;},
  setItem(){assert.fail('reading a saved password must not save anything');}
};
context.fetch=async url=>{
  assert.notEqual(url,'/api/check');
  if(url==='/api/budget')return {ok:true,json:async()=>({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:3,
    resets_at:'2099-11-03T00:00:00Z',status:'ready'})};
  return {ok:false};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
assert.equal(tree.querySelector('#live-password').value,config.remembered?'session-only-marker':'');
assert.ok(!tree.textContent.includes('session-only-marker'));
"""

BUDGET = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
let data={day:'2026-11-02',daily_limit_usd:3,daily_spent_usd:.59,daily_remaining_usd:2.41,
  resets_at:'2026-11-03T00:00:00Z',status:'ready'};
let fail=false, checks=0;
context.fetch=async url=>{
  if(url==='/api/budget')return {ok:!fail,json:async()=>data};
  if(url==='/api/check'){checks++;assert.fail('stopped input must never submit');}
  return {ok:false};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const text=tree.querySelector('#live-budget-text'),meter=tree.querySelector('#live-budget-meter');
const note=tree.querySelector('#live-budget-note'),input=tree.querySelector('#live-input'),submit=tree.querySelector('#live-submit');
assert.ok(text.textContent.includes('$2.41'));assert.ok(text.textContent.includes('$3.00'));
assert.ok(text.textContent.includes('00:00'));assert.equal(meter.max,3);assert.equal(meter.value,2.41);
assert.equal(input.disabled,false);assert.equal(note.hidden,true);
data={...data,daily_remaining_usd:.09};await context.liveTest.refreshLiveBudget();
assert.equal(note.hidden,false);assert.ok(/Almost used up|即將用完/.test(note.textContent));
data={...data,daily_remaining_usd:.10};await context.liveTest.refreshLiveBudget();assert.equal(note.hidden,true);
data={...data,daily_remaining_usd:0,status:'budget_exhausted'};await context.liveTest.refreshLiveBudget();
assert.equal(input.disabled,true);assert.equal(submit.disabled,true);assert.equal(meter.value,0);
assert.ok(note.textContent.includes('2026-11-03'));assert.ok(note.textContent.includes('00:00'));
await tree.querySelector('#live-form').events.submit({preventDefault(){}});assert.equal(checks,0);
data={...data,day:'2026-11-03',resets_at:'2026-11-04T00:00:00Z',daily_remaining_usd:3,status:'ready'};
await context.liveTest.refreshLiveBudget();assert.equal(input.disabled,false);assert.equal(meter.value,3);
for(const status of ['credit_exhausted','total_budget_exhausted']){
  data={...data,status};await context.liveTest.refreshLiveBudget();
  assert.equal(input.disabled,true);assert.equal(submit.disabled,true);
  assert.ok(/paused|暫停/.test(note.textContent));
  context.stamps.setLanguage('zh');assert.ok(note.textContent.includes('暫停'));
  context.stamps.setLanguage('en');assert.ok(note.textContent.includes('paused'));
}
fail=true;await context.liveTest.refreshLiveBudget();assert.equal(input.disabled,true);assert.equal(meter.hidden,true);
assert.ok(text.textContent.includes('unavailable'));
"""
