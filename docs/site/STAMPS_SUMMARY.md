# Hero stamp animation

Implemented on `site/stamp-animation`, directly after the hero headline/subtitle
and before “A real post, checked.” The scene fills the existing content width at
360 px high on desktop and 300 px on phones. The example follows with a 12 px gap.
No commit or push was made.

## Files changed

- `docs/site/index.html`: labeled scene, scan gate, hidden moving track, accessible
  claim list and pause button.
- `docs/site/styles.css`: responsive cards, ink mask, paper grain, both theme
  tokens and static reduced-motion row; 58%-width double-border stamps,
  condensed caps, 18/16 px claims, paper surfaces/shadows and gate-label pill.
- `docs/site/script.js`: conveyor clock, scan/evidence/stamp sequence, deterministic
  angles, language updates, visibility/off-screen/manual pausing, retained outgoing
  stacking, mask-loading fallback, gate-pill pulse and deterministic seek hook.
- `docs/scripts/build_site.py`: report-derived `stamp_cards` extraction.
- `docs/site/data/site.json`: rebuilt offline, including all nine stamp cards.
- `docs/site/img/stamp-ink.webp` and `docs/site/img/stamp-paper.webp`: generated and
  optimized material textures.
- `docs/prompts/site/stamps.md` and `docs/prompts/site/README.md`: exact prompts,
  generation notes, sizes and reuse instructions.
- `tests/test_site_stamps.py`: report identity, verdict, ticker, source, language,
  filing/evidence and cyclic-order checks.
- `tests/test_site_stamps_runtime.py`: offline JavaScript clock/lifecycle checks.
- `docs/site/STAMPS_SUMMARY.md`: this implementation and verification record.

## Cards, in loop order

Source references below are claim indices within the linked original reports.
Tickers, original quotes, statuses, verdicts, summaries and filing URLs are read
from those reports. Compact bilingual display text preserves the claims; the two
original Chinese quotes are unchanged in Chinese mode.

| Card | Verdict | Source report / claim |
| --- | --- | --- |
| AMZN: Q3 2023 revenue $143.1B | TRUE | [demo-thread-baseten](../evidence/posts-2026-10-28/demo-thread-baseten/report.json), #1 |
| AAPL: fiscal Q4 2025 alone, $416.2B revenue | FALSE | [demo-thread-baseten](../evidence/posts-2026-10-28/demo-thread-baseten/report.json), #3 |
| NVDA: still cheap at 30× sales | CAN'T CHECK (opinion) | [demo-thread-baseten](../evidence/posts-2026-10-28/demo-thread-baseten/report.json), #4 |
| NVDA: FY2024 revenue $60.9B, more than double | TRUE | [demo-thread-baseten](../evidence/posts-2026-10-28/demo-thread-baseten/report.json), #2 |
| TSLA: full-year 2025 revenue grew 3% | FALSE | [bigtech-thread-baseten](../evidence/posts-2026-10-28/bigtech-thread-baseten/report.json), #3 |
| MSFT: FY2024 revenue $245.1B, up 16% | TRUE | [tw-social-post-meta](../evidence/posts-2026-10-28/tw-social-post-meta/report.json), #1 |
| AAPL: revenue will cross $500B by 2027 | CAN'T CHECK (forecast) | [bigtech-thread-baseten](../evidence/posts-2026-10-28/bigtech-thread-baseten/report.json), #5 |
| AAPL: fiscal 2024 revenue $391.0B | TRUE | [bigtech-thread-baseten](../evidence/posts-2026-10-28/bigtech-thread-baseten/report.json), #4 |
| KO: 2024 revenue exceeded $50B | FALSE | [tw-social-post-meta](../evidence/posts-2026-10-28/tw-social-post-meta/report.json), #3 |

There are no equal adjacent verdicts, including the last-to-first transition.
The first three crossings show TRUE, FALSE and CAN'T CHECK over four seconds on
desktop, or 5.776 seconds at a 375 px viewport.
`not_checked` opinions/forecasts keep the report's absent verdict and display
CAN'T CHECK; they never receive SEC evidence chips. The Apple quarter's report
records $102.5B of derived quarterly revenue and supplies no filing URL, so its
static card links to that report. Other cards use their filing URLs where present;
cards without filing URLs retain their source report as a link target.
Report fallback links resolve relative to the published `docs/` root, preserving
the repository prefix on GitHub Pages as well as working in the checkout.

## Motion and accessibility

