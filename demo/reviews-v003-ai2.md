**Overall: FAIL.** Viewed all **142 PNGs**: 49 raw frames, 49 captioned frames and 44 subtitle panels. No files edited; no builds run.

Files below were local outputs in `out/review-v3`, not included in a clean clone. See the committed [build record](BUILD_LOG.md). Frame ranges include every indexed frame in that range. Caption timing is judged against `index.json` cues.

**1. Product name + UI visible by 3 s — PASS**

| Result | Shot / frame | Evidence |
|---|---|---|
| PASS | `m01-open` — `keyframe-02-0p300s.png`, frame 01 | At 0.300 s, “Market Claim Verifier” and the Apple claim card are visible. At 2.624 s, the card shows FALSE. |

**2. Phone readability and 64 px edge margin — FAIL**

Applied the stated 56 px text / 96 px number bar visually and inspected representative captioned frames at 375 px wide.

| Result | Shot / frame | Evidence |
|---|---|---|
| FAIL | `m06-proof` — `captioned/keyframe-26-83p940s.png`, frames 27–28 | **143,083 / 158,877 / 404,824 / 450,167** collide across column boundaries. The final digit of the highlighted value meets the next value. At phone width, the row resembles one continuous number string. Large type has not produced readable cells. |
| PASS | Frames 01–25 and 29–49 | No additional phone-readability failure observed at the brief’s minimum. Examples: frame 17 separates Apple’s quarter/year amounts; frame 38 separates providers and percentages; frame 49 keeps the URL and attribution readable. |
| PASS | All 49 full-frame pairs | The top, left and right 64 px bands contain only background. No important content enters those edge margins. |

**3. Bottom 200 px reserved for subtitles — PASS**

| Result | Shot / frame | Evidence |
|---|---|---|
| PASS | All 49 raw frames | Every pixel from **y=880 through 1079** is background. Captioned versions use that region for subtitles. |
| PASS | `m03-baseline` — frames 08–11; `m06-proof` — frame 26; `m08-results` — frame 38 | Baseline content ends at y=849. The proof link/underline ends at y=876; the results board ends at y=875. None enters the reserved region. |

**4. Number consistency — PASS**

| Result | Shot / frame | Evidence |
|---|---|---|
| PASS | `m01-open`, `m02-spread`, `m04-extract`, `m05-verdicts` — especially `keyframe-17-58p793s.png` | Opening **$416B** is rounded. Detailed frames consistently identify the erroneous quarter claim as **$416.2B**, the actual quarter as **$102.5B**, and the full year as **$416.2B**, with an approximately **4×** comparison. |
| PASS | `m02-spread`, `m04-extract`, `m05-verdicts`, `m06-proof` — frames 03, 13, 18, 26–28 | Amazon’s **$143.1B** agrees with **143,083 USD millions** after rounding. All four proof-row values match the shot list, despite their overlap. |
| PASS | `m04-extract`, `m05-verdicts` — frames 14, 19 | NVIDIA’s **FY2024 $60.9B** claim and **more than 2×** verdict are consistent. |
| PASS | `m03-baseline`, `m08-results` — frames 08–11, 38–45 | **357 claims** throughout. Fireworks **20→90.5%**, Baseten **21→90.5%**, Meta **44→83%**. Maximum improvement is **70.5 percentage points**. |
| PASS | `m09-chinese` — frames 46–48 | **500 億 = $50.0B**; filed revenue **$47.1B** is below that threshold. This agrees with the revised shot list. |

**5. Picture matches narration cue — FAIL for caption/cue synchronization**

| Result | Shot / frame | Evidence |
|---|---|---|
| PASS | `m02-spread` — `keyframe-06-9p193s.png`; `m05-verdicts` — frame 20; `m08-results` — frames 39–45 | The erroneous **$416B** appears at “quietly wrong”; Apple appears at “Apple”; **83%** and both **90.5%** rows appear at their indexed cues. |
| PASS | `m05-verdicts` — frames 21–25; `m06-proof` — frames 27–28; `m07-program` — frames 30–37; `m09-chinese` — frame 47 | Apple’s correction is already visible at the correction cues. The proof highlight/link, program-check stages, rejected E9 and Chinese conversion match their indexed cues. |
| FAIL | `m05-verdicts` — `keyframe-18-48p203s.png`, `keyframe-20-53p381s.png` | At the indexed **“Amazon”** cue, the subtitle still says “An agent looks up SEC data…” until **48.825 s**, about **622 ms** later. At **“Apple”**, the subtitle still names NVIDIA until **53.463 s**. |
| FAIL | `m05-verdicts` — `keyframe-22-56p887s.png`, `keyframe-24-58p927s.png` | These are explicitly marked **spoken-cue-start** samples. “That’s the whole year” still carries the Apple/false subtitle until **57.070 s**. “The quarter was 102.5 billion” still carries the whole-year subtitle until **59.131 s**. |
| FAIL | `m09-chinese` — `keyframe-48-141p733s.png` | The indexed cue is **“too”**, but no subtitle is present: its SRT interval ended at **141.640 s**, about **93 ms** earlier. |

