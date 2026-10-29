**Overall: FAIL on the supplied evidence.** Viewed all 45 PNGs. Shot-level findings below apply to every supplied frame in that shot unless a specific frame is identified.

All frame files were local outputs in `out/review-v2`, not included in a clean clone. See the committed [build record](BUILD_LOG.md).

**1. Product name + UI visible by 3 seconds — PASS**

| Result | Shot / frame | Evidence |
|---|---|---|
| PASS | `m01-open` — `keyframe-02-0p300s.png`, `keyframe-01-2p624s.png` | Product name and Apple claim card are visible at 0.300 s. The card shows FALSE by 2.624 s. |

**2. Mobile readability — FAIL**

At 375 px wide, the frame scales to 19.53%: 44 px source text becomes 8.6 px. Essential supporting text throughout these frames is approximately that size.

| Result | Shot / representative frame | Evidence |
|---|---|---|
| FAIL | `m01-open` — `keyframe-01-2p624s.png` | Apple’s question and the supporting sentence become roughly 10–11 px text. |
| FAIL | `m02-spread` — `keyframe-03-11p691s.png` | The sentence connecting Amazon’s revenue to its reporting period becomes tiny; large numbers alone lose that context. |
| FAIL | `m03-baseline` — `keyframe-11-27p212s.png` | Provider names and “Muse Spark from memory · 357 finance claims” become roughly 8–9 px. |
| FAIL | `m04-extract` — `keyframe-13-32p367s.png` | Exact quotes, company labels and extraction status are too small. Enlarged numeric fragments crowd the surrounding sentence. |
| FAIL | `m05-verdicts` — `keyframe-20-53p381s.png` | Quarter/year labels become tiny. These labels are essential to understanding Apple’s error. |
| FAIL | `m06-proof` — `keyframe-23-78p412s.png` | Period headings, “USD in millions,” and the original-filing link become roughly 8–9 px. |
| FAIL | `m07-program` — `keyframe-25-105p883s.png` | Most check descriptions become roughly 8–9 px; the complete diagram is too dense at phone width. |
| FAIL | `m08-results` — `keyframe-34-128p662s.png` | Provider names, column headings and evaluation context become tiny, despite readable percentages. |
| FAIL | `m09-chinese` — `keyframe-42-144p208s.png` | The Chinese claim and explanatory text become roughly 9–10 px. |
| FAIL | `m10-cta` — `keyframe-45-154p401s.png` | The demo URL is small; repository URL and build/model attribution become roughly 8–9 px. |

Pixel checks found no content inside the left or right 64 px margins.

**3. Bottom 200 px reserved for subtitles — FAIL**

| Result | Shot / frames | Evidence |
|---|---|---|
| FAIL | `m03-baseline` — `keyframe-08-24p636s.png`, `keyframe-09-26p794s.png`, `keyframe-10-26p794s.png`, `keyframe-11-27p212s.png` | Footnote descenders enter the reserved strip at **y=880–881**. In frame 11, the offending pixels span x=206–532. |
| PASS | Other 41 PNGs | Pixel checks found no non-background pixels at y≥880. |

**4. Number consistency — FAIL on gain-label precision**

| Result | Shot / frames | Evidence |
|---|---|---|
| PASS | `m02-spread`, `m05-verdicts`, `m06-proof` — frames 03, 18, 23 | Amazon’s $143.1B agrees with **143,083 USD millions**, rounded to one decimal billion. |
| PASS | `m01-open`, `m04-extract`, `m05-verdicts` — frames 01, 15, 20 | Apple’s $416B is consistent with rounded $416.2B; the quarterly claim is marked FALSE. The required $102.5B correction is not demonstrated by these samples. |
| PASS | `m04-extract`, `m05-verdicts` — frames 14, 19 | NVIDIA’s $60.9B and “more than double” agree with the later >2× verdict. |
| PASS | `m03-baseline`, `m08-results` — frames 11, 34 | Meta: 44→83%; Baseten: 21→90.5%; Fireworks: 20→90.5%. Both shots use 357 claims. These agree with the shot list. |
| PASS | `m09-chinese` — `keyframe-42-144p208s.png` | 623 億 converts to $62.3B. |
| FAIL | `m08-results` — `keyframe-34-128p662s.png` | The unqualified **“+70 points”** badge is imprecise: displayed gains are **39, 69.5 and 70.5 percentage points**. The shot list repeats this imprecise badge. |

**5. Picture matches narration cue — FAIL**

| Result | Shot / frame | Evidence |
|---|---|---|
| FAIL | `m02-spread` — `keyframe-05-9p193s.png` | At “some are quietly wrong,” only $143.1B and 2× are visible, both green and later treated as true. The erroneous $416B appears in frame 06 and turns coral only in frame 07 at 12.491 s. |
| FAIL | `m08-results` — `keyframe-41-125p456s.png` | At **“90.5 percent,”** only the Meta row with **83%** is visible. Neither 90.5% row is on screen. |
| PASS | `m05-verdicts` — frames 18–21 | Amazon, NVIDIA, Apple and “false” cues have the corresponding company/verdict visible. |
| FAIL — coverage | `m05-verdicts` — `keyframe-17-58p793s.png` and all other supplied m05 frames | None shows the planned **$102.5B quarter versus $416.2B full-year comparison**, or its 4× explanation. That part of the narration cannot pass from this review set. |
| PASS | `m01-open`, `m03-baseline`, `m04-extract` — frames 02, 09–11, 13–16 | Title, baseline values, exact-quote extraction and “not judged” imagery match their indexed cues. |
| PASS | `m06-proof`, `m07-program`, `m09-chinese` — frames 23–24, 26–33, 43–44 | Highlight/link, program-check stages, rejected E9, Chinese conversion and verdict match their indexed cues. |

Entries labelled only “midpoint” establish scene context; they do not establish synchronization with a particular spoken phrase.

**6. Visual quality — FAIL**

| Result | Shot / frame | Evidence |
|---|---|---|
| FAIL | `m02-spread` — `keyframe-03-11p691s.png`; `m04-extract` — frames 13–14 | Literal **`&#39;`** appears in Amazon’s and NVIDIA’s names. Its **39** is enlarged like a financial number. |
| FAIL | `m04-extract` — frames 13, 15 | Period tokens visually run together as **Q32023 / Q42025**, weakening the exact-quote demonstration. |
| FAIL | `m05-verdicts` — `keyframe-17-58p793s.png` | The enlarged Apple card overlaps NVIDIA’s card and covers part of its TRUE verdict. |
| FAIL | `m06-proof` — `keyframe-22-83p940s.png` | Zoom clips the left edge of “Total net sales” and the rightmost **450,167** value. |
| FAIL | `m08-results` — frames 34, 37–41 | “points” crosses the badge’s bottom border and hangs below its container. |
| FAIL | `m09-chinese` — frames 42–44 | Headline spacing visually collapses after the period and comma. Frames 42/44 show FALSE beside a correct conversion without identifying which part of the claim failed. |
| FAIL | `m10-cta` — `keyframe-45-154p401s.png` | Displayed demo URL ends in **`/market-claim-verifier/site/`**; the shot list specifies **`/market-claim-verifier`**. The destination needs reconciliation. |
| PASS | All 45 PNGs | No completely empty frames observed. |

**7. Explicit hackathon + Meta-model attribution — FAIL on supplied evidence**

| Result | Shot / frame | Evidence |
|---|---|---|
| FAIL | `m10-cta` — `keyframe-45-154p401s.png` | Says **“Built this week · Muse Spark · Meta open weights.”** It does not explicitly say the work was built **during the hackathon**. The shot-list narration contains that statement, but the supplied frame and its “midpoint” cue do not demonstrate delivery. |

No matching full-v2 subtitle file was found. `demo-v001.srt` contains the earlier Tesla script; `motiontest-m05-verdicts.srt` covers two seconds. Neither establishes v2 subtitle coverage.

**Ranked concrete fixes**

1. **Show Apple’s correction explicitly.** `m05-verdicts`, `keyframe-17-58p793s.png`: display quarter **$102.5B**, full year **$416.2B**, and the 4× explanation. Include a review frame at the correction cue. Keep the enlargement clear of NVIDIA’s verdict.

2. **Reflow for phone readability.** All shots; particularly `m06-proof` frame 23, `m07-program` frame 25, `m08-results` frame 34 and `m10-cta` frame 45. Reduce simultaneous text and enlarge essential labels toward 14–16 px at phone width—approximately 72–82 px in the source frame.

3. **Fix cue timing.** `m08-results`, `keyframe-41-125p456s.png`: reveal a 90.5% result when that number is spoken. `m02-spread`, `keyframe-05-9p193s.png`: show the erroneous Apple number during “quietly wrong.”

4. **Repair escaped text and spacing.** `m02-spread` frame 03 and `m04-extract` frames 13–15: render apostrophes correctly and preserve spaces in quarter/year labels. Repair headline spacing in `m09-chinese`, frame 42.

5. **Keep the proof table inside its viewport.** `m06-proof`, `keyframe-22-83p940s.png`: constrain or reposition the zoom so the row label and complete rightmost value remain visible.

6. **Make the closing claim explicit and reconcile the CTA.** `m10-cta`, `keyframe-45-154p401s.png`: state “Everything shown was built during the Meta hackathon,” retain model credits, and align the displayed URL, QR destination and shot list.

7. **Correct the results badge.** `m08-results`, `keyframe-34-128p662s.png`: use an explicit maximum such as **“Up to 70.5 percentage points”** and keep the complete label inside its box.

8. **Move the baseline footnote upward.** `m03-baseline`, frames 08–11: place every glyph above y=880, with additional clearance.

9. **Explain the Chinese FALSE verdict.** `m09-chinese`, `keyframe-42-144p208s.png` and frame 44: identify the failed growth assertion and show its supporting comparison separately from the correct unit conversion.

10. **Supply v2 subtitle evidence.** `m01-open`, `keyframe-02-0p300s.png`, through `m10-cta`, frame 45: provide the matching full-length SRT and captioned review frames to verify the shot-list subtitle requirement.
