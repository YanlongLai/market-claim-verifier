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


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [390, 768, 1440])
def test_budget_remaining_progress_low_warning_midnight_and_stops(language, viewport):
    run_check(BUDGET, language=language, viewport=viewport)


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
let remaining=3,budgetReads=0;
const budget=()=>({day:'2026-11-02',daily_limit_usd:3,daily_remaining_usd:remaining,daily_spent_usd:3-remaining,
  resets_at:'2099-11-03T00:00:00Z',status:remaining===0?'budget_exhausted':'ready'});
// Keep rollover timers inert in this DOM test; the real browser owns them.
context.setTimeout=(fn,ms)=>ms>32000?0:setTimeout(fn,ms);context.clearTimeout=clearTimeout;
context.fetch=async (url,opts)=>{
  if(url==='data/live-demo.json')return {ok:true,json:async()=>demo};
  if(url==='/api/budget'){budgetReads++;assert.equal(opts.cache,'no-store');return {ok:true,json:async()=>budget()};}
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
assert.ok(tree.querySelector('#recorded-trace').textContent.includes('FY2026Q3'));
context.stamps.setLanguage('zh');
assert.ok(tree.querySelector('#live-status').textContent.includes('重設'));
context.stamps.setLanguage('en');
assert.ok(tree.querySelector('#live-status').textContent.includes('00:00 UTC'));
await form.events.submit({preventDefault(){}});assert.equal(requests.length,2);
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
