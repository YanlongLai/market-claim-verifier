# Stamp v3 Hover — final keyframes

All breakpoints use the same deterministic clock. Append `?stamp-t=<seconds>`
to `docs/site/`, or call `window.__stampScene.seek(seconds)`. Seeking pauses
playback. The eleven-card loop takes **82.8 s**: nine checkable slots of **8.0 s**
and two CAN'T CHECK slots of **5.4 s**. Apple Q4 is the second card, starting at
**8.0 s**. No dates, personas, claim data or Example post tags have changed.

| Frame | Seek (desktop, tablet and phone) | Expected content |
| --- | --- | --- |
| Read | **9.05 s** — `?stamp-t=9.05` | Inspect facing the post; scan and $416.2B glow; “Reading the post…”; filing box waiting; step 1. |
| Reach | **9.80 s** — `?stamp-t=9.80` | Reach facing the filing; “Opening the 10-K…” from the actual form; SEC header reveals; step 2. |
| Search | **10.55 s** — `?stamp-t=10.55` | A wide cone from the moving visor sweeps the dimmed filing rows; the post stays undimmed; step 2. |
| Find | **10.95 s** — `?stamp-t=10.95` | Point facing the filing; cone locked on Total net sales / 416,161; the value blooms, then its amber sweep begins; “Found it: 416,161”; ledger −313,695 / =102,466, derivation and accession reveal; step 2. |
| Compare | **12.10 s** — `?stamp-t=12.10` | Think facing front; two visor beams cover the post number and the filed/compare rows; clear text pools, six drifting motes, 45% shade and 12 px letterbox; “$102.5B filed vs $416.2B posted”; Severe, 0 / 100, 306% off; step 3. |
| Flash | **12.82 s** — `?stamp-t=12.82` | Both cones cut at 12.80; the 80 ms white post flash is in progress and shade is lifting; FALSE bubble; step 4. |
| Dip peak | **12.86 s** — `?stamp-t=12.86` | Body is 8 px below its floating baseline; stamp → stamp-down cross-fade is halfway; separate mint burst is 1.6× and visible below the nozzle; post impact VFX fires. |
| Strike | **12.94 s** — `?stamp-t=12.94` | Stamp-down facing the post; FALSE stamp landing, brief shake and recovering dip; thruster remains in its 250 ms burst; the flash has ended; filing stays in its fixed box; step 4. |
| Recoil settled | **13.05 s** — `?stamp-t=13.05` | Dip has recovered; thruster switches back to its six-frame loop exactly at 250 ms; stamp-down holds and the normal continuous float continues. |
| React | **13.60 s** — `?stamp-t=13.60` | Concern pose; FALSE bubble, Severe and both panels held for reading; letterbox has eased out; step 4. |

Relative checkable beats (milliseconds): Enter 0–700, Read 700–1500, Reach
1500–2300, Find 2300–3700, Compare 3700–4500, Wind-up 4500–4800, Strike
4800–5300, React 5300–6400, Exit 6400–7200, rest 7200–8000. Each pose changes
with a **120 ms** cross-fade. Ledger rows reveal 200 ms apart. The character has
±4 px continuous bob over approximately 1.6 s, up to 3° lean toward the active
panel, and an 8 px downward strike dip (60 ms down, 160 ms recovery). There are
52 float cycles per scene loop, giving a seamless 1592.31 ms period. A separate
floor ellipse stays in place and shrinks as the robot floats upward.

The first CAN'T CHECK card starts at **16.0 s**: Read at 16.7, shrug and
“Opinion / forecast — no filed number” at 17.5, grey stamp at 19.0, exit at 20.6,
next card at 21.4. The permanent filing panel shows “No SEC number to check”,
“Filings report results, not opinions or forecasts.” and the actual Opinion /
Forecast label. The bubble says “Opinion — not in any filing” (or Forecast).
Steps 2 and 3 are dimmed and struck through throughout this card; step 1 stays
active until the grey stamp activates step 4. No passage, score or light is
shown for this claim. The second CAN'T CHECK
slot starts at 45.4 s. The article starts at 66.8 s; the repost starts at 74.8 s.

