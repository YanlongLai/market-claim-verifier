Site polish verification, 2026-11-03 UTC. Local worktree only; no publication, model calls, SEC requests, synthesis, or video rendering. Baseline: `origin/main` at `bd4aee434cd2c6bce6c6d1792bba2be91c18d3b8`.

The [home page](../../site/index.html) now has the canonical URL, complete Open Graph/Twitter metadata, bilingual DappGo titles, theme colors, robot-derived icons, and bilingual footer credits. The [1200×630 preview](../../site/img/og/og-image.png) is a Chrome capture of the real saved scene at `?stamp-t=49.5#top`, composed with the existing headline. Its final size is **293,558 bytes**. No new imagery or financial figures were generated. The [icon and crawl artifact checks](assets.json) record dimensions and the two sitemap destinations.

[robots.txt](../../robots.txt), [sitemap.xml](../../sitemap.xml), [404.html](../../404.html), and [security headers](../../_headers) live directly under `docs/`. The preview server mirrors the Pages root-copy overlay and returns an actual HTTP 404 for missing paths. The browser check tested that response and the no-JS fallback.

The initial [recursive route crawl](routes-original.txt) found seven Markdown links into repository-only `tests/`, `scripts/`, and `src/` paths, all reached through the multimodal report. Both capability links now open that report on GitHub, where those relative links resolve. The recorded report itself was preserved. **Before adding 404.html**, the [second crawl](routes-before-404.txt) checked **20 local paths, zero missing**. The [final static crawl](routes-final.txt) checks **28 paths, zero missing**, including both explorer languages, scripts, stylesheets, CSS images, metadata images, fetched data, and linked Markdown documents. The [rendered route check](rendered-routes.txt) additionally tested **57 distinct local href/src destinations with HTTP HEAD: all 200**, against the server with no SPA fallback.

The hero starts at **3.02 seconds**, when the first post and all filing rows are populated. Absolute timeline coordinates, loop boundaries, explicit `?stamp-t=0`, and saved seek links retain their original meaning. Steps 1–4 are semantic buttons that seek and pause the current review; steps 2–3 are disabled for uncheckable claims. Pause/resume, offscreen/hidden lifecycle behavior, reduced motion, language changes, and progressive enhancement remain covered. Mobile links/buttons, including filing links, report links, dialog controls, and reduced-motion cards, measure at least **44px tall**. The dialog heading has static bilingual fallback text.

Measured from navigation start to visible, nonempty panel text, checking ancestor opacity/display and viewport intersection on every animation frame:

| Viewport / language | Before: post | Before: filing | After: post | After: filing |
| --- | ---: | ---: | ---: | ---: |
| 1440×900 EN | 399 ms | 2643 ms | 134 ms | 134 ms |
| 1440×900 中文 | 459 ms | 2646 ms | 133 ms | 133 ms |
| 375×812 EN | 350 ms | 2640 ms | 117 ms | 117 ms |
| 375×812 中文 | 310 ms | 2507 ms | 130 ms | 130 ms |

Each after-run records both panels populated on the first painted scene frame. These are unthrottled local samples, not a production performance benchmark. [Clean baseline measurements](hero-before.json) use the original HTML/CSS/JS served from `origin/main` with the same viewport and language setup. An [earlier baseline](hero-before-initial.json) is retained: its small HTTP server backlog produced connection resets under four simultaneous asset-heavy pages, and the original missing favicon returned 404. The preview server now uses HTTP/1.1 and a 128-connection backlog; the subsequent baseline and final runs have zero request failures.

The [final browser log](browser-final.log) and [structured results](browser-final.json) cover `/` and `/explorer/`, EN/中文, 1440×900 and 375×812: **zero CSP violations, console errors, failed requests, or horizontal overflow**. Additional checks exercise the filing dialog, all four step buttons, pause/resume, seek times 0 / 12.94 / 25.5 / 33.5 / 49.5, reduced motion, dark mode, language titles, and explorer search (1/357 then 357/357). First-frame and eight-second screenshots, full pages, and supplemental dark/no-JS images are retained at:

```text
/private/tmp/claude-501/-Users-yan-git/8d31d2e6-e330-47b1-860e-dd1fecbc04fe/scratchpad/hk-polish-shots/final-reviewed/
```

The CSP inventory is based on source inspection and the actual requests in `browser-final.json`. External hyperlink destinations are not subresource origins and were not fetched.

