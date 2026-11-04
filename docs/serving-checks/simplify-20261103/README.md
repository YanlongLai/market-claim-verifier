# Approved information architecture — 2026-11-03

Implementation on `site/simplify`, based on `f54856f6b60477db15ee5a6a680a77d4be6e0ae1`. The owner supplied `DESIGN-final.md` sections 1–3 and `fact-sheet-2026-11-03.md`; the approved positioning and all eight bilingual fact-table rows are retained verbatim. AI001 remains disabled.

## Content and preservation

- [README](../../../README.md): 12-line opening, shared fact table and linked technical detail. [繁體中文](../../../README.zh-TW.md) follows the same structure.
- [Judge guide](../../../JUDGES.md): watch → saved check → live check → evidence; shared table, honesty limits and disclosure. Video TODO retained; live-check TODO replaced.
- [Homepage](../../site/index.html) and generated [Chinese page](../../zh/index.html): Hero → Try → Facts → Evidence → footer; navigation Try · Facts · Evidence. The saved trace opens on request. No corrected-draft output is invented for the saved run.
- [Technical guide](../../evidence/TECHNICAL_GUIDE.md), [Chinese reference](../../evidence/TECHNICAL_GUIDE.zh-TW.md), [extended judge review](../../evidence/REVIEW_GUIDE.md), [site evidence tour](../../evidence/site-tour/index.html): relocated material, original anchors and honesty labels retained. Existing evidence files are preserved. The [public evidence index](../../evidence/index.html) links source documents on GitHub so repository-relative references resolve.
- Metadata, Open Graph, Twitter, JSON-LD and both `llms.txt` files use 240/266 (90.2%) and false support 1/139. Historical full-set charts and scores live on evidence pages and remain labelled; real-world coverage remains distinct from accuracy.
- [Production receipt](../../evidence/live-prod-2026-11-03/REPORT.md) records the owner's supplied production checks, with their provenance. No paid model calls, SEC requests, synthesis, deployment or media rendering were performed for this IA update.

## Validation

The existing offline tests now exercise the stamp scene on its evidence page and the live form on the homepage. SEO checks independently recompute the held-out numerator and false-support denominator from the saved per-claim results.

Browser limitation: the frontend skill's Chrome inspector exited before opening the page (`Chrome exited early, code null`); the computer-use browser host was also unavailable. No new browser screenshots or visual-approval claim are made. Static lint and offline DOM/runtime checks remain available.

The initial Markdown-link scan found the missing validation receipt itself; this file supplies that destination. The [initial scan](links-initial.log) and [baseline frontend lint](taste-baseline.json) are retained.

The [first full verifier run](verify-attempt1.log.gz) reported **3 failed, 1,140 passed**: two checks still expected relocated capabilities/scene masks on the homepage, and one new architecture assertion rejected a retained bookmark as if it were an animation container. The [focused site run](targeted-site-attempt1.log.gz) reported **1 failed, 111 passed** before that bookmark assertion was narrowed to the actual container class. The [focused correction check](targeted-fix.log) passes. These logs retain the failures rather than replacing them.

The route crawler's [first audit](routes-attempt1.log.gz) exposed repository-only links reached through locally served Markdown. The [second audit](routes-attempt2.log.gz) reduced this to the existing extensionless explorer URL and two live API routes. The preview resolver now recognizes an existing `.html` counterpart; nonexistent paths still return 404. The crawler reports `/api/budget` and `/api/check` as runtime routes covered by the server/Pages-boundary tests. The [final route audit](routes-final.log) checks **37 local paths, zero missing files, two runtime routes**, without SPA fallback or external fetches.

[Final static frontend lint](taste-final.json): **0 failures, 4 warnings**, matching the baseline warning categories (existing form outlines, trace numbering and em-dash usage). Approved table wording is retained.

The [second full verifier run](verify-attempt2.log.gz) reported **12 failed, 1,131 passed**: the static-scene seek checks still asserted `../evidence/` links after the implementation switched to required root-relative links. The [diagnostic run](runtime-diagnosis.log.gz) isolated this expectation; the [corrected seek checks](runtime-fix.log) pass all **12** size/language/reduced-motion combinations.

The [copy and preservation audit](copy-audit.log) confirms all eight approved English/Traditional Chinese answers, the 12-line README opening, every original Markdown/HTML anchor, unchanged recorded data and saved traces, unchanged pre-existing evidence, and no edits under `workers/`, `server/`, `functions/` or `src/`.

Startup review found that legacy bookmark IDs could still match the old widget renderers. The homepage now skips the historical dataset entirely; the evidence tour retains its explicit `data-evidence-tour` marker and loads it. The [regression before the fix](homepage-boot-before.log.gz) and [final startup checks](bootstrap-final.log) retain both behaviors, including opening the saved check and changing language. Three startup checks pass. Intermediate test-adapter calibrations are retained: [translated labels](homepage-boot-translation-expectation.log.gz), [CSS attribute selectors](homepage-boot-selector-adapter.log.gz), [document fragments](archive-boot-fragment-adapter.log.gz), and [rounded historical chart labels](archive-boot-rounded-chart.log.gz).

The [third verifier run](verify-attempt3.log.gz), with `UV_OFFLINE=1`, passed **1,143 product tests** and **205 demo tests**, then found one stale website-script hash in the active demo preview. `demo/motion_v3.py --preview-only` regenerates that single hash; the measured host timeline, narration and keyframes remain unchanged. The [focused preview check](demo-preview-fix.log) passes. The hover source was also regenerated from the final website script.

The [fourth verifier run](verify-attempt4.log.gz) passed **1,146 product tests, 206 demo tests and 97 standalone Node tests**, then found that the figure registry still checked embeds against the former long README. The figure builder, registry output paths and [visual index](../../VISUALS.md) now target the relocated technical guide. Recorded inputs, chart values, figures and prompt files remain unchanged. The [focused check](figure-reference-fix.log) and [disposable offline rebuild](figure-preflight.log) both pass, including the post-rebuild check and Markdown links. Future figure rebuilds keep the root README short.

[Final implementation hashes](sources.sha256.json) record the approved spec sections, supporting fact sheet, implementation files and unchanged saved data outputs.

The [fifth verifier run](verify-attempt5.log.gz) reported **1 failed, 1,145 passed**: the figure-builder test's isolated fixture still created a root README instead of the relocated technical guide. The fixture now follows the documented reference location; the [focused figure regression](figure-fixture-fix.log) passes.

## Final result

`UV_OFFLINE=1 bash scripts/verify.sh` is green: **1,146 product tests, 206 demo tests and 97 standalone Node tests**. The [complete final log](verify-final.log) records the offline suites, figure input/embed checks and regeneration, three byte-identical explorer/site/build outputs, one byte-identical wild snapshot, Markdown links/anchors, network guards and unchanged source-tree check. All earlier failed attempts remain alongside it.

The final implementation is sealed by **32 source hashes** and four unchanged recorded-output hashes in [the manifest](sources.sha256.json). Generated `/zh/`, asset stamps and the demo hover/preview source match the final website script. No files under `workers/`, `server/`, `functions/` or `src/` changed.

The delivery commit is prepared with isolated Git metadata because the worktree's shared Git directory is outside the writable workspace. A bundle is verified against the original base and imported into a separate base clone; the original branch reference is not changed. Browser inspection remains unavailable as described above.
