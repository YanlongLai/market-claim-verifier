import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {parseArgs} from '../motion/render.mjs';
import {assertV3Layout} from '../motion/v3/layout-checks.mjs';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
const plain=html=>html.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ');
function page(search='',editData=()=>{}) {
  const stage={dataset:{},style:{},innerHTML:''};
  const context={document:{getElementById:()=>stage},URLSearchParams,location:{search}};
  context.window=context;context.globalThis=context;vm.createContext(context);
  for(const file of ['logic.js','v3/hover-source.js','v3/preview-data.js','v3/broll-data.js','v3/broll.js']) vm.runInContext(read('../motion/'+file),context);
  context.MOTION_DATA=context.MOTION_PREVIEW;
  editData(context.MOTION_DATA);
  vm.runInContext(read('../motion/v3/motion.js'),context);
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
      assert(box.y>=64&&box.y+box.h<=(box.realworld?816:880),box.text);
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

function encodedHolds(window,stage,start,end,identity) {
  const holds=[];
  for(let frame=Math.ceil(start*30);frame<Math.ceil(end*30);frame++) {
    window.seek(frame/30);
    const key=identity(window.frame,stage.innerHTML),last=holds.at(-1);
    if(last?.key===key)last.frames++;else holds.push({key,frames:1});
  }
  return holds;
}

test('Amazon, NVIDIA and opinion each hold for 75 encoded frames, including the reviewed early speech cue',()=>{
  for(const useReviewedCue of [false,true]) {
    const {window,stage}=page('',d=>{
      if(useReviewedCue)d.cues._events['v303-extract'][0].t=21.8176;
    }),shot=window.timeline.shots.find(s=>s.id==='v303-extract');
    const holds=encodedHolds(window,stage,shot.start,shot.end,(_,html)=>
      /AMZN/.test(html)?'Amazon':/opinion<\/div>/.test(html)?'Opinion':/NVDA/.test(html)?'NVIDIA':'Unexpected');
    assert.deepEqual(holds.map(h=>h.key),['Amazon','NVIDIA','Opinion']);
    for(const h of holds)assert(h.frames>=75,`${h.key}: ${h.frames}/30 s`);
    if(!useReviewedCue) {
      assert.deepEqual(holds.map(h=>h.frames),[75,77,138],'Approved v011 card holds changed');
      const event=window.MOTION_DATA.cues._events[shot.id][0],reveal=Math.ceil(event.t*30)/30;
      assert(event.cue_start>=reveal-.1,'Opinion speech precedes the card reveal');
      assert.equal(window.timeline.duration,177.2611);
    }
    window.seek(shot.start+4.9);assert(!/416\.2B/.test(stage.innerHTML),'Repeated Apple extraction card returns.');
    window.seek(shot.start+5);assert(!/AMZN/.test(stage.innerHTML));
  }
});

test('each real-world page holds at least 75 encoded frames in the unchanged 11.3081 s reserve',()=>{
  const {window,stage}=page(),shot=window.timeline.shots.find(s=>s.id==='v311b-realworld');
  assert(Math.abs(shot.end-shot.start-11.3081)<1e-8);
  const holds=encodedHolds(window,stage,shot.start,shot.end,(_,html)=>html.match(/data-realworld-page="(\d+)"/)[1]);
  assert.deepEqual(holds.map(h=>h.key),['0','1','2','3']);
  for(const h of holds)assert(h.frames>=75,`Real-world page ${h.key}: ${h.frames}/30 s`);
  const {window:overcrowded}=page('',d=>d.realworld.examples.push(structuredClone(d.realworld.examples[0])));
  assert.throws(()=>overcrowded.seek(shot.start),/at least 2.5 s/);
});

test('Hover uses real H assets, site pose clock, thruster and spotlight alphas',()=>{
  const {window,stage}=page(),a=window.MOTION_DATA.hover_anchors;
  for(const [t,age] of a.slice(0,-1)) {
    window.seek(t+.001);
    assert(Math.abs(window.frame.hover.siteAge-age)<10);
    if(!window.frame.broll)assert.match(stage.innerHTML,/docs\/site\/img\/auditor\/H\//);
  }
  window.seek(a.find(a=>a[1]===3700)[0]+.2);
  assert.equal(window.frame.hover.phase,'compare');
  assert.match(stage.innerHTML,/416\.2B/);assert.match(stage.innerHTML,/102\.5B/);
  assert(!/FALSE/.test(stage.innerHTML),'The verdict waits for the stamp');assert.match(stage.innerHTML,/Program compares/);
  assert(window.frame.hover.shade>0);assert.match(stage.innerHTML,/class="spotlight"/);
  assert(window.frame.hover.postAlpha>0&&window.frame.hover.filingAlpha>0&&window.frame.hover.yearAlpha>0);
  for(const name of ['filing','post','year'])assert(stage.innerHTML.includes(`data-beam="${name}"`));
  window.seek(a.find(a=>a[1]===4800)[0]+.01);
  assert.match(stage.innerHTML,/FALSE/);
  assert.equal(window.frame.hover.pose,'stamp-down');assert.equal(window.frame.hover.thruster,'burst');
  assert(window.frame.hover.dip>0);assert.match(stage.innerHTML,/Claim: FALSE/);
  const quarter=window.frame.boxes.find(b=>b.text==='$102.5B');
  assert.equal(quarter.className,'mint');
  assert.equal(window.frame.boxes.find(b=>b.text==='Filed quarter').className,'body mint');
});

test('Hover gates Claim: FALSE to the physical strike and holds the ratio for its later cue',()=>{
  // Exercise the new event contract with the committed preview as well as host data.
  let strike,ratio;
  const {window,stage}=page('',data=>{
    const events=data.cues._events['v304-hover'];
    strike=events.find(e=>e.event==='strike').t;
    ratio=data.beats.beats_s.find(b=>b>strike+1);
    data.cues._events['v304-hover']=events.filter(e=>e.event!=='ratio').concat({event:'ratio',t:ratio});
  });
  window.seek(strike-.001);assert(!/FALSE|≈4×/.test(stage.innerHTML));
  window.seek(strike+.01);
  assert.equal(window.frame.hover.pose,'stamp-down');assert(window.frame.hover.struck);
  assert.match(stage.innerHTML,/Claim: FALSE/);assert(!/≈4×/.test(stage.innerHTML));
  window.seek(ratio-.001);assert(!/≈4×/.test(stage.innerHTML));
  window.seek(ratio);assert.match(stage.innerHTML,/≈4×/);assert.match(stage.innerHTML,/Claim: FALSE/);
  window.seek(window.timeline.shots.find(s=>s.id==='v304-hover').end-.001);
  assert.match(stage.innerHTML,/≈4×/);assert.match(stage.innerHTML,/Claim: FALSE/);
});

test('Hover searches before locking the quarter and reserves detected beats around the strike',()=>{
  const {window}=page(),a=window.MOTION_DATA.hover_anchors,
    find=a.find(([t,age])=>age===2300)[0],lock=a.find(([t,age])=>age===2900)[0];
  const shot=window.timeline.shots.find(s=>s.id==='v304-hover'),
    cues=window.MOTION_DATA.cues._events[shot.id];
  assert(shot.voice_start>=shot.start+9);
  assert(find<shot.voice_start&&shot.voice_start<=lock);
  assert.equal(lock,cues.find(e=>e.event==='find').t);
  const opening=window.MOTION_DATA.keyframes.find(f=>f.shot===shot.id&&f.position==='opening');
  assert(find<opening.t&&opening.t<shot.voice_start);
  window.seek((find+shot.voice_start)/2);
  assert(window.frame.hover.finding&&!window.frame.hover.locked);
  window.seek(find+.001);const first=JSON.stringify(window.frame.hover.row);
  assert(window.frame.hover.finding&&!window.frame.hover.locked);
  window.seek((find+lock)/2);
  assert.notEqual(JSON.stringify(window.frame.hover.row),first);
  window.seek(lock+.001);
  assert(window.frame.hover.locked);assert.equal(window.frame.hover.row.x,1184);
  assert.equal(window.frame.hover.row.y,464);
  const strike=a.find(([t,age])=>age===4800)[0],i=window.MOTION_DATA.beats.beats_s.indexOf(strike);
  const compare=a.find(([t,age])=>age===3700)[0],beats=window.MOTION_DATA.beats.beats_s;
  assert.equal(a.find(([t,age])=>age===4500)[0],beats[Math.max(beats.indexOf(compare)+1,i-2)]);
  assert.equal(a.find(([t,age])=>age===5300)[0],window.MOTION_DATA.beats.beats_s[i+2]);
});

test('program audit separates the claim verdict from neutral E1 citations and filed evidence',()=>at('program',(window,stage)=>{
  const citations=window.frame.boxes.find(b=>b.text==='Citations: E1');
  assert(citations);assert(!citations.className.includes('coral'));
  assert(!/FALSE|CONTRADICTED/.test(citations.text));
  const badge=window.frame.boxes.find(b=>b.text==='Claim: FALSE');
  assert(badge&&badge.className.includes('status')&&badge.className.includes('coral'));
  assert.match(stage.innerHTML,/<span class="coral"><span class="number"[^>]*>\$416\.2B<\/span><\/span>/);
  assert.match(stage.innerHTML,/<span class="mint"><span class="number"[^>]*>\$102\.5B<\/span><\/span>/);
}));

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
  const correction=window.frame.boxes.find(b=>b.text.includes('→')&&b.text.includes('$1.57')),
    period=window.frame.boxes.find(b=>b.text.includes('FY2025 Q3'));
  assert(correction&&period&&correction.y+correction.h<=period.y);
  if(scene==='audio') {assert.match(html,/speaker unverified/);assert.match(stage.innerHTML,/Waveform measured/);}
  else {
    assert.match(html,/CONTRADICTED/);assert.match(stage.innerHTML,/tests\/fixtures\/multimodal\/example-post.png/);
    assert.match(stage.innerHTML,/class="abs source-crop"/);assert(!/source-thumb/.test(stage.innerHTML));
    assert.match(stage.innerHTML,/data-source-font-size="29" data-source-number="\$1\.67"/);
    assert.match(stage.innerHTML,/left:-976px;top:-1224px;width:4000px;height:2480px/);
    assert.match(html,/fiscal Q3 2025 · EPS source crop/);
  }
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
    assert.match(html,/44\/60 · full-media audio/);assert.match(html,/50\/60 · frozen-ASR text recheck/);
    const qualifier=window.frame.boxes.find(b=>b.text==='Post-hoc development probe · coverage ≠ verdict accuracy');
    assert(qualifier&&qualifier.size>=56&&qualifier.y+qualifier.h<=880);
    for(const label of ['Speaker labels: unverified','L4: regression test · not held out']) {
      const box=window.frame.boxes.find(b=>b.text===label);
      assert(box&&box.size>=56&&box.y+box.h<=880);
    }
    for(const row of Object.values(window.MOTION_DATA.product.inputs))
      assert(stage.innerHTML.includes(`href="../../../${row.source}"`));
    for(const row of Object.values(window.MOTION_DATA.product.recall.coverage))
      assert(stage.innerHTML.includes(`href="../../../${row.source}"`));
  });
});

