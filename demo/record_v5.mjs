/** Host-only Playwright worker. Never print an error object or a fill argument. */
import {createRequire} from 'node:module';
import {readFile, writeFile, rename, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const presentation={viewport:[1920,1080],deviceScaleFactor:1,css_zoom:1.95,
  body_font_px:30,column_css_px:800,cursor:'hidden except click indicator',playback_scale:1};
export const captureVersion=7;
// Delivered in the document's first head bytes, before site CSS or scripts can paint.
// Hiding the body preserves layout, so geometry can be audited under the cover.
export const captureCoverCSS='html{background:#f7f5ef!important}body{visibility:hidden!important}html::after{content:"";position:fixed;inset:0;background:#f7f5ef!important;z-index:2147483647;visibility:visible!important}html[data-capture-ready="true"] body{visibility:visible!important}html[data-capture-ready="true"]::after{display:none!important}';
export function coverDocument(html){
  if(!/<head(?:\s[^>]*)?>/i.test(html))throw new Error('capture_document_head_missing');
  return html.replace(/<head(?:\s[^>]*)?>/i,head=>`${head}<style id="capture-boot-cover">${captureCoverCSS}</style>`);
}
export const captureCSS=`
  *,*::before,*::after{cursor:none!important}html{scroll-behavior:auto!important}
  .language-switch,[data-language],[hreflang^="zh"],[lang^="zh"]{display:none!important}
  body{margin:0!important;min-width:0!important}header{position:static!important}
  .shell{width:100%!important;max-width:none!important;margin-inline:auto!important;padding-inline:0!important}
  .live-layout,.try-layout{display:block!important}
  .live-workspace{box-sizing:border-box;width:800px!important;max-width:none!important;margin-inline:auto!important}
  .history-panel,aside[class*="history"],[id*="history"]{display:none!important}
  #live-form,#live-result{font-size:30px!important;line-height:1.18!important}
  #live-form :is(label,button,input,textarea,p,span),
  #live-result :is(p,li,small,code,pre,summary,h5,h6,blockquote){font-size:30px!important;line-height:1.18!important}
  #live-result .trace-result{padding:16px}
  #live-result .corrected-draft-text{white-space:normal;line-height:1.18!important}
  #live-result .correction-citations{padding-left:16px;margin-block:6px}
  #live-result .correction-citations li{font-size:24px!important}
  #live-result .correction-changes{margin-block:6px}
  #live-result .correction-changes p{margin-block:4px}
  #live-result .trace-head .live-small{overflow-wrap:anywhere}
  #live-result .trace-verdict{font-size:56px!important}
  #live-result .trace-step{padding:12px}
  #live-result .trace-step code,#live-result .trace-step .trace-time{font-size:24px!important}
  #live-result .trace-data pre{max-height:none;overflow:visible;white-space:pre-wrap}
`;
export const hasCJK=text=>/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u.test(text);
// This function is serialized by Playwright, so every browser dependency is local.
export function installCaptureDOM({presentation,captureCSS}){
  const cjk=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
  let removed=0;
  function sanitize(){
    document.querySelectorAll('.language-switch').forEach(el=>el.remove());
    const walker=document.createTreeWalker(document,NodeFilter.SHOW_TEXT);
    for(let node;node=walker.nextNode();){
      if(['SCRIPT','STYLE'].includes(node.parentElement?.tagName))continue;
      if(cjk.test(node.textContent)){node.textContent='';removed++;}
    }
    document.querySelectorAll('*').forEach(el=>{
      for(const attr of ['title','alt','placeholder','aria-label'])if(cjk.test(el.getAttribute(attr)||'')){el.removeAttribute(attr);removed++;}
    });
  }
  function scan(){
    sanitize();let textNodes=0,attributes=0;
    const walker=document.createTreeWalker(document,NodeFilter.SHOW_TEXT);
    for(let node;node=walker.nextNode();)if(!['SCRIPT','STYLE'].includes(node.parentElement?.tagName)&&cjk.test(node.textContent))textNodes++;
    document.querySelectorAll('*').forEach(el=>{for(const name of ['title','alt','placeholder','aria-label'])if(cjk.test(el.getAttribute(name)||''))attributes++;});
    return {text_nodes:textNodes,attributes,removed,language_switches:document.querySelectorAll('.language-switch').length};
  }
  window.captureLanguageScan=scan;
  const observer=new MutationObserver(sanitize);observer.observe(document,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','alt','placeholder','aria-label']});
  document.addEventListener('DOMContentLoaded',()=>{
    document.documentElement.lang='en';document.documentElement.style.zoom=String(presentation.css_zoom);
    const style=document.createElement('style');style.id='capture-layout';style.textContent=captureCSS;document.head.append(style);
    const dot=document.createElement('div');dot.id='record-click';dot.setAttribute('aria-hidden','true');
    dot.style.cssText='position:fixed;z-index:2147483647;pointer-events:none;width:14px;height:14px;border:2px solid #e97628;border-radius:50%;display:none;transform:translate(-50%,-50%)';
    document.body.append(dot);sanitize();
  },{once:true});
}
export function revealCaptureDOM(){
  const cover=getComputedStyle(document.documentElement,'::after');
  if(!document.querySelector('#capture-boot-cover')||!document.querySelector('#capture-layout')||
      Number(document.documentElement.style.zoom)!==1.95||getComputedStyle(document.body).visibility!=='hidden'||
      cover.backgroundColor!=='rgb(247, 245, 239)'||cover.visibility!=='visible'||cover.display==='none')
    throw new Error('capture_cover_or_layout_missing');
  document.documentElement.dataset.captureReady='true';
  return {cover_present:true,cover_opaque:true,layout_installed:true,zoom:Number(document.documentElement.style.zoom)};
}

export function namedSelectors(phase,result){
  const primary='#live-result ';
  const fixed={
    use_apple_example:[['post','#live-input']],
    check_against_sec:[['Run check','#live-submit']],
    verdict_reveal:[['verdict',primary+'.trace-verdict']],
    draft_reveal:[['corrected number',primary+'.corrected-draft-text strong']],
    agent_trace_expand:[['trace model and receipt',primary+'.live-receipt']],
    hover_receipt:[['receipt',primary+'.live-receipt']],
  };
  if(phase==='evidence_reveal'){
    const index=(result?.evidence||[]).filter(e=>!e.error).findIndex(e=>e.ticker==='AAPL'&&e.derived);
    if(index<0)throw new Error('named_apple_evidence_missing');
    return [['SEC evidence row',`${primary}.live-evidence-row:nth-child(${index+1}) .evidence-primary`]];
  }
  const step=/^tool_call_(\d+)_reveal$/.exec(phase);
  if(step)return [[`trace tool call ${step[1]}`,`${primary}.trace-step`,Number(step[1])-1]];
  if(phase==='program_verdict_reveal')return [['program verdict',`${primary}.trace-step`,result.events.findIndex(e=>e.kind==='verdict')]];
  return fixed[phase]||[];
}
export async function captureNamedElements(page,phase,result,at_s){
  const specs=namedSelectors(phase,result);
  if(!specs.length)return null;
  const elements=await page.evaluate(specs=>specs.map(([name,selector,index=0])=>{
    const el=document.querySelectorAll(selector)[index];
    if(!el)throw new Error('named_element_missing');
    const r=el.getBoundingClientRect();
    if(r.width<=0||r.height<=0||r.left<60||r.right>1860||r.top<0||r.bottom>558)
      throw new Error('named_element_outside_picture');
    return {name,selector,index,left:r.left,right:r.right,top:r.top,bottom:r.bottom};
  }),specs);
  return {phase,at_s,elements};
}
export function validateGeometry(g){
  if(!['source_width','left_margin','right_margin','horizontal_overflow'].every(k=>Number.isFinite(g[k]))||g.source_width<1500||g.left_margin<60||g.right_margin<60||Math.abs(g.left_margin-g.right_margin)>4||g.horizontal_overflow>1)throw new Error('workspace_must_be_full_width_and_centred');
}

export async function showTraceAndFiling({page,result,report,mark,frame,click,hold}) {
  await click('#live-result .live-trace > summary');
  const trace=page.locator('#live-result .live-trace');
  report.trace_details_open=await trace.evaluate(el=>el.open);
  if(!report.trace_details_open)throw new Error('trace_details_not_open');
  await frame('#live-result .live-receipt');
  mark('agent_trace_expand');await hold(700);
  mark('trace_model_id_reveal');await hold(700);
  const steps=page.locator('#live-result .trace-step');
  const shown=[];
  for(let i=0;i<result.events.length;i++){
    const event=result.events[i];
    if(event.kind!=='tool_call'&&event.kind!=='verdict')continue;
    const step=steps.nth(i);
    await frame(step);
    const stepBox=await step.evaluate(el=>{const r=el.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom].map(Math.round);});
    if(!await step.isVisible()||!await trace.evaluate(el=>el.open)||!(stepBox[0]>=60&&stepBox[2]<=1860&&stepBox[1]>=70&&stepBox[1]<=520&&stepBox[3]<=548)){
      report.trace_step_failure={index:i,kind:event.kind,box:stepBox,band:[60,70,1860,548]};
      throw new Error('trace_step_hidden_or_cropped');
    }
    mark(event.kind==='tool_call'?`tool_call_${i+1}_reveal`:'program_verdict_reveal');
    shown.push({index:i,kind:event.kind,name:event.name||null,visible:true,hold_ms:700});
    await hold(700);
  }
  report.trace_steps_shown=shown;
  report.tool_calls_shown=shown.filter(e=>e.kind==='tool_call').length;
  report.program_verdict_shown=shown.some(e=>e.kind==='verdict');
  if(report.tool_calls_shown!==4||!report.program_verdict_shown)throw new Error('trace_coverage');
  if(report.tool_calls_shown!==result.events.filter(e=>e.kind==='tool_call').length)throw new Error('tool_call_coverage');
  // The Apple quarter is derived from the two actual filing components. Inspect the
  // native JSON, including its derivation; no SEC navigation or fabricated overlay.
  const evidence=(result.evidence||[]).filter(e=>!e.error);
  const index=evidence.findIndex(e=>e.ticker==='AAPL'&&e.derived&&e.components?.length===2);
  if(index<0)throw new Error('apple_derivation_missing');
  const fact=evidence[index];
  await click(`#live-result .live-evidence-row:nth-child(${index+1}) .evidence-data > summary`);
  const details=page.locator('#live-result .live-evidence-row').nth(index).locator('details');
  report.apple_inspect_open=await details.evaluate(el=>el.open);
  if(!report.apple_inspect_open)throw new Error('apple_inspect_closed');
  const pre=details.locator('pre');
  const raw=JSON.parse(await pre.innerText());
  if(raw.derivation!==fact.derivation||raw.components[0].value-raw.components[1].value!==raw.value)
    throw new Error('apple_annual_minus_nine_months');
  // Scroll to the actual derivation line inside the unmodified native <pre>.
  const target=await pre.evaluate(el=>{
    const index=el.firstChild.textContent.indexOf('"derivation"');
    if(index<0)throw new Error('derivation_line_missing');
    const range=document.createRange();range.setStart(el.firstChild,index);range.setEnd(el.firstChild,index+12);
    return scrollY+range.getBoundingClientRect().top-140;
  });
  await frame(pre, target);
  mark('apple_derivation_reveal');await hold(2000);
  const nineMonthsTarget=await pre.evaluate((el,value)=>{
    const index=el.firstChild.textContent.indexOf(`"value": ${value}`);
    if(index<0)throw new Error('nine_month_component_missing');
    const range=document.createRange();range.setStart(el.firstChild,index);range.setEnd(el.firstChild,index+12);
    return scrollY+range.getBoundingClientRect().top-140;
  },raw.components[1].value);
  await frame(pre,nineMonthsTarget);mark('apple_nine_months_reveal');await hold(1500);
  report.apple_derivation={evidence_id:fact.evidence_id,derivation:raw.derivation,
    annual:raw.components[0].value,nine_months:raw.components[1].value,quarter:raw.value,hold_ms:2000};
}

export function redact(value, secret='') {
  if (Array.isArray(value)) return value.map(item=>redact(item,secret));
  if (value && typeof value==='object') return Object.fromEntries(Object.entries(value)
    .filter(([key])=>!/password|secret|authorization|cookie|credential|balance|budget/i.test(key) &&
      !/^(?:access_token|refresh_token|id_token|api_key|token)$/i.test(key))
    .map(([key,item])=>[secret?key.split(secret).join('[REDACTED]'):key,redact(item,secret)]));
  return typeof value==='string' && secret ? value.split(secret).join('[REDACTED]') : value;
}

export function endingExpectedLinks(result){
  const edit=result.corrections?.edits?.find(e=>e.original==='$416.2 billion'&&e.replacement==='$102.5 billion');
  const links=(edit?.citations||[]).filter(c=>['10-K','10-Q'].includes(c.form)&&/^https:\/\/www\.sec\.gov\/Archives\//.test(c.url||''));
  if(!['10-K','10-Q'].every(form=>links.some(c=>c.form===form))||new Set(links.map(c=>c.url)).size<2)throw new Error('both_component_filing_links_required');
  return [...new Set(links.map(c=>c.url))];
}
export function validateLiveResult(result) {
  if (result.mode!=='live' || result.provider!=='baseten' ||
      result.model!=='meta-models/muse-spark-open-1026' || result.verdict!=='contradicted' || result.error)
    throw new Error('live_result_contract');
  if (!result.corrections?.edits?.some(edit=>edit.original==='$416.2 billion' && edit.replacement==='$102.5 billion'))
    throw new Error('required_correction_missing');
  if (!result.events?.some(event=>event.kind==='tool_call') ||
      !result.evidence?.some(fact=>/^https:\/\/www\.sec\.gov\/Archives\//.test(fact.filing_url||'')))
    throw new Error('evidence_or_tools_missing');
  if (!Number.isFinite(result.cost_usd) || !Number.isFinite(result.latency_ms))
    throw new Error('measured_receipt_missing');
}

function playwright() {
  if (!process.env.PLAYWRIGHT_MODULE) throw new Error('module_missing');
  const require=createRequire(import.meta.url);
  const module=require(process.env.PLAYWRIGHT_MODULE);
  const version=require(path.join(process.env.PLAYWRIGHT_MODULE,'package.json')).version;
  return {chromium:module.chromium,version};
}

export async function record(config) {
  const report={status:'started',page_url:config.page_url,timings:[],live_check_limit:1,
    recording:'Playwright recordVideo, one continuous page; beat9 is its continuous final segment',
    capture_version:captureVersion,presentation,geometry_checks:[],language_checks:[],named_element_checks:[],
    privacy:'No screenshot, request-body log, HAR, browser trace or storage export'};
  let browser,context,page,video,secret='',stage='password_file';
  let began=performance.now();
  const namedPending=[];
  const mark=label=>{
    stage=label;const at_s=(performance.now()-began)/1000;report.timings.push({phase:label,at_s});
    if(page)namedPending.push(captureNamedElements(page,label,report.result,at_s).then(check=>{if(check)report.named_element_checks.push(check);}).catch(()=>{report.named_element_failure=label;}));
  };
  try {
    secret=(await readFile(process.env.LIVE_CHECK_PASSWORD_FILE,'utf8')).replace(/[\r\n]+$/g,'');
    if (!secret || /[\r\n]/.test(secret)) throw new Error('password_file_invalid');
    const engine=playwright(); report.playwright_version=engine.version;
    mark('browser_launch');
    browser=await engine.chromium.launch({headless:true});
    const videoDir=path.join(config.out,`session-${config.stamp}`);
    await mkdir(videoDir,{recursive:true});
    context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,
      colorScheme:'light',serviceWorkers:'block',recordVideo:{dir:videoDir,size:{width:1920,height:1080}}});
    let checks=0;
    const origin=new URL(config.page_url).origin;
    await context.route('**/*',async route=>{
      const request=route.request(), url=new URL(request.url());
      if (url.origin!==origin) return route.abort('blockedbyclient');
      if (url.pathname==='/api/check' || url.pathname==='/api/check-example') {
        if (request.method()!=='POST' || ++checks>1) return route.abort('blockedbyclient');
      }
      if(request.resourceType()==='document'&&url.pathname==='/'){
        const response=await route.fetch();
        const html=coverDocument(await response.text());
        report.startup_cover={injected_before_content:true,colour:'#f7f5ef',release_geometry_index:null};
        return route.fulfill({response,body:html});
      }
      return route.continue();
    });
    await context.routeWebSocket('**/*',socket=>socket.close());
    await context.addInitScript(installCaptureDOM,{presentation,captureCSS});
    page=await context.newPage();video=page.video();began=performance.now();
    const audit=async()=>{
      const scan=await page.evaluate(()=>window.captureLanguageScan());
      if(scan.text_nodes||scan.attributes||scan.language_switches)throw new Error('capture_language_purity');
      report.language_checks.push({at_s:(performance.now()-began)/1000,...scan});
      const g=await page.locator('.live-workspace').first().evaluate(el=>{
        const r=el.getBoundingClientRect();return {source_width:r.width,left_margin:r.left,right_margin:innerWidth-r.right,column_center_x:(r.left+r.right)/2,horizontal_overflow:Math.max(0,document.documentElement.scrollWidth-document.documentElement.clientWidth),zoom:Number(document.documentElement.style.zoom)};
      });
      validateGeometry(g);report.geometry_checks.push({at_s:(performance.now()-began)/1000,...g});
    };
    const hold=async ms=>{await page.waitForTimeout(ms);await audit();};
    const wheelTo=async target=>{
      const from=await page.evaluate(()=>scrollY);
      // Long traversals remain visible but take at most 450 ms, at the capture zoom.
      const steps=Math.max(1,Math.min(9,Math.ceil(Math.abs(target-from)/120)));
      for(let i=0;i<steps;i++){
        const remaining=target-await page.evaluate(()=>scrollY);
        await page.mouse.wheel(0,remaining/(steps-i));
        await hold(50);
      }
      await hold(90);
    };
    const frame=async (selector,explicitTarget)=>{
      const locator=typeof selector==='string'?page.locator(selector).first():selector;
      const target=explicitTarget??await locator.evaluate(el=>{
        const r=el.getBoundingClientRect();
        return Math.max(0,Math.min(document.documentElement.scrollHeight-innerHeight,
          scrollY+r.top-Math.max(80,Math.min(180,540-r.height))));
      });
      await wheelTo(target);
    };
    const click=async selector=>{
      await frame(selector);
      const box=await page.locator(selector).boundingBox();
      if(!box)throw new Error('click_target_missing');
      await page.evaluate(({x,y})=>{
        const dot=document.querySelector('#record-click'),zoom=1.95;
        dot.style.left=`${x/zoom}px`;dot.style.top=`${y/zoom}px`;dot.style.display='block';
      },{x:box.x+box.width/2,y:box.y+box.height/2});
      await page.locator(selector).click({timeout:5000});
      await hold(220);
      await page.evaluate(()=>document.querySelector('#record-click').style.display='none');
    };
    mark('open_page');
    await page.goto(config.page_url,{waitUntil:'load',timeout:20000});
    await page.evaluate(()=>document.fonts.ready);
    await audit();
    const release=await page.evaluate(revealCaptureDOM);
    report.startup_cover={...report.startup_cover,...release,release_geometry_index:report.geometry_checks.length-1,released_at_s:(performance.now()-began)/1000};
    report.readability={...report.geometry_checks.at(-1),playback_body_px:presentation.body_font_px*presentation.css_zoom/4};
    await hold(500);
    await page.waitForFunction(()=>!document.querySelector('#live-input')?.disabled &&
      !document.querySelector('#live-submit')?.disabled,null,{timeout:12000});
    await click('#live-example');
    await frame('#live-input');
    mark('use_apple_example');await hold(3200);
    const input=await page.locator('#live-input').inputValue();
    if(!input.includes('Apple pulled in $416.2 billion') || !input.includes('Amazon') || !input.includes('NVIDIA'))
      throw new Error('wrong_default_example');
    mark('type_masked_password');
    if(await page.locator('#live-password').getAttribute('type')!=='password')throw new Error('unmasked_password');
    await click('#live-password');
    await page.locator('#live-password').pressSequentially(secret,{delay:25});
    if(await page.locator('#live-password').getAttribute('type')!=='password')throw new Error('unmasked_password');
    await frame('#live-submit');
    const clickedAt=performance.now();
    const [response]=await Promise.all([
      page.waitForResponse(r=>/\/api\/check(-example)?$/.test(r.url()) && r.url().startsWith(origin) && r.request().method()==='POST',{timeout:90000}),
      click('#live-submit').then(()=>mark('check_against_sec')),
    ]);
    const result=await response.json();
    report.result=redact(result,secret);report.http_status=response.status();
    mark('validate_live_result');
    if(!response.ok())throw new Error('http_result_not_successful');
    validateLiveResult(result);
    await page.locator('#live-result .trace-verdict').first().waitFor({state:'visible'});
    await frame('#live-result .trace-verdict');mark('verdict_reveal');await hold(2500);
    const model=(await page.locator('#live-result .live-receipt, #live-result .trace-head').allInnerTexts()).join(' ');
    if(!model.includes(result.model))throw new Error('native_model_line_missing');
    report.native_ui={model_line:result.model,provider:result.provider,
      provider_display:'Native form says Baseten; native result heading shows the model ID separately. Model/provider also named by the receipt-bound motion card.'};
    await frame('#live-result .corrected-draft-text strong');mark('draft_reveal');await hold(3300);
    const deleted=await page.locator('#live-result .corrected-draft-text del').allTextContents();
    const corrected=await page.locator('#live-result .corrected-draft-text strong').allTextContents();
    if(!deleted.includes('$416.2 billion') || !corrected.includes('$102.5 billion'))throw new Error('native_correction_missing');
    const appleIndex=result.evidence.filter(e=>!e.error).findIndex(e=>e.ticker==='AAPL'&&e.derived);
    await frame(`#live-result .live-evidence-row:nth-child(${appleIndex+1}) .evidence-primary`);
    mark('evidence_reveal');await hold(6200);
    // Show the actual link without navigating away to SEC or making an SEC request.
    await page.locator('#live-result .live-evidence a').first().hover();await hold(400);
    await showTraceAndFiling({page,result,report,mark,frame,click,hold});
    await frame('#live-result .live-receipt');
    await page.locator('#live-result .live-receipt').first().hover();mark('hover_receipt');await hold(800);
    report.beat6_actions_end_s=(performance.now()-began)/1000;
    report.after_click_s=(performance.now()-clickedAt)/1000;
    mark('beat6_choreography_gate');
    // Leave two seconds for the recorder's initial frame / encoder start variance.
    if(report.after_click_s>56||report.beat6_actions_end_s>56)throw new Error('beat6_actions_exceed_first_58_seconds');
    await hold(Math.max(0,60000-(performance.now()-began)));
    mark('beat9_frame_corrected_draft_and_filing');
    let draft='#live-result .corrected-draft-text strong';
    const citation='#live-result .correction-citations';
    // Prefer the draft itself. At the full-frame capture size the whole post and its
    // intervening scope text may not fit with both citations; then hold the native
    // corrected edit within the same draft section, immediately above the filings.
    const span=await page.evaluate(({draft,citation})=>
      document.querySelector(citation).getBoundingClientRect().bottom-
      document.querySelector(draft).getBoundingClientRect().top,{draft,citation});
    if(span>480)draft='#live-result .correction-changes > li > strong';
    report.ending_frame={draft_selector:draft,citation_selector:citation,
      description:'Native corrected draft/edit and both component filing links; held through final frame'};
    const target=await page.evaluate(({draft,citation})=>{
      const a=document.querySelector(draft).getBoundingClientRect();
      const b=document.querySelector(citation).getBoundingClientRect();
      // Keep both native links above the motion overlay and chapter/caption lanes.
      if(b.bottom-a.top>480)throw new Error('draft_and_filing_do_not_fit');
      return Math.max(0,scrollY+a.top-80-(480-(b.bottom-a.top))/2);
    },{draft,citation});
    await wheelTo(target);
    const together=await page.evaluate(({draft,citation})=>[draft,citation].every(s=>{
      const r=document.querySelector(s).getBoundingClientRect();return r.left>=60&&r.right<=1860&&r.top>=80&&r.bottom<=586;
    }),{draft,citation});
    if(!together)throw new Error('draft_and_filing_not_in_view');
    const beat9Start=performance.now();
    // Director D5: the film ends on the working result. Hold the corrected draft and its
    // filing link for the whole scene; the URL is overlaid by the motion system, not the footer.
    mark('beat9_corrected_draft_and_filing_hold');
    await hold(Math.max(15000,17000-(performance.now()-beat9Start)));
    const links=await page.locator(`${citation} a`).evaluateAll(elements=>elements.map(el=>{
      const r=el.getBoundingClientRect();return {href:el.href,left:r.left,right:r.right,top:r.top,bottom:r.bottom};
    }));
    const expected=endingExpectedLinks(result);
    if(expected.some(url=>!links.some(l=>l.href===url&&l.left>=60&&l.right<=1860&&l.top>=80&&l.bottom<=586)))throw new Error('both_component_filing_links_required');
    report.ending_frame.both_links=expected.length;report.ending_frame.links=links;
    report.ending_frame.named_elements=await page.evaluate(({draft,citation})=>[draft,citation].map(selector=>{
      const r=document.querySelector(selector).getBoundingClientRect();
      return {name:selector,selector,left:r.left,right:r.right,top:r.top,bottom:r.bottom};
    }),{draft,citation});
    report.ending_frame.visible_together=true;
    await audit();
    report.beat9_footer_at_s=null;
    report.beat9_span_s=(performance.now()-beat9Start)/1000;
    report.live_checks=checks;
    if(checks!==1)throw new Error('exactly_one_live_check');
    await Promise.all(namedPending);
    if(report.named_element_failure)throw new Error('named_element_audit_failed');
    report.named_element_checks.sort((a,b)=>a.at_s-b.at_s);
    report.status='captured';
  } catch {
    report.status='failed';report.failure_stage=stage;
    report.failure='Attempt retained; no automatic retry. No raw exception or credential is logged.';
  } finally {
    await Promise.allSettled(namedPending);
    try {await context?.close();}catch{}
    try {await browser?.close();}catch{}
    if(video){
      try {
        const file=await video.path(), target=path.join(config.out,`beat6-${config.stamp}.webm`);
        await rename(file,target);report.video=path.basename(target);
      }catch{report.status='failed';report.failure_stage='save_video';}
    }
    await writeFile(config.receipt,JSON.stringify(redact(report,secret),null,2)+'\n',{flag:'wx'});
  }
  return report.status==='captured';
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try {
    if(process.argv[2]==='--preflight'){
      const browser=await playwright().chromium.launch({headless:true});await browser.close();
    }else{
      const config=JSON.parse(await readFile(process.argv[2],'utf8'));
      if(!await record(config))process.exitCode=1;
    }
  }catch{process.exitCode=1;}
}
