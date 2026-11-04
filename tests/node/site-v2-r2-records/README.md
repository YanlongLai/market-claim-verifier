# Site v2 round 2 — offline records

Base: `af5a75adb6bbd682c523ba89face43710cbf4533`, branch `site/r3-polish`.
This is a presentation repair using retained financial evidence. No model calls,
SEC fetches, paid checks or new OCR/ASR tests were performed. The paid-call budget
was $0. Existing claims, results, prompts, provider models and evidence are unchanged.

## Changes covered

- English stamp identities, bylines and repost attribution are localized at the
  data source. Chinese fictional names remain on the Chinese page. The
  [language test](../../test_site_copy.py) checks every rendered text node and
  accessible label, including hidden cards, static cards and multiple scene phases.
- Each Facts topic has one title, a short paragraph and an unboxed
  `Fact: … · Evidence ↗` line. The README and judge-guide facts retain their full
  answers. Accuracy keeps its held-out and corrected-gold qualifications.
- The scene's controls stay below its cards, including on phones, with no
  full-width background strip. Existing 44 px controls, keyboard operation and
  reduced-motion behavior remain. The three saved-check cards stack at 375 px,
  keep their descriptions and accept up/down as well as left/right keys.
- Both READMEs have descriptive GIF alt text and a static PNG link. The existing
  `docs/site/img/readme-robot.gif` was preserved byte for byte. The new PNG is
  exported from its current still; it is not a new browser capture. A successful
  [host capture](../../../scripts/capture_readme_gif.py) also refreshes that PNG.
- Stamp data was rebuilt with `docs/scripts/build_site.py --offline`; `/zh/`
  and the CSS/JS content-hash stamps were regenerated.
- The demo's adapted-source comment and offline preview provenance hashes were
  refreshed. These are five hash entries in two generated files. All ten other
  narration/host files were unchanged; no timing, voice or media was regenerated.

## Runs retained

| Record | Result and boundary |
| --- | --- |
| [Targeted attempt 1](targeted-attempt1.log.gz) | 190 failed, 220 passed. A missing default `order` property in the CSS geometry adapter caused the repeated failures; this attempt is retained. |
| [Purity diagnostic](purity-attempt1.log.gz) | 1 failed, 1 passed. Isolated the same adapter failure at desktop width. |
| [Geometry and purity recheck](geometry-attempt1.log.gz) | 24 passed, 300 deselected after the default was made explicit; covers 375 px geometry and all-node English purity with/without reduced motion. |
| [Copy, SEO and stamps](copy-final.log.gz) | 39 passed after restoring the Chinese held-out label. |
| [Full verifier attempt 1](verify-attempt1.log.gz) | 1 failed, 1,448 passed. The shortened Chinese accuracy line omitted the literal held-out label required by the SEO copy check; the label was restored without changing the result. |
| [Full verifier attempt 2](verify-attempt2.log.gz) | All 1,449 product/site tests passed; 3 demo hash checks failed and 203 passed. The site changes required refreshing the generated demo adapter and offline preview provenance. |
| [Final full verifier](verify-attempt3.log.gz) | `UV_OFFLINE=1 bash scripts/verify.sh` passed: 1,449 product/site tests, 206 demo tests and 97 standalone Node tests; figure rebuild/checks, byte-identical data rebuilds, links and source/network guards passed. |
| [First refresh attempt](preview-refresh-attempt1.txt) and [demo diagnostic](demo-attempt1.log.gz) | The protection check assumed an optional `beats.json` existed and stopped before any writes. The diagnostic retained the same 3 stale-hash failures and 203 passing tests. |
| [Preview refresh](preview-refresh.log.gz) and [before/after hashes](preview-refresh.json) | Preview-only compiler plus `hover_source` adapter; all ten other narration/host files preserved. |
| [Final demo suite](demo-final.log.gz) | 206 passed after the hash refresh. |
| [Standalone Node suite](node-final.log.gz) | 97 passed. |
| [Figure preflight](figures-final.log.gz) and [link preflight](links-preflight.log.gz) | Committed figure inputs/embeds and offline Markdown links passed. |
| [Source lint](lint-final.txt) | 0 failures, 2 warnings. Padding belongs to UTC times; existing em dashes remain in recorded/UI copy. This is not a browser review. |
| [Browser limitation](browser-attempt.txt) | The skill inspector could not launch Chrome; the browser host was unavailable and native Chrome use was not approved. No rendered approval is claimed. |

[Final source hashes](final-source-hashes.json) were collected before the final
offline verifier. [Attempt 2 hashes](verify-attempt2-source-hashes.json) precede
the demo hash refresh; [attempt 1 hashes](verify-attempt1-source-hashes.json) were
collected during that run. Earlier targeted attempts did not freeze their full
input manifests; no retrospective pre-run freeze is claimed.

The final receipt was retained after verification. Final source-hash, link,
mirror, asset-stamp and whitespace checks are recorded in `delivery-checks.json`.

## Browser and host-capture boundary

Offline geometry envelopes and event tests do not measure browser fonts, prove
the rendered two-line limit or replace a visual review. The
[host browser checker](../../../scripts/check_site_browser.mjs) now checks every
English stamp text node, real Facts paragraph/summary line counts, controls below
the scene, stacked cards and overflow at 375 px, keyboard playback and reduced
motion. It saves separate How/Facts screenshots for English and Chinese. Its
syntax was checked; Chromium execution remains pending.

Run the preview in one terminal, then the browser checker in another:

```sh
python3 scripts/serve_site.py
```

```sh
SITE_URL=http://127.0.0.1:8765 SHOTS_DIR=/tmp/site-v2-r2-host \
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
node scripts/check_site_browser.mjs
```

The host GIF capture keeps the requested path, updates the PNG fallback and
retains its frames, log and receipt:

```sh
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
uv run python scripts/capture_readme_gif.py --record-dir /tmp/site-v2-r2-gif-host
```

`DESIGN-final.md` was not present in this checkout; the explicit V1–V5 review
rules were followed while retaining the accepted page structure.