test('CTA remains visible on the last frame, with matching new QR and required credits',()=>{
  const {window,stage}=page();window.seek(window.timeline.duration);
  assert.match(plain(stage.innerHTML),/Explore the saved demo/);
  assert.match(plain(stage.innerHTML),/https:\/\/hackathon\.dappgo\.com\//);
  const url=window.frame.boxes.find(b=>b.text==='https://hackathon.dappgo.com/');
  assert(url&&url.size>=56);assert(!/<br>/.test(stage.innerHTML));
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
    textLeft:64,textRight:600,textTop:332,textBottom:420}],numbers:[{text:'1.67',fontSize:112}],
    sourceCrops:[{text:'$1.67',fontSize:116,left:64,right:1856,top:420,bottom:612,
      imageLeft:-912,imageRight:3088,imageTop:-804,imageBottom:1676}]};
  assert.equal(assertV3Layout(good).subtitleTop,880);
  for(const change of [m=>m.text[0].textRight=1857,m=>m.text[0].textBottom=501,
                      m=>m.text[0].bottom=881,m=>m.text[0].fontSize=55,m=>m.numbers[0].fontSize=95,
                      m=>m.text.push({...m.text[0],text:'Overlapping label'}),
                      m=>m.sourceCrops[0].fontSize=95,m=>m.sourceCrops[0].fontSize=Infinity,
                      m=>m.sourceCrops[0].bottom=881,
                      m=>m.sourceCrops[0].imageLeft=65]) {
    const bad=structuredClone(good);change(bad);assert.throws(()=>assertV3Layout(bad));
  }
});

