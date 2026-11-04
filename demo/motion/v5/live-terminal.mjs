/** Stateless projection: seeking backwards and frame capture use only the film clock. */
export function liveTerminalAt(local,trace){
 if(!trace||local+1e-9<trace.typing_start_scene_s||local+1e-9>=trace.end_scene_s)return null;
 const elapsed=local-trace.start_scene_s,done=elapsed+1e-9>=trace.verdict.at_s;
 const progress=Math.max(0,Math.min(1,(local-trace.typing_start_scene_s)/.6));
 const command=trace.command.slice(0,Math.floor(progress*trace.command.length+1e-7));
 const rows=[{kind:'command',text:command}];
 for(const call of trace.calls)if(elapsed+1e-9>=call.at_s)rows.push({kind:'call',text:call.text});
 const reasoning=elapsed+1e-9>=trace.reasoning_at_s&&!done;
 if(reasoning)rows.push({kind:'reasoning',text:trace.reasoning_text});
 if(done)rows.push({kind:'verdict',text:trace.verdict_text});
 const tenths=Math.floor((Math.min(Math.max(0,elapsed),trace.verdict.at_s)+1e-9)*10);
 return {rows:rows.slice(-5),clock:`${(tenths/10).toFixed(1).padStart(4,'0')} s`,
  running:local+1e-9>=trace.start_scene_s&&!done,done,
  cursor:reasoning&&Math.floor(elapsed/.65)%2===0};
}
