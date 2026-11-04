import test from 'node:test';
import assert from 'node:assert/strict';
import {stateAt,architectureReveal,boundaries,repostCascade,liveTakeCrop,siteURL} from '../motion/v4/plan.js';
import {parseArgs} from '../motion/render.mjs';
import {redact,validateLiveResult,showTraceAndFiling,presentation} from '../record_v4.mjs';

test('nine director beats use exact cuts, including the final frame',()=>{
  assert.deepEqual(boundaries,[0,9,22,34,50,66,124,148,164,178]);
  for(let i=0;i<9;i++){
    assert.equal(stateAt(boundaries[i]).shot,`v40${i+1}`);
    assert.equal(stateAt(boundaries[i+1]-1/30).shot,`v40${i+1}`);
    assert.equal(stateAt(boundaries[i]).placeholder,i===5||i===8);
  }
  assert.equal(stateAt(178).shot,'v409');
  assert.throws(()=>stateAt(178.001));assert.throws(()=>stateAt(NaN));
});
test('five architecture stages reveal in sequence over fourteen seconds',()=>{
  assert.deepEqual(architectureReveal(0).nodes,[0,0,0,0,0]);
  assert.deepEqual(architectureReveal(14).nodes,[1,1,1,1,1]);
  assert.deepEqual(architectureReveal(14).links,[1,1,1,1]);
  const half=architectureReveal(6);
  assert.equal(half.nodes[0],1);assert.equal(half.nodes[4],0);
  assert.equal(stateAt(63).architecture.nodes[4],1);
});
test('all of beat 7 is terminal only and renderer chooses v4',()=>{
  for(let frame=124*30;frame<148*30;frame++)assert.equal(stateAt(frame/30).broll,null);
  assert.equal(parseArgs(['--entry','v4/index.html','--t','70','--out','/tmp/v4']).entry,'v4/index.html');
});
test('beat 2 spreads five fading copies of the post without a numeric metric',()=>{
  for(const t of [0,.5,1,2,4,8,12.99]){
    const copies=repostCascade(t);
    assert.equal(copies.length,5);
    assert(copies.every(c=>c.opacity>=0&&c.opacity<=.4&&c.scale>0&&c.scale<=1));
    stateAt(9+t).cascade.forEach((copy,i)=>{
      for(const key of Object.keys(copy))assert(Math.abs(copy[key]-copies[i][key])<1e-10);
    });
    assert.equal(stateAt(9+t).broll,null);
    assert.equal(stateAt(9+t).reposts,undefined);
  }
  assert(repostCascade(2)[0].x>repostCascade(1)[0].x);
  assert(repostCascade(4)[0].opacity<repostCascade(2)[0].opacity);
  assert.deepEqual(repostCascade(4.5)[0],repostCascade(0)[0]);
  assert.equal(stateAt(22).cascade,null);
});
test('only beat 9 carries the small site URL, for its entire live take',()=>{
  assert.equal(siteURL,'hackathon.dappgo.com');
  for(const t of [164,164+1/30,170,178-1/30,178])assert.equal(stateAt(t).siteURL,siteURL);
  for(const t of [0,9,66,124,148,164-1/30])assert.equal(stateAt(t).siteURL,null);
});
test('1.6× capture and D4 crop centre the result with a 20px body floor at 480w',()=>{
  assert.deepEqual(presentation.viewport,[1920,1080]);assert.equal(presentation.css_zoom,1.6);
  assert(presentation.body_font_px*presentation.css_zoom*1.4/4>=20);
  for(const shot of ['v406','v409']){
    const crop=liveTakeCrop(shot);
    assert.equal(crop.scale,1.4);
    assert(crop.x<=0&&crop.x+1920*crop.scale>=1920);
    assert(crop.y<=0&&crop.y+1080*crop.scale>=1080);
    assert(Math.abs(960*crop.scale+crop.x-960)<1e-9);
  }
  const receipt=liveTakeCrop('v406');
  // Receipt positions in the retained verdict and draft-scroll source frames.
  for(const y of [240,540,700])assert(y*receipt.scale+receipt.y>=0&&(y+32)*receipt.scale+receipt.y<=880);
  assert.deepEqual(stateAt(66).liveTake,liveTakeCrop('v406'));
  assert.deepEqual(stateAt(164).liveTake,liveTakeCrop('v409'));
  assert.equal(stateAt(34).liveTake,null);
});
test('input pictures hold screenshot/PDF/audio/video on their specified intervals',()=>{
  for(const [a,b,index] of [[0,3.5,0],[3.5,7,1],[7,10.5,2],[10.5,12,3]]){
    assert.equal(stateAt(22+a).input,index);
    assert.equal(stateAt(22+b-1/30).input,index);
  }
});

