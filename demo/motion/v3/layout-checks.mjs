/** Real DOM measurements, invoked only by the host renderer. */
import assert from 'node:assert/strict';

export function assertV3Layout(metrics) {
  for(const box of metrics.text) {
    assert(box.fontSize>=56,`Unreadable label: ${box.text}`);
    assert(box.left>=63.5&&box.right<=1856.5&&box.top>=63.5&&box.bottom<=880,
      `Text enters edge/subtitle zone: ${box.text}`);
    assert(box.textLeft>=box.left-.5&&box.textRight<=box.right+.5&&
      box.textTop>=box.top-.5&&box.textBottom<=box.bottom+.5,
      `Text overflows its box: ${box.text}`);
  }
  for(const number of metrics.numbers) assert(number.fontSize>=96,`Unreadable number: ${number.text}`);
  for(let i=0;i<metrics.text.length;i++) for(let j=i+1;j<metrics.text.length;j++) {
    const a=metrics.text[i],b=metrics.text[j];
    const width=Math.min(a.textRight,b.textRight)-Math.max(a.textLeft,b.textLeft),
      height=Math.min(a.textBottom,b.textBottom)-Math.max(a.textTop,b.textTop);
    assert(width<=.5||height<=.5,`Text overlaps: ${a.text} / ${b.text}`);
  }
  return {labels:metrics.text.length,numbers:metrics.numbers.length,subtitleTop:880};
}

export async function checkV3Layout(page) {
  return assertV3Layout(await page.evaluate(()=>{
    const text=[...document.querySelectorAll('[data-fit="text"]')].filter(el=>el.textContent.trim()).map(el=>{
      const box=el.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(el);
      const content=range.getBoundingClientRect();
      return {text:el.textContent,fontSize:parseFloat(getComputedStyle(el).fontSize),
        left:box.left,right:box.right,top:box.top,bottom:box.bottom,
        textLeft:content.left,textRight:content.right,textTop:content.top,textBottom:content.bottom};
    });
    const numbers=[...document.querySelectorAll('.number,.table-cell:not(.row-label),.table-year')]
      .map(el=>({text:el.textContent,fontSize:parseFloat(getComputedStyle(el).fontSize)}));
    return {text,numbers};
  }));
}
