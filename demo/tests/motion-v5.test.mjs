import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {stateAt,boundaries,chapterState,repostCascade,overlayAt,terminalAt,outroStampAt} from '../motion/v5/plan.js';
import {labelPositions} from '../motion/v5/chapters.js';
import {assertNamedClearance,checkV5Layout} from '../motion/v5/layout-checks.mjs';
import {installCaptureDOM,validateGeometry,hasCJK,presentation,showTraceAndFiling,validateLiveResult,redact,endingExpectedLinks,coverDocument,captureCoverCSS,revealCaptureDOM,namedSelectors} from '../record_v5.mjs';
import {parseArgs} from '../motion/render.mjs';
const ctx={window:{}};vm.runInNewContext(readFileSync(new URL('../motion/v5/data.js',import.meta.url),'utf8'),ctx);
const data=JSON.parse(JSON.stringify(ctx.window.MOTION_DATA)),scenes=data.scenes,segments=data.chapter_bar.segments;
const state=t=>stateAt(t,scenes,segments);
test('ten binding cuts, full-frame live playback, 178-second film',()=>{
 assert.deepEqual(boundaries,[0,8,20,32,46,58,116,138,154,170,178]);
 boundaries.slice(0,-1).forEach((t,i)=>assert.equal(state(t).shot,`v50${i}`));
 assert.equal(state(178).shot,'v509');assert.equal(state(178).fade,0);
 assert.throws(()=>state(NaN));assert.throws(()=>state(178.001));
 for(const t of [58,89,115.99,154,169.99])assert.deepEqual(state(t).liveTake,{scale:1,x:0,y:0});
 assert.equal(parseArgs(['--entry','v5/index.html','--t','100','--out','/tmp/v5']).entry,'v5/index.html');
});
test('seven live overlays change exactly at their receipt phase, never early',()=>{
 const events=scenes[5].cue_events;assert.equal(events.length,7);
 assert.equal(overlayAt(0,events),null);
 for(const [i,e] of events.entries()){
  assert.equal(state(58+e.at_scene_s).overlay.event,e.event);
  assert.equal(state(58+e.at_scene_s-1/300).overlay?.event,i?events[i-1].event:undefined);
  const cue=data.cues._events.v505.find(c=>c.event===e.event);assert.equal(cue.t,58+e.at_scene_s);assert.equal(cue.cue_start,cue.t);
 }
 assert.deepEqual(events.map(e=>e.receipt_phase),['use_apple_example','check_against_sec','verdict_reveal','draft_reveal','evidence_reveal','agent_trace_expand','hover_receipt']);
});
test('duration-weighted chapter fill is exact on every film frame',()=>{
 for(let frame=0;frame<=178*30;frame++){
  const t=frame/30,chapters=chapterState(t,segments);
  assert(Math.abs(chapters.reduce((n,c)=>n+c.width,0)-100)<1e-9);
  assert(Math.abs(chapters.reduce((n,c)=>n+c.fill*c.duration_s,0)-t)<1e-8);
  assert.equal(chapters.filter(c=>c.current).length,1);assert(chapters[state(t).index].current);
 }
});
test('cascade duplicates seven real HTML cards and settles without counters',()=>{
 assert.equal(repostCascade(0).length,7);
 assert(repostCascade(2)[6].x<repostCascade(8)[6].x);
 assert.deepEqual(repostCascade(9),repostCascade(11.9));
 assert(state(8).cascade.every(c=>c.opacity===0));
 const app=readFileSync(new URL('../motion/v5/app.js',import.meta.url),'utf8');
 assert(app.includes('class="post-card"'));assert(!app.includes('reposts'));
 assert(!app.includes('.png\'')&&!app.includes('broll'));
});
test('all four real input tiles are present together after the entrance',()=>{
 assert.equal(data.inputs.length,4);assert.deepEqual(state(31).inputs,[1,1,1,1]);
 assert.equal(data.inputs[1].preview,'demo/assets/examples-v5/a-pdf-page1.png');
 assert.equal(data.inputs[2].source,'a.mp3');assert.equal(data.inputs[3].preview,'demo/assets/examples-v5/a-video-frame.png');
});
test('batch narration changes at the recut terminal block boundaries',()=>{
 for(const [time,event] of [[116,'run'],[121,'ocr'],[124,'asr'],[127,'median'],[131.5,'projection']])assert.equal(state(time).terminal.event,event);
 assert.equal(state(138).terminal,null);
});
test('capture geometry requires >=1500 pixels and equal >=60-pixel margins',()=>{
 assert.equal(presentation.css_zoom,1.95);assert.equal(presentation.column_css_px*presentation.css_zoom,1560);
 const valid={source_width:1560,left_margin:180,right_margin:180,horizontal_overflow:0};validateGeometry(valid);
 for(const bad of [{source_width:1499},{left_margin:185},{right_margin:59},{horizontal_overflow:2},{source_width:NaN},{left_margin:undefined}])assert.throws(()=>validateGeometry({...valid,...bad}));
});
function domFixture(){
 const nodes=[{textContent:'DappGo · English',parentElement:{tagName:'P'}},{textContent:'\u4e2d\u6587',parentElement:{tagName:'P'}},{textContent:'\ud840\udc00',parentElement:{tagName:'SPAN'}}];
 const attributes={title:'\u65e5\u672c',alt:'English image'};
 const el={getAttribute:k=>attributes[k]||null,removeAttribute:k=>delete attributes[k]};
 let switches=[{remove(){switches=[];}}],mutation;
 const document={querySelectorAll:s=>s==='.language-switch'?switches:s==='*'?[el]:[],createTreeWalker:()=>{let i=0;return {nextNode:()=>nodes[i++]};},addEventListener:()=>{}};
 const context={document,window:{},NodeFilter:{SHOW_TEXT:4},MutationObserver:class{constructor(callback){mutation=callback;}observe(){}}};
 vm.runInNewContext(`(${installCaptureDOM.toString()})(${JSON.stringify({presentation,captureCSS:''})})`,context);
 return {context,nodes,attributes,mutate:()=>mutation()};
}
test('capture DOM sanitizer removes language switch, Han nodes and rendered attributes',()=>{
 const dom=domFixture();const result=dom.context.window.captureLanguageScan();
 assert.equal(result.text_nodes,0);assert.equal(result.attributes,0);assert.equal(result.language_switches,0);
 assert.equal(dom.nodes[0].textContent,'DappGo · English');assert.equal(dom.nodes[1].textContent,'');assert.equal(dom.nodes[2].textContent,'');assert.equal(dom.attributes.alt,'English image');assert.equal(dom.attributes.title,undefined);
 dom.nodes[1].textContent='\ud55c\uae00';dom.mutate();assert.equal(dom.nodes[1].textContent,'');
 for(const text of ['\u4e2d','\u3042','\u30ab','\ud55c','\ud840\udc00'])assert(hasCJK(text));
 assert.equal(hasCJK('Meta Muse Spark · Baseten → SEC'),false);
});
function traceFixture(){
 const actions=[],report={},open={trace:false,inspect:false};
 const fact={ticker:'AAPL',derived:true,evidence_id:'E3',derivation:'FY2025 - 9M YTD',value:102466000000,components:[{value:416161000000},{value:313695000000}]};
 const result={evidence:[fact],events:[{kind:'tool_call',name:'a'},{kind:'tool_call',name:'b'},{kind:'tool_call',name:'c'},{kind:'tool_call',name:'d'},{kind:'verdict'}]};
 const pre={id:'pre',innerText:async()=>JSON.stringify(fact),evaluate:async()=>300};
 const details={evaluate:async()=>open.inspect,locator:()=>pre};
 const steps={nth:index=>({id:`step-${index}`,isVisible:async()=>open.trace,evaluate:async()=>[180,80,1740,520]})};
 const page={locator:s=>s.endsWith('.live-trace')?{evaluate:async()=>open.trace}:s.endsWith('.trace-step')?steps:{nth:()=>({locator:()=>details})}};
 return {page,result,report,mark:s=>actions.push(s),frame:async()=>{},click:async s=>{if(s.includes('live-trace'))open.trace=true;else open.inspect=true;},hold:async()=>{},actions};
}
test('recorder retains trace expansion, four visible tool calls, program verdict and Apple inspector',async()=>{
 const f=traceFixture();await showTraceAndFiling(f);
 assert.equal(f.report.tool_calls_shown,4);assert.equal(f.report.program_verdict_shown,true);assert.equal(f.report.apple_inspect_open,true);assert.equal(f.report.trace_details_open,true);
 assert.equal(f.report.apple_derivation.quarter,102466000000);
 assert(f.actions.includes('agent_trace_expand'));
});
test('live result contract and redaction are preserved',()=>{
 const result={mode:'live',provider:'baseten',model:'meta-models/muse-spark-open-1026',verdict:'contradicted',cost_usd:.01,latency_ms:6000,corrections:{edits:[{original:'$416.2 billion',replacement:'$102.5 billion'}]},events:[{kind:'tool_call'}],evidence:[{filing_url:'https://www.sec.gov/Archives/example'}]};
 validateLiveResult(result);assert.throws(()=>validateLiveResult({...result,mode:'saved'}));
 assert.deepEqual(redact({cost_usd:.01,password:'secret',balance:9,items:['keep','secret']},'secret'),{cost_usd:.01,items:['keep','[REDACTED]']});
});

test('ending validates the two correction citations from the actual response envelope',()=>{
 const result={corrections:{edits:[{original:'$416.2 billion',replacement:'$102.5 billion',citations:[{form:'10-K',url:'https://www.sec.gov/Archives/annual/'},{form:'10-Q',url:'https://www.sec.gov/Archives/nine-months/'}]}]}};
 assert.deepEqual(endingExpectedLinks(result),['https://www.sec.gov/Archives/annual/','https://www.sec.gov/Archives/nine-months/']);
 result.corrections.edits[0].citations.pop();assert.throws(()=>endingExpectedLinks(result));
});

test('first document bytes hide the page until an audited zoomed layout is installed',()=>{
 const html=coverDocument('<html><head><script>site()</script></head><body>Product page</body></html>');
 assert(html.indexOf('capture-boot-cover')<html.indexOf('<script>'));
 assert(html.includes(`>${captureCoverCSS}</style>`));assert.throws(()=>coverDocument('<body>page</body>'));
 const document={documentElement:{style:{zoom:'1.95'},dataset:{}},body:{},querySelector:()=>({})};
 const fixture={document,getComputedStyle:(_el,pseudo)=>pseudo?{backgroundColor:'rgb(247, 245, 239)',visibility:'visible',display:'block'}:{visibility:'hidden'}};
 vm.runInNewContext(`(${revealCaptureDOM.toString()})()`,fixture);
 assert.equal(document.documentElement.dataset.captureReady,'true');
 document.documentElement.style.zoom='1';delete document.documentElement.dataset.captureReady;
 assert.throws(()=>vm.runInNewContext(`(${revealCaptureDOM.toString()})()`,fixture));
 assert.equal(document.documentElement.dataset.captureReady,undefined);
 document.documentElement.style.zoom='1.95';document.querySelector=()=>null;
 assert.throws(()=>vm.runInNewContext(`(${revealCaptureDOM.toString()})()`,fixture));
});

