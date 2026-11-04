"""Offline interactions with real saved data; these do not rerun OCR/ASR."""
import pytest

from test_site_live_runtime import run_check
from test_site_examples_runtime import SETUP


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("viewport", [375, 768, 1440])
def test_stepper_uses_saved_claim_component_filings_tolerance_and_keyboard(language, viewport):
    run_check(STEPPER, language=language, viewport=viewport,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_stepper_missing_record_retains_a_safe_link_and_keyboard_navigation(language):
    run_check(STEPPER_FAILURE, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_provider_chart_toggle_uses_historical_data_and_survives_relocalization(language):
    run_check(CHART, language=language,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_history_time_is_explicit_utc_with_today_yesterday_and_date_fallback(language):
    run_check(UTC_TIME, language=language)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("compact_path", [False, True])
def test_saved_file_is_discovered_even_before_manifest_pointer_is_updated(language, compact_path):
    # The response is synthetic UI plumbing around the real frozen envelope.
    setup = SETUP.replace("saved_result:story==='a'&&kind==='text'?'/data/examples/a-text.json':null",
                          "saved_result:null")
    recording = ("{receipt:'docs/evidence/example-records/20261103T170500Z/a-text/receipt.json'}"
                 if compact_path else "{recorded_at:'2026-11-03T17:05:00Z'}")
    setup = setup.replace("mode:'recorded'})", f"mode:'recorded',recording:{recording}}})")
    run_check(setup + DISCOVERY, language=language)


STEPPER = r"""
context.URL=URL;
const record=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
const before=JSON.stringify(record),requests=[];
context.fetch=async (url,options={})=>{
  requests.push(url);assert.ok(!options.method);assert.ok(!JSON.stringify(options).includes('password'));
  assert.equal(url,'/data/live-demo-post.json');return {ok:true,json:async()=>record};
};
await context.liveTest.setupFollowNumber();
const tabs=tree.querySelectorAll('[data-follow-step]'),panel=tree.querySelector('#follow-panel');
const claim=record.claims.find(row=>row.program_verdict==='contradicted');
const fact=record.evidence.find(row=>claim.evidence_ids.includes(row.evidence_id));
assert.deepEqual(requests,['/data/live-demo-post.json']);assert.equal(tabs.length,3);
const claimSnapshot=JSON.parse(panel.querySelector('code').textContent);
assert.equal(claimSnapshot[config.language==='zh'?'主張值':'stated_value'],claim.stated_value);
assert.equal(claimSnapshot[config.language==='zh'?'期間':'period'],fact.period);
tabs[0].events.keydown({key:'ArrowRight',preventDefault(){}});
assert.equal(tabs[1].getAttribute('aria-selected'),'true');assert.equal(tabs[0].getAttribute('tabindex'),'-1');
assert.ok(tabs[1].focused);assert.equal(panel.getAttribute('aria-labelledby'),'follow-step-2');
assert.ok(panel.textContent.includes('$416.2B'));assert.ok(panel.textContent.includes('$313.7B'));
assert.ok(panel.textContent.includes('$102.5B'));assert.equal(panel.querySelectorAll('a').length,2);
for(const [index,link] of panel.querySelectorAll('a').entries()){
  assert.ok(link.href.startsWith('https://www.sec.gov/Archives/edgar/data/320193/'));
  assert.ok(link.href.includes(fact.components[index].accn.replaceAll('-','')));
}
tabs[1].events.keydown({key:'End',preventDefault(){}});
assert.equal(panel.getAttribute('aria-labelledby'),'follow-step-3');
assert.ok(panel.textContent.includes(claim.actual_value.toLocaleString(config.language==='zh'?'zh-TW':'en-US')));
assert.ok(panel.textContent.includes(claim.tolerance.toLocaleString(config.language==='zh'?'zh-TW':'en-US')));
assert.ok(panel.querySelector('code').textContent.includes(String(claim.stated_value)));
assert.ok(panel.querySelector('.follow-verdict').className.includes('is-contradicted'));
tabs[2].events.keydown({key:'Home',preventDefault(){}});
assert.equal(panel.getAttribute('aria-labelledby'),'follow-step-1');
assert.equal(tabs.filter(tab=>tab.getAttribute('tabindex')==='0').length,1);
tabs[0].events.keydown({key:'ArrowDown',preventDefault(){}});
assert.equal(tabs[1].getAttribute('aria-selected'),'true');assert.ok(tabs[1].focused);
tabs[1].events.keydown({key:'ArrowUp',preventDefault(){}});
assert.equal(tabs[0].getAttribute('aria-selected'),'true');assert.ok(tabs[0].focused);
assert.equal(JSON.stringify(record),before,'presentation never mutates saved evidence');
"""

STEPPER_FAILURE = r"""
context.fetch=async()=>({ok:false,status:404});
await context.liveTest.setupFollowNumber();
const panel=tree.querySelector('#follow-panel');
assert.ok(panel.textContent.includes(config.language==='zh'?'無法讀取':'could not load'));
assert.equal(tree.querySelector('.follow-record a').getAttribute('href'),'/data/live-demo-post.json');
tree.querySelector('[data-follow-step="2"]').events.click();
assert.ok(panel.textContent.includes(config.language==='zh'?'無法讀取':'could not load'));
"""

CHART = r"""
context.window.addEventListener=()=>{};
context.fetch=async url=>{assert.equal(url,'/data/site.json');return {ok:true,json:async()=>JSON.parse(readFileSync(root+'/docs/site/data/site.json','utf8'))};};
context.liveTest.setupControls();await context.liveTest.loadData();
const chart=tree.querySelector('#chart'),buttons=tree.querySelectorAll('[data-chart-provider]');
assert.equal(chart.querySelectorAll('.chart-row').length,3);
const chartSource=JSON.parse(readFileSync(root+'/docs/site/data/site.json','utf8'));
for(const id of ['baseten','fireworks','meta']){
  const button=tree.querySelector(`[data-chart-provider="${id}"]`);button.events.click();
  assert.equal(chart.querySelectorAll('.chart-row').length,1);
  const expected=chartSource.chart.find(row=>row.id===id);
  assert.ok(chart.textContent.includes(`${expected.without.percent}%`));
  assert.ok(chart.textContent.includes(`${expected.with_checks.percent}%`));
  assert.equal(button.getAttribute('aria-pressed'),'true');
  assert.equal(buttons.filter(item=>item.getAttribute('aria-pressed')==='true').length,1);
}
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.equal(chart.querySelectorAll('.chart-row').length,1);
tree.querySelector('[data-chart-provider="all"]').events.click();
assert.equal(chart.querySelectorAll('.chart-row').length,3);
"""

UTC_TIME = r"""
const now=new Date('2026-11-04T00:10:00Z');
assert.equal(context.liveTest.historyTime('2026-11-04T08:09:00+08:00',now),
  config.language==='zh'?'00:09 世界協調時間 · 今天':'00:09 UTC · today');
assert.equal(context.liveTest.historyTime('2026-11-03T23:59:00Z',now),
  config.language==='zh'?'23:59 世界協調時間 · 昨天':'23:59 UTC · yesterday');
assert.ok(context.liveTest.historyTime('2026-11-01T12:34:00Z',now).endsWith('2026-11-01'));
assert.equal(context.liveTest.historyTime('invalid',now),'—');
"""

DISCOVERY = r"""
await new Promise(resolve=>setImmediate(resolve));
assert.equal(tree.querySelector('#example-saved').textContent,config.language==='zh'?'查看已儲存結果':'See saved result');
assert.ok(tree.querySelector('#example-recording').textContent.includes('2026-11-03'));
assert.ok(tree.querySelector('#example-recording').textContent.includes('Baseten'));
await click('#example-saved');
assert.equal(paid.length,0);assert.equal(tree.querySelector('#live-result').hidden,false);
assert.ok(tree.querySelector('#live-result .live-corrections'));
"""
