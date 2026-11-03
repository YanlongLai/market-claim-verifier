# Site round 3 — viral post first

Base: `0d11d8127b3026d9d20f98f8e49b1af4eafdbc86`; delivery branch: `site/r3`.
AI001 remains disabled. `DESIGN-final.md` was absent from the checkout and
the local folders searched; the owner's R1–R4 requirements and existing
round 2 style govern this bounded change. No new design direction was drawn.

## Result

- The placeholder and **Use Apple example** preserve the recorded post verbatim,
  including its emoji, blank lines and trailing newline: **323 Unicode code points**.
- The primary saved result is **Saved check · viral post · 28 Oct 2026**.
  **Saved check · one claim** remains a secondary selector. The hero's saved-check
  action returns to the post even after selecting the one-claim example.
- [The post envelope](../../site/data/live-demo-post.json) combines the unchanged
  report, extraction trace and three verification traces, with five source hashes.
  Evidence IDs are qualified by assertion because each trace restarts at E1.
  It contains one deterministic edit: **$416.2 billion → $102.5 billion**, citing
  the annual 10-K and nine-month 10-Q. Three supported program checks and the
  unjudged valuation opinion retain explicit bilingual reasons for no correction.
  The correction is derived from frozen program checks; no new model run occurred.
- Rendered order in both languages: **verdict → corrected draft → SEC evidence
  (including the program-check details) → agent trace**. Detailed claim rows are
  inside the proof section so they do not push the correction below the proof.
- The localhost-only Pages mock accepts both saved inputs. The production path,
  `src/`, `workers/live/`, `server/` and `functions/` logic are unchanged.
- `/zh/`, CSS/JS stamps, the demo Hover source hash and the offline preview hash
  were regenerated. The original one-claim JSON, site/explorer data, paragraph
  counts and legacy anchors remain unchanged. [Preservation audit](preservation-final.log).

## Retained checks

- [Full `bash scripts/verify.sh` run](verify-final.log): **1,251 product tests,
  206 demo tests and 97 standalone Node tests passed**. Both saved envelopes
  rebuild byte for byte. Figure checks/rebuild, three site/explorer outputs,
  wild data, offline guards and Markdown links pass. Verification runs in a
  disposable copy; [the final Markdown check](links-final.log) also includes
  this subsequently added receipt.
- [Focused final run](targeted-final.log): **372 passed**; includes saved-post
  rendering in EN/繁中 at 390/768/1280 px, exact default text, selector/hero behavior,
  one cited edit, all retained reasons, result section order and stamp runtime tests.
- [Initial focused run](targeted-attempt1.log.gz): 14 failed, 27 passed. New checks
  used an abbreviated Chinese verdict and lacked a focus stub; existing fetch
  fixtures still expected the old default. [Second run](targeted-attempt2.log):
  41 passed after correcting those fixtures. The final run also checks the proof
  grouping and the broader stamp/copy suites.
- [Pages mock/boundary tests](mock-final.log): **12 passed**, including both recorded
  inputs, rejection of other inputs and the production restriction on mock mode.
- [Route audit](routes-final.log): **38 local paths, zero missing**, two runtime
  routes, no SPA fallback. [Initial Markdown check](links-attempt1.log) passed.
- [Demo check](demo-refresh.log): Hover source matches the site hash; the preview
  remains 13 scenes / 177.2611 seconds. No narration, browser capture or video render.
- [Source hashes](sources.sha256.json) identify the reviewed implementation,
  regenerated artifacts, tests and both saved envelopes.

## Browser boundary

[The real-browser inspector](inspect-attempt1.log) failed before page access:
Chrome exited early. [Computer Use](browser-access.log) reported its browser host
unavailable. No screenshots or visual scores are claimed; responsive DOM/CSS
adapter checks are not browser font or overflow measurements.

[Frontend lint](taste-final.json) flags the owner's required verbatim thread emoji
in the textarea placeholder. It is source text, not an added UI ornament, and is
retained as instructed. The four warnings match round 2: two real form outlines,
trace numbering and existing em-dash usage. Existing design conventions remain.

All checks reuse recorded data. No paid calls, SEC fetches, OCR/ASR rechecks,
synthesis, full media rendering, publishing or deployment were performed.
