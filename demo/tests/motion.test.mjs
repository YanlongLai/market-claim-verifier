import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';
import {parseArgs,sampleTimes,frameName} from '../motion/render.mjs';
const require=createRequire(import.meta.url), L=require('../motion/logic.js');
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
const json=p=>JSON.parse(read(p));
const raw=json('../assets/beats-seed92.json'), {offset,beats}=L.normalizeBeats(raw);
const timing=json('../motion/timing.json');

test('easing clamps, settles exactly, back overshoots, push is symmetric',()=>{
  for(const ease of [L.easeInOut,L.easeOutBack]) {
    assert.equal(ease(-2),0); assert.equal(ease(0),0); assert.equal(ease(1),1); assert.equal(ease(2),1);
  }
  assert(L.easeOutBack(.7)>1);
  for(const x of [.1,.2,.3,.6,.8]) assert(Math.abs(L.easeInOut(x)+L.easeInOut(1-x)-1)<1e-12);
  assert.equal(L.progress(5,5),0); assert.equal(L.progress(5.25,5),1);
});
test('detected beats align video zero; fitted metadata never shifts music',()=>{
  assert.equal(offset,9.4041); assert.notEqual(offset,raw.first_beat_s); assert.equal(beats[0],0);
  const b=L.beatHelpers(beats);
  assert.equal(b.beatAt(2),.9288); assert.equal(b.nearestBeat(.3),.4644);
  assert.equal(b.onOrAfter(.465),.9288); assert.equal(b.onOrAfter(.4644),.4644);
  assert.throws(()=>b.beatAt(-1)); assert.throws(()=>b.onOrAfter(999));
  assert.throws(()=>L.beatHelpers([0,0])); assert.throws(()=>b.nearestBeat(NaN));
});
test('target timing and real narration timing select the FIRST eligible detected beat',()=>{
  const scenes=[{id:'a',target_s:5},{id:'b',target_s:13}];
  assert.deepEqual(L.targetTiming(scenes).shots,[{id:'a',start:0,end:5},{id:'b',start:5,end:18}]);
  const result=L.narrationTiming(scenes,{a:1,b:2},beats);
  let start=0;
  result.shots.forEach((s,i)=>{
    const eligible=beats.find(b=>b>=start+[1,2][i]+.3-1e-9);
    assert.equal(s.start,start);assert.equal(s.end,eligible);start=eligible;
  });
  assert.throws(()=>L.narrationTiming(scenes,{a:0,b:2},beats));
  assert.throws(()=>L.narrationTiming(scenes,{a:1,b:2},beats,.2));
});
test('all pops and flips land on DETECTED beats and complete within .25 s',()=>{
  for(const shot of timing.shots) {
    const events=L.eventsForShot(shot,beats,json('../motion/cues.json')._events[shot.id]);
    for(const value of Object.values(events).flat(Infinity)) assert(beats.includes(value));
  }
  const window=L.testWindow(timing,beats,'m05',2);
  assert(window.from<window.event);assert(window.to>window.event+1);
  assert.equal(window.to-window.from,2); assert.equal(window.shot,'m05-verdicts');
  assert.throws(()=>L.testWindow(timing,beats,'missing'));
});
test('typography/safe bands and palette meet the brief',()=>{
  assert(L.TYPE.body>=56);assert(L.TYPE.number>=96);assert(L.TYPE.headline>=96);
  assert(L.TYPE.safe>=64);assert(L.TYPE.subtitleReserve>=200);
  for(const fg of ['white','muted','mint','coral','amber']) for(const bg of ['navy','panel']) assert(L.contrast(L.PALETTE[fg],L.PALETTE[bg])>=4.5,`${fg} on ${bg}`);
  for(const bg of ['mint','coral','amber']) assert(L.contrast(L.PALETTE.navy,L.PALETTE[bg])>=4.5);
  const css=read('../motion/motion.css');
  assert(!/\b(?:animation|transition)\s*:/.test(css));assert(!/@import|https?:\/\//.test(css));
});
function fakePage() {
  const stage={style:{setProperty(){}},dataset:{},innerHTML:''};
  const context={document:{getElementById:()=>stage},console}; context.window=context;context.globalThis=context;
  vm.createContext(context);
  for(const file of ['logic.js','data.js']) vm.runInContext(read('../motion/'+file),context);
  vm.runInContext(read('../motion/motion.js'),context);
  return {stage,window:context};
}
function eventsFor(window,index) {
  const shot=window.timeline.shots[index];
  return L.eventsForShot(shot,beats,window.MOTION_DATA.cues._events[shot.id]);
}
const plain=html=>html.replace(/<br\s*\/?\s*>|<\/?div\b[^>]*>/g,' ').replace(/<[^>]*>/g,'')
  .replace(/&amp;/g,'&').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&gt;/g,'>').replace(/&lt;/g,'<').replace(/\s+/g,' ');
