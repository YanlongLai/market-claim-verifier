import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {parseArgs} from '../motion/render.mjs';
import {assertV3Layout} from '../motion/v3/layout-checks.mjs';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
const plain=html=>html.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ');
function page(search='') {
  const stage={dataset:{},style:{},innerHTML:''};
  const context={document:{getElementById:()=>stage},URLSearchParams,location:{search}};
  context.window=context;context.globalThis=context;vm.createContext(context);
  for(const file of ['logic.js','v3/hover-source.js','v3/data.js','v3/motion.js']) vm.runInContext(read('../motion/'+file),context);
  return {window:context,stage};
}
function at(scene,fn) {
  const {window,stage}=page(),shot=window.timeline.shots.find(s=>s.id.includes(scene));
  window.seek(shot.end-.01);return fn(window,stage,shot);
}

test('v007 opens with disclosure and product on frame zero; query seek works',()=>{
  const {window,stage}=page();
  const disclosure=read('../JUDGE_INTRO.md').match(/^> (.+)$/m)[1],shot=window.timeline.shots[0];
  assert.equal(window.frame.time,0);
  for(const t of [0,(shot.start+shot.end)/2,shot.end-1/30]) {
    window.seek(t);
    assert(plain(stage.innerHTML).includes(disclosure));
    assert.match(plain(stage.innerHTML),/Market Claim Verifier/);
    assert.match(stage.innerHTML,/416\.2B/);assert.match(stage.innerHTML,/Open saved check/);
    const text=window.frame.boxes.find(b=>b.className==='body disclosure');
    assert.equal(text.text,disclosure);assert(text.size>=64);
  }
  assert.equal(page('?t=100').window.frame.time,100);
});

test('all v007 frames obey safe rectangles/type floors without a browser',()=>{
  const {window,stage}=page();
  for(let i=0;i<Math.ceil(window.timeline.duration*30);i++) {
    window.seek(i/30);
    for(const box of window.frame.boxes) {
      assert(box.size>=56,box.text);
      assert(box.x>=64&&box.x+box.w<=1856,box.text);
      assert(box.y>=64&&box.y+box.h<=880,box.text);
      if(box.className==='headline')assert(box.size>=96);
    }
    assert(!/NaN|Infinity|undefined/.test(stage.innerHTML));
    for(const value of stage.innerHTML.matchAll(/class="number" style="font-size:(\d+)px"/g)) assert(+value[1]>=96);
  }
});

test('v007 seek is deterministic after arbitrary backwards and forwards seeks',()=>{
  const {window,stage}=page(),times=window.MOTION_DATA.keyframes.map(f=>f.t);
  const expected=times.map(t=>{window.seek(t);return [stage.innerHTML,JSON.stringify(window.frame)];});
  for(let i=times.length-1;i>=0;i--) {
    window.seek(window.timeline.duration-times[i]);window.seek(times[i]);
    assert.equal(stage.innerHTML,expected[i][0]);assert.equal(JSON.stringify(window.frame),expected[i][1]);
  }
  assert.throws(()=>window.seek(NaN),/finite/);assert.throws(()=>window.seek(Infinity),/finite/);
  window.seek(-10);assert.equal(window.frame.time,0);
  window.seek(1000);assert.equal(window.frame.time,window.timeline.duration);
});