**6. Visual quality — FAIL**

| Result | Shot / frame | Evidence |
|---|---|---|
| FAIL | `m06-proof` — `keyframe-26-83p940s.png`, frames 27–28 | Adjacent financial values overlap. The highlight ends before the full visual footprint of **143,083**, compromising the exact-number demonstration. |
| FAIL | `m07-program` — `keyframe-29-105p883s.png`, frames 30–37 | The headline visually reads **“Model proposes.Program decides.”** There is no normal space after the period. |
| FAIL | `m09-chinese` — `keyframe-46-144p208s.png`, frames 47–48 | The headline visually reads **“Same checks.In Chinese,too.”** Missing spacing after both punctuation marks remains visible at full resolution and phone width. |
| PASS | Remaining inspected layouts | No completely empty frames observed. Apostrophes and quarter/year spacing in the extraction quotes are decoded and separated. Apple no longer covers NVIDIA; the results badge stays inside its box. |

**7. Explicit hackathon + Meta-model attribution — PASS**

| Result | Shot / frame | Evidence |
|---|---|---|
| PASS | `m10-cta` — `keyframe-49-154p401s.png` | Displays **“Built during the Meta Global AI Developer Hackathon”** and **“Muse Spark · Meta open weights.”** The displayed URL matches the shot list, and the QR decodes to that same URL. |

Fixes, in priority order:

1. **Separate the SEC values.** `m06-proof`, `keyframe-26-83p940s.png` and frames 27–28: retain all four values and their headings, but provide real spacing between cells. Use a condensed numeric face or redistribute column widths while preserving numbers at ≥96 px. Keep the complete highlighted **143,083** inside its own cell.

2. **Reconcile subtitles with the narration cues.** `m05-verdicts`, `keyframe-18-48p203s.png`, `keyframe-20-53p381s.png`, `keyframe-22-56p887s.png`, `keyframe-24-58p927s.png`; `m09-chinese`, `keyframe-48-141p733s.png`: align SRT boundaries and index cues against the narration, then regenerate captioned evidence. The active subtitle must identify the company or correction being spoken.

3. **Restore headline spaces.** `m07-program`, `keyframe-29-105p883s.png`; `m09-chinese`, `keyframe-46-144p208s.png`: render **“Model proposes. Program decides.”** and **“Same checks. In Chinese, too.”** Apply this across their shots.

The ten v002 fixes:

| # | Previous fix | Status | v003 evidence |
|---|---|---|---|
| 1 | Show Apple’s correction explicitly | **FIXED** | `m05-verdicts`, frame 17 and correction-cue frames 21–25: **$102.5B quarter**, **$416.2B year**, proportional bars and **4×** explanation; both TRUE cards remain visible. |
| 2 | Reflow for phone readability | **NOT FIXED** | `m06-proof`, `keyframe-26-83p940s.png`, frames 27–28: the four numbers remain crowded and overlap at phone width. |
| 3 | Fix results/spread cue timing | **FIXED** | `m02-spread`, frames 06–07: coral **$416B** at “quietly wrong.” `m08-results`, frames 41–45: both **90.5%** rows at that cue. Subtitle timing is a separate remaining failure. |
| 4 | Repair escaped text and spacing | **NOT FIXED** | Apostrophes and **Q3 2023 / Q4 2025** spacing are repaired in frames 03, 13–15. `m09-chinese`, frames 46–48, still shows **“checks.In”** and **“Chinese,too.”** |
| 5 | Keep proof table inside viewport | **FIXED** | `m06-proof`, frames 26–28: “Total net sales” and the complete rightmost **450,167** are inside the viewport. Inter-cell overlap remains a different failure. |
| 6 | Explicit closing claim and reconciled CTA | **FIXED** | `m10-cta`, frame 49: explicit hackathon line, model credits, displayed `/market-claim-verifier/site/` URL and decoded QR all agree with the revised shot list. |
| 7 | Correct results badge | **FIXED** | `m08-results`, frame 38 and frames 41–45: **“Up to +70.5 points”** is contained within the badge. |
| 8 | Move baseline footnote upward | **FIXED** | `m03-baseline`, frames 08–11: all content ends by **y=849**, above y=880. |
| 9 | Explain Chinese FALSE verdict | **FIXED** | `m09-chinese`, frames 46 and 48: the revised threshold claim separates the correct **500 億 = $50.0B** conversion from **Filed: $47.1B — FALSE**. |
| 10 | Supply matching subtitle evidence | **FIXED** | The 26-cue `demo-v003.srt` matches the evidence hash and review-directory SRT. Captioned frames and 44 subtitle-panel PNGs are supplied. SRT entries contain at most two lines and 41 characters per line; synchronization defects are listed above. |
