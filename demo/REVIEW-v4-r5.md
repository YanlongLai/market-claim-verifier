# v4 round 5 — remaining AI2 findings

Source and terminal delivery based on `ceea7413` on `demo/v4`. The cut remains
**0, 9, 22, 34, 50, 66, 124, 148, 164, 178 s**, in the same beat order.
The r4 hero, five-card cascade, closing hold and URL remain. Existing v3 outputs,
voice cache, live takes, terminal takes and saved evidence are preserved.

## Changes

- **B1:** The recorder clicks the native `Agent trace (N steps)` summary, asserts
  its `<details>` is open, returns to the native model ID, and frames every actual
  `tool_call` and program `verdict` for 700 ms each. It checks both DOM visibility
  and the crop-safe viewport. Receipts retain the open state and shown event indices.
  It then opens the derived Apple evidence row's **Inspect data**, shows the actual
  `FY2025 - 9M YTD` derivation/annual component for 2 s and the nine-month component
  for another 2 s. Arithmetic is checked against the native JSON.
  The gate requires completion within 56 s after submission and within the first
  56 s of the 58 s scene. Earlier holds are verdict **2 s**, draft **3 s**, evidence
  **2 s**. Long scrolls take at most 450 ms plus settling. Each paid attempt remains
  a single request, with no automatic retry.
- **M1:** Capture is 1920×1080, CSS zoom **1.6**, with the 800-CSS-px form/result
  column centred. Active elements sit in the upper middle of the crop. Body/code/
  citation text uses 36 CSS px: **36 × 1.6 × 1.4 / 4 = 20.16 px** at 480 width.
  D4 retains its uniform **1.4×** crop, now centred on the centred column in both
  axes. The closing hold checks the corrected edit and both component filing links
  fit above captions; it prefers the draft span and falls back to its native edit
  row when intervening scope text makes that span too tall. It never ends at the
  footer. New terminal clips live alongside prior clips under
  `assets/terminal-v4-r5/`: labels **56 px**, principal ratios/median/projection
  **96 px**. They rasterize literal events from a real zsh PTY recording, with
  cast hashes, row fonts and source hashes in each receipt. Supporting results
  labels are also 56 px.
- **M2:** v406 uses the requested number-free narration. Its four `cue_events`
  carry the complete text groups and exact scene onsets: **0**, **verdict − 1**,
  **verdict + 2**, **draft reveal**, derived from the wired receipt's
  `timings[].at_s`. Re-recording rewires them automatically. Numeric-copy gates
  now require genuine finite measurements, without targeting an unrelated cost
  or latency. Older takes fail the new r5 choreography gate. No site copy changed.
- **M3:** The mixer places four contiguous source spans of the new v406 voice on
  that receipt clock; captions use the same translation. Speech is neither sped
  up nor omitted. The scale panel starts at scene **6 s**, its last keystroke at
  **6.78 s**, ahead of the retained scale sentence at **8.6 s**, and stays through
  both scale sentences. Beat 4 introduces tools at scene 4 s. Input pictures are
  explicitly locked to **0–3.5 / 3.5–7 / 7–10.5 / 10.5–12 s** for screenshot /
  PDF / podcast / video. Host keyframes include every recorded trace/filing reveal.
- **N3:** High-contrast footers distinguish **Saved Threads run · Nov 3**,
  **Frozen media run · Oct 30**, and the **Oct 27** evaluation. They finish above
  y=880, before the reserved caption zone. The terminal frame extractor now uses
  the correct film starts, 34 s and 124 s, and a separate r5 output directory.
- **N4:** `November 4.` and `run.` are reflowed into the preceding caption line,
  with at most **2 × 42** characters in both review and rendered captions.
- **N5:** Beat 7 contains only its terminal replay. The Wan insert and its player
  path are removed; its existing assets/attempt receipts remain untouched.

## Host commands

Run from the repository root. Re-record before measured voice preparation so the
four cue budgets use the new take's actual reveal times. The password file must
already be configured privately; never paste its contents into a command.

```sh
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
export UV_CACHE_DIR=/private/tmp/mcv-v4-r5-uv-cache
uv run --project demo python demo/record_v4.py --site-ref main --port 8765
uv run --project demo python demo/build.py voice --storyboard demo/storyboard-v4.yaml --only v406
uv run --project demo python demo/motion_v4.py
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v4.yaml --out demo/out/review-v4-r5
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v4.yaml --out demo/out/keyframes-v4-r5
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v4.yaml
```

No synthesis, new live request or full film render was performed for this delivery.
The Chromium preflight failed before any live call; see the retained
[preflight result](prep/v4/r5/browser-preflight.log). The generated v4 data/SRT are
explicitly unmeasured source previews, not new film evidence.

The requested tool-sentence and verdict onsets are only **3 s apart**. The voice
preparation gate rejects a span that exceeds that window, overlaps the next cue,
or runs past the scene. The existing wired take also leaves less than 1 s between
the requested verdict cue and draft reveal; only the new host take can establish
that budget. A failed timing gate retains the voice take and requires resolving
the cue budget; it must not be bypassed by mixing overlapping speech or shortening
the recording. Pauses are scheduled audio gaps, not spoken `[pause]` tags.

## Retained verification

- [31 focused Python checks](prep/v4/r5/focused-python-keyframes.log), including
  actual FFmpeg mixing of synthetic WAV spans at four separate onsets.
- [12 focused Node checks](prep/v4/r5/focused-node-final.log), including the
  closed-trace regression, tool coverage, crop floor and input-picture intervals.
- [237 demo tests](prep/v4/r5/all-demo-final.log) and
  [109 standalone Node tests](prep/v4/r5/all-node-final.log) pass. The initial
  broader run caught a legacy mixer argument change; the final implementation
  preserves the original arguments for unsegmented v3 clips.
- [Terminal frame extraction](prep/v4/r5/terminal-frames.log): 40 exact 1 fps
  frames; 1920×1080, 30 fps, 16/24 s. Actual 480 px reductions were inspected in
  [this contact sheet](prep/v4/r5/visuals/terminal-480-sheet.png).
- [Compiler preview](prep/v4/r5/motion-keyframes-final.log).
- [Final offline verification log](prep/v4/r5/offline-verification-final.log)
  passes with `UV_OFFLINE=1`: **1,269 product tests, 237 demo tests, 109 Node
  tests**, figure checks, byte-identical data rebuilds and source links. The
  [earlier failed attempt](prep/v4/r5/offline-verification.log) is retained.
- [Isolated delivery checkout](prep/v4/r5/bundle-demo-tests.log): the same **237
  demo tests pass** with the initial unrelated worktree changes excluded.
- [Preservation audit](prep/v4/r5/preservation.json): **276/276** protected files
  unchanged. A direct working-tree Markdown scan also traverses the ignored AI2
  review and rejects its existing absolute link outside the repository; that
  [attempt is retained](prep/v4/r5/links.log). The official disposable verifier
  omits ignored `demo/out/` and checks the deliverable source links.

The initial baseline, failed/partial terminal render, intermediate test failure
and later results are retained under `prep/v4/r5/` and the new terminal directory.
They are offline rechecks and do not retest OCR/ASR.

The delivery commit carries:

```text
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```
