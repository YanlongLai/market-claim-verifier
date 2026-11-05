"""Exercise the shipped terminal through form events in both reading layers."""
import pytest

from test_site_live_runtime import run_check


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("compare", [False, True])
def test_terminal_opens_polls_with_shared_cadence_and_collapses_on_result(language, compare):
    run_check(SCENE, language=language, compare=compare,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


SCENE = r"""
context.AbortController=AbortController;
let now=1000, nextTimer=0, finishPost, completed=false;
const timers=new Map(), polls=[], writes=[];
context.Date=class extends Date {static now(){return now;}};
context.setTimeout=(fn,ms)=>{timers.set(++nextTimer,{fn,ms});return nextTimer;};
context.clearTimeout=id=>timers.delete(id);
const saved=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
const providerIds=['meta','baseten','fireworks'];
const models={meta:'muse-spark-1.3',baseten:'meta-models/muse-spark-open-1026',fireworks:'accounts/fireworks/models/muse-spark-open'};
const result=provider=>({...saved,mode:'live',receipt:{provider,model:models[provider],cost_usd:.01,latency_ms:5000,preprocessing:null},input:{kind:'text',text_read:'Apple FY2025 revenue was $416B.'}});
context.fetch=async(url,opts={})=>{
  if(opts.method==='POST'){writes.push(JSON.parse(opts.body));return new Promise(resolve=>{finishPost=resolve;});}
  if(url.startsWith('/api/progress/')){
    assert.equal(opts.cache,'no-store');assert.ok(!JSON.stringify(opts).includes('offline-password'));
    polls.push({url,at:now});
    const after=Number(url.split('after=')[1]);
    const lines=[{t_s:.1,text:'model  running  step=1'},
      {t_s:4.3,text:'tool_call  lookup_fact  AMZN  revenue  2023Q3'},
      {t_s:4.4,text:'model  completed  step=2  $0.01000'},
      {t_s:4.5,text:'program_check  count=1'},
      {t_s:5,text:'verdict  supported  $0.01000  duration=5.0s'}];
    const end=completed?5:after===0?2:3;
    return {ok:true,json:async()=>({lines:lines.slice(after,end),done:completed,next:end})};
  }
  if(url==='/api/budget')return {ok:true,json:async()=>budgetFixture({status:'ready'})};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>saved};
  return publicFixture(url)||{ok:false,status:404,json:async()=>({})};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input');input.value='Apple FY2025 revenue was $416B.';input.events.input();
tree.querySelector('#live-password').value='offline-password';
tree.querySelector('#compare-all').checked=config.compare;
const pending=tree.querySelector('#live-form').events.submit({preventDefault(){}});
const panels=tree.querySelector('#live-progress').querySelectorAll('.live-terminal');
assert.equal(panels.length,config.compare?3:1);
assert.ok(panels.every(panel=>panel.querySelector('details').open));
assert.equal(panels[0].querySelector('h3').textContent,config.language==='zh'?'執行中':'Running');
assert.equal(panels[0].querySelector('.terminal-clock').textContent,'0:00');
assert.ok(panels[0].querySelector('.terminal-status').textContent.includes(config.compare?'Meta Model API':'Baseten'));
assert.equal(tree.querySelector('#live-submit').textContent,config.language==='zh'?'查核中…':'Checking…');
assert.equal(tree.querySelector('#live-submit').disabled,true);
assert.match(writes[0].client_run_id,/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
const tick=async()=>{const entry=[...timers].find(([,timer])=>timer.ms===700);assert.ok(entry);timers.delete(entry[0]);now+=700;entry[1].fn();await new Promise(resolve=>setImmediate(resolve));};
await tick();assert.equal(polls.length,1);
assert.ok(polls[0].url.includes(writes[0].client_run_id+'?after=0'));
assert.ok(panels[0].querySelector('pre').textContent.includes('+4.3 s tool_call lookup_fact AMZN revenue 2023Q3'));
assert.equal(panels[0].querySelector('.terminal-stages').children[2].dataset.active,'true');
assert.ok(panels[0].querySelector('.terminal-clock').textContent === '0:00');
for(let index=0;index<4;index++)await tick();
assert.equal(polls.length,1,'700 ms UI ticks do not burst the origin');
await tick();assert.equal(polls.length,2);assert.ok(polls[1].at-polls[0].at>=3000);
assert.equal(panels[0].querySelector('.terminal-stages').children[3].dataset.active,'true');
assert.equal(panels[0].querySelector('.terminal-clock').textContent,'0:04');
assert.equal(panels[0].querySelector('.terminal-stages').children[2].dataset.done,'true');
completed=true;
finishPost({ok:true,status:200,json:async()=>config.compare?{runs:providerIds.map(result)}:result('baseten')});
await pending;
assert.ok(panels.every(panel=>!panel.querySelector('details').open));
assert.ok(panels.every(panel=>panel.querySelector('summary').textContent.includes(config.language==='zh'?'伺服器紀錄（5 行）':'Server log (5 lines)')));
assert.ok(panels.every(panel=>panel.querySelector('.terminal-stages').children[5].dataset.active==='true'));
assert.equal(tree.querySelector('#live-result').hidden,false);
assert.ok(![...timers.values()].some(timer=>timer.ms===700),'poll timer stops on completion');
assert.ok(!panels[0].textContent.includes('offline-password'));
assert.ok(!panels[0].textContent.includes(writes[0].text));
if(config.compare){
  for(let index=0;index<3;index++){
    const id=writes[0].client_run_id.slice(0,-1)+((parseInt(writes[0].client_run_id.slice(-1),16)+index)%16).toString(16);
    assert.ok(polls.some(poll=>poll.url.includes('/'+id+'?')));
  }
}
const terminalCss=readFileSync(root+'/docs/site/styles.css','utf8');assert.match(terminalCss,/\.terminal-lines\s*\{[^}]*font:\s*15px/);
"""


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("error", ["locked", "busy", "slow_down"])
def test_abuse_errors_are_localized_and_terminal_stops(language, error):
    run_check(r"""
context.AbortController=AbortController;
const timers=new Map();let timer=0;
context.setTimeout=(fn,ms)=>{timers.set(++timer,{fn,ms});return timer;};
context.clearTimeout=id=>timers.delete(id);
const saved=JSON.parse(readFileSync(root+'/docs/site/data/live-demo-post.json','utf8'));
context.fetch=async(url,opts={})=>{
  if(opts.method==='POST')return {ok:false,status:429,json:async()=>({error:config.error})};
  if(url==='/api/budget')return {ok:true,json:async()=>budgetFixture({status:'ready'})};
  if(url==='/data/live-demo-post.json')return {ok:true,json:async()=>saved};
  return publicFixture(url)||{ok:false,status:404,json:async()=>({})};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input');input.value='Apple FY2025 revenue was $416B.';input.events.input();
tree.querySelector('#live-password').value='offline-password';
await tree.querySelector('#live-form').events.submit({preventDefault(){}});
const message=tree.querySelector('#live-status').textContent;
const messages=config.language==='zh'?{locked:'已鎖定 30 分鐘',busy:'伺服器忙碌',slow_down:'等候 10 分鐘'}:
  {locked:'Locked for 30 minutes',busy:'server is busy',slow_down:'wait 10 minutes'};
assert.ok(message.includes(messages[config.error]),message);
if(config.language==='en')assert.ok(!/[\u3400-\u9fff]/.test(message));
else assert.ok(!/[A-Za-z]{2,}/.test(message));
assert.equal(tree.querySelector('#live-progress').querySelector('details').open,true,'failures retain the open server log');
assert.ok(tree.querySelector('#live-progress .history-verdict').textContent);
assert.ok(![...timers.values()].some(timer=>timer.ms===700));
""", language=language, error=error,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("case", ["timeout_behind_proxy", "overloaded"])
def test_slow_or_overloaded_provider_is_named_not_generic(language, case):
    run_check(PROVIDER_FAILURE_SCENE.replace("CASE", case), language=language,
              page="docs/zh/index.html" if language == "zh" else "docs/site/index.html")


PROVIDER_FAILURE_SCENE = r"""
context.AbortController=AbortController;
let timerId=0;context.setTimeout=()=>++timerId;context.clearTimeout=()=>{};
const failureCase='CASE';
const errorLine=failureCase==='overloaded'?'error  provider_overloaded  provider_status=503  $0.04834':'error  timeout  $0.04693';
// Behind the proxy the reply can be a bare "unavailable"; the server's own log line still says why.
const reply=failureCase==='overloaded'?{error:'provider_overloaded'}:{error:'unavailable'};
context.fetch=async(url,opts={})=>{
  if(opts.method==='POST')return {ok:false,status:503,json:async()=>reply};
  if(url.startsWith('/api/progress/'))return {ok:true,json:async()=>({lines:[{t_s:.1,text:'model  step=1  running'},{t_s:85,text:errorLine}],done:true,next:2})};
  if(url==='/api/budget')return {ok:true,json:async()=>budgetFixture({status:'ready'})};
  return publicFixture(url)||{ok:false,status:404,json:async()=>({})};
};
context.liveTest.setupLive();await new Promise(resolve=>setImmediate(resolve));
const input=tree.querySelector('#live-input');input.value='Apple FY2025 revenue was $416B.';input.events.input();
tree.querySelector('#live-password').value='offline-password';
await tree.querySelector('#live-form').events.submit({preventDefault(){}});
const zh=config.language==='zh';
const status=tree.querySelector('#live-status').textContent;
if(failureCase==='overloaded') assert.ok(status.includes(zh?'過載':'overloaded'),status);
else assert.ok(status.includes(zh?'回應緩慢或過載':'slow or overloaded'),status);
assert.ok(!status.includes(zh?'即時查核暫時無法使用':'Live checking is unavailable'),status);
const pill=tree.querySelector('#live-progress .history-verdict');
assert.ok(pill.className.includes('is-timeout'),pill.className);
"""
