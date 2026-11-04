"""Execute shipped form/trace JS in the existing offline DOM adapter."""
import json
import subprocess

import pytest

from claimcheck.correction import build_corrections
from test_site_stamps_runtime import ROOT, run_check as run_scene_check


def run_check(script, **config):
    config.setdefault("page", "docs/site/index.html")
    run_scene_check(PUBLIC_FIXTURES + script, **config)


PUBLIC_FIXTURES = r"""
// Shared endpoint fixture; every test exercises the shipped provider shape.
const budgetFixture = (legacy = {}) => {
  const status = legacy.status || 'ready', limit = legacy.daily_limit_usd ?? 3;
  const remaining = legacy.daily_remaining_usd ?? limit;
  const row = {daily_limit:limit,daily_spent:legacy.daily_spent_usd ?? limit-remaining,daily_remaining:remaining,
    lifetime_limit:20,lifetime_spent:0,lifetime_remaining:20,status};
  return {day:'2026-11-03',resets_at:'2099-11-04T00:00:00Z',...legacy,
    providers:legacy.providers || Object.fromEntries(['baseten','fireworks','meta'].map(id=>[id,{...row}]))};
};
const publicFixture = url => {
  if(url==='/examples/manifest.json' || url==='/data/examples/index.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/examples/manifest.json','utf8'))};
  if(/^\/examples\/[a-z-]+\.txt$/.test(url))return {ok:true,text:async()=>readFileSync(root+'/docs'+url,'utf8')};
  if(/^\/data\/examples\/[a-z-]+\.json$/.test(url))return {ok:false,status:404};
  if(url.startsWith('/api/progress/'))return {ok:true,json:async()=>({lines:[],done:true,next:0})};
  if(url==='/api/history?limit=50')return {ok:true,json:async()=>({rows:[]})};
  return null;
};
"""


@pytest.mark.parametrize("language", ["en", "zh"])
def test_homepage_boot_restores_chart_and_preserves_legacy_example_anchors(language):
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
@pytest.mark.parametrize("stated,replacement,value,expected", [
    ("$1,200.0 million", "$1,178.0 million", 1178000000, "$1,178.0M"),
    ("$1.2 billion", "$0.9 billion", 900000000, "$0.9B"),
    ("$60.0M", "$60.9M", 60922000, "$60.9M"),
    ("-$60.0 million", "-$60.9 million", -60922000, "−$60.9M"),
])
def test_draft_keeps_edit_text_while_citations_and_evidence_share_stated_scale(language, stated, replacement, value, expected):
    run_check(SCALED_MONEY, language=language, stated=stated, replacement=replacement,
              value=value, expected=expected)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("edit_count", [0, 2])
def test_corrected_draft_is_verbatim_except_recorded_codepoint_edits(language, edit_count):
    text = ('🧵 e\u0301 — Amazon revenue was $143.1 billion.\r\n'
            'NVIDIA revenue was $60.9 billion; growth: 20%.\t'
            'Apple Q4 revenue: $416.2 billion.\n'
            'Unchanged: 20%, $416.2 billion.\u00a0\u202f<keep>&.')
    edits = []
    for original, replacement in [("20%", "125.9%"), ("$416.2 billion", "$102.5 billion")][:edit_count]:
        start = text.index(original)
        edits.append({"start": start, "end": start + len(original),
                      "original": original, "replacement": replacement})
    corrections = {"original_text": text, "span_unit": "unicode_codepoints", "edits": edits}
    page = "docs/zh/index.html" if language == "zh" else "docs/site/index.html"
    run_check(VERBATIM_DRAFT, page=page, language=language, corrections=corrections)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("mode", ["recorded", "live", "mock"])
def test_receipts_round_cost_to_cents_and_duration_to_tenths(language, mode):
    run_check(RECEIPT_PRECISION, language=language, mode=mode)


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
def test_provider_meters_switch_compare_midnight_and_independent_stops(language, viewport):
    run_check(BUDGET, language=language, viewport=viewport)