function styles(html,className) {
  return [...html.matchAll(/<div class="([^"]*)" style="([^"]*)">/g)]
    .filter(m=>m[1].split(' ').includes(className))
    .map(m=>Object.fromEntries(m[2].split(';').filter(Boolean).map(v=>{
      const colon=v.indexOf(':');return [v.slice(0,colon),v.slice(colon+1)];
    })));
}
test('seek renders all ten shots synchronously and is independent of previous seeks',()=>{
  const {stage,window}=fakePage();
  for(const shot of window.timeline.shots) {
    const t=(shot.start+shot.end)/2; window.seek(t);const expected=stage.innerHTML;
    window.seek(0);window.seek(159);window.seek(t);
    assert.equal(stage.innerHTML,expected);assert.equal(stage.dataset.shot,shot.id);
  }
  window.seek(3);assert.match(plain(stage.innerHTML),/Apple made \$416B in one quarter\?/);assert.match(stage.innerHTML,/FALSE/);
  window.seek(65);assert.match(stage.innerHTML,/Apple/);assert.match(plain(stage.innerHTML),/Post says \$416.2B in one quarter/);
  window.seek(155);assert.match(stage.innerHTML,/<svg/);assert.match(stage.innerHTML,/Try the live demo/);
  assert.throws(()=>window.seek(Infinity));assert.throws(()=>window.seek(NaN));
  assert(!/requestAnimationFrame|setInterval|setTimeout|Math\.random|Date\(/.test(read('../motion/motion.js')));
});
test('opening shows a concrete Apple claim and flips to coral FALSE on beat 3',()=>{
  const {stage,window}=fakePage(), event=eventsFor(window,0).verdict;
  assert.equal(event,beats[2]);
  window.seek(event-1/30);
  assert.match(plain(stage.innerHTML),/Apple made \$416B in one quarter\?/);
  assert(!/TRUE|FALSE/.test(stage.innerHTML));
  window.seek(event+.24);
  assert.match(stage.innerHTML,/class="verdict coral"[^>]*>FALSE/);
  assert(!stage.innerHTML.includes('TRUE'));
});
test('number highlighting escapes text AFTER tokenisation and preserves spaced periods',()=>{
  for(const source of ["Amazon's Q3 2023 revenue was $143.1 billion.","NVIDIA's fiscal 2024 revenue was $60.9 billion.","Apple's Q4 2025 revenue."]){
    const html=L.highlightQuote(source);
    assert.equal(plain(html).trim(),source);
    assert(!/<span[^>]*>39<\/span>/.test(html));
    assert(!/&#<span/.test(html));
  }
  assert.match(L.highlightQuote('Q3 2023 and Q4 2025'),/class="period number">Q3 2023<\/span> and <span class="period number">Q4 2025/);
  assert(!L.highlightQuote('Literal &#39; and &amp; stay literal.').includes('class="number"'));
  assert.equal(plain(L.highlightQuote('<img onerror="unsafe"> $50B')).trim(),'<img onerror="unsafe"> $50B');
  assert(!L.highlightQuote('<script>1</script>').includes('<script>'));
  const css=read('../motion/motion.css');
  assert.match(css,/\.period\s*\{[^}]*white-space:nowrap;[^}]*word-spacing:12px/);
});
test('quietly wrong reveals the coral $416B during that phrase',()=>{
  const {stage,window}=fakePage(), events=eventsFor(window,1);
  const cue=window.MOTION_DATA.cues._events['m02-spread'].find(e=>e.event==='tokens.2');
  window.seek(events.tokens[2]-1/30);
  assert.equal(styles(stage.innerHTML,'hook-token')[2].opacity,'0');
  window.seek(events.tokens[2]+.001);
  const tokens=styles(stage.innerHTML,'hook-token');
  assert.deepEqual(tokens.map(s=>s.opacity),['1','1','1']);
  assert.deepEqual(tokens.map(s=>s.color),['var(--mint)','var(--mint)','var(--coral)']);
  assert.equal(cue.cue,'some are quietly wrong');assert(events.tokens[2]<cue.cue_end);
  assert.match(plain(stage.innerHTML),/\$416B Claimed quarter \?/);
  assert.match(plain(stage.innerHTML),/Amazon's/);assert(!plain(stage.innerHTML).includes('&#39;'));
});
test('extraction advances through three exact facts and an explicitly unjudged opinion',()=>{
  const {stage,window}=fakePage(), events=eventsFor(window,3);
  const claims=window.MOTION_DATA.product.english_claims;
  [...events.claims,...events.stamps].forEach((event,i)=>{
    window.seek(event+.24);
    assert(plain(stage.innerHTML).includes(claims[i].quote));
    assert(!plain(stage.innerHTML).includes('&#39;'));
    assert(!stage.innerHTML.includes('undefined'));
    assert.equal(styles(stage.innerHTML,'extraction-status').length,4);
    if(i<3) assert.match(stage.innerHTML,/class="tag mint"/);
    else {
      assert.match(stage.innerHTML,/class="tag not-judged"[^>]*>not judged/);
      assert(!stage.innerHTML.includes('Exact quote extracted'));
    }
  });
});
const bounds=s=>({left:parseFloat(s.left),top:parseFloat(s.top),right:parseFloat(s.left)+parseFloat(s.width),bottom:parseFloat(s.top)+parseFloat(s.height)});
const inSafeArea=r=>r.left>=64&&r.right<=1856&&r.top>=64&&r.bottom<=880;
const overlap=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
test('Apple never overlaps either TRUE card throughout the eight-second push',()=>{
  const {stage,window}=fakePage(), events=eventsFor(window,4), shot=window.timeline.shots[4];
  for(let t=shot.start;t<shot.end;t+=1/30) {
    window.seek(t);
    const cards=styles(stage.innerHTML,'card').filter(c=>Number(c.opacity)>0).map(bounds);
    assert(cards.every(inSafeArea),`safe area at ${t}`);
    for(let i=0;i<cards.length;i++)for(let j=i+1;j<cards.length;j++)assert(!overlap(cards[i],cards[j]),`overlap at ${t}`);
  }
  const start=events.appleFalse+.24;
  window.seek(start+4);const halfway=parseFloat(styles(stage.innerHTML,'apple-card')[0].width);
  window.seek(start+8);const full=parseFloat(styles(stage.innerHTML,'apple-card')[0].width);
  assert(halfway<full);assert(full-halfway<32);
  assert(styles(stage.innerHTML,'card').slice(0,2).every(c=>c.opacity==='1'));
});
test('both Apple correction cues show complete, proportional bars and the 4× explanation',()=>{
  const {stage,window}=fakePage();
  const events=window.MOTION_DATA.cues._events['m05-verdicts'];
  const samples=[65,...events.filter(e=>['appleYear','appleQuarter'].includes(e.event)).flatMap(e=>[e.cue_start,e.t+.3])];
  assert.equal(samples.length,5);
  for(const t of samples){
    window.seek(t);const text=plain(stage.innerHTML);
    for(const phrase of ['Post says $416.2B in one quarter','Fiscal Q4 2025$102.5B','Full fiscal year 2025$416.2B',"4× too high · that's the full year"])assert(text.includes(phrase),`${phrase} at ${t}`);
    const quarter=styles(stage.innerHTML,'apple-quarter-bar')[0],year=styles(stage.innerHTML,'apple-year-bar')[0];
    assert.equal(quarter.opacity,'1');assert.equal(year.opacity,'1');
    assert.equal(quarter.background,'var(--coral)');assert.equal(year.background,'var(--muted)');
    assert(Math.abs(parseFloat(quarter.width)/parseFloat(year.width)-102.466/416.161)<1e-12);
    assert(styles(stage.innerHTML,'card').every(c=>c.opacity==='1'));
    const parent=styles(stage.innerHTML,'apple-card')[0];
    for(const child of ['apple-claim','apple-quarter-bar','apple-year-bar','apple-explanation']){
      const r=bounds(styles(stage.innerHTML,child)[0]);assert(r.right<=parseFloat(parent.width));assert(r.bottom<parseFloat(parent.height));
    }
    assert.match(stage.innerHTML,/font-size:96px;float:right;color:var\(--coral\).*?\$102\.5B/);
  }
});
test('baseline labels and note remain above the subtitle strip at maximum zoom',()=>{
  const {stage,window}=fakePage(), shot=window.timeline.shots[2];window.seek(shot.end-.001);
  const chart=styles(stage.innerHTML,'baseline-chart')[0], zoom=Number(chart.transform.match(/scale\(([^)]+)\)/)[1]);
  const cx=parseFloat(chart.width)/2,cy=parseFloat(chart.height)/2;
  const rect=s=>{
    const left=parseFloat(chart.left)+cx+(parseFloat(s.left)-cx)*zoom;
    const top=parseFloat(chart.top)+cy+(parseFloat(s.top)-cy)*zoom;
    return {left,top,right:left+parseFloat(s.width)*zoom,bottom:top+parseFloat(s.height)*zoom};
  };
  const bars=styles(stage.innerHTML,'baseline-bar').map(rect),counters=styles(stage.innerHTML,'baseline-counter').map(rect);
  const providers=styles(stage.innerHTML,'baseline-provider').map(rect),note=bounds(styles(stage.innerHTML,'baseline-note')[0]);
  for(const r of [...bars,...counters,...providers,note])assert(inSafeArea(r));
  counters.forEach((counter,i)=>assert(counter.bottom+3<=bars[i].top));
  assert(providers.every(p=>p.bottom+20<note.top));assert(note.bottom<=870);
});
test('all narration events resolve to the first eligible detected beat',()=>{
  const {window}=fakePage(), doc=window.MOTION_DATA.cues;
  for(const shot of window.timeline.shots){
    const actualEvents=eventsFor(window,window.timeline.shots.indexOf(shot));
    for(const event of doc._events[shot.id]){
      assert.equal(event.t,L.beatHelpers(beats).onOrAfter(Math.max(shot.start,event.cue_start-.1)));
      let actual=actualEvents;for(const key of event.event.split('.'))actual=actual[key];
      assert.equal(actual,event.t);assert(event.t>=shot.start&&event.t<shot.end);
    }
  }
  const good=doc._events['m05-verdicts'][0];
  assert.throws(()=>L.eventsForShot(window.timeline.shots[4],beats,[{...good,t:good.t+1/30}]),/cue beat/);
});
test('program and results boards occupy at least 60% of the safe area',()=>{
  const {stage,window}=fakePage();
  const safeArea=(1920-2*64)*(1080-64-200);
  for(const [index,className] of [[6,'program-board'],[7,'results-board']]){
    window.seek(window.timeline.shots[index].end-.1);const board=styles(stage.innerHTML,className)[0];
    assert(parseFloat(board.width)*parseFloat(board.height)>=.6*safeArea);
    assert(inSafeArea(bounds(board)));
  }
  const declarations=[...read('../motion/motion.css').matchAll(/font-size:(\d+)px/g)];
  assert(declarations.every(m=>Number(m[1])>=56));
  const inline=[...read('../motion/motion.js').matchAll(/font-size:(\d+)px/g)];
  assert(inline.every(m=>Number(m[1])>=56));
});
test('program rejection and both 90.5% results appear during their spoken cues',()=>{
  const {stage,window}=fakePage(), program=eventsFor(window,6);
  window.seek(program.fake-1/30);assert.match(stage.innerHTML,/fake-evidence coral" style="[^\"]*opacity:0/);
  window.seek(program.fake+.001);assert.match(stage.innerHTML,/fake-evidence coral" style="[^\"]*opacity:1/);assert(plain(stage.innerHTML).includes('E9 ✕'));
  assert.equal(styles(stage.innerHTML,'flow-node').at(-1).opacity,'1');
  const resultEvents=eventsFor(window,7), cue=window.MOTION_DATA.cues._events['m08-results'].find(e=>e.event==='results.1.1');
  assert.equal(cue.cue,'90.5 percent');assert(resultEvents.results[1][1]<cue.cue_end);
  window.seek(resultEvents.results[1][1]-1/30);
  assert.deepEqual(styles(stage.innerHTML,'result-checked').map(s=>s.opacity),['1','0','0']);
  window.seek(resultEvents.results[1][1]+.001);
  assert.deepEqual(styles(stage.innerHTML,'result-checked').map(s=>s.opacity),['1','1','1']);
  assert.equal((stage.innerHTML.match(/font-size:112px">90\.5%/g)||[]).length,2);
  assert(plain(stage.innerHTML).includes('Up to +70.5 points'));
  const badge=styles(stage.innerHTML,'results-badge')[0];assert(inSafeArea(bounds(badge)));
  assert.equal(badge['white-space'],'nowrap');assert(parseFloat(badge.height)>=128);
  const providers=window.MOTION_DATA.product.providers;
  assert.equal(Math.max(...providers.map(r=>r.checked-r.alone)),70.5);
});
test('proof uses the brief\'s two-column quarter close-up with fixed widths and real gutters',()=>{
  const {stage,window}=fakePage();window.seek(window.timeline.shots[5].end-.1);
  const text=plain(stage.innerHTML);
  for(const value of ['143,083','158,877','Total net sales','USD in millions','Three months · Sep 30'])assert(text.includes(value),value);
  for(const value of ['404,824','450,167'])assert(!text.includes(value),value);
  assert.deepEqual(Array.from(window.MOTION_DATA.product.filing.values),['143,083','158,877','404,824','450,167']);
  assert(!/filing-table" style="transform:scale/.test(stage.innerHTML));
  assert.match(read('../motion/motion.css'),/\.filing-table\s*\{\s*width:100%/);
  const css=read('../motion/motion.css');
  assert.match(css,/grid-template-columns:500px 576px 576px; column-gap:48px/);
  assert.match(css,/\.table-cell\s*\{[^}]*justify-content:flex-end;[^}]*font-size:128px;[^}]*font-variant-numeric:tabular-nums/);
  assert.match(css,/\.filing-highlight\s*\{[^}]*inset:0;[^}]*justify-content:flex-end/);
  assert.match(stage.innerHTML,/amzn-20240930\.htm#f-212/);
});
test('rendered headline text keeps one space after punctuation in every shot',()=>{
  const {stage,window}=fakePage();
  for(const [index,shot] of window.timeline.shots.entries()) {
    window.seek((shot.start+shot.end)/2);
    const match=stage.innerHTML.match(/class="abs headline"[^>]*>([\s\S]*?)<\/div>/);
    assert(match,shot.id);
    const text=match[1].replace(/<[^>]*>/g,'');
    assert(!/[.,:?](?=[A-Za-z])/.test(text),text);
    for(const space of text.matchAll(/[.,:?](\s+)(?=\S)/g))assert.equal(space[1],' ',text);
    if(index===6)assert.equal(text,'Model proposes. Program decides.');
    if(index===8)assert.equal(text,'Same checks. In Chinese, too.');
  }
  assert.match(read('../motion/motion.css'),/\.headline\s*\{[^}]*letter-spacing:0; word-spacing:\.12em/);
});
test('Chinese claim is Coca-Cola with a separate $50B conversion and $47.1B filed comparison',()=>{
  const {stage,window}=fakePage(),events=eventsFor(window,8);
  window.seek(events.convert+.001);assert.equal(styles(stage.innerHTML,'chinese-conversion')[0].opacity,'1');
  window.seek(events.chineseVerdict+.001);
  const text=plain(stage.innerHTML);
  for(const phrase of ['可口可樂 2024 年營收突破 500 億美元。','500 億 = $50.0B','Filed: $47.1B','FALSE','FY2024'])assert(text.includes(phrase),phrase);
  assert(!/623|62\.3|Units converted/.test(text));
  assert.equal(window.MOTION_DATA.product.chinese_claim.ticker,'KO');
  assert.equal(window.MOTION_DATA.product.claim_numbers.chinese_filed_b,47.061);
});
test('CTA has the explicit hackathon line, model credits, correct URL and original QR',()=>{
  const {stage,window}=fakePage();window.seek(155);
  assert.match(stage.innerHTML,/class="abs body mint cta-url"[^>]*>yanlonglai\.github\.io\/<br>market-claim-verifier\/site\//);
  assert(plain(stage.innerHTML).includes('Built during the Meta Global AI Developer Hackathon'));
  assert(plain(stage.innerHTML).includes('Muse Spark · Meta open weights'));
  assert.match(stage.innerHTML,/<svg[^>]*aria-label="QR code for https:\/\/yanlonglai\.github\.io\/market-claim-verifier\/site\/"/);
  assert.deepEqual(JSON.parse(JSON.stringify(window.MOTION_DATA.qr)),json('../motion/qr.json'));
  assert.equal(styles(stage.innerHTML,'hackathon-credit')[0]['font-size'],'56px');
});
test('renderer CLI supports exact stills and end-exclusive integer-indexed sequences',()=>{
  const still=parseArgs(['--t','3','--t','65','--t','155','--out','demo/out/test']);
  assert.deepEqual(sampleTimes(still),[3,65,155]);
  const sequence=parseArgs(['--from','2.1','--to','4.1','--fps','30','--out','demo/out/test']);
  const samples=sampleTimes(sequence); assert.equal(samples.length,60);assert.equal(samples[0],2.1);assert(samples.at(-1)<4.1);
  assert.equal(frameName(0,0,true),'frame-000000.png');
  for(const args of [['--t','NaN','--out','x'],['--from','4','--to','2','--out','x'],['--t','3','--from','0','--to','2','--out','x']]) assert.throws(()=>parseArgs(args));
});

test('precomputed QR independently decodes to the exact live-demo URL (v4 M byte mode)',()=>{
  const qr=json('../motion/qr.json'), m=qr.matrix.map(r=>[...r].map(c=>c==='1')),n=m.length;
  assert.equal(n,33);assert(qr.matrix.every(r=>r.length===n));assert.equal(qr.quiet_zone,4);
  // Read format BCH word, then unmask and deinterleave the two v4-M data blocks.
  let format=0;
  for(let i=0;i<15;i++){const y=i<6?i:i<8?i+1:n-15+i;if(m[y][8]) format|=1<<i;}
  const data=(format^0x5412)>>>10, mask=data&7;assert.equal(data>>>3,0);
  const reserved=Array.from({length:n},()=>Array(n).fill(false));
  const reserve=(x,y,w,h)=>{for(let r=y;r<y+h;r++)for(let c=x;c<x+w;c++)reserved[r][c]=true;};
  reserve(0,0,9,9);reserve(n-8,0,8,9);reserve(0,n-8,9,8);reserve(24,24,5,5);
  for(let i=0;i<n;i++){reserved[6][i]=true;reserved[i][6]=true;}
  const masks=[(r,c)=>(r+c)%2===0,(r,c)=>r%2===0,(r,c)=>c%3===0,(r,c)=>(r+c)%3===0,(r,c)=>(Math.floor(r/2)+Math.floor(c/3))%2===0,(r,c)=>r*c%2+r*c%3===0,(r,c)=>(r*c%2+r*c%3)%2===0,(r,c)=>(r*c%3+(r+c)%2)%2===0];
  const bits=[];let up=true;
  for(let col=n-1;col>0;col-=2){if(col===6)col--;for(let j=0;j<n;j++){const row=up?n-1-j:j;for(let c=col;c>=col-1;c--)if(!reserved[row][c])bits.push(Number(m[row][c]!==masks[mask](row,c)));}up=!up;}
  const bytes=Array.from({length:100},(_,i)=>bits.slice(i*8,i*8+8).reduce((a,b)=>a*2+b,0));
  const payload=[...Array.from({length:32},(_,i)=>bytes[i*2]),...Array.from({length:32},(_,i)=>bytes[i*2+1])];
  const stream=payload.flatMap(v=>Array.from({length:8},(_,i)=>(v>>(7-i))&1));let cursor=0;
  const take=n=>{let result=0;for(let i=0;i<n;i++)result=result*2+stream[cursor++];return result;};
  assert.equal(take(4),4);const length=take(8);const decoded=String.fromCharCode(...Array.from({length},()=>take(8)));
  assert.equal(decoded,'https://yanlonglai.github.io/market-claim-verifier/site/');assert.equal(decoded,qr.url);
});
