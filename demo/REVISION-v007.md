# v007 source revision — approved gate 1 edits

**Gate 1 passed with the Owner's two edits applied.** The later host voice pass cached the narration, then
failed Hover's timing preparation. This source follow-up runs no TTS, Chromium, MPS, key-frame capture, full video
render, upload or post. The approved v006 is 160.433 s; its source timeline and narration remain intact.
[Shot list](SHOTLIST-v3.md), [storyboard](storyboard-v3.yaml), [narration](NARRATION-v007.txt).

## What changed

Twelve seekable product scenes retain the Apple whole-year/quarter trap, original Amazon proof table and original
v2 results. New scenes show the complete opening disclosure, the site's real Hover H art/pose/spotlight logic,
META guidance, Adobe non-GAAP EPS, self-made screenshot/audio inputs, recorded recall limits, and the new CTA.
The source compiler adapts the relevant expressions directly from `docs/site/script.js`, records its hash, uses
its H pose/nozzle anchors, search/lock-on geometry and compare beams, and references the original WebP assets.
Website/product source is unchanged. Strike windup and recovery prefer two actual detected beats on either side,
using a nearer interior beat when necessary; impossible pose windows still fail closed.

Shot 1 now targets **6 s**, speaking exactly “Built entirely during the Meta hackathon. Nothing here pre-existed.”
The complete disclosure is read from [JUDGE_INTRO](JUDGE_INTRO.md) and stays on screen at **64 px** throughout
the opening, with the product and saved Apple claim visible at frame zero. Shot 4 receives all **12 saved seconds**
and targets **28 s**. Shots 2 and 3 move earlier; shots 5–12 retain their original target boundaries.

The optional per-scene `narration_lead_s` defaults to **0**. Hover sets it to **9**: its voice begins on the first
detected beat at/after scene start +9 s. Audio placement, music ducking, sentence cues, cue events and subtitles
share that voice origin; cuts still use narration end +0.3 s and the absolute target hold. Reading, reaching and
beam-search poses use distinct beats across the lead window; the quarter locks on the spoken find cue, followed
by compare and strike. Music-only review windows keep the bed audible. Hover's three keyframes sample the search,
comparison and strike. Other scenes keep their original timing, narration and keyframe times.

The failed host anchors were **32.067 / 33.019 / 34.412 / 41.819 / 60.209 s** (start / find / compare / strike /
end); find collided with the old 1500 ms reach anchor. Regression tests retain these numbers and all twelve
recorded clip lengths, verify the lead fixes the sequence and preserves every cut, and reject impossible grids.
Using those lengths, Hover's voice starts at **41.3547 s**, ends at **52.3947 s**, and retains the scene's
**32.0667–60.2093 s** boundaries. These are computed timing checks, not a rendered or listening approval.

`storyboard-v3.yaml` uses `version: 2` for the existing clone/motion pipeline and `motion_variant: v3` to select
`motion/v3/index.html`. `window.seek(t)` is synchronous and repeatable after arbitrary seeks; `?t=SECONDS` works.
No playback clock or external requests. The approved v006 entry/data remain in `motion/`; its previous QR is
preserved as `motion/qr-v006.json`. The requested `motion/qr.json` now encodes **https://hackathon.dappgo.com/**,
independently decoded in the Node suite. The final URL/QR stay visible through the last frame.

`motion_v3.py` compiles only recorded evidence. It verifies release spans/values against L4-01/L4-27 raw checks,
EPS checks against hash-matched self-made fixtures, and original v2 counts. The corrected text control comes from
the [30b text report](../docs/evidence/multimodal-2026-10-30b/text/checks/text/report.json): text / screenshot / audio
all contradict **$1.67**, against **$1.57** filed. Screenshot/audio were not rerun; their evidence remains in the
30 directory. The compiler includes report, ingest, trace and SEC filing links, with hashes for local sources.

Shot 11 reads guarded/program-checked coverage directly from the [30b comparison data](../docs/evidence/multimodal-2026-10-30b/before-after.json):
**44/60** for `long-call-r2` live media, **50/60** for the frozen-ASR **text recheck**. These counts describe assertion
coverage, not verdict accuracy. Speaker labels remain unverified, sourced to the retained ingest limitation.
The [30b report](../docs/evidence/multimodal-2026-10-30b/REPORT.md) retains the failed extraction attempt and all
post-hoc caveats. L4 stays a furnished, unaudited regression test. No new held-out result or general error rate is claimed.
Source and art hashes enter render cache identities/receipts. No evaluation, SEC fetch or model call is used;
the evidence directory names are recorded report labels, with actual timestamps in their protocols.

## Per-shot edit targets

