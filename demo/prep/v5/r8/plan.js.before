export const boundaries=[0,8,20,32,46,58,116,138,154,170,178];
export const siteURL='hackathon.dappgo.com';
export const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
export function chapterState(t,segments){
 return segments.map(s=>({...s,width:100*s.duration_s/178,left:100*s.start_s/178,
  fill:clamp((t-s.start_s)/s.duration_s),current:t>=s.start_s&&(t<s.end_s||t===178&&s.end_s===178)}));
}
export function repostCascade(local){
 return Array.from({length:7},(_,i)=>{
  const p=clamp((local-i*.12)/1.2),ease=1-(1-p)**3;
  return {x:(30+i*30)*ease,y:([-44,44,-68,68,-24,24,0][i])*ease,
   rotation:(i-3)*2.4*ease,scale:1-.035*(i+1)*ease,opacity:p===0?0:.12+.055*(7-i)};
 });
}
export function overlayAt(local,events){
 // Adding then subtracting a scene offset can lose a few floating-point bits.
 return [...events].reverse().find(e=>local+1e-9>=(e.picture_at_scene_s??e.at_scene_s))||null;
}
export function terminalAt(local,replay){
 const block=[...replay.blocks].reverse().find(b=>local+1e-9>=b.at_s)||replay.blocks[0];
 const frame=[...block.frames].reverse().find(f=>local+1e-9>=f.at_s)||block.frames[0];
 return {block:block.block,rows:frame.rows};
}
// Site hero WINDUP -> STRIKE -> REACT, reduced to a single 1.6-second sign-off.
export function outroStampAt(local){
 const strike=.3,react=.8,duration=1.6;
 const dip=local<strike?0:local<strike+.06?14*clamp((local-strike)/.06):14*(1-clamp((local-strike-.06)/.16));
 return {pose:local<strike?'stamp':local<react?'stamp-down':'approve',dip,
  lean:local<strike?-4*(1-clamp(local/strike)):0,ink:clamp((local-strike)/.18),settled:local>=duration};
}
export function stateAt(t,scenes,chapters){
 if(!Number.isFinite(t)||t<0||t>178)throw new Error('v5 time must be in 0..178');
 const index=t===178?9:boundaries.findIndex((a,i)=>i<10&&t>=a&&t<boundaries[i+1]);
 const local=t-boundaries[index],scene=scenes[index],active=overlayAt(local,scene.cue_events);
 const ready=name=>local+1e-9>=(scene.cue_events.find(e=>e.event===name)?.picture_at_scene_s??Infinity);
 const repostAt=scene.cue_events.find(e=>e.event==='reposts')?.picture_at_scene_s??Infinity;
 const program=ready('program'),principle=ready('principle');
 return {shot:`v50${index}`,index,local,active:active?.event||null,placeholder:Boolean(scene.placeholder),
  liveTake:[5,8].includes(index)?{scale:1,x:0,y:0}:null,
  cascade:index===1?repostCascade(local-repostAt):null,
  inputs:index===2?['screenshot','pdf','podcast','video'].map(name=>ready(name)):null,
  overlay:index===5?active:null,
  terminal:index===6?active:null,
  architecture:index===4?{nodes:program?[.3,.3,.3,1,1]:[.65,1,1,.15,.15],links:program?[.2,.2,1,1]:[1,1,.1,.1],headline:principle}:null,
  buildDisclosure:index===0&&ready('disclosure_build'),
  postFocus:index===1&&ready('period'),question:index===2&&ready('question'),
  results:index===7?{accuracy:ready('accuracy'),false_support:ready('false_support'),cost_time:ready('cost_time'),coverage:ready('coverage')}:null,
  url:index===8&&ready('url'),wordmark:index===9&&ready('wordmark'),
  chapters:chapterState(t,chapters),fade:index===9?clamp((178-t)/1.2):1};
}
