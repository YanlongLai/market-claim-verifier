/** Layout assertions run on the real DOM before the host renderer saves a frame. */
import assert from 'node:assert/strict';

const inside=(inner,outer,slack=.5)=>inner.left>=outer.left-slack&&inner.right<=outer.right+slack
  &&inner.top>=outer.top-slack&&inner.bottom<=outer.bottom+slack;

export function assertLayout({headlines,table}) {
  for(const headline of headlines) {
    assert(!/[.,:?](?=[A-Za-z])/.test(headline.text),`Missing headline space: ${headline.text}`);
    assert(headline.letterSpacing>=0,'Headline tracking must preserve spaces');
    for(const space of headline.spaces) {
      assert.equal(space.text,' ','Headlines need a single space after punctuation');
      assert(space.width>=headline.fontSize*.14,'Rendered headline space is too narrow');
    }
    for(const rect of headline.lines) assert(rect.left>=headline.box.left-.5&&rect.right<=headline.box.right+.5,'Headline overflows its width');
  }
  if(!table) return {headlines:headlines.length};
  assert(table.gap>=40,'Proof grid gutter must be at least 40 px');
  assert.equal(table.cells.length,3,'Quarter close-up needs a label and two values');
  for(const [i,cell] of table.cells.entries()) {
    assert(inside(cell.box,table.box),'Proof cell overflows the fixed table viewport');
    assert(inside(cell.textBox,cell.box),'Proof text overflows its cell');
    if(i) {
      assert(cell.box.left-table.cells[i-1].box.right>=40,'Proof cells overlap or have less than 40 px gutter');
      assert(cell.fontSize>=96,'Quarter values must remain at least 96 px');
      assert.equal(cell.align,'flex-end','Proof values must be right aligned');
      assert(cell.numeric.includes('tabular-nums'),'Proof values need tabular numerals');
    }
  }
  assert.deepEqual(table.cells.slice(1).map(c=>c.text),['143,083','158,877']);
  const selected=table.cells[1],highlight=selected.highlight;
  assert(highlight&&inside(selected.textBox,highlight),'Amber highlight must cover the entire 143,083 value');
  assert(Math.abs(highlight.left-selected.box.left)<=.5&&Math.abs(highlight.right-selected.box.right)<=.5,
    'Amber highlight must span the full 143,083 cell');
  return {headlines:headlines.length,minGutter:Math.min(...table.cells.slice(1).map((c,i)=>c.box.left-table.cells[i].box.right))};
}

export async function checkLayout(page) {
  const metrics=await page.evaluate(()=>{
    const rect=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom});
    const textRect=el=>{const range=document.createRange();range.selectNodeContents(el);return rect(range.getBoundingClientRect());};
    const headlines=[...document.querySelectorAll('.headline')].map(el=>{
      const style=getComputedStyle(el),nodes=[],walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
      let node;while((node=walker.nextNode()))nodes.push(node);
      const text=nodes.map(n=>n.textContent).join('');
      const point=index=>{for(const n of nodes){if(index<n.length)return [n,index];index-=n.length;}return [nodes.at(-1),nodes.at(-1).length];};
      const range=document.createRange();range.selectNodeContents(el);
      const lines=[...range.getClientRects()].map(rect);
      const spaces=[...text.matchAll(/[.,:?](\s+)(?=\S)/g)].map(match=>{
        const start=match.index+1,end=start+match[1].length;
        const range=document.createRange();range.setStart(...point(start));range.setEnd(...point(end));
        return {text:match[1],width:range.getBoundingClientRect().width};
      });
      return {text,fontSize:parseFloat(style.fontSize),letterSpacing:parseFloat(style.letterSpacing)||0,
        spaces,lines,box:rect(el.getBoundingClientRect())};
    });
    const grid=document.querySelector('.filing-table');
    const table=grid?{box:rect(grid.getBoundingClientRect()),gap:parseFloat(getComputedStyle(grid).columnGap),
      cells:[...grid.querySelectorAll('.table-cell')].map(el=>{
        const style=getComputedStyle(el),span=el.querySelector(':scope > span'),highlight=el.querySelector('.filing-highlight');
        return {text:span.textContent,box:rect(el.getBoundingClientRect()),textBox:textRect(span),
          fontSize:parseFloat(style.fontSize),align:style.justifyContent,numeric:style.fontVariantNumeric,
          highlight:highlight?rect(highlight.getBoundingClientRect()):null};
      })}:null;
    return {headlines,table};
  });
  return assertLayout(metrics);
}
