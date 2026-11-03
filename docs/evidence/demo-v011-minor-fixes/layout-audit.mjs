// Extract the actual offline motion renderer's aggregate boxes; no browser or media.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const stage={dataset:{},style:{},innerHTML:''};
const context={document:{getElementById:()=>stage},URLSearchParams,location:{search:''}};
context.window=context;context.globalThis=context;vm.createContext(context);
for(const file of ['logic.js','v3/hover-source.js','v3/preview-data.js','v3/broll-data.js','v3/broll.js'])
  vm.runInContext(readFileSync('demo/motion/'+file,'utf8'),context);
context.MOTION_DATA=context.MOTION_PREVIEW;
vm.runInContext(readFileSync('demo/motion/v3/motion.js','utf8'),context);
const pages=[157,165].map(t=>{
  context.seek(t);
  return {t,boxes:context.frame.boxes.filter(box=>box.text.trim())};
});
process.stdout.write(JSON.stringify(pages,null,2)+'\n');
