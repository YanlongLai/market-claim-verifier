# Site judge follow-up, 2026-11-04

Base: `22bab8e4`, including per-provider budgets `7eb894a6`. The three independent meters and Baseten default remain in place. No deployment or paid check was performed.

## Changes and checks

- Provider presentation: Meta Model API, Baseten, Fireworks; Baseten stays selected by default. Both language pages share the same structure. Current provider tables use the same order; recorded scores and receipts are unchanged.
- Judge hint: the team name, with no password value embedded in site HTML or JavaScript. The requested password value appears in README, the judge guide and submission notes.
- Time chain: runner/model HTTP 85 seconds; server text 90 / example 95; Pages origin text 92 / example 97; browser single 100. Pages comparison fetches members sequentially, with separate origin responses and a shared deadline of at most 290 seconds. Budget/provider failures continue; a rate stop ends the sequence.
- Hero: full-width copy above the full-width stamp scene. Existing phone card stacking, robot, callout, animation timing and step bar remain. Issuer and author text wraps at word boundaries. The English persona is US Stocks in 1 Minute with its English handle; the Chinese identity remains in the Chinese locale.
- The existing protected site-data hash remains unchanged. Its regression test reverses only the authorized display-order, Meta label and English handle changes before checking the original hash, so all financial values, records and excerpts remain protected.

## Retained runs

- [First focused run](targeted-attempt1.log): 514 passed, one failed. The new copy-wide purity check found an old Chinese example-tab label in the English dictionary. It is now translated; the check was retained.
- [Second focused run](targeted-attempt2.log): 149 passed, including the new locale-data purity, provider order/default, timer and stacked-layout assertions.
- [Pages boundary run](node-attempt1.log): 29 passed, including sequential fetch/body consumption, independent member errors, authentication rejection and the 290-second shared deadline.
- [First full verification](verify-attempt1.log): 1527 passed and four failed assertions that still required the old password hint; all four were updated to the exact requested English/Chinese note.
- [Password/form follow-up](targeted-attempt3.log): 57 passed.
- [Second full verification](verify-attempt2.log): all 1531 product tests passed; the demo suite had 203 passes and three stale preview/source-hash failures after the site updates. Only hash metadata was refreshed; [protected host-output hashes](demo-preview-refresh.json) are unchanged.
- [Demo follow-up](demo-final.log): 206 passed. [Standalone demo Node tests](demo-node-final.log): 97 passed. [Figure preflight](figures-preflight.log) and [offline links](links-preflight.log) passed.
- [Final full offline verification](verify-attempt3.log): passed. All 1531 product tests, 206 demo tests, standalone Node tests, figures, byte-identical rebuilds and offline links passed. This is the authoritative complete receipt. Includes both Python suites, standalone Node tests, figures, byte-identical data rebuilds and Markdown links. No new model calls, SEC requests, OCR or ASR testing.
- [Source lint](lint-final.log): zero failures. Its two warnings concern UTC date padding and existing em dashes; neither changes the hero composition.

## Browser and README host handoff

The [browser inspector could not launch Chrome](inspect-before-failed.log), and the [browser host was unavailable](browser-host.json). Therefore these records contain no fresh visual approval. Existing scene tests supply offline behavior and CSS envelopes, not measured browser font geometry.

The [README capture attempt](capture-attempt1.log) failed because Playwright is unavailable. Its detailed failure is retained in the screenshots subdirectory. No screenshot PNG was created, replaced or staged. The prior PNGs remain historical assets; the host must regenerate them after applying these commits.

The [capture script](../../../scripts/capture_readme_shots.py) now refuses a capture unless all three provider meters and the new password hint are visible inside Try, the provider order is correct, and Baseten is selected. It records source hashes and enforces the corrected-draft image height of at most 1500 px. Run the host commands documented in that script, then commit only the fresh PNGs and their new receipt.

Git staging failed because the worktree metadata is outside the writable sandbox. The delivery commit and bundle are constructed using temporary Git metadata in `/tmp`; the original worktree branch reference cannot be advanced here. The bundle has the original base commit as a prerequisite and can be imported by the host.
