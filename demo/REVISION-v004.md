# Demo v004 — the three v003 review fixes

Implements `/Users/yan/note/dappgo/flow-atlas/hackathon-briefs/brief-demo-v004.md` and
`reviews-v003-ai2.md`. Worktree: `/Users/yan/git/market-claim-verifier-demo`, branch `demo/pipeline`.
All edits are within `demo/**`. No commit or push. The ten narration strings, ten cached voice keys,
music and 160.4266-second presentation timeline are unchanged.

| Fix | Result | Regression coverage |
| --- | --- | --- |
| m06 proof values | Uses the brief's authorized two-column fallback: **Three months · Sep 30**, 2023 **143,083** highlighted and 2024 **158,877**. Fixed 500/576/576 px columns, **48 px gutters**, right-aligned **128 px tabular numerals**, no numeric tracking. Amber fills the entire selected cell with matching text alignment. Nine-month values **404,824 / 450,167** remain in `motion/data.js` source data and the linked original filing. | CSS/grid geometry regression; rejection tests for overlap, 39 px gutters, overflowing text, incomplete highlight, centered values and proportional digits. Host renderer checks actual DOM/text rectangles before every frame and records results in `render.json`. |
| Subtitle synchronization | The SRT and caption compositor now use the same `cues.json` sentence alignment as motion. Long sentences subdivide by character offsets on that alignment; no motion phrase is split across SRT entries. Starts include the frame containing each onset, with matching millisecond SRT timestamps. Final captions extend through the settled motion cue, fixing m09's late “too” sample. | All **37 events** checked against the serialized SRT at `cue_start`, `cue_end` and `t + 0.3 s`, plus actual 30 fps caption lookup at each time. Dedicated Amazon, Apple, whole-year, quarter and Chinese regressions. Full narration coverage, two lines/42 characters, nonoverlap and unchanged voice keys verified. |
| Headline spaces | Shared `.headline` typography removes **−2 px tracking** and adds **0.12 em word spacing**. Existing single ASCII spaces remain intact in every shot, including “Model proposes. Program decides.” and “Same checks. In Chinese, too.” | Rendered headline markup checked across all ten shots; `. , : ?` spacing regressions; host DOM Range checks reject missing, doubled or visually collapsed punctuation spaces and horizontal overflow. |

## Prepared evidence and checks

- `out/review-v4/plan.json`: **49** review times, including the two exact Apple correction onsets.
- `out/review-v4/subtitles.srt`: complete revised **32-entry** SRT.
- `motion/{timing,cues,beats}.json`, `motion/data.js`, `motion/cue-summary.md`: regenerated from cached narration.
- **83 Python tests passed**, including the motion/layout Node suites and synthetic FFmpeg checks.
- **41 standalone Node tests passed** across motion, layout and capture suites.
- `verification-v004.json`: source hashes, prepared-artifact hashes and verification status.

Representative exported SRT intervals (seconds):

| Phrase | SRT interval |
| --- | --- |
| Amazon | 47.866–49.933 |
| Apple | 53.166–56.300 |
| That's the whole year | 56.866–58.900 |
| The quarter was 102.5 billion | 58.900–61.733 |
| It works in Chinese too | 140.033–141.766; includes the **141.7327** settled review cue |

Browser rendering remains a host check: the required existing Playwright **1.64.x** installation could not
be resolved in this execution environment. Browser policy also rejected the optional local-file preview;
that route was stopped. No new PNGs or v004 MP4 are claimed, and no historical v003 review evidence was
overwritten. The local geometry tests exercise the checks; actual font/layout measurements execute on
the host when frames render.

## Exact host commands

Use the existing pinned Python environment and an existing Playwright 1.64.x + Chromium installation:

```sh
cd /Users/yan/git/market-claim-verifier-demo
demo/.venv/bin/python -m pytest demo/tests --basetemp=demo/cache/pytest-v004 -q
node --test demo/tests/motion.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
node demo/capture/browser.mjs --version
demo/.venv/bin/python demo/build.py review-frames --out demo/out/review-v4
demo/.venv/bin/python demo/build.py keyframes --t 3 --t 65 --t 155 --out demo/out/keyframes-v4
demo/.venv/bin/python demo/build.py motiontest --shot m05 --len 2
demo/.venv/bin/python demo/build.py render
```

Review the raw/captioned proof row and both headline shots, the company/correction subtitle frames and
the late Chinese cue. The renderer fails before saving a frame if layout assertions fail. The full render
exports the next unused version (currently **demo-v004.mp4** and matching SRT), using the revised captions
and unchanged narration. No voice synthesis, dependency installation, commit or push is needed.

To refresh only the plan/SRT without Chromium:

```sh
demo/.venv/bin/python demo/build.py review-frames --prepare-only --out demo/out/review-v4
```