- Cards travel left to right in six seconds. The crossing interval is
  `max(baseInterval, ceil(6000 * (cardWidth + 24) / (sceneWidth + cardWidth)))`,
  with base intervals of 2000 ms on desktop and 2500 ms on phones. This keeps
  at least 24 px between carriers. At 1280 px the interval is 2000 ms and the
  nine-card cycle lasts 18 seconds; at 375 px the scene is 341 px wide, the card
  is 270 px wide (72vw), the interval is 2888 ms and the cycle lasts 25.992 seconds.
  Playback starts with cards already in flight.
- The 300 ms beam sweep starts 400 ms before the centered gate crossing,
  followed by a 100 ms evidence pop for checkable claims. Stamp contact coincides
  with the card's center reaching the gate, followed by a 300 ms impact/settle.
  The scale moves from
  1.8 to 0.94 to 1.04 to 1.0; the card shakes by at most 3 px. Each claim's hash
  fixes its angle within −12°…+8°. A static blurred ink duplicate fades over
  150 ms to a faint 12% ink bleed. The impression has a 4 px outer border and
  1.5 px inner border, with a more visible 340 px grain-mask scale. Travel,
  sweep, impact, label pulse and settling animate transform/opacity only.
- Stamps and evidence stay on their cards through the right-edge fade. Outgoing
  cards retain higher stacking than incoming cards, including after the previous
  one-second gate highlight would have ended. Hidden cards keep their ink until
  recycled off-screen left. The permanent stamp stays solid if its texture cannot
  load; the luminance mask is enabled only after a successful local-image load.
- Cards continue right and fade out. The animation clock freezes off-screen via
  IntersectionObserver, on `visibilitychange`, and with the pause button; resume
  preserves the current point rather than catching up on hidden time.
- `prefers-reduced-motion: reduce` schedules no animation frames and hides the
  conveyor/gate/pause control. All nine already-stamped, linked cards appear in a
  manually scrollable static row within the same scene height. A preference
  change is handled immediately.
- Moving cards are `aria-hidden` and `inert`. The single matching claim/verdict
  list stays available to screen readers, visually hidden during motion and
  visible for reduced motion. Its links enter keyboard order in static mode.
- Claim text is 18 px on desktop and 16 px on phones, limited to two/three lines. Cards
  use warm off-white (`#fff9ed`) or lighter slate (`#283b44`), the existing paper
  grain in an isolated layer above the background, a subtle shadow and bolder
  ticker chips. Card heights are 210 px on desktop and at least 154 px on phones;
  scene heights remain 360/300 px.
  The gate label sits in a centered pill and pulses when a stamp lands.
  The existing EN/中文
  switch translates claims, source labels, gate, stamps, controls and region label.
- Ink-to-paper token contrast is TRUE 6.31:1, FALSE 5.59:1, unknown 4.20:1 in
  light mode; TRUE 7.14:1, FALSE 5.08:1, unknown 7.15:1 in dark mode. Automated
  tests calculate all six ratios against the actual paper tokens (required ≥3:1).

## Deterministic QA

After site data loads, `window.__stampScene.seek(seconds)` pauses playback and
renders that exact timeline position. It returns the normalized time within the
measured loop (18 seconds at 1280 px, 25.992 seconds at 375 px). Time zero places
the first AMZN card off-screen left; scanning starts at 2.6 seconds and stamp
contact occurs at the centered gate at 3 seconds. Subsequent crossings use the
width-dependent interval above. Ordinary playback starts at 3 seconds to show a
check immediately. Seek normalization uses the measured spacing as well.

Open `site/?stamp-t=12.5` (or append `?stamp-t=12.5` to the existing site URL) to
start paused at 12.5 seconds. The query parameter uses the same seek function.
Invalid/negative/empty query values are ignored; invalid console arguments throw
`RangeError`. The Play animation button resumes from the sought time. Visibility,
language and size changes preserve the paused state. Inspect the reported NVDA
FY2024 card (`data-card-id="demo-thread-baseten-2"`, fourth in the loop) using
the same measured interval as the animation:

