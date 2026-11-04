/** Host-only Playwright worker. Never print an error object or a fill argument. */
import {createRequire} from 'node:module';
import {readFile, writeFile, rename, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

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
    presentation:{viewport:[1920,1080],deviceScaleFactor:1,css_zoom:1.25,cursor:'hidden except click indicator'},
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
      if (url.pathname==='/api/check') {
        if (request.method()!=='POST' || ++checks>1) return route.abort('blockedbyclient');
      }
      return route.continue();
    });
    await context.routeWebSocket('**/*',socket=>socket.close());
    await context.addInitScript(()=>{
      document.addEventListener('DOMContentLoaded',()=>{
        document.documentElement.style.zoom='1.25';
        const style=document.createElement('style');
        style.textContent='*,*::before,*::after{cursor:none!important}html{scroll-behavior:auto!important}';
        document.head.append(style);
        const dot=document.createElement('div');dot.id='record-click';dot.setAttribute('aria-hidden','true');
        dot.style.cssText='position:fixed;z-index:2147483647;pointer-events:none;width:14px;height:14px;border:2px solid #e97628;border-radius:50%;display:none;transform:translate(-50%,-50%)';
        document.body.append(dot);
      },{once:true});
    });
    page=await context.newPage();video=page.video();began=performance.now();
    const hold=ms=>page.waitForTimeout(ms);
    const wheelTo=async target=>{
      const from=await page.evaluate(()=>scrollY);
      const steps=Math.ceil(Math.abs(target-from)/60);
      for(let i=0;i<steps;i++){
        const remaining=target-await page.evaluate(()=>scrollY);
        await page.mouse.wheel(0,Math.sign(remaining)*Math.min(60,Math.abs(remaining)));
        await hold(50);
      }
      await hold(90);
    };
    const frame=async selector=>{
      const target=await page.locator(selector).first().evaluate(el=>{
        const r=el.getBoundingClientRect();
        return Math.max(0,Math.min(document.documentElement.scrollHeight-innerHeight,
          scrollY+r.top-Math.max(50,(innerHeight-r.height)/2)));
      });
      await wheelTo(target);
    };
    const click=async selector=>{
      await frame(selector);
      const box=await page.locator(selector).boundingBox();
      if(!box)throw new Error('click_target_missing');
      await page.evaluate(({x,y})=>{
        const dot=document.querySelector('#record-click'),zoom=1.25;
        dot.style.left=`${x/zoom}px`;dot.style.top=`${y/zoom}px`;dot.style.display='block';
      },{x:box.x+box.width/2,y:box.y+box.height/2});
      await page.locator(selector).click({timeout:5000});
      await hold(220);
      await page.evaluate(()=>document.querySelector('#record-click').style.display='none');
    };
    mark('open_page');
    await page.goto(config.page_url,{waitUntil:'load',timeout:20000});
    await page.evaluate(()=>document.fonts.ready);
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
    mark('check_against_sec');
    const [response]=await Promise.all([
      page.waitForResponse(r=>r.url()===`${origin}/api/check` && r.request().method()==='POST',{timeout:45000}),
      click('#live-submit'),
    ]);
    const result=await response.json();
    report.result=redact(result,secret);report.http_status=response.status();
    mark('validate_live_result');
    if(!response.ok())throw new Error('http_result_not_successful');
    validateLiveResult(result);
    await page.locator('#live-result .trace-verdict').first().waitFor({state:'visible'});
    mark('verdict_hold');
    await frame('#live-result .trace-head');await hold(2500);
    const model=await page.locator('#live-result .trace-head').first().innerText();
    if(!model.includes(result.model))throw new Error('native_model_line_missing');
    report.native_ui={model_line:result.model,provider:result.provider,
      provider_display:'Native form says Baseten; native result heading shows the model ID separately. No model/provider overlay added.'};
    mark('corrected_draft_hold');
    await frame('#live-result .corrected-draft-text');await hold(4000);
    const deleted=await page.locator('#live-result .corrected-draft-text del').allTextContents();
    const corrected=await page.locator('#live-result .corrected-draft-text strong').allTextContents();
    if(!deleted.includes('$416.2 billion') || !corrected.includes('$102.5 billion'))throw new Error('native_correction_missing');
    mark('sec_evidence_hold');
    await frame('#live-result .live-evidence');await hold(3000);
    // Show the actual link without navigating away to SEC or making an SEC request.
    await page.locator('#live-result .live-evidence a').first().hover();await hold(400);
    mark('agent_trace');
    const steps=page.locator('#live-result .trace-step');
    const count=await steps.count();
    report.trace_steps_shown=count;report.tool_calls_shown=0;
    // Director cut: dwell only on the model's tool calls and the final program verdict;
    // the other steps scroll past so the whole live beat fits its 50-second scene.
    for(let i=0;i<count;i++){
      const cls=await steps.nth(i).getAttribute('class');
      const tool=cls.includes('trace-tool_call'), last=i===count-1;
      if(tool)report.tool_calls_shown++;
      if(!tool && !last && i!==0) continue;
      await frame(`#live-result .trace-step:nth-child(${i+1})`);
      await hold(tool?700:300);
    }
    if(report.tool_calls_shown!==result.events.filter(e=>e.kind==='tool_call').length)throw new Error('tool_call_coverage');
    mark('hover_receipt');
    await frame('#live-result .trace-metrics');
    await page.locator('#live-result .trace-metrics').first().hover();await hold(1200);
    report.beat6_actions_end_s=(performance.now()-began)/1000;
    mark('beat6_choreography_gate');
    // Leave two seconds for the recorder's initial frame / encoder start variance.
    if(report.beat6_actions_end_s>56)throw new Error('beat6_actions_exceed_first_58_seconds');
    await hold(Math.max(0,60000-(performance.now()-began)));
    mark('beat9_frame_corrected_draft_and_filing');
    const draft='#live-result .corrected-draft-text', citation='#live-result .correction-citations a';
    const target=await page.evaluate(({draft,citation})=>{
      const a=document.querySelector(draft).getBoundingClientRect();
      const b=document.querySelector(citation).getBoundingClientRect();
      if(b.bottom-a.top>innerHeight-100)throw new Error('draft_and_filing_do_not_fit');
      return Math.max(0,scrollY+a.top-(innerHeight-(b.bottom-a.top))/2);
    },{draft,citation});
    await wheelTo(target);
    const together=await page.evaluate(({draft,citation})=>[draft,citation].every(s=>{
      const r=document.querySelector(s).getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;
    }),{draft,citation});
    if(!together)throw new Error('draft_and_filing_not_in_view');
    const beat9Start=performance.now();
    mark('beat9_corrected_draft_and_filing_hold');await hold(5000);
    mark('beat9_native_footer');await frame('.site-footer');
    report.beat9_footer_at_s=(performance.now()-beat9Start)/1000;
    if(report.beat9_footer_at_s>11.5)throw new Error('footer_exceeds_first_16_seconds');
    await hold(Math.max(4500,17000-(performance.now()-beat9Start)));
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
