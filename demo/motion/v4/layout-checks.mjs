/** Director r4 assertions against each actual browser frame, before capture. */
import assert from 'node:assert/strict';

export async function checkV4Layout(page,state) {
  const layout=await page.evaluate(()=>{
    const stage=document.querySelector('#stage');
    const frame=stage.querySelector('iframe');
    const doc=frame?.contentDocument;
    const video=stage.querySelector('.live-take');
    const url=stage.querySelector('.site-url');
    const box=element=>{
      const {x,y,width,height,right,bottom}=element.getBoundingClientRect();
      return {x,y,width,height,right,bottom};
    };
    const matrix=video?new DOMMatrix(getComputedStyle(video).transform):null;
    return {
      hero:doc?{title:doc.querySelector('#hero-title')?.textContent,
        sections:doc.querySelectorAll('section').length,
        navigation:doc.querySelectorAll('nav,header,script').length,
        scrollHeight:doc.documentElement.scrollHeight,height:doc.documentElement.clientHeight,
        overflow:getComputedStyle(doc.documentElement).overflow}:null,
      copies:stage.querySelectorAll('.repost-copy').length,
      originals:stage.querySelectorAll('.original-post').length,
      text:stage.innerText.trim(),counter:Boolean(stage.querySelector('#reposts')),
      video:video?{...box(video),sourceWidth:video.videoWidth,sourceHeight:video.videoHeight,
        scaleX:matrix.a,scaleY:matrix.d,skewX:matrix.b,skewY:matrix.c,
        fit:getComputedStyle(video).objectFit,
        overflow:getComputedStyle(video.parentElement).overflow}:null,
      url:url?{...box(url),text:url.textContent,fontSize:parseFloat(getComputedStyle(url).fontSize)}:null,
      accent:stage.querySelectorAll('[data-accent],.scale-accent').length,
      input:stage.querySelector('#input-label')?.textContent,
      metricFonts:[...stage.querySelectorAll('.metric span')].map(el=>parseFloat(getComputedStyle(el).fontSize)),
    };
  });
  if(state.index===0){
    assert.equal(layout.hero?.title,'Paste a finance post.','Opening must use the simplified worktree hero');
    assert.equal(layout.hero.sections,1,'Opening iframe must contain only the hero');
    assert.equal(layout.hero.navigation,0,'Opening must not load navigation or site scripts');
    assert.equal(layout.hero.overflow,'hidden');
    assert(layout.hero.scrollHeight<=layout.hero.height,'Opening hero must not scroll');
  }
  if(state.index===1){
    assert.equal(layout.copies,5,'Repost cascade requires five duplicates');
    assert.equal(layout.originals,1);
    assert.equal(layout.counter,false,'Repost counter must not return');
    assert.equal(layout.text,'A real number.\nThe wrong period.','Beat 2 has no fabricated metric');
  }
  if(state.liveTake&&!state.placeholder){
    const v=layout.video;
    assert(v,'Live scene must retain its video');
    assert.equal(v.sourceWidth,1920);assert.equal(v.sourceHeight,1080);
    assert.equal(v.scaleX,1.4);assert.equal(v.scaleY,1.4);
    assert.equal(v.skewX,0);assert.equal(v.skewY,0);
    assert.equal(v.fit,'contain');assert.equal(v.overflow,'hidden');
    assert(Math.abs(v.x-state.liveTake.x)<.5&&Math.abs(v.y-state.liveTake.y)<.5);
    assert(v.x<=0&&v.y<=0&&v.right>=1919.5&&v.bottom>=1079.5,'Crop must cover the canvas');
    if(state.siteURL){
      assert.equal(layout.url?.text,state.siteURL);
      assert.equal(layout.text,state.siteURL,'No other overlay may be added to beat 9');
      assert(layout.url.fontSize>=48,'Closing URL must remain at least 48 px');
      assert(layout.url.right<=1920&&layout.url.bottom<=1080&&layout.url.x>960&&layout.url.y>900);
    }
  }
  if(!state.siteURL)assert.equal(layout.url,null,'URL overlay belongs only to beat 9');
  assert.equal(layout.accent,0,'The rejected Wan insert must not return');
  for(const size of layout.metricFonts)assert(size>=56,'Supporting metric labels must be readable');
  if(state.index===2)assert.equal(layout.input.split(' · ')[0],['Screenshot','PDF','Podcast','Video'][state.input]);
  return layout;
}
