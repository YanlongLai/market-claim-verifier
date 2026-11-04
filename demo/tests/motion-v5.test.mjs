import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {stateAt,boundaries,chapterState,repostCascade,overlayAt,terminalAt,outroStampAt} from '../motion/v5/plan.js';
import {labelPositions} from '../motion/v5/chapters.js';
import {targets} from '../motion/v5/sentence-targets.mjs';
import {assertNamedClearance,checkV5Layout} from '../motion/v5/layout-checks.mjs';
import {installCaptureDOM,validateGeometry,hasCJK,presentation,showTraceAndFiling,validateLiveResult,redact,endingExpectedLinks,coverDocument,captureCoverCSS,revealCaptureDOM,namedSelectors,requestIdFromLog,saveRequestId} from '../record_v5.mjs';
import {parseArgs} from '../motion/render.mjs';
import {liveTerminalAt,localTerminalAt} from '../motion/v5/live-terminal.mjs';
import {assertLiveTerminal,assertWaitCue} from '../motion/v5/layout-checks.mjs';
const ctx={window:{}};vm.runInNewContext(readFileSync(new URL('../motion/v5/data.js',import.meta.url),'utf8'),ctx);
const data=JSON.parse(JSON.stringify(ctx.window.MOTION_DATA)),scenes=data.scenes,segments=data.chapter_bar.segments;
const terminalFixtures=JSON.parse(readFileSync(new URL('./fixtures/v5-terminals.json',import.meta.url),'utf8'));
data.live_terminal=terminalFixtures.online;data.local_terminal=terminalFixtures.local;
const state=t=>stateAt(t,scenes,segments);
test('real-log terminal uses runner elapsed, scrolls five rows, freezes at verdict and yields to card 3',()=>{
 const trace=data.live_terminal,start=trace.start_scene_s;
 assert.equal(liveTerminalAt(trace.typing_start_scene_s-.001,trace),null);
 assert.equal(trace.typing_start_scene_s,start);
 assert.equal(liveTerminalAt(start,trace).rows[0].kind,'request');
 assert(!liveTerminalAt(start,trace).rows[0].text.startsWith('$'));
 assert.equal(liveTerminalAt(start,trace).clock,'00.0 s');
 for(const row of trace.rows){
  assert(!(liveTerminalAt(start+row.at_s-.001,trace)?.rows||[]).some(r=>r.text===row.text));
  assert(liveTerminalAt(start+row.at_s,trace).rows.some(r=>r.text===row.text));
 }
 const reasoning=liveTerminalAt(start+9,trace);
 assert.equal(reasoning.rows.length,5);assert(!reasoning.rows.some(r=>r.kind==='command'));
 assert(reasoning.rows.at(-1).text.includes('model · step 3'));
 let previous=0;
 for(let f=Math.ceil(trace.typing_start_scene_s*30);f/30<trace.end_scene_s;f++){
  const picture=liveTerminalAt(f/30,trace);assert(picture.rows.length<=5);
  const elapsed=parseFloat(picture.clock);assert(elapsed>=previous);previous=elapsed;
 }
 const final=liveTerminalAt(start+trace.verdict.at_s,trace);
 assert.equal(final.rows.at(-1).text,'verdict  contradicted  16.4 s  $0.0215');assert(!final.running);
 assert.equal(liveTerminalAt(trace.end_scene_s-.001,trace).clock,final.clock);
 assert.equal(liveTerminalAt(trace.end_scene_s,trace),null);
 // Native result reframe keeps the terminal, with no stale card-2 headline.
 assert.equal(liveTerminalAt(trace.end_scene_s-.03,trace).rows.at(-1).kind,'verdict');
});

test('terminal cursor and stopwatch use seek time, including backward and nonsequential seeks',()=>{
 const trace=data.live_terminal,start=trace.start_scene_s;
 assert.notEqual(liveTerminalAt(start+9.2,trace).cursor,liveTerminalAt(start+9.8,trace).cursor);
 const a=liveTerminalAt(start+3.2,trace);liveTerminalAt(start+16.8,trace);
 assert.deepEqual(liveTerminalAt(start+3.2,trace),a);
 const later=structuredClone(trace);later.verdict.at_s=12.345;
 assert.equal(liveTerminalAt(start+13,later).clock,'12.3 s');
 const instant=structuredClone(trace);instant.rows[0]={...instant.rows[0],kind:'call'};
 assert(!(liveTerminalAt(start-.1,instant)?.rows||[]).some(r=>r.kind==='call'));
 assert(liveTerminalAt(start,instant).rows.some(r=>r.kind==='call'));
});

test('terminal audit rejects fabricated rows, small text, clipping and coverage of native status',()=>{
 const trace=data.live_terminal,expected=liveTerminalAt(trace.start_scene_s+10,trace);
 const terminal={left:80,right:1840,top:558,bottom:790,colour:'rgb(17, 26, 32)',opacity:'1',
  title:trace.title,dots:3,footer:trace.honesty_label,clock:expected.clock,running:String(expected.running),cursor:expected.cursor,
  rows:expected.rows.map((r,i)=>({...r,left:103,right:1817,top:603+i*36,bottom:639+i*36,width:1714,font:30,lineHeight:36,scroll:1714}))};
 const native={phase:'check_against_sec',elements:[{name:'native in-progress SEC status',left:180,right:1531,top:187,bottom:224}]};
 assertLiveTerminal(terminal,expected,native,trace);
 for(const mutate of [t=>t.clock='99.9 s',t=>t.rows[0].text='invented call',t=>t.rows[0].font=27,t=>t.rows[0].lineHeight=33,t=>t.rows.push(t.rows[0]),t=>t.opacity='.9',t=>t.rows[0].scroll=2000,t=>t.rows[0].bottom=800]){
  const bad=structuredClone(terminal);mutate(bad);assert.throws(()=>assertLiveTerminal(bad,expected,native,trace));
 }
 native.elements[0].bottom=560;
 assert.throws(()=>assertLiveTerminal(terminal,expected,native,trace),/covers/);
});

test('wait narration is checked against its named source rows on every spoken film frame',()=>{
 const film=JSON.parse(JSON.stringify(ctx.window.MOTION_DATA)),trace=film.live_terminal;
 for(const e of film.cues._events.v505.filter(e=>e.receipt_phase==='check_against_sec')){
  for(let f=Math.ceil(e.cue_start*30);f/30<=e.cue_end;f++){
   const picture=liveTerminalAt(f/30-58,trace);
   assert.equal(assertWaitCue(picture,trace,e.event).status,'pass');
  }
 }
 const first=trace.rows.find(r=>r.event==='tool_call');
 assert.throws(()=>assertWaitCue(liveTerminalAt(trace.start_scene_s+first.at_s-.001,trace),trace,'tools'),/First real tool_call/);
 const claims=film.cues._events.v505.find(e=>e.event==='claims');
 const three=liveTerminalAt(claims.cue_start-58,trace);three.rows.pop();
 assert.throws(()=>assertWaitCue(three,trace,'claims'),/four real tool_call/);
 const ids=film.cues._events.v505.find(e=>e.event==='evidence_ids');
 const missing=liveTerminalAt(ids.cue_start-58,trace);missing.rows=missing.rows.filter(r=>!r.text.includes('→ E6'));
 assert.throws(()=>assertWaitCue(missing,trace,'evidence_ids'),/evidence-ID/);
 const thinking=film.cues._events.v505.find(e=>e.event==='thinking');
 assert.throws(()=>assertWaitCue(liveTerminalAt(thinking.cue_start-58,trace),trace,'decide'),/real checks and final verdict/);
});

test('terminal header audit rejects unreadable or overlapping source/replay disclosures',()=>{
 const trace=data.live_terminal,expected=liveTerminalAt(trace.start_scene_s+10,trace);
 const terminal={left:80,right:1840,top:558,bottom:790,colour:'rgb(17, 26, 32)',opacity:'1',
  title:trace.title,dots:3,footer:trace.honesty_label,clock:expected.clock,running:String(expected.running),cursor:expected.cursor,
  rows:expected.rows.map((r,i)=>({...r,left:103,right:1817,top:603+i*36,bottom:639+i*36,width:1714,font:30,lineHeight:36,scroll:1714})),
  header:[{left:103,right:500,bottom:600,font:30},{left:600,right:1400,bottom:600,font:30}]};
 assertLiveTerminal(terminal,expected,null,trace);
 for(const mutate of [t=>t.header[1].font=22,t=>t.header[1].left=490,t=>t.header[1].right=1900]){
  const bad=structuredClone(terminal);mutate(bad);assert.throws(()=>assertLiveTerminal(bad,expected,null,trace));
 }
});

