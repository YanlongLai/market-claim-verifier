document.querySelector("#language-switch").href="index.zh.html"+location.hash;
addEventListener("hashchange",()=>document.querySelector("#language-switch").href="index.zh.html"+location.hash);
const SYS=[["meta","Meta Model API","muse-spark-1.3"],["baseten","Baseten","muse-spark-open-1026 · open weights"],["fireworks","Fireworks","muse-spark-open · open weights"]];
const VLAB={supported:"Supported",contradicted:"Contradicted",insufficient_evidence:"Insufficient evidence"};
const FAM={value:"Value",approx:"Approximation",inequality:"Inequality",yoy:"Year-over-year growth",period_trap:"Period trap",unit_trap:"Unit trap",multi_part:"Multiple values",record_first:"First / record",not_checkable:"SEC Unavailable",ambiguous_period:"Ambiguous period"};
const LAYER={generated:"Generated",paraphrased:"Paraphrased",real:"News"};
const ORDER=["single_shot@meta","agent@meta","single_shot@baseten","agent@baseten","single_shot@fireworks","agent@fireworks"];
const $=s=>document.querySelector(s);
const pct=x=>(x*100).toFixed(1)+"%";
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const sysName=s=>{const [m,p]=s.split("@");return (m==="agent"?"Agent":"Single-shot")+" · "+SYS.find(x=>x[0]===p)[1]};
function money(v){if(v==null)return"—";const a=Math.abs(v);if(a>=1e9)return"$"+(v/1e9).toFixed(3)+"B";if(a>=1e6)return"$"+(v/1e6).toFixed(2)+"M";if(a<100)return(Number.isInteger(v)?v:v.toFixed(2))+"";return"$"+v.toLocaleString()}
function acc(o){const ci=o.accuracy_ci||(o.confidence_intervals||{}).accuracy||{};return{a:o.accuracy,lo:ci.lower,hi:ci.upper,c:o.correct,n:o.n}}

function highlight(t){
  let s=esc(t);
  s=s.replace(/(\b(?:fiscal|calendar|FY)\s*(?:Q[1-4]\s*)?\d{4}\b|\bQ[1-4]\s*(?:of\s*)?(?:fiscal\s*)?\d{4}\b|\b(?:first|second|third|fourth)\s+quarter(?:\s+of)?(?:\s+fiscal)?\s+\d{4}\b|\b(?:full[- ]year|fiscal year)\s+\d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)/gi,'<mark class="p">$1</mark>');
  s=s.replace(/(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:billion|million|trillion|[BMK]\b)?|\b\d[\d,]*(?:\.\d+)?\s?(?:%|percent|billion|million)|\b\d+(?:\.\d+)?x\b)/gi,'<mark class="n">$1</mark>');
  return s;
}

let D, current=null, curSys="agent@baseten", curRun="v2";
fetch("data.json").then(r=>r.json()).then(d=>{D=d;init()}).catch(e=>{$("#detail").innerHTML='<p>Data loading failed: '+esc(e.message)+'. Please reload the page.</p>'});