test('all chapter labels keep 24 px on either side, including Results / Fix / DappGo',()=>{
 assert.deepEqual(segments.slice(-3).map(s=>s.label),['Results','Fix','DappGo']);
 const widths=[78,74,101,68,73,65,96,124,49,132],centres=labelPositions(segments,widths);
 for(let i=0;i<centres.length;i++){
  assert(centres[i]-widths[i]/2>=24);assert(centres[i]+widths[i]/2<=1896);
  if(i)assert(centres[i]-widths[i]/2-(centres[i-1]+widths[i-1]/2)>=48);
 }
 assert.throws(()=>labelPositions(segments,Array(10).fill(190)));
});

test('rendered on_screen nodes equal their storyboard strings, including changed copy',()=>{
 const stage={innerHTML:'',querySelector:()=>null,querySelectorAll:()=>[]};
 const element=()=>({style:{},getBoundingClientRect:()=>({width:100}),classList:{toggle(){}},querySelector:()=>({style:{}})});
 const context={window:{MOTION_DATA:structuredClone(data)},document:{querySelector:s=>s==='#stage'?stage:s==='#chapter-layer'?{}:s.startsWith('[data-')||s.startsWith('#node-')||s.startsWith('#link-')?element():null}};
 vm.runInNewContext(readFileSync(new URL('../motion/v5/bundle.js',import.meta.url),'utf8')+'\nglobalThis.sceneBody=body;',context);
 const decode=s=>s.replaceAll('&lt;','<').replaceAll('&gt;','>').replaceAll('&quot;','"').replaceAll('&amp;','&');
 let count=0;
 for(let i=0;i<10;i++){
  const html=context.sceneBody(stateAt(boundaries[i],scenes,segments));
  for(const match of html.matchAll(/<[^>]+data-on-screen="(v50\d)"[^>]*>([^<]*)<\//g)){
   assert.equal(decode(match[2]),scenes.find(s=>s.id===match[1]).on_screen);count++;
  }
 }
 assert.equal(count,2);
 context.window.MOTION_DATA.scenes[0].on_screen='Changed & exact <storyboard> copy.';
 assert(context.sceneBody(state(0)).includes('Changed &amp; exact &lt;storyboard&gt; copy.'));
 assert(!context.sceneBody(state(170)).includes('disclosure'));
});

test('every frame of the batch run shows saved CoreWeave verdicts and no failure panel',()=>{
 for(let f=0;f<5*30;f++){
  const picture=terminalAt(f/30,data.terminal_replays.beat6),text=picture.rows.map(r=>r.text).join('\n');
  assert.equal(picture.block,'run');assert(text.includes('FY2024 · SUPPORTED'));assert(text.includes('$51.31B → $5.131B'));assert(text.includes('FY2023 · CONTRADICTED'));
  assert(!/FAILED|INSUFFICIENT|UNCHECKED/.test(text));assert(picture.rows.every(r=>r.row!==12));
 }
 assert(terminalAt(4.99,data.terminal_replays.beat6).rows.some(r=>r.text==='$2.29B → $229M'));
 assert.equal(terminalAt(5,data.terminal_replays.beat6).block,'ocr');
});

test('overlay audit rejects any intersection with named evidence, verdict, correction, trace or receipt',()=>{
 const overlay={left:80,right:1840,top:558,bottom:784};
 for(const name of ['verdict','corrected number','SEC evidence row','trace tool call','receipt']){
  const check={phase:name,elements:[{name,left:180,right:1000,top:80,bottom:548}]};
  assertNamedClearance([overlay],[check]);check.elements[0].bottom=560;
  assert.throws(()=>assertNamedClearance([overlay],[check]),/covers/);
 }
 assert(namedSelectors('tool_call_4_reveal',{}).some(s=>s[2]===3));
 assert(namedSelectors('evidence_reveal',{evidence:[{ticker:'AAPL',derived:true}]}).some(s=>s[1].includes('nth-child(1)')));
});

test('outro uses the site stamp / stamp-down / approve poses and settles within 1.6 s',()=>{
 assert.equal(outroStampAt(0).pose,'stamp');assert.equal(outroStampAt(.3).pose,'stamp-down');assert.equal(outroStampAt(.8).pose,'approve');
 assert(outroStampAt(.36).dip>outroStampAt(.6).dip);assert.equal(outroStampAt(1.6).settled,true);
 assert.deepEqual(outroStampAt(1.6),outroStampAt(7));
 assert(Object.values(data.brand_motion.poses).every(p=>p.startsWith('docs/site/img/auditor/H/')));
});

test('actual-frame audit rejects a translucent band, cramped labels and scene text in the rail lane',async()=>{
 const current=state(116),widths=Array(10).fill(90),centres=labelPositions(segments,widths);
 const actual={cjk:false,inserts:0,bar:{height:12,width:1920,top:844},band:{left:0,right:1920,top:790,bottom:1080,colour:'rgb(17, 26, 32)',opacity:'1'},
  labels:centres.map((c,i)=>({font:32,left:c-45,right:c+45,bottom:834,current:i===6})),
  segments:current.chapters.map(s=>({width:1920*s.duration_s/178,fill:s.fill})),onScreen:[],
  textBoxes:[{text:'Saved replay',bottom:748}],terminalCaption:{font:56,bottom:748},namedChecks:[],overlay:null,video:null};
 await checkV5Layout({evaluate:async()=>actual},current);
 await assert.rejects(()=>checkV5Layout({evaluate:async()=>({...actual,captureVersion:6})},state(58)),/v7 take/);
 for(const mutate of [a=>a.band.colour='rgba(17, 26, 32, 0.96)',a=>a.labels[9].left=a.labels[8].right+12,a=>a.terminalCaption.bottom=800,a=>a.textBoxes[0].bottom=844]){
  const changed=structuredClone(actual);mutate(changed);await assert.rejects(()=>checkV5Layout({evaluate:async()=>changed},current));
 }
});
