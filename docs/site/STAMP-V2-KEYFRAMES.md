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
respective poses, behind the stamp. Hover body/thruster assets load on the existing
scene-start path and remain unloaded under reduced motion. The static footer
separately reuses one lazily loaded Hover greeting.

Height arithmetic, including panel labels and the progress strip:

| Viewport | Height calculation | Total | Robot box |
| --- | --- | --- | --- |
| ≥1024 | 24 letterbox reserve + 24 label + 316 panels + 12 gap + 44 strip | **420 px** | 190 × 260 |
| 640–1023 | 24 letterbox reserve + 24 label + 334 panels + 10 gap + 52 strip | **444 px** | 120 × 165 |
| <640 | 24 letterbox reserve + 36 strip + 20 label + measured post maximum + 96 robot band + 20 label + measured filing maximum | **196 px + both maxima** | 100 × 88 |

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
206 px post / 214 px filing, giving a 616 px CSS fallback envelope. Synthetic
heterogeneous and fractional DOM-box fixtures verify the maximum calculation
and the one-screen 844 px envelope; actual font wrapping awaits Claude's render.
Caption heights are fixed at 46 px desktop / 60 px tablet / 64 px phone so a
caption change cannot move the cached robot origin. The stray folder tab is
removed. Desktop/tablet comparison offsets are measured so the filed value's
baseline box meets the meter center, above the accession.

The headline caps at 64 px.
Conservative header + hero top padding + two headline lines + two lede lines +
scene margin + scene envelopes are **≤714 px at 1024×768** and **≤763 px at
1440×900**, in either language. Reduced motion shows the full, linked static list instead;
its height is intentionally unconstrained so every claim and passage can be read.

EN/中文 share the strip's first three headings with How it works, which now
follows the hero directly, before A real post, checked. Post cards retain their
theme-aware ink and severity colours; filings now keep light bond paper in both
themes. Playback pauses while
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

## Polish pass — 2026-10-29

The beat times, H pose/visor/nozzle calibration, loop order, score values, verdicts,
source dates and spotlight constants above are preserved. The height table now
includes the existing two 12 px letterbox reserves; this corrects its previous
arithmetic, without increasing the actual stage. The offline envelope measures
713.40 px at 1024×768 and 762.78 px at 1440×900 for header + headline + lede + stage.
These remain conservative geometry checks, not browser font measurements.

The post formats now follow `source_kind`: microblog threads, rounded community
posts, a fictional newspaper and an embedded original for reposts. Avatars use
existing 256 px exports at 48 px (40 px below 640). Thread positions come from
numbered entries in each saved post, not the extraction count: the big-tech
forecast remains 5/5 even though six claims were extracted. Fictional activity
counts are stored in `site.json` and explicitly labelled as example activity.
The article's headline and lead use its saved claim text; its two decorative
finance illustrations switch from revenue to ledger at Compare/React, from the
same scene phase. Reduced motion displays both illustrations in the static card.

Filings are warm bond paper in both themes (`#fff9ed` / `#e1dacb`), with two offset
sheets, contact shadow, generated grain/stack edge/paperclip, serif small-cap
commission/form headings, statement rules and dotted leaders, and a textured ink
ring around the real filed date. Accession remains the page-footer line. The
commission heading contains no seal. Filing ink, secondary text and date ink
retain at least 4.5:1 contrast including the decoded grain extremes.

Post headers, article decks, quote-card content and filing headers now have new
intrinsic positions. `measure()` reads the actual number, filing row, ledger and
comparison boxes after localization, resize, font completion and artwork load.
It caches phone maxima per width/language and aligns desktop comparisons to the
meter. No clock frame reads layout. Regression checks move target boxes before
an artwork load and confirm the light pools follow the new coordinates.

