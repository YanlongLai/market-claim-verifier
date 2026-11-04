/** Capture geometry in delivery pixels; the lower mask joins the rail at y=790. */
export const cardBands={bottom:{left:80,right:1840,top:558,bottom:790},top:{left:80,right:1840,top:24,bottom:250}};
export function crossesCardEdge(rect,band=cardBands.bottom){
 const edges=band.top===558?[band.top]:[band.top,band.bottom];
 // Sub-pixel tolerance: fractional rect edges must not make a glyph line count as bisected.
 return rect.left<band.right&&rect.right>band.left&&edges.some(y=>rect.top<y-.75&&rect.bottom>y+.75);
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
 // The proof that must stay clear of the card is the element's text, not its padding:
 // use the last text line inside each named element when the audit can see one.
 const proofBottom=r=>{const inside=(audit.lines||[]).filter(l=>l.top>=r.top-1&&l.bottom<=r.bottom+1&&l.left<r.right&&l.right>r.left);
  return inside.length?Math.max(...inside.map(l=>l.bottom)):r.bottom;};
 let low=Math.max(-scroll,...elements.map(r=>proofBottom(r)-548));
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
 // Edge-aligned candidates can all miss by sub-pixel margins; scan the feasible range finely.
 const scan=[];for(let d=Math.ceil(low*2)/2;d<=high;d+=.5)scan.push(d);
 for(const d of scan.sort((a,b)=>Math.abs(a)-Math.abs(b))){
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
 // Under the startup cover the body is visibility:hidden by the cover stylesheet while an
 // opaque fixed layer sits above everything; lifting the body rule during this read lets
 // the audit see the page's own visibility (inactive stamp scenes stay hidden) without
 // exposing a pixel. Visually-hidden labels (clip-path / 1 px overflow) are not text lines.
 const bodyVisibility=document.body.style.getPropertyValue('visibility'),bodyPriority=document.body.style.getPropertyPriority('visibility');
 if(underCover)document.body.style.setProperty('visibility','visible','important');
 const visible=el=>{for(let p=el;p;p=p.parentElement){const s=getComputedStyle(p);
  // Content of a closed <details> (outside its <summary>) is not rendered even though rects exist.
  if(p.tagName==='DETAILS'&&!p.open&&!(el.closest('summary')&&p.contains(el.closest('summary'))&&el.closest('summary').parentElement===p))return false;
  if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0||p.getAttribute?.('aria-hidden')==='true')return false;
  if((s.clipPath&&s.clipPath!=='none')||(s.overflow==='hidden'&&p.getBoundingClientRect().width<=1))return false;}return true;};
 const lines=[],walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 for(let node;node=walker.nextNode();){
  if(!node.textContent.trim()||['SCRIPT','STYLE','TEXTAREA'].includes(node.parentElement.tagName)||!visible(node.parentElement))continue;
  const range=document.createRange();range.selectNodeContents(node);
  for(const r of range.getClientRects())if(r.width>0&&r.height>0&&r.bottom>-1080&&r.top<2160)lines.push({...box(r),text:node.textContent.trim().slice(0,24)});
 }
 const controls=[...document.querySelectorAll('#live-form button,#live-form input,#live-input,#live-count')]
  .filter(visible).map(el=>box(el.getBoundingClientRect()));
 const rect=selector=>{const el=document.querySelector(selector);return el&&visible(el)?box(el.getBoundingClientRect()):null;};
 // The receipt's last line is the unrelated input-reading charge, above the verdict.
 const out={lines,controls,input_charge:rect('#live-result .live-receipt .live-small'),corrected_heading:rect('#live-result .live-corrections h5')};
 if(underCover)document.body.style.setProperty('visibility',bodyVisibility,bodyPriority);
 return out;
}
