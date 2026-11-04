# Demo v003 — review fixes and host handoff

Implemented the supplied `/Users/yan/note/dappgo/flow-atlas/hackathon-briefs/brief-demo-v003.md`
in `demo/**` on `demo/pipeline`. No commit/push. All ten narration lines, cached voice keys and scene
starts match v002; **no new voice clips are required**. Prepared duration: **160.4266 s**.

Source/tests/subtitle preparation are complete. Claude renders and re-reviews the new picture on the
host, as the brief specifies. This report does not assert a rendered v003 MP4 or a visual review pass.

## All ten AI2 fixes

| AI2 | What changed | Verification / evidence |
| --- | --- | --- |
| 1 · Apple correction | At FALSE, switch immediately to a complete Apple comparison in a separate right column. Keep Amazon/NVIDIA TRUE visible at left. Both proportional bars, $102.5B quarter, $416.2B full year and “4× too high · that's the full year” remain visible throughout the eight-second push. | Node regression samples all m05 positions at 30 fps for overlap/safe bounds, and checks full detail at both correction onsets, both cue+0.3 s frames and t=65. |
| 2 · Phone readability | Meaningful text ≥56 px; default body 64 px; extraction/Chinese quotes and result providers 72 px. Highlighted numbers / financial data ≥96 px. Remove extra copy/share arrows; show one large exact quote at a time. Program board is 66.7% and results board 62.3% of the safe area. Captions are 56 px. | Type/contrast and board geometry tests; host picture/phone review still required. |
| 3 · Cue timing | m02 coral $416B appears on “some are quietly wrong”; both m08 90.5% rows appear on “90.5 percent”, along with their provider labels. Meta appears on “83 percent”. Results show their correct values immediately while bars grow. | Cue/visibility regressions; review samples at 9.1932 s and 125.4555 s. |
| 4 · Escaping / spacing | Decode entities once at product-data load. Highlight numbers in plain decoded text before escaping output; skip literal entity tokens. Keep Q3 2023 / Q4 2025 in single spaced tokens; reduce headline tracking. | Python once-only decoding test, Node apostrophe/entity/injection/exact-quote/period tests. |
| 5 · Filing viewport | Keep all four original numeric cells and row label inside a fixed padded table; highlight the target without zooming the table out of view. Labels ≥56 px, cell values 96 px. | Source-value and fixed-table regressions; host review includes late m06 midpoint 83.9402 s. |
| 6 · Closing claim / CTA | Explicit 56 px “Built during the Meta Global AI Developer Hackathon”; retain Muse Spark / Meta open weights and GitHub star CTA. Shot list and QR use the correct live `/market-claim-verifier/site/` destination. | CTA regression and independent decoding of unchanged QR. |
| 7 · Gain badge | Contained single-line “Up to +70.5 points”, derived from the displayed differences 39 / 69.5 / 70.5. Larger 724×136 container; +70.5 is 96 px. | Maximum-gain calculation and containment regression. |
| 8 · Baseline subtitle clearance | Bounded 1.02× chart push; provider labels clear the note; note ends at y=866, with 14 px clearance before the subtitle strip. Claim count is 96 px. | Maximum-zoom bounds and label/note separation regression. |
| 9 · Explain Chinese FALSE | Replace the disputed Meta rounding example with report claim 3, Coca-Cola. Claim: 「可口可樂 2024 年營收突破 500 億美元。」 Show 500 億 = $50.0B, then coral Filed: $47.1B and FALSE. Filed $47.061B (=470.6 億) is below the threshold. | Python source/check/evidence assertions and Node conversion/filed/verdict test. |
| 10 · Subtitle evidence | Reconstruct the full matching v002 SRT using its exact narration, voice keys and recorded scene timing. Extract all 45 actual captioned frames from its existing MP4. Prepare full SRT for the 49-frame v003 plan; the host review command automatically creates raw/captioned pairs with validated receipts. | `out/demo-v002.srt`, `out/demo-v002-subtitle-evidence.json`, `out/review-v2-captioned/{index,evidence}.json`; `out/review-v3/{plan.json,subtitles.srt}`. Caption placement/boundary, full narration coverage and review-index tests. |

## Director notes A–G

| Note | Implementation |
| --- | --- |
| A | Once-only decoding in `motion_data.py`; safe tokenisation/escaping and spaced quarter tokens in `motion/logic.js`. Dedicated Python + Node regressions cover apostrophes, entities, exact quotes and Q3 2023 / Q4 2025. |
| B | m09 uses Coca-Cola / KO / report claim 3 and the filed $47.061B comparison. Conversion and FALSE are separate reveals. Narration remains exactly “It works in Chinese too.” |
| C | m07 and m08 occupy 66.7% / 62.3% of the safe area; fewer words in larger nodes/rows. Badge reads exactly “Up to +70.5 points” inside its box. |
| D | Meaningful scene text and captions ≥56 px; primary bodies 64–72 px; financial/highlighted numbers ≥96 px. Nonessential words/decorations removed. |
| E | Fully populated correction appears at FALSE, before both correction phrases. The Apple panel stays separate from NVIDIA for every sampled frame. Added exact onset and settled review times listed below. |
| F | Exact hackathon line at 56 px, with model credits. Correct live URL preserved in storyboard, displayed path, unchanged QR and updated `SHOTLIST-v2.md`. |
| G | Coral $416B follows “quietly wrong”; both Baseten/Fireworks 90.5% rows follow “90.5 percent”. Cue-specific review samples and regressions added. |

## New correction review times

Times are absolute video seconds from the cached narration alignment. Character-offset alignment remains
an estimate; the full Apple comparison is already visible from the FALSE beat at **56.4477 s**.

| Cue | Exact phrase onset | Beat | Settled review frame |
| --- | ---: | ---: | ---: |
| That's the whole year | 56.887282540 | 56.9585 | 57.2585 |
| The quarter was 102.5 billion | 58.926647619 | 58.8626 | 59.1626 |
| some are quietly wrong | 8.770998969 | 8.8932 | 9.1932 |
| 90.5 percent | 125.007278689 | 125.1555 | 125.4555 |

`motion/cue-summary.md` records all 37 events; `out/review-v3/plan.json` contains 10 midpoints,
37 event+0.3 s frames, and the two exact Apple correction onsets: **49 stills**.

## Checks and host commands

Local checks (no Chromium or model synthesis):

```sh
demo/.venv/bin/python -m pytest -q demo/tests
node --test demo/tests/motion.test.mjs demo/tests/capture.test.mjs
demo/.venv/bin/python demo/build.py review-frames --prepare-only
```

Results: **76 Python tests passed; 25 standalone Node tests passed** (21 motion, 4 capture).
Logs: `cache/v003-pytest.log`, `cache/v003-node-tests.log`. The Python suite also invokes the motion Node
suite and real synthetic FFmpeg caption/audio checks. Existing v002 narration/timing and source evidence
remain the inputs; synthetic test media is never substituted into the demo.

Run from `/Users/yan/git/market-claim-verifier-demo` on the host:

```sh
demo/.venv/bin/python demo/build.py review-frames --out demo/out/review-v3
demo/.venv/bin/python demo/build.py keyframes --t 3 --t 65 --t 155 --out demo/out/keyframes-v3
```

Review `review-v3/index.json` and both raw/captioned PNG sets, particularly the correction onsets, all four
filing values, phone readability, subtitle clearance and both 90.5% rows. Then use the existing host
motion-test/render workflow. The next successful full export will be `demo-v003.mp4` with matching SRT;
this task leaves that render/re-review to Claude per the brief.
