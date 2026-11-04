"""Offline behavior checks for the final Try layout; browser geometry is separate."""
import pytest

from test_site_examples_runtime import SETUP
from test_site_live_runtime import run_check


@pytest.mark.parametrize("language", ["en", "zh"])
def test_idle_now_has_six_pending_stages_and_one_selected_story_hint(language):
    run_check(SETUP + r"""
const idle=tree.querySelector('#live-idle');
assert.equal(idle.hidden,false);assert.equal(tree.querySelector('#live-progress').hidden,true);
assert.equal(tree.querySelector('#live-running-bar').hidden,true);
assert.equal(tree.querySelector('#now-title').textContent,config.language==='zh'?'目前狀態':'Now');
assert.ok(idle.textContent.includes(config.language==='zh'?'目前沒有執行中的查核':'No check running'));
const stages=idle.querySelector('.terminal-stages').children;
assert.equal(stages.length,6);assert.ok(stages.every(stage=>stage.dataset.active==='false'));
assert.equal(tree.querySelectorAll('#story-expected').length,1);
assert.ok(tree.querySelector('#story-expected').textContent.includes('$416.2B'));
await click('[data-story-slot="1"]');
assert.ok(tree.querySelector('#story-expected').textContent.includes(config.language==='zh'?'證據支持':'Supported'));
assert.ok(!tree.querySelector('#story-expected').textContent.includes('$416.2B'));
assert.equal(tree.querySelector('#live-password').getAttribute('aria-describedby'),'live-password-note live-status');
assert.equal(paid.length,0);
""", language=language, page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_history_has_two_lines_relative_times_and_six_then_ten_more(language):
    run_check(SETUP + r"""
context.Date=class extends Date {static now(){return new Date('2026-11-04T12:00:00Z').getTime();}};
historyData=Array.from({length:50},(_,i)=>({id:`history-${i}`,story:i===2?null:'a',kind:'text',provider:'baseten',
 at:['2026-11-04T11:55:00Z','2026-11-04T10:00:00Z','2026-11-03T09:00:00Z'][i%3],
 verdict:'contradicted',latency_ms:15700,cost_usd:.02,device:'Desktop',browser:'Chrome'}));
await click('#history-refresh');
let rows=tree.querySelectorAll('[data-history-row]');assert.equal(rows.length,6);
assert.equal(rows[0].tagName,'button');assert.equal(rows[0].getAttribute('aria-haspopup'),'dialog');
assert.equal(rows[0].querySelector('.history-line-one').textContent,config.language==='zh'?'故事 A · 文字':'Story A · Text');
assert.ok(rows[0].querySelector('.history-line-two').textContent.startsWith(config.language==='zh'?'Baseten · 15.7 秒 · $0.02':'Baseten · 15.7 s · $0.02'));
assert.equal(rows[0].querySelector('.history-when').textContent,config.language==='zh'?'5 分鐘前':'5 min ago');
assert.equal(rows[1].querySelector('.history-when').textContent,config.language==='zh'?'2 小時前':'2 h ago');
assert.equal(rows[2].querySelector('.history-when').textContent,config.language==='zh'?'11月3日':'Nov 3');
assert.equal(rows[2].querySelector('.history-line-one').textContent,config.language==='zh'?'自訂文字 · 文字':'Custom text · Text');
assert.ok(rows[0].title.includes('2026-11-04T11:55:00.000Z · Desktop · Chrome'));
assert.ok(!rows[0].textContent.includes('Desktop'));
for(const count of [16,26,36,46,50]){await click('#history-more');assert.equal(tree.querySelectorAll('[data-history-row]').length,count);}
assert.equal(tree.querySelector('#history-more').hidden,true);
context.stamps.setLanguage(config.language==='zh'?'en':'zh');
assert.equal(tree.querySelectorAll('[data-history-row]').length,50);
assert.equal(paid.length,0);
""", language=language, page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_own_running_row_phone_bar_and_finished_summary_follow_the_request(language):
    setup = SETUP.replace('context.URL=URL;', r"""
context.URL=URL;
const listeners={};context.window.addEventListener=(key,fn)=>{listeners[key]=fn;};
context.window.removeEventListener=(key,fn)=>{if(listeners[key]===fn)delete listeners[key];};
context.window.innerHeight=900;
context.window.matchMedia=query=>({matches:query.includes('max-width')});
""")
    run_check(setup + r"""
let bounds={top:100,bottom:600,height:500};
tree.querySelector('#live-now').getBoundingClientRect=()=>bounds;
let scrolled=null;tree.querySelector('#live-now').scrollIntoView=options=>{scrolled=options;};
let finish;responseFactory=()=>new Promise(resolve=>finish=resolve);
password.value='password-marker';const running=submit();
assert.equal(tree.querySelectorAll('#history-rows .is-mine').length,1);
assert.equal(tree.querySelector('#history-rows .history-verdict').textContent,config.language==='zh'?'執行中':'Running');
assert.ok(tree.querySelector('#history-rows .history-line-two').textContent.includes(config.language==='zh'?'你':'you'));
assert.equal(tree.querySelector('#live-running-bar').hidden,true);
bounds={top:-600,bottom:-100,height:500};listeners.scroll();
assert.equal(tree.querySelector('#live-running-bar').hidden,false);
await click('#live-running-bar');assert.equal(scrolled.block,'start');
assert.equal(scrolled.behavior,'smooth');
const result=envelope();historyData=[{id:'finished',story:'a',kind:'text',provider:'baseten',
 at:'2026-11-04T12:00:00Z',verdict:'contradicted',latency_ms:6300,cost_usd:.01}];
finish({ok:true,status:200,json:async()=>result});await running;
assert.equal(tree.querySelector('#live-running-bar').hidden,true);
assert.equal(tree.querySelector('#live-idle').hidden,true);
assert.equal(tree.querySelectorAll('#history-rows .is-mine').length,0);
assert.equal(tree.querySelector('[data-history-row]').getAttribute('data-history-row'),'finished');
assert.equal(tree.querySelector('#live-progress h3').textContent,config.language==='zh'?'完成':'Done');
assert.equal(tree.querySelector('#live-progress details').open,false);
assert.equal(tree.querySelector('.terminal-metrics').children.length,3);
assert.ok(tree.querySelector('.terminal-metrics').textContent.includes('$0.01'));
assert.ok(tree.querySelector('.terminal-status').textContent.includes(config.language==='zh'?'用時 6.3 秒':'finished in 6.3 s'));
assert.ok(tree.querySelector('#live-progress .terminal-stages').children.every(stage=>stage.dataset.done==='true'));
assert.equal(tree.querySelector('.terminal-result-link').href,'#live-result');
assert.equal(tree.querySelector('#live-submit').textContent,config.language==='zh'?'執行查核':'Run check');
""", language=language, page="docs/zh/index.html" if language == "zh" else "docs/site/index.html", viewport=375)
