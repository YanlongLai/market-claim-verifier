/* Browser + Node pure timeline math. No wall clock, random state, or browser dependency. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.MotionLogic = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const TYPE = Object.freeze({body: 64, number: 104, headline: 104, safe: 64, subtitleReserve: 200});
  const PALETTE = Object.freeze({navy:'#111a20', panel:'#18272f', mint:'#3ddc97', coral:'#ff6b6b', amber:'#d9a74a', white:'#ffffff', muted:'#b5c4cd'});
  const clamp = (v, a=0, b=1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a+(b-a)*clamp(t);
  const easeInOut = x => { x=clamp(x); return x<.5 ? 4*x*x*x : 1-Math.pow(-2*x+2,3)/2; };
  const easeOutBack = x => { x=clamp(x); if(x===0||x===1)return x; const c=1.70158; return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2); };
  const progress = (t, start, duration=.24) => clamp((t-start)/duration);
  const escapeHTML = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function highlightQuote(decoded) {
    // Tokenise plain, already decoded source text. Never scan escaped HTML:
    // otherwise the 39 in an apostrophe's &#39; becomes a financial number.
    const text=String(decoded??'');
    const tokens=/&(?:#\d+|#x[\da-f]+|[a-z][\da-z]*);|\bQ[1-4]\s+\d{4}\b|\$?\d[\d,.]*(?:%|×|x)?/gi;
    let html='', cursor=0;
    for(const match of text.matchAll(tokens)) {
      html+=escapeHTML(text.slice(cursor,match.index));
      const token=match[0];
      html+=token.startsWith('&')?escapeHTML(token):`<span class="${/^Q/.test(token)?'period number':'number'}">${escapeHTML(token)}</span>`;
      cursor=match.index+token.length;
    }
    return html+escapeHTML(text.slice(cursor));
  }
  function lowerBound(a, t) {
    let low=0, high=a.length;
    while (low<high) { const mid=(low+high)>>>1; if(a[mid]<t-1e-9) low=mid+1; else high=mid; }
    return low;
  }
  function beatHelpers(beats) {
    if (!Array.isArray(beats) || !beats.length || beats.some((b,i)=>!Number.isFinite(b)||b<0||(i&&b<=beats[i-1]))) throw new Error('Invalid detected beat grid');
    const beatAt=n=>{ if(!Number.isInteger(n)||n<0||n>=beats.length) throw new Error('Beat index out of range'); return beats[n]; };
    const onOrAfter=t=>{ if(!Number.isFinite(t)) throw new Error('Beat time must be finite'); const i=lowerBound(beats,t); if(i===beats.length) throw new Error('Detected beat grid exhausted'); return beats[i]; };
    const nearestBeat=t=>{
      if(!Number.isFinite(t)) throw new Error('Beat time must be finite');
      const i=lowerBound(beats,t); if(i===0) return beats[0]; if(i===beats.length) return beats.at(-1);
      return t-beats[i-1]<=beats[i]-t ? beats[i-1] : beats[i];
    };
    return {beatAt,nearestBeat,onOrAfter};
  }
  function normalizeBeats(grid) {
    beatHelpers(grid.beats_s);
    const offset=grid.beats_s[0];
    return {offset,beats:grid.beats_s.map(b=>Number((b-offset).toFixed(9)))};
  }
  function targetTiming(scenes) {
    let start=0;
    const shots=scenes.map(s=>{
      if(!Number.isFinite(s.target_s)||s.target_s<=0) throw new Error('Invalid target duration');
      const shot={id:s.id,start:Number(start.toFixed(9)),end:Number((start+s.target_s).toFixed(9))}; start+=s.target_s; return shot;
    });
    return {source:'targets',duration:Number(start.toFixed(9)),shots};
  }
  function narrationTiming(scenes,durations,beats,pad=.3) {
    if(!Number.isFinite(pad)||pad<.3) throw new Error('At least 0.3 s narration padding is required');
    const {onOrAfter}=beatHelpers(beats); let start=0;
    const shots=scenes.map(s=>{
      const voice_s=durations[s.id]; if(!Number.isFinite(voice_s)||voice_s<=0) throw new Error('Invalid narration duration');
      const voice_end=Number((start+voice_s).toFixed(9)),end=onOrAfter(voice_end+pad);
      const shot={id:s.id,start,end,voice_s,voice_end}; start=end; return shot;
    });
    return {source:'narration',duration:start,shots};
  }
  function shotAt(timeline,t) {
    if(!Number.isFinite(t)) throw new Error('seek(t) requires finite seconds');
    const time=clamp(t,0,timeline.duration);
    return timeline.shots.find(s=>s.start<=time && time<s.end) || timeline.shots.at(-1);
  }
  function eventsForShot(shot,beats,cueEvents=[]) {
    const local=beats.filter(b=>b>=shot.start-1e-9&&b<shot.end-1e-9);
    if(!local.length) throw new Error('Shot contains no detected beat');
    const b=i=>local[Math.min(Math.max(0,i),local.length-1)];
    const at=fraction=>b(Math.floor(fraction*(local.length-1)));
    const events={title:b(0),verdict:b(2),tokens:[b(2),b(3),b(4)],question:b(local.length-1),
      bars:[b(1),b(2),b(3)],claims:[b(0),at(.28),at(.56)],stamps:[at(.82)],
      flips:[b(4),b(5),b(6)],appleFalse:b(6),appleYear:b(7),appleQuarter:b(8),sweep:b(2),link:b(local.length-1),
      modelLane:b(0),programLane:b(0),
      plan:b(1),cite:b(3),parse:b(5),calendar:b(7),evidence:b(9),fake:b(Math.max(10,local.length-3)),
      results:[[b(1),b(2)],[b(3),b(4)],[b(5),b(6)]],badge:b(8),convert:b(2),chineseVerdict:b(4)};
    for(const event of cueEvents) {
      const expected=beatHelpers(beats).onOrAfter(Math.max(shot.start,event.cue_start-.10));
      if(!Number.isFinite(event.t)||Math.abs(event.t-expected)>1e-8||event.t>=shot.end) throw new Error('Invalid narration cue beat');
      const keys=event.event.split('.');let target=events;
      for(const key of keys.slice(0,-1)) {
        if(!Object.hasOwn(target,key)||!Array.isArray(target[key])) throw new Error('Unknown cue event path');
        target=target[key];
      }
      const key=keys.at(-1);
      if(!Object.hasOwn(target,key)||typeof target[key]!=='number') throw new Error('Unknown cue event');
      target[key]=event.t;
    }
    return events;
  }
  function testWindow(timing,beats,prefix='m05',len=2,fps=30,cueEvents={}) {
    const matches=timing.shots.filter(s=>s.id===prefix||s.id.startsWith(prefix+'-'));
    if(matches.length!==1) throw new Error('Choose one motiontest shot');
    const shot=matches[0];
    if(!Number.isFinite(len)||len<=0||len>shot.end-shot.start) throw new Error('Invalid motiontest length');
    const event=eventsForShot(shot,beats,cueEvents[shot.id]||[]).flips[0];
    const from=Math.max(shot.start,Math.floor(Math.min(event-.2,shot.end-len)*fps)/fps);
    return {shot:shot.id,event,from,to:from+len};
  }
  function contrast(a,b) {
    const lum=s=>{ const c=s.match(/[a-f\d]{2}/gi).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4));return .2126*c[0]+.7152*c[1]+.0722*c[2]; };
    const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
  }
  return {TYPE,PALETTE,clamp,lerp,easeInOut,easeOutBack,progress,escapeHTML,highlightQuote,beatHelpers,normalizeBeats,targetTiming,narrationTiming,shotAt,eventsForShot,testWindow,contrast};
});
