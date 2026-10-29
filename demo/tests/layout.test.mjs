import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {assertLayout} from '../motion/layout-checks.mjs';

const box=(left,right,top=546,bottom=710)=>({left,right,top,bottom});
function metrics() {
  return {headlines:[{text:'Model proposes. Program decides.',fontSize:104,letterSpacing:0,
    spaces:[{text:' ',width:32}],box:box(64,1856,188,312),lines:[box(64,1730,188,300)]}],
    table:{box:box(82,1838,346,710),gap:48,cells:[
      {text:'Total net sales',box:box(82,582),textBox:box(98,450,560,690)},
      {text:'143,083',box:box(630,1206),textBox:box(690,1190,560,696),fontSize:128,
        align:'flex-end',numeric:'tabular-nums',highlight:box(630,1206,548,708)},
      {text:'158,877',box:box(1254,1830),textBox:box(1314,1814,560,696),fontSize:128,
        align:'flex-end',numeric:'tabular-nums'}]}};
}
test('fixed proof columns have no overlaps and at least 40 px gutters',()=>{
  const css=readFileSync(new URL('../motion/motion.css',import.meta.url),'utf8');
  const columns=css.match(/grid-template-columns:([\dpx ]+); column-gap:(\d+)px/);
  assert(columns,'Proof columns must have explicit pixel widths');
  const widths=columns[1].trim().split(/\s+/).map(parseFloat),gap=Number(columns[2]);
  const observed=metrics();
  assert.deepEqual(widths,observed.table.cells.map(c=>c.box.right-c.box.left));
  assert.equal(gap,observed.table.gap);
  assert.equal(assertLayout(observed).minGutter,48);
});
for(const [name,change,message] of [
  ['overlapping cells',m=>{m.table.cells[2].box.left=1190;},/overlap|40 px/],
  ['a 39 px gutter',m=>{m.table.cells[2].box.left=1245;},/40 px/],
  ['overflowing digits',m=>{m.table.cells[1].textBox.right=1210;},/overflows/],
  ['a partial amber highlight',m=>{m.table.cells[1].highlight.right=1150;},/highlight/],
  ['centered numbers',m=>{m.table.cells[1].align='center';},/right aligned/],
  ['proportional digits',m=>{m.table.cells[1].numeric='normal';},/tabular/],
  ['missing headline spaces',m=>{m.headlines[0].text='Model proposes.Program decides.';},/Missing headline space/],
  ['collapsed visual spacing',m=>{m.headlines[0].spaces[0].width=1;},/too narrow/],
  ['negative headline tracking',m=>{m.headlines[0].letterSpacing=-2;},/tracking/],
  ['double headline spaces',m=>{m.headlines[0].spaces[0].text='  ';},/single space/],
]) test(`geometry guard rejects ${name}`,()=>{
  const measured=metrics();change(measured);
  assert.throws(()=>assertLayout(measured),message);
});
for(const punctuation of ['.',',',':','?']) test(`headline keeps one rendered space after ${punctuation}`,()=>{
  const measured=metrics();measured.headlines[0].text=`First${punctuation} Next`;
  assert.doesNotThrow(()=>assertLayout(measured));
  measured.headlines[0].text=`First${punctuation}Next`;
  assert.throws(()=>assertLayout(measured),/Missing headline space/);
});
