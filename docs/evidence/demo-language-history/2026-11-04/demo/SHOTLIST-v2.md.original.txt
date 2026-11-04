# Demo v2 shot list — v004 visual revision

Brief (Owner's template, filled in):
「Use the Market Claim Verifier hackathon material to make a **16:9 (1920×1080)** motion video for **hackathon judges
and people on X / Discord**. Goal: **make them understand the product's highlights** (catches wrong finance numbers,
shows the SEC proof, the program decides, measured accuracy). CTA: **Try the live demo** at
https://yanlonglai.github.io/market-claim-verifier/site/ (plus star the GitHub repo). Animation written in HTML + CSS + JavaScript,
frame-addressable (any second can be rendered), Playwright screenshots every frame, ffmpeg assembles the MP4 with
music; motion is cut to the music's beat.」

## Production method (v2 replaces v001's live-site recordings)

- `demo/motion/index.html` + CSS + JS: one timeline. `window.seek(t)` draws the exact frame for second `t`
  (no real-time playback), so any frame can be rendered and re-rendered deterministically.
- Playwright renders 30 fps PNG frames (1920×1080) → ffmpeg encodes → mixes narration + music.
- Music: ACE-Step bed at 92 BPM (beat = 0.652 s, bar = 2.609 s). The beat grid is measured from the audio
  (librosa onset/beat tracking) and written to `motion/beats.json`; every scene change lands on a detected beat and
  every pop/flip lands on a beat.
- All numbers on screen are real (from the reports / eval), rebuilt as crisp HTML instead of screen recordings.
- **One narrator voice for every scene:** generate one reference line with voice design, Owner approves it, then
  every scene is synthesized in Breeze **voice-clone mode** from that same reference audio + transcript + fixed seed.
  (v001 used voice design per scene, which drifts between speakers.)

## Acceptance criteria (checked on every build)

1. Product name + UI appear within **3 s**.
2. Mobile-readable: meaningful text ≥ 56 px (body defaults to 64 px), numbers ≥ 96 px, headlines ≥ 96 px at 1080p; nothing important within 64 px
   of the edge; contrast ≥ 4.5:1.
3. Subtitles on every spoken line (burned in + .srt), ≤ 2 lines, ≤ 42 chars per line.
4. Same narrator voice in all scenes (speaker-similarity check across clips).
5. Every scene cut on a detected beat; motion hits within ±1 frame of a beat.
6. Total length ≤ 2:50 (hackathon limit 3:00).
7. States clearly that everything shown was built during the hackathon, and uses Meta models (Muse Spark, open weights).
8. A second AI reviewer (Codex, separate run, given only the frames + this checklist) passes it; Claude reviews too.

## Shot list (≈ 2:40, 61 bars at 92 BPM)