| Resource | Home page | Explorer EN/中文 | CSP allowance |
| --- | --- | --- | --- |
| Scripts | `/script.js` | `/explorer/script.js`, `/explorer/script.zh.js` | `'self'`; no inline scripts, event attributes, or eval |
| Stylesheets | `/styles.css` | `/explorer/styles.css`; Google Fonts CSS | `'self'`, `https://fonts.googleapis.com` |
| Inline styles | JS-set geometry/style attributes | Generated chart widths and colors | `'unsafe-inline'` for styles only; also supports the 404's small inline stylesheet |
| Images | `/img/` robot poses, avatars, paper/VFX textures, input/section art, icons | No remote images | `'self'`; `data:` image payloads permitted |
| Fonts | System fonts | Google Fonts font files | `'self'`, `https://fonts.gstatic.com` |
| Fetches | `/data/site.json` | `/explorer/data.json` | `'self'` |
| Frames / objects / forms | None | None | `'none'`; `frame-ancestors 'none'` |
| Cloudflare additions | Same-origin `/cdn-cgi/` challenge scripts; analytics on deployment | Same | Script: `https://static.cloudflareinsights.com`; connect: `https://cloudflareinsights.com`; same-origin scripts allowed |

The explorer scripts were moved byte for byte from each HTML page to external files. The common stylesheet retains every original rule and adds mobile touch sizing. Existing data files, evaluation results, provider configuration, and product code under `src/` were untouched.

[Full offline verification](verify-final.log): **930 product/site tests, 149 demo tests, 55 standalone Node tests passed**, figure checks/rebuild passed, three data outputs rebuilt byte for byte, Markdown links/anchors passed. Final lines:

```text
PASS offline Python and Node suites
PASS figure rebuild + --check
PASS explorer, site data and build summary: 3 byte-identical outputs
PASS Markdown links and anchors
PASS no model calls, SEC fetches or credentials; source tree unchanged
```

The [first verification attempt](verify-attempt1.log.gz) retained five failures: the old local multimodal report href and four 32px-strip geometry expectations. The affected site tests now expect the GitHub destination, 44px strip, populated initial clock, and button markup. The [second attempt](verify-attempt2.log.gz) passed all 930 product/site tests and found two demo snapshot mismatches. Only the generated [site-source adapter](../../../demo/motion/v3/hover-source.js) was refreshed: its site-script SHA, unused initial-clock constant, and extracted comment changed. Its pose/spotlight formulas and saved media/run records were preserved. A new offline test exercises step seeking and uncheckable-step disabling.

Design review kept the existing cream/ink palette, system/Georgia typography, physical filing paper, H auditor art, saved financial text, and interactive review scene. The footer robot now follows its heading so that heading fits in two lines; the mobile rerun table's text floor is 13px. [Source lint](taste-lint.log): zero failures/warnings. [Final inspector](taste-final.log): zero failures and four inherited warnings (font-size variety, the existing 15.7px body size, one long paragraph, and no background video). The real animated verification scene supplies the moving picture. Three explicit inspector allowances retain the frozen post's thread emoji, the data chart's row rules, and ignore hit-test false positives from deeply nested inactive decorative stamps; these were also reported in the [initial inspection](taste-initial.log). Screenshots were visually reviewed at all requested sizes/languages and at the skill's 768px tablet width. Reviewer assessment: design 8/10, usability 9/10, creativity 8/10, content 9/10; weighted 8.4/10. This is a visual review, not an external award or benchmark.

Reproduce from the repository root, using Python/uv/Node and installed Chrome. Browser tooling is installed outside the checkout:

```sh
npm install --prefix /tmp/hk-polish-tools --no-audit --no-fund playwright-core@1.64.1
export PLAYWRIGHT_MODULE=/tmp/hk-polish-tools/node_modules/playwright-core/index.mjs
python3 scripts/serve_site.py --port 8765
```

In another terminal with `PLAYWRIGHT_MODULE` set:

```sh
python3 scripts/check_site_routes.py
uv run --no-project --with pillow==11.3.0 python scripts/render_site_icons.py
node scripts/render_site_og.mjs
SHOTS_DIR=/tmp/hk-polish-shots node scripts/check_site_browser.mjs
sh scripts/verify.sh
```

Use `CHROME_PATH` for a different Chrome executable and `SITE_URL` for another preview port. [OG render log](render-og.log), [asset checks](assets.json), [browser source](../../../scripts/check_site_browser.mjs), [route crawler](../../../scripts/check_site_routes.py), [preview server](../../../scripts/serve_site.py), [OG capture script](../../../scripts/render_site_og.mjs), and [icon renderer](../../../scripts/render_site_icons.py) are retained for reuse. All paid-test counters are zero. Earlier browser runs and partial/failing verifier logs remain alongside the final records. Failed verifier logs are compressed byte for byte (`gzip -dc` to read them); their original-byte hashes are in `inputs.sha256.json`. The post-receipt link check also passed: 143 Markdown files and 1100 local links/anchors ([log](links-final.log)).