| # | Scene | Target time | Duration |
| --- | --- | --- | --- |
| 1 | Disclosure / product | 0:00–0:06 | 6 s |
| 2 | Apple post | 0:06–0:20 | 14 s |
| 3 | Extract | 0:20–0:32 | 12 s |
| 4 | Hover spotlight / strike | 0:32–1:00 | 28 s |
| 5 | Filing proof | 1:00–1:15 | 15 s |
| 6 | Program checks | 1:15–1:27 | 12 s |
| 7 | L4 releases | 1:27–1:52 | 25 s |
| 8 | Screenshot | 1:52–2:05 | 13 s |
| 9 | Audio | 2:05–2:18 | 13 s |
| 10 | Original v2 results | 2:18–2:35 | 17 s |
| 11 | Saved checks / limits | 2:35–2:48 | 13 s |
| 12 | CTA | 2:48–2:58 | 10 s |

## Key-frame times

These are **preview seconds**, derived from beat-snapped cuts and Hover pose anchors. Preview length **178.1899 s**;
edit target **178 s**. Three times (opening / middle / settled end) for **every new or revised scene**:

| Scene | Opening / middle / end (s) |
| --- | --- |
| v301-disclosure | 0.492 / 3.077 / 5.661 |
| v302-apple | 7.296 / 13.293 / 19.291 |
| v303-extract | 21.364 / 26.250 / 31.136 |
| v304-hover | 40.438 / 44.952 / 58.187 |
| v305-proof | 61.417 / 67.756 / 74.095 |
| v306-program | 76.242 / 81.177 / 86.112 |
| v307-l4 | 89.063 / 99.625 / 110.187 |
| v308-screenshot | 113.235 / 118.677 / 124.119 |
| v309-audio | 126.198 / 131.669 / 137.140 |
| v310-results | 139.547 / 146.715 / 153.883 |
| v311-limits | 156.270 / 161.634 / 166.998 |
| v312-cta | 168.833 / 173.105 / 177.376 |

Machine-readable: [keyframes.json](motion/v3/keyframes.json). After voice preparation, `build.py keyframes`
regenerates these times from the measured timeline and Hover anchors; use that manifest rather than preview absolutes.
Additional cue +0.3 s and midpoint samples come from `review-frames`. The busiest 2 s motion test is Hover's strike;
its exact window is selected from measured `cues.json`, not from an invented BPM grid.

## Host commands for Claude

The shot list is approved. The current brief authorizes source edits/tests and a local commit or bundle;
**do not render or push during this handoff**. The commands below are for the Director's later production pass,
not executed steps. Prepare locked dependencies without following the shared `.venv` symlink:

```sh
cd /Users/yan/git/market-claim-verifier-video
export UV_PROJECT_ENVIRONMENT="$PWD/demo/.venv"
export UV_CACHE_DIR="$PWD/demo/cache/uv"
uv sync --project demo --locked
```

The host needs its approved `demo/assets/voice/narrator-ref.wav` plus matching transcript and receipt, the pinned
`demo/cache/music/bed-seed92.wav`, Breeze installation, FFmpeg and preinstalled Playwright/Chromium. Preserve ignored
media before moving/removing any worktree. Use the existing approved reference; no new voice design or fallback.

Read-only source check / regenerate **target data only** (no narration/browser/media):

```sh
demo/.venv/bin/python demo/motion_v3.py --check
# After an approved storyboard edit, refresh the target preview and narration text:
demo/.venv/bin/python demo/motion_v3.py
```

Rerun voice preparation with the **locked Breeze clone**. The host already cached all twelve clips; the lead
changes no voice keys, so this command reuses them without `--force`, then rebuilds cues/cuts. Check one-voice consistency:

```sh
demo/.venv/bin/python demo/build.py voice --storyboard demo/storyboard-v3.yaml
demo/.venv/bin/python demo/build.py voicecheck --storyboard demo/storyboard-v3.yaml
```

The voice step automatically writes measured `motion/v3/data.js`, `timing.json`, `beats.json`, `cues.json` and
`keyframes.json`. It fails above 180 s or if the beat/cue sequence cannot fit. Never accelerate narration or
substitute synthetic test-media audio for the narrator. Sentence/character alignment is estimated; listen at each cue.
The standalone `motion_v3.py --check` checks **committed target previews**, so it is expected to differ after host
measurement; do not run target regeneration between measured preparation and frame/full rendering.

Gate 2 / key frames (all 36 times, then captioned cue-review pairs):

```sh
demo/.venv/bin/python demo/build.py keyframes --storyboard demo/storyboard-v3.yaml --out demo/out/keyframes-v007
demo/.venv/bin/python demo/build.py review-frames --storyboard demo/storyboard-v3.yaml --prepare-only --out demo/out/review-v007
demo/.venv/bin/python demo/build.py review-frames --storyboard demo/storyboard-v3.yaml --out demo/out/review-v007
```

Review frame zero as well (complete disclosure + visible product), using the same measured data:

