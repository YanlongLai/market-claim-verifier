#!/usr/bin/env node
/** Host-only PNG stills/sequences. No browser is launched when this module is imported. */
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {launch, restrictNetwork} from '../capture/browser.mjs';
import {checkLayout} from './layout-checks.mjs';

export function parseArgs(args) {
  const out={times:[],fps:30};
  for(let i=0;i<args.length;i++) {
    const flag=args[i], value=args[++i];
    if(!['--t','--from','--to','--fps','--out'].includes(flag)||value===undefined) throw new Error('Usage: node render.mjs --t 3 --t 65 --t 155 --out dir | --from A --to B --fps 30 --out dir');
    if(flag==='--out') out.out=path.resolve(value);
    else {
      const n=Number(value); if(!Number.isFinite(n)) throw new Error('Times/fps must be finite');
      if(flag==='--t') out.times.push(n); else out[flag.slice(2)]=n;
    }
  }
  const sequence=out.from!==undefined||out.to!==undefined;
  if(!out.out||(!sequence&&!out.times.length)||sequence&&out.times.length) throw new Error('Choose still times OR a frame sequence, and --out');
  if(!Number.isInteger(out.fps)||out.fps<1||out.fps>120) throw new Error('fps must be an integer in 1..120');
  if(sequence&&(!Number.isFinite(out.from)||!Number.isFinite(out.to)||out.from<0||out.to<=out.from)) throw new Error('Require 0 <= from < to');
  if(out.times.some(t=>t<0)) throw new Error('Still times must be nonnegative');
  return {...out,sequence};
}
export function sampleTimes(options) {
  return options.sequence ? Array.from({length:Math.ceil((options.to-options.from)*options.fps-1e-8)},(_,i)=>options.from+i/options.fps) : options.times;
}
export function frameName(i,t,sequence) {
  return sequence?`frame-${String(i).padStart(6,'0')}.png`:`keyframe-${String(i+1).padStart(2,'0')}-${t.toFixed(3).replace('.','p')}s.png`;
}
export async function renderFrames(options) {
  const times=sampleTimes(options), entry=path.join(path.dirname(fileURLToPath(import.meta.url)),'index.html');
  await mkdir(options.out,{recursive:true});
  const browser=await launch();
  try {
    const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,colorScheme:'dark',serviceWorkers:'block',reducedMotion:'reduce'});
    await restrictNetwork(context,true);
    const page=await context.newPage();
    const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(pathToFileURL(entry).href,{waitUntil:'load'});
    await page.evaluate(async()=>{await document.fonts.ready;if(!window.motionReady)throw new Error('Motion data is missing. Run build.py keyframes to inline it.');});
    const timeline=await page.evaluate(()=>window.timeline);
    if(times.some(t=>t>timeline.duration+1e-8)) throw new Error(`Requested time exceeds timeline duration ${timeline.duration}`);
    const frames=[];
    for(let i=0;i<times.length;i++) {
      const t=times[i];
      const state=await page.evaluate(t=>window.seek(t),t); // seek is synchronous; screenshot flushes layout.
      if(errors.length) throw new Error(errors.join('\n'));
      const layout=await checkLayout(page);
      const name=frameName(i,t,options.sequence);
      await page.screenshot({path:path.join(options.out,name),type:'png',animations:'disabled',fullPage:false});
      frames.push({file:name,t,shot:state.shot,layout});
      if(i%60===0) console.log(`frame ${i+1}/${times.length} @ ${t.toFixed(3)}s (${state.shot})`);
    }
    const report={viewport:[1920,1080],deviceScaleFactor:1,fps:options.fps,sequence:options.sequence,
      from:options.sequence?options.from:null,to:options.sequence?options.to:null,timeline,frames};
    await writeFile(path.join(options.out,'render.json'),JSON.stringify(report,null,2)+'\n');
    return report;
  } finally { await browser.close(); }
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  try { const report=await renderFrames(parseArgs(process.argv.slice(2))); console.log(`Rendered ${report.frames.length} PNG(s).`); }
  catch(error) { console.error(error.message); process.exitCode=1; }
}