test('all five B-roll inserts select each native frame identically in forward and reverse order',()=>{
  const {window,stage}=page(),B=window.BrollLayer,D=window.MOTION_DATA,
    windows=B.windows(D);
  assert.equal(windows.length,5);
  for(const clip of windows) {
    assert(D.beats.beats_s.includes(clip.start));assert(D.beats.beats_s.includes(clip.end));
    assert.equal(clip.play_end-clip.start,45/16);
    assert(clip.end<=D.timing.shots.find(s=>s.id===clip.shot).end);
    const expected=[];
    for(let index=0;index<45;index++) {
      const t=clip.start+(index+.5)/16;
      window.seek(t);
      assert.equal(window.frame.broll.frameIndex,index);
      assert.match(window.frame.broll.src,new RegExp(`frame-${String(index).padStart(4,'0')}\\.png$`));
      expected.push([stage.innerHTML,JSON.stringify(window.frame)]);
    }
    for(let index=44;index>=0;index--) {
      window.seek(100);window.seek(clip.start+(index+.5)/16);
      assert.deepEqual([stage.innerHTML,JSON.stringify(window.frame)],expected[index]);
    }
    window.seek(clip.start);assert.equal(window.frame.broll.frameIndex,0);
    for(let index=1;index<45;index++) {
      window.seek(clip.start+index/16);assert.equal(window.frame.broll.frameIndex,index);
    }
    window.seek(clip.play_end);assert.equal(window.frame.broll.frameIndex,44);
    window.seek(clip.end-1e-8);assert.equal(window.frame.broll.frameIndex,44);
    window.seek(clip.end);assert.equal(window.frame.broll,null);
    if(clip.start>0){window.seek(clip.start-1e-8);assert.equal(window.frame.broll,null);}
  }
  assert.throws(()=>B.select(D,NaN),/finite/);
  assert.throws(()=>B.select(D,Infinity),/finite/);
  assert(!/<video|<canvas/.test(stage.innerHTML));
  const point=windows.find(c=>c.id==='point-glow-s29');
  assert(point.end<=D.timing.shots.find(s=>s.id===point.shot).voice_start);
});

