# Demo v5 round 7 — readable terminals and source-bound narration

Base: `demo/v5` at `ed71ce698f779f4fcf17fa8228de08578c04fc6e` (host v022).
This round keeps the 20261104T170659731519Z take, pod log, local CLI session,
evaluation evidence, saved OCR/ASR replays, music, and 178-second cuts.
No new verification request, SEC fetch, recording, OCR or ASR was performed.

The source and measured timeline are ready for host rendering. Headless Chromium
cannot launch in this workspace; the retained v022 export and review frames are
historical evidence. Round-7 encoded pixels, listening and full-picture review
remain pending. The [round-7 records](prep/v5/r7/README.md) distinguish successful
source checks from this rendering limit and retain every attempt.

## Terminals and provenance

Both windows span x=80–1840, with five 30 px Menlo rows at a 36 px pitch and a
44 px header. Titles, source/replay labels and stopwatch labels also use 30 px.
The source label stays inside the header. Body lines never wrap.

The online window begins with the real request-start event, condensed to
`+0.0 s  request  POST /api/check · text · baseten`. It has no CLI command.
The retained log actually records `chars=0` at start and 321 after preprocessing;
it contains no 322-character request row. The presentation omits that placeholder
count instead of inventing one. The first real `tool_call` is **+2.69 s**, rather
than the brief's +4.3 s example. Cue binding reads that event from the hash-checked
log. This take has **six** `program_check` events at +15.97 s, condensed to
`program_check × 6` with all source indices retained. The last row remains
`verdict  contradicted  16.0 s  $0.0200`. The header labels the clock
**Request elapsed**; its genuine request duration includes SEC lookups and model
reasoning. The source label is **live request 145a6982 · pod log**.

The local title remains **Local · CLI · recorded 2026-11-04**. Its real command
is typed from the session argv. The long `--out` destination is omitted from the
display with an ellipsis and an explicit note; full argv remains in compiled data.
Twelve selected rows retain their source event indices and arrival times. Each of
five tool call/result pairs occupies one row, appearing only after its result
arrives. Each claim verdict remains. JSON and repeated model bookkeeping do not
enter the display. The footer reads **replayed at 3× · 38.6 s run**.

The local window stays above the separately labelled saved OCR/ASR and throughput
proof throughout the 116–138 s batch block. Its source clock advances at 3×;
no idle intervals are deleted. The real receipt arrives on film at **129.433 s**
(first complete 30 fps frame) and its condensed summary
`verdict  2 supported · 1 contradicted  38.6 s  $0.0611` holds until **138 s**.
The surrounding note explicitly identifies selected pairs and the receipt summary.
Ledger row v506-01 requires **command typed; timestamped progress rows**. The
later receipt is a separately audited hold and is not claimed during that sentence.

## Sentence sync and polish

The tools cue starts after the first real call. Its first call row remains visible
through the last word. The evidence-ID phrase shows E1, E2, E3 and E6 results.
The replacement clock sentence keeps its original **74.856 s** start and uses the
whole-request wording requested by the director. It shows `model · step 2` and
the running request clock. The short count phrases follow it with clearly editorial
**4 factual claims** and **4 tool calls: 3 lookups + 1 calculation** annotations and
all four actual call rows. Decision narration starts after the real verdict and
holds the program-check group and verdict through its last word.

Only `v505-thinking` and `v505-lookups` were synthesized: the latter replaces the
inaccurate "Four SEC lookups" with "Four tool calls." Every other voice unit is
reused. Local synthesis used the existing pinned Breeze model and seed, with its
Numba compilation cache redirected to a permitted temporary directory; inference
settings and source engine files were unchanged. Audio remains in the local
ignored cache, as required by the repository's distribution policy.

A declared hold of the original native verdict frame, taken inside its recorded
stationary interval, keeps the verdict and filing proof visible through the moved
sentence. The same take resumes before the unchanged draft cue. The raw MP4 and
capture receipt remain byte-identical. Frame audits check this declared source
clock rather than pretending the held source time is the original film time.

The illustrative-post label is larger and explicitly says **Illustrative viral-post
scenario**. The Apple subtraction clears at the recorded trace handoff. The password
mask begins at y=542, adding 12 px beneath the helper text; its encoded mask check
uses an interior region below that edge. The closing SEC/URL hold remains unchanged:
this round's 3× replay fits without shortening any existing proof window.

Semantic regression checks examine every spoken wait-window frame and reject a
missing first call, a missing fourth call, a missing E6 result, or a decision while
the model is still running. Actual browser audits additionally require 30 px text,
36 px pitch, unwrapped rows and clear header labels. A passing source check is not
a substitute for final encoded-picture review.

## Retained encoded export

The following measurement describes the historical v022 export. It does not certify
round 7. The normal render command updates this block only after a successful export.

<!-- actual-encode:start -->
Actual r6 encode: **demo-v022**, 178.000 s; **-14.18 LUFS integrated**, **-1.23 dBTP**.
Measured from `demo-v022.mp4`; SHA-256 `1dc5a48a33704eeb48f339f3436b9e7a0676ca33bda5b5edfe3a86e6bcc1fba8`.
[Export and measurement receipt](runs/20261104T174936925302Z-v022.json).
<!-- actual-encode:end -->

## Host completion

Run from this worktree, which already has the two new voice units in its local
cache. The voice command only synthesizes missing changed units; it reuses the
others. No recorder command is needed.

```sh
export UV_CACHE_DIR=/private/tmp/claimcheck-verify-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
uv run --project demo python demo/build.py voice --only v505 --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/motion_v5.py --measured
uv run --project demo python demo/motion_v5.py --measured --check
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5-r7
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v5.yaml --out demo/out/keyframes-v5-r7
CLANG_MODULE_CACHE_PATH=/private/tmp/mcv-v5-swift-cache uv run --project demo python demo/review_v5.py --frames demo/out/review-v5-r7
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5-r7
```

Use the new r7 review directories so the AI2 v022 review, earlier frames and ledger
remain untouched. Listen to the export and inspect both encoded resolutions before
signing the new ledger. The 178 s, audio loudness/peak, English-only, mask and ending
proof gates remain in force.
