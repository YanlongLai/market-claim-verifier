**Overall: FAIL.** Two-line subtitles violate the 64 px bottom edge margin.

Viewed all **143 PNGs**: 49 raw frames, 49 captioned frames and 45 subtitle panels. Inspected representative frames at 375 px wide. No files edited; no builds run. Frame references below are in [review-v4](/Users/yan/git/market-claim-verifier-demo/demo/out/review-v4). Cue judgments use `index.json` and the supplied SRT.

| 1. Product name + UI by 3 s | Verdict | Evidence |
|---|---|---|
| `m01-open` — `keyframe-02-0p300s.png`, frame 01 | PASS | At 0.300 s, “Market Claim Verifier” and the Apple claim card are visible. At 2.624 s, the card shows FALSE. |

| 2. Phone readability and edge margins | Verdict | Evidence |
|---|---|---|
| `m02-spread` — [keyframe-03-11p691s.png](/Users/yan/git/market-claim-verifier-demo/demo/out/review-v4/captioned/keyframe-03-11p691s.png); affected frames **03–16, 27–29, 34–37, 39–45** | **FAIL** | In all 28 affected frames, subtitle glyphs extend through **y=1034**, leaving only **45 px** below them. The required clearance is 64 px. |
| `m06-proof` — `keyframe-26-83p940s.png`, frames 27–28 | PASS | **143,083** and **158,877** occupy separate columns. The highlighted number remains complete and readable at phone width. |
| Remaining important content across all shots | PASS | No additional small-text, low-contrast, crowding or edge-margin failure observed at the stated readability bar. |

| 3. Bottom 200 px reserved for subtitles | Verdict | Evidence |
|---|---|---|
| All 49 raw frames | PASS | Every pixel from **y=880 through 1079** is background. Important non-subtitle content stays above the reserved region. |
| `m06-proof` — `keyframe-26-83p940s.png`; `m08-results` — `keyframe-38-128p662s.png` | PASS | The proof link and results board remain above y=880. |

| 4. Number consistency | Verdict | Evidence |
|---|---|---|
| Apple — `m01-open`, `m02-spread`, `m04-extract`, `m05-verdicts`; especially `keyframe-24-58p927s.png` | PASS | Rounded **$416B** agrees with detailed **$416.2B**. The correction distinguishes **$102.5B quarter** from **$416.2B full year**, with proportional bars and approximately **4×** comparison. |
| Amazon — `keyframe-13-32p367s.png`, `keyframe-18-48p203s.png`, `keyframe-26-83p940s.png` | PASS | **$143.1B** agrees with **143,083 USD millions** after rounding. **158,877** is separately labeled 2024, matching the revised shot list. |
| NVIDIA — `keyframe-14-33p806s.png`, `keyframe-19-51p012s.png` | PASS | **FY2024 $60.9B** and **more than double** remain consistent. |
| Evaluation — frames 08–11, 38–45 | PASS | **357 claims** throughout. Meta **44→83%**, Baseten **21→90.5%**, Fireworks **20→90.5%**. Maximum improvement: **70.5 points**. |
| Chinese example — `keyframe-46-144p208s.png`, frame 48 | PASS | **500 億 = $50.0B**; filed **$47.1B** is below that threshold, matching FALSE and the shot list. |

| 5. Picture matches narration cues | Verdict | Evidence |
|---|---|---|
| `m05-verdicts` — frames 18–25 | PASS | Amazon, NVIDIA and Apple appear at their named cues. Frames 22–23 show the full-year correction; frames 24–25 show **$102.5B** with the quarter subtitle. |
| `m02-spread`, `m06-proof`, `m07-program`, `m08-results` — frames 06–07, 27–28, 30–37, 39–45 | PASS | Coral claim, highlighted filing value, program checks/rejection, **83%**, and both **90.5%** rows match their indexed cues. |
| `m09-chinese` — `keyframe-48-141p733s.png`; remaining indexed frames | PASS | Chinese claim and comparison are visible with “It works in Chinese too.” No other cue mismatch observed. |

| 6. Visual quality | Verdict | Evidence |
|---|---|---|
| `m06-proof` — frames 26–28 | PASS | Separate numeric cells; complete highlight; no overlapping or clipped values. |
| `m07-program` — `keyframe-29-105p883s.png`; `m09-chinese` — `keyframe-46-144p208s.png` | PASS | Headlines contain the restored spaces: “Model proposes. Program decides.” and “Same checks. In Chinese, too.” |
| All reviewed frames | PASS | No additional alignment, clipping, empty-frame, font, colour or typo defect observed. Subtitle edge clearance fails criterion 2. |

| 7. Hackathon and Meta attribution | Verdict | Evidence |
|---|---|---|
| `m10-cta` — `keyframe-49-154p401s.png` | PASS | Explicitly displays “Built during the Meta Global AI Developer Hackathon” and “Muse Spark · Meta open weights.” |

Required fix, ranked:

1. **Raise two-line subtitle text by at least 19 px.** Affected shots: `m02-spread` frames 03–07; `m03-baseline` 08–11; `m04-extract` 12–16; `m06-proof` 27–28; `m07-program` 29 and 34–37; `m08-results` 39–45. Representative frame: **`keyframe-03-11p691s.png`**. Keep subtitle glyphs within **y=880–1015**, tightening vertical padding without covering content above y=880.

The three v003 fixes:

| Previous fix | Status | v004 evidence |
|---|---|---|
| Separate SEC values | **FIXED under the authorized v004 revision** | `m06-proof`, `keyframe-26-83p940s.png`, frames 27–28: revised two-column layout separates **143,083 / 158,877** and fully contains the highlight. The current shot list explicitly authorizes this two-column treatment. |
| Reconcile subtitles with narration cues | **FIXED** | `m05-verdicts`, frames 18, 20, 22, 24: subtitles identify Amazon, Apple, the full year and the corrected quarter respectively. `m09-chinese`, frame 48: Chinese subtitle remains active. |
| Restore headline spaces | **FIXED** | `m07-program`, `keyframe-29-105p883s.png`; `m09-chinese`, `keyframe-46-144p208s.png`: both requested headlines have visible word and sentence spacing. |