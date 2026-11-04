/** Assertions run against every actual Chromium frame before host PNG capture. */
import assert from 'node:assert/strict';
import {targets,requiredText} from './sentence-targets.mjs';
import {assertCardFrame,cardBands} from './card-band.mjs';
import {liveTerminalAt,localTerminalAt} from './live-terminal.mjs';

export function intersects(a,b){
 return a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
}
export function assertNamedClearance(obstructions,checks){
 for(const check of checks)for(const element of check.elements){
  for(const obstruction of obstructions)if(obstruction)
   assert(!intersects(obstruction,element),`${check.phase}: overlay/caption/rail covers ${element.name}`);
 }
}
export function assertVerdictReferents(check,expected){
 assert(check.native?.elements?.some(e=>e.name==='verdict'),'Native verdict referent required');
 assert.equal(expected?.length,2,'Both receipt-bound E3 filing components required');
 assert.equal(check.filings?.length,2,'Both filing referents required for the entire verdict sentence');
 for(const source of expected){
  const link=check.filings.find(c=>c.form===source.form);
  assert(link&&link.evidence_id==='E3'&&link.href===source.url&&link.text===`${source.form} · ${source.period_label}`,'Filing form, period and SEC URL must match E3 in the result JSON');
  assert.equal(link.font,56,'Filing citations use the other cards\' 56 px type scale');
 }
}

export function assertLiveTerminal(terminal,expected,native,trace,top=558){
 assert(terminal,'Receipt-bound terminal window required');
 assert.deepEqual([terminal.left,terminal.right,terminal.top,terminal.bottom],[80,1840,top,top+232]);
 assert.equal(terminal.colour,'rgb(17, 26, 32)');assert.equal(terminal.opacity,'1');
 assert.equal(terminal.title,trace.title);assert.equal(terminal.dots,3);
 assert.equal(terminal.footer,trace.honesty_label);
 assert.equal(terminal.clock,expected.clock);assert.equal(terminal.running,String(expected.running));
 assert.deepEqual(terminal.rows.map(r=>({kind:r.kind,text:r.text})),expected.rows);
 assert(terminal.rows.length<=5,'Terminal scrolls at five lines');
 for(const row of terminal.rows){
  assert(row.font>=28);assert(row.lineHeight>=34);
  assert(row.left>=terminal.left&&row.right<=terminal.right&&row.top>=terminal.top+32&&row.bottom<=terminal.bottom-28,'Terminal row is clipped');
  assert(row.scroll<=row.width+1,'Terminal row overflows horizontally');
 }
 assert.equal(terminal.cursor,expected.cursor,'Cursor blink must follow the film clock');
 assertNamedClearance([terminal],native?[native]:[]);
}

