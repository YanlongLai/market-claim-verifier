export function chapterMarkup(segments){
 return `<nav id="chapters" aria-label="Film chapters"><div class="chapter-labels">${segments.map(s=>`<span data-chapter="${s.scene}" style="left:${100*(s.start_s+s.duration_s/2)/178}%">${s.label}</span>`).join('')}</div><div class="chapter-rail">${segments.map(s=>`<i data-segment="${s.scene}" style="left:${100*s.start_s/178}%;width:${100*s.duration_s/178}%"><b></b></i>`).join('')}</div></nav>`;
}
export function updateChapters(state){
 const labels=state.chapters.map(s=>{
  const segment=document.querySelector(`[data-segment="${s.scene}"]`),label=document.querySelector(`[data-chapter="${s.scene}"]`);
  segment.querySelector('b').style.transform=`scaleX(${s.fill})`;
  label.classList.toggle('current',s.current);
  const width=label.offsetWidth;
  return {label,width,centre:Math.max(width/2+12,Math.min(1920-width/2-12,1920*(s.start_s+s.duration_s/2)/178))};
 });
 // The 8-second final segment is narrower than its label. Shift labels within
 // their neighbours' spare space while retaining the duration-weighted rail.
 let right=1908;
 for(let i=labels.length-1;i>=0;i--){
  const item=labels[i];item.centre=Math.min(item.centre,right-item.width/2);
  item.label.style.left=`${item.centre}px`;right=item.centre-item.width/2-12;
 }
}