| # | Time | Bars | Picture & motion (director's notes) | Narration (one voice) | On-screen text |
|---|---|---|---|---|---|
| 1 | 0:00–0:05 | 2 | **Cold open on the product.** Title slams in on the downbeat; the claim card asks "Apple made $416B in one quarter?" and flips to coral FALSE on beat 3. | "This is Market Claim Verifier." | Market Claim Verifier · Check the number before you share it |
| 2 | 0:05–0:18 | 5 | A social post types in with decoded apostrophes and spaced period labels. $143.1B and 2× appear with “Some numbers are right”; $416B appears coral with “some are quietly wrong”. Each token retains a readable period or claim label. | "Finance posts move fast. Some numbers are right, some are quietly wrong, and almost nobody checks." | Numbers spread faster than facts |
| 3 | 0:18–0:31 | 5 | Bar chart: model-alone results 20%, 21%, 44% on their narration beats. Provider labels are 64 px; the 56 px Muse Spark / 357-claim note ends at y=866, clear of subtitles. A bounded 1.0→1.02 push keeps every label inside the safe area. | "Ask a language model on its own and it guesses. On 357 finance claims, Muse Spark from memory was right only 20 to 44 percent of the time." | Model alone: 20–44% |
| 4 | 0:31–0:52 | 8 | Step 1. One full-width exact quote at a time, with 72 px body and numbers at least 96 px. A highlight sweeps across each fact; four short status cells track Amazon, NVIDIA, Apple and the opinion. The opinion is explicitly “not judged”. | "Paste a post. Muse Spark pulls out each checkable claim with its exact quote. Forecasts and opinions are labeled, not judged." | 1 · Extract claims |
| 5 | 0:52–1:13 | 8 | Step 2. Amazon and NVIDIA flip TRUE; Apple flips FALSE. At FALSE, Apple opens in a separate right column and both TRUE cards remain visible in the left column. Immediately show “Post says $416.2B in one quarter”, coral “Fiscal Q4 2025: $102.5B”, grey “Full fiscal year 2025: $416.2B”, both proportional bars and “4× too high · that's the full year”. All detail is fully visible at “That's the whole year” and “The quarter was 102.5 billion”; a restrained eight-second push never overlaps NVIDIA. | "An agent looks up SEC data for each one. Amazon, 143.1 billion: true. NVIDIA, more than double: true. Apple, 416 billion in one quarter: false. That's the whole year. The quarter was 102.5 billion." | 2 · Verdict for every claim |
| 6 | 1:13–1:34 | 8 | Step 3. Use the authorized two-column SEC 10-Q close-up: Total net sales; Three months ended Sep 30; 2023: 143,083 highlighted, 2024: 158,877. Fixed 500/576/576 px columns have 48 px gutters; values are right-aligned 128 px tabular numerals. The amber sweep covers the full 143,083 cell. Nine-month values 404,824 / 450,167 remain in source data and the linked original filing. Period/source/link labels are at least 56 px. | "Every verdict links to proof: the exact table row in the 10-K or 10-Q, number highlighted, one click to the original filing." | 3 · See the SEC proof |
| 7 | 1:34–1:57 | 9 | Two large lanes fill over 60% of the safe area. MODEL: Plan SEC lookups → Cite E1, E2. PROGRAM: Number ±0.05B → Fiscal ↔ calendar → Evidence. A fake E9 receives a coral ✕ at “rejects”. Short labels are at least 56 px and numeric/evidence tokens at least 96 px. | "The key design: the model proposes, the program decides. Code re-reads the number and its precision, checks fiscal and calendar years, and rejects any evidence the model made up." | Model proposes · program decides |
| 8 | 1:57–2:20 | 9 | A full-width results board fills over 60% of the safe area: Meta Model API 44→83%, Baseten 21→90.5%, Fireworks 20→90.5%. Show Meta with “83 percent” and both 90.5% rows with “90.5 percent”. A contained badge reads “Up to +70.5 points”. Provider names are 72 px, results at least 104 px; context says pre-registered / 357 claims / Muse Spark. | "We committed the answers before running anything. With tools and program checks: 83 percent on the Meta Model API, and 90.5 percent with open-weight Muse Spark on Baseten and Fireworks." | Pre-registered · 357 claims |
| 9 | 2:20–2:28 | 3 | Chinese Coca-Cola claim 3: 「可口可樂 2024 年營收突破 500 億美元。」 Show “500 億 = $50.0B” on the Chinese cue, then coral “Filed: $47.1B” and FALSE. The FY2024 10-K reports $47.061B (= 470.6 億), below the claimed threshold. Keep the claim and conversion separate from the filed comparison. | "It works in Chinese too." | English · 中文 |
| 10 | 2:28–2:40 | 4 | CTA. Large live-demo URL https://yanlonglai.github.io/market-claim-verifier/site/ and matching QR, GitHub repo, the explicit 56 px line “Built during the Meta Global AI Developer Hackathon”, and “Muse Spark · Meta open weights”. Music resolves; 2 s fade. | "Built this week for the Meta hackathon. Try the live demo, and check the number before you share it." | Try the live demo · https://yanlonglai.github.io/market-claim-verifier/site/ |

## Host review gates

The v004 brief authorizes these three source fixes and local checks. Host rendering and re-review use the commands in `REVISION-v004.md`. Narration stays unchanged.

1. **This shot list** records the authorized v004 direction.
2. **Voice:** one reference line in the chosen voice → Owner approves → locked for all scenes.
3. **3 key frames** (shot 1 at 0:03, shot 5 at 1:05, shot 10 at 2:35) as PNGs → check visual direction.
4. **2-second motion test** (shot 5 card flips on the beat, with music) → check speed and rhythm.
5. Full render → automatic checks + second-AI review + Claude review → Owner review.
