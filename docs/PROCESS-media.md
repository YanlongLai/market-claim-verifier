# How the website, social posts and demo video were made

A running record of the media work for the Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026).
It covers who did what, the decisions and review gates, what went wrong, and where every asset and prompt lives.
Detailed per-build records for the video are in `demo/BUILD_LOG.md` and `demo/runs/` on the `demo/pipeline` branch.

## Roles

| Who | Does |
|---|---|
| Owner (Yenlung) | Sets goals, approves every gate, picks voice and examples, approves anything published |
| Claude Code | Director and reviewer: writes shot lists and briefs, sets acceptance criteria, renders on the host, reviews every output in the browser or frame by frame, decides what goes back for fixes |
| Codex (gpt-6.1-sol, max) | Implements: code, tests, animation, AI images (built-in image_gen); runs in its own git worktree, never commits |
| Second AI reviewer | A separate Codex run that sees only the rendered frames and the checklist, and must report strictly |

Rule: nothing is merged, published or posted without Claude's review and the Owner's OK.

## Tools and licences

| Tool | Used for | Runs | Licence |
|---|---|---|---|
| Breeze-TTS-2 (BreezeBlue) | Narration voice | Locally on the Mac GPU (MPS), ~10× slower than real time; installed in `~/ml-engines/breeze-tts` | Code Apache-2.0; weights research / non-commercial |
| ACE-Step 3.5B | Background music | Locally on MPS (number-rpg's install), 190 s in ~4 min | Apache-2.0 |
| Codex image_gen | Stills, social images, textures | Codex | — |
| Playwright 1.64 + Chromium | Rendering HTML frames, screenshots | Host | Apache-2.0 |
| ffmpeg 9 | Encoding, subtitles, mixing, loudness (−14 LUFS) | Host | LGPL/GPL |

## Website

1. **Simple landing page** (Day 3): real post example first, three steps, one chart, EN/中文.
2. **"See filing" pop-up**: the exact SEC table row with the number highlighted, links to the original filing.
   Review found wrong facts under a passage, duplicates and unreadable tables on phones; Codex fixed them.
3. **Post-hoc rerun block**: the rerun numbers, clearly labelled as a regression check.
4. **Stamp animation** (in progress, branch `site/stamp-animation`): finance cards with tickers pass a
   "Muse Spark agent + SEC check" gate and get stamped TRUE / FALSE / CAN'T CHECK. Every card is a real verdict.
   - Round 1 review: stamps vanished about 1 s after landing; stamps too small; cards flat grey.
   - Round 2: desktop passes. Phone fails: two cards share the screen and get clipped → one card at a time.
   - Added a deterministic `?stamp-t=` seek so every moment can be checked exactly.
   - AI art: ink texture and paper grain only; stamp words are real text so spelling is always right.

## Social

- **X** (@dappgoDev, Oct 28): 2-post thread with a Codex image. The first draft was 99 characters over the limit,
  so it was split into a thread without changing the approved wording.
- **Discord #intros** (Oct 28): shortened intro with 2 images. Track not mentioned (may switch to Startup);
  technical detail and numbers kept for the video.

## Demo video

### v001 — first end-to-end build (2:10)

Storyboard YAML → Breeze narration → Playwright recordings of the live site → Codex stills → ACE-Step music →
ffmpeg with subtitles and ducking. **Rejected:**
- The narrator sounded like a different person in every scene (voice designed per clip).
- Site recordings were too small to read; light site vs dark stills; one scene showed the Chinese explorer under
  English narration; captions collided.

### Method change (Owner)

- Animation written in HTML + CSS + JS with `seek(t)`, so any second renders exactly; Playwright renders frames;
  ffmpeg assembles with music; motion cut to the beat.
- Staged approval: **shot list → voice → 3 key frames → 2 s motion test → full render → second-AI review.**
- Acceptance criteria: product within 3 s, phone-readable text, subtitles, one voice, ≤ 3:00, built-during-the-hackathon
  statement.

### Gates

| Gate | What happened |
|---|---|
| Shot list | 10 shots, ~2:40, approved as written (`demo/SHOTLIST-v2.md`) |
| Voice | 3 candidates (seeds 1234 / 2026 / 7); Owner picked B. Locked as a clone reference; every scene is cloned from it. Voice check: minimum similarity 0.90 (threshold 0.85) |
| Music | Prompt asked for 92 BPM; ACE-Step produced ~129 BPM with drift up to 0.24 s, so motion snaps to each detected beat instead of a fixed grid |
| Key frames | Approved after 3 tweaks. Owner asked for a more dramatic false example: Tesla (+3% vs −2.9%) replaced by Apple "$416.2B in one quarter" — really the full year; the quarter was $102.5B (4×). The new example post was run through the checker first ($0.06) so the video only shows real verdicts |
| 2 s motion test | Cards hit the beat, but were too small and flipped before the narrator named each company → cues now follow the narration (silence detection per sentence, event on the next beat) |
| v002 (2:40) | Rendered. **Failed** both reviews: `&#39;` shown in text, small labels on phones, a few reveals out of sync, a clipped table, an imprecise "+70 points", no explicit hackathon line, and a Chinese example (Meta 623 億) whose FALSE relied on strict rounding → replaced by Coca-Cola 500 億 vs $47.1B |
| v003 | Fixing all findings; will be re-reviewed by the second AI and Claude before the Owner sees it |

### Lessons

- Lock the voice before generating any narration; per-clip voice design drifts.
- Rebuild key UI in HTML instead of recording the live page: sharper text and exact numbers.
- Drive animation from narration timing, not just the beat.
- A second, independent AI reviewer caught issues the director missed (sync, precision of labels, clipping).
- Check the delivery tolerance: −14 LUFS ±0.5 failed on an AAC encode at −14.86; ±1 LU is standard.

## Where things are

| What | Path |
|---|---|
| Video pipeline, storyboard, shot list, build log, runs | `demo/` on branch `demo/pipeline` |
| Video prompts (music, stills) | `demo/prompts/` |
| Locked narrator reference | `demo/assets/voice/narrator-ref.wav` + `.txt` |
| Demo example post and its check | `examples/posts/demo-thread.txt`, `docs/evidence/posts-2026-10-28/demo-thread-baseten/` |
| Social images and prompts | `docs/social/`, `docs/prompts/social/` |
| Site image prompts | `docs/prompts/site/` |
| Codex briefs | Kept in the Owner's private notes (not in this repo) |
