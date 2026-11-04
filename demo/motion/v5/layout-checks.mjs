/** Assertions run against every actual Chromium frame before host PNG capture. */
import assert from 'node:assert/strict';

export function intersects(a,b){
 return a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
}
export function assertNamedClearance(obstructions,checks){
 for(const check of checks)for(const element of check.elements){
  for(const obstruction of obstructions)if(obstruction)
   assert(!intersects(obstruction,element),`${check.phase}: overlay/caption/rail covers ${element.name}`);
 }
}

export async function checkV5Layout(page,state){
 const actual=await page.evaluate(({index,local})=>{
  const data=window.MOTION_DATA;
  const box=el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
  const cjk=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
  const overlay=document.querySelector('.live-overlay'),v=document.querySelector('.live-take');
  const textBoxes=[],walker=document.createTreeWalker(document.querySelector('#stage'),NodeFilter.SHOW_TEXT);
  for(let node;node=walker.nextNode();){
   if(!node.textContent.trim())continue;
   const range=document.createRange();range.selectNodeContents(node);
   const rect=box(range),clip=node.parentElement.closest('.scene,.architecture');
   if(clip){assertClip(clip);rect.bottom=Math.min(rect.bottom,clip.getBoundingClientRect().bottom);}
   textBoxes.push({text:node.textContent,...rect});
  }
  function assertClip(el){if(getComputedStyle(el).overflow!=='hidden'||el.getBoundingClientRect().bottom>766)throw new Error('Scene must stop before the chapter band');}
  return {
   cjk:cjk.test(document.body.innerText),bar:box(document.querySelector('.chapter-rail')),
   band:{...box(document.querySelector('#chapters')),colour:getComputedStyle(document.querySelector('#chapters')).backgroundColor,opacity:getComputedStyle(document.querySelector('#chapters')).opacity},
   labels:[...document.querySelectorAll('[data-chapter]')].map(el=>({text:el.textContent,...box(el),font:parseFloat(getComputedStyle(el).fontSize),current:el.classList.contains('current')})),
   segments:[...document.querySelectorAll('[data-segment]')].map(el=>({...box(el),fill:new DOMMatrix(getComputedStyle(el.querySelector('b')).transform).a})),
   overlay:overlay?{...box(overlay),phase:overlay.dataset.phase,fonts:[...overlay.querySelectorAll('h2,p,code,span')].map(el=>parseFloat(getComputedStyle(el).fontSize)),keyFonts:[...overlay.querySelectorAll('strong,.equation b')].map(el=>parseFloat(getComputedStyle(el).fontSize)),scroll:overlay.scrollHeight,client:overlay.clientHeight}:null,
   video:v?{...box(v),fit:getComputedStyle(v).objectFit,transform:getComputedStyle(v).transform,source:[v.videoWidth,v.videoHeight]}:null,
   captureVersion:data.portable_inputs.recordings[data.scenes[index].id]?.receipt.capture_version,
   onScreen:[...document.querySelectorAll('[data-on-screen]')].map(el=>({scene:el.dataset.onScreen,text:el.textContent,expected:data.scenes.find(s=>s.id===el.dataset.onScreen).on_screen})),
   textBoxes,terminalCaption:document.querySelector('.terminal-caption')?{...box(document.querySelector('.terminal-caption')),font:parseFloat(getComputedStyle(document.querySelector('.terminal-caption')).fontSize)}:null,
   namedChecks:index===5?data.live_named_elements.filter(c=>Math.abs(c.at_s-local)<1e-6):index===8?[{phase:'ending hold',elements:data.ending_named_elements}]:[],
   copies:document.querySelectorAll('.post-copy').length,tiles:document.querySelectorAll('.input-tile').length,
   inserts:document.querySelectorAll('.scale-accent,[data-accent],iframe').length,
  };
 },{index:state.index,local:state.local});
 assert.equal(actual.cjk,false,'Film DOM contains non-English glyphs');
 assert.equal(actual.inserts,0,'All motion is native web code');
 if([5,8].includes(state.index))assert.equal(actual.captureVersion,7,'A v7 take with an audited startup cover is required before frame capture');
 assert.equal(actual.bar.height,12);assert.equal(actual.bar.width,1920);assert.equal(actual.bar.top,844);
 assert.equal(actual.band.colour,'rgb(17, 26, 32)','Chapter band must be fully opaque');assert.equal(actual.band.opacity,'1');
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
 if(state.index===1)assert.equal(actual.copies,7);
 if(state.index===2)assert.equal(actual.tiles,4);
 if(actual.video){
  assert.deepEqual(actual.video.source,[1920,1080]);assert.equal(actual.video.fit,'contain');assert.equal(actual.video.transform,'none');
  assert.equal(actual.video.left,0);assert.equal(actual.video.top,0);assert.equal(actual.video.right,1920);assert.equal(actual.video.bottom,1080);
 }
 if(state.index===5&&state.overlay){
  assert.equal(actual.overlay?.phase,state.overlay.receipt_phase);assert(actual.overlay.bottom<790);
  assert(actual.overlay.fonts.every(x=>x>=56));assert(actual.overlay.keyFonts.every(x=>x>=96),'Key numbers must be at least 96 px');
  assert(actual.overlay.scroll<=actual.overlay.client+2,'Live explanation overflows');
  if(Math.abs(state.local-state.overlay.at_scene_s)<1e-6)assert(actual.namedChecks.length,'Missing named element audit at cue onset');
 }
 assertNamedClearance([actual.overlay,actual.band,{left:0,right:1920,top:880,bottom:1080}],actual.namedChecks);
 return actual;
}
