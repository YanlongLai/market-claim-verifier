"""Exercise shipped example UI and hostile OCR text in the offline DOM."""
import pytest

from test_site_live_runtime import run_check
from test_site_examples_runtime import SETUP


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1280])
@pytest.mark.parametrize("has_correction", [True, False])
def test_model_read_block_is_first_safe_localized_and_trace_is_collapsed(language, viewport, has_correction):
    run_check(READ_BLOCK, language=language, viewport=viewport, has_correction=has_correction,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_cards_saved_pending_password_live_busy_and_budget_paths(language):
    run_check(SETUP + CARDS, language=language, page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


READ_BLOCK = r"""
context.URL=URL;
const saved=JSON.parse(readFileSync(root+'/docs/site/data/examples/text.json','utf8'));
const hostile='<img src=x onerror="globalThis.pwned=1"><script>evil()</script> Apple Q4 $416.2B';
const result={...saved,input:{example_id:'image',kind:'image',text_read:hostile,
  preprocessing:{model:'<svg onload=evil()>',provider:'meta',cost_usd:.00123,latency_ms:1500}}};
if(!config.has_correction)result.corrections={...saved.corrections,edits:[]};
const target=tree.querySelector('#live-result');
context.liveTest.renderLiveTrace(result,target);
const verify=language=>{
  assert.deepEqual(target.children.map(node=>node.className),['live-input-read','live-receipt','trace-head','live-corrections','live-proof','live-trace']);
  const head=target.querySelector('.trace-head');
  assert.equal(head.querySelectorAll('.trace-verdict').length,1);
  const receipt=target.querySelector('.live-receipt');
  assert.ok(receipt.textContent.includes('$0.00'));
  assert.ok(receipt.textContent.includes('1.5'));
  assert.ok(!receipt.querySelector('svg'));
  const input=target.querySelector('.live-input-read');
  assert.equal(input.querySelector('h5').textContent,language==='zh'?'模型讀到了什麼':'What the model read');
  assert.equal(input.querySelector('blockquote').textContent,hostile);
  assert.ok(!input.querySelector('img'));assert.ok(!input.querySelector('script'));assert.ok(!input.querySelector('svg'));
  assert.ok(!input.textContent.includes('[object Object]'));
  const trace=target.querySelector('.live-trace');
  assert.equal(trace.tagName,'details');assert.equal(trace.open,!config.has_correction);
  assert.equal(trace.querySelector('summary').textContent,language==='zh'?
    `代理執行過程（${result.events.length} 個步驟）`:`Agent trace (${result.events.length} steps)`);
};
verify(config.language);
const other=config.language==='zh'?'en':'zh';context.stamps.setLanguage(other);
context.liveTest.renderLiveTrace(result,target);verify(other);
assert.equal(context.pwned,undefined);
"""


CARDS = r"""
assert.equal(tree.querySelectorAll('[data-input-kind]').length,5);
await click('#example-saved');
assert.equal(paid.length,0);assert.ok(!tree.querySelector('#live-result').hidden);
assert.equal(tree.querySelector('#live-result .trace-input').textContent,raw);
await click('[data-input-kind="image"]');
const missingBefore=reads.filter(url=>url==='/data/examples/a-image.json').length;
await click('#example-saved');
assert.equal(reads.filter(url=>url==='/data/examples/a-image.json').length,missingBefore);
assert.equal(paid.length,0);assert.ok(tree.querySelector('#live-result').hidden);
assert.equal(tree.querySelector('#example-saved-status').textContent,config.language==='zh'?'已儲存結果待補':'Saved result pending');
await submit();assert.equal(paid.length,0);
assert.ok(tree.querySelector('#live-status').textContent.includes(config.language==='zh'?'密碼':'password'));
password.value='example-password-marker';
let finish;
responseFactory=()=>new Promise(resolve=>finish=resolve);
const pending=submit();assert.ok(tree.querySelector('#live-submit').disabled);assert.ok(password.disabled);
await submit();assert.equal(paid.length,1);
assert.deepEqual(paid[0].body,{example_id:'a-image',password:'example-password-marker',provider:'baseten'});
assert.ok(!JSON.stringify(paid[0].opts.headers).includes('example-password-marker'));
finish({ok:true,status:200,json:async()=>envelope('a-image')});await pending;
assert.equal(context.liveTest.state().liveStatus,'complete');
assert.equal(tree.querySelector('#live-result .trace-input').textContent,raw);
assert.ok(!tree.textContent.includes('example-password-marker'));
budgetStatus='budget_exhausted';await context.liveTest.refreshLiveBudget();
assert.ok(tree.querySelector('#live-submit').disabled);assert.ok(!tree.querySelector('#example-saved').disabled);
await click('[data-input-kind="text"]');await click('#example-saved');assert.equal(paid.length,1);
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.ok(tree.querySelector('#live-result').textContent.includes(config.language==='zh'?'What the model read':'模型讀到了什麼'));
"""