The Hover artwork is requested at `img/auditor/H/<pose>.webp`. Missing reach and
point fall back to present; think to inspect; stamp-down to stamp; approve,
concern and shrug to idle. The beat, facing and cross-fade remain correct while
fallback artwork is used. Archived B assets remain on disk and are never
requested by the page. All eleven bodies use one 0.5× scale on a 704×744 canvas,
with the shared nozzle at (352, 520). Each body has no baked jet. Six separate
`H/thruster-{0..5}.webp` frames cycle every 80 ms; `H/thruster-burst.webp` replaces
them at 1.6× scale during [strike, strike + 250 ms). Its 160×160 canvas attaches
at (80, 20). The outgoing and incoming jets cross-fade and mirror with their
respective poses, behind the stamp. All assets load on the existing scene-start
path and remain unloaded under reduced motion.

Height arithmetic, including panel labels and the progress strip:

| Viewport | Height calculation | Total | Robot box |
| --- | --- | --- | --- |
| ≥1024 | 24 label + 316 panels + 12 gap + 44 strip | **396 px** | 190 × 260 |
| 640–1023 | 24 label + 334 panels + 10 gap + 52 strip | **420 px** | 120 × 165 |
| <640 | 36 strip + 20 label + measured post maximum + 96 robot band + 20 label + measured filing maximum | **172 px + both maxima** | 100 × 88 |

On phones the robot sits on the left of the 96 px band, with a fixed-height
bubble to its right. Compare adds a small verdict word inside that bubble;
there is no equality badge. Cones point up to the post and down to the filing.
The strip is one 36 px row: four numbers, only the active step's visible label,
and an icon-only Pause/Play button with a localized aria-label. Next chips are
hidden on phones. Repeated upcoming tickers on larger screens include their
data-derived kind, e.g. “$NVDA opinion” / “$NVDA revenue” (also in 中文).

Both phone panel heights use the ceiling of the maximum intrinsic content
height across all cards, measured once per width/language/font completion.
Seeks, playback and observer echoes reuse those maxima. CSS fallbacks are
206 px post / 214 px filing, giving a 592 px initial envelope. Synthetic
heterogeneous and fractional DOM-box fixtures verify the maximum calculation
and the one-screen 844 px envelope; actual font wrapping awaits Claude's render.
Caption heights are fixed at 46 px desktop / 60 px tablet / 64 px phone so a
caption change cannot move the cached robot origin. The stray folder tab is
removed. Desktop/tablet comparison offsets are measured so the filed value's
baseline box meets the meter center, above the accession.

The headline caps at 64 px.
Conservative header + hero top padding + two headline lines + two lede lines +
scene margin + scene envelopes are **≤691 px at 1024×768** and **≤740 px at
1440×900**, in either language. Reduced motion shows the full, linked static list instead;
its height is intentionally unconstrained so every claim and passage can be read.

EN/中文 share the strip's first three headings with How it works, which now
follows the hero directly, before A real post, checked. Light/dark retain their
v2 paper, ink, severity colours and accessible contrast. Playback pauses while
off-screen, while the tab is hidden, when requested, and under reduced motion.

Spotlight geometry and constants (production `createStampConveyor`):

- `POSE_ANCHORS` stores image-pixel visor/nozzle anchors from `H/manifest.json`;
  `POSE_VISORS` derives normalized visor coordinates. `POSE_CANVAS = [704, 744]`
  is the unloaded fallback; each loaded image supplies its real canvas size.
  Contain-fit, CSS mirroring, the 120 ms pose blend, lean, bob and dip all feed
  the light origin. Artwork load/fallback invalidates light geometry alone.
- `measure()` caches the robot box, post number, full filed row, ledger rows and
  comparison row. Each cone is the convex hull of a 2 px visor radius and every
  target corner; its outer feather adds a 6 px skirt. The filed cone spans both
  the source row and comparison row during Compare. No frame reads layout.
- `FIND_SWEEP = 600 ms`, `FIND_LOCK = 2900 ms`, `BLOOM = 180 ms`,
  `AMBER_SWEEP = 660 ms`. The sweep searches ledger rows and returns to the
  matching filed row before the value blooms and amber traverses it.