function traceFixture({opens=true}={}){
  const actions=[],report={},state={open:false,inspect:false};
  const fact={ticker:'AAPL',derived:true,evidence_id:'E3',derivation:'FY2025 - 9M YTD',
    value:102466000000,components:[{value:416161000000},{value:313695000000}]};
  const result={evidence:[fact],events:[{kind:'model'},{kind:'tool_call',name:'lookup_fact'},
    {kind:'tool_result'},{kind:'tool_call',name:'compute_change'},{kind:'verdict'}]};
  const pre={id:'pre',innerText:async()=>JSON.stringify(fact),evaluate:async()=>360};
  const details={evaluate:async()=>state.inspect,locator:()=>pre};
  const steps={nth:index=>({id:`step${index}`,isVisible:async()=>state.open,evaluate:async()=>true})};
  const page={locator:selector=>selector.endsWith('.live-trace')?{evaluate:async()=>state.open}:
    selector.endsWith('.trace-step')?steps:{nth:()=>({locator:()=>details})}};
  return {result,report,actions,page,mark:phase=>actions.push(phase),
    frame:async selector=>actions.push(typeof selector==='string'?selector:selector.id),
    click:async selector=>{actions.push(selector);if(selector.includes('live-trace'))state.open=opens;else state.inspect=true;},
    hold:async ms=>actions.push(ms)};
}
test('choreography opens the real summary before showing every tool and final verdict',async()=>{
  const fixture=traceFixture();await showTraceAndFiling(fixture);
  assert.equal(fixture.report.trace_details_open,true);
  assert.equal(fixture.report.apple_inspect_open,true);
  assert.equal(fixture.report.tool_calls_shown,2);
  assert.equal(fixture.report.program_verdict_shown,true);
  assert.deepEqual(fixture.actions.filter(a=>typeof a==='string'&&a.startsWith('step')),['step1','step3','step4']);
  assert.equal(fixture.actions.filter(a=>a===700).length,4);
  assert.equal(fixture.actions.at(-1),2000);
  assert.equal(fixture.report.apple_derivation.annual-fixture.report.apple_derivation.nine_months,
    fixture.report.apple_derivation.quarter);
  assert(fixture.actions.indexOf('#live-result .live-trace > summary')<fixture.actions.indexOf('step1'));
});
test('a collapsed details element fails instead of claiming tools were shown',async()=>{
  const fixture=traceFixture({opens:false});
  await assert.rejects(showTraceAndFiling(fixture),/trace_details_not_open/);
  assert.equal(fixture.report.tool_calls_shown,undefined);
});
test('real recordings replace pending state without moving any cut',()=>{
  const scenes=Array.from({length:9},()=>({}));
  scenes[5]={recording:{asset:'beat6.mp4'}};scenes[8]={recording:{asset:'beat9.mp4'}};
  assert.equal(stateAt(66,scenes).placeholder,false);
  assert.equal(stateAt(164,scenes).placeholder,false);
  assert.equal(stateAt(178,scenes).shot,'v409');
});
test('recording receipts strip nested password fields, budgets and secret echoes',()=>{
  const result=redact({password:'private',nested:{PASSWORD:'private',message:'echo private',cost_usd:.01,input_tokens:100},
    events:[{arguments:{text:'public',password:'private'}}],budget:{remaining:2},account_balance:99},'private');
  assert.deepEqual(result,{nested:{message:'echo [REDACTED]',cost_usd:.01,input_tokens:100},events:[{arguments:{text:'public'}}]});
  assert(!JSON.stringify(result).includes('private'));
});
test('saved or incomplete envelopes cannot be presented as a real live capture',()=>{
  const result={mode:'live',provider:'baseten',model:'meta-models/muse-spark-open-1026',verdict:'contradicted',
    cost_usd:.01,latency_ms:6000,corrections:{edits:[{original:'$416.2 billion',replacement:'$102.5 billion'}]},
    events:[{kind:'tool_call'}],evidence:[{filing_url:'https://www.sec.gov/Archives/edgar/data/1/a.htm'}]};
  assert.doesNotThrow(()=>validateLiveResult(result));
  for(const patch of [{mode:'recorded'},{mode:'mock'},{provider:'meta'},{events:[]},{corrections:{edits:[]}},
    {latency_ms:null},{evidence:[]}])assert.throws(()=>validateLiveResult({...result,...patch}));
});
