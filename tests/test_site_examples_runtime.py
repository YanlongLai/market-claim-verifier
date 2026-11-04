"""Render the production input matrix against mocked v3 JSON endpoints.

The shared Node DOM adapter executes shipped JS; no provider or SEC is called.
Browser screenshots are reviewed separately from these behavior checks.
"""
import pytest

from test_site_live_runtime import run_check


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [375, 768, 1440])
def test_all_fifteen_inputs_run_by_manifest_id_and_render_receipts(language, viewport):
    run_check(SETUP + ALL_INPUTS, language=language, viewport=viewport,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_saved_results_need_no_password_and_missing_results_stay_pending(language):
    run_check(SETUP + SAVED, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("custom", [False, True])
def test_compare_uses_one_sequential_api_request_and_three_provider_columns(language, custom):
    run_check(SETUP + COMPARE, language=language, custom=custom)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_public_history_opens_full_envelope_then_edits_text_and_provider(language):
    run_check(SETUP + HISTORY, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_budget_partial_comparison_and_unavailable_history_keep_public_reads(language):
    run_check(SETUP + PARTIAL, language=language)


def test_stale_history_and_text_responses_cannot_replace_a_new_selection():
    run_check(SETUP + RACES)


def test_manifest_paths_and_hostile_text_never_create_executable_markup():
    run_check(SETUP + HOSTILE)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_radio_selection_preserves_the_server_read_text_and_pending_assets(language):
    run_check(SETUP + PROVIDER_AND_PENDING, language=language)


@pytest.mark.parametrize("viewport", [375, 768, 1023, 1024, 1280, 1440])
def test_layout_uses_bounded_columns_and_stacks_history_on_small_screens(viewport):
    run_check(SETUP + LAYOUT, viewport=viewport)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_committed_w3_catalogue_loads_all_ready_inputs_counts_text_and_skips_missing_saves(language):
    run_check(COMMITTED_CATALOGUE, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("code", ["rate_limited", "auth_rate_limited"])
def test_rate_limit_shows_the_server_reset_time_and_keeps_it_on_language_change(language, code):
    run_check(SETUP + RATE_LIMIT, language=language, code=code)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_rate_limit_without_server_retry_time_reports_it_as_unavailable(language):
    run_check(SETUP + RATE_LIMIT_UNKNOWN, language=language)


SETUP = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
const saved=JSON.parse(readFileSync(root+'/docs/site/data/examples/text.json','utf8'));
const raw=saved.input.text_read;
const modelIds={baseten:'meta-models/muse-spark-open-1026',fireworks:'accounts/fireworks/models/muse-spark-open',meta:'muse-spark-1.3'};
const manifest={stories:[
  {id:'a',title_en:'A · Wrong period',title_zh:'A · 期間錯誤',expected:'contradicted'},
  {id:'b',title_en:'B · All correct',title_zh:'B · 全部正確',expected:'supported'},
  {id:'c',title_en:'C · Mixed',title_zh:'C · 混合主張',expected:'mixed'}
],examples:['a','b','c'].flatMap(story=>['text','image','pdf','audio','video'].map(kind=>({
  id:`${story}-${kind}`,story,kind,file:`${story}-${kind}.${{text:'txt',image:'png',pdf:'pdf',audio:'mp3',video:'mp4'}[kind]}`,
  preview:`${story}-preview.png`,sha256:'a'.repeat(64),what_en:`${story} ${kind} input`,what_zh:`${story} ${kind} 範例`
  ,saved_result:story==='a'&&kind==='text'?'/data/examples/a-text.json':null
})))};
const envelope=(id='a-text',provider='baseten')=>({...saved,mode:'live',
  verdict:id.startsWith('b-')?'supported':'contradicted',
  corrections:id.startsWith('b-')?{...saved.corrections,edits:[]}:saved.corrections,
  input:{example_id:id,kind:id.split('-')[1],story:id[0],text_read:raw},
  receipt:{provider,model:modelIds[provider],latency_ms:6300,cost_usd:.01,
    preprocessing:id.endsWith('-text')?null:{model:'muse-voice-transcribe-1.0',latency_ms:1500,cost_usd:.0005}}});
let paid=[],reads=[],historyData=[],historyDetails={},responseFactory=null,budgetStatus='ready',historyFail=false;
context.fetch=async (url,opts={})=>{
  if(!opts.method) {reads.push(url);assert.ok(!JSON.stringify(opts).includes('password-marker'));}
  if(url==='/examples/manifest.json')return {ok:true,json:async()=>manifest};
  if(url.startsWith('/examples/')&&url.endsWith('.txt'))return {ok:true,text:async()=>raw};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>saved};
  if(url==='/api/budget')return {ok:true,json:async()=>({day:'2026-11-03',daily_limit_usd:3,
    daily_remaining_usd:budgetStatus==='ready'?3:0,resets_at:'2099-11-04T00:00:00Z',status:budgetStatus})};
  if(url==='/api/history?limit=50')return {ok:!historyFail,json:async()=>({rows:historyData})};
  if(url.startsWith('/api/history/'))return {ok:true,json:async()=>historyDetails[url.split('/').pop()]};
  if(url.startsWith('/data/examples/'))return url==='/data/examples/a-text.json'
    ?{ok:true,json:async()=>({...envelope(),mode:'recorded'})}:{ok:false,status:404};
  assert.ok(['/api/check','/api/check-example','/api/compare'].includes(url),url);
  const body=JSON.parse(opts.body);paid.push({url,body,opts});
  if(responseFactory)return responseFactory(url,body);
  return {ok:true,status:200,json:async()=>envelope(body.example_id||'a-text',body.provider)};
};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const click=selector=>tree.querySelector(selector).events.click();
const submit=()=>tree.querySelector('#live-form').events.submit({preventDefault(){}});
const password=tree.querySelector('#live-password');
context.liveTest.setupLive();await tick();
"""

ALL_INPUTS = r"""
assert.equal(tree.querySelectorAll('[data-story-slot]').length,3);
assert.equal(tree.querySelectorAll('[data-input-kind]').length,5);
assert.equal(tree.querySelectorAll('input[name="provider"]').length,3);
assert.equal(password.value,'');
password.value='password-marker';
for(const [index,story] of ['a','b','c'].entries()){
  await click(`[data-story-slot="${index}"]`);
  assert.equal(tree.querySelector(`[data-story-slot="${index}"]`).getAttribute('aria-pressed'),'true');
  for(const kind of ['text','image','pdf','audio','video']){
    await click(`[data-input-kind="${kind}"]`);
    assert.equal(tree.querySelector(`[data-input-kind="${kind}"]`).getAttribute('aria-selected'),'true');
    assert.equal(tree.querySelector('#input-panel').getAttribute('aria-labelledby'),`input-tab-${kind}`);
    const preview=tree.querySelector('#input-preview');
    assert.equal(tree.querySelector('#text-input-panel').hidden,kind!=='text');
    if(['audio','video'].includes(kind)) {assert.equal(preview.children[0].tagName,kind);assert.equal(preview.children[0].controls,true);}
    if(['image','pdf'].includes(kind))assert.equal(preview.querySelector('img').src,`/examples/${story}-${kind==='image'?'image':'preview'}.png`);
    await submit();
    assert.deepEqual(paid.at(-1).body,{example_id:`${story}-${kind}`,password:'password-marker',provider:'baseten'});
    const target=tree.querySelector('#live-result');
    assert.deepEqual(target.children.map(node=>node.className),['live-input-read','live-receipt','trace-head','live-corrections','live-proof','live-trace']);
    assert.equal(target.querySelector('.trace-input').textContent,raw);
    assert.ok(target.querySelector('.live-receipt').textContent.includes(modelIds.baseten));
    assert.ok(target.querySelector('.live-receipt').textContent.includes('$0.01'));
    if(kind!=='text')assert.ok(target.querySelector('.live-receipt').textContent.includes('$0.00'));
    assert.equal(target.querySelector('.live-trace').open,story==='b');
    assert.equal(target.querySelector('.live-input-read h5').textContent,config.language==='zh'?'模型讀到了什麼':'What the model read');
    if(story==='b')assert.ok(target.textContent.includes(config.language==='zh'?'已核對的主張無需修正':'Nothing to correct'));
  }
}
assert.equal(paid.length,15);
assert.ok(reads.filter(url=>url==='/api/history?limit=50').length>=16);
assert.ok(!tree.textContent.includes('password-marker'));
// Keyboard tab navigation follows the visible five-tab order.
await tree.querySelector('#input-tab-video').events.keydown({key:'Home',preventDefault(){}});await tick();
assert.equal(tree.querySelector('#input-tab-text').getAttribute('tabindex'),'0');
assert.ok(tree.querySelector('#input-tab-text').focused);
"""

SAVED = r"""
await click('#example-saved');
assert.equal(paid.length,0);assert.ok(!tree.querySelector('#live-result').hidden);
assert.equal(tree.querySelector('#live-result .trace-input').textContent,raw);
await click('[data-input-kind="image"]');await click('#example-saved');
assert.equal(paid.length,0);assert.ok(tree.querySelector('#live-result').hidden);
assert.equal(tree.querySelector('#example-saved-status').textContent,config.language==='zh'?'已儲存結果待補':'Saved result pending');
await submit();assert.equal(paid.length,0);
assert.ok(tree.querySelector('#live-status').textContent.includes(config.language==='zh'?'密碼':'password'));
budgetStatus='budget_exhausted';await context.liveTest.refreshLiveBudget();
assert.ok(tree.querySelector('#live-submit').disabled);assert.ok(!tree.querySelector('#example-saved').disabled);
await click('[data-input-kind="text"]');await click('#example-saved');assert.equal(paid.length,0);
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.equal(tree.querySelector('#live-result .live-input-read h5').textContent,config.language==='zh'?'What the model read':'模型讀到了什麼');
"""

COMPARE = r"""
password.value='password-marker';
if(config.custom){tree.querySelector('#live-input').value='Apple revenue test';tree.querySelector('#live-input').events.input();}
else await click('[data-input-kind="video"]');
const checkbox=tree.querySelector('#compare-all');checkbox.checked=true;checkbox.events.change();
let finish;
responseFactory=()=>new Promise(resolve=>finish=resolve);
const running=submit();
assert.ok(tree.querySelector('#live-submit').disabled);assert.ok(password.disabled);
await submit();assert.equal(paid.length,1);
assert.equal(paid[0].url,'/api/compare');
assert.deepEqual(paid[0].body,{...(config.custom?{text:'Apple revenue test'}:{example_id:'a-video'}),password:'password-marker',providers:['baseten','fireworks','meta']});
finish({ok:true,status:200,json:async()=>({runs:Object.keys(modelIds).map(provider=>envelope('a-video',provider))})});await running;
const table=tree.querySelector('.compare-table');
assert.equal(table.querySelectorAll('th').length,3);assert.equal(table.querySelectorAll('tbody tr').length,6);
assert.ok(table.textContent.includes('Fireworks'));assert.ok(table.textContent.includes('$0.00050'));
assert.equal(tree.querySelector('#live-result .live-receipt').textContent.includes('Baseten'),true);
await table.querySelectorAll('button')[1].events.click();
assert.ok(tree.querySelector('#live-result .live-receipt').textContent.includes('Fireworks'));
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.equal(tree.querySelectorAll('.compare-table th').length,3);
assert.equal(tree.querySelector('.compare-table caption').textContent,config.language==='zh'?'Provider comparison':'供應商比較');
"""

HISTORY = r"""
historyData=Array.from({length:57},(_,i)=>({id:`run-${i}`,at:'2026-11-03T17:05:00Z',device:'Desktop',browser:'Chrome',
 story:'c',kind:'image',example_id:'c-image',provider:'fireworks',model:modelIds.fireworks,verdict:'contradicted',
 input_text:'An editable saved claim',latency_ms:6300,cost_usd:.01,preprocessing_cost_usd:.0005}));
historyDetails['run-0']={envelope:{...envelope('c-image','fireworks'),input:{kind:'image',story:'c',text_read:'An editable saved claim'}}};
await click('#history-refresh');
assert.equal(tree.querySelectorAll('#history-rows tr').length,50);
assert.ok(tree.querySelector('#history-rows').textContent.includes('Desktop / Chrome'));
assert.ok(tree.querySelector('#history-rows').textContent.includes('$0.00050'));
await tree.querySelector('#history-rows tr').events.click();
assert.equal(paid.length,0);assert.ok(reads.includes('/api/history/run-0'));
assert.equal(tree.querySelector('#live-result .trace-input').textContent,'An editable saved claim');
await click('#result-edit');
assert.equal(tree.querySelector('#live-input').value,'An editable saved claim');
assert.equal(context.liveTest.state().selectedProvider,'fireworks');
assert.equal(tree.querySelector('#input-tab-text').getAttribute('aria-selected'),'true');
assert.equal(password.value,'');password.value='password-marker';await submit();
assert.deepEqual(paid.at(-1).body,{text:'An editable saved claim',password:'password-marker',provider:'fireworks'});
"""

PARTIAL = r"""
password.value='password-marker';tree.querySelector('#compare-all').checked=true;
responseFactory=async()=>({ok:false,status:429,json:async()=>({error:'budget_exhausted',runs:[envelope(),
 {error:'budget_exhausted',receipt:{provider:'fireworks',model:modelIds.fireworks,latency_ms:0,cost_usd:0,preprocessing:null}}]})});
await submit();
assert.ok(tree.querySelector('#compare-result').textContent.includes(config.language==='zh'?'未執行':'Not run'));
assert.ok(tree.querySelector('#live-submit').disabled);
assert.equal(tree.querySelector('#live-result .trace-input').textContent,raw);
historyFail=true;await click('#history-refresh');
assert.ok(tree.querySelector('#history-status').textContent.includes(config.language==='zh'?'無法讀取':'unavailable'));
assert.ok(!tree.querySelector('#history-refresh').disabled);
await click('#example-saved');assert.equal(paid.length,1);assert.ok(!tree.querySelector('#live-result').hidden);
"""

RACES = r"""
historyData=[{id:'older',at:'2026-11-03',provider:'meta'},{id:'newer',at:'2026-11-03',provider:'baseten'}];
await click('#history-refresh');
const baseFetch=context.fetch;let finishOld,finishNew;
context.fetch=async(url,opts)=>url==='/api/history/older'?new Promise(resolve=>finishOld=resolve):
 url==='/api/history/newer'?new Promise(resolve=>finishNew=resolve):baseFetch(url,opts);
const old=click('[data-history-id="older"]'),fresh=click('[data-history-id="newer"]');
finishNew({ok:true,json:async()=>({...envelope(),input:{kind:'text',text_read:'New result'}})});await fresh;
finishOld({ok:true,json:async()=>({...envelope(),input:{kind:'text',text_read:'Stale result'}})});await old;
assert.equal(tree.querySelector('#live-result .trace-input').textContent,'New result');
let finishText;
context.fetch=async(url,opts)=>url==='/examples/b-text.txt'?new Promise(resolve=>finishText=resolve):baseFetch(url,opts);
const loading=click('[data-story-slot="1"]');
const input=tree.querySelector('#live-input');input.value='User typed while loading';input.events.input();
finishText({ok:true,text:async()=>raw});await loading;
assert.equal(input.value,'User typed while loading');
"""

HOSTILE = r"""
const hostile='<img src=x onerror="globalThis.pwned=1"><script>evil()</script>';
const result={...envelope('a-image'),input:{kind:'image',text_read:hostile},receipt:{provider:'baseten',model:hostile,
 cost_usd:.01,latency_ms:1,preprocessing:{model:hostile,cost_usd:.00123,latency_ms:1500}}};
const target=tree.querySelector('#live-result');context.liveTest.renderLiveTrace(result,target);
assert.equal(target.querySelector('blockquote').textContent,hostile);
assert.ok(target.querySelector('.live-receipt').textContent.includes('$0.00'));assert.ok(target.textContent.includes('1.5'));
assert.ok(!target.querySelector('img'));assert.ok(!target.querySelector('script'));assert.equal(context.pwned,undefined);
// A manifest must never load remote, traversal, or executable preview URLs.
manifest.examples[0].file='../../private.txt';await context.liveTest.loadExamples();
assert.ok(tree.querySelector('#input-description').textContent.includes('could not be loaded'));
assert.ok(!reads.includes('/examples/../../private.txt'));
"""


PROVIDER_AND_PENDING = r"""
const radio=tree.querySelector('input[value="meta"]');radio.checked=true;radio.events.change();
const text=tree.querySelector('#live-input');text.value='Custom claim';text.events.input();
password.value='password-marker';
responseFactory=async()=>({ok:true,json:async()=>({...envelope('a-text','meta'),input:{kind:'text',text_read:'Server-normalized claim'}})});
await submit();
assert.deepEqual(paid.at(-1).body,{text:'Custom claim',password:'password-marker',provider:'meta'});
assert.equal(tree.querySelector('#live-result .trace-input').textContent,'Server-normalized claim');
// A pending manifest entry has neither a player nor a paid path.
manifest.examples.find(row=>row.id==='a-audio').status='pending';
await context.liveTest.loadExamples();await click('[data-input-kind="audio"]');
assert.ok(tree.querySelector('#live-submit').disabled);assert.ok(!tree.querySelector('#input-preview audio'));
assert.ok(!tree.querySelector('#example-saved').disabled);
const count=paid.length;await submit();assert.equal(paid.length,count);
// Once the same asset is ready, its player appears without changing its input hash.
manifest.examples.find(row=>row.id==='a-audio').status='ready';
await context.liveTest.loadExamples();assert.ok(tree.querySelector('#input-preview audio'));
"""

LAYOUT = r"""
assert.equal(property('.try-layout','grid-template-columns'),viewport<=1023?'minmax(0, 1fr)':'minmax(0, 1.3fr) minmax(0, 1fr)');
assert.equal(property('.try-layout > *','min-width'),'0');
assert.equal(property('.history-table','table-layout'),'fixed');
assert.equal(property('.compare-table','table-layout'),'fixed');
assert.equal(property('.provider-options','grid-template-columns'),'repeat(3, minmax(0, 1fr))');
assert.equal(tree.querySelector('.try-layout').children.filter(node=>node.tagName!=='#text')[1].className,'history-panel');
assert.equal(tree.querySelectorAll('.history-table th').length,4);
assert.equal(property('.live-section [hidden]','display'),'none');
"""


COMMITTED_CATALOGUE = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
const catalogue=JSON.parse(readFileSync(root+'/docs/examples/manifest.json','utf8'));
const gets=[];
context.fetch=async(url,options={})=>{
  assert.ok(!options.method);gets.push(url);
  if(url==='/examples/manifest.json')return {ok:true,json:async()=>catalogue};
  if(/^\/examples\/[abc]\.txt$/.test(url))return {ok:true,text:async()=>readFileSync(root+'/docs'+url,'utf8')};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'))};
  if(url==='/api/budget')return {ok:true,json:async()=>({day:'2026-11-03',daily_limit_usd:3,daily_remaining_usd:3,
    resets_at:'2099-11-04T00:00:00Z',status:'ready'})};
  if(url==='/api/history?limit=50')return {ok:true,json:async()=>({rows:[]})};
  const saved=catalogue.find(row=>row.saved_result===url);
  assert.ok(saved,`must not request an absent saved result: ${url}`);
  return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site'+url,'utf8'))};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const click=async selector=>{await tree.querySelector(selector).events.click();await new Promise(resolve=>setImmediate(resolve));};
assert.ok(!tree.querySelector('#corrected-draft'));
assert.ok(tree.querySelector('.compare-choice').textContent.includes(config.language==='zh'?'≈3× 費用':'≈3× cost'));
assert.ok(tree.querySelector('#live-privacy').textContent.includes('IP'));
for(const [index,story] of ['a','b','c'].entries()){
  await click(`[data-story-slot="${index}"]`);
  for(const kind of ['text','image','pdf','audio','video']){
    await click(`[data-input-kind="${kind}"]`);
    const asset=catalogue.find(row=>row.story===story&&row.kind===kind);
    assert.equal(asset.status,'ready');
    assert.ok(!tree.querySelector('#input-description').textContent.includes(config.language==='zh'?'待補':'pending'));
    assert.ok(!tree.querySelector('.asset-pending'));
    if(kind==='text'){
      const text=readFileSync(root+'/docs/examples/'+asset.file,'utf8');
      assert.equal(tree.querySelector('#live-input').value,text);
      assert.equal(tree.querySelector('#live-count').textContent,`${Array.from(text).length} / 600`);
    }else if(['image','pdf'].includes(kind)){
      assert.equal(tree.querySelector('#input-preview img').src,`/examples/${story}.png`);
    }else assert.equal(tree.querySelector(`#input-preview ${kind}`).src,asset.url);
    if(!asset.saved_result){
      const before=gets.length;
      assert.equal(tree.querySelector('#example-saved').textContent,config.language==='zh'?'已儲存結果待補':'Saved result pending');
      await click('#example-saved');assert.equal(gets.length,before);
      assert.equal(tree.querySelector('#example-saved-status').textContent,config.language==='zh'?'已儲存結果待補':'Saved result pending');
      assert.ok(tree.querySelector('#live-result').hidden);
    }
  }
}
"""


RATE_LIMIT = r"""
const fixed=Date.parse('2026-11-04T05:04:03Z');
context.Date=class extends Date {static now(){return fixed;}};
password.value='password-marker';
responseFactory=async()=>({ok:false,status:429,json:async()=>({error:config.code,retry_after:73})});
await submit();
const verify=language=>{
  const expected=new Date(fixed+73000).toLocaleString(language==='zh'?'zh-TW':'en-US',{
    month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',timeZoneName:'short'});
  const text=tree.querySelector('#live-status').textContent;
  assert.ok(text.includes(expected),text);
  assert.ok(text.includes(language==='zh'?'重設時間':'Resets'));
  if(config.code==='rate_limited')assert.ok(text.includes('IP'));
  assert.ok(!text.includes('{reset}'));assert.ok(!text.includes('password-marker'));
};
verify(config.language);context.stamps.setLanguage(config.language==='zh'?'en':'zh');
verify(config.language==='zh'?'en':'zh');
"""


RATE_LIMIT_UNKNOWN = r"""
password.value='password-marker';
responseFactory=async()=>({ok:false,status:429,json:async()=>({error:'rate_limited'})});
await submit();
assert.ok(tree.querySelector('#live-status').textContent.includes(config.language==='zh'?'無法取得重設時間':'Reset time unavailable'));
"""
