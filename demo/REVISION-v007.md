# v007 source revision — gate 1 handoff

**Proposal only; Owner shot-list approval is pending.** No TTS, Chromium, MPS, key-frame capture, video render,
upload or post was run for v007. The approved v006 is 160.433 s; its source timeline and narration remain intact.
[Shot list](SHOTLIST-v3.md), [storyboard](storyboard-v3.yaml), [narration](NARRATION-v007.txt).

## What changed

Twelve seekable product scenes retain the Apple whole-year/quarter trap, original Amazon proof table and original
v2 results. New scenes show the complete opening disclosure, the site's real Hover H art/pose/spotlight logic,
META guidance, Adobe non-GAAP EPS, self-made screenshot/audio inputs, retained misses and limits, and the new CTA.
The source compiler adapts the relevant expressions directly from `docs/site/script.js`, records its hash, uses
its H pose/nozzle anchors, and references the original WebP assets. Website/product source is unchanged.

`storyboard-v3.yaml` uses `version: 2` for the existing clone/motion pipeline and `motion_variant: v3` to select
`motion/v3/index.html`. `window.seek(t)` is synchronous and repeatable after arbitrary seeks; `?t=SECONDS` works.
No playback clock or external requests. The approved v006 entry/data remain in `motion/`; its previous QR is
preserved as `motion/qr-v006.json`. The requested `motion/qr.json` now encodes **https://hackathon.dappgo.com/**,
independently decoded in the Node suite. The final URL/QR stay visible through the last frame.

`motion_v3.py` compiles only recorded evidence. It verifies release spans/values against L4-01/L4-27 raw checks,
the new 2026-10-30 EPS checks against hash-matched self-made fixtures, and original v2 counts. Source and art hashes
enter render cache identities/receipts. No evaluation, SEC fetch or model call is used. The 2026-10-30 directory is
the recorded report label; actual run timestamps remain in its protocols. No new held-out claim is made.

## Key-frame times

These are **preview seconds**, snapped to the committed detected beat grid. Preview length **178.1899 s**;
edit target **178 s**. Three times (opening / middle / settled end) for **every new or revised scene**:

| Scene | Opening / middle / end (s) |
| --- | --- |
| v301-disclosure | 1.451 / 9.067 / 16.684 |
| v302-apple | 19.249 / 25.101 / 30.952 |
| v303-extract | 33.036 / 38.127 / 43.218 |
| v304-hover | 45.469 / 52.198 / 58.928 |
| v305-proof | 61.417 / 67.756 / 74.095 |
| v306-program | 76.242 / 81.177 / 86.112 |
| v307-l4 | 89.063 / 99.625 / 110.187 |
| v308-screenshot | 113.235 / 118.677 / 124.119 |
| v309-audio | 126.198 / 131.669 / 137.140 |
| v310-results | 139.547 / 146.715 / 153.883 |
| v311-limits | 156.270 / 161.634 / 166.998 |
| v312-cta | 168.833 / 173.105 / 177.376 |

Machine-readable: [keyframes.json](motion/v3/keyframes.json). After synthesis, `build.py keyframes` regenerates
these times relative to each measured shot; use the regenerated manifest rather than the preview absolutes.
Additional cue +0.3 s and midpoint samples come from `review-frames`. The busiest 2 s motion test is Hover's strike;
its exact window is selected from measured `cues.json`, not from an invented BPM grid.

## Host commands for Claude

Run **only after Owner approval of the shot list**, in this worktree. These are handoff commands, not executed
production steps. Prepare locked dependencies without following the shared `.venv` symlink:

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

Synthesize the 12 paragraphs via the **locked Breeze clone**; measure cues/cuts and check one-voice consistency:

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

New Python tests check evidence/fixture hashes, raw release and EPS data, exact script/shot-list agreement, baseline
voice/music settings, original results counts, measured timing/overrun refusal, all-word subtitle coverage and the
36-frame manifest. New Node tests cover every preview frame at 30 fps, arbitrary/reverse seek determinism, Hover poses,
source values/labels, type and safe rectangles, final CTA, and rejection paths for the host DOM geometry guard.
The existing Node entry imports the new suite, so the full offline verifier includes it.

Result: **`UV_OFFLINE=1 sh scripts/verify.sh` passed** — 817 product, 94 demo and 52 Node tests;
figure regeneration/check; all three explorer/site outputs byte-identical; local links/anchors; no model/SEC
requests or credentials. The final scene and Markdown checks pass as well. These are source/test results.

**Remaining review:** actual voice durations, real Chromium font geometry, decoded art appearance, phone readability,
beat/word perception, final loudness and independent/Owner approval. Static and offline tests do not claim these passed.

## Local commit handoff

The shared `.git/worktrees/market-claim-verifier-video/index.lock` path rejected writes in this environment.
As authorized by the brief, the local commit is packaged in `demo/out/v007-source.bundle`; the source changes are
also present in this worktree. The bundle carries branch `demo/v007` and the exact requested footer:

```text
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

Import/review from a clean checkout containing the bundle's recorded base commit:

```sh
git bundle verify /Users/yan/git/market-claim-verifier-video/demo/out/v007-source.bundle
git fetch /Users/yan/git/market-claim-verifier-video/demo/out/v007-source.bundle refs/heads/demo/v007
git show --stat FETCH_HEAD
```

No push, merge, publication or Owner approval is implied by the bundle.
