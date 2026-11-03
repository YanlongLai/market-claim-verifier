# SEO, static Traditional Chinese and mobile QA — 2026-11-03

Implemented locally on `feat/seo-ai-20261103`. No deployment or push was performed. The exact new English/Traditional Chinese copy and numerical source map are in [COPY.md](COPY.md).

## Changes

- Generated [the static Traditional Chinese page](../../zh/index.html) from [English HTML](../../site/index.html) and the production [COPY dictionary](../../site/script.js). The generator imports the complete DOM-free Node export, without regex extraction or a second translation dictionary. `scripts/build_zh_page.py --check` runs both in the full verifier and a regression test.
- Added canonical/hreflang metadata and real language links; page language follows its URL even with a conflicting saved preference. Root-relative stamped CSS/JS and runtime image/data URLs work under `/zh/`. `stamp_site_assets.py` includes the generated page.
- Added WebApplication JSON-LD to both landing pages and Dataset JSON-LD to both explorers. Descriptions share their exact text with OG/Twitter/schema fields. Explorer favicon/theme metadata is present; the stray viewport meta is removed. Dataset licensing is omitted because the README explicitly identifies a code license, without a dataset-specific license grant.
- Added [the served crawler guide](../../llms.txt), Content-Signal and a sitemap with reciprocal alternates and lastmod. Existing static routing already serves `/zh/` and `/llms.txt` with HTTP 200; no redirect or SPA fallback is needed. The 404 page includes a Traditional Chinese home link.
- Phone robot poses load eagerly rather than relying on lazy-load visibility below a taller translated hero. Both layouts retain the same animation clock; desktop pose loading and dimensions are unchanged. Language links retain the previous button appearance and touch size.
- Refreshed exactly one source-hash reference in each of `demo/motion/v3/hover-source.js` and `preview-data.js`. The generated animation implementation, recorded media, host timing, cues, narration and benchmark evidence are unchanged.

## Final verification

[Full verifier log](verify-final.log), exit 0:

```text
1014 passed (product suite)
206 passed (demo suite)
PASS offline Python and Node suites
PASS figure rebuild + --check
PASS explorer, site data and build summary: 3 byte-identical outputs
PASS wild findings: 1 byte-identical output
PASS Markdown links and anchors
PASS no model calls, SEC fetches or credentials; source tree unchanged
```

[Post-record Markdown link check](links-final.txt): 182 files, 1,667 local links/anchors; PASS.

`python3 scripts/stamp_site_assets.py --check`: exit 0. `python3 scripts/build_zh_page.py --check`: exit 0, `PASS static /zh/ matches English HTML and production COPY`.

[Route crawl](routes-final.txt): `CHECKED 32 local paths; 0 missing; no fallback used`.

[Final browser results](browser-final.json) and [console output](browser-final.log): eight successful cases, covering `/`, `/zh/`, `/explorer/`, `/explorer/index.zh.html` at 1440×900 and 375×812. Each has zero console/page/HTTP errors, zero failed requests, zero CSP violations, and no horizontal overflow. Mobile visible controls are at least 44 px high. Filtering, filing dialogs, real language navigation, reduced motion and JavaScript-disabled rendering also pass.

`scripts/serve_site.py` applies the actual `docs/_headers` CSP. Curl compared the complete response CSP against that file byte for byte after header whitespace normalization; no policy was injected or relaxed for QA. All four HTML pages plus `/llms.txt` and `/robots.txt` return 200; an unknown path returns 404. See [curl results](curl-final.json). All four JSON-LD blocks parse and use the expected schema type, canonical URL and language.

| Curl route | Raw-HTML visible-text words | Raw Traditional Chinese | JSON-LD |
| --- | ---: | --- | --- |
| `/` | 317 | Existing language/example selectors | WebApplication parses |
| `/zh/` | 329 | Full translated hero, body and accessibility copy | WebApplication parses |
| `/explorer/` | 450 | Existing language selector | Dataset parses |
| `/explorer/index.zh.html` | 649 | Full translated explorer introduction/body | Dataset parses |

Counts use Chrome `Intl.Segmenter` word-like segments on the curl response, excluding head/scripts/styles, hidden and aria-hidden elements, dialogs and closed details. They measure static visible-text content, independently of viewport and JavaScript-generated results.

## Screenshot review

Screenshots are retained in the requested `hk-seo-shots` scratch directory, with the final run under its `attempt2/` subdirectory. [Screenshot hashes and relative filenames](screenshots.sha256) identify every retained image; no machine-specific filesystem paths are committed.

For each landing language and viewport, screenshots cover first render, five seconds, eight seconds, the full page, and deterministic seeks at 0, 1.6, 3.9, 5, 12.94, 25.5, 33.5 and 49.5 seconds. The test also operates all four step buttons and pause/resume. At each seek it waits for a decoded, visible robot pose, verifies overflow and records scene/pose/time. On the phone the robot occupies the existing 88 px slot between the post and filing. Visual review confirmed the robot at read/open/compare/stamp states in both languages and the unchanged desktop composition.

Design-taste static lint has no findings ([before](taste-lint-before.json), [after](taste-lint-after.json)). The broader visual inspector retains exactly the pre-existing findings ([before](taste-before.json), [after](taste-after.json)): thread emoji, chart row rules, decorative TRUE/FALSE text coverage, plus typography/measure/video warnings. Those baseline design choices are outside this focused SEO/mobile change; no new finding was introduced.

## Retained attempts

- [Verifier attempt 1](verify-attempt1.log.gz): 955 passed, 59 failed. Runtime tests still expected relative image paths and all-lazy robot loading. Updated assertions preserve the existing evidence/pose checks while requiring output-root paths and eager phone poses.
- [Verifier attempt 2](verify-attempt2.log.gz): all 1,014 product tests passed; 203 demo tests passed and three failed on generated site-source hash references. Refreshed only the two derived hash references; [the three focused demo checks](demo-focused.log) then passed.
- [Verifier attempt 3](verify-attempt3.log.gz): partial run, stopped after a host-Python preflight lacked YAML, before the preview refresh. The refresh used an isolated environment with the locked demo dependencies. This partial run is not reported as a pass.
- [Final full verifier](verify-final.log): complete pass after those corrections.
- [Browser attempt 1](browser-attempt1.json.gz) / [log](browser-attempt1.log): all eight cases passed. [Final browser run](browser-final.json) adds overflow assertions at every seek and uses the final explorer copy; all eight cases passed again.

[Source and input hashes](source-hashes.json) freeze the final production files, checkers/tests, CSP/routing inputs, generated preview references and published evaluation inputs. Saved evaluation data and reports were reused; no paid model calls, SEC fetches, synthesis or media rendering were performed. Logs redact machine-specific temporary paths while retaining failure details and outcomes.
