document.querySelector("#language-switch").href="index.html"+location.hash;
addEventListener("hashchange",()=>document.querySelector("#language-switch").href="index.html"+location.hash);
const SYS=[["meta","Meta Model API","muse-spark-1.3"],["baseten","Baseten","muse-spark-open-1026 · 開放權重"],["fireworks","Fireworks","muse-spark-open · 開放權重"]];
const VLAB={supported:"屬實",contradicted:"不實",insufficient_evidence:"證據不足"};
const FAM={value:"數值",approx:"近似值",inequality:"不等式",yoy:"年增率",period_trap:"期間陷阱",unit_trap:"單位陷阱",multi_part:"多數字",record_first:"首次 / 紀錄",not_checkable:"SEC 查不到",ambiguous_period:"財年曆年不明"};
const LAYER={generated:"程式生成",paraphrased:"模型改寫",real:"真實新聞"};
const ORDER=["single_shot@meta","agent@meta","single_shot@baseten","agent@baseten","single_shot@fireworks","agent@fireworks"];
const $=s=>document.querySelector(s);
const pct=x=>(x*100).toFixed(1)+"%";
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const sysName=s=>{const [m,p]=s.split("@");return (m==="agent"?"Agent":"一次回答")+" · "+SYS.find(x=>x[0]===p)[1]};
function money(v){if(v==null)return"—";const a=Math.abs(v);if(a>=1e9)return"$"+(v/1e9).toFixed(3)+"B";if(a>=1e6)return"$"+(v/1e6).toFixed(2)+"M";if(a<100)return(Number.isInteger(v)?v:v.toFixed(2))+"";return"$"+v.toLocaleString()}
function acc(o){const ci=o.accuracy_ci||(o.confidence_intervals||{}).accuracy||{};return{a:o.accuracy,lo:ci.lower,hi:ci.upper,c:o.correct,n:o.n}}

function highlight(t){
  let s=esc(t);
  s=s.replace(/(\b(?:fiscal|calendar|FY)\s*(?:Q[1-4]\s*)?\d{4}\b|\bQ[1-4]\s*(?:of\s*)?(?:fiscal\s*)?\d{4}\b|\b(?:first|second|third|fourth)\s+quarter(?:\s+of)?(?:\s+fiscal)?\s+\d{4}\b|\b(?:full[- ]year|fiscal year)\s+\d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)/gi,'<mark class="p">$1</mark>');
  s=s.replace(/(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:billion|million|trillion|[BMK]\b)?|\b\d[\d,]*(?:\.\d+)?\s?(?:%|percent|billion|million)|\b\d+(?:\.\d+)?x\b)/gi,'<mark class="n">$1</mark>');
  return s;
}

let D, current=null, curSys="agent@baseten", curRun="v2";
fetch("data.json").then(r=>r.json()).then(d=>{D=d;init()}).catch(e=>{$("#detail").innerHTML='<p>資料載入失敗：'+esc(e.message)+'。請重新整理頁面。</p>'});

