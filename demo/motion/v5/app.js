import {stateAt,terminalAt,outroStampAt} from './plan.js';
import {chapterMarkup,updateChapters} from './chapters.js';
import {paintVideoFrame} from './video-frame.mjs';
import {liveTerminalAt,localTerminalAt} from './live-terminal.mjs';
const data=window.MOTION_DATA,stage=document.querySelector('#stage'),root='../../../';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
let previous='',pending=[];
const video=(path,classes='terminal')=>`<video muted preload="auto" class="${classes}" data-source="${esc(path)}" src="${root}${esc(path)}"></video><canvas class="native-video-frame" width="1920" height="1080" aria-label="Decoded native page"></canvas>`;
const post=()=>`<article class="post-card"><p class="post-byline">Illustrative post</p>${data.post_text.split('\n\n').map((p,i)=>i===0?`<h2>${esc(p)}</h2>`:`<p class="post-paragraph${p.includes('Apple')?' apple-line':''}">${esc(p)}</p>`).join('')}<p class="post-focus"><strong>$416.2 billion</strong><br>… fiscal Q4 2025</p></article>`;
function terminalMarkup(state,trace,classes='',cue=''){
 return `<aside class="terminal-window ${classes}" data-phase="check_against_sec" data-cue="${esc(cue)}" aria-label="${esc(trace.title)}">
 <header><span class="terminal-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="live-terminal-title">${esc(trace.title)}</span><time class="live-stopwatch" data-running="${state.running}">${state.clock}</time></header>
 <div class="live-terminal-lines">${state.rows.map(row=>`<div class="live-terminal-line" data-kind="${row.kind}">${esc(row.text)}${row.kind==='reasoning'?`<span class="live-terminal-cursor" style="visibility:${state.cursor?'visible':'hidden'}">▎</span>`:''}</div>`).join('')}</div><footer>${esc(trace.honesty_label)}</footer></aside>`;
}
function liveOverlay(event,local){
 const terminal=liveTerminalAt(local,data.live_terminal);
 if(terminal)return terminalMarkup(terminal,data.live_terminal,'live-overlay live-terminal',event?.receipt_phase==='check_against_sec'?event.event:'');
 if(!event)return '';
 const titles={draft:'4 · Corrected draft',evidence:'5 · SEC evidence',trace:'6 · Agent trace',each:'6 · Each tool call',program:'6 · Program verdict',receipt:'7 · Live take'};
 if(event.event==='verdict')titles.verdict='3 · Contradicted · Apple SEC · E3';
 const items=event.event==='draft'?'<p class="principal"><strong>$416.2B → $102.5B</strong></p>':event.event==='evidence'?'<div class="equation"><p><span>10-K annual</span><strong>$416.2B</strong></p><b>−</b><p><span>10-Q nine months</span><strong>$313.7B</strong></p><b>=</b><p><span>Fiscal Q4</span><strong>$102.5B</strong></p></div>':event.event==='trace'?`<p class="principal"><strong>${data.live_receipt?data.live_receipt.tool_calls:4}</strong> tool calls · on the record</p>`:event.event==='receipt'?`<p class="principal">${data.live_receipt?`<strong>$${data.live_receipt.cost_usd.toFixed(4)}</strong> · <strong>${(data.live_receipt.latency_ms/1000).toFixed(1)} s</strong>`:'Measured cost · elapsed time · capture pending'}</p>`:'';
 const binding=data.cues._events.v505.find(e=>e.event===event.event);
 const native=binding?.native_check;
 // The recorder reserves one of two full bands. Audit both speech boundaries
 // against its rectangles; never infer clearance from overlay opacity.
 const top=native?.overlay_band==='top';
 const filings=event.event==='verdict'?(data.live_filing_citations||[]).map(c=>`<a class="filing-citation" data-evidence-id="${esc(c.evidence_id)}" data-form="${esc(c.form)}" href="${esc(c.url)}">${esc(c.form)} · ${esc(c.period_label)}</a>`).join(''):'';
 return `<aside class="live-overlay${top?' top-band':''}" data-phase="${event.receipt_phase}" aria-label="${esc(event.overlay)}">${event.event==='evidence'?'':`<h2>${esc(titles[event.event]||event.overlay)}</h2>`}${items}${filings}</aside>`;
}
function body(state){
 const scene=data.scenes[state.index];
 if(state.liveTake){
  const picture=scene.recording?video(scene.recording.asset,'live-take'):`<div class="pending"><h1>Host live capture pending</h1><p>${state.index===5?'One real check · sentence-bound receipt phases':'Corrected draft · both SEC filing links'}</p><p>Layout preview · no new live result</p></div>`;
  return `<section class="live-take-frame">${picture}<div class="live-backplate${state.index===8?' ending-backplate':''}" aria-hidden="true"></div>${state.index===5?'<div id="live-overlay"></div>':'<aside class="live-overlay ending"><h2>Every number, checked against the filing.</h2></aside><span class="site-url">hackathon.dappgo.com</span>'}</section>`;
 }
 switch(state.index){
 case 0:return `<section class="scene brand intro"><div class="brand-rule"></div><p class="wordmark">${esc(data.brand.wordmark)}</p><h1>${esc(data.brand.title)}</h1><p class="origin">DappGo existed before this hackathon.</p><p class="disclosure" data-on-screen="${scene.id}">${esc(scene.on_screen)}</p></section>`;
 case 1:return `<section class="scene viral"><div class="cascade" aria-hidden="true">${state.cascade.map(()=>`<div class="post-copy">${post()}</div>`).join('')}</div><div class="post-original">${post()}</div><h1 class="viral-headline">A real number.<br>The wrong period.</h1></section>`;
 case 2:return `<section class="scene inputs"><h1 class="inputs-headline">More than text.</h1><h1 class="inputs-question">How do you check all of them?</h1><div class="input-tiles">${data.inputs.map(i=>`<article class="input-tile"><div class="asset-preview">${i.type==='audio'?`<div class="waveform" aria-label="Waveform from a.mp3">${data.waveform.map(v=>`<i style="height:${8+v*210}px"></i>`).join('')}</div>`:`<img src="${root}${i.preview}" alt="${esc(i.label)} preview from ${esc(i.source)}">`}</div><h2>${i.label}</h2></article>`).join('')}</div></section>`;
 case 3:return '<section class="scene terminal-scene"><div id="terminal-rows"></div><p class="terminal-caption" id="batch-block"></p></section>';
 case 4:return `<div class="architecture">${data.architecture_svg}</div>`;
 case 6:return '<section class="scene terminal-scene"><div id="local-terminal"></div><div id="terminal-rows"></div><p class="terminal-caption" id="batch-block"></p></section>';
 case 7:{const m=data.metrics;return `<section class="scene results"><h1>Held-out text claims</h1><div class="metrics"><div class="metric" data-metric="accuracy"><strong>${(100*m.heldout_correct/m.heldout_n).toFixed(1)}%</strong><span>${m.heldout_correct}/${m.heldout_n} correct</span></div><div class="metric" data-metric="false_support"><strong>${m.false_support}/${m.negative_n}</strong><span>non-supported claims<br>wrongly supported</span></div><div class="metric" data-metric="cost_time"><strong>$${m.mean_cost_usd.toFixed(2)}</strong><span>mean / claim</span></div><div class="metric" data-metric="cost_time"><strong>${Math.round(m.median_claim_seconds)} s</strong><span>median / claim</span></div></div><p class="results-note">Real posts: coverage ≠ accuracy.</p><p class="provenance">Original v2 · Baseten · corrected gold · failures count as wrong</p></section>`;}
 case 9:return `<section class="scene brand outro"><div class="brand-rule"></div><div class="outro-stamp" aria-label="Site auditor robot stamps the sign-off"><div class="stamp-imprint" aria-label="Completed stamp">DappGo</div><div class="stamp-robot">${Object.entries(data.brand_motion.poses).map(([pose,src])=>`<img data-pose="${pose}" src="${root}${src}" alt="">`).join('')}</div></div><h1>${esc(data.brand.url)}</h1><p class="credit">${esc(data.brand.credit)}</p><p class="wordmark">${esc(data.brand.wordmark)}</p></section>`;
 default:throw new Error('Unknown v5 scene');
 }
}
function seekVideo(el,time){
 pending.push(paintVideoFrame(el,time,el.nextElementSibling));
}
window.seek=t=>{
 pending=[];const state=stateAt(t,data.scenes,data.chapter_bar.segments);
 if(state.shot!==previous){stage.innerHTML=body(state);previous=state.shot;}
 const overlay=document.querySelector('#live-overlay');if(overlay)overlay.innerHTML=liveOverlay(state.overlay,state.local);
 const plate=document.querySelector('.live-backplate');if(plate){
  // The recorded password form persists until the POST; extend only that state.
  const password=state.index===5&&state.local<(data.live_terminal?.start_scene_s??0);
  plate.dataset.state=password?'password':'normal';
 }
 const rows=document.querySelector('#terminal-rows');if(rows){
  const local=state.index===6?localTerminalAt(state.local,data.local_terminal):null;
  const localWindow=document.querySelector('#local-terminal');if(localWindow)localWindow.innerHTML=local?terminalMarkup(local,data.local_terminal,'local-terminal'):'';
  rows.style.display=local?'none':'';
  const terminal=terminalAt(state.local,data.terminal_replays[state.index===3?'beat3':'beat6']);
  rows.innerHTML=terminal.rows.map(row=>`<p data-row="${row.row}" class="terminal-row${row.principal?' principal':''}">${esc(row.text)}</p>`).join('');
  const block=document.querySelector('#batch-block');block.textContent=data.batch_labels[state.index===3?'comparison':local?'run':terminal.block];block.dataset.block=local?'run':terminal.block;
 }
 if(state.cascade)stage.querySelectorAll('.post-copy').forEach((el,i)=>{const s=state.cascade[i];el.style.cssText=`transform:translate(${s.x}px,${s.y}px) rotate(${s.rotation}deg) scale(${s.scale});opacity:${s.opacity}`;});
 if(state.inputs)stage.querySelectorAll('.input-tile').forEach((el,i)=>{el.style.transform='none';el.style.opacity=1;});
 if(state.architecture){state.architecture.nodes.forEach((v,i)=>document.querySelector(`#node-${i}`).style.opacity=v);state.architecture.links.forEach((v,i)=>document.querySelector(`#link-${i}`).style.opacity=v);}
 stage.dataset.active=state.active||'';
 const visible=(selector,yes)=>{const el=stage.querySelector(selector);if(el){el.style.opacity=Number(Boolean(yes));el.style.visibility=yes?'visible':'hidden';}};
 visible('.disclosure',state.buildDisclosure);visible('.origin',!state.buildDisclosure);
 const viral=stage.querySelector('.viral');if(viral){viral.classList.toggle('focus-period',state.postFocus);viral.querySelector('.viral-headline').innerHTML=state.active==='question'?'Is it right?':state.active==='stakes'?'Numbers<br>move money.':'A real number.<br>The wrong period.';}
 if(state.inputs){stage.querySelectorAll('.input-tile').forEach((el,i)=>el.classList.toggle('lit',state.inputs[i]));visible('.inputs-question',state.question);visible('.inputs-headline',!state.question);}
 if(state.results){stage.querySelectorAll('[data-metric]').forEach(el=>{const yes=state.results[el.dataset.metric];el.classList.toggle('lit',yes);el.style.visibility=yes?'visible':'hidden';});visible('.results-note',state.results.coverage);}
 visible('.site-url',state.url);visible('.outro .wordmark',state.wordmark);
 const heading=stage.querySelector('.architecture [data-on-screen]');if(heading){heading.style.opacity=Number(state.architecture.headline);heading.style.visibility=state.architecture.headline?'visible':'hidden';}
 const brand=stage.querySelector('.brand');if(brand){brand.style.opacity=state.fade;brand.style.setProperty('--reveal',1);}
 const stamp=stage.querySelector('.outro-stamp');if(stamp){
  const motion=outroStampAt(Math.max(0,state.local-(data.scenes[9].cue_events.find(e=>e.event==='wordmark').picture_at_scene_s))),robot=stamp.querySelector('.stamp-robot');
  robot.dataset.pose=motion.pose;robot.style.transform=`translateY(${motion.dip}px) rotate(${motion.lean}deg)`;
  robot.querySelectorAll('img').forEach(img=>{img.style.opacity=Number(img.dataset.pose===motion.pose);});
  const ink=stamp.querySelector('.stamp-imprint');ink.style.opacity=motion.ink;ink.style.transform=`scale(${.9+.1*motion.ink}) rotate(-8deg)`;
 }
 for(const el of stage.querySelectorAll('video'))seekVideo(el,state.local+(data.scenes[state.index].recording?.offset_s||0));
 updateChapters(state);return state;
};
document.querySelector('#chapter-layer').innerHTML=chapterMarkup(data.chapter_bar.segments);
window.settleMotion=async()=>{await Promise.all(pending);await document.fonts.ready;};
window.timeline=data.timing;window.motionReady=true;window.seek(0);
