/** Capture geometry in delivery pixels; the lower mask joins the rail at y=790. */
export const cardBands={bottom:{left:80,right:1840,top:558,bottom:790},top:{left:80,right:1840,top:24,bottom:250}};
export function crossesCardEdge(rect,band=cardBands.bottom){
 const edges=band.top===558?[band.top]:[band.top,band.bottom];
 return rect.left<band.right&&rect.right>band.left&&edges.some(y=>rect.top<y&&rect.bottom>y);
}
export function assertCardFrame(audit,band=cardBands.bottom,{verdict=false}={}){
 if(!audit?.lines?.length||!Array.isArray(audit.controls))throw new Error('native_text_line_audit_missing');
 if([...audit.lines,...audit.controls].some(r=>crossesCardEdge(r,band)))throw new Error('native_text_crosses_card_edge');
 if(verdict){
  if(!audit.input_charge||audit.input_charge.bottom>0)throw new Error('input_reading_charge_in_verdict_view');
  const h=audit.corrected_heading;
  if(!h||!(h.top>=band.top||h.top>=0&&h.bottom<=band.top))throw new Error('corrected_heading_split_or_clipped');
 }
}
/** Find the nearest line gap while preserving the entire named native proof. */
export function cardScrollDelta(audit,elements,scroll,maxScroll,{verdict=false}={}){
 let low=Math.max(-scroll,...elements.map(r=>r.bottom-548));
 let high=Math.min(maxScroll-scroll,...elements.map(r=>r.top-80));
 if(verdict){
  if(!audit.input_charge||!audit.corrected_heading)throw new Error('verdict_surroundings_missing');
  low=Math.max(low,audit.input_charge.bottom+2);
 }
 const rects=[...audit.lines,...audit.controls,...(verdict?[audit.corrected_heading]:[])];
 const candidates=[Math.max(low,Math.min(high,0)),low,high,
  ...rects.flatMap(r=>[r.top-cardBands.bottom.top-2,r.bottom-cardBands.bottom.top+2])];
 const shifted=(r,d)=>({...r,top:r.top-d,bottom:r.bottom-d});
 for(const d of candidates.filter(d=>d>=low&&d<=high).sort((a,b)=>Math.abs(a)-Math.abs(b))){
  try{
   assertCardFrame({...audit,lines:audit.lines.map(r=>shifted(r,d)),controls:audit.controls.map(r=>shifted(r,d)),
    input_charge:audit.input_charge&&shifted(audit.input_charge,d),corrected_heading:audit.corrected_heading&&shifted(audit.corrected_heading,d)},cardBands.bottom,{verdict});
   return d;
  }catch{}
 }
 throw new Error('no_clean_card_band_for_native_state');
}
/** Serialized into the recorder page. Keep every browser dependency local. */
export function readCardFrame(){
 const box=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom});
 const underCover=document.querySelector('#capture-boot-cover')&&document.documentElement.dataset.captureReady!=='true';
 const visible=el=>{for(let p=el;p;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||!underCover&&s.visibility==='hidden'||Number(s.opacity)===0)return false;}return true;};
 const lines=[],walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 for(let node;node=walker.nextNode();){
  if(!node.textContent.trim()||['SCRIPT','STYLE','TEXTAREA'].includes(node.parentElement.tagName)||!visible(node.parentElement))continue;
  const range=document.createRange();range.selectNodeContents(node);
  for(const r of range.getClientRects())if(r.width>0&&r.height>0&&r.bottom>-1080&&r.top<2160)lines.push(box(r));
 }
 const controls=[...document.querySelectorAll('#live-form button,#live-form input,#live-input,#live-count')]
  .filter(visible).map(el=>box(el.getBoundingClientRect()));
 const rect=selector=>{const el=document.querySelector(selector);return el&&visible(el)?box(el.getBoundingClientRect()):null;};
 // The receipt's last line is the unrelated input-reading charge, above the verdict.
 return {lines,controls,input_charge:rect('#live-result .live-receipt .live-small'),corrected_heading:rect('#live-result .live-corrections h5')};
}
