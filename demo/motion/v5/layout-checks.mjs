/** Assertions run against every real Chromium frame before PNG capture. */
import assert from 'node:assert/strict';
export async function checkV5Layout(page,state){
 const actual=await page.evaluate(()=>{
  const box=el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
  const cjk=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
  const overlay=document.querySelector('.live-overlay'),v=document.querySelector('.live-take');
  return {cjk:cjk.test(document.body.innerText),bar:box(document.querySelector('.chapter-rail')),labels:[...document.querySelectorAll('[data-chapter]')].map(el=>({text:el.textContent,...box(el),font:parseFloat(getComputedStyle(el).fontSize),current:el.classList.contains('current')})),segments:[...document.querySelectorAll('[data-segment]')].map(el=>({...box(el),fill:new DOMMatrix(getComputedStyle(el.querySelector('b')).transform).a})),overlay:overlay?{...box(overlay),phase:overlay.dataset.phase,fonts:[...overlay.querySelectorAll('h2,p,code,span')].map(el=>parseFloat(getComputedStyle(el).fontSize)),keyFonts:[...overlay.querySelectorAll('strong,.equation b')].map(el=>parseFloat(getComputedStyle(el).fontSize)),scroll:overlay.scrollHeight,client:overlay.clientHeight}:null,video:v?{...box(v),fit:getComputedStyle(v).objectFit,transform:getComputedStyle(v).transform,source:[v.videoWidth,v.videoHeight]}:null,copies:document.querySelectorAll('.post-copy').length,tiles:document.querySelectorAll('.input-tile').length,inserts:document.querySelectorAll('.scale-accent,[data-accent],iframe').length};
 });
 assert.equal(actual.cjk,false,'Film DOM contains non-English glyphs');
 assert.equal(actual.inserts,0,'All motion is native web code');
 assert.equal(actual.bar.height,12);assert.equal(actual.bar.width,1920);assert.equal(actual.bar.top,844);assert(actual.bar.bottom<=880,'Chapter rail intersects caption lane');
 assert.equal(actual.labels.length,10);assert.equal(actual.segments.length,10);
 assert.equal(actual.labels.filter(l=>l.current).length,1);assert(actual.labels[state.index].current);
 actual.labels.forEach((l,i)=>{assert(l.font>=32);assert(l.left>=0&&l.right<=1920&&l.bottom<=844);if(i)assert(l.left>=actual.labels[i-1].right-1,'Chapter labels overlap');});
 actual.segments.forEach((s,i)=>{assert(Math.abs(s.width-1920*state.chapters[i].duration_s/178)<1);assert(Math.abs(s.fill-state.chapters[i].fill)<.001);});
 if(state.index===1)assert.equal(actual.copies,7);
 if(state.index===2)assert.equal(actual.tiles,4);
 if(actual.video){assert.deepEqual(actual.video.source,[1920,1080]);assert.equal(actual.video.fit,'contain');assert.equal(actual.video.transform,'none');assert.equal(actual.video.left,0);assert.equal(actual.video.top,0);assert.equal(actual.video.right,1920);assert.equal(actual.video.bottom,1080);}
 if(state.index===5&&state.overlay){assert.equal(actual.overlay?.phase,state.overlay.receipt_phase);assert(actual.overlay.bottom<790);assert(actual.overlay.fonts.every(x=>x>=56));assert(actual.overlay.keyFonts.every(x=>x>=96),'Key numbers must be at least 96 px');assert(actual.overlay.scroll<=actual.overlay.client+2,'Live explanation overflows');}
 return actual;
}
