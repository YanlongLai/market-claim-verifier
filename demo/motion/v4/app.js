import {stateAt} from './plan.js';
const data=window.MOTION_DATA,stage=document.querySelector('#stage');
const root='../../../';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
let previous='',pending=[];
const video=(path,classes='terminal')=>`<video muted preload="auto" class="${classes}" data-source="${esc(path)}" src="${root}${esc(path)}"></video>`;
const brollPaths={
  'cards-fanning-out':'demo/assets/broll-v4/cards-fanning-out.mp4',
  'numbers-raining-into-filing':'demo/assets/broll-v4/numbers-raining-into-filing.mp4',
};
function body(state){
 const scene=data.scenes[state.index];
 if(state.placeholder)return `<section class="scene placeholder"><div class="kicker">DIRECTOR RECORDING PENDING · ${state.shot}</div><h1>${state.index===5?'Live site run — uncut':'Corrected draft + SEC filing'}</h1><p class="duration">${scene.target_s.toFixed(3)} seconds</p><p>${state.index===5?'Paste → Check → Meta trace → CONTRADICTED → SEC filing → corrected draft':'End on the working result · hackathon.dappgo.com'}</p><p class="note">Exact director duration. No live call, site recording or production receipt has been created for this scene.</p></section>`;
 switch(state.index){
 case 0:return `<iframe class="hero" src="${root}docs/site/index.html" title="Saved local site hero"></iframe><section class="disclosure"><h1>DappGo existed before this hackathon.</h1><p>This verifier, its site and every piece of evidence were built between October 27 and November 4.</p><p class="note">Director disclosure · local site source preview · no live call</p></section>`;
 case 1:return `<section class="scene"><img class="phone" src="${root}${esc(data.phone_post.path)}" alt="Full saved finance post · 28 Oct 2026"><div class="viral-question"><h1>Is it right?</h1><strong id="reposts">0</strong><p class="note">Illustrative repost counter — not measured reach</p><p>A real number.<br>The wrong period.</p></div></section>`;
 case 2:return `<section class="scene"><div class="kicker">REAL SAVED CLI INPUTS · CONTROLLED FIXTURES</div><h1 id="input-label"></h1><div id="input-preview"></div><div class="input-details"><p>One verification path.</p><p>Extract claims → SEC tools → Python verdict</p><code id="input-path"></code><p class="note">fair-multimodal-v1 · saved inputs and outputs<br>Not a new OCR/ASR execution.</p></div></section>`;
 case 3:return video('demo/assets/terminal-v4/beat4.mp4');
 case 4:return `<div class="architecture">${data.architecture_svg}</div>`;
 case 6:return video('demo/assets/terminal-v4/beat7.mp4');
 case 7:{const m=data.metrics;return `<section class="scene"><div class="kicker">ORIGINAL V2 · BASETEN · CORRECTED REFERENCE LABELS</div><h1>Held-out text claims</h1><div class="metrics"><div class="metric"><strong>${(100*m.heldout_correct/m.heldout_n).toFixed(1)}%</strong><span>${m.heldout_correct}/${m.heldout_n} correct</span></div><div class="metric"><strong>${m.false_support}/${m.negative_n}</strong><span>false support</span></div><div class="metric"><strong>$${m.mean_cost_usd.toFixed(2)}</strong><span>mean cost / claim</span></div><div class="metric"><strong>${Math.round(m.median_claim_seconds)} s</strong><span>median / claim</span></div></div><p class="results-note">Real posts: coverage ≠ accuracy.</p><p class="note">Saved benchmark text · failures count as wrong · not a guarantee on every post</p></section>`;}
 default:throw new Error('Unknown v4 scene');
 }
}
function seekVideo(el,time){
 const wait=()=>new Promise((resolve,reject)=>{
  const target=Math.max(0,Math.min(time,el.duration-1/30));
  if(Math.abs(el.currentTime-target)<.0001){
   if(el.readyState>=2)return resolve();
   el.addEventListener('loadeddata',resolve,{once:true});return;
  }
  el.addEventListener('seeked',resolve,{once:true});
  el.addEventListener('error',()=>reject(new Error(`Missing recorded asset: ${el.dataset.source}`)),{once:true});
  el.currentTime=target;
 });
 const task=el.readyState>=1?wait():new Promise((resolve,reject)=>{
  el.addEventListener('loadedmetadata',()=>wait().then(resolve,reject),{once:true});
  el.addEventListener('error',()=>reject(new Error(`Missing recorded asset: ${el.dataset.source}`)),{once:true});
 });
 pending.push(task);
}
window.seek=t=>{
 const state=stateAt(t);pending=[];
 if(previous!==state.shot){stage.innerHTML=body(state);previous=state.shot;}
 if(state.index===1)document.querySelector('#reposts').textContent=Math.floor(Math.min(1,state.local/12)*1000).toLocaleString('en-US');
 if(state.index===2){
  const index=Math.min(3,Math.floor(state.local/3.5)),input=data.inputs[index];
  document.querySelector('#input-label').textContent=input.label;
  document.querySelector('#input-path').textContent=`claimcheck ingest ${input.path}`;
  const preview=document.querySelector('#input-preview');
  if(preview.dataset.index!==String(index)){
   preview.dataset.index=index;
   if(index===0)preview.innerHTML=`<img class="input-view" src="${root}${input.path}" alt="Recorded financial-claim screenshot fixture">`;
   else if(index===1)preview.innerHTML=`<img class="input-view" src="${root}eval/multimodal-v1/inputs/MSFT/input.png" alt="Original text shown in the recorded PDF"><p class="note" style="position:absolute;top:820px">Native-text PDF uses this same frozen source text.</p>`;
   else if(index===2)preview.innerHTML=`<div class="input-view"><div class="wave">${input.waveform.map(v=>`<i style="height:${8+v*220}px"></i>`).join('')}</div><p class="note">Waveform from the retained synthetic test audio<br>Recorded Muse Voice ASR; no speaker identity claim.</p></div>`;
   else preview.innerHTML=video(input.path,'input-view');
  }
 }
 if(state.architecture){
  state.architecture.nodes.forEach((v,i)=>document.querySelector(`#node-${i}`).style.opacity=v);
  state.architecture.links.forEach((v,i)=>document.querySelector(`#link-${i}`).style.opacity=v);
 }
 const accent=stage.querySelector('[data-accent]');
 if(state.broll){
  if(!accent){const holder=document.createElement('div');holder.dataset.accent=state.broll;
   holder.innerHTML=video(brollPaths[state.broll],state.index===6?'scale-accent':'accent');
   const media=holder.querySelector('video');media.addEventListener('error',()=>{holder.innerHTML=`<div class="accent-status">480 TEST B-ROLL PENDING<br>${state.broll}</div>`;},{once:true});stage.append(holder);
  }
 }else accent?.remove();
 for(const el of stage.querySelectorAll('video')){
  const isAccent=el.closest('[data-accent]');
  seekVideo(el,isAccent?state.local-(state.index===1?14:8):state.index===2?state.local-10.5:state.local);
 }
 return state;
};
window.settleMotion=async()=>{await Promise.all(pending);};
window.timeline=data.timing;window.motionReady=true;window.seek(0);
