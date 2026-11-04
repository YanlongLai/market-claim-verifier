export function chapterMarkup(segments){
 return `<nav id="chapters" aria-label="Film chapters"><div class="chapter-labels">${segments.map(s=>`<span data-chapter="${s.scene}" style="left:${100*(s.start_s+s.duration_s/2)/178}%">${s.label}</span>`).join('')}</div><div class="chapter-rail">${segments.map(s=>`<i data-segment="${s.scene}" style="left:${100*s.start_s/178}%;width:${100*s.duration_s/178}%"><b></b></i>`).join('')}</div></nav>`;
}
export function labelPositions(segments,widths,width=1920,padding=25){
 if(widths.reduce((a,b)=>a+b,0)+2*padding*widths.length>width)throw new Error('Chapter labels cannot keep 24 px on each side');
 const centres=segments.map((s,i)=>Math.max(widths[i]/2+padding,Math.min(width-widths[i]/2-padding,width*(s.start_s+s.duration_s/2)/178)));
 let right=width-padding;
 for(let i=centres.length-1;i>=0;i--){centres[i]=Math.min(centres[i],right-widths[i]/2);right=centres[i]-widths[i]/2-2*padding;}
 let left=padding;
 for(let i=0;i<centres.length;i++){centres[i]=Math.max(centres[i],left+widths[i]/2);left=centres[i]+widths[i]/2+2*padding;}
 return centres;
}
export function updateChapters(state){
 document.querySelector('#chapters').style.opacity=state.fade;
 const labels=state.chapters.map(s=>{
  const segment=document.querySelector(`[data-segment="${s.scene}"]`),label=document.querySelector(`[data-chapter="${s.scene}"]`);
  segment.querySelector('b').style.transform=`scaleX(${s.fill})`;
  label.classList.toggle('current',s.current);
  const width=label.getBoundingClientRect().width;
  return {label,width};
 });
 const centres=labelPositions(state.chapters,labels.map(l=>l.width));
 labels.forEach((item,i)=>{item.label.style.left=`${centres[i]}px`;});
}
