# Demo v5 round 3 — sentence measurement and picture binding

Round 3 starts at `a3440e73` on `demo/v5`, following the FAIL in
`demo/out/review-v5/AI2-REVIEW-v017.md`. AI001 remains disabled. The ten cuts remain
0 / 8 / 20 / 32 / 46 / 58 / 116 / 138 / 154 / 170 / 178 seconds; output remains
1920×1080, 30 fps. The chapter label **Fix stays**, by the Owner's design decision.

This is a source handoff for the host sequence below. The committed motion data and SRT
are explicitly **unmeasured layout previews**, not a new film or accepted ledger. The old
measured inputs are retained in [inputs-before.json](prep/v5/r3/inputs-before.json); the
v017 film, review, ledger, WAVs and failed/partial attempts are preserved. New per-sentence
measurements, the final SRT and a fresh ledger are produced after host recording/synthesis.
Do not reuse the v017 ledger as acceptance for this revision.

[Narration](NARRATION-v5.txt) and [storyboard](storyboard-v5.yaml) now have **43 independent
sentence/phrase voice units**. All scenes have `cue_events`; none aliases a multi-sentence
v4 WAV. New units use `demo/cache/voice/<scene>-<event>/<voice-key>/clip.wav`.
Unchanged single-sentence units keep their exact cache identities. In v505 the numeric
edit changes only the evidence unit to **$416.2 billion**. Splitting the old paste/trace
units requires new source audio; the tools, verdict, draft and receipt words stay unchanged.
The program-verdict row has its own short cue: “The program's verdict.”

[voice_v5.py](voice_v5.py) measures each unit's outer speech envelope directly from its
16-bit PCM samples: 5 ms RMS windows, −50 dBFS, two adjacent active windows to reject
isolated clicks. It retains internal pauses and every source sample in the lossless assembly.
Receipts retain the unit WAV hash, sample rate, threshold, onset/end sample frames and voice
key. These are acoustic measurements of one supplied sentence, not word recognition or a
new OCR/ASR test. Listening to the final mix is still required.

The compiler places the measured onset, schedules its picture **0.2 s earlier**, and keeps
the state through the measured last word. Web sentences can move later to retain their full
source and the preceding sentence's picture. Live phases stay fixed to the continuous take.
Compilation fails if audio exceeds its cut/phase window or native proof is abandoned before
the last word. It never speeds or cuts speech. Each unit fits one two-line, 42-column subtitle;
SRT timestamps are quantized to the containing video frame, without internal text estimates.

Picture changes:

- v500: full title at the first frame; the build disclosure enters with its own sentence.
- v501: cascade begins with “Thousands repost it” and is clipped to the left 55%; the right
  headline column is reserved. The Apple sentence adds a highlight band and enlarged
  `$416.2 billion … fiscal Q4 2025` excerpt. The card says “Illustrative post” in muted 24 px.
- v502: all four real previews are present from the opening state. Screenshot, PDF, Audio
  and Video light on separate measured phrases; the question is a later headline state.
- v503: completed literal saved rows replace partial typewriter numbers. `74/357 · 20.7%`
  is ready before the first sentence; `90.5%` waits for the separate “nine in ten” cue;
  `240/266 held-out · 90.2%` is complete before the held-out phrase. Includes-dev,
  corrected-gold and failures-as-wrong labels remain.
- v504: Muse Spark/SEC focus first, with Python dim; Python/corrected draft focus second;
  “Model proposes; program decides.” appears with sentence three.
- v506: completed saved output follows each phrase; the projection row is withheld until
  its own cue. No new product OCR/ASR run is implied.
- v507: 90.2%, 1/139, $0.02 + 10 s, then coverage. The false-support label has two lines:
  “non-supported claims” / “wrongly supported”, at the same 56 px as the other tile labels.
- v508/v509: the URL and DappGo wordmark enter with their words. The robot stamps a
  legible DappGo imprint and finishes before the sign-off; the chapter rail shares its fade.

The recorder is now **capture v8**. It keeps the opaque startup cover until the Try input
has been scrolled into its centred 1560 px workspace. The continuous raw WebM is retained.
After capture, the decoded cover edge calibrates page/video clocks and three native workspace
frames establish the MP4 start; paper-only,
black, hero and stamp startup frames cannot enter the film. This is a continuous selection,
not a montage or speed change. The v017/v7 take cannot pass the v8 export gate.

| Live cue | Receipt phase | Named native proof |
| --- | --- | --- |
| Live, on the site. | `live_workspace_reveal` | Centred Try input |
| Paste the post. | `use_apple_example` | Native English post |
| Muse Spark calls the SEC tools. | `check_against_sec` | Native in-progress status, framed above the card |
| Contradicted, with the filing. | `verdict_reveal` | Native verdict word |
| And here is the corrected draft. | `draft_reveal` | Cited changes title and corrected edit, below a top-band card |
| Apple's annual revenue… | `evidence_reveal` | Apple evidence, held before any derivation inspection |
| Every SEC call is on the record. | `tool_call_2_reveal` | First native tool-call row |
| You can see each call. | `tool_call_4_reveal` | Tool-call walk |
| The program's verdict. | `program_verdict_reveal` | Native program-verdict row |
| Cost and time, on the receipt. | `hover_receipt` | Native receipt |

