import {mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {launch, restrictNetwork} from '../capture/browser.mjs';

const [template, output] = process.argv.slice(2);
if (!template || !output) throw new Error('Usage: node demo/cards/render.mjs TEMPLATE.html OUTPUT.png');
await mkdir(path.dirname(output), {recursive:true});
const browser = await launch();
try {
  const context = await browser.newContext({viewport:{width:1920,height:1080}, deviceScaleFactor:1,
    colorScheme:'light', serviceWorkers:'block'});
  await restrictNetwork(context, true);
  const page = await context.newPage();
  await page.goto(pathToFileURL(path.resolve(template)).href, {waitUntil:'networkidle'});
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path:output, type:'png', animations:'disabled'});
  await context.close();
} finally {
  await browser.close();
}
