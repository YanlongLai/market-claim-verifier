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
  for(const crop of metrics.sourceCrops||[]) {
    assert(Number.isFinite(crop.fontSize)&&crop.fontSize>=96,`Unreadable source number: ${crop.text}`);
    assert(crop.left>=64&&crop.right<=1856&&crop.top>=64&&crop.bottom<=880,
      `Source crop enters edge/subtitle zone: ${crop.text}`);
    assert(crop.imageLeft<=crop.left&&crop.imageRight>=crop.right&&
      crop.imageTop<=crop.top&&crop.imageBottom>=crop.bottom,'Source crop is not filled by its image');
  }
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
    const sourceCrops=[...document.querySelectorAll('[data-source-font-size]')].map(el=>{
      const box=el.getBoundingClientRect(),img=el.querySelector('img'),image=img.getBoundingClientRect();
      return {text:el.dataset.sourceNumber,fontSize:Number(el.dataset.sourceFontSize)*
        Math.min(image.width/img.naturalWidth,image.height/img.naturalHeight),
        left:box.left,right:box.right,top:box.top,bottom:box.bottom,
        imageLeft:image.left,imageRight:image.right,imageTop:image.top,imageBottom:image.bottom};
    });
    return {text,numbers,sourceCrops};
  }));
}