test('B-roll and product remain disjoint above captions at every film frame; product appears before 3 s',()=>{
  const {window,stage}=page();let inserts=0;
  for(let i=0;i<Math.ceil(window.timeline.duration*30);i++) {
    window.seek(i/30);const frame=window.frame,b=frame.broll?.rect;
    if(i<=90) {
      assert.match(stage.innerHTML,/416\.2B/);assert.match(stage.innerHTML,/Open saved check/);
      assert.match(plain(stage.innerHTML),/Market Claim Verifier/);
    }
    if(!b)continue;
    inserts++;
    assert(b.x>=64&&b.y>=64&&b.x+b.w<=1856&&b.y+b.h<=880);
    assert(b.w>=560&&b.w<=640&&b.h===b.w);
    assert(frame.broll.frameIndex>=0&&frame.broll.frameIndex<45);
    const panel=stage.innerHTML.match(/<div class="broll-panel"[^>]*>(.*?)<\/div>/)[1];
    assert.equal(plain(panel).trim(),'');assert.match(panel,/<img /);
    for(const box of frame.boxes) {
      const overlapX=Math.min(b.x+b.w,box.x+box.w)-Math.max(b.x,box.x),
        overlapY=Math.min(b.y+b.h,box.y+box.h)-Math.max(b.y,box.y);
      assert(overlapX<=0||overlapY<=0,box.text);
    }
  }
  assert(inserts>300);
});