def test_pages_boundary_without_provider_key_or_network():
    result = subprocess.run(["node", "--test", "tests/node/live-boundary.test.mjs", "tests/node/live-v3-boundary.test.mjs", "tests/node/live-progress.test.mjs"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


HOMEPAGE_BOOT = r"""
const ids=['post-text','claim-list','posthoc-rerun','research-list'];
const labels=ids.map(id=>tree.querySelector('#'+id).textContent);
const requests=[];
context.fetch=async url=>{
  if(publicFixture(url))return publicFixture(url);
  requests.push(url);
  return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/site.json','utf8'))};
};
context.window.addEventListener=()=>{};
context.window.location.hash='';
context.liveTest.setupControls();
await context.liveTest.loadData();
assert.deepEqual(requests,['/data/site.json']);
assert.equal(tree.querySelectorAll('#chart .chart-row').length,3);
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
const editData=JSON.parse(section.querySelector('.trace-data').querySelector('pre').textContent);
assert.equal(editData.citations[0].value,416161000000);assert.equal(editData.citations[1].value,313695000000);
assert.equal(section.querySelector('.trace-data').open,undefined);
assert.equal(target.querySelector('.live-trace').open,false);
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
assert.equal(target.querySelector('.live-trace').open,true,'invalid edit spans do not collapse the trace');
// Exercise the same envelope through the form and a subsequent language switch.
context.AbortController=AbortController;context.setTimeout=()=>0;context.clearTimeout=()=>{};
context.fetch=async url=>({ok:true,json:async()=>url==='/api/check'?result:url==='/api/budget'?
  budgetFixture({day:'2026-11-03',daily_limit_usd:3,daily_remaining_usd:3,resets_at:'2099-11-04T00:00:00Z',status:'ready'}):
  JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'))});
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
tree.querySelector('#live-input').value=config.corrections.original_text;
tree.querySelector('#live-input').events.input();
tree.querySelector('#live-password').value='offline-only';
await tree.querySelector('#live-form').events.submit({preventDefault(){}});
assert.equal(target.querySelector('.corrected-draft-text').querySelector('strong').textContent,'$102.5B');
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.ok(target.textContent.includes(config.language==='zh'?'Corrected draft — only listed assertions checked':'修正版草稿——僅核對列出的主張'));
assert.ok(target.textContent.includes(config.language==='zh'?'This assertion was not judged':'此主張未評判'));
"""


SCALED_MONEY = r"""
context.URL=URL;
const target=tree.querySelector('#live-result');
const fact={evidence_id:'E1',ticker:'AAPL',metric:'revenue',unit:'USD',value:config.value,
  period:'FY2025',period_basis:'fiscal',period_type:'annual',form:'10-K'};
const edit={start:0,end:Array.from(config.stated).length,original:config.stated,replacement:config.replacement,
  actual_value:config.value,unit:'USD',period:'FY2025',evidence_ids:['E1'],citations:[{...fact}]};
const result={events:[],evidence:[fact],claims:[{text:config.stated,evidence_ids:['E1']}],corrections:{
  original_text:config.stated,span_unit:'unicode_codepoints',edits:[edit],not_corrected:[]}};
context.liveTest.renderLiveTrace(result,target);
assert.equal(target.querySelector('.corrected-draft-text').querySelector('del').textContent,config.stated);
assert.equal(target.querySelector('.corrected-draft-text').querySelector('strong').textContent,config.replacement);
assert.ok(target.querySelector('.citation-primary').textContent.includes(config.expected));
assert.ok(target.querySelector('.evidence-primary').textContent.startsWith(config.expected+' · '));
assert.ok(!/億|兆/.test(target.querySelector('.corrected-draft-text').textContent));
assert.equal(JSON.parse(target.querySelector('.trace-data').querySelector('pre').textContent).actual_value,config.value);
assert.equal(target.querySelector('.live-trace').open,false);
result.corrections=null;
context.liveTest.renderLiveTrace(result,target);
assert.equal(target.querySelector('.live-trace').open,true);
"""


VERBATIM_DRAFT = r"""
context.URL=URL;
const target=tree.querySelector('#live-result');
const corrections=config.corrections;
const original=Array.from(corrections.original_text);
let expected=original.slice(),annotated=original.slice();
for(const edit of corrections.edits.slice().reverse()){
  expected.splice(edit.start,edit.end-edit.start,...Array.from(edit.replacement));
  annotated.splice(edit.start,edit.end-edit.start,...Array.from(`${edit.original} → ${edit.replacement}`));
}
const verify=()=>{
  context.liveTest.renderLiveTrace({events:[],corrections},target);
  const draft=target.querySelector('.corrected-draft-text');
  // Omit struck text and the edit arrow to read the resulting corrected draft.
  const draftText=draft.children.filter(node=>['span','strong'].includes(node.tagName)).map(node=>node.textContent).join('');
  assert.equal(draftText,expected.join(''),'only the listed codepoint spans change');
  assert.equal(draft.children.filter(node=>['span','del'].includes(node.tagName)).map(node=>node.textContent).join(''),corrections.original_text);
  assert.equal(draft.textContent,annotated.join(''),'all displayed text and edit tokens stay verbatim');
  assert.deepEqual(draft.querySelectorAll('del').map(node=>node.textContent),corrections.edits.map(edit=>edit.original));
  assert.deepEqual(draft.querySelectorAll('strong').map(node=>node.textContent),corrections.edits.map(edit=>edit.replacement));
};
verify();
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
verify();
"""


RECEIPT_PRECISION = r"""
context.URL=URL;
const target=tree.querySelector('#live-result');
const event={kind:'model',at_ms:12345.678,latency_ms:38424.567,cost_usd:.061234567,finish_reason:'stop'};
const result={mode:config.mode,cost_usd:event.cost_usd,latency_ms:event.latency_ms,events:[event]};
const saved=JSON.stringify(result);
for(const bound of [false,true]){
  result.cost_is_bound=bound;
  context.liveTest.renderLiveTrace(result,target);
  const seconds=config.language==='zh'?'秒':'s';
  const metrics=target.querySelector('.live-receipt').textContent;
  assert.ok(metrics.includes(`38.4 ${seconds}`) && metrics.includes(': $0.06'),metrics);
  const model=target.querySelector('.trace-model');
  assert.equal(model.querySelector('p').textContent,`38.4 ${seconds} · $0.06 · stop`);
  assert.equal(model.querySelector('.trace-time').textContent,`+12.3 ${seconds} · `);
  const raw=model.querySelector('.trace-data');
  assert.ok(raw.querySelector('summary').textContent.includes(config.language==='zh'?'檢視資料':'Inspect data'));
  assert.deepEqual(JSON.parse(raw.querySelector('pre').textContent),event);
}
delete result.cost_is_bound;
assert.equal(JSON.stringify(result),saved,'rounding leaves recorded values intact');
"""


POST_RENDER = r"""
context.URL=URL;
const demo=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
const target=tree.querySelector('#recorded-trace');
context.liveTest.renderLiveTrace(demo,target);
const verify=language=>{
  const head=target.querySelector('.trace-head'),corrections=target.querySelector('.live-corrections');
  const evidence=target.querySelector('.live-proof'),trace=target.querySelector('.live-trace');
  assert.deepEqual(target.children.map(node=>node.className),['live-input-read','live-receipt','trace-head','live-corrections','live-proof','live-trace']);
  assert.equal(head.querySelector('.trace-verdict').textContent,language==='zh'?'證據矛盾':'Contradicted');
  assert.equal(evidence.querySelector('.live-claims').querySelectorAll('li').length,5);
  const draft=corrections.querySelector('.corrected-draft-text');
  assert.equal(draft.querySelectorAll('del').length,1);
  assert.equal(draft.querySelectorAll('strong').length,1);
  assert.equal(draft.querySelector('del').textContent,demo.corrections.edits[0].original);
  assert.equal(draft.querySelector('strong').textContent,demo.corrections.edits[0].replacement);
  assert.ok(draft.textContent.includes('$143.1 billion'));
  assert.ok(draft.textContent.includes('$60.9 billion'));
  let expected=Array.from(demo.corrections.original_text);
  for(const edit of demo.corrections.edits.slice().reverse()){
    expected.splice(edit.start,edit.end-edit.start,...Array.from(edit.replacement));
  }
  assert.equal(draft.children.filter(node=>['span','strong'].includes(node.tagName)).map(node=>node.textContent).join(''),expected.join(''));
  assert.equal(corrections.querySelector('.correction-changes').children.length,1);
  const links=corrections.querySelectorAll('a');
  assert.equal(links.length,2);
  assert.ok(links[0].href.endsWith('/000032019325000079/'));
  assert.ok(links[1].href.endsWith('/000032019326000020/'));
  const citationLines=corrections.querySelectorAll('.citation-primary').map(node=>node.textContent);
  assert.deepEqual(citationLines,language==='zh'?[
    '10-K · 2025 財年（全年） · $416.2B 營收 · 開啟申報文件',
    '10-Q · 截至 2025 年 6 月 28 日的 9 個月 · $313.7B 營收 · 開啟申報文件'
  ]:[
    '10-K · fiscal 2025 (annual) · $416.2B revenue · Open SEC filing',
    '10-Q · nine months to 28 Jun 2025 · $313.7B revenue · Open SEC filing'
  ]);
  assert.equal(corrections.querySelector('.correction-derivation').textContent,language==='zh'?
    '申報季度 = 全年 − 前九個月':'Filed quarter = annual − nine months');
  const rawEdit=JSON.parse(corrections.querySelector('.trace-data').querySelector('pre').textContent);
  assert.equal(rawEdit.evidence_ids[0],'C3:E1');
  assert.equal(rawEdit.citations[0].accn,'0000320193-25-000079');
  assert.equal(rawEdit.citations[0].value,416161000000);
  assert.equal(rawEdit.citations[1].value,313695000000);
  const cards=evidence.querySelectorAll('.live-evidence-row');
  assert.equal(cards.length,demo.evidence.length);
  assert.deepEqual(cards.map(card=>card.querySelector('.evidence-primary').textContent),language==='zh'?[
    '$143.1B · Amazon 營收 · 2023 曆年第 3 季 · 10-Q',
    '$60.9B · NVIDIA 營收 · 2024 財年（全年） · 10-K',
    '125.9% · NVIDIA 營收成長 · 2024 對 2023 財年 · 10-K',
    '$102.5B · Apple 營收 · 2025 財年第 4 季 · 10-K − 10-Q'
  ]:[
    '$143.1B · Amazon revenue · calendar Q3 2023 · 10-Q',
    '$60.9B · NVIDIA revenue · fiscal 2024 (annual) · 10-K',
    '125.9% · NVIDIA revenue growth · fiscal 2024 vs 2023 · 10-K',
    '$102.5B · Apple revenue · fiscal Q4 2025 · 10-K − 10-Q'
  ]);
  cards.forEach((card,index)=>{
    assert.equal(card.children.length,1,'one compact disclosure per evidence item');
    const details=card.querySelector('.trace-data');
    assert.ok(!details.open);
    assert.deepEqual(JSON.parse(details.querySelector('pre').textContent),demo.evidence[index]);
    const primary=card.querySelector('.evidence-primary').textContent;
    assert.ok(!/C\d+:E\d+|\d{10}|us-gaap|RevenueFrom|\d{4}-\d{2}-\d{2}|億|兆/.test(primary));
  });
  const unchanged=corrections.querySelector('.correction-unchanged');
  assert.equal(unchanged.children.length,4);
  assert.ok(unchanged.textContent.includes(language==='zh'?'程式支持此主張，無須修改。':'The program supports this assertion; no edit needed.'));
  assert.ok(unchanged.textContent.includes(language==='zh'?'此主張未評判（意見或超出範圍）。':'This assertion was not judged (opinion or out of scope).'));
  assert.ok(unchanged.textContent.includes('NVDA at 30x sales is still cheap.'));
  assert.equal(unchanged.tagName,'ol');
  assert.equal(unchanged.querySelectorAll('q').length,0);
  unchanged.children.forEach(row=>{
    assert.equal(row.children.length,2);
    assert.equal(row.children[0].className,'correction-assertion');
    assert.equal(row.children[1].className,'correction-reason');
  });
  assert.equal(property('.correction-assertion','font-size'),'1rem');
  assert.equal(property('.correction-reason','color'),'var(--muted)');
  assert.equal(trace.tagName,'details');
  assert.equal(trace.open,false);
  assert.equal(trace.querySelector('summary').textContent,language==='zh'?
    `代理執行過程（${demo.events.length} 個步驟）`:`Agent trace (${demo.events.length} steps)`);
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
  if(publicFixture(url))return publicFixture(url);
  requests.push(url);assert.notEqual(url,'/api/check');
  if(url==='/api/budget')return {ok:true,json:async()=>(budgetFixture({day:'2026-11-03',daily_limit_usd:3,daily_remaining_usd:3,
    resets_at:'2099-11-04T00:00:00Z',status:'ready'}))};
  assert.ok(['/data/live-demo-post.json','/data/live-demo.json'].includes(url));
  return {ok:true,json:async()=>url==='/data/live-demo-post.json'?post:claim};
};
context.liveTest.setupLive();context.liveTest.setupControls();
await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input'),target=tree.querySelector('#recorded-trace');
const postButton=tree.querySelector('[data-saved-demo="post"]'),claimButton=tree.querySelector('[data-saved-demo="claim"]');
input.focus=()=>{};
const example=readFileSync(root+'/docs/examples/a.txt','utf8');
assert.ok(Array.from(example).length<=600);
await tree.querySelector('#live-example').events.click();assert.equal(input.value,example);
assert.equal(tree.querySelector('#live-count').textContent,Array.from(example).length+' / 600');
assert.equal(context.liveTest.state().savedLiveDemo.input,original);
assert.equal(postButton.getAttribute('aria-pressed'),'true');
assert.equal(claimButton.getAttribute('aria-pressed'),'false');
assert.ok(postButton.textContent.includes(config.language==='zh'?'熱傳貼文':'Saved check · viral post · 28 Oct 2026'));
assert.equal(requests.filter(url=>url==='/data/live-demo.json').length,0);
await claimButton.events.click();
assert.equal(context.liveTest.state().savedLiveDemo.input,claim.input);
assert.equal(claimButton.getAttribute('aria-pressed'),'true');
assert.equal(target.querySelector('.corrected-draft-text').querySelectorAll('del').length,0);
assert.equal(target.querySelector('.live-trace').open,true);
await tree.querySelector('#live-example').events.click();assert.equal(input.value,example);
tree.querySelector('a[href="#recorded-run"]').events.click();
assert.equal(tree.querySelector('#saved-check-details').open,true);
assert.equal(context.liveTest.state().savedLiveDemo.input,original);
assert.equal(postButton.getAttribute('aria-pressed'),'true');
assert.equal(target.querySelector('.corrected-draft-text').querySelectorAll('del').length,1);
assert.equal(target.querySelector('.live-trace').open,false);
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
assert.equal(corrections.querySelector('.corrected-draft-text').textContent,demo.corrections.original_text);
assert.ok(corrections.querySelector('.correction-unchanged').textContent.includes(config.language==='zh'?
  '程式支持此主張，無須修改。':'The program supports this assertion; no edit needed.'));
assert.ok(corrections.querySelector('.correction-scope').textContent.includes(config.language==='zh'?
  '文中其餘內容均未經查證':'nothing else in the text was verified'));
assert.equal(target.querySelectorAll('.trace-step').length,7);
assert.equal(target.querySelectorAll('.trace-model').length,3);
assert.ok(target.textContent.includes('109417000000'));
assert.equal(target.querySelector('.evidence-primary').textContent,config.language==='zh'?
  '$109.4B · Apple 營收 · 2026 財年第 3 季 · 10-Q':
  '$109.4B · Apple revenue · fiscal Q3 2026 · 10-Q');
assert.equal(target.querySelector('.live-trace').open,true);
assert.ok(target.textContent.includes('FY2026Q3'));
assert.ok(target.textContent.includes('0000320193-26-000020'));
assert.ok(target.querySelector('.live-receipt').textContent.includes('$0.01'));
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
const budget=()=>(budgetFixture({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:remaining,daily_spent_usd:3-remaining,
  resets_at:'2099-11-03T00:00:00Z',status:remaining===0?'budget_exhausted':'ready'}));
// Keep rollover timers inert in this DOM test; the real browser owns them.
context.setTimeout=(fn,ms)=>ms>100000?0:setTimeout(fn,ms);context.clearTimeout=clearTimeout;
context.fetch=async (url,opts)=>{
  if(publicFixture(url))return publicFixture(url);
  if(url==='/data/examples/index.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/examples/index.json','utf8'))};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'))};
  if(url==='/api/budget'){budgetReads++;assert.equal(opts.cache,'no-store');return {ok:true,json:async()=>budget()};}
  requests.push({url,opts});
  return new Promise(resolve=>{finish=resolve;});
};
context.liveTest.setupLive();
await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input'),form=tree.querySelector('#live-form'),submit=tree.querySelector('#live-submit');
input.value=demo.input;input.events.input();
tree.querySelector('#live-password').value='offline-password';
const pending=form.events.submit({preventDefault(){}});
assert.equal(submit.disabled,true);assert.equal(form.getAttribute('aria-busy'),'true');
assert.equal(requests.length,1);assert.equal(requests[0].url,'/api/check');
const sent=JSON.parse(requests[0].opts.body);assert.match(sent.client_run_id,/^[0-9a-f-]{36}$/);
delete sent.client_run_id;assert.deepEqual(sent,{text:demo.input,password:'offline-password',provider:'baseten'});
remaining=2.41;
finish({ok:true,json:async()=>({...demo,mode:'live'})});await pending;
assert.equal(budgetReads,2);
assert.ok(tree.querySelector('#budget-baseten-text').textContent.includes('$2.41'));
assert.equal(submit.disabled,false);assert.equal(form.getAttribute('aria-busy'),'false');
assert.equal(tree.querySelector('#live-result').hidden,false);
assert.equal(tree.querySelector('#live-result').querySelectorAll('.trace-step').length,7);
const failed=form.events.submit({preventDefault(){}});
remaining=0;
finish({ok:false,json:async()=>({error:'budget_exhausted'})});await failed;
assert.equal(budgetReads,3);assert.equal(input.disabled,false);assert.equal(submit.disabled,true);
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
  if(publicFixture(url))return publicFixture(url);
  if(url==='/data/examples/index.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/examples/index.json','utf8'))};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'))};
  if(url==='/api/budget'){
    assert.ok(!JSON.stringify(opts).includes(credential));
    return {ok:true,json:async()=>(budgetFixture({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:3,
      resets_at:'2099-11-03T00:00:00Z',status:'ready'}))};
  }
  requests.push({url,opts});
  return new Promise(resolve=>{finish=resolve;});
};
const password=tree.querySelector('#live-password'),form=tree.querySelector('#live-form');
password.value='';password.focus=()=>{};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input');input.value=demo.input;input.events.input();
assert.equal(password.value,'');assert.equal(password.getAttribute('type'),'password');
assert.equal(password.getAttribute('autocomplete'),'off');assert.equal(form.getAttribute('method'),'post');
assert.ok(tree.querySelector('#recorded-trace').textContent.includes('FY2025Q4'));
assert.ok(tree.querySelector('#budget-baseten-text').textContent.includes('$3'));
assert.equal(tree.querySelector('#live-password-note').textContent,config.language==='zh'?
  '密碼是我們的隊名。查看儲存結果不需密碼。':
  'Password is our team name. Saved results need none.');
await form.events.submit({preventDefault(){}});assert.equal(requests.length,0);
password.value=credential;
const denied=form.events.submit({preventDefault(){}});
assert.equal(password.disabled,true);assert.equal(writes.length,0);
finish({ok:false,status:401,json:async()=>({error:'unauthorized'})});await denied;
assert.equal(writes.length,0);assert.equal(saved.size,0);assert.equal(password.value,'');
password.value=credential;
const locked=form.events.submit({preventDefault(){}});
finish({ok:false,status:429,json:async()=>({error:'auth_rate_limited',retry_after:900})});await locked;
assert.equal(writes.length,0);assert.ok(tree.querySelector('#live-status').textContent.includes(config.language==='zh'?'重設時間':'Resets'));
const success=form.events.submit({preventDefault(){}});
assert.equal(writes.length,0);
finish({ok:true,status:200,json:async()=>({...demo,mode:'live'})});await success;
assert.equal(password.disabled,false);
assert.deepEqual(writes,config.blocked?[]:[{key,value:credential}]);
for(const {url,opts} of requests){
  assert.equal(url,'/api/check');assert.ok(!JSON.stringify(opts.headers).includes(credential));
  const sent=JSON.parse(opts.body);assert.match(sent.client_run_id,/^[0-9a-f-]{36}$/);delete sent.client_run_id;
  assert.deepEqual(sent,{text:demo.input,password:credential,provider:'baseten'});
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
  if(publicFixture(url))return publicFixture(url);
  assert.notEqual(url,'/api/check');
  if(url==='/api/budget')return {ok:true,json:async()=>(budgetFixture({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:3,
    resets_at:'2099-11-03T00:00:00Z',status:'ready'}))};
  return {ok:false};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
assert.equal(tree.querySelector('#live-password').value,config.remembered?'session-only-marker':'');
assert.ok(!tree.textContent.includes('session-only-marker'));
"""

BUDGET = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
let data=budgetFixture({day:'2026-11-02',daily_limit_usd:3,daily_spent_usd:.59,daily_remaining_usd:2.41,
  resets_at:'2026-11-03T00:00:00Z',status:'ready'});
data.providers.fireworks={daily_limit:30,daily_spent:2,daily_remaining:28,lifetime_limit:50,lifetime_spent:12,lifetime_remaining:38,status:'ready'};
data.providers.meta={daily_limit:15,daily_spent:1,daily_remaining:14,lifetime_limit:100,lifetime_spent:70,lifetime_remaining:30,status:'ready'};
let fail=false,checks=0;
context.fetch=async url=>{
  if(publicFixture(url))return publicFixture(url);
  if(url==='/api/budget')return {ok:!fail,json:async()=>data};
  if(url==='/api/check'){checks++;assert.fail('stopped provider must never submit');}
  return {ok:false};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const text=tree.querySelector('#budget-baseten-text'),meter=tree.querySelector('#budget-baseten-meter');
const note=tree.querySelector('#budget-baseten-status'),input=tree.querySelector('#live-input'),submit=tree.querySelector('#live-submit');
assert.equal(tree.querySelectorAll('.provider-budget-meter').length,3);
assert.ok(!tree.querySelector('#live-budget-meter'));
assert.ok(text.textContent.includes('$2.41'));assert.ok(tree.querySelectorAll('.provider-model')[1].title.includes('$20.00'));
assert.equal(meter.max,3);assert.equal(meter.value,2.41);
assert.ok(tree.querySelectorAll('.provider-model')[2].title.includes('$38.00'));
assert.ok(tree.querySelectorAll('.provider-model')[0].title.includes('$100.00'));
assert.equal(input.disabled,false);assert.equal(note.hidden,true);
for(const status of ['budget_exhausted','credit_exhausted','total_budget_exhausted']){
  data.providers.baseten={...data.providers.baseten,daily_remaining:0,status};
  await context.liveTest.refreshLiveBudget();
  assert.equal(submit.disabled,true);assert.equal(input.disabled,false);assert.equal(meter.value,0);
  assert.equal(note.hidden,false);
  assert.ok(/Paused|暫停/.test(note.textContent));
  assert.ok(/daily|credit|lifetime|每日|額度|累計/.test(note.textContent));
  await tree.querySelector('#live-form').events.submit({preventDefault(){}});assert.equal(checks,0);
  const radio=tree.querySelector('input[name="provider"][value="fireworks"]');radio.checked=true;radio.events.change();
  assert.equal(submit.disabled,false,'switching to an available provider enables Run');
  const selected=tree.querySelector('input[name="provider"][value="baseten"]');selected.checked=true;selected.events.change();
  assert.equal(submit.disabled,true);
  const compare=tree.querySelector('#compare-all');compare.checked=true;compare.events.change();
  assert.equal(submit.disabled,false,'compare skips the exhausted provider');
  compare.checked=false;compare.events.change();assert.equal(submit.disabled,true);
  context.stamps.setLanguage('zh');assert.ok(note.textContent.includes('暫停'));
  context.stamps.setLanguage('en');assert.ok(note.textContent.includes('Paused'));
}
data={...data,day:'2026-11-03',resets_at:'2026-11-04T00:00:00Z'};
data.providers.baseten={...data.providers.baseten,daily_remaining:3,status:'ready'};
await context.liveTest.refreshLiveBudget();assert.equal(submit.disabled,false);assert.equal(meter.value,3);
for(const row of Object.values(data.providers))row.status='credit_exhausted';
const compare=tree.querySelector('#compare-all');compare.checked=true;compare.events.change();
await context.liveTest.refreshLiveBudget();assert.equal(submit.disabled,true);
fail=true;await context.liveTest.refreshLiveBudget();assert.equal(submit.disabled,true);assert.equal(meter.hidden,true);
assert.ok(text.textContent.includes('unavailable'));
"""
