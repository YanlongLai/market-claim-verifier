"""Exercise shipped example UI and hostile OCR text in the offline DOM."""
import pytest

from test_site_live_runtime import run_check


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_model_read_block_is_first_safe_localized_and_trace_is_collapsed(language, viewport):
    run_check(READ_BLOCK, language=language, viewport=viewport,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_cards_saved_pending_password_live_busy_and_budget_paths(language):
    run_check(CARDS, language=language, page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


READ_BLOCK = r"""
context.URL=URL;
const saved=JSON.parse(readFileSync(root+'/docs/site/data/examples/text.json','utf8'));
const hostile='<img src=x onerror="globalThis.pwned=1"><script>evil()</script> Apple Q4 $416.2B';
const result={...saved,input:{example_id:'image',kind:'image',text_read:hostile,
  preprocessing:{model:'<svg onload=evil()>',provider:'meta',cost_usd:.00123,latency_ms:1500}}};
const target=tree.querySelector('#example-result');
context.liveTest.renderLiveTrace(result,target);
const verify=language=>{
  assert.deepEqual(target.children.map(node=>node.className),['live-input-read','trace-head','live-corrections','live-proof','live-trace']);
  const input=target.querySelector('.live-input-read');
  assert.equal(input.querySelector('h5').textContent,language==='zh'?'模型讀到了什麼':'What the model read');
  assert.equal(input.querySelector('blockquote').textContent,hostile);
  assert.ok(input.textContent.includes('$0.00123'));
  assert.ok(input.textContent.includes('1.5'));
  assert.ok(!input.querySelector('img'));assert.ok(!input.querySelector('script'));assert.ok(!input.querySelector('svg'));
  assert.ok(!input.textContent.includes('[object Object]'));
  const trace=target.querySelector('.live-trace');
  assert.equal(trace.tagName,'details');assert.ok(!trace.open);
  assert.equal(trace.querySelector('summary').textContent,language==='zh'?'代理執行過程':'Agent trace');
};
verify(config.language);
const other=config.language==='zh'?'en':'zh';context.stamps.setLanguage(other);
context.liveTest.renderLiveTrace(result,target);verify(other);
assert.equal(context.pwned,undefined);
"""


CARDS = r"""
context.URL=URL;context.AbortController=AbortController;
context.setTimeout=()=>0;context.clearTimeout=()=>{};
const saved=JSON.parse(readFileSync(root+'/docs/site/data/examples/text.json','utf8'));
const index=JSON.parse(readFileSync(root+'/docs/site/data/examples/index.json','utf8'));
const post=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
let calls=[],finish,spent=false;
context.fetch=async (url,opts)=>{
  if(url==='/data/examples/index.json')return {ok:true,json:async()=>index};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>post};
  if(url==='/data/examples/text.json')return {ok:true,json:async()=>saved};
  if(url==='/data/examples/image.json')return {ok:false,status:404};
  if(url==='/api/budget')return {ok:true,json:async()=>({day:'2026-11-03',daily_limit_usd:3,
    daily_remaining_usd:spent?0:3,resets_at:'2099-11-04T00:00:00Z',status:spent?'budget_exhausted':'ready'})};
  assert.equal(url,'/api/check-example');calls.push({url,opts});
  return new Promise(resolve=>finish=resolve);
};
const exampleCards=tree.querySelectorAll('[data-example-card]');assert.equal(exampleCards.length,5);
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const password=tree.querySelector('#live-password');password.focus=()=>{};
assert.equal(password.value,'');
await tree.querySelector('[data-example-saved="text"]').events.click();
assert.equal(calls.length,0);assert.ok(!tree.querySelector('#example-result').hidden);
assert.equal(tree.querySelector('#example-result .trace-input').textContent,saved.input.text_read);
await tree.querySelector('[data-example-saved="image"]').events.click();
assert.equal(calls.length,0);assert.ok(tree.querySelector('#example-result').hidden);
assert.equal(tree.querySelector('#example-saved-status').textContent,config.language==='zh'?'已儲存結果待補':'Saved result pending');
const run=tree.querySelector('[data-example-run="image"]');assert.ok(!run.disabled);
assert.ok(tree.querySelector('[data-example-run="audio"]').disabled);
assert.ok(tree.querySelector('[data-example-run="video"]').disabled);
await run.events.click();assert.equal(calls.length,0);
assert.ok(tree.querySelector('#live-status').textContent.includes(config.language==='zh'?'密碼':'password'));
password.value='example-password-marker';
const pending=run.events.click();assert.ok(run.disabled);assert.ok(password.disabled);
await run.events.click();assert.equal(calls.length,1);
assert.deepEqual(JSON.parse(calls[0].opts.body),{example_id:'image',password:'example-password-marker'});
assert.ok(!JSON.stringify(calls[0].opts.headers).includes('example-password-marker'));
finish({ok:true,status:200,json:async()=>({...saved,mode:'live',input:{...saved.input,example_id:'image',kind:'image'}})});
await pending;
assert.equal(context.liveTest.state().liveStatus,'complete');
assert.equal(tree.querySelector('#live-result .trace-input').textContent,saved.input.text_read);
assert.ok(!tree.textContent.includes('example-password-marker'));
spent=true;await context.liveTest.refreshLiveBudget();
assert.ok(tree.querySelectorAll('[data-example-run]').every(button=>button.disabled));
assert.ok(tree.querySelectorAll('[data-example-saved]').every(button=>!button.disabled));
await tree.querySelector('[data-example-saved="text"]').events.click();assert.equal(calls.length,1);
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.ok(tree.querySelector('#example-result').textContent.includes(config.language==='zh'?'What the model read':'模型讀到了什麼'));
"""
