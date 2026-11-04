/** Paint decoded pixels, so frame zero never depends on the video compositor. */
export function waitForVideo(video,event,ready,action){
 return new Promise((resolve,reject)=>{
  let timer;
  const cleanup=()=>{clearTimeout(timer);video.removeEventListener(event,done);video.removeEventListener('error',failed);};
  const done=()=>{if(ready()){cleanup();resolve();}};
  const failed=()=>{cleanup();reject(new Error(`Recorded image unavailable: ${video.dataset.source}`));};
  video.addEventListener(event,done);video.addEventListener('error',failed);
  timer=setTimeout(failed,15000);
  if(video.error)return failed();
  if(action)action();
  done();
 });
}
export async function paintVideoFrame(video,time,canvas){
 await waitForVideo(video,'loadedmetadata',()=>video.readyState>=1);
 const target=Math.max(0,Math.min(time,video.duration-1/30));
 if(Math.abs(video.currentTime-target)>.0001||video.seeking)
  await waitForVideo(video,'seeked',()=>!video.seeking&&Math.abs(video.currentTime-target)<.0001,()=>{video.currentTime=target;});
 // loadedmetadata at currentTime=0 does not mean the first image is decoded.
 await waitForVideo(video,'loadeddata',()=>video.readyState>=2&&!video.seeking);
 if(video.videoWidth!==1920||video.videoHeight!==1080)throw new Error('Native recording must stay 1920x1080');
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 ctx.drawImage(video,0,0,1920,1080);
 canvas.dataset.nativePageReady='true';canvas.dataset.sourceTime=String(target);
}
