/* Every visible property is a pure function of seek(t). This file never starts playback. */
(function () {
  'use strict';
  const L=window.MotionLogic, D=window.MOTION_DATA, stage=document.getElementById('stage');
  if(!L||!D) throw new Error('Run build.py review-frames --prepare-only to prepare local motion data.js');
  const {clamp,lerp,easeInOut,easeOutBack,progress,escapeHTML:esc,highlightQuote:quote}=L;
  const P=D.product, beats=D.beats.beats_s;
  const amazonAmount='$'+P.claim_numbers.amazon_b.toFixed(1)+'B';
  const claimedApple='$'+P.apple.claimed_b.toFixed(1)+'B';
  const hookApple='$'+P.apple.claimed_b.toFixed(0)+'B';
  const multiplier=P.claim_numbers.nvidia_multiplier+'×';
  const helpers=L.beatHelpers(beats);
  window.beatAt=helpers.beatAt; window.nearestBeat=helpers.nearestBeat;
  window.timeline=D.timing;
  for(const [key,value] of Object.entries(L.TYPE)) stage.style.setProperty('--'+key,value+'px');
  const num=(s,style='')=>`<span class="number" style="${style}">${esc(s)}</span>`;
  const box=(x,y,w,h,html,cls='',style='')=>`<div class="abs ${cls}" style="left:${x}px;top:${y}px;width:${w}px;${h===null?'':'height:'+h+'px;'}${style}">${html}</div>`;
  // Keep semantic type at full size during reveals. Bars and background sweeps animate;
  // readable text fades in without scaling down or transiently reporting wrong values.
  const pop=(t,event)=>easeOutBack(progress(t,event));
  const visible=(t,event)=>t>=event?1:0;
  const verdictWord=v=>({supported:'TRUE',contradicted:'FALSE',insufficient_evidence:'INSUFFICIENT'})[v];
  function qrSVG() {
    const {matrix,quiet_zone:q}=D.qr, size=matrix.length+2*q;
    const path=matrix.flatMap((row,y)=>[...row].flatMap((bit,x)=>bit==='1'?[`M${x+q},${y+q}h1v1h-1z`]:[])).join('');
    return `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="QR code for ${esc(D.qr.url)}" viewBox="0 0 ${size} ${size}" shape-rendering="crispEdges"><rect width="${size}" height="${size}" fill="#fff"/><path d="${path}" fill="#000"/></svg>`;
  }
  function chrome(scene,index) {
    const labels=['Check before you share','Finance posts','Model alone','1 · Extract claims',
      '2 · Check claims','3 · SEC proof','Program checks','Pre-registered results','English · 中文','Try the live demo'];
    return `<div class="label">${esc(labels[index])}</div><div class="brand">Market Claim Verifier</div><div class="rule"></div>`;
  }
  function open(t,s,e) {
    const judged=t>=e.verdict;
    return box(64,196,950,300,'Market Claim<br><span class="mint">Verifier</span>','headline','font-size:128px')
      +box(64,552,950,190,'Check the number<br>before you share it.','body','font-size:72px')
      +box(1064,354,792,500,`<div class="body">Apple made</div><div style="margin:12px 0">${num(hookApple,'font-size:128px')}</div><div class="body">in one quarter?</div><div class="verdict ${judged?'coral':''}" style="margin-top:20px">${judged?verdictWord(P.apple.verdict):'?'}</div>`,'panel opening-claim','padding:32px');
  }
  function spread(t,s,e) {
    const full=P.english_claims[0].quote;
    const typed=full.slice(0,Math.floor(clamp((t-s.start)/1.4)*full.length));
    let html=box(64,188,1792,124,'Numbers spread faster than facts.','headline');
    html+=box(64,332,1792,300,`<div class="quote body" style="font-size:72px;line-height:1.2">${quote(typed)}</div>`,'panel','padding:24px 32px');
    [amazonAmount,multiplier,hookApple].forEach((value,i)=>{
      const isWrong=i===2, event=e.tokens[i];
      html+=box(64+i*608,648,576,216,`${num(value)}<div class="body" style="margin-top:8px;font-size:56px">${['Q3 2023 revenue','FY2024 growth','Claimed quarter'][i]}${isWrong?' ?':''}</div>`,'panel hook-token',`padding:12px 24px;color:var(--${isWrong?'coral':'mint'});opacity:${visible(t,event)}`);
    });
    return html;
  }
  function baseline(t,s,e) {
    const push=easeInOut(progress(t,s.start,s.end-s.start));
    let chart='';
    [...P.providers].reverse().forEach((row,i)=>{
      const grow=clamp(pop(t,e.bars[i])), height=210*row.alone/44*grow;
      chart+=box(76+i*584,342-height,400,height,'','baseline-bar',`background:var(--coral);opacity:${visible(t,e.bars[i])}`);
      chart+=box(76+i*584,226-height,400,112,num(row.alone+'%'),'coral baseline-counter',`opacity:${visible(t,e.bars[i])}`);
      chart+=box(76+i*584,350,400,76,esc(row.id==='meta'?'Meta API':row.label),'body baseline-provider','font-size:64px');
    });
    return box(64,188,1792,124,'Model alone: <span class="coral">20–44%</span>','headline')
      +box(64,306,1792,440,chart,'baseline-chart',`transform:scale(${lerp(1,1.02,push)});transform-origin:center center`)
      +box(64,758,1792,108,`Muse Spark · ${num(P.claim_count,'font-size:96px')} finance claims · from memory`,'body muted baseline-note','font-size:56px');
  }
  function extract(t,s,e) {
    const events=[...e.claims,...e.stamps];
    let active=0;
    events.forEach((at,i)=>{if(t>=at) active=i;});
    const current=P.english_claims[active], judged=current.kind==='reported_fact';
    const names=['Amazon','NVIDIA','Apple','Opinion'];
    let html=box(64,188,1792,124,'Extract the checkable claims.','headline');
    html+=box(64,328,1792,414,`<div class="sweep" style="transform:scaleX(${easeInOut(progress(t,events[active]))});background:${judged?'#164e3c':'#2b3c47'}"></div><div class="card-name" style="position:relative">${names[active]}</div><div class="tag ${judged?'mint':'not-judged'}" style="position:absolute;right:28px;top:20px">${judged?'Exact quote extracted':'not judged'}</div><div class="quote body" style="position:relative;margin-top:36px;font-size:72px">${quote(current.quote)}</div>`,'panel','padding:28px 32px');
    names.forEach((name,i)=>{
      html+=box(64+i*456,766,424,98,`${esc(name)} ${t>=events[i]?(i===3?'—':'✓'):'·'}`,'panel extraction-status',`padding:16px 20px;font-size:56px;color:var(--${i===3?'muted':'mint'})`);
    });
    return html;
  }
  function verdicts(t,s,e) {
    const expanded=t>=e.appleFalse;
    const config=D.presentation_focus||{settle_s:.24,push_s:8};
    const focus=easeInOut(progress(t,e.appleFalse+config.settle_s,config.push_s));
    const names=['Amazon','NVIDIA','Apple'], values=[amazonAmount,'> '+multiplier,claimedApple];
    const periods=['Q3 2023 revenue','FY2024 revenue','Fiscal Q4 2025'];
    let html=box(64,176,1792,112,expanded?'Apple: a year is not a quarter.':'A verdict for every claim.','headline');
    names.forEach((name,i)=>{
      const isApple=i===2;
      let x=64+i*608,y=328,w=576,h=536,content='';
      if(expanded&&isApple) {
        x=lerp(600,568,focus);y=296;w=lerp(1256,1288,focus);h=568;
        const inner=w-64, quarterWidth=inner*P.apple.quarter_b/P.apple.full_year_b;
        content=box(32,20,inner,88,'Apple <span class="verdict coral" style="float:right">FALSE</span>','card-name','font-size:64px')
          +box(32,104,inner,104,`Post says ${num(claimedApple,'font-size:96px')} in one quarter`,'body apple-claim','font-size:56px')
          +box(32,210,inner,104,`<span class="period-label">Fiscal Q4 2025</span>${num('$'+P.apple.quarter_b.toFixed(1)+'B','font-size:96px;float:right;color:var(--coral)')}`,'body apple-comparison','font-size:56px')
          +box(32,318,quarterWidth,16,'','apple-quarter-bar','background:var(--coral);opacity:1')
          +box(32,336,inner,104,`<span class="period-label">Full fiscal year 2025</span>${num('$'+P.apple.full_year_b.toFixed(1)+'B','font-size:96px;float:right')}`,'body muted apple-comparison','font-size:56px')
          +box(32,444,inner,16,'','apple-year-bar','background:var(--muted);opacity:1')
          +box(32,460,inner,104,`${num('4×','font-size:96px')} too high · that's the full year`,'body apple-explanation','font-size:56px');
      } else if(expanded) {
        x=64;y=296+i*296;w=472;h=272;
        content=box(20,16,w-40,64,`${name}<span class="mint" style="float:right">TRUE</span>`,'card-name')
          +box(20,82,w-40,112,num(values[i]),'mint')
          +box(20,194,w-40,66,periods[i],'body muted','font-size:56px');
      } else {
        content=box(28,28,w-56,80,name,'card-name','font-size:64px')
          +box(28,142,w-56,100,t>=e.flips[i]?verdictWord(P.english_claims[i].verdict):'…',`verdict ${isApple?'coral':'mint'}`)
          +box(28,264,w-56,118,num(values[i]),'')
          +box(28,408,w-56,100,periods[i],'body muted','font-size:56px');
      }
      // The correction composition occupies a separate right column immediately at
      // FALSE. Its complete comparison stays readable throughout the slow push.
      html+=box(x,y,w,h,content,'card'+(isApple?' apple-card':''),`opacity:${visible(t,e.flips[i])}`);
    });
    return html;
  }
  function proof(t,s,e) {
    const sweep=easeInOut(progress(t,e.sweep,.24));
    let table='<div></div>';
    // The brief's quarter-only close-up leaves real gutters at phone-readable type.
    // Nine-month columns remain in P.filing and in the linked original filing.
    table+='<div class="table-group" style="grid-column:span 2">Three months · Sep 30</div>';
    table+='<div></div>'+P.filing.years.slice(0,2).map(y=>`<div class="table-year number">${esc(y)}</div>`).join('');
    table+=`<div class="table-cell row-label"><span>Total net<br>sales</span></div>`;
    P.filing.values.slice(0,2).forEach((value,i)=>{
      table+=`<div class="table-cell number"><span>${esc(value)}</span>${i===0?`<div class="filing-highlight" style="clip-path:inset(0 ${100*(1-sweep)}% 0 0)"><span>${esc(value)}</span></div>`:''}</div>`;
    });
    return box(64,188,1792,124,'The exact filing line.','headline')
      +`<div class="table-window"><div class="filing-table">${table}</div></div>`
      +box(64,738,1792,70,`AMZN · ${esc(P.filing.form)} · ${esc(P.filing.unit)}`,'body muted','font-size:56px')
      +box(64,810,1792,64,`<a href="${esc(P.filing.url)}" style="color:inherit;text-underline-offset:8px">Open in original filing ↗</a>`,'body amber',`font-size:56px;opacity:${t>=e.link?1:.8}`);
  }
  function program(t,s,e) {
    const node=(x,y,w,h,html,event,color='mint')=>box(x,y,w,h,html,'flow-node',`opacity:${visible(t,event)};border-color:var(--${color})`);
    return box(64,188,1792,124,'Model proposes. Program decides.','headline')
      +box(64,320,1792,544,'','panel program-board')
      +box(88,344,300,200,'MODEL','body muted flow-lane',`font-size:64px;opacity:${visible(t,e.modelLane)}`)
      +node(414,344,608,196,'Plan<br>SEC lookups',e.plan)
      +box(1046,386,90,100,'→','arrow',`opacity:${visible(t,e.cite)}`)
      +node(1160,344,672,196,`Cite ${num('E1 · E2')}`,e.cite)
      +box(88,592,300,246,'PROGRAM<br><span class="mint">decides</span>','body flow-lane',`font-size:56px;opacity:${visible(t,e.programLane)}`)
      +node(414,584,442,256,`Number<br>${num('±'+P.claim_numbers.precision_b+'B')}`,e.parse)
      +node(880,584,500,256,'Fiscal ↔<br>calendar',e.calendar)
      +node(1404,584,428,256,`Evidence<div class="fake-evidence coral" style="margin-top:16px;opacity:${visible(t,e.fake)}">${num('E9')} ✕</div>`,Math.min(e.evidence,e.fake),t>=e.fake?'coral':'mint');
  }
  function results(t,s,e) {
    let html=box(64,176,1040,112,'Measured accuracy.','headline');
    html+=box(1132,174,724,136,`Up to ${num('+'+P.max_gain_points.toFixed(1),'font-size:96px')} points`,'panel mint results-badge',`padding:14px 24px;font-size:56px;white-space:nowrap;opacity:${visible(t,e.badge)}`);
    html+=box(64,298,1792,64,'Pre-registered · Muse Spark','body muted','font-size:56px')
      +box(64,368,1792,508,'','panel results-board')
      +box(96,374,680,104,`${num(P.claim_count,'font-size:96px')} claims`,'body muted','font-size:56px')
      +box(850,382,420,70,'Model alone','body muted','font-size:56px')
      +box(1390,382,434,70,'With checks','body mint','font-size:56px');
    P.providers.forEach((row,i)=>{
      const y=480+i*128, alone=e.results[i][0], checked=e.results[i][1];
      html+=box(96,y+12,680,98,esc(row.label),'body result-provider',`font-size:72px;opacity:${visible(t,alone)}`);
      html+=box(850,y,420,112,num(row.alone+'%'),'muted result-alone',`opacity:${visible(t,alone)}`);
      html+=box(1390,y,434,112,num(row.checked+'%','font-size:112px'),'mint result-checked',`opacity:${visible(t,checked)}`);
      html+=box(850,y+114,420,10,`<div class="bar" style="background:var(--muted);width:${row.alone*clamp(pop(t,alone))}%"></div>`,'track',`opacity:${visible(t,alone)}`);
      html+=box(1390,y+114,434,10,`<div class="bar" style="background:var(--mint);width:${row.checked*clamp(pop(t,checked))}%"></div>`,'track',`opacity:${visible(t,checked)}`);
    });
    return html;
  }
  function chinese(t,s,e) {
    return box(64,188,1792,124,'Same checks. In Chinese, too.','headline')
      +box(64,328,1792,302,`<div class="card-name">可口可樂 · Coca-Cola</div><div class="quote body" style="margin-top:24px;font-size:72px">${quote(P.chinese_claim.quote)}</div>`,'panel','padding:28px 32px')
      +box(64,660,1000,116,num(P.claim_numbers.chinese_yi+' 億 = $'+P.claim_numbers.chinese_b.toFixed(1)+'B','font-size:104px'),'amber chinese-conversion',`opacity:${visible(t,e.convert)}`)
      +box(1100,660,756,116,`Filed: ${num('$'+P.claim_numbers.chinese_filed_b.toFixed(1)+'B')}`,'body coral chinese-filed',`font-size:64px;opacity:${visible(t,e.chineseVerdict)}`)
      +box(64,798,1000,66,'FY2024 · audited 10-K','body muted','font-size:56px')
      +box(1100,794,756,70,verdictWord(P.chinese_claim.verdict),'verdict coral',`opacity:${visible(t,e.chineseVerdict)}`);
  }
  function cta(t,s,e) {
    return box(64,188,1792,124,'Try the live demo.','headline')
      +box(64,348,1336,212,'yanlonglai.github.io/<br>market-claim-verifier/site/','body mint cta-url','font-size:80px;line-height:1.25;letter-spacing:0')
      +box(1472,322,384,384,qrSVG(),'qr')
      +box(64,600,1336,76,'Star GitHub · YanlongLai/market-claim-verifier ↗','body','font-size:56px')
      +box(64,716,1792,68,'Built during the Meta Global AI Developer Hackathon','body hackathon-credit','font-size:56px')
      +box(64,788,1792,78,'Muse Spark · Meta open weights','body muted','font-size:64px');
  }
  const renderers=[open,spread,baseline,extract,verdicts,proof,program,results,chinese,cta];
  window.seek=function seek(time) {
    const shot=L.shotAt(D.timing,time), index=D.timing.shots.indexOf(shot);
    const t=clamp(time,0,D.timing.duration), scene=D.scenes[index];
    const events=L.eventsForShot(shot,beats,D.cues?D.cues._events[shot.id]:[]);
    const fade=index===9?easeInOut(progress(t,D.timing.duration-2,2)):0;
    stage.innerHTML=chrome(scene,index)+renderers[index](t,shot,events)+`<div class="fade" style="opacity:${fade}"></div>`;
    stage.dataset.shot=shot.id; stage.dataset.time=String(t);
    return {time:t,shot:shot.id};
  };
  window.motionReady=true;
  window.seek(0);
})();
