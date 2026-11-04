export const boundaries=[0,8,20,32,46,58,116,138,154,170,178];
export const siteURL='hackathon.dappgo.com';
export const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
export function chapterState(t,segments){
 return segments.map(s=>({...s,width:100*s.duration_s/178,left:100*s.start_s/178,
  fill:clamp((t-s.start_s)/s.duration_s),current:t>=s.start_s&&(t<s.end_s||t===178&&s.end_s===178)}));
}
export function repostCascade(local){
 return Array.from({length:7},(_,i)=>{
  const p=clamp((local-.35-i*.25)/2.8),ease=1-(1-p)**3;
  return {x:(120+i*94)*ease,y:([-44,44,-68,68,-24,24,0][i])*ease,
   rotation:(i-3)*2.4*ease,scale:1-.035*(i+1)*ease,opacity:p===0?0:.12+.055*(7-i)};
 });
}
export function overlayAt(local,events){
 return [...events].reverse().find(e=>local>=e.at_scene_s)||null;
}
export function stateAt(t,scenes,chapters){
 if(!Number.isFinite(t)||t<0||t>178)throw new Error('v5 time must be in 0..178');
 const index=t===178?9:boundaries.findIndex((a,i)=>i<10&&t>=a&&t<boundaries[i+1]);
 const local=t-boundaries[index],scene=scenes[index];
 return {shot:`v50${index}`,index,local,placeholder:Boolean(scene.placeholder),
  // Playback is 1:1. All framing is done by the recorder; no post-capture crop.
  liveTake:[5,8].includes(index)?{scale:1,x:0,y:0}:null,
  cascade:index===1?repostCascade(local):null,
  inputs:index===2?Array.from({length:4},(_,i)=>clamp((local-i*.55)/.75)):null,
  overlay:index===5?overlayAt(local,scene.cue_events):null,
  terminal:index===6?overlayAt(local,scene.cue_events):null,
  architecture:index===4?{nodes:[1,1,1,1,1],links:Array.from({length:4},(_,i)=>clamp((local-i*1.8-1.1)/.4))}:null,
  chapters:chapterState(t,chapters),fade:index===9?clamp((178-t)/1.2):1};
}
