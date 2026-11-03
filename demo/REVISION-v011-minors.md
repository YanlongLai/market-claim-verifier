# v011 AI2 minor fixes — N4 and N5

Source changes for the two findings in the local review at
`demo/out/review-v011/AI2-REVIEW.md`. No new film is exported by this change.

- **N4:** Both real-world aggregate pages use 56 px Supported, Contradicted,
  Insufficient and failed-runs labels. Count columns are 144 px; label columns are
  416 px with a 16 px internal gap and 32 px between columns. Item coverage,
  claim-verdict counts, route and post-hoc limitations remain explicit. Text boxes
  end at y=816, above the y=880 caption band and the y=1016 caption-panel limit.
- **N5:** `narration_offset_s: 1.05` places the unchanged extraction voice clip
  1.05 s later. Both sentences and their captions share that placement; no audio
  is sliced, accelerated or synthesized. The retained opinion clause clock becomes
  22.770308257 s, with its SRT beginning at 22.766 s (the 22.766667 s video frame).
  The opinion picture stays on the first detected beat at scene + 5 s: 22.7555 s,
  encoded at 22.766667 s. Amazon/NVIDIA/opinion holds stay 75/77/138 frames.
  The existing 2.5627 s post-speech hold becomes 1.5127 s; all scene cuts and the
  177.2611 s source timeline stay unchanged.

The generators now support an exact voice-placement offset after any beat lead
and a fixed scene-relative picture event. Offset validation runs before voice
preparation, and placement edits retain voice cache keys. The five host outputs
`data.js`, `timing.json`, `keyframes.json`, `beats.json`, and `cues.json` are left
byte for byte as found; only the committed offline preview is regenerated here.

## Host regeneration and render

Run from the repository root with the existing thirteen voice clips and music
cache. These commands reuse cached narration and fail if it is missing; they do
not synthesize it.

```sh
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml review-frames --prepare-only --out demo/out/review-v012-plan
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml keyframes --out demo/out/keyframes-v012
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml render
```

The first command refreshes the host timing/data/keyframes/beats/cues and writes a
full-length review SRT without launching Chromium. The second captures regenerated
keyframes. The last exports the next numbered film and SRT. Inspect the aggregate
pages at 480 px playback width and confirm the shifted spoken clause on the host.
No voice, render, model/SEC call, push or upload was executed for this source fix.

## Verification

[Retained checks and limitations](../docs/evidence/demo-v011-minor-fixes/README.md)
include the real-world/preview checks, regression tests, full repository verifier,
font/geometry audit, and failed first Node/browser attempts. This is an offline
source recheck, not fresh OCR/ASR or a new encoded-film review. Browser still review
could not run: Playwright 1.64 was absent, browser access was unavailable, and
Computer Use rejected Google Chrome access.

Shared Git metadata is read-only. Delivery is a verified local bundle at
`runs/v011-minor-fixes.bundle`, with branch `demo/v010`, based on `6ca4544d` and the
requested Claude Opus 5.5 co-author footer. Import after reviewing the bundle:

```sh
git bundle verify runs/v011-minor-fixes.bundle
git fetch runs/v011-minor-fixes.bundle refs/heads/demo/v010
git show --stat FETCH_HEAD
git merge --ff-only FETCH_HEAD
```
