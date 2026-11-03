import test from 'node:test';
import assert from 'node:assert/strict';
import {stateAt,architectureReveal,boundaries} from '../motion/v4/plan.js';
import {parseArgs} from '../motion/render.mjs';

test('nine director beats use exact cuts, including the final frame',()=>{
  assert.deepEqual(boundaries,[0,6,26,40,56,72,122,146,162,178]);
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
  assert.equal(stateAt(20).broll,'cards-fanning-out');
  assert.equal(stateAt(23).broll,null);
  assert.equal(stateAt(130).broll,'numbers-raining-into-filing');
  assert.equal(stateAt(133).broll,null);
  assert.equal(parseArgs(['--entry','v4/index.html','--t','70','--out','/tmp/v4']).entry,'v4/index.html');
});