export async function checkV5Layout(page,state){
 const actual=await page.evaluate(({index,local,targets,requiredText})=>{
  const data=window.MOTION_DATA;
  const box=el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
  const visible=el=>{let opacity=1;for(let p=el;p;p=p.parentElement){const s=getComputedStyle(p);if(s.visibility==='hidden'||s.display==='none')return false;opacity*=Number(s.opacity);}return opacity>=.5;};
  const cjk=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
  const overlay=document.querySelector('.live-overlay'),v=document.querySelector('.live-take'),paint=document.querySelector('.native-video-frame'),terminal=document.querySelector('.terminal-window'),plate=document.querySelector('.live-backplate');
  const textBoxes=[],walker=document.createTreeWalker(document.querySelector('#stage'),NodeFilter.SHOW_TEXT);
  for(let node;node=walker.nextNode();){
   if(!node.textContent.trim()||!visible(node.parentElement)||node.parentElement.closest('.post-copy'))continue;
   const range=document.createRange();range.selectNodeContents(node);
   const rect=box(range),clip=node.parentElement.closest('.scene,.architecture');
   if(clip)assertClip(clip);
   textBoxes.push({text:node.textContent,...rect});
  }
  function assertClip(el){if(getComputedStyle(el).overflow!=='hidden'||el.getBoundingClientRect().bottom>766)throw new Error('Scene must stop before the chapter band');}
  const sid=data.scenes[index].id,at=data.scenes[index].target_start_s+local;
  const sentenceChecks=data.cues._events[sid].filter(e=>at+1e-7>=e.cue_start&&at<=e.cue_end+1e-7).map(e=>{
   const selectors=targets[sid]?.[e.event];if(!selectors?.length)throw new Error(`Missing named targets: ${sid}/${e.event}`);
   const elements=selectors.flatMap(selector=>{
    const els=[...document.querySelectorAll(selector)].filter(visible);
    if(!els.length)throw new Error(`Named element absent or dim at sentence onset/end: ${sid}/${e.event} ${selector}`);
    return els.map(el=>({name:selector,...box(el),text:el.textContent}));
   });
   const expected=requiredText[`${sid}/${e.event}`];
   if(selectors.includes('.live-terminal')&&terminal?.dataset.cue!==e.event)throw new Error(`Terminal focus must lead and hold through its measured sentence: ${e.event}`);
   if(sid==='v502'&&e.event==='formats'&&elements.length!==4)throw new Error('All four real previews must be present at sentence onset');
   if(expected&&!elements.some(el=>el.text.includes(expected)))throw new Error(`Incomplete named text at onset/end: ${sid}/${e.event}`);
   const native=index===5?e.native_check:index===8?{phase:'ending hold',at_s:0,visible_until_s:16,elements:data.ending_named_elements}:null;
   if([5,8].includes(index)&&(!native?.elements?.length||local<native.at_s-1e-6||local>native.visible_until_s+1e-6))throw new Error(`Native proof not held through sentence: ${sid}/${e.event}`);
   const filings=sid==='v505'&&e.event==='verdict'?[...document.querySelectorAll('.filing-citation')].filter(visible).map(el=>({form:el.dataset.form,evidence_id:el.dataset.evidenceId,href:el.href,text:el.textContent,font:parseFloat(getComputedStyle(el).fontSize)})):null;
   return {scene:sid,event:e.event,at_s:at,measured:e.measured,status:'pass',elements,native,expected,filings,
    ...(selectors.includes('.live-terminal')?{referents:['terminal window','native in-progress SEC status']}:{} )};
  });
  return {
   sentenceChecks,
   expectedFilings:data.live_filing_citations,
   liveTrace:data.live_terminal,
   localTrace:data.local_terminal,
   plate:plate?{...box(plate),state:plate.dataset.state,colour:getComputedStyle(plate).backgroundColor,opacity:getComputedStyle(plate).opacity}:null,
   terminalNative:data.live_named_elements.find(c=>c.phase==='check_against_sec'),
   terminal:terminal?{...box(terminal),colour:getComputedStyle(terminal).backgroundColor,opacity:getComputedStyle(terminal).opacity,
    title:terminal.querySelector('.live-terminal-title').textContent,dots:terminal.querySelectorAll('.terminal-dots i').length,
    footer:terminal.querySelector('footer').textContent,clock:terminal.querySelector('time').textContent,running:terminal.querySelector('time').dataset.running,
    cursor:!!terminal.querySelector('.live-terminal-cursor')&&getComputedStyle(terminal.querySelector('.live-terminal-cursor')).visibility==='visible',
    rows:[...terminal.querySelectorAll('.live-terminal-line')].map(el=>({...box(el),kind:el.dataset.kind,text:el.firstChild?.nodeValue||'',font:parseFloat(getComputedStyle(el).fontSize),lineHeight:parseFloat(getComputedStyle(el).lineHeight),scroll:el.scrollWidth}))}:null,
   cjk:cjk.test(document.body.innerText),bar:box(document.querySelector('.chapter-rail')),
   band:{...box(document.querySelector('#chapters')),colour:getComputedStyle(document.querySelector('#chapters')).backgroundColor,opacity:getComputedStyle(document.querySelector('#chapters')).opacity},
   labels:[...document.querySelectorAll('[data-chapter]')].map(el=>({text:el.textContent,...box(el),font:parseFloat(getComputedStyle(el).fontSize),current:el.classList.contains('current')})),
   segments:[...document.querySelectorAll('[data-segment]')].map(el=>({...box(el),fill:new DOMMatrix(getComputedStyle(el.querySelector('b')).transform).a})),
   overlay:overlay?{...box(overlay),phase:overlay.dataset.phase,colour:getComputedStyle(overlay).backgroundColor,opacity:getComputedStyle(overlay).opacity,fonts:[...overlay.querySelectorAll('h2,p,code,span')].map(el=>parseFloat(getComputedStyle(el).fontSize)),keyFonts:[...overlay.querySelectorAll('strong,.equation b')].map(el=>parseFloat(getComputedStyle(el).fontSize)),scroll:overlay.scrollHeight,client:overlay.clientHeight}:null,
   video:v?{...box(v),fit:getComputedStyle(v).objectFit,transform:getComputedStyle(v).transform,source:[v.videoWidth,v.videoHeight]}:null,
   decodedFrame:paint?{...box(paint),ready:paint.dataset.nativePageReady==='true',sourceTime:Number(paint.dataset.sourceTime)}:null,
   captureVersion:data.portable_inputs.recordings[data.scenes[index].id]?.receipt.capture_version,
   onScreen:[...document.querySelectorAll('[data-on-screen]')].map(el=>({scene:el.dataset.onScreen,text:el.textContent,expected:data.scenes.find(s=>s.id===el.dataset.onScreen).on_screen})),
   textBoxes,terminalCaption:document.querySelector('.terminal-caption')?{...box(document.querySelector('.terminal-caption')),font:parseFloat(getComputedStyle(document.querySelector('.terminal-caption')).fontSize)}:null,
   namedChecks:index===5?data.live_named_elements.filter(c=>local+1e-6>=c.at_s&&local<=c.visible_until_s):index===8?[{phase:'ending hold',elements:data.ending_named_elements}]:[],
   copies:document.querySelectorAll('.post-copy').length,tiles:document.querySelectorAll('.input-tile').length,
   cascadeClip:document.querySelector('.cascade')?box(document.querySelector('.cascade')):null,
   viralHeadline:document.querySelector('.viral-headline')?box(document.querySelector('.viral-headline')):null,
   inserts:document.querySelectorAll('.scale-accent,[data-accent],iframe').length,
  };
 },{index:state.index,local:state.local,targets,requiredText});
 assert.equal(actual.cjk,false,'Film DOM contains non-English glyphs');
 assert.equal(actual.inserts,0,'All motion is native web code');
 if([5,8].includes(state.index))assert.equal(actual.captureVersion,9,'A v9 take with decoded workspace start and native text line audits is required before frame capture');
 assert.equal(actual.bar.height,12);assert.equal(actual.bar.width,1920);assert.equal(actual.bar.top,844);
 assert.equal(actual.band.colour,'rgb(17, 26, 32)','Chapter band must be fully opaque');assert(Math.abs(Number(actual.band.opacity)-state.fade)<1e-6,'Rail must fade with the sign-off');
 assert.equal(actual.band.left,0);assert.equal(actual.band.right,1920);assert(actual.band.bottom>=1080);
 assert.equal(actual.labels.length,10);assert.equal(actual.segments.length,10);
 assert.equal(actual.labels.filter(l=>l.current).length,1);assert(actual.labels[state.index].current);
 actual.labels.forEach((l,i)=>{
  assert(l.font>=32);assert(l.left>=24&&l.right<=1896&&l.bottom<=844);
  if(i)assert(l.left-actual.labels[i-1].right>=48-.1,'Chapter labels need 24 px clear space on both sides');
 });
 actual.segments.forEach((s,i)=>{assert(Math.abs(s.width-1920*state.chapters[i].duration_s/178)<1);assert(Math.abs(s.fill-state.chapters[i].fill)<.001);});
 actual.onScreen.forEach(copy=>assert.equal(copy.text,copy.expected,`${copy.scene}: rendered on_screen differs from storyboard`));
 if([0,4].includes(state.index))assert.equal(actual.onScreen.length,1);
 const textLimit=actual.video?790:766;
 actual.textBoxes.forEach(r=>assert(r.bottom<=textLimit+.1,`Scene text enters reserved rail/caption lane: ${r.text}`));
 if(actual.terminalCaption){assert.equal(actual.terminalCaption.font,56);assert(actual.terminalCaption.bottom<=Math.min(800,actual.band.top-24));}
 if(state.index===1){assert.equal(actual.copies,7);assert(actual.cascadeClip.right<=1056);assert(actual.viralHeadline.left>=1056,'Headline column is reserved');}
 if(state.index===2)assert.equal(actual.tiles,4);
 if(actual.video){
  assert(actual.plate,'Whole-composite backplate required, including between cues');
  assert.equal(actual.plate.left,0);assert.equal(actual.plate.right,1920);
  assert.equal(actual.plate.colour,'rgb(17, 26, 32)');assert.equal(actual.plate.opacity,'1');
  assert.equal(actual.plate.top,state.index===8?610:actual.plate.state==='password'?530:558);
  assert.equal(actual.plate.bottom,790);
  assert.deepEqual(actual.video.source,[1920,1080]);assert.equal(actual.video.fit,'contain');assert.equal(actual.video.transform,'none');
  assert.equal(actual.video.left,0);assert.equal(actual.video.top,0);assert.equal(actual.video.right,1920);assert.equal(actual.video.bottom,1080);
  assert(actual.decodedFrame?.ready,'Decoded native image must be painted before composing the frame, including the ending cut');
  assert.equal(actual.decodedFrame.left,0);assert.equal(actual.decodedFrame.top,0);assert.equal(actual.decodedFrame.right,1920);assert.equal(actual.decodedFrame.bottom,1080);
  assert(Math.abs(actual.decodedFrame.sourceTime-state.local)<1/30+.0001,'Decoded native frame must follow the unchanged take clock');
 }
 if(state.index===5&&state.overlay){
  const terminal=liveTerminalAt(state.local,actual.liveTrace);
  assert.equal(actual.overlay?.phase,terminal?'check_against_sec':state.overlay.receipt_phase);assert.equal(actual.overlay.colour,'rgb(17, 26, 32)');assert.equal(actual.overlay.opacity,'1');assert(actual.overlay.bottom<=790);
  if(actual.overlay.top===558)assert.equal(actual.overlay.bottom,790,'Lower mask must meet the chapter band without a paragraph slit');
  if(terminal)assertLiveTerminal(actual.terminal,terminal,actual.terminalNative,actual.liveTrace);
  else {assert(actual.overlay.fonts.every(x=>x>=56));assert(actual.overlay.keyFonts.every(x=>x>=96),'Key numbers must be at least 96 px');}
  assert(actual.overlay.scroll<=actual.overlay.client+2,'Live explanation overflows');
  if(Math.abs(state.local-state.overlay.at_scene_s)<1e-6)assert(actual.namedChecks.length,'Missing named element audit at cue onset');
 }
 const local=state.index===6?localTerminalAt(state.local,actual.localTrace):null;
 if(local)assertLiveTerminal(actual.terminal,local,null,actual.localTrace,250);
 assertNamedClearance([actual.overlay,actual.plate,actual.band,{left:0,right:1920,top:880,bottom:1080}],actual.namedChecks);
 for(const check of actual.namedChecks)if(state.index===5)assertCardFrame(check.card_edge_audit,cardBands[check.overlay_band],{verdict:check.phase==='verdict_reveal'});
 for(const check of actual.sentenceChecks){
  for(const r of check.elements){assert(r.width>0&&r.height>0&&r.left>=0&&r.right<=1920&&r.top>=0&&r.bottom<=790,`${check.scene}/${check.event}: named proof is clipped`);}
  // Web proof may itself be the overlay; native proof must clear it completely.
  assertNamedClearance([actual.overlay,actual.plate,actual.band,{left:0,right:1920,top:880,bottom:1080}],check.native?[check.native]:[]);
  if(state.index===5)assertCardFrame(check.native?.card_edge_audit,cardBands[check.native?.overlay_band],{verdict:check.event==='verdict'});
  if(check.scene==='v505'&&check.event==='verdict'){
   assertVerdictReferents(check,actual.expectedFilings);
   check.referents=['verdict','filing'];
  }
 }
 return actual;
}