- `DIM = 0.45` leaves 55% stage brightness. Separate SVG masks exclude padded
  text boxes from shade and exclude their exact boxes from light, preserving
  the original ink. `POOL_PAD = 6 px`; radial pool falloff adds 16 px horizontally
  and 12 px vertically. Feathering is gradient-based, with no live blur filter.
- `LETTERBOX = 12 px`, `LETTERBOX_EASE = 250 ms`, `FLASH = 80 ms`,
  `DIM_LIFT = 250 ms`; cones cut exactly on Strike, shade lifts, and bars ease
  out on React. Six seeded dust dots use `DUST_PERIOD = 2100 ms`.
- Light-theme light is warm `#ffe0a3`; dark-theme light is mint-white `#d9fff0`.
  Reduced motion disables beams, shade, motes, bars and flash.

Offline tests execute the production JavaScript against parsed shipped HTML,
check exact beat boundaries, all pose cross-fades, facing, fallbacks, fixed
filing reveals, comparison, score, stamp, seek determinism, lifecycle, i18n,
static list and CSS geometry at 320 / 375 / 390 / 639 / 640 / 768 / 1023 / 1024 /
1280 / 1440 px. Added checks cover cone corners, mirrored/blended visor origins,
swapped image canvases, both masks, sweep/lock/bloom, dust determinism, exact
flash and letterbox timing, no frame layout reads, bilingual data-only captions,
skipped steps, Next disambiguation, cached phone maxima and comparison alignment.
These are geometry envelopes, not browser font measurements.
The Hover checks also cover separate effect anchors and mirroring, actual
alpha bounds and empty exhaust corridors, the exact 250 ms burst cutoff,
8 px dip peak, shrinking stationary floor shadow, lazy loading and failure
fallbacks. `img/auditor/H/contact.png` provides all eleven composited poses on
both themes and six stamp-down/recoil samples (120–420 ms after impact, once the pose cross-fade has completed). The browser permission gate declined
the local preview; browser font/layout review remains unverified. No commit or push.

Hover calibration (image pixels before mirroring; shared 704×744 canvas):

| Pose | Bytes | Alpha bbox (exclusive right/bottom) | Visor | Nozzle |
| --- | ---: | --- | --- | --- |
| idle | 31,982 | (111, 12, 572, 527) | (415, 270) | (352, 520) |
| inspect | 35,862 | (115, 33, 632, 536) | (414, 304) | (352, 520) |
| reach | 31,928 | (128, 48, 677, 544) | (415, 300) | (352, 520) |
| present | 33,854 | (127, 42, 661, 526) | (404, 285) | (352, 520) |
| point | 32,406 | (123, 28, 652, 538) | (421, 280) | (352, 520) |
| think | 31,710 | (120, 6, 571, 536) | (416, 270) | (352, 520) |
| stamp | 32,906 | (127, 32, 687, 523) | (412, 300) | (352, 520) |
| stamp-down | 33,382 | (106, 47, 679, 525) | (417, 335) | (352, 520) |
| approve | 31,648 | (131, 27, 608, 530) | (412, 276) | (352, 520) |
| concern | 35,290 | (101, 7, 643, 541) | (412, 286) | (352, 520) |
| shrug | 33,818 | (67, 28, 636, 523) | (391, 280) | (352, 520) |

Thruster root: **(80, 20)** on a 160×160 canvas. Frame sizes in order 0–5: 2,968, 3,178, 3,346, 3,082, 3,230, 2,992 bytes; burst: **3,736 bytes**.

Runtime total: **387,318 bytes** (eleven bodies: **364,786**; seven effects: **22,532**). Contact sheet: **895,977 bytes**, 1560×1640. Contact/source/provenance files are never requested by the page.

Validation: `.venv/bin/python -m pytest -q` — **498 passed in 54.33 s** on the final exports. The site subset passed **199 tests**. `node --check docs/site/script.js` and `git diff --check` passed. All eleven archived B WebPs retain their pre-task SHA-256 hashes. No commit or push.
