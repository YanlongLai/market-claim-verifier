# Media production playbook (reusable)

A repeatable way to make product demo videos, site animations and launch posts with AI, with a human approving
each step. Copy this folder into any project, fill in `templates/brief.md`, and follow the steps.
First used for Market Claim Verifier; that project's real record is [docs/PROCESS-media.md](../../PROCESS-media.md).
Edit freely: change gates, criteria or tools per project, and note what you changed at the bottom.

## Roles

- **Owner** approves every gate and anything published.
- **Director** (Claude Code) writes the brief, shot list and acceptance criteria; renders on the host; reviews
  every output; decides what goes back for fixes.
- **Builder** (Codex) implements code, tests, animation and AI images in its own git worktree; never commits.
- **Second reviewer** (a separate AI run) sees only the output frames + checklist and reports strictly.

## Steps

| # | Step | Output | Gate |
|---|---|---|---|
| 0 | Check tools: ffmpeg, Playwright + Chromium, TTS, music model, disk space (≥ 15 GB free) | Tool report | — |
| 1 | Fill the brief: size, audience, goal, CTA, acceptance criteria | `templates/brief.md` filled | Owner |
| 2 | Shot list: time, picture & motion, narration, on-screen text, director notes | `templates/shot-list.md` filled | **Owner** |
| 3 | Voice: 3 candidates from one description → Owner picks → lock as clone reference | `assets/voice/narrator-ref.wav` + `.txt` | **Owner** |
| 4 | Music: generate the bed; measure the real beat (models ignore BPM prompts) | music WAV + `beats.json` | Owner listens |
| 5 | Builder makes the HTML/CSS/JS timeline with `seek(t)` (any second renders exactly) | motion code + tests | Director |
| 6 | 3 key frames (opening, middle, end) | 3 PNGs | **Owner** |
| 7 | 2-second motion test of the busiest moment, with music and narration | 2 s MP4 | **Owner** |
| 8 | Full render; automatic checks; review frames per shot and per narration cue | MP4 + SRT + run record | — |
| 9 | Second-AI review + director review against `templates/acceptance.md` | review report | must pass |
| 10 | Owner review, then publish; log the result | published link | **Owner** |

Fix loop: any FAIL in step 9 → one brief to the builder listing every finding → re-render → re-review.

## Rules that saved time

- Lock one narrator voice before generating any narration (per-clip voice design sounds like different people).
- Rebuild key UI in HTML instead of recording the live page (crisp text, exact numbers).
- Every number on screen comes from real data; if you change an example, run the product on it first.
- Pictures follow the narration: detect sentence timing (ffmpeg `silencedetect`), fire each event on the next beat.
- AI images never carry important words; render text with HTML/SVG so spelling is guaranteed.
- Save every generation prompt next to its asset so it can be regenerated.
- Animations need a deterministic seek hook (`?t=`) so reviewers can check exact moments.
- Loudness −14 LUFS ±1 LU, true peak ≤ −1 dBTP.

## Templates

- [brief.md](templates/brief.md) — the one-paragraph brief + acceptance criteria
- [shot-list.md](templates/shot-list.md) — shot list table
- [acceptance.md](templates/acceptance.md) — checklist used by both reviewers
- [builder-brief.md](templates/builder-brief.md) — how to hand a step to Codex
- [second-review.md](templates/second-review.md) — prompt for the independent AI reviewer
- [site-animation.md](templates/site-animation.md) — variant for a looping website animation

## Change log
- 2026-10-28: first version, from the Market Claim Verifier demo (v001 → v003) and stamp animation.
