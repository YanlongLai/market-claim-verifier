/** Find the already-installed Playwright. Never let npx download a package. */
import {createRequire} from 'node:module';
import {existsSync, readdirSync} from 'node:fs';
import {homedir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const require = createRequire(import.meta.url);

export function playwright() {
  const candidates = [process.env.PLAYWRIGHT_MODULE, 'playwright', '/opt/homebrew/lib/node_modules/playwright'];
  const cached = path.join(homedir(), '.npm/_npx');
  if (existsSync(cached)) {
    for (const entry of readdirSync(cached).sort()) candidates.push(path.join(cached, entry, 'node_modules/playwright'));
  }
  for (const candidate of candidates.filter(Boolean)) {
    let module, manifest;
    try {
      module = require(candidate);
      manifest = require(require.resolve(path.join(candidate, 'package.json')));
    } catch { continue; }
    if (!/^1\.64\./.test(manifest.version)) continue;
    return {chromium: module.chromium, version: manifest.version};
  }
  throw new Error('Playwright 1.64 is not installed. Install it and Chromium on the host first. '
    + 'PLAYWRIGHT_MODULE may point to its existing package directory. No network installation was attempted.');
}

export async function launch() {
  try {
    return await playwright().chromium.launch({headless: true});
  } catch (error) {
    throw new Error('Chromium could not launch. If the sandbox reports MachPortRendezvous / Permission denied, '
      + 'run this command on the host. Leave live captures pending; do not substitute screenshots or fake footage.\n'
      + String(error).slice(0, 1800));
  }
}

export function isPublicProjectURL(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.host === 'yanlonglai.github.io'
      && url.pathname.startsWith('/market-claim-verifier/');
  } catch { return false; }
}

export async function restrictNetwork(context, localOnly = false) {
  await context.route('**/*', route => {
    const url = route.request().url();
    const allowed = localOnly ? url.startsWith('file:') : isPublicProjectURL(url);
    return allowed ? route.continue() : route.abort('blockedbyclient');
  });
  await context.routeWebSocket('**/*', socket => socket.close());
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url) && process.argv[2] === '--version') {
  console.log(playwright().version);
}
