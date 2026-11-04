# Simplification review round 2 — 2026-11-03

Base: `a708c61c4dfe5f0c754ef49a7ee9f8b2c8487cd7` on `site/simplify`.
AI001 remains disabled. The accepted structure, navigation and headline
values are retained. No new design direction was drawn. `DESIGN-final.md`
was absent from the checkout; the owner's supplied section 6 rules and
S1–S9 review instructions govern this change.

## Copy and layout changes

- The public summaries use one price, timing and accuracy format. The
  [number regression tests](../../../../tests/test_site_copy.py) scan
  README EN/繁中, JUDGES, both llms files, site EN/繁中 and site COPY.
  The HTML scan includes JSON-LD, meta, OG and Twitter descriptions.
  Historical evidence retains its original measurements and scores.
- The shared Facts table has two columns and eight bilingual answers.
  English answers contain at most 84 characters; 繁中 at most 34.
  Both site languages show the 繁中 answer below the English answer.
  Nuance is in [Facts in detail](../../../evidence/REVIEW_GUIDE.md#facts-in-detail),
  linked once under each table. Site links use GitHub's rendered guide,
  where repository-relative references resolve.
- README keeps its 12-line first screen. Lines 6–9 each state one fact
  and contain 30, 21, 9 and 34 characters. Navigation chains have at most
  three items. The Chinese opening follows the same arrangement.
- The corrected-draft block has one sentence per language. The Try
  section keeps its scope line. All 68 original site anchors and all
  17 explicit JUDGES anchors survive; the former 33-link site list and
  16-link JUDGES list have no visible link list.
- The Chinese hero uses 1.08 line-height and a 26 px minimum size.
  Section headings share one scale. Paragraphs use a 65ch maximum;
  Facts headers use sentence case. All four evidence metrics use 2rem
  with one caption style, and each card note is a short sentence.
- `/zh/`, CSS/JS stamps, demo Hover source hash and offline preview
  provenance were regenerated. Product code, raw evaluation evidence,
  figures, data snapshots and measured narration remain unchanged.

## Validation receipts

- [Final `bash scripts/verify.sh` run](verify-final.log): **1,163 product
  tests, 206 demo tests and 97 standalone Node tests passed**. Figure
  checks and rebuild, all three site/explorer data outputs, wild data,
  Markdown links and offline guards pass. No model calls or SEC fetches.
  The [initial full run](verify-attempt1.log) also passed; the final run
  includes the detail-link correction and shorter Chinese navigation.
- [Focused checks](targeted-final.log): **22 passed**, covering number
  consistency, bilingual wording, length limits, bookmark preservation,
  metadata, Chinese generation and asset hashes.
  [The earlier focused check](targeted-attempt1.log) also passed.
- [Copy and preservation audit](copy-audit.log): all eight summary
  surfaces, all original anchors and protected evidence paths pass.
  [Source hashes](sources.sha256.json) identify the reviewed files.
- [Final Markdown-link check](links-final.log) includes this receipt;
  [delivery preflight](delivery-preflight.log) verifies the base, branch,
  source hashes and unchanged source Git metadata.
- [Routes](routes-final.log): **37 local paths, zero missing files,
  two runtime routes**, no SPA fallback. The [first audit](routes-attempt1.log)
  found that serving the raw Markdown guide exposed repository-only
  links; the final site links point to the rendered GitHub guide.
- [Demo regeneration](demo-refresh.log): Hover source refreshed; the
  offline preview regenerated and passes `--preview-only --check`.
- [Final frontend lint](taste-final.json): **zero failures, four warnings**.
  [Baseline](taste-baseline.json) has the same warning categories: form
  outlines, trace numbering and existing em-dash usage. The real form
  boundaries and trace formatting are retained; copy uses fewer dashes.

## Browser limitation

The [inspector exception](inspect-baseline.log) and
[Computer Use results](browser-access.log) are retained. Chrome exited
before the inspector could open the page; the browser host was
unavailable, and native Chrome access was rejected by Computer Use.
No screenshots or visual scores are claimed. Desktop/375 px EN/繁中
confirmation remains pending, including the exact hero/table wrapping,
paragraph measure, two-line card notes and absence of horizontal scroll.

The existing round 1 receipts are preserved. These checks do not make
paid model calls, fetch SEC data, retest OCR/ASR, render media or deploy.