function init(){
  renderPosthoc();
  const ci=D.stats.confidence_intervals, pc=D.stats.paired_comparisons, tot=D.stats.system_totals;
  const best=acc(ci["agent@baseten"].overall), ssm=acc(ci["single_shot@meta"].overall), am=acc(ci["agent@meta"].overall);
  const fsA=ci["agent@baseten"].overall.false_supported, fsS=ci["single_shot@meta"].overall.false_supported, harm=ci["agent@baseten"].overall.harmful_gold;
  $("#thesis").innerHTML=`
   <div><span class="eyebrow">Agent Best (Baseten / Fireworks)</span><span class="big">${pct(best.a)}</span><small>${best.c}/${best.n}  correct · 95% CI ${pct(best.lo)}–${pct(best.hi)}</small></div>
   <div><span class="eyebrow">Meta API: Single-shot → Agent</span><span class="big"><span class="from">${pct(ssm.a)} →</span> ${pct(am.a)}</span><small>Paired difference +${(pc["agent@meta_vs_single_shot@meta"].accuracy_difference*100).toFixed(1)}  points, p &lt; 0.0001</small></div>
   <div><span class="eyebrow">False-supported</span><span class="big"><span class="from">${fsS} →</span> ${fsA}</span><small>Among ${harm}  non-supported claims (Single-shot Meta → Agent Baseten)</small></div>
   <div><span class="eyebrow">News 43  claims</span><span class="big">${realScore("agent@baseten")}</span><small>Agent Baseten; Single-shot Meta only ${realScore("single_shot@meta")}</small></div>`;

  $("#systems").innerHTML=SYS.map(([p,name,model])=>{
    const s=acc(ci["single_shot@"+p].overall), a=acc(ci["agent@"+p].overall), pr=pc[`agent@${p}_vs_single_shot@${p}`];
    const ts=tot["single_shot@"+p], ta=tot["agent@"+p];
    const bar=(lab,o,cls)=>`<div class="bar"><span>${lab}</span><div class="track" role="img" aria-label="${lab} ${pct(o.a)}"><div class="fill ${cls}" style="width:${o.a*100}%"></div><div class="ci" style="left:${o.lo*100}%;width:${(o.hi-o.lo)*100}%"></div></div><span class="num">${pct(o.a)} <span style="color:var(--muted);font-size:11px">${(o.lo*100).toFixed(0)}–${(o.hi*100).toFixed(0)}</span></span></div>`;
    return `<article class="sheet prov"><header><h3>${name}</h3><span class="model">${model}</span></header>
      ${bar("Single-shot",s,"ss")}${bar("Agent",a,"ag")}
      <p class="delta">Agent Improvement <b>+${(pr.accuracy_difference*100).toFixed(1)}</b>  points (95% CI +${(pr.bootstrap_95_ci.lower*100).toFixed(0)} to +${(pr.bootstrap_95_ci.upper*100).toFixed(0)}); Agent alone correct ${pr.discordant.left_only} ; single-shot alone correct ${pr.discordant.right_only}  claims.</p>
      <div class="kv">
        <div>Cost per claim<b>$${ta.cost_usd.mean.toFixed(3)}</b></div>
        <div>Mean latency<b>${(ta.latency_ms.mean/1000).toFixed(0)} s</b></div>
        <div>False-supported<b>${ci["agent@"+p].overall.false_supported}</b></div>
        <div>Single-shot cost<b>$${ts.cost_usd.mean.toFixed(3)}</b></div>
      </div></article>`}).join("");

  const fams=Object.keys(FAM).filter(f=>ci["agent@meta"].family[f]);
  const layers=["generated","paraphrased","real"];
  const head=`<thead><tr><th>System</th>${fams.map(f=>`<th>${FAM[f]}</th>`).join("")}${layers.map(l=>`<th>${LAYER[l]}</th>`).join("")}</tr></thead>`;
  const cell=o=>{const r=o.correct/o.n;const col=`color-mix(in srgb, var(--ok) ${Math.round(r*55)}%, var(--bad-wash))`;return `<td class="cell" style="background:${col}">${o.correct}/${o.n}</td>`};
  $("#heat").innerHTML=head+"<tbody>"+ORDER.map(s=>`<tr><th scope="row" style="text-transform:none;letter-spacing:0;font-size:12px">${sysName(s)}</th>${fams.map(f=>cell(ci[s].family[f])).join("")}${layers.map(l=>cell(ci[s].layer[l])).join("")}</tr>`).join("")+"</tbody>";

  const tiers=((D.stats.source_scorecard||{}).source_reliability||{}).by_tier||{};
  const TL={primary:"Company IR / official releases",major_press:"Major press",aggregator:"Financial aggregators"};
  $("#tier").innerHTML=Object.entries(tiers).map(([k,v])=>{const c=v.counts,n=v.n;const w=x=>(x/n*100).toFixed(1)+"%";return `<div class="sheet"><h3>${TL[k]||k}</h3><span class="mono" style="font-size:12px;color:var(--muted)">n = ${n}</span><div class="stack"><i style="width:${w(c.supported)};background:var(--ok)"></i><i style="width:${w(c.contradicted)};background:var(--bad)"></i><i style="width:${w(c.insufficient_evidence)};background:var(--warn)"></i></div><span style="font-size:12.5px">Supported ${c.supported} · Contradicted ${c.contradicted} · Unverifiable ${c.insufficient_evidence} <span style="color:var(--muted)">Supported 95% CI ${pct(v.wilson_95_ci.supported.lower)}–${pct(v.wilson_95_ci.supported.upper)}</span></span></div>`}).join("");

  const fsel=$("#f-fam");fams.forEach(f=>fsel.insertAdjacentHTML("beforeend",`<option value="${f}">${FAM[f]}</option>`));
  ["#f-q","#f-layer","#f-fam","#f-out"].forEach(id=>$(id).addEventListener("input",renderList));
  $("#foot").innerHTML=`Data: <span class="mono">${esc(D.run)}/summary.json</span> and per-claim traces · Reference labels: <span class="mono">eval/v2/claims-v2-corrected.jsonl</span> · Rebuilt: <span class="mono">docs/scripts/build_explorer_data.py</span>`;
  renderList();
  const h=location.hash.slice(1);
  select(D.claims.find(c=>c.id===h)?h:"G0119");
}
function realScore(s){const o=D.stats.confidence_intervals[s].layer.real;return `${o.correct}/${o.n}`}
function renderPosthoc(){
  const rerun=D.posthoc_rerun;
  $("#posthoc").hidden=!rerun;
  if(!rerun)return;
  $("#posthoc-rows").innerHTML=rerun.systems.map(s=>`<tr><th scope="row">${esc(s.provider)}</th><td>${pct(s.v2.accuracy)} → ${pct(s.rerun.accuracy)}</td><td>${s.v2.false_supported} → ${s.rerun.false_supported}</td></tr>`).join("");
  $("#posthoc-report").href=rerun.report_url;
}
function ok(c,s,run="v2"){const r=(run==="rerun"?c.rerun:c.results)?.[s];return !!r&&r.status==="completed"&&r.verdict===c.gold}
function match(c){
  const q=$("#f-q").value.trim().toLowerCase(), L=$("#f-layer").value, F=$("#f-fam").value, O=$("#f-out").value;
  if(L&&c.layer!==L)return false; if(F&&c.family!==F)return false;
  if(q&&!(c.id.toLowerCase().includes(q)||c.claim.toLowerCase().includes(q)))return false;
  const ag=ORDER.filter(s=>s.startsWith("agent")), ss=ORDER.filter(s=>s.startsWith("single"));
  if(O==="agent_wrong"&&ag.every(s=>ok(c,s)))return false;
  if(O==="false_sup"&&!(c.gold!=="supported"&&ORDER.some(s=>c.results[s]?.verdict==="supported")))return false;
  if(O==="ss_wrong_agent_right"&&!(ag.every(s=>ok(c,s))&&ss.some(s=>!ok(c,s))))return false;
  if(O==="corrected"&&!c.gold_correction)return false;
  if(O==="rerun_changed"&&!ag.some(s=>c.rerun?.[s]&&ok(c,s)!==ok(c,s,"rerun")))return false;
  return true;
}
function renderList(){
  const rows=D.claims.filter(match);
  $("#count").textContent=`${rows.length} / ${D.claims.length}  claims · Meta, Baseten, Fireworks: single-shot (light), agent (dark). Green = correct; red = incorrect.`;
  $("#list").innerHTML=rows.map(c=>`<button class="row" role="listitem" data-id="${c.id}" aria-current="${c.id===current}"><span class="rid">${c.id}</span><span class="rtext">${esc(c.claim)}</span><span class="dots">${ORDER.map(s=>`<i class="dot ${ok(c,s)?"y":"n"} ${s.startsWith("single")?"ss":""}" title="${sysName(s)}"></i>`).join("")}</span></button>`).join("");
  $("#list").querySelectorAll(".row").forEach(b=>b.addEventListener("click",()=>select(b.dataset.id)));
}
function select(id){
  current=id; document.querySelector("#language-switch").href="index.zh.html"+"#"+id; try{history.replaceState(null,"","#"+id)}catch(e){}
  $("#list").querySelectorAll(".row").forEach(b=>b.setAttribute("aria-current",b.dataset.id===id));
  renderDetail();
}
function vchip(v){return `<span class="verdict v-${v||"none"}">${VLAB[v]||"No result"}</span>`}
function renderDetail(){
  const c=D.claims.find(x=>x.id===current); if(!c)return;
  const src=c.source;
  let srcHtml="";
  if(src&&src.source_url){srcHtml=`<div class="quote"><span class="eyebrow">Claim source</span><a href="${esc(src.source_url)}" target="_blank" rel="noopener">${esc(src.source_title||src.source_domain)}</a><span style="color:var(--muted);font-size:12px">${esc(src.source_domain)} · ${esc(src.published||"")} · ${({primary:"Official issuer",major_press:"Major press",aggregator:"Aggregator"})[src.source_tier]||esc(src.source_tier)} · Paraphrased claim; follow the link for the original</span></div>`}
  const corr=c.gold_correction?`<p style="font-size:12.5px"><b>Corrected reference label: </b>Originally registered as “${VLAB[c.gold_correction.registered_gold]}”. ${esc(c.gold_correction.reason)}</p>`:"";
  const rerun=c.rerun?.[curSys];
  const useRerun=curRun==="rerun"&&!!rerun;
  const r=(useRerun?rerun:c.results[curSys])||{};
  $("#detail").innerHTML=`
    <div style="display:grid;gap:10px">
      <div class="chips"><span class="chip">${c.id}</span><span class="chip">${LAYER[c.layer]||c.layer}</span><span class="chip">${FAM[c.family]||c.family}</span><span class="chip">${c.split==="test"?"Held-out test":"Development"}</span></div>
      <p class="claimtext">${highlight(c.claim)}</p>
      ${srcHtml}
    </div>
    <div class="gold"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><span class="eyebrow">Reference label</span>${vchip(c.gold)}</div><span>${esc(c.gold_note||"")}</span>${corr}</div>
    <div style="display:grid;gap:8px"><span class="eyebrow">v2 Six systems (select for details)</span>
      <div class="grid6">${ORDER.map(s=>{const x=c.results[s]||{};const y=ok(c,s), rr=c.rerun?.[s];return `<button class="sys" data-s="${s}" aria-pressed="${s===curSys}"><span class="name">${sysName(s)}</span>${vchip(x.verdict)}<span class="mark ${y?"y":"n"}">${y?"✓ Correct":"✗ Incorrect"}</span>${rr&&x.verdict!==rr.verdict?`<span class="rerun-change">v2: ${VLAB[x.verdict]||"No result"} → rerun: ${VLAB[rr.verdict]||"No result"}</span>`:""}<span class="meta">$${(x.cost??0).toFixed(4)} · ${x.latency_s??"—"} s</span></button>`}).join("")}</div>
    </div>
    <div style="display:grid;gap:10px"><span class="eyebrow">${sysName(curSys)} verification steps · ${useRerun?"rerun (post-hoc)":"v2"}</span>
      ${rerun?`<div class="run-switch" role="group" aria-label="Run version"><button type="button" data-run="v2" aria-pressed="${!useRerun}">v2</button><button type="button" data-run="rerun" aria-pressed="${useRerun}">rerun · Post-hoc rerun</button></div>`:""}
      <div class="run-verdict">${vchip(r.verdict)}<span>${ok(c,curSys,useRerun?"rerun":"v2")?"✓ Correct":"✗ Incorrect"}</span></div>
      ${r.status!=="completed"?`<p class="summary">${useRerun?"rerun":"v2"} Incomplete (${esc(r.status||"No result")}), Counted as incorrect.</p>`:""}
      ${r.summary?`<p class="summary">Model summary: ${esc(r.summary)}</p>`:""}
      ${curSys.startsWith("agent")?agentSteps(r):`<p class="summary">Single-shot uses no tools or retrieved evidence; its verdict is the model's answer.</p>`}
    </div>`;
  $("#detail").querySelectorAll(".sys").forEach(b=>b.addEventListener("click",()=>{curSys=b.dataset.s;if(!c.rerun?.[curSys])curRun="v2";renderDetail()}));
  $("#detail").querySelectorAll("[data-run]").forEach(b=>b.addEventListener("click",()=>{curRun=b.dataset.run;renderDetail()}));
}
function reasonText(ck){
  const R=ck.reason||"";
  if(/period interpretations/.test(R))return "Both fiscal and calendar interpretations checked";
  if(/unchecked_other/.test(R))return "SEC tools lack this metric (for example segment revenue); no program verdict";
  if(/no valid evidence|evidence_invalid/.test(R))return "No valid evidence ID; cannot support the claim";
  return "";
}
function agentSteps(r){
  const checks=r.checks||[]; const ev=r.evidence||[];
  if(!checks.length)return `<p class="summary">No checkable subclaims.</p>`;
  const blocks=checks.map((ck,i)=>{
    const st=ck.stated_value_used, act=ck.actual_value, tol=ck.tolerance;
    const diff=(st!=null&&act!=null)?Math.abs(act-st):null;
    const cmp={eq:"equal within stated precision",gt:"greater than",gte:"at least",lt:"less than",lte:"at most",approx:"approximately equal"}[ck.comparator]||ck.comparator;
    const why=reasonText(ck);
    return `<div class="steps">
      <div class="step"><span class="lab">Subclaim ${i+1}</span><span>${highlight(ck.text||"")}</span></div>
      <div class="step"><span class="lab">Program-parsed claim</span><span class="val">${money(st)} · Comparison: ${esc(cmp)}${ck.comparator_corrected?` (Model selected “${esc(ck.model_comparator)}”, corrected from wording)`:""}</span></div>
      <div class="step"><span class="lab">SEC value (${(ck.evidence_ids||[]).join(", ")||"No evidence"})</span><span class="val">${money(act)}</span></div>
      ${tol!=null?`<div class="step"><span class="lab">Tolerance</span><span class="val">± ${money(tol)} Difference ${diff!=null?money(diff):"—"}</span></div>`:""}
      <div class="step key"><span class="lab">Program verdict</span><span><span class="decision">${VLAB[ck.program_verdict]||(ck.program_verdict==="unchecked"?"Unchecked":esc(ck.program_verdict))}</span>${why?" "+why:""}${ck.period_ambiguous?" Ambiguous period":""}</span><span style="font-size:12px;color:var(--muted)">${esc(ck.evidence_summary||"")}</span></div>
    </div>`}).join("");
  const evs=ev.map(e=>`<div class="ev"><div class="evh"><b class="mono">${esc(e.id)} · ${esc(e.entity||e.ticker)}</b><span>${e.tier?`Evidence tier ${esc(e.tier)}`:""}${e.restated?" · Restated":""}</span></div><dl>
     <dt>Value</dt><dd><mark class="n">${money(e.value)}</mark> ${esc(e.unit||"")}</dd>
     <dt>XBRL Concept</dt><dd>${esc(e.concept||e.metric)}</dd>
     <dt>Period</dt><dd>${esc(e.start||"")} → ${esc(e.end||"")}${e.frame?` · SEC frame ${esc(e.frame)}`:""}${e.fiscal_year?` · Fiscal year ${e.fiscal_year} ${esc(e.fiscal_period||"")}`:""}</dd>
     <dt>Source</dt><dd>${e.derived?"Derived by subtracting filing values":`${esc(e.form)} · Filed ${esc(e.filed)}`}${e.accn?` · ${esc(e.accn)}`:""}</dd>
     ${e.filing_url?`<dt>Original filing</dt><dd><a href="${esc(e.filing_url)}" target="_blank" rel="noopener">Open in SEC EDGAR</a></dd>`:""}
   </dl></div>`).join("");
  return blocks+(evs?`<div style="display:grid;gap:8px"><span class="eyebrow">Cited SEC evidence</span>${evs}</div>`:"");
}