function init(){
  renderPosthoc();
  const ci=D.stats.confidence_intervals, pc=D.stats.paired_comparisons, tot=D.stats.system_totals;
  const best=acc(ci["agent@baseten"].overall), ssm=acc(ci["single_shot@meta"].overall), am=acc(ci["agent@meta"].overall);
  const fsA=ci["agent@baseten"].overall.false_supported, fsS=ci["single_shot@meta"].overall.false_supported, harm=ci["agent@baseten"].overall.harmful_gold;
  $("#thesis").innerHTML=`
   <div><span class="eyebrow">Agent 最佳（Baseten / Fireworks）</span><span class="big">${pct(best.a)}</span><small>${best.c}/${best.n} 條正確 · 95% CI ${pct(best.lo)}–${pct(best.hi)}</small></div>
   <div><span class="eyebrow">Meta API：一次回答 → Agent</span><span class="big"><span class="from">${pct(ssm.a)} →</span> ${pct(am.a)}</span><small>同一批題目配對差距 +${(pc["agent@meta_vs_single_shot@meta"].accuracy_difference*100).toFixed(1)} 點，p &lt; 0.0001</small></div>
   <div><span class="eyebrow">把不實說成屬實</span><span class="big"><span class="from">${fsS} →</span> ${fsA}</span><small>在 ${harm} 條非屬實說法中（一次回答 Meta → Agent Baseten）</small></div>
   <div><span class="eyebrow">真實新聞 43 條</span><span class="big">${realScore("agent@baseten")}</span><small>Agent Baseten；一次回答 Meta 只有 ${realScore("single_shot@meta")}</small></div>`;

  $("#systems").innerHTML=SYS.map(([p,name,model])=>{
    const s=acc(ci["single_shot@"+p].overall), a=acc(ci["agent@"+p].overall), pr=pc[`agent@${p}_vs_single_shot@${p}`];
    const ts=tot["single_shot@"+p], ta=tot["agent@"+p];
    const bar=(lab,o,cls)=>`<div class="bar"><span>${lab}</span><div class="track" role="img" aria-label="${lab} ${pct(o.a)}"><div class="fill ${cls}" style="width:${o.a*100}%"></div><div class="ci" style="left:${o.lo*100}%;width:${(o.hi-o.lo)*100}%"></div></div><span class="num">${pct(o.a)} <span style="color:var(--muted);font-size:11px">${(o.lo*100).toFixed(0)}–${(o.hi*100).toFixed(0)}</span></span></div>`;
    return `<article class="sheet prov"><header><h3>${name}</h3><span class="model">${model}</span></header>
      ${bar("一次回答",s,"ss")}${bar("Agent",a,"ag")}
      <p class="delta">Agent 多對 <b>+${(pr.accuracy_difference*100).toFixed(1)}</b> 點（95% CI +${(pr.bootstrap_95_ci.lower*100).toFixed(0)} 到 +${(pr.bootstrap_95_ci.upper*100).toFixed(0)}）；只有 Agent 對 ${pr.discordant.left_only} 條，只有一次回答對 ${pr.discordant.right_only} 條。</p>
      <div class="kv">
        <div>每條成本<b>$${ta.cost_usd.mean.toFixed(3)}</b></div>
        <div>平均延遲<b>${(ta.latency_ms.mean/1000).toFixed(0)} s</b></div>
        <div>誤判屬實<b>${ci["agent@"+p].overall.false_supported}</b></div>
        <div>一次回答成本<b>$${ts.cost_usd.mean.toFixed(3)}</b></div>
      </div></article>`}).join("");

  const fams=Object.keys(FAM).filter(f=>ci["agent@meta"].family[f]);
  const layers=["generated","paraphrased","real"];
  const head=`<thead><tr><th>系統</th>${fams.map(f=>`<th>${FAM[f]}</th>`).join("")}${layers.map(l=>`<th>${LAYER[l]}</th>`).join("")}</tr></thead>`;
  const cell=o=>{const r=o.correct/o.n;const col=`color-mix(in srgb, var(--ok) ${Math.round(r*55)}%, var(--bad-wash))`;return `<td class="cell" style="background:${col}">${o.correct}/${o.n}</td>`};
  $("#heat").innerHTML=head+"<tbody>"+ORDER.map(s=>`<tr><th scope="row" style="text-transform:none;letter-spacing:0;font-size:12px">${sysName(s)}</th>${fams.map(f=>cell(ci[s].family[f])).join("")}${layers.map(l=>cell(ci[s].layer[l])).join("")}</tr>`).join("")+"</tbody>";

  const tiers=((D.stats.source_scorecard||{}).source_reliability||{}).by_tier||{};
  const TL={primary:"公司 IR / 官方新聞稿",major_press:"主要媒體",aggregator:"財經聚合站"};
  $("#tier").innerHTML=Object.entries(tiers).map(([k,v])=>{const c=v.counts,n=v.n;const w=x=>(x/n*100).toFixed(1)+"%";return `<div class="sheet"><h3>${TL[k]||k}</h3><span class="mono" style="font-size:12px;color:var(--muted)">n = ${n}</span><div class="stack"><i style="width:${w(c.supported)};background:var(--ok)"></i><i style="width:${w(c.contradicted)};background:var(--bad)"></i><i style="width:${w(c.insufficient_evidence)};background:var(--warn)"></i></div><span style="font-size:12.5px">屬實 ${c.supported} · 不實 ${c.contradicted} · 無法查證 ${c.insufficient_evidence}　<span style="color:var(--muted)">屬實 95% CI ${pct(v.wilson_95_ci.supported.lower)}–${pct(v.wilson_95_ci.supported.upper)}</span></span></div>`}).join("");

  const fsel=$("#f-fam");fams.forEach(f=>fsel.insertAdjacentHTML("beforeend",`<option value="${f}">${FAM[f]}</option>`));
  ["#f-q","#f-layer","#f-fam","#f-out"].forEach(id=>$(id).addEventListener("input",renderList));
  $("#foot").innerHTML=`資料：<span class="mono">${esc(D.run)}/summary.json</span> 與每條判決的追蹤檔 · 標準答案：<span class="mono">eval/v2/claims-v2-corrected.jsonl</span> · 重建：<span class="mono">docs/scripts/build_explorer_data.py</span>`;
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
  $("#count").textContent=`${rows.length} / ${D.claims.length} 條 · 方塊依序為 Meta、Baseten、Fireworks 的一次回答（淡）與 Agent（深），綠 = 對、紅 = 錯`;
  $("#list").innerHTML=rows.map(c=>`<button class="row" role="listitem" data-id="${c.id}" aria-current="${c.id===current}"><span class="rid">${c.id}</span><span class="rtext">${esc(c.claim)}</span><span class="dots">${ORDER.map(s=>`<i class="dot ${ok(c,s)?"y":"n"} ${s.startsWith("single")?"ss":""}" title="${sysName(s)}"></i>`).join("")}</span></button>`).join("");
  $("#list").querySelectorAll(".row").forEach(b=>b.addEventListener("click",()=>select(b.dataset.id)));
}
function select(id){
  current=id; document.querySelector("#language-switch").href="index.html"+"#"+id; try{history.replaceState(null,"","#"+id)}catch(e){}
  $("#list").querySelectorAll(".row").forEach(b=>b.setAttribute("aria-current",b.dataset.id===id));
  renderDetail();
}
function vchip(v){return `<span class="verdict v-${v||"none"}">${VLAB[v]||"無結果"}</span>`}
function renderDetail(){
  const c=D.claims.find(x=>x.id===current); if(!c)return;
  const src=c.source;
  let srcHtml="";
  if(src&&src.source_url){srcHtml=`<div class="quote"><span class="eyebrow">說法來源</span><a href="${esc(src.source_url)}" target="_blank" rel="noopener">${esc(src.source_title||src.source_domain)}</a><span style="color:var(--muted);font-size:12px">${esc(src.source_domain)} · ${esc(src.published||"")} · ${({primary:"公司官方",major_press:"主要媒體",aggregator:"聚合站"})[src.source_tier]||esc(src.source_tier)} · 上面這句是改寫，原文請開連結查看</span></div>`}
  const corr=c.gold_correction?`<p style="font-size:12.5px"><b>標準答案經修正：</b>原登記為「${VLAB[c.gold_correction.registered_gold]}」。${esc(c.gold_correction.reason)}</p>`:"";
  const rerun=c.rerun?.[curSys];
  const useRerun=curRun==="rerun"&&!!rerun;
  const r=(useRerun?rerun:c.results[curSys])||{};
  $("#detail").innerHTML=`
    <div style="display:grid;gap:10px">
      <div class="chips"><span class="chip">${c.id}</span><span class="chip">${LAYER[c.layer]||c.layer}</span><span class="chip">${FAM[c.family]||c.family}</span><span class="chip">${c.split==="test"?"保留測試集":"開發集"}</span></div>
      <p class="claimtext">${highlight(c.claim)}</p>
      ${srcHtml}
    </div>
    <div class="gold"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><span class="eyebrow">標準答案</span>${vchip(c.gold)}</div><span>${esc(c.gold_note||"")}</span>${corr}</div>
    <div style="display:grid;gap:8px"><span class="eyebrow">v2 六個系統的判決（點選看細節）</span>
      <div class="grid6">${ORDER.map(s=>{const x=c.results[s]||{};const y=ok(c,s), rr=c.rerun?.[s];return `<button class="sys" data-s="${s}" aria-pressed="${s===curSys}"><span class="name">${sysName(s)}</span>${vchip(x.verdict)}<span class="mark ${y?"y":"n"}">${y?"✓ 正確":"✗ 錯誤"}</span>${rr&&x.verdict!==rr.verdict?`<span class="rerun-change">v2: ${VLAB[x.verdict]||"無結果"} → rerun: ${VLAB[rr.verdict]||"無結果"}</span>`:""}<span class="meta">$${(x.cost??0).toFixed(4)} · ${x.latency_s??"—"} s</span></button>`}).join("")}</div>
    </div>
    <div style="display:grid;gap:10px"><span class="eyebrow">${sysName(curSys)} 的判斷過程 · ${useRerun?"rerun（事後）":"v2"}</span>
      ${rerun?`<div class="run-switch" role="group" aria-label="判斷過程版本"><button type="button" data-run="v2" aria-pressed="${!useRerun}">v2</button><button type="button" data-run="rerun" aria-pressed="${useRerun}">rerun · 事後重跑</button></div>`:""}
      <div class="run-verdict">${vchip(r.verdict)}<span>${ok(c,curSys,useRerun?"rerun":"v2")?"✓ 正確":"✗ 錯誤"}</span></div>
      ${r.status!=="completed"?`<p class="summary">${useRerun?"rerun":"v2"} 未完成（${esc(r.status||"無結果")}），計為錯誤。</p>`:""}
      ${r.summary?`<p class="summary">模型摘要：${esc(r.summary)}</p>`:""}
      ${curSys.startsWith("agent")?agentSteps(r):`<p class="summary">一次回答沒有工具，也沒有證據可以核對；判決直接採用模型的回答。</p>`}
    </div>`;
  $("#detail").querySelectorAll(".sys").forEach(b=>b.addEventListener("click",()=>{curSys=b.dataset.s;if(!c.rerun?.[curSys])curRun="v2";renderDetail()}));
  $("#detail").querySelectorAll("[data-run]").forEach(b=>b.addEventListener("click",()=>{curRun=b.dataset.run;renderDetail()}));
}
function reasonText(ck){
  const R=ck.reason||"";
  if(/period interpretations/.test(R))return "財年與曆年兩種讀法都檢查過";
  if(/unchecked_other/.test(R))return "SEC 查詢工具沒有這種資料（例如分部營收），程式不判斷";
  if(/no valid evidence|evidence_invalid/.test(R))return "沒有有效的證據編號，不能判為屬實";
  return "";
}
function agentSteps(r){
  const checks=r.checks||[]; const ev=r.evidence||[];
  if(!checks.length)return `<p class="summary">沒有可核對的子說法。</p>`;
  const blocks=checks.map((ck,i)=>{
    const st=ck.stated_value_used, act=ck.actual_value, tol=ck.tolerance;
    const diff=(st!=null&&act!=null)?Math.abs(act-st):null;
    const cmp={eq:"等於（在精度內）",gt:"大於",gte:"至少",lt:"小於",lte:"至多",approx:"約等於"}[ck.comparator]||ck.comparator;
    const why=reasonText(ck);
    return `<div class="steps">
      <div class="step"><span class="lab">子說法 ${i+1}</span><span>${highlight(ck.text||"")}</span></div>
      <div class="step"><span class="lab">程式從原文解析</span><span class="val">${money(st)} · 比較方式：${esc(cmp)}${ck.comparator_corrected?`（模型原本選「${esc(ck.model_comparator)}」，已依用字更正）`:""}</span></div>
      <div class="step"><span class="lab">SEC 數字（${(ck.evidence_ids||[]).join("、")||"無證據"}）</span><span class="val">${money(act)}</span></div>
      ${tol!=null?`<div class="step"><span class="lab">容許誤差</span><span class="val">± ${money(tol)}　差距 ${diff!=null?money(diff):"—"}</span></div>`:""}
      <div class="step key"><span class="lab">決定判決</span><span><span class="decision">${VLAB[ck.program_verdict]||(ck.program_verdict==="unchecked"?"不判斷":esc(ck.program_verdict))}</span>${why?"　"+why:""}${ck.period_ambiguous?"　期間有歧義":""}</span><span style="font-size:12px;color:var(--muted)">${esc(ck.evidence_summary||"")}</span></div>
    </div>`}).join("");
  const evs=ev.map(e=>`<div class="ev"><div class="evh"><b class="mono">${esc(e.id)} · ${esc(e.entity||e.ticker)}</b><span>${e.tier?`證據等級 ${esc(e.tier)}`:""}${e.restated?" · 曾被修訂":""}</span></div><dl>
     <dt>數字</dt><dd><mark class="n">${money(e.value)}</mark> ${esc(e.unit||"")}</dd>
     <dt>XBRL 概念</dt><dd>${esc(e.concept||e.metric)}</dd>
     <dt>期間</dt><dd>${esc(e.start||"")} → ${esc(e.end||"")}${e.frame?` · SEC frame ${esc(e.frame)}`:""}${e.fiscal_year?` · 財年 ${e.fiscal_year} ${esc(e.fiscal_period||"")}`:""}</dd>
     <dt>來源</dt><dd>${e.derived?"由兩筆申報數字相減推算":`${esc(e.form)} · 申報日 ${esc(e.filed)}`}${e.accn?` · ${esc(e.accn)}`:""}</dd>
     ${e.filing_url?`<dt>原始申報</dt><dd><a href="${esc(e.filing_url)}" target="_blank" rel="noopener">在 SEC EDGAR 開啟</a></dd>`:""}
   </dl></div>`).join("");
  return blocks+(evs?`<div style="display:grid;gap:8px"><span class="eyebrow">引用的 SEC 證據</span>${evs}</div>`:"");
}