```sh
node demo/motion/render.mjs --entry v3/index.html --t 0 --out demo/out/v007-opening
```

After key-frame approval, gate 3 / 2 s Hover test. Use the first detected beat at/after the strike cue, 0.2 s pre-roll:

```sh
demo/.venv/bin/python demo/build.py motiontest --storyboard demo/storyboard-v3.yaml --shot v304-hover --len 2 --out demo/out/motiontest-v007.mp4
```

After motion-test approval, full render and captioned review. Existing v001–v006 run records make the next export v007;
if another successful export has appeared, the pipeline uses the next free version rather than overwriting a film.

```sh
demo/.venv/bin/python demo/build.py render --storyboard demo/storyboard-v3.yaml
demo/.venv/bin/python demo/build.py review-frames --storyboard demo/storyboard-v3.yaml --out demo/out/review-v007
```

The same compositor uses ≥56 px captions, ≤2 lines ×42 characters, a ≤136 px panel anchored 64 px above the bottom,
so only y=880..1080 is occupied. Host layout guards measure actual text bounds, number sizes, table gutters and
subtitle-zone clearance before every PNG; image decoding is awaited before capture. End card has no picture fade.
Verify final duration ≤180 s, H.264/AAC at 1920×1080/30 fps, −14 LUFS ±1 LU and true peak ≤−1 dBTP. Have the separate
reviewer see only frames + subtitles + checklist; Owner approval precedes any upload/publication. No publishing command
is included here.

## Source verification

```sh
sh scripts/verify.sh
UV_OFFLINE=1 sh scripts/verify.sh
```

Python tests check evidence/fixture hashes, raw release and corrected EPS data, 30b coverage/attribution sources,
stale-verdict and inconsistent-evidence rejection, exact script/shot-list agreement, baseline
voice/music settings, original results counts, measured timing/overrun refusal, all-word subtitle coverage and the
36-frame manifest. Node tests cover every preview frame at 30 fps, arbitrary/reverse seek determinism, the complete
disclosure throughout the opening, Hover search/lock-on/compare beams and beat spacing, corrected verdicts/coverage
with evidence links, type and safe rectangles, final CTA, and rejection paths for the host DOM geometry guard.
The existing Node entry imports the new suite, so the full offline verifier includes it.

Before this narration follow-up, both **`sh scripts/verify.sh`** and **`UV_OFFLINE=1 sh scripts/verify.sh`** passed:
**840 product, 100 demo and 53 Node tests** each; figure rebuild/check; all three explorer/site outputs
byte-identical; local Markdown links/anchors; no model/SEC requests or credentials; source tree unchanged.
The targeted v3 suites also passed (17 Python and 12 Node tests).

For the narration follow-up, **both commands passed again** with **840 product, 121 demo and 53 Node tests**
each, plus the same figure, byte-identical rebuild, link and offline/source-integrity checks. Targeted narration/v3
Python tests passed **38/38**. Added checks cover invalid leads before synthesis, cached voice reuse, unchanged
scene cuts, shifted cues/captions, the recorded Hover collision, sparse/impossible grids, audio-window seeking,
and synthetic WAV measurements of music during the lead and ducking at voice onset. No full video was rendered.

**Remaining review:** host preparation with cached clips, real Chromium font geometry, decoded art appearance, phone readability,
beat/word perception, final loudness and independent/Owner approval. Static and offline tests do not claim these passed.

## Local commit handoff

Staging was blocked at `/Users/yan/git/market-claim-verifier/.git/worktrees/market-claim-verifier-video/index.lock`
by the workspace's write restrictions. As authorized by the brief, the local commit is packaged after
verification in `demo/out/v007-owner-edits.bundle`, based on `2eab9f3` (the existing v007 source commit, above the
30b recall fixes). The source edits remain in this worktree. The bundle uses branch `demo/v007` and the exact footer:

```text
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

Import/review from a clean checkout containing the bundle's recorded base commit:

```sh
git bundle verify /Users/yan/git/market-claim-verifier-video/demo/out/v007-owner-edits.bundle
git fetch /Users/yan/git/market-claim-verifier-video/demo/out/v007-owner-edits.bundle refs/heads/demo/v007
git show --stat FETCH_HEAD
```

No push, merge, publication or Owner approval is implied by the bundle.

### Narration follow-up bundle

Staging the follow-up hit the same `index.lock` write restriction. The authorized replacement is
`demo/out/v007-narration-lead.bundle`, based on **5179908** and containing the `demo/v007` commit with the exact
co-author footer above. Source changes remain in this worktree; the existing branch reference is unchanged.

```sh
git bundle verify /Users/yan/git/market-claim-verifier-video/demo/out/v007-narration-lead.bundle
git fetch /Users/yan/git/market-claim-verifier-video/demo/out/v007-narration-lead.bundle refs/heads/demo/v007
git show --stat FETCH_HEAD
```