All overlay backgrounds are fully opaque. Recorded native rectangles determine whether the
card uses the top or bottom band; capture rejects a state that fits neither. Native visibility
intervals end before the next scroll. The Apple hold is 7.6 s; derivation inspection follows.
All four tool rows and the program verdict are still inspected. The receipt card says
**Live take**, with the actual capture cost and elapsed time formatted like **16.3 s**.
A new take's measured values replace the old values; they are not pinned to the v017 receipt.
The ending frames the native Cited changes title, corrected edit and both SEC component links;
spacing moves the unrelated Inspect data / Not corrected section entirely below the frame.

Every real Chromium review frame runs [the layout audit](motion/v5/layout-checks.mjs).
[Sentence targets](motion/v5/sentence-targets.mjs) cover every row: the audit checks actual
DOM visibility, full numeric text, clipping, opaque cards and native rectangle clearance at
both measured speech boundaries. Native proof uses capture rectangles over the recorded
stationary interval, with the actual video shown 1:1. `review-frames` retains the per-row
results in `index.json`; `review_v5.py` requires complete coverage and writes
`named-element-audit.json` before its local 20-frame OCR check.
[sync_v5.py](sync_v5.py) refuses any unmeasured row, old inferred method, missing boundary
frame or missing/failed frame audit. New ledger rows contain measured acoustic start/end,
source measurement and PNG hashes. They retain pending human listening/full-film acceptance;
automatic geometry checks do not certify pronunciation or continuous-picture quality.

## Bundle import in this linked worktree

The sandbox permits source edits here but cannot write the linked Git metadata under
`/Users/yan/git/market-claim-verifier/.git/worktrees/`. The attempted index write is
retained in [git-worktree-write.log](prep/v5/r3/git-worktree-write.log). Delivery commits
are therefore made on `demo/v5` in a writable temporary clone of `a3440e73`; the bundle
carries that branch. The supplied worktree keeps the exact source changes, and its HEAD
stays at the original commit until the host imports the bundle.

Before the host sequence, while on `demo/v5`, import the commit without discarding files:

```sh
git fetch demo/out/v5-r3.bundle demo/v5
git merge-base --is-ancestor HEAD FETCH_HEAD
git reset --mixed FETCH_HEAD
```

The ancestry check must pass before the reset. The mixed reset advances the branch/index;
it preserves working files, including any later host recording changes. Existing untracked
assets and run records are not added to the delivery commit.

## Host sequence

Run this exact order. Do not repeat the single live check because a later voice or render
step fails; retain and repair/reuse its capture. No `--force` is needed for voice: unchanged
single-sentence sources are read from cache. Preserve previous review directories first.

```sh
export UV_CACHE_DIR=/private/tmp/mcv-v5-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
: "${LIVE_CHECK_PASSWORD_FILE:?Set this to the existing private password file}"
export LIVE_CHECK_PASSWORD_FILE
git merge-base --is-ancestor c8b09738 main
v5_review_stamp=$(date -u +%Y%m%dT%H%M%SZ)
for v5_review_dir in demo/out/review-v5 demo/out/keyframes-v5; do
  if test -e "$v5_review_dir"; then
    mv "$v5_review_dir" "$v5_review_dir-before-r3-$v5_review_stamp"
  fi
done
uv run --project demo python demo/record_v5.py --preflight
uv run --project demo python demo/record_v5.py --site-ref main --port 8765
uv run --project demo python demo/record_v5.py --check
uv run --project demo python demo/build.py voice --storyboard demo/storyboard-v5.yaml --only v501,v502,v503,v505,v507,v508,v509
uv run --project demo python demo/motion_v5.py --measured
uv run --project demo python demo/motion_v5.py --measured --check
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v5.yaml --out demo/out/keyframes-v5
CLANG_MODULE_CACHE_PATH=/private/tmp/mcv-v5-swift-cache uv run --project demo python demo/review_v5.py --frames demo/out/review-v5
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5
```

The render creates the next versioned MP4/SRT and run receipt. Existing −14±1 LUFS,
≤−1 dBTP and 178 s export limits remain. Independent film review follows the fresh ledger,
actual MP4, captions and native proof; inspect silent holds as well as the 43 spoken rows.

Offline checks (no synthesis, SEC request or paid live check):

```sh
uv run --project demo python demo/motion_v5.py --check
uv run --project demo python -m pytest -q demo/tests
node --test demo/tests/motion.test.mjs demo/tests/motion-v3.test.mjs demo/tests/motion-v4.test.mjs demo/tests/motion-v5.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
UV_CACHE_DIR=/private/tmp/mcv-v5-verify-uv-cache UV_OFFLINE=1 sh scripts/verify.sh
```

Offline logs, including initial failures, are retained in [prep/v5/r3](prep/v5/r3/).
Local Chromium launch failed under the workspace sandbox; the failure is retained in
[browser-first.log](prep/v5/r3/browser-first.log). No paid check, synthesis, new native take,
OCR frame review or final film render was run in this source round. Actual host frame/film
acceptance is outstanding. All new `demo/` text is English; historical records remain intact.
