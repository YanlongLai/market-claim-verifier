"""Execute shipped form/trace JS in the existing offline DOM adapter."""
import subprocess

import pytest

from test_site_stamps_runtime import ROOT, run_check


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1280])
def test_saved_trace_has_ordered_public_steps_sec_row_and_safe_text(language, viewport):
    run_check(RENDER, language=language, viewport=viewport)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_live_submit_busy_success_failure_and_language_switch(language):
    run_check(FORM, language=language)


def test_pages_boundary_without_provider_key_or_network():
    result = subprocess.run(["node", "--test", "tests/node/live-boundary.test.mjs"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


RENDER = r"""
context.URL=URL;
const demo=JSON.parse(readFileSync(root+'/docs/site/data/live-demo.json','utf8'));
const target=tree.querySelector('#recorded-trace');
context.liveTest.renderLiveTrace(demo,target);
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
context.fetch=async (url,opts)=>{
  if(url==='data/live-demo.json')return {ok:true,json:async()=>demo};
  requests.push({url,opts});
  return new Promise(resolve=>{finish=resolve;});
};
context.liveTest.setupLive();
await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input'),form=tree.querySelector('#live-form'),submit=tree.querySelector('#live-submit');
input.value=demo.input;
const pending=form.events.submit({preventDefault(){}});
assert.equal(submit.disabled,true);assert.equal(form.getAttribute('aria-busy'),'true');
assert.equal(requests.length,1);assert.equal(requests[0].url,'/api/check');
assert.deepEqual(JSON.parse(requests[0].opts.body),{text:demo.input});
finish({ok:true,json:async()=>({...demo,mode:'live'})});await pending;
assert.equal(submit.disabled,false);assert.equal(form.getAttribute('aria-busy'),'false');
assert.equal(tree.querySelector('#live-result').hidden,false);
assert.equal(tree.querySelector('#live-result').querySelectorAll('.trace-step').length,7);
const failed=form.events.submit({preventDefault(){}});
finish({ok:false,json:async()=>({error:'budget_exhausted'})});await failed;
assert.equal(tree.querySelector('#live-result').hidden,true);
assert.ok(tree.querySelector('#recorded-trace').textContent.includes('FY2026Q3'));
context.stamps.setLanguage('zh');
assert.ok(tree.querySelector('#live-status').textContent.includes('明天'));
context.stamps.setLanguage('en');
assert.ok(tree.querySelector('#live-status').textContent.includes('try again tomorrow'));
"""
