# Try v3 site integration and W2 round 2

Merge source: `feat/w2-site` at `3ff78d32`; first parent: `feat/try-v3` at `2211ac0d`. The merge preserves the determinism changes and r4/r5 result presentation while adding the W2 story × input × provider × history interface and W3's 15 ready assets. No model calls, SEC fetches, narration synthesis or production deployment were made for this integration.

## Merge decisions by file

| File | Decision |
| --- | --- |
| [docs/site/script.js](../../../docs/site/script.js) | Combine W2 selection, example-ID requests, provider comparison, saved results and history with HEAD's readable citations, SEC primary lines, verbatim correction spans, rounded main receipt and correction-dependent trace disclosure. Accept the committed 15-row W3 catalogue as well as the W2 object format and the older five-row array. |
| [docs/site/index.html](../../../docs/site/index.html) | Take W2's Try form, story chips, input tabs, provider controls and history panel; preserve the saved claim/post entry points and remove the redundant draft explainer. Re-stamp assets. |
| [docs/site/styles.css](../../../docs/site/styles.css) | Keep HEAD's readable result/citation/evidence styles and W2's controls/history styles. Set the history breakpoint to two columns at 1024 px and above, stacked below. Preserve the established palette, type and model-ID monospace. |
| [docs/zh/index.html](../../../docs/zh/index.html) | Regenerate from the combined English template and COPY dictionary; do not hand-merge generated translations. |
| [docs/examples/manifest.json](../../../docs/examples/manifest.json) | Start from W2/W3's 15-asset catalogue and rebuild. All 15 assets are ready; source hashes and recorded media remain unchanged. |
| [docs/site/data/examples/index.json](../../../docs/site/data/examples/index.json) | Start from W2/W3 and rebuild from the catalogue and retained saved results. Missing recordings have null saved-result paths. |
| [scripts/build_examples.py](../../../scripts/build_examples.py) | Start from W2/W3; emit notices only for pending media, remove stale ready-media notices, and reject stale notices during `--check`. |
| [scripts/build_example_results.py](../../../scripts/build_example_results.py) | Start from W2; reuse W3's `recorded_envelope` validation/serialization so later host recordings rebuild identically. Hash the actual retained legacy text rather than the first, different W3 asset. |
| [tests/test_site_examples_runtime.py](../../../tests/test_site_examples_runtime.py) | Keep W2's complete matrix/compare/history/race/security suite; update presentation expectations and add committed-catalogue, count, missing-save and reset-time cases. |
| [tests/test_site_live_runtime.py](../../../tests/test_site_live_runtime.py) | Keep HEAD's r4/r5 and determinism-era result, precision, language, password and budget checks; adapt selectors and request expectations to W2. |
| [demo/motion/v3/hover-source.js](../../../demo/motion/v3/hover-source.js) | Regenerate using `motion_v3.hover_source`; do not hand-merge. |
| [demo/motion/v3/preview-data.js](../../../demo/motion/v3/preview-data.js) | Regenerate using `demo/motion_v3.py --preview-only`. No host media render or voice generation. |
| [docs/evidence/index.html](../../../docs/evidence/index.html) | Regenerate CSS/JS content-hash references. |
| [docs/evidence/site-tour/index.html](../../../docs/evidence/site-tour/index.html) | Regenerate CSS/JS content-hash references. |

HEAD's model-read-first, hostile-text, trace-collapse and saved/password/busy/budget regressions are also retained in [tests/test_site_result_order_runtime.py](../../../tests/test_site_result_order_runtime.py). W3's asset/provenance tests and the original asset/host-recorder tests remain, with merged catalogue/path expectations and notice lifecycle coverage.

## Rendered result order

**What the model read → run receipt → verdict → corrected draft (or “Nothing to correct in the checked claims”) → SEC evidence → agent trace.**

The trace is collapsed when a valid correction exists and open otherwise. Corrected draft text changes only the recorded Unicode code-point spans; readable citation and evidence summaries retain their raw data disclosures. Main receipt costs round to cents and durations to tenths of a second; raw data retains precision.

## Review items

1. The actual W3 manifest now loads successfully. Example text is loaded into the textarea and the counter counts that text, including Unicode code points. Loading or failed catalogue requests have their own states; “Example asset pending” is reserved for an asset marked pending.
2. Remove the standalone “Corrected draft — A corrected draft replaces…” explainer between form and history. Corrections remain in each rendered result.
3. History sits beside the form from 1024 px upward and below it on smaller viewports. Regression widths include 1023, 1024 and 1280 px.
4. “Compare on all” has the adjacent “≈3× cost” note, localized in Chinese. Model IDs retain monospace.
5. The limit is described as **5 checks / 10 min per IP**, including shared office IPs. Rate-limit errors show a dated reset time and timezone derived from the server's `retry_after`; the same deadline survives language changes. Missing retry timing is explicitly unavailable. Password lockouts use the same reset display.
6. English/Chinese site copy, README files, JUDGES and both llms.txt surfaces use **6–20 s live (one claim → four-assertion post); 10 s median in the benchmark**. Owner-supplied production observations for 2026-11-03 were one claim 6.3 s and a four-assertion post 12.9–21.8 s. These are recorded observations, not new measurements or service guarantees.
7. Delete all six stale `a/b/c.mp3/mp4.pending.txt` files. The builder produces no pending notices while all 15 assets are ready. Tests cover genuine pending media, stale-notice rejection and readiness transitions.
8. The button/status says “Saved result pending” for absent recordings without fetching or linking a nonexistent result. The legacy `text.json` contains the older post, not the new `a-text` input; it remains accessible through the saved-post fallback and is not relabelled as a W3 run. All 15 new story/input IDs currently await matching host recordings. After the host records them, rebuild both catalogues offline with `scripts/build_examples.py` and `scripts/build_example_results.py`; each builder supports `--check`.

## Validation

`bash scripts/verify.sh` completed successfully: **1,416 product tests, 206 demo Python tests and 97 standalone Node tests passed**. [Full passing receipt](verify-r2.log). Asset/envelope rebuilds, figure checks/regeneration, explorer/site/wild rebuilds and Markdown links all passed without model calls, SEC fetches or credentials.

The [final copy/result runtime check](copy-runtime-final.log) passed 74 tests. The [preview reproducibility regression](preview-test-r1.log) passed after regenerating the final preview. [Source lint](design-lint-r2.log) has zero failures. [Final link checks](links-final.log) passed.

The [first verifier attempt](verify-r1.log) passed all 1,416 product tests and then found the stale preview source hash; that failed run is retained. Earlier focused attempts are retained as `focused-r1.log.gz`, `focused-r2.log.gz` and `focused-r3.log.gz`, alongside builder/bootstrap and browser failures. These offline checks do not retest OCR/ASR and do not establish a new accuracy score.

Browser capture could not run: the skill inspector's Chrome process exited early, and the in-app browser reported “The browser access host is unavailable.” No screenshot-based visual review is claimed. Source lint reported zero failures; its warnings concern preserved trace ordinals and data/missing-value em dashes.

## Delivery

This worktree's Git metadata points outside the writable workspace. The initial merge failed while creating `ORIG_HEAD.lock`; the integration therefore uses temporary writable Git metadata and is delivered as `try-v3-site.bundle`, with a real merge commit on its `feat/try-v3` ref and the requested co-author footer. The original worktree branch pointer remains at `2211ac0d`; merged files are present in the workspace. Existing `live-determinism.bundle` and `w1-server.bundle` are preserved.
