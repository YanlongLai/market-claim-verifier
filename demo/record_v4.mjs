/** Host-only Playwright worker. Never print an error object or a fill argument. */
import {createRequire} from 'node:module';
import {readFile, writeFile, rename, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const presentation={viewport:[1920,1080],deviceScaleFactor:1,css_zoom:1.6,
  body_font_px:36,column_css_px:800,cursor:'hidden except click indicator'};
// 36 CSS px × 1.6 capture zoom × the 1.4 presentation crop / 4 = 20.16 px at 480w.
export const captureCSS=`
  *,*::before,*::after{cursor:none!important}html{scroll-behavior:auto!important}
  .live-layout,.try-layout{display:block!important}.live-workspace{width:800px;max-width:100%;margin-inline:auto}.history-panel,aside[class*="history"],[id*="history"]{display:none!important}
  #live-form,#live-result{font-size:36px!important;line-height:1.2!important}
  #live-form :is(label,button,input,textarea,p,span),
  #live-result :is(p,li,small,code,pre,summary,h5,h6,blockquote){font-size:36px!important;line-height:1.2!important}
  #live-result .trace-result{padding:16px}
  #live-result .corrected-draft-text{white-space:normal;line-height:1.2!important}
  #live-result .correction-citations{padding-left:20px;margin-block:8px}
  #live-result .correction-changes{margin-block:8px}
  #live-result .correction-changes p{margin-block:4px}
  #live-result .trace-head .live-small{overflow-wrap:anywhere}
  #live-result .trace-verdict{font-size:56px!important}
  #live-result .trace-step{padding:12px}
  #live-result .trace-data pre{max-height:none;overflow:visible;white-space:pre-wrap}
`;

export async function showTraceAndFiling({page,result,report,mark,frame,click,hold}) {
  mark('agent_trace_expand');
  await click('#live-result .live-trace > summary');
  const trace=page.locator('#live-result .live-trace');
  report.trace_details_open=await trace.evaluate(el=>el.open);
  if(!report.trace_details_open)throw new Error('trace_details_not_open');
  await frame('#live-result .live-receipt');
  mark('trace_model_id_reveal');await hold(700);
  const steps=page.locator('#live-result .trace-step');
  const shown=[];
  for(let i=0;i<result.events.length;i++){
    const event=result.events[i];
    if(event.kind!=='tool_call'&&event.kind!=='verdict')continue;
    const step=steps.nth(i);
    await frame(step);
    if(!await step.isVisible()||!await trace.evaluate(el=>el.open)||!await step.evaluate(el=>{
      const r=el.getBoundingClientRect();return r.top>=120&&r.top<=700&&r.bottom<=1040;
    }))throw new Error('trace_step_hidden_or_cropped');
    mark(event.kind==='tool_call'?`tool_call_${i+1}_reveal`:'program_verdict_reveal');
    shown.push({index:i,kind:event.kind,name:event.name||null,visible:true,hold_ms:700});
    await hold(700);
  }
  report.trace_steps_shown=shown;
  report.tool_calls_shown=shown.filter(e=>e.kind==='tool_call').length;
  report.program_verdict_shown=shown.some(e=>e.kind==='verdict');
  if(!report.tool_calls_shown||!report.program_verdict_shown)throw new Error('trace_coverage');
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
    return scrollY+range.getBoundingClientRect().top-240;
  });
  await frame(pre, target);
  mark('apple_derivation_reveal');await hold(2000);
  const nineMonthsTarget=await pre.evaluate((el,value)=>{
    const index=el.firstChild.textContent.indexOf(`"value": ${value}`);
    if(index<0)throw new Error('nine_month_component_missing');
    const range=document.createRange();range.setStart(el.firstChild,index);range.setEnd(el.firstChild,index+12);
    return scrollY+range.getBoundingClientRect().top-240;
  },raw.components[1].value);
  await frame(pre,nineMonthsTarget);mark('apple_nine_months_reveal');await hold(2000);
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
    presentation,
    privacy:'No screenshot, request-body log, HAR, browser trace or storage export'};
  let browser,context,page,video,secret='',stage='password_file';
  let began=performance.now();
  const mark=label=>{stage=label;report.timings.push({phase:label,at_s:(performance.now()-began)/1000});};
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
      return route.continue();
    });
    await context.routeWebSocket('**/*',socket=>socket.close());
    await context.addInitScript(({presentation,captureCSS})=>{
      document.addEventListener('DOMContentLoaded',()=>{
        document.documentElement.style.zoom=String(presentation.css_zoom);
        const style=document.createElement('style');
        style.textContent=captureCSS;
        document.head.append(style);
        const dot=document.createElement('div');dot.id='record-click';dot.setAttribute('aria-hidden','true');
        dot.style.cssText='position:fixed;z-index:2147483647;pointer-events:none;width:14px;height:14px;border:2px solid #e97628;border-radius:50%;display:none;transform:translate(-50%,-50%)';
        document.body.append(dot);
      },{once:true});
    },{presentation,captureCSS});
    page=await context.newPage();video=page.video();began=performance.now();
    const hold=ms=>page.waitForTimeout(ms);
    const wheelTo=async target=>{
      const from=await page.evaluate(()=>scrollY);
      // Long traversals remain visible but take at most 450 ms, even at 1.6× zoom.
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
          scrollY+r.top-Math.max(200,Math.min(350,770-r.height))));
      });
      await wheelTo(target);
    };
    const click=async selector=>{
      await frame(selector);
      const box=await page.locator(selector).boundingBox();
      if(!box)throw new Error('click_target_missing');
      await page.evaluate(({x,y})=>{
        const dot=document.querySelector('#record-click'),zoom=1.6;
        dot.style.left=`${x/zoom}px`;dot.style.top=`${y/zoom}px`;dot.style.display='block';
      },{x:box.x+box.width/2,y:box.y+box.height/2});
      await page.locator(selector).click({timeout:5000});
      await hold(220);
      await page.evaluate(()=>document.querySelector('#record-click').style.display='none');
    };
    mark('open_page');
    await page.goto(config.page_url,{waitUntil:'load',timeout:20000});
    await page.evaluate(()=>document.fonts.ready);
    report.readability=await page.locator('.live-workspace').first().evaluate(el=>{
      const r=el.getBoundingClientRect();
      return {column_center_x:(r.left+r.right)/2,source_width:r.width,
        playback_body_px:parseFloat(getComputedStyle(document.querySelector('#live-input')).fontSize)*1.6*1.4/4};
    });
    if(Math.abs(report.readability.column_center_x-960)>4||report.readability.playback_body_px<20)
      throw new Error('capture_readability_floor');
    await hold(500);
    await page.waitForFunction(()=>!document.querySelector('#live-input')?.disabled &&
      !document.querySelector('#live-submit')?.disabled,null,{timeout:12000});
    mark('use_apple_example');
    await click('#live-example');
    const input=await page.locator('#live-input').inputValue();
    if(!input.includes('Apple pulled in $416.2 billion') || !input.includes('Amazon') || !input.includes('NVIDIA'))
      throw new Error('wrong_default_example');
    mark('type_masked_password');
    if(await page.locator('#live-password').getAttribute('type')!=='password')throw new Error('unmasked_password');
    await click('#live-password');
    await page.locator('#live-password').pressSequentially(secret,{delay:25});
    if(await page.locator('#live-password').getAttribute('type')!=='password')throw new Error('unmasked_password');
    await frame('#live-submit');
    mark('check_against_sec');const clickedAt=performance.now();
    const [response]=await Promise.all([
      page.waitForResponse(r=>/\/api\/check(-example)?$/.test(r.url()) && r.url().startsWith(origin) && r.request().method()==='POST',{timeout:90000}),
      click('#live-submit'),
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
      provider_display:'Native form says Baseten; native result heading shows the model ID separately. No model/provider overlay added.'};
    await frame('#live-result .corrected-draft-text strong');mark('draft_reveal');await hold(3000);
    const deleted=await page.locator('#live-result .corrected-draft-text del').allTextContents();
    const corrected=await page.locator('#live-result .corrected-draft-text strong').allTextContents();
    if(!deleted.includes('$416.2 billion') || !corrected.includes('$102.5 billion'))throw new Error('native_correction_missing');
    const appleIndex=result.evidence.filter(e=>!e.error).findIndex(e=>e.ticker==='AAPL'&&e.derived);
    await frame(`#live-result .live-evidence-row:nth-child(${appleIndex+1}) .evidence-primary`);
    mark('evidence_reveal');await hold(2000);
    // Show the actual link without navigating away to SEC or making an SEC request.
    await page.locator('#live-result .live-evidence a').first().hover();await hold(400);
    await showTraceAndFiling({page,result,report,mark,frame,click,hold});
    mark('hover_receipt');
    await frame('#live-result .live-receipt');
    await page.locator('#live-result .live-receipt').first().hover();await hold(1200);
    report.beat6_actions_end_s=(performance.now()-began)/1000;
    report.after_click_s=(performance.now()-clickedAt)/1000;
    mark('beat6_choreography_gate');
    // Leave two seconds for the recorder's initial frame / encoder start variance.
    if(report.after_click_s>56||report.beat6_actions_end_s>56)throw new Error('beat6_actions_exceed_first_58_seconds');
    await hold(Math.max(0,60000-(performance.now()-began)));
    mark('beat9_frame_corrected_draft_and_filing');
    let draft='#live-result .corrected-draft-text strong';
    const citation='#live-result .correction-citations';
    // Prefer the draft itself. At the 20px playback floor the whole post and its
    // intervening scope text may not fit with both citations; then hold the native
    // corrected edit within the same draft section, immediately above the filings.
    const span=await page.evaluate(({draft,citation})=>
      document.querySelector(citation).getBoundingClientRect().bottom-
      document.querySelector(draft).getBoundingClientRect().top,{draft,citation});
    if(span>570)draft='#live-result .correction-changes > li > strong';
    report.ending_frame={draft_selector:draft,citation_selector:citation,
      description:'Native corrected draft/edit and both component filing links; held through final frame'};
    const target=await page.evaluate(({draft,citation})=>{
      const a=document.querySelector(draft).getBoundingClientRect();
      const b=document.querySelector(citation).getBoundingClientRect();
      // D4's centred 1.4× crop and the caption panel leave source y=200…770 safe.
      if(b.bottom-a.top>570)throw new Error('draft_and_filing_do_not_fit');
      return Math.max(0,scrollY+a.top-200-(570-(b.bottom-a.top))/2);
    },{draft,citation});
    await wheelTo(target);
    const together=await page.evaluate(({draft,citation})=>[draft,citation].every(s=>{
      const r=document.querySelector(s).getBoundingClientRect();return r.top>=200&&r.bottom<=770;
    }),{draft,citation});
    if(!together)throw new Error('draft_and_filing_not_in_view');
    const beat9Start=performance.now();
    // Director D5: the film ends on the working result. Hold the corrected draft and its
    // filing link for the whole scene; the URL is overlaid by the motion system, not the footer.
    mark('beat9_corrected_draft_and_filing_hold');
    await hold(Math.max(15000,17000-(performance.now()-beat9Start)));
    report.beat9_footer_at_s=null;
    report.beat9_span_s=(performance.now()-beat9Start)/1000;
    report.status='captured';
  } catch {
    report.status='failed';report.failure_stage=stage;
    report.failure='Attempt retained; no automatic retry. No raw exception or credential is logged.';
  } finally {
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
