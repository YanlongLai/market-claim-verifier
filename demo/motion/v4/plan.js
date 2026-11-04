export const boundaries=[0,9,22,34,50,66,124,148,164,178];
export const siteURL='hackathon.dappgo.com';
export function repostCascade(local) {
  return Array.from({length:5},(_,i)=>{
    const elapsed=local-i*.45;
    const progress=elapsed<0?0:(elapsed%4.5)/4.5;
    const spread=1-(1-progress)**2;
    return {x:(100+i*65)*spread,y:([-45,35,-65,55,-20][i])*spread,
      rotation:(i-2)*3*spread,scale:1-.12*spread,
      opacity:elapsed<0?0:.4*Math.min(1,progress/.12)*(1-progress)**1.5};
  });
}
export function liveTakeCrop(shot) {
  if(!['v406','v409'].includes(shot))return null;
  // The retained 1920×1080 takes put the form/result at x=892…1628.
  // Clamp the centred crop to the source edge; use the top for beat 6 so its
  // receipt survives the original draft scroll, and the middle for beat 9.
  const scale=1.4,centerX=(892+1628)/2;
  return {scale,x:Math.max(1920*(1-scale),960-centerX*scale),y:shot==='v406'?0:540*(1-scale)};
}
export const architectureReveal=local=>({
  nodes:Array.from({length:5},(_,i)=>Math.max(0,Math.min(1,(local-i*2.8)/.6))),
  links:Array.from({length:4},(_,i)=>Math.max(0,Math.min(1,(local-(i*2.8+1.8))/.5))),
});
export function stateAt(t,scenes=[]) {
  if(!Number.isFinite(t)||t<0||t>178) throw new Error('v4 time must be in 0..178');
  const index=t===178?8:boundaries.findIndex((a,i)=>i<9&&t>=a&&t<boundaries[i+1]);
  const local=t-boundaries[index];
  const shot=`v40${index+1}`;
  return {shot,index,local,placeholder:scenes.length?Boolean(scenes[index]?.placeholder):index===5||index===8,
    cascade:index===1?repostCascade(local):null,liveTake:liveTakeCrop(shot),siteURL:index===8?siteURL:null,
    architecture:index===4?architectureReveal(local):null,
    broll:index===6&&local>=8&&local<11?'numbers-raining-into-filing':null};
}
