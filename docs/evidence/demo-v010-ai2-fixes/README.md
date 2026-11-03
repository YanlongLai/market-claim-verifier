# v010 AI2 fix verification

These are offline source/layout regressions for M1, M2, N1, N2 and N3. No model calls, SEC fetches,
voice synthesis or film render were performed. This is not a new financial evaluation, OCR/ASR test,
audio-alignment study or rendered visual approval. See the [source handoff](../../../demo/AI2-FIXES-v010.md).

Each numbered attempt has its exact argv, UTC start/end and exit status in a same-stem JSON receipt,
plus unabridged stdout/stderr in a `.log` file. Failed attempts remain alongside the later passes:

- [01 compiler](01-compile-realworld.log), [02 B-roll addresses](02-broll-data.log),
  [03 preview](03-preview.log): rebuilt from retained inputs without inference or media rendering.
- [04 focused Python](04-python-regressions.log): **81 passed**.
- [05 initial Node suite](05-node-regressions.log): **26 passed, 2 failed**. Both failures caught a
  16-pixel right-edge overrun in the new aggregate label box. The box width was corrected.
- [06 corrected Node suite](06-node-regressions.log): **28 passed**, including holds at 30 fps,
  type floors, original/post-hoc counts, receipt timing and the replacement source at all 45 frame indices.
- [07 realworld check](07-realworld-check.log), [08 preview check](08-preview-check.log),
  [09 B-roll check](09-broll-check.log): reproducibility/source checks passed.
- [10 browser still attempt](10-browser-layout.log): failed before capture because Playwright 1.64
  was unavailable. No package was installed, no browser still or film was rendered, and no visual
  approval is claimed. The host commands retain this remaining review step.
- [11 first full verifier](11-offline-verification.log): **1,010 product tests passed**;
  **197 demo tests passed, 1 failed** because the extra v010 extraction keyframes also changed the
  historical v007 manifest count. The additional keyframes were scoped to v010; the historical
  manifest contract is preserved.
- [12 final motion suite](12-node-final.log): **28 passed** after adding report links to the cards.
- [13 local links](13-links.log): local Markdown links and anchors passed.
- [14 complete demo suite](14-demo-suite.log): **198 passed** after scoping the extra samples to v010.
- [15 final preview check](15-preview-final.log) and [16 final realworld check](16-realworld-final.log):
  both passed against the final source.
- [17 final full verifier](17-offline-verification-final.log): `bash scripts/verify.sh` passed
  **1,010 product tests, 198 demo tests and 97 Node tests**, figure rebuild/check, three byte-identical
  explorer/site outputs, the byte-identical wild snapshot and Markdown links/anchors. Provider
  credentials were removed and the Python/Node network guards were checked by the verifier.

[reading-plan.json](reading-plan.json) records the compiler replay of retained narration lengths and
the frozen pause fixture. Its times are an offline picture-cue replay, not new phonetic alignment.
[host-output-hashes.json](host-output-hashes.json) records matching before/after hashes for the five
protected host outputs. Financial source/trace records are retained unchanged; the real-world snapshot
now additionally copies the recorded `stated_value` for each selected program check.