All current cards are recorded **Text** inputs. Future producers can supply
`input_kind: audio | video | screenshot` with an `input_media` object. Audio needs
an actual `timestamp`, bilingual `transcript` and normalized `[0, 1]` `waveform`
samples. Video needs an actual local `thumbnail` and timestamp; screenshots need
a thumbnail. Incomplete payloads display Text with no media strip. No sample
waveforms, frames, durations or transcripts were added to the published cards.

New artwork: **11 WebPs, 108,004 bytes**, with [exact reusable prompts and per-file
sizes](../prompts/site/polish.md) and a [hash manifest](img/polish/manifest.json).
Sections use lazy grain images; How it works has three H-reference spot scenes.
The footer reuses the existing palm-out H pose. New art was visually inspected
as processed contact sheets on ivory/navy; the page still awaits Claude's actual
browser render/review. Chromium was not run, per the brief.

The offline builder now revalidates first-filed dates from the existing
hash-checked SEC snapshots. Gap/stamp tests use temporary filing caches and
block downloads. The prompt log's retired A/C export inventory retains its exact
filenames, dimensions, byte counts and prompts as plain text where files are no
longer present, so the clean-clone link checker does not point to missing assets.

Local staging was blocked by the sandbox when Git tried to create the worktree's
`index.lock` outside the writable root. Changes remain uncommitted; nothing was
pushed. Intended logical commits: cache-independent tests/build; site polish and
art; verification/handoff documentation. Each should end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

Polish validation: `UV_OFFLINE=1 sh scripts/verify.sh` completed successfully —
**616 product/site tests**, **83 demo Python tests**, and **41 standalone Node
tests** passed. No tests were skipped. Figure regeneration/checks and all three
byte-identical data rebuilds passed. Final output:

```text
PASS offline Python and Node suites
PASS figure rebuild + --check
PASS explorer, site data and build summary: 3 byte-identical outputs
PASS Markdown links and anchors
PASS no model calls, SEC fetches or credentials; source tree unchanged
```

The source design lint has 0 failures / 0 warnings; JavaScript syntax, export
hash/budget checks and whitespace checks pass. A comparison against the previous
site snapshot confirms every pre-existing card field is unchanged except its
128 → 256 px avatar path; new publication/input metadata is additive. Figures,
recorded results, program checks and prompts used by the verifier are unchanged.

## Director review, round 1 — 2026-10-29

The [round 1 specification](STAMP-V2-DESIGN.md#10-director-review-round-1-2026-10-29)
supersedes the earlier polish's avatar sizes and phone layout. The scene timings
and verdicts are unchanged. Filing rows, fact IDs, primary URLs and ink dates now
come from the original first-filed accessions, freshly extracted from the
[complete SEC fixtures](../../tests/fixtures/sec-filings/README.md). The
[generated chronology](BUILD_SUMMARY.md#on-screen-filing-chronology) gives the
post date, displayed filing and all first-filed component accessions per card.
All component numbers still match; no comparative-column fallback is used.

Intrinsic post/paper maxima are now measured at every width, cached per width,
language and font state. The compact tablet rules extend through 1100 px.
Phone controls, paper head and repeated prose are compacted; the footer anchors
to the card bottom. Source-kind geometry regressions include deliberately tall
desktop cards and the 600 px phone envelope, both languages, twelve widths.
Avatars are 56/44 px from 256 px sources. Paper stack edges are clipped and warm
paper dimming is independent of stage atmosphere, with lit rows fully exposed.

The source design lint reports no findings; JavaScript syntax and whitespace
checks pass. The browser gate declined access to the local preview; no new
browser screenshots or browser font measurements are claimed. Geometry tests
exercise the production code with supplied intrinsic boxes.

Final round 1 verification: `UV_OFFLINE=1 sh scripts/verify.sh` passed with
**720 product/site tests**, **83 demo Python tests** and **41 standalone Node
tests**, with no skips. All 11 first-filing iXBRL/value checks, figure checks,
three byte-identical output rebuilds and Markdown links passed. Staging failed
because the sandbox could not create the parent repository's worktree
`index.lock`; the polish and review fixes remain uncommitted. Nothing was pushed.
