import test from 'node:test';
import assert from 'node:assert/strict';
import {stateAt,architectureReveal,boundaries} from '../motion/v4/plan.js';
import {parseArgs} from '../motion/render.mjs';
import {redact,validateLiveResult} from '../record_v4.mjs';

test('nine director beats use exact cuts, including the final frame',()=>{
  assert.deepEqual(boundaries,[0,9,26,40,56,72,122,146,162,178]);
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
  assert.equal(stateAt(70).architecture.nodes[4],1);
});
test('new Wan accents stay inside the director beats and renderer chooses v4',()=>{
  assert.equal(stateAt(23).broll,'cards-fanning-out');
  assert.equal(stateAt(26).broll,null);
  assert.equal(stateAt(130).broll,'numbers-raining-into-filing');
  assert.equal(stateAt(133).broll,null);
  assert.equal(parseArgs(['--entry','v4/index.html','--t','70','--out','/tmp/v4']).entry,'v4/index.html');
});
test('real recordings replace pending state without moving any cut',()=>{
  const scenes=Array.from({length:9},()=>({}));
  scenes[5]={recording:{asset:'beat6.mp4'}};scenes[8]={recording:{asset:'beat9.mp4'}};
  assert.equal(stateAt(72,scenes).placeholder,false);
  assert.equal(stateAt(162,scenes).placeholder,false);
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
