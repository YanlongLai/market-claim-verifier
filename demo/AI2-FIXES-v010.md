# v010 AI2 fixes

This revision addresses M1, M2, N1, N2 and N3 from the retained review at
`demo/out/review-v010/AI2-REVIEW.md`, against base `3b929cc2` on `demo/v010`.
The presentation remains **177.2611 s**. All narration text, cached voice inputs, music,
financial results and retained original/post-hoc evidence remain unchanged.

| Finding | Change |
| --- | --- |
| M1 | Four pages: original News + Threads aggregate, CoreWeave, SanDisk, post-hoc News aggregate. Each holds **2.827025 s** within **155.7130–167.0211 s**. CoreWeave compares **$2.29B → $229M**, SEC 10-K FY2023. SanDisk compares **23% → 377.9% recorded YoY**, SEC 10-Q FY2027Q1. The values are **112 px**, source/period/outcome at least **56 px**, and CONTRADICTED is a **64 px** chip. The example pages contain no repeated aggregate rows. Aggregate labels are at least **48 px**. Coverage and post-hoc qualifications remain visible. Cost and latency detail stays in the linked reports and snapshot. |
| M2 | Amazon holds **17.6704–20.1704 s**, then NVIDIA until the deferred opinion picture cue. The repeated Apple extraction card is removed. With the retained voice-length/pause replay, the opinion reveal is **22.7555 s** and holds to **27.3531 s**. The sentence/subtitle clock stays attached to the existing audio; only the picture waits for reading time. |
| N1 | Both aggregates name **Baseten · post route** and use **0 run failures / 6 run failures**. Checked/all-attempted denominators remain **44/80**, **42/78**, and **43/80** for the recheck. The counts are explicitly claim verdicts, distinct from item coverage. |
| N2 | **Saved trace · recorded 8.080 s, compressed** stays fixed throughout the trace. Per-step monetary detail is removed. The compact final run receipt holds **34.1643–36.6643 s**, before the retained Hover narration starts. Step and receipt keyframes use the same compressed clock. |
| N3 | The L4 placement formerly using `turn-point-s11` now selects the approved `point-glow-s29` source frames. The manifest retains all original source/receipt records and explicitly maps the replacement. No source media was generated or changed. |

[Regression evidence](../docs/evidence/demo-v010-ai2-fixes/README.md) retains every test attempt,
including the initial margin failure and the unavailable browser capture. Tests enforce type floors,
safe rectangles, at least **75 encoded frames at 30 fps** per extraction card and real-world page,
the final receipt hold, recorded-value binding, deterministic seeks and approved replacement hashes.
The five host outputs are byte-identical to their pre-task hashes. The committed preview is updated;
host `data.js`, `timing.json`, `keyframes.json`, `beats.json` and `cues.json` are excluded from delivery.

## Host commands

Run these from `/Users/yan/git/market-claim-verifier-video` after importing the delivered commit.
They reuse cached narration. `broll.py extract` only decodes the existing approved 480 clips.
The source update did not synthesize voice or render a film.

```sh
uv run --project demo python demo/broll.py check
uv run --project demo python demo/broll.py extract --ffmpeg /opt/homebrew/bin/ffmpeg
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  keyframes --out demo/out/keyframes-v010-ai2-fixes
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  review-frames --out demo/out/review-v010-ai2-fixes
```

Inspect the changed intervals with captions and at phone size. The browser still attempt here failed
before launch because Playwright 1.64 was unavailable; no rendered visual pass is claimed. After that
host review, the exact film command is:

```sh
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml render
```

The renderer chooses the next versioned output and preserves the previous film. No `voice`, model,
SEC-fetch or overwrite command is needed for these changes.

## Bundle import

Shared Git metadata is read-only in this environment, so delivery uses `runs/v010-ai2-fixes.bundle`,
containing `refs/heads/demo/v010` with base `3b929cc2aed162dc8f9468c42cbafbe8c1b8d484` as prerequisite.
Import on the host:

```sh
git bundle verify runs/v010-ai2-fixes.bundle
git fetch runs/v010-ai2-fixes.bundle refs/heads/demo/v010
git show --stat FETCH_HEAD
git merge --ff-only FETCH_HEAD
```
