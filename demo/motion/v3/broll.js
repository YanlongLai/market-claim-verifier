/* Pure source-frame selection. seek history, video decoders and wall clocks are irrelevant. */
(function(root) {
  'use strict';
  function windows(data, clips=root.BROLL_DATA) {
    const duration=clips.frame_count/clips.fps;
    return clips.clips.map(clip=>{
      const shot=data.timing.shots.find(s=>s.id===clip.shot);
      if(!shot) throw new Error(`Missing B-roll shot: ${clip.shot}`);
      const event=clip.anchor==='start'?shot.start:
        data.cues._events[shot.id].find(e=>e.event===clip.anchor)?.t;
      if(!Number.isFinite(event)) throw new Error(`Missing B-roll cue: ${clip.anchor}`);
      const target=event-clip.lead_s;
      const available=data.beats.beats_s.filter(b=>b>=shot.start&&b+duration<=shot.end);
      if(!available.length) throw new Error(`B-roll cannot fit ${shot.id}; review holds.`);
      const start=available.filter(b=>b<=target+1e-9).at(-1)??available[0],play_end=start+duration;
      // Keep the clean final frame until a detected beat permits the layout cut.
      // The opener keeps that still while its full disclosure remains on screen.
      const end=clip.id==='hover-arrive-s11'?shot.end:
        data.beats.beats_s.find(b=>b>=play_end-1e-9&&b<=shot.end)??shot.end;
      if(clip.id==='point-glow-s29'&&end>shot.voice_start)
        throw new Error('Point-glow must finish inside the Hover narration lead.');
      return {...clip,start,play_end,end};
    });
  }
  function select(data,time,clips=root.BROLL_DATA) {
    if(!Number.isFinite(time)) throw new Error('B-roll time must be finite.');
    const clip=windows(data,clips).find(c=>time>=c.start&&time<c.end);
    if(!clip)return null;
    const frameIndex=Math.min(clips.frame_count-1,Math.floor((time-clip.start)*clips.fps+1e-9));
    return {...clip,frameIndex,src:clips.base+(clip.asset_id||clip.id)+`/frame-${String(frameIndex).padStart(4,'0')}.png`,
      rect:{...(clip.panel||clips.panel)}};
  }
  function panel(frame) {
    const {x,y,w,h}=frame.rect;
    return `<div class="broll-layer" aria-hidden="true"><div class="broll-panel" data-broll-panel="${frame.id}" data-broll-frame="${frame.frameIndex}" style="left:${x-64}px;top:${y-64}px;width:${w}px;height:${h}px"><img src="${frame.src}" alt=""></div></div>`;
  }
  root.BrollLayer={windows,select,panel};
})(globalThis);