test('Hover uses real H assets, site pose clock, thruster and spotlight alphas',()=>{
  const {window,stage}=page(),a=window.MOTION_DATA.hover_anchors;
  for(const [t,age] of a.slice(0,-1)) {
    window.seek(t+.001);
    assert(Math.abs(window.frame.hover.siteAge-age)<10);
    assert.match(stage.innerHTML,/docs\/site\/img\/auditor\/H\//);
  }
  window.seek(a.find(a=>a[1]===3700)[0]+.2);
  assert.equal(window.frame.hover.phase,'compare');
  assert.match(stage.innerHTML,/416\.2B/);assert.match(stage.innerHTML,/102\.5B/);assert.match(stage.innerHTML,/FALSE/);
  assert(window.frame.hover.shade>0);assert.match(stage.innerHTML,/class="spotlight"/);
  assert(window.frame.hover.postAlpha>0&&window.frame.hover.filingAlpha>0&&window.frame.hover.yearAlpha>0);
  for(const name of ['filing','post','year'])assert(stage.innerHTML.includes(`data-beam="${name}"`));
  window.seek(a.find(a=>a[1]===4800)[0]+.01);
  assert.equal(window.frame.hover.pose,'stamp-down');assert.equal(window.frame.hover.thruster,'burst');
  assert(window.frame.hover.dip>0);assert.match(stage.innerHTML,/≈4×/);
});

test('Hover searches before locking the quarter and reserves detected beats around the strike',()=>{
  const {window}=page(),a=window.MOTION_DATA.hover_anchors,
    find=a.find(([t,age])=>age===2300)[0],lock=a.find(([t,age])=>age===2900)[0];
  window.seek(find+.001);const first=JSON.stringify(window.frame.hover.row);
  assert(window.frame.hover.finding&&!window.frame.hover.locked);
  window.seek((find+lock)/2);
  assert.notEqual(JSON.stringify(window.frame.hover.row),first);
  window.seek(lock+.001);
  assert(window.frame.hover.locked);assert.equal(window.frame.hover.row.x,1184);
  assert.equal(window.frame.hover.row.y,464);
  const strike=a.find(([t,age])=>age===4800)[0],i=window.MOTION_DATA.beats.beats_s.indexOf(strike);
  assert.equal(a.find(([t,age])=>age===4500)[0],window.MOTION_DATA.beats.beats_s[i-2]);
  assert.equal(a.find(([t,age])=>age===5300)[0],window.MOTION_DATA.beats.beats_s[i+2]);
});

test('new L4 scene retains raw values, fiscal period and unaudited regression labels',()=>{
  const {window,stage}=page(),shot=window.timeline.shots.find(s=>s.id==='v307-l4');
  window.seek(shot.start+.1);let html=plain(stage.innerHTML);
  assert.match(html,/META/);assert.match(html,/\$47\.5-50\.5 billion/);
  assert.match(html,/FY2025Q3/);assert.match(html,/Regression example/);assert.match(html,/furnished \/ unaudited/);
  const events=window.MOTION_DATA.cues._events[shot.id];
  window.seek(events.find(e=>e.event==='adobe').t+.01);html=plain(stage.innerHTML);
  assert.match(html,/Adobe/);assert.match(html,/non-GAAP/);assert.match(html,/\$5\.31/);
  window.seek(shot.end-.1);assert.match(plain(stage.innerHTML),/not future performance/);
});

for(const scene of ['screenshot','audio']) test(`${scene} shows its self-made input and recorded EPS contradiction`,()=>at(scene,(window,stage)=>{
  const html=plain(stage.innerHTML);assert.match(html,/Self-made test media/);
  assert.match(html,/1\.67/);assert.match(html,/\$1\.57/);
  assert.match(html,/FY2025 Q3/);
  if(scene==='audio') {assert.match(html,/speaker unverified/);assert.match(stage.innerHTML,/Waveform measured/);}
  else {assert.match(html,/CONTRADICTED/);assert.match(stage.innerHTML,/tests\/fixtures\/multimodal\/example-post.png/);}
}));

test('v007 original results and recall limits retain recorded corrections and evidence links',()=>{
  at('results',(window,stage)=>{
    for(const score of ['44.3%','83.2%','20.7%','90.5%','19.9%'])assert(stage.innerHTML.includes(score));
    assert.match(plain(stage.innerHTML),/includes dev \/ corrected gold/);
    assert(!/Pre-registered|92\.2|91\.0|85\.4/.test(stage.innerHTML));
  });
  at('limits',(window,stage)=>{
    const html=plain(stage.innerHTML);
    for(const label of ['Text control','Screenshot','Audio'])assert(html.includes(label));
    assert.equal(html.match(/CONTRADICTED/g).length,3);
    assert(!/INSUFFICIENT|missed/.test(html));
    assert.match(html,/Saved development probes/);assert.match(html,/not held out/);
    assert.match(html,/Speaker labels: unverified/);assert.match(html,/guarded \/ checked/);
    assert.match(html,/44\/60 live/);assert.match(html,/50\/60 frozen ASR/);
    for(const row of Object.values(window.MOTION_DATA.product.inputs))
      assert(stage.innerHTML.includes(`href="../../../${row.source}"`));
    for(const row of Object.values(window.MOTION_DATA.product.recall.coverage))
      assert(stage.innerHTML.includes(`href="../../../${row.source}"`));
  });
});

test('CTA remains visible on the last frame, with matching new QR and required credits',()=>{
  const {window,stage}=page();window.seek(window.timeline.duration);
  assert.match(plain(stage.innerHTML),/https:\/\/ hackathon\.dappgo\.com\//);
  assert.match(stage.innerHTML,/QR code for https:\/\/hackathon\.dappgo\.com\//);
  assert.match(plain(stage.innerHTML),/Built during the Meta Global AI Developer Hackathon/);
  assert.match(plain(stage.innerHTML),/Muse Spark · Meta open weights/);
  assert(!/github\.io|class="fade"/.test(stage.innerHTML));
});

test('no autonomous playback or network, and all CSS type constants are readable',()=>{
  const js=read('../motion/v3/motion.js'),css=read('../motion/v3/motion.css');
  assert(!/requestAnimationFrame|Date\.now|Math\.random|setInterval|setTimeout|fetch\(/.test(js));
  assert(!/\b(?:animation|transition)\s*:/.test(css));
  assert([...css.matchAll(/font-size:(\d+)px/g)].every(m=>+m[1]>=56));
  assert.match(read('../motion/v3/index.html'),/connect-src 'none'; media-src 'none'/);
  assert.equal(parseArgs(['--entry','v3/index.html','--t','2','--out','demo/out/check']).entry,'v3/index.html');
  assert.throws(()=>parseArgs(['--entry','https://example.com','--t','2','--out','demo/out/check']));
});

test('host geometry guard rejects clipping, small numbers and subtitle collisions',()=>{
  const good={text:[{text:'Claim',fontSize:64,left:64,right:1856,top:332,bottom:500,
    textLeft:64,textRight:600,textTop:332,textBottom:420}],numbers:[{text:'1.67',fontSize:112}]};
  assert.equal(assertV3Layout(good).subtitleTop,880);
  for(const change of [m=>m.text[0].textRight=1857,m=>m.text[0].textBottom=501,
                      m=>m.text[0].bottom=881,m=>m.text[0].fontSize=55,m=>m.numbers[0].fontSize=95,
                      m=>m.text.push({...m.text[0],text:'Overlapping label'})]) {
    const bad=structuredClone(good);change(bad);assert.throws(()=>assertV3Layout(bad));
  }
});
