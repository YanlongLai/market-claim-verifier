/** Real DOM measurements, invoked only by the host renderer. */
import assert from 'node:assert/strict';

export function assertV3Layout(metrics) {
  for(const panel of metrics.broll||[]) {
    assert(panel.left>=64&&panel.right<=1856&&panel.top>=64&&panel.bottom<=880,
      'B-roll enters edge/subtitle zone');
    assert(panel.width>=560&&panel.width<=640&&Math.abs(panel.width-panel.height)<.5,
      'B-roll must remain a framed square panel');
    assert(panel.naturalWidth===480&&panel.naturalHeight===480,'B-roll PNG is missing or scaled at extraction');
    assert(!panel.text.trim(),'B-roll panel must contain no text');
    for(const box of metrics.text) {
      const width=Math.min(panel.right,box.right)-Math.max(panel.left,box.left),
        height=Math.min(panel.bottom,box.bottom)-Math.max(panel.top,box.top);
      assert(width<=0||height<=0,`B-roll covers product text: ${box.text}`);
    }
  }
  for(const box of metrics.text) {
    assert(box.fontSize>=56,`Unreadable label (minimum 56 px): ${box.text}`);
    if(box.exampleValue)assert(box.fontSize>=96,`Unreadable example value: ${box.text}`);
    assert(box.left>=63.5&&box.right<=1856.5&&box.top>=63.5&&box.bottom<=(box.realworld?816:880),
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
        realworld:Boolean(el.closest('[data-realworld]')),
        aggregateLabel:el.classList.contains('aggregate-label')&&
          el.closest('[data-realworld-kind="aggregate"]')!==null,
        exampleValue:el.closest('[data-realworld-kind="example"]')!==null&&
          el.querySelector('.number')!==null,
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
    const broll=[...document.querySelectorAll('[data-broll-panel]')].map(el=>{
      const box=el.getBoundingClientRect(),img=el.querySelector('img');
      return {left:box.left,right:box.right,top:box.top,bottom:box.bottom,
        width:box.width,height:box.height,naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,
        text:el.textContent};
    });
    return {text,numbers,sourceCrops,broll};
  }));
}