```js
const scene = document.querySelector('#stamp-scene');
const cardWidth = document.querySelector('.stamp-static-item .stamp-card').getBoundingClientRect().width;
const travel = 6000;
const crossing = travel / 2;
const scanDuration = 300;
const evidenceDuration = 100;
const impactOvershoot = 105;
const inkSettled = 300;
const interval = Math.max(matchMedia('(max-width: 639px)').matches ? 2500 : 2000,
  Math.ceil(travel * (cardWidth + 24) / (scene.clientWidth + cardWidth)));
const loop = document.querySelectorAll('#stamp-track > .stamp-carrier').length * interval;
const seekAge = (age) => window.__stampScene.seek((3 * interval + age) / 1000);

seekAge(crossing - scanDuration - evidenceDuration - 25); // Before scanning: no stamp/evidence.
seekAge(crossing + impactOvershoot);                     // Visible impact and gate-pill pulse.
seekAge(crossing + inkSettled);                          // Settled TRUE stamp and SEC evidence.
seekAge(crossing + inkSettled + 1000);                   // Moving right: stamp/evidence remain.
seekAge(travel - 1);                                    // Right-edge fade: ink remains.
seekAge(loop);                                          // Recycled off-screen left: ink reset.
```

The corresponding seek times are:

| Checkpoint | 1280 px | 375 px |
| --- | --- | --- |
| Before scanning | 8.575 s | 11.239 s |
| Visible impact | 9.105 s | 11.769 s |
| Settled | 9.300 s | 11.964 s |
| Moving right | 10.300 s | 12.964 s |
| Right-edge fade | 11.999 s | 14.663 s |
| Recycled | 24.000 s | 34.656 s |

For phone/theme/language QA, use a 375 px viewport, light or dark color scheme,
and the existing EN/中文 toggle, then use the derived checkpoints above. With reduced
motion, seeking still schedules no frames and preserves the visible, fully
stamped linked list; it never enables the hidden conveyor or pulses the pill.

## Generated assets

Both images were created with the built-in image-generation tool. Exact prompts,
export settings and reuse notes: [stamps.md](../prompts/site/stamps.md).

| Asset | Dimensions | Bytes |
| --- | --- | --- |
| [stamp-ink.webp](img/stamp-ink.webp) | 1024 × 1024 | 124,168 |
| [stamp-paper.webp](img/stamp-paper.webp) | 512 × 512 | 4,766 |

Both are below 150 KB. Stamp words remain real HTML text.
Fix1 reuses both original generated files; no new artwork, prompts or downloads.

## Verification

- `.venv/bin/python docs/scripts/build_site.py --offline`: completed using stored
  reports and excerpts; no external requests.
- Fix3 stamp tests: **40 passed** in this worktree, including all nine cards' continuous
  stamp/evidence retention, stacking after age 4 seconds, right-edge exit and
  recycling, forward/backward/repeated seeks, query equivalence/validation,
  mask-load failure, pill pulse, 1280/375 px dimensions, EN/中文 and reduced motion.
  New checks sample a full measured loop at both widths (including impact shake
  and wraparound) and verify all nine cards at centered contact and visible impact.
  Card bounds stay within the scene; rotated/scaled stamp boxes stay within the
  cards at visible impact. The adapter derives scene width from page padding
  (341 px at a 375 px viewport), card sizes from CSS and timing from the production
  travel/base-interval constants and minimum-gap formula. These remain offline
  geometry checks, not browser layout verification.
- Fix1 full suite (historical): **249 passed** in 57.51 seconds in the isolated copy
  `/private/tmp/stamp-fix1-offline-1bhgqy32`, using the existing `.venv`, cached
  company facts/tickers from the main checkout and read-only Git revision
  discovery. Python socket connections and DNS resolution were disabled. The
  first isolated run passed 248 tests but lacked Git metadata needed by an
  existing manifest-provenance test; retaining revision discovery resolved it.
  No out-of-scope worktree cache or metadata files were changed.
- The JavaScript lifecycle test runs the production animation code with a small
  offline element/event adapter. It checks crossing timing, sweep, evidence pop,
  stamp overshoot/settle, cyclic position, all pause/resume paths, reduced-motion
  links, angle bounds and Chinese localization. Phone dimensions are supplied to
  the production renderer by the DOM adapter; this does not verify browser layout.
- `node --check docs/site/script.js`, frontend source lint (0 failures/warnings),
  token contrast checks and `git diff --check`: passed.
- The prior browser visual verification attempt was unavailable: automatic approval review
  rejected opening `http://127.0.0.1:8766/site/` because the origin-access gate
  declined browser network authority. No alternate browser, CDP or rendering
  workaround was used. No visual score or screenshot verification is claimed.

The existing site design guided this single-section change; no new design draw,
external images, libraries, screenshots or page-wide redesign were introduced.
The Git remote is absent from the DappGo workspace registry; discovery was
recorded as degraded and the work stayed within the brief's standalone scope.