test('B-roll is recomputed from shifted scene/cue times and refuses invalid host windows',()=>{
  const {window}=page(),B=window.BrollLayer,D=window.MOTION_DATA,
    first=B.windows(D).find(c=>c.id==='stamp-press-s29');
  const changed=structuredClone(D),shot=changed.timing.shots.find(s=>s.id===first.shot);
  changed.cues._events[shot.id].find(e=>e.event==='verdict').t=shot.start+3;
  const shifted=B.windows(changed).find(c=>c.id===first.id);
  assert(shifted.start<first.start);
  shot.end=shot.start+2;
  assert.throws(()=>B.windows(changed),/cannot fit/);
  const broken=structuredClone(D);
  broken.cues._events[first.shot]=[];
  assert.throws(()=>B.windows(broken),/Missing B-roll cue/);
  const early=structuredClone(D);
  const earlyHover=early.timing.shots.find(s=>s.id==='v304-hover');
  earlyHover.voice_start=earlyHover.start+1;
  assert.throws(()=>B.windows(early),/narration lead/);
});

test('L4 insert uses the contained approved point-glow PNGs at every source-frame index',()=>{
  const {window}=page(),D=window.MOTION_DATA,B=window.BrollLayer;
  const insert=B.windows(D).find(c=>c.shot==='v307-l4'),approved=window.BROLL_DATA.clips.find(c=>c.id==='point-glow-s29');
  assert.equal(insert.asset_id,'point-glow-s29');
  assert.equal(insert.source_sha256,approved.source_sha256);
  assert.equal(insert.receipt_sha256,approved.receipt_sha256);
  for(let frame=0;frame<45;frame++) {
    const chosen=B.select(D,insert.start+(frame+.5)/16);
    assert(chosen.src.includes('/point-glow-s29/'));
    assert(!chosen.src.includes('/turn-point-s11/'));
    assert.equal(chosen.frameIndex,frame);
  }
});

test('v010 pending real-world reserve is honest, silent and deterministic',()=>{
  const {window,stage}=page('',d=>{
    d.realworld={status:'awaiting_evidence',sources:[],examples:[],narration:null,provenance:{}};
    d.cues['v311b-realworld']=[];
  }),D=window.MOTION_DATA,
    shot=D.timing.shots.find(s=>s.id==='v311b-realworld');
  assert.equal(D.timing.shots.length,13);assert.equal(D.timing.duration,177.2611);
  assert(Math.abs(shot.end-shot.start-11.3081)<1e-7);
  assert.equal(D.realworld.status,'awaiting_evidence');
  assert.equal(D.cues[shot.id].length,0);
  for(const t of [shot.start,shot.end-.001,shot.start+5,shot.start]) {
    window.seek(t);
    assert.match(stage.innerHTML,/Evidence pending/);
    assert.match(stage.innerHTML,/No recorded results yet/);
    assert(!/p50|cost.per.item|tested ·|@/.test(stage.innerHTML));
  }
});

