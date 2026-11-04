# Demo v5 round 4 — the three v018 blockers

Source base: `demo/v5` at `2d20f823`, following
`demo/out/review-v5/AI2-REVIEW-v018.md`. This round addresses B1–B3 only.
AI001 remains disabled. Narration, sentence WAV identities, chapter labels and the ten
cuts remain unchanged: 0 / 8 / 20 / 32 / 46 / 58 / 116 / 138 / 154 / 170 / 178 s,
1920×1080, 30 fps. The retained v018 take, film, SRT, ledger and review remain evidence
of that failed run; they are not acceptance evidence for round 4.

- **B1:** the verdict card holds both Apple SEC E3 component citations, projected from
  the result JSON and checked against the correction links: **10-K · fiscal 2025 annual**
  and **10-Q · nine months to 28 Jun 2025**. Both use the other cards' 56 px type scale.
  The native verdict stays above the card. Each boundary frame audit now requires the
  native verdict plus both filing forms, periods and SEC URLs; `v505-04` names both
  verdict and filing in its required visual. A verdict-only audit cannot make a ledger.
- **B2:** the recorder is **capture v9**. Before framing each state it finds a clean
  card edge while keeping the native proof whole. It measures surrounding text lines
  with DOM Ranges and whole form controls, including Reset/count, rather than checking
  only the named rectangle. At every named cue onset it rejects any line/control
  crossing the card edge. The verdict also requires the input-reading charge wholly
  above the viewport and the complete corrected-draft heading visible or masked.
  Captured line rectangles are retained and rechecked in review frames. Lower live
  masks now end exactly at the chapter band, **y=790**. The centred 1560 px workspace
  and 1:1 native playback remain. The old v8 take cannot pass the new export gate.
- **B3:** capture waits for decoded video data, including at time zero, and draws those
  pixels to a full-size canvas before the screenshot. It retains the valid image until
  the next decoded seek is ready. Every live frame audit requires that decoded image.
  Full render also checks the **actual encoded master** at frames **4619–4622** against
  the outgoing render and native take. Frame 4619 is still Results at 153.967 s; the
  unchanged cut requires the native page from frame 4620 (154.000 s) through 4622.
  A dark first frame fails export before a versioned deliverable is produced.

[The encoded-frame baseline check](prep/v5/r4/ending-v018-baseline.json) detects exactly
v018's bad frame 4620 (mean RGB error 209.41/255); frames 4621–4622 pass at <0.66/255.
This recheck uses retained video, not a new live check or OCR/ASR test. The extracted
frames remain in `/private/tmp/mcv-v5-r4-ending-v018-baseline-r2`.

## Bundle import in this linked worktree

The linked Git metadata is outside the writable sandbox, as recorded in
[the prior write failure](prep/v5/r3/git-worktree-write.log). Delivery commits are on
`demo/v5` in a writable temporary clone starting from `2d20f823`; the supplied source
worktree keeps the same changes. The bundle transports the branch without adding
existing untracked media or run records. On the host, while on `demo/v5`:

```sh
git fetch demo/out/v5-r4.bundle demo/v5
git merge-base --is-ancestor HEAD FETCH_HEAD
git reset --mixed FETCH_HEAD
```

The ancestry check must pass before the mixed reset. This advances the branch/index
while preserving working files, including any later host recording changes.

## Host sequence

Re-record once, then reuse that take if a later step fails. Preserve all prior attempts
and review directories. The existing 43 sentence WAVs are reused; no voice synthesis or
narration edit is needed. Run these commands in order after importing the bundle:

```sh
export UV_CACHE_DIR=/private/tmp/mcv-v5-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
: "${LIVE_CHECK_PASSWORD_FILE:?Set this to the existing private password file}"
export LIVE_CHECK_PASSWORD_FILE
git merge-base --is-ancestor c8b09738 main
v5_review_stamp=$(date -u +%Y%m%dT%H%M%SZ)
for v5_review_dir in demo/out/review-v5 demo/out/keyframes-v5; do
  if test -e "$v5_review_dir"; then
    mv "$v5_review_dir" "$v5_review_dir-before-r4-$v5_review_stamp"
  fi
done
uv run --project demo python demo/record_v5.py --preflight
uv run --project demo python demo/record_v5.py --site-ref main --port 8765
uv run --project demo python demo/record_v5.py --check
uv run --project demo python demo/motion_v5.py --measured
uv run --project demo python demo/motion_v5.py --measured --check
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v5.yaml --out demo/out/keyframes-v5
CLANG_MODULE_CACHE_PATH=/private/tmp/mcv-v5-swift-cache uv run --project demo python demo/review_v5.py --frames demo/out/review-v5
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5
```

Render automatically retains `ending-cut/check.json` and the four actual encoded cut
frames in its new motion cache folder; its run receipt includes that check. For a
separate recheck of the newly exported film, substitute its versioned path below and
use a new output directory if this one exists:

```sh
uv run --project demo python demo/check_ending_v5.py --film demo/out/demo-v019.mp4 --out demo/out/review-v5/ending-cut
```

The next export keeps the 178 s, −14±1 LUFS and ≤−1 dBTP gates. Independent film review
must inspect both B1 referents throughout “Contradicted, with the filing,” the surrounding
native text at each cue's onset/end, silent holds, and encoded frames 4619–4622. The fresh
43-row ledger still requires human listening and full-duration picture acceptance.

Offline checks (no synthesis, SEC request or paid live check):

```sh
uv run --project demo python demo/motion_v5.py --check
uv run --project demo python -m pytest -q demo/tests
node --test demo/tests/motion.test.mjs demo/tests/motion-v3.test.mjs demo/tests/motion-v4.test.mjs demo/tests/motion-v5.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
UV_CACHE_DIR=/private/tmp/mcv-v5-verify-uv-cache UV_OFFLINE=1 sh scripts/verify.sh
```

Round-4 validation logs, including initial failures, are retained in [prep/v5/r4](prep/v5/r4/).
The guarded `UV_OFFLINE=1` verifier passes: 1,269 product tests, 310 demo Python tests,
133 Node tests, figure/data rebuilds and Markdown links. Narration and timing hashes
are recorded unchanged in [unchanged-timing.json](prep/v5/r4/unchanged-timing.json).
Local Chromium cannot launch under this workspace sandbox; the permission failure is
retained in [browser-launch.log](prep/v5/r4/browser-launch.log). No new live check, voice,
native take or full film was produced in this source round. Host re-recording and final
film acceptance remain pending. All new text is English.
