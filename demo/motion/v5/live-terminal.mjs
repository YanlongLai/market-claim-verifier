/** Stateless projection: seeking backwards and frame capture use only the film clock. */
export function liveTerminalAt(local,trace){
 if(!trace||local+1e-9<trace.typing_start_scene_s||local+1e-9>=trace.end_scene_s)return null;
 const elapsed=local-trace.start_scene_s,done=elapsed+1e-9>=trace.verdict.at_s;
 const progress=Math.max(0,Math.min(1,(local-trace.typing_start_scene_s)/.6));
 const command=trace.command.slice(0,Math.floor(progress*trace.command.length+1e-7));
 const rows=[{kind:'command',text:command}];
 for(const row of trace.rows)if(elapsed+1e-9>=row.at_s)rows.push({kind:row.kind,text:row.text});
 const reasoning=rows.at(-1)?.kind==='reasoning'&&!done;
 const tenths=done?Math.round(trace.verdict.at_s*10):Math.floor((Math.max(0,elapsed)+1e-9)*10);
 return {rows:rows.slice(-5),clock:`${(tenths/10).toFixed(1).padStart(4,'0')} s`,
  running:local+1e-9>=trace.start_scene_s&&!done,done,
  cursor:reasoning&&Math.floor(elapsed/.65)%2===0};
}

export function localTerminalAt(local,trace){
 if(!trace||local+1e-9<trace.typing_start_scene_s||local+1e-9>=trace.end_scene_s)return null;
 const progress=Math.max(0,Math.min(1,(local-trace.typing_start_scene_s)/.6));
 const command=trace.command.slice(0,Math.floor(progress*trace.command.length+1e-7));
 const elapsed=Math.max(0,(local-trace.start_scene_s)*trace.speed);
 const rows=command.split('\n').map(text=>({kind:'command',text}));
 const frame=[...trace.frames].reverse().find(frame=>elapsed+1e-9>=frame.at_s);
 if(frame)rows.push(...frame.rows);
 const done=elapsed+1e-9>=trace.frames.at(-1).at_s;
 return {rows:rows.slice(-5),clock:`${Math.min(elapsed,trace.source_duration_s).toFixed(1)} s`,running:!done,done,cursor:false};
}