function syntheticWorld() {
  const sources=['news','threads'].map(id=>({id,label:id==='news'?'DappGo News':'Threads',
    items_tested:3,items_checked:2,items_with_errors:1,coverage_percent:66.7,
    verdict_counts:{supported:0,contradicted:1,insufficient_evidence:1},
    cost_per_item_usd:.03,p50_latency_s:3}));
  const primary={check_index:0,claim_type:'value',verdict:'contradicted',value:10,stated_value:12.5,unit:'USD',
    period:'FY2025',metric:'revenue',source_label:'10-K',source_tier:'L1',evidence_ids:['E1'],
    gap:{gap_kind:'relative',gap:.25}};
  return {status:'ready',runs:[{id:'synthetic-original',phase:'original',provider:'baseten',path:'post',sources},
    {id:'synthetic-fix',phase:'posthoc_frozen_text_recheck',provider:'baseten',path:'post',sources:[sources[1]]}],
    examples:[{run_id:'synthetic-original',source_id:'news',report:'synthetic-report.json',handle:null,paraphrase:'Synthetic news paraphrase.',
      verdict:'supported',primary,comparisons:[]},
      {run_id:'synthetic-original',source_id:'threads',report:'synthetic-report.json',handle:'@synthetic_user',paraphrase:'Synthetic: 12.5 claimed; source says 10.',
        verdict:'contradicted',primary,comparisons:[]}]};
}

