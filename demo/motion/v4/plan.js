export const boundaries=[0,6,26,40,56,72,122,146,162,178];
export const architectureReveal=local=>({
  nodes:Array.from({length:5},(_,i)=>Math.max(0,Math.min(1,(local-i*2.8)/.6))),
  links:Array.from({length:4},(_,i)=>Math.max(0,Math.min(1,(local-(i*2.8+1.8))/.5))),
});
export function stateAt(t) {
  if(!Number.isFinite(t)||t<0||t>178) throw new Error('v4 time must be in 0..178');
  const index=t===178?8:boundaries.findIndex((a,i)=>i<9&&t>=a&&t<boundaries[i+1]);
  const local=t-boundaries[index];
  return {shot:`v40${index+1}`,index,local,placeholder:index===5||index===8,
    architecture:index===4?architectureReveal(local):null,
    broll:index===1&&local>=14&&local<17?'cards-fanning-out':
      index===6&&local>=8&&local<11?'numbers-raining-into-filing':null};
}