test('ten binding cuts, full-frame live playback, 178-second film',()=>{
 assert.deepEqual(boundaries,[0,8,20,32,46,58,116,138,154,170,178]);
 boundaries.slice(0,-1).forEach((t,i)=>assert.equal(state(t).shot,`v50${i}`));
 assert.equal(state(178).shot,'v509');assert.equal(state(178).fade,0);
 assert.throws(()=>state(NaN));assert.throws(()=>state(178.001));
 for(const t of [58,89,115.99,154,169.99])assert.deepEqual(state(t).liveTake,{scale:1,x:0,y:0});
 assert.equal(parseArgs(['--entry','v5/index.html','--t','100','--out','/tmp/v5']).entry,'v5/index.html');
});
test('live cards arrive 0.2 s before their sentence and trace starts on the first tool row',()=>{
 const events=scenes[5].cue_events;assert.equal(events.length,15);
 for(const [i,e] of events.entries()){
  const at=e.picture_at_scene_s;
  assert.equal(state(58+at).overlay.event,e.event);
  if(at>0)assert.equal(state(58+at-1/300).overlay?.event,i?events[i-1].event:undefined);
  const cue=data.cues._events.v505.find(c=>c.event===e.event);
  assert(cue.cue_start-cue.t>=.1-1e-7&&cue.cue_start-cue.t<=.3+1e-7);
  if(i)assert(cue.t>=data.cues._events.v505[i-1].cue_end-1e-7);
 }
 assert.equal(events.find(e=>e.event==='trace').receipt_phase,'tool_call_2_reveal');
 assert.equal(events.find(e=>e.event==='each').receipt_phase,'tool_call_4_reveal');
 assert.equal(events.find(e=>e.event==='program').receipt_phase,'program_verdict_reveal');
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
 for(let frame=0;frame<360;frame++)assert(repostCascade(frame/30).every(c=>c.opacity===0||c.opacity===1),'Visible paper cards must stay opaque throughout their entrance and hold');
 assert(repostCascade(.5)[6].x<repostCascade(8)[6].x);
 assert.deepEqual(repostCascade(9),repostCascade(11.9));
 assert(state(8).cascade.every(c=>c.opacity===0));
 const app=readFileSync(new URL('../motion/v5/app.js',import.meta.url),'utf8');
 assert(app.includes('class="post-card"'));assert(!app.includes('reposts'));
 assert(!app.includes('.png\'')&&!app.includes('broll'));
});
test('all four real input tiles are present together after the entrance',()=>{
 assert.equal(data.inputs.length,4);assert.deepEqual(state(31).inputs,[true,true,true,true]);
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
test('recorder retains trace expansion, four visible tools and the result-JSON Apple derivation',async()=>{
 const f=traceFixture();await showTraceAndFiling(f);
 assert.equal(f.report.tool_calls_shown,4);assert.equal(f.report.program_verdict_shown,true);assert.equal(f.report.apple_inspect_open,false);assert.equal(f.report.trace_details_open,true);
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
 const document={documentElement:{style:{zoom:'1.95'},dataset:{}},body:{},querySelector:()=>({getBoundingClientRect:()=>({left:180,right:1740,top:180,bottom:480,width:1560,height:300})})};
 const fixture={document,getComputedStyle:(_el,pseudo)=>pseudo?{backgroundColor:'rgb(247, 245, 239)',visibility:'visible',display:'block'}:{visibility:'hidden'}};
 vm.runInNewContext(`(${revealCaptureDOM.toString()})()`,fixture);
 assert.equal(document.documentElement.dataset.captureReady,'true');
 delete document.documentElement.dataset.captureReady;
 document.querySelector=()=>({getBoundingClientRect:()=>({left:180,right:1740,top:900,bottom:1200,width:1560,height:300})});
 assert.throws(()=>vm.runInNewContext(`(${revealCaptureDOM.toString()})()`,fixture),/not_framed/);
 assert.equal(document.documentElement.dataset.captureReady,undefined);
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
 const stage={innerHTML:'',dataset:{},querySelector:()=>null,querySelectorAll:()=>[]};
 const element=()=>({style:{},getBoundingClientRect:()=>({width:100}),classList:{toggle(){}},querySelector:()=>({style:{}})});
 const context={window:{MOTION_DATA:structuredClone(data)},document:{querySelector:s=>s==='#stage'?stage:s==='#chapter-layer'?{}:s==='#chapters'||s.startsWith('[data-')||s.startsWith('#node-')||s.startsWith('#link-')?element():null}};
 const source=['plan.js','chapters.js','video-frame.mjs','live-terminal.mjs','app.js'].map(name=>readFileSync(new URL('../motion/v5/'+name,import.meta.url),'utf8').split('\n').filter(line=>!line.startsWith('import ')).join('\n').replaceAll('export ','')).join('\n');
 vm.runInNewContext(source+'\nglobalThis.sceneBody=body;',context);
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

test('real local session types the recorded command, compresses chunk times and holds its final receipt',()=>{
 const trace=data.local_terminal;
 assert.equal(localTerminalAt(-.001,trace),null);
 assert.equal(localTerminalAt(0,trace).rows[0].text,'');
 assert(localTerminalAt(.6,trace).rows.some(r=>r.text.startsWith('$ uv run python -m claimcheck')));
 for(const frame of trace.frames){
  const at=trace.start_scene_s+frame.at_s/trace.speed;
  assert.deepEqual(localTerminalAt(at,trace).rows.slice(-frame.rows.length),frame.rows.map(({kind,text})=>({kind,text})));
 }
 const final=localTerminalAt(trace.end_scene_s-.001,trace);
 assert(final.done);assert(final.rows.at(-1).text.includes('$0.0611'));
 assert(!final.rows.some(r=>r.text.includes('CoreWeave')));
 assert.equal(localTerminalAt(trace.end_scene_s,trace),null);
 const back=localTerminalAt(1,trace);localTerminalAt(4,trace);assert.deepEqual(localTerminalAt(1,trace),back);
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
 const actual={sentenceChecks:[],cjk:false,inserts:0,bar:{height:12,width:1920,top:844},band:{left:0,right:1920,top:790,bottom:1080,colour:'rgb(17, 26, 32)',opacity:'1'},
  labels:centres.map((c,i)=>({font:32,left:c-45,right:c+45,bottom:834,current:i===6})),
  segments:current.chapters.map(s=>({width:1920*s.duration_s/178,fill:s.fill})),onScreen:[],
  textBoxes:[{text:'Saved replay',bottom:748}],terminalCaption:{font:56,bottom:748},namedChecks:[],overlay:null,video:null};
 await checkV5Layout({evaluate:async()=>actual},current);
 await assert.rejects(()=>checkV5Layout({evaluate:async()=>({...actual,captureVersion:8})},state(58)),/v9 take/);
 for(const mutate of [a=>a.band.colour='rgba(17, 26, 32, 0.96)',a=>a.labels[9].left=a.labels[8].right+12,a=>a.terminalCaption.bottom=800,a=>a.textBoxes[0].bottom=844]){
  const changed=structuredClone(actual);mutate(changed);await assert.rejects(()=>checkV5Layout({evaluate:async()=>changed},current));
 }
});

test('every voice row has named frame targets and later referents wait for their sentence',()=>{
 let count=0;
 for(const scene of scenes)for(const e of scene.cue_events){assert(targets[scene.id][e.event]?.length);count++;}
 assert.equal(count,48);
 const when=(i,name)=>boundaries[i]+scenes[i].cue_events.find(e=>e.event===name).picture_at_scene_s;
 assert(state(when(1,'reposts')-.01).cascade.every(c=>c.opacity===0));
 assert(state(when(1,'reposts')+.2).cascade.some(c=>c.opacity>0));
 assert.deepEqual(state(when(2,'formats')+.1).inputs,[false,false,false,false]);
 for(const [i,name] of ['screenshot','pdf','podcast','video'].entries()){
  const lights=state(when(2,name)+.001).inputs;assert(lights[i]);assert.equal(lights.filter(Boolean).length,i+1);
 }
 assert.equal(state(when(2,'question')-.01).question,false);assert(state(when(2,'question')).question);
 assert.equal(state(when(4,'program')-.01).architecture.nodes[3],.15);
 assert.equal(state(when(4,'program')+.01).architecture.nodes[3],1);
 assert.equal(state(when(4,'principle')-.01).architecture.headline,false);assert(state(when(4,'principle')).architecture.headline);
 for(const name of ['false_support','cost_time','coverage']){assert.equal(state(when(7,name)-.01).results[name],false);assert(state(when(7,name)).results[name]);}
 assert.equal(state(when(8,'url')-.01).url,false);assert(state(when(8,'url')).url);
 assert.equal(state(when(9,'wordmark')-.01).wordmark,false);assert(state(when(9,'wordmark')).wordmark);
 const terminal=name=>terminalAt(scenes[3].cue_events.find(e=>e.event===name).picture_at_scene_s+.001,data.terminal_replays.beat3).rows.map(r=>r.text).join('\n');
 assert(!terminal('agent').includes('90.5%'));assert(terminal('nine').includes('90.5%'));
 const median=terminalAt(scenes[6].cue_events.find(e=>e.event==='median').picture_at_scene_s+.001,data.terminal_replays.beat6);
 assert(!median.rows.some(r=>r.text.includes('1,000')));
});

import {cardBands,assertCardFrame,cardScrollDelta} from '../motion/v5/card-band.mjs';
import {paintVideoFrame} from '../motion/v5/video-frame.mjs';
import {assertVerdictReferents} from '../motion/v5/layout-checks.mjs';

const rect=(top,bottom)=>({left:180,right:1740,top,bottom});
test('card framing keeps entire Reset/count controls clear of the edge, preserving the post',()=>{
 const audit={lines:[rect(180,240),rect(540,580)],controls:[rect(537,594)]};
 assert.throws(()=>assertCardFrame(audit),/crosses_card_edge/);
 const d=cardScrollDelta(audit,[rect(180,511)],400,4000);
 assert((537-d>=558||594-d<=558)&&180-d>=80&&511-d<=548);
 assertCardFrame({lines:audit.lines.map(r=>rect(r.top-d,r.bottom-d)),controls:audit.controls.map(r=>rect(r.top-d,r.bottom-d))});
 assert.equal(cardBands.bottom.bottom,790);
});
test('verdict framing removes the unrelated input charge and preserves the complete draft heading',()=>{
 const audit={lines:[rect(180,309),rect(520,585)],controls:[],input_charge:rect(-30,38),corrected_heading:rect(520,585)};
 assert.throws(()=>assertCardFrame(audit,cardBands.bottom,{verdict:true}),/crosses_card_edge/);
 const d=cardScrollDelta(audit,[rect(180,309)],1000,4000,{verdict:true});
 assert(d>=38.25&&180-d>=80);
 assertCardFrame({lines:[rect(180-d,309-d),rect(520-d,585-d)],controls:[],input_charge:rect(-30-d,38-d),corrected_heading:rect(520-d,585-d)},cardBands.bottom,{verdict:true});
 assert.throws(()=>cardScrollDelta(audit,[rect(80,548)],1000,4000,{verdict:true}),/no_clean_card_band/);
});
test('a passing verdict rectangle cannot stand in for either E3 filing referent',()=>{
 const expected=[{form:'10-K',period_label:'fiscal 2025 annual',url:'https://www.sec.gov/Archives/annual/'},{form:'10-Q',period_label:'nine months to 28 Jun 2025',url:'https://www.sec.gov/Archives/nine-months/'}];
 const check={native:{elements:[{name:'verdict'}]},filings:expected.map(c=>({form:c.form,evidence_id:'E3',href:c.url,text:`${c.form} · ${c.period_label}`,font:56}))};
 assertVerdictReferents(check,expected);
 for(const mutate of [c=>c.filings.pop(),c=>c.filings[1].text='10-Q',c=>c.filings[0].href='https://example.com/',c=>c.filings[0].font=32,c=>c.native.elements=[]]){
  const bad=structuredClone(check);mutate(bad);assert.throws(()=>assertVerdictReferents(bad,expected));
 }
});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
class Video extends EventTarget{
 readyState=1;duration=16;_time=0;seeking=false;videoWidth=1920;videoHeight=1080;dataset={source:'ending.mp4'};
 get currentTime(){return this._time;}
 set currentTime(t){this._time=t;this.seeking=true;}
}
test('ending frame zero waits for a decoded image and paints it before the screenshot may proceed',async()=>{
 const video=new Video(),draws=[],canvas={dataset:{},getContext:()=>({drawImage:(...args)=>draws.push(args)})};
 const first=paintVideoFrame(video,0,canvas);await tick();
 assert.equal(draws.length,0);assert.equal(canvas.dataset.nativePageReady,undefined);
 video.readyState=2;video.dispatchEvent(new Event('loadeddata'));await first;
 assert.equal(draws.length,1);assert.equal(canvas.dataset.sourceTime,'0');assert.equal(canvas.dataset.nativePageReady,'true');
 // The valid image remains in place until the next decoded seek can replace it.
 const next=paintVideoFrame(video,1/30,canvas);await tick();assert.equal(draws.length,1);
 video.seeking=false;video.dispatchEvent(new Event('seeked'));await next;
 assert.equal(draws.length,2);assert.equal(Number(canvas.dataset.sourceTime),1/30);
});
test('decode failure rejects the frame instead of accepting a dark placeholder',async()=>{
 const video=new Video(),canvas={dataset:{},getContext:()=>{throw new Error('must not paint');}};
 const painting=paintVideoFrame(video,0,canvas);await tick();
 video.dispatchEvent(new Event('error'));await assert.rejects(painting,/Recorded image unavailable/);
 assert.equal(canvas.dataset.nativePageReady,undefined);
});


test('recorder learns the response ID or the unique captured POST-window ID, never a prior request',async()=>{
 const folder=mkdtempSync(path.join(tmpdir(),'v5-log-id-'));
 try{
  const id='a'.repeat(32),other='b'.repeat(32),wall=Date.parse('2026-11-04T16:00:00Z');
  const row=(rid,time)=>JSON.stringify({line:`${time} INFO live id=${rid} +0.00s event=start`});
  const config={request_id_file:path.join(folder,'response-id'),server_log_spool:path.join(folder,'spool')};
  writeFileSync(config.server_log_spool,row(other,'2026-11-04T15:59:30Z')+'\n'+row(id,'2026-11-04T16:00:00Z')+'\n');
  const fromResponse=await saveRequestId(config,{request_id:other},wall);
  assert.equal(fromResponse.source,'response');assert.equal(readFileSync(config.request_id_file,'utf8').trim(),other);
  config.request_id_file=path.join(folder,'log-id');
  const fallback=await saveRequestId(config,{},wall);assert.equal(fallback.id,id);
  assert.equal(readFileSync(config.request_id_file,'utf8').trim(),id);
  assert.equal(requestIdFromLog(row(other,'2026-11-04T15:59:30Z')+'\n',wall),null);
  assert.equal(requestIdFromLog(row(id,'2026-11-04T16:00:00Z'),wall),null); // partial JSONL write
  assert.throws(()=>requestIdFromLog(row(id,'2026-11-04T16:00:00Z')+'\n'+row(other,'2026-11-04T16:00:01Z')+'\n',wall),/ambiguous/);
  await assert.rejects(()=>saveRequestId(config,{request_id:'bad'},wall),/invalid_response/);
 }finally{rmSync(folder,{recursive:true,force:true});}
});

test('whole-composite audit checks full-width gutters and higher password mask between cues',async()=>{
 const current=state(58.1),widths=Array(10).fill(90),centres=labelPositions(segments,widths);
 const actual={sentenceChecks:[],cjk:false,inserts:0,captureVersion:9,bar:{height:12,width:1920,top:844},
  band:{left:0,right:1920,top:790,bottom:1080,colour:'rgb(17, 26, 32)',opacity:'1'},
  labels:centres.map((c,i)=>({font:32,left:c-45,right:c+45,bottom:834,current:i===5})),
  segments:current.chapters.map(s=>({width:1920*s.duration_s/178,fill:s.fill})),onScreen:[],textBoxes:[],namedChecks:[],
  plate:{left:0,right:1920,top:542,bottom:790,state:'password',topBand:false,colour:'rgb(17, 26, 32)',opacity:'1'},
  overlay:{left:80,right:1840,top:558,bottom:790,phase:current.overlay.receipt_phase,colour:'rgb(17, 26, 32)',opacity:'1',fonts:[56],keyFonts:[],scroll:232,client:232},
  video:{source:[1920,1080],fit:'contain',transform:'none',left:0,right:1920,top:0,bottom:1080},
  decodedFrame:{ready:true,left:0,right:1920,top:0,bottom:1080,sourceTime:.1},liveTrace:data.live_terminal};
 await checkV5Layout({evaluate:async()=>actual},current);
 for(const mutate of [a=>a.plate=null,a=>a.plate.left=80,a=>a.plate.right=1840,a=>a.plate.top=558,a=>a.plate.opacity='.96']){
  const bad=structuredClone(actual);mutate(bad);await assert.rejects(()=>checkV5Layout({evaluate:async()=>bad},current));
 }
});