test('compiled-source renderer covers metrics, handles and separately labeled rechecks within the reserve',()=>{
  const {window,stage}=page('',d=>d.realworld=syntheticWorld()),
    shot=window.timeline.shots.find(s=>s.id==='v311b-realworld'),seen=new Set();
  const expected=[];
  for(let i=0;i<Math.ceil((shot.end-shot.start)*30);i++) {
    const t=Math.min(shot.end-.00001,shot.start+i/30);window.seek(t);
    const text=plain(stage.innerHTML);
    assert.match(text,/Baseten · post route/);
    assert.match(text,/coverage ≠ accuracy/i);
    assert(!/p50|\/item| errors/.test(text),'Receipt detail belongs in linked evidence.');
    const badge=window.frame.boxes.find(b=>b.className.includes('claim-verdict'));
    const colors={SUPPORTED:'mint',CONTRADICTED:'coral',INSUFFICIENT:'amber'};
    if(badge) {
      assert(badge.className.includes(colors[badge.text]));
      for(const label of ['$12.5','$10','SEC 10-K · FY2025'])assert(text.includes(label));
      assert(!/Supported|Insufficient|failed runs/.test(text),'Example must have one comparison.');
    } else {
      assert.match(text,/2\/3 items checked \(66\.7%\)/);assert.match(text,/1 failed runs/);
      for(const label of ['Supported','Contradicted','Insufficient','verdict counts'])assert(text.includes(label));
    }
    assert(!/https?:\/\/|threads\.(net|com)\//.test(stage.innerHTML));
    if(/DappGo News/.test(text))seen.add('news');
    if(/Threads/.test(text))seen.add('threads');
    if(/Post-hoc · frozen text/.test(text)) {
      seen.add('recheck');assert.match(text,/OCR\/ASR not retested/);
    }
    for(const box of window.frame.boxes) {
      assert(box.x>=64&&box.x+box.w<=1856);
      assert(box.y>=64&&box.y+box.h<=816);
      assert(box.size>=56,box.text);
    }
    expected.push([t,stage.innerHTML]);
  }
  assert.deepEqual([...seen].sort(),['news','recheck','threads']);
  assert(expected.some(([,html])=>html.includes('@synthetic_user')));
  for(const [t,html] of expected.reverse()) {
    window.seek(0);window.seek(t);assert.equal(stage.innerHTML,html);
  }
});

test('recorded examples give one large comparison; original and post-hoc aggregates keep counts distinct',()=>{
  const {window,stage}=page(),D=window.MOTION_DATA,
    shot=window.timeline.shots.find(s=>s.id==='v311b-realworld');
  const expected=[
    ['@taiwandata · paraphrase of post','CoreWeave','$2.29B','$229M','SEC 10-K · FY2023','Annual revenue'],
    ['@sky311091 · paraphrase of post','SanDisk','23%','377.9%','SEC 10-Q · FY2027Q1','Recorded YoY revenue growth']];
  for(const [i,texts] of expected.entries()) {
    const frame=D.keyframes.find(f=>f.position==='realworld-page-'+(i+2));
    window.seek(frame.t);
    const text=plain(stage.innerHTML).replace(/&#39;/g,"'");
    for(const value of texts)assert(text.includes(value),value);
    assert.match(stage.innerHTML,/class="abs claim-verdict coral"/);
    assert.match(text,/CONTRADICTED/);
    assert.match(text,/Saved original · coverage ≠ accuracy/);
    assert(!/items checked|failed runs|Supported|Insufficient|\$11\.0|354\.9/.test(text));
    assert.equal([...stage.innerHTML.matchAll(/class="number"/g)].length,2);
    assert(stage.innerHTML.includes(`href="../../../${D.realworld.examples[i].report}"`));
    const badge=window.frame.boxes.find(b=>b.className.includes('claim-verdict'));
    assert(badge.size>=56&&badge.w>=700&&badge.h>=96);
    for(const b of window.frame.boxes)assert(b.size>=56&&b.y+b.h<=816,b.text);
  }
  for(const page of [1,4]) {
    window.seek(D.keyframes.find(f=>f.position==='realworld-page-'+page).t);
    assert.match(stage.innerHTML,/Coverage ≠ accuracy/);
    assert.match(stage.innerHTML,/Baseten · post route/);
    assert.match(stage.innerHTML,/verdict counts are claims/);
    assert(!stage.innerHTML.includes('claim-verdict'));
    if(page===4) {
      for(const label of ['Post-hoc · frozen text','43/80 items checked (53.8%)','0 failed runs',
        'OCR/ASR not retested','Previously seen inputs'])assert(stage.innerHTML.includes(label));
    } else {
      for(const label of ['DappGo News','Threads','44/80 items checked (55.0%)',
        '42/78 items checked (53.8%)','0 failed runs','6 failed runs'])assert(stage.innerHTML.includes(label));
    }
    const labels=window.frame.boxes.filter(b=>b.className.includes('aggregate-label'));
    for(const label of ['Supported','Contradicted','Insufficient'])assert(labels.some(b=>b.text===label));
    assert(labels.some(b=>b.text.includes('failed runs')));
    for(const b of labels) {
      assert(b.size>=56,`${b.text}: ${b.size} px; minimum 56 px`);
      assert(b.h>=b.size*1.2,`${b.text}: line box is too short`);
      assert(b.x>=64&&b.x+b.w<=1856&&b.y+b.h<=816,b.text);
    }
  }
  assert(shot.end-shot.start<12);
});

test('comparison values come from recorded checks rather than the paraphrase or a new calculation',()=>{
  const {window,stage}=page('',d=>{
    d.realworld=syntheticWorld();
    Object.assign(d.realworld.examples[1].primary,{stated_value:9876,value:1234});
  });
  const shot=window.timeline.shots.find(s=>s.id==='v311b-realworld');
  window.seek((shot.start+shot.end)/2);
  assert.match(plain(stage.innerHTML),/\$9\.876K/);
  assert.match(plain(stage.innerHTML),/\$1\.234K/);
});

test('real-world geometry guard enforces 56px labels without aggregate exceptions and 96px values',()=>{
  const good={text:[{text:'SEC 10-K · FY2023',realworld:true,fontSize:56,
    left:944,right:1824,top:404,bottom:472,textLeft:944,textRight:1500,textTop:404,textBottom:471}],numbers:[]};
  assertV3Layout(good);
  for(const change of [m=>m.text[0].fontSize=55,m=>m.text[0].bottom=817,
    m=>m.text[0].textRight=1825,m=>m.text[0].textBottom=473,
    m=>{m.text[0].fontSize=95;m.text[0].exampleValue=true;}]) {
    const bad=structuredClone(good);change(bad);assert.throws(()=>assertV3Layout(bad));
  }
  const aggregate=structuredClone(good);Object.assign(aggregate.text[0],{aggregateLabel:true,fontSize:56});
  assertV3Layout(aggregate);
  for(const fontSize of [48,55]) {
    aggregate.text[0].fontSize=fontSize;assert.throws(()=>assertV3Layout(aggregate),/minimum 56 px/);
  }
});

test('Apple ribbon animates recorded steps and fact IDs during the existing lead with seek-stable cost/latency',()=>{
  const {window,stage}=page(),D=window.MOTION_DATA,T=D.agent_trace,
    shot=D.timing.shots.find(s=>s.id==='v304-hover'),
    start=window.BrollLayer.windows(D).find(c=>c.id==='point-glow-s29').end,end=shot.voice_start;
  assert(start<end&&end-shot.start>=9);
  const samples=T.steps.map(step=>start+(step.start_s+step.latency_s*.5)/T.latency_s*(end-2.5-start));
  const expected=samples.map((t,i)=>{
    window.seek(t);const step=T.steps[i],state=window.frame.hover.trace;
    assert.equal(window.frame.broll,null);
    assert.equal(state.index,step.index);assert.equal(state.name,step.name);
    assert.deepEqual(Array.from(state.fact_ids),Array.from(step.fact_ids));
    assert(stage.innerHTML.includes(step.name));assert.match(stage.innerHTML,/E1/);
    assert.match(stage.innerHTML,/class="trace-fill"/);
    assert(stage.innerHTML.includes('Saved trace · recorded 8.080 s, compressed'));
    assert(!stage.innerHTML.includes('Step ~$'));
    for(const b of window.frame.boxes.filter(b=>/trace-/.test(b.className))) {
      assert(b.x>=64&&b.x+b.w<=1856&&b.y>=150&&b.y+b.h<=332);
      if(b.text)assert(b.h>=b.size*1.2);
    }
    return [stage.innerHTML,JSON.stringify(window.frame)];
  });
  for(let i=samples.length-1;i>=0;i--) {
    window.seek(shot.end-.001);window.seek(samples[i]);
    assert.deepEqual([stage.innerHTML,JSON.stringify(window.frame)],expected[i]);
  }
  window.seek(end);assert.equal(window.frame.hover.trace,null);
  assert.equal(window.timeline.duration,177.2611);
});

test('Apple trace label is fixed throughout and final run receipt holds at least 75 encoded frames',()=>{
  const {window,stage}=page(),D=window.MOTION_DATA,shot=D.timing.shots.find(s=>s.id==='v304-hover'),
    start=window.BrollLayer.windows(D).find(c=>c.id==='point-glow-s29').end;
  const holds=encodedHolds(window,stage,start,shot.voice_start,(frame,html)=>{
    assert(html.includes('Saved trace · recorded 8.080 s, compressed'));
    if(frame.hover.trace.receipt) {
      assert(html.includes('Run ~$'+D.agent_trace.cost_usd.toFixed(5)));
      assert(html.includes('3 requests · E1'));
    }
    return frame.hover.trace.receipt?'receipt':'steps';
  });
  assert.deepEqual(holds.map(h=>h.key),['steps','receipt']);
  assert(holds.at(-1).frames>=75,`Receipt: ${holds.at(-1).frames}/30 s`);
  for(const frame of D.keyframes.filter(f=>f.position.startsWith('recorded-trace-'))) {
    window.seek(frame.t);
    if(frame.position==='recorded-trace-receipt')assert(window.frame.hover.trace.receipt);
    else assert.equal(window.frame.hover.trace.index,Number(frame.position.at(-1)));
  }
});

test('host B-roll guard rejects text occlusion, subtitle incursions and wrong decoded PNGs',()=>{
  const metrics={text:[{text:'Product',fontSize:64,left:704,right:1856,top:332,bottom:500,
    textLeft:704,textRight:1200,textTop:332,textBottom:420}],numbers:[],
    broll:[{left:64,right:664,top:256,bottom:856,width:600,height:600,naturalWidth:480,naturalHeight:480,text:''}]};
  assertV3Layout(metrics);
  for(const change of [m=>m.broll[0].bottom=881,m=>m.broll[0].right=900,
    m=>m.broll[0].width=1920,m=>m.broll[0].height=560,m=>m.broll[0].naturalWidth=0,
    m=>m.broll[0].text='Text inside clip']) {
    const bad=structuredClone(metrics);change(bad);assert.throws(()=>assertV3Layout(bad));
  }
});
