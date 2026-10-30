/* Synchronous, frame-addressable product reenactment of committed run reports. */
(function () {
  'use strict';
  const D=window.MOTION_DATA,L=window.MotionLogic,H=window.HoverSource;
  const stage=document.getElementById('stage'), P=D.product.base;
  const {escapeHTML:esc,highlightQuote:quote,clamp,progress}=L;
  const beat=L.beatHelpers(D.beats.beats_s);
  const ASSET='../../../docs/site/img/';
  let boxes=[];
  const plain=s=>String(s).replace(/<[^>]*>/g,'').replace(/&[^;]+;/g,' ');
  function box(x,y,w,h,html,cls='body',size=64,extra='') {
    boxes.push({x,y,w,h,text:plain(html),className:cls,size});
    return `<div class="abs ${cls}" data-fit="${cls.includes('surface')?'panel':'text'}" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;font-size:${size}px;${extra}">${html}</div>`;
  }
  const n=(value,size=112)=>`<span class="number" style="font-size:${size}px">${esc(value)}</span>`;
  const dollars=(value,decimals=1)=>'$'+value.toFixed(decimals)+'B';
  const surface=(x,y,w,h)=>box(x,y,w,h,'','product-surface',64);
  const title=text=>box(64,188,1792,128,esc(text),'headline',104);
  const show=(t,e,name)=>t>=e[name];
  const verdict=v=>({supported:'TRUE',contradicted:'FALSE',insufficient_evidence:'INSUFFICIENT'})[v];
  function chrome(label) {
    return box(64,64,850,72,esc(label),'body mint',56)+
      box(1050,64,806,72,'Market Claim Verifier','body muted',56,'text-align:right')+
      box(64,148,1792,2,'','rule',64);
  }
  function disclosure() {
    return chrome('Built during the hackathon')+
      box(64,184,1792,400,esc(D.product.disclosure),'body disclosure',64)+
      surface(64,600,1792,264)+
      box(96,612,1040,232,'Market Claim<br><span class="mint">Verifier</span>','headline',96)+
      box(1192,608,632,72,'Apple · claimed quarter','body muted',56)+
      box(1192,680,632,116,n(dollars(P.apple.claimed_b),96),'coral',96)+
      box(1192,796,632,68,'Open saved check ↗','body mint',56);
  }
  function apple(t,s,e) {
    return chrome('Paste a post')+title('Apple. One quarter?')+
      surface(64,332,1792,390)+
      box(96,360,1728,80,'Post · exact source quote','body muted',56)+
      box(96,470,1728,244,quote(P.english_claims[2].quote),'source-text',72)+
      box(64,758,1792,106,show(t,e,'paste')?'Post pasted → extract claims':'Check the period before sharing.','body mint',64);
  }
  function extract(t,s,e) {
    const b=D.beats.beats_s.filter(b=>b>=s.start&&b<s.end),
      index=show(t,e,'opinion')?3:t>=b[8]?2:t>=b[4]?1:0,
      claim=P.english_claims[index];
    return chrome('Extract claims')+title('Keep the exact quote.')+
      surface(64,332,1792,430)+
      box(96,360,1728,80,esc(claim.ticker||'NVDA')+' · '+(index===3?'opinion':'checkable claim'),'body muted',64)+
      box(96,480,1728,250,quote(claim.quote),'source-text',72)+
      box(64,794,1792,70,index===3?'Opinion · not judged':'Quote + company + period → SEC lookup','body '+(index===3?'muted':'mint'),56);
  }
  function siteAge(t) {
    const anchors=D.hover_anchors;
    if(t<=anchors[0][0])return 0;
    for(let i=1;i<anchors.length;i++) if(t<=anchors[i][0]){
      const [a,b]=[anchors[i-1],anchors[i]];
      return a[1]+(b[1]-a[1])*clamp((t-a[0])/(b[0]-a[0]));
    }
    return anchors.at(-1)[1];
  }
  function hover(t,s,e) {
    const year={x:480,y:464,width:608,height:138},quarter={x:1184,y:464,width:640,height:138},
      targets={post:year,row:year,quarter,compare:{x:1184,y:632,width:640,height:74},
        search:[year,{x:1184,y:354,width:640,height:74},quarter]};
    const age=siteAge(t),state=H.state(age,{excerpt:true,status:'verified',verdict:P.apple.verdict},(t-s.start)*1000,targets);
    const struck=show(t,e,'strike'),cmp=show(t,e,'compare'),
      ratio=show(t,e,'ratio')||(e.ratio===undefined&&struck); // Older committed preview has no ratio event.
    const x=64,y=356,w=352,h=372, visor={x:x+w*state.visor[0],y:y+h*state.visor[1]};
    const images=[state.previous,state.pose].map((pose,i)=>`<img class="hover-pose" src="${ASSET}auditor/H/${pose}.webp" alt="" style="opacity:${i?state.blend:1-state.blend};transform:scaleX(${pose==='stamp'||pose==='stamp-down'||pose==='inspect'?-1:1})">`).join('');
    const thruster=state.thruster==='burst'?'burst':state.thruster;
    const beams=[['filing',state.filingTarget,state.filingAlpha,visor],
      ['post',targets.post,state.postAlpha,visor],
      ['year',targets.row,state.yearAlpha,{x:quarter.x+quarter.width/2,y:quarter.y+quarter.height/2}]]
      .map(([name,target,alpha,origin])=>`<polygon data-beam="${name}" points="${H.conePoints(origin,target,4)}" fill="url(#beam)" opacity="${alpha}"/>`).join('');
    let html=chrome('Hover · SEC audit')+title('The year is not the quarter.')+
      surface(448,332,672,408)+surface(1152,332,704,408)+
      `<img class="abs texture" style="left:448px;top:332px;width:1408px;height:408px" src="${ASSET}stamp-paper.webp" alt="">`+
      `<svg class="spotlight" viewBox="0 0 1920 880" aria-hidden="true"><defs><mask id="stage-hole"><rect x="448" y="332" width="1408" height="408" fill="white"/><rect x="464" y="440" width="640" height="190" rx="16" fill="black"/><rect x="1168" y="440" width="672" height="190" rx="16" fill="black"/></mask></defs><rect x="448" y="332" width="1408" height="408" fill="#050b10" mask="url(#stage-hole)" opacity="${state.shade*.65}"/></svg>`+
      `<img class="abs fx" src="${ASSET}fx/beam-pool.webp" alt="" style="left:1168px;top:440px;width:672px;height:190px;opacity:${state.postAlpha*.16}">`+
      box(480,354,608,74,'Apple · full FY2025','body muted',56)+
      box(1184,354,640,74,'Apple · fiscal Q4 2025','body muted',56)+
      box(480,464,608,138,n(dollars(P.apple.full_year_b)),'muted',112)+
      box(1184,464,640,138,n(dollars(P.apple.quarter_b)),'mint',112)+
      box(480,632,608,74,'Claim uses the full year','body muted',56)+
      box(1184,632,640,74,'Filed quarter','body mint',56)+
      box(448,742,672,122,ratio?n('≈'+Math.round(P.apple.claimed_b/P.apple.quarter_b)+'×',96)+' too high':'Compare periods','body amber',64)+
      box(1152,744,704,120,struck?'Claim: '+verdict(P.apple.verdict):cmp?'Program compares…':'SEC proof → program','status '+(struck?'claim-verdict coral':'muted'),struck?80:56)+
      `<svg class="spotlight" viewBox="0 0 1920 880" aria-hidden="true"><defs><linearGradient id="beam"><stop stop-color="#d9a74a" stop-opacity=".04"/><stop offset="1" stop-color="#d9a74a" stop-opacity=".2"/></linearGradient></defs>${beams}<rect data-find-lock="${state.locked}" x="${state.row.x-12}" y="${state.row.y-12}" width="${state.row.width+24}" height="${state.row.height+24}" rx="12" fill="none" stroke="#d9a74a" stroke-width="4" opacity="${state.filingAlpha}"/></svg>`+
      box(128,724,224,24,'','hover-shadow',64)+
      `<div class="abs" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;transform:${state.transform}">${images}</div>`+
      `<img class="abs fx" src="${ASSET}fx/lens-flare.webp" alt="" style="left:${visor.x-64}px;top:${visor.y-10}px;width:128px;height:20px;opacity:${Math.max(state.postAlpha,state.filingAlpha)*.45}">`+
      `<img class="hover-thruster" src="${ASSET}auditor/H/thruster-${thruster}.webp" alt="" style="left:${x+w*state.nozzle[0]/704-40}px;top:${y+h*state.nozzle[1]/744-10+state.bob+state.dip}px;transform:scale(${thruster==='burst'?1.6:1})">`;
    return {html,state:{...state,siteAge:age,struck}};
  }
  function proof(t,s,e) {
    const F=P.filing;
    return chrome('Open SEC proof')+title('The row. The period. The source.')+
      `<div class="table-window" data-fit="panel"><div class="filing-table"><div class="table-group">USD millions</div><div class="table-group" style="grid-column:2 / 4">Three Months Ended</div><div></div><div class="table-year">${esc(F.years[0])}</div><div class="table-year">${esc(F.years[1])}</div><div class="table-cell row-label"><span>Total net<br>sales</span></div><div class="table-cell"><span>${esc(F.values[0])}</span><div class="filing-highlight" style="clip-path:inset(0 ${100*(1-progress(t,e.sweep,.5))}% 0 0)">${esc(F.values[0])}</div></div><div class="table-cell"><span>${esc(F.values[1])}</span></div></div></div>`+
      box(64,756,1792,108,`Amazon · ${esc(F.form)} · <a href="${esc(F.url)}">Open original filing ↗</a>`,'body mint',56);
  }
  function program(t,s,e) {
    const checked=show(t,e,'checks');
    return chrome('Program audit')+title('Model proposes. Program decides.')+
      surface(64,332,1792,532)+
      box(96,368,330,116,'Number','body muted',64)+
      box(440,344,1384,142,checked?'<span class="coral">'+n(dollars(P.apple.claimed_b))+'</span> ≠ <span class="mint">'+n(dollars(P.apple.quarter_b))+'</span>':'Reading source number…','body',64)+
      box(96,514,330,112,'Period','body muted audit-row',64)+
      box(440,514,1384,112,'FY2025 · fiscal Q4','body audit-row',64)+
      box(96,680,848,112,'Citations: '+esc(D.product.apple_evidence_ids.join(' · ')),'body muted audit-row',64)+
      box(992,680,832,112,show(t,e,'verdict')?'Claim: '+verdict(P.apple.verdict):'Program checks…','status '+(show(t,e,'verdict')?'claim-verdict coral':'muted'),80);
  }
  function l4(t,s,e) {
    const r=D.product.releases[show(t,e,'adobe')?1:0],meta=r.kind==='guidance',src=r.excerpt.source_evidence;
    return chrome('L4 · furnished / unaudited')+title('Earnings releases.')+
      surface(64,332,1792,532)+
      box(96,352,1728,88,meta?'META · revenue guidance':'Adobe · non-GAAP diluted EPS','body',72)+
      box(96,448,1728,72,esc(src.period)+' · Regression example','body muted',56)+
      box(96,532,1728,98,meta?'“We expect third quarter 2025 total revenue”':'“Non-GAAP diluted net income per share”','body',64)+
      box(96,642,1728,136,meta?n(r.excerpt.value):n('$'+src.value.toFixed(2)),'mint',112)+
      box(96,796,1728,68,show(t,e,'caution')?'Company-furnished · unaudited · not future performance':'MATCHES RELEASE · source passage retained','body '+(show(t,e,'caution')?'amber':'mint'),56);
  }
  function input(t,s,e,audio) {
    const R=D.product.inputs[audio?'audio':'screenshot'],checked=show(t,e,'checked');
    let html=chrome('Self-made test media')+title(audio?'Synthetic audio → SEC check':'Screenshot → SEC check');
    if(audio) {
      const bars=D.product.waveform.map((peak,i)=>`<rect x="${i*27}" y="${48-peak*45}" width="14" height="${Math.max(2,peak*90)}" rx="4" fill="${i/D.product.waveform.length<clamp((t-s.start)/(s.end-s.start))?'#3ddc97':'#b5c4cd'}"/>`).join('');
      html+=`<svg class="abs" style="left:64px;top:324px;width:1792px;height:96px" viewBox="0 0 1792 96" aria-label="Waveform measured from the self-made eSpeak test WAV">${bars}</svg>`;
      html+=box(64,432,1792,204,quote(D.product.inputs.audio.display_quote),'source-text',64);
    } else {
      html+=box(64,328,1792,72,'Apple · fiscal Q3 2025 · EPS source crop','body muted',56)+
        // Original 1000×620 PNG, source rectangle (244,306)..(692,354), enlarged 4×.
        // Its 29 px source type becomes 116 px; unrelated revenue text is outside the viewport.
        `<div class="abs source-crop" data-source-font-size="29" data-source-number="$1.67" style="left:64px;top:420px;width:1792px;height:192px"><img style="left:-976px;top:-1224px;width:4000px;height:2480px" src="../../../tests/fixtures/multimodal/example-post.png" alt="Magnified self-made source: diluted EPS of $1.67 for fiscal Q3"></div>`;
    }
    const x=64,w=1792,y=636;
    html+=surface(x,y,w,152)+
      box(x+24,y+12,w-48,140,'<span class="coral">'+n('$'+R.check.stated_value_used.toFixed(2))+'</span> → '+(checked?'<span class="mint">'+n('$'+R.check.actual_value.toFixed(2))+'</span>':'SEC check…'),'body',80)+
      box(x,796,w,68,esc(R.period_label)+' · '+(audio?'eSpeak test · speaker unverified':(show(t,e,'verdict')?'CONTRADICTED':'OCR quote → program check')),'body '+(checked?'coral':'muted'),56);
    return html;
  }
  function results(t,s,e) {
    let html=chrome('Saved v2 results')+
      box(64,188,1040,128,'Measured accuracy.','headline',104)+
      box(1132,188,724,124,n(P.claim_count,96)+' claims','body muted',56)+
      box(64,320,1792,72,'Original v2 · includes dev / corrected gold','body muted',56)+
      surface(64,416,1792,448)+
      box(96,428,650,70,'Muse Spark','body muted',56)+
      box(830,428,430,70,'Model alone','body muted',56)+
      box(1344,428,480,70,'With checks','body mint',56);
    for(const [i,row] of D.product.scores.entries()) {
      const y=510+i*116,visible=show(t,e,i===0?'meta':'open');
      html+=box(96,y,650,104,esc(row.label),'body',64)+
        box(830,y,430,118,n(row.alone.percent.toFixed(1)+'%',96),'muted',96)+
        box(1344,y,480,118,visible?n(row.checked.percent.toFixed(1)+'%',96):'SEC + checks','mint',56);
    }
    return html;
  }
  function limits() {
    const R=D.product.recall,{live,frozen_asr:frozen}=R.coverage;
    let html=chrome('Saved development probes')+title('The limits stay visible.')+
      surface(64,332,1792,532);
    for(const [i,kind] of ['text','screenshot','audio'].entries()) {
      const row=D.product.inputs[kind],x=96+i*576;
      html+=box(x,340,552,80,kind==='text'?'Text control':kind==='audio'?'Audio':'Screenshot','body',64)+
        box(x,420,552,68,`<a href="../../../${esc(row.source)}">${esc(row.verdict.toUpperCase())}</a>`,'body coral',56);
    }
    return html+
      box(96,488,1728,68,'Long-call coverage · guarded / checked','body muted',56)+
      box(96,556,848,88,`<a href="../../../${esc(live.source)}">${esc(live.program_checked+'/'+live.expected)}</a>`,'body amber',72)+
      box(96,644,848,68,'· full-media audio','body amber',56)+
      box(976,556,848,88,`<a href="../../../${esc(frozen.source)}">${esc(frozen.program_checked+'/'+frozen.expected)}</a>`,'body amber',72)+
      box(976,644,848,68,'· frozen-ASR text recheck','body amber',56)+
      box(96,712,1728,68,'Post-hoc development probe · coverage ≠ verdict accuracy','body muted',56)+
      box(96,780,800,68,'Speaker labels: '+(R.speaker_identity.verified?'verified':'unverified'),'body',56)+
      box(920,780,904,68,'L4: regression test · not held out','body muted',56);
  }
  function qrSVG() {
    const {matrix,quiet_zone:q}=D.qr,size=matrix.length+2*q;
    const d=matrix.flatMap((row,y)=>[...row].flatMap((bit,x)=>bit==='1'?[`M${x+q},${y+q}h1v1h-1z`]:[])).join('');
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" aria-label="QR code for ${esc(D.qr.url)}" shape-rendering="crispEdges"><rect width="${size}" height="${size}" fill="#fff"/><path d="${d}" fill="#000"/></svg>`;
  }
  function cta() {
    return chrome('Explore the saved demo')+title('Check before you share.')+
      box(64,428,1344,112,esc(D.qr.url),'body mint',80,'white-space:nowrap')+
      box(1472,344,384,384,qrSVG(),'qr',64)+
      box(64,716,1792,72,'Built during the Meta Global AI Developer Hackathon','body',56)+
      box(64,796,1792,76,'Muse Spark · Meta open weights','body muted',56);
  }
  const renderers={disclosure,apple,extract,hover,proof,program,l4,
    screenshot:(t,s,e)=>input(t,s,e,false),audio:(t,s,e)=>input(t,s,e,true),results,limits,cta};
  window.seek=function(time) {
    const shot=L.shotAt(D.timing,time),index=D.timing.shots.indexOf(shot),t=clamp(time,0,D.timing.duration);
    const scene=D.scenes[index],events=Object.fromEntries(D.cues._events[shot.id].map(e=>[e.event,e.t]));
    boxes=[];
    const output=renderers[scene.renderer](t,shot,events),html=typeof output==='string'?output:output.html;
    stage.className='v3';stage.innerHTML=html;stage.dataset.shot=shot.id;stage.dataset.time=String(t);
    window.frame={time:t,shot:shot.id,boxes,hover:typeof output==='string'?null:output.state};
    return {time:t,shot:shot.id};
  };
  window.timeline=D.timing;window.motionReady=true;window.beatAt=beat.beatAt;window.nearestBeat=beat.nearestBeat;
  const query=new URLSearchParams(window.location?window.location.search:'').get('t');
  window.seek(query===null?0:Number(query));
})();
