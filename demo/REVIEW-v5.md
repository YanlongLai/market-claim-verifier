# Demo v5 round 6 — real online and local traces

Base: `demo/v5` at `4f65cf54` (host v021). This is a **source delivery pending a new
host capture and render**. Chromium cannot launch inside this session's macOS
sandbox; Computer Use also denied Chrome access. No paid request or voice synthesis
was made. [Preflight record](prep/v5/r6/host-preflight.json). AI001 remains disabled.

The existing v021 MP4, recordings, generated timeline and bundle are retained as
historical outputs. They do **not** show r6. The preview entry refuses stale r5 data;
production compilation and `record_v5.py --check` reject the old take because it has
no real server-log JSONL. No response-event or synthetic fixture substitutes for it.

## Online

The recorder starts **main checkout** `scripts/tail_live_log.py` before Chromium and
the POST, with `DAPPGO_HA_SUDO_FILE`. It retains
`demo/cache/live-takes/v5/serverlog-<stamp>.jsonl`, its full spool, diagnostics and ID
file next to the take. After the response, it atomically saves `request_id`. Until
Pages forwards that field, it can select the **only** `live id=` in the POST window,
using the retained Kubernetes source timestamps to exclude the 30-second pre-roll.
Multiple IDs fail closed. Partial attempts remain; there is no automatic paid retry.
Both take receipts retain the selected log's SHA-256, request ID, ID source and
main helper hash. Carry that exact selected JSONL when moving the new scene to
another checkout; portable response metadata is deliberately insufficient. `--check` requires that exact file and a complete matching verdict.

The terminal title is **Online · hackathon.dappgo.com · server log**, with footer
**live request <8-character prefix> · pod log**. The command is retained. Every public
log row appears at `check_against_sec + runner elapsed`; JSONL host arrival times and
response events do not position rows. Display-only condensation keeps time, event,
ticker, metric, period and evidence ID in fixed columns. Public model-running
notifications read “model reasoning (Muse Spark)” with their recorded step; this is
a progress label, not access to private reasoning. The film-clock stopwatch freezes
on the real `event=verdict`. The terminal holds through native result arrival and
yields only when card 3 is ready.

## Local

[local-cli.json](assets/cli-v5/local-cli.json) is a byte-identical copy of main's
`runs/real-trace-001/local-cli.json`; [receipt](assets/cli-v5/receipt.json) retains
its source/copy SHA-256, input hash and original report hashes. It is a completed,
non-dry-run **38.571843 s** recording from 2026-11-04: **2 supported, 1 contradicted,
1 not checked**, measured total **$0.061142** (displayed **$0.0611**).

The window title is **Local · CLI · recorded 2026-11-04**. Its typed shell command
comes from the session's `command`, wrapped with shell continuations. Completed
PTY chunks, including partial lines and report JSON, follow their original
`t_rel_s` and reflow at 98 columns; the final counts/cost come
from that session. The compiler chooses the smallest integer replay speed that
fits the measured run picture window, reserving 0.6 s for typing and at least
0.4 s for its final receipt. The muted footer explicitly says **replayed at N×**.
No speed is claimed before the changed narration is measured.

Only `v506/run` changes words: “The same check runs locally from the command line.”
`voice --only v506` reuses the other four cached cue WAVs. OCR and ASR keep their
saved-replay labels and sources. The old CoreWeave run rows are removed from the
compiled run block.

## Readability and AI2 leftovers

Both terminals use **28 px monospace, 34 px line pitch, five scrolling rows plus
header**, with 28 px titles, clocks and muted footers. Older rows leave at the top;
text never shrinks. The online window keeps **x=80–1840, y=558–790**; the local
window uses the same 1760 × 232 style above its scene caption.

B1: a fully opaque backplate covers **x=0–1920, y=558–790**, including both side
gutters. During the recorded password-form state it begins at **y=530**. The real
field, button, native SEC status, cover calibration, card-band and named-element
checks remain. Every rendered Chromium frame audits the whole backplate and named
proof clearance; review keyframes add silent one-second samples and cue-edge
neighbors. The export also decodes **every live-scene frame** to check both outer
gutters and the higher password mask, preserving a `composite.json` receipt and
rejecting native glyph leaks. Actual whole-film visual acceptance remains pending.

B2: `v503-02.required_visual` now reads **“SEC tools + Python verdict heading;
357 claims · corrected gold · includes dev qualifier”**. The score remains on
`v503-03`. The median footer is **78 attempts · 72 completed · median 6.8 s**.
“Illustrative post” uses the card's 30 px byline/body scale.

<!-- actual-encode:start -->
Actual existing encode: **v021**, 178.000 s; **−14.20 LUFS integrated**, **−1.23 dBTP**.
These are fresh FFmpeg measurements of `demo/out/demo-v021.mp4`, not r6 estimates.
[Measurement receipt](prep/v5/r6/v021-actual-loudness.json) ·
[raw measurement](prep/v5/r6/v021-actual-loudness.log). **R6 encode pending.**
<!-- actual-encode:end -->

## Host sequence

Run from this worktree after importing the `demo/v5` bundle. Keep the existing
password files private. The recorder writes the new log directly next to the new
take; it never writes credentials into receipts. Retain old review directories.

```sh
export UV_CACHE_DIR=/private/tmp/claimcheck-verify-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
export LIVE_CHECK_PASSWORD_FILE="$HOME/secret/live-check-password.txt"
export DAPPGO_HA_SUDO_FILE="$HOME/secret/dappgo-ha-cp-1.txt"

uv run --project demo python demo/record_v5.py --preflight
uv run --project demo python demo/record_v5.py
uv run --project demo python demo/record_v5.py --check
uv run --project demo python demo/build.py voice --only v506 --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/motion_v5.py --measured
uv run --project demo python demo/motion_v5.py --measured --check

v5_review_stamp=$(date -u +%Y%m%dT%H%M%SZ)
for v5_review_dir in demo/out/review-v5 demo/out/keyframes-v5; do
  if test -e "$v5_review_dir"; then
    mv "$v5_review_dir" "$v5_review_dir-before-r6-$v5_review_stamp"
  fi
done
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v5.yaml --out demo/out/keyframes-v5
CLANG_MODULE_CACHE_PATH=/private/tmp/mcv-v5-swift-cache uv run --project demo python demo/review_v5.py --frames demo/out/review-v5
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5
```

A short take that cannot hold every existing checking sentence with the 0.4 s
margin fails the measured gate. Retain it and repair timing; never invent a longer
server run or retry automatically. The 178 s limit, −14±1 LUFS / ≤−1 dBTP gate and
encoded 154 s cut check remain. A successful full r6 render updates the actual-encode
block above from its measured export, then the sync ledger awaits listening and
continuous-picture review.

[Round-6 test records](prep/v5/r6/) retain failures and subsequent results. Synthetic
online logs live only under test fixtures and are never film inputs. Offline tests
exercise the new pipeline without SSH, model calls, SEC fetches or private media.
The full guarded verification result is recorded there; capture, new voice,
frame inspection, r6 export and listening still require the host sequence above.

Final guarded verification: **1,269 product tests, 332 demo Python tests and 138
Node tests pass**, with figure/data rebuilds and links green
([full log](prep/v5/r6/offline-verify-final.log)).
