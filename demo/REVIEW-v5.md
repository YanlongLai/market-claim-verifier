# Demo v5 implementation and host handoff

Binding source: `DESIGN-final.md` sections 4, 6 and 10, whose path and SHA-256 are retained in
[director-source.json](prep/v5/director-source.json). Round 2 starts from host commit `f631b4c3` on `demo/v5` (`fa6a356f` plus the host
measured narration edits). AI001 remains disabled.

Round 2 fixes the seven host findings in source. The host's v500/v504 narration, every cue
onset, all ten cuts, live take bytes, voice cache and recorder choreography holds are retained.
The committed motion data/SRT retain **measured host timing**. Portable measured metadata in
[motion/v5/inputs.json](motion/v5/inputs.json) lets the offline compiler reproduce those values
without the private voice or video cache; it does not approve a take for export.

The current v6 take remains wired for traceability. **It must be re-recorded:**
`record_v5.py --check` deliberately rejects it because its startup is not covered. Capture v7
injects an opaque paper cover in the document head before any site content can paint, then
releases it only after capture CSS, 1.95 zoom, English sanitation and centred geometry pass.
The receipt records the pre-content cover, opaque computed style, release time and audit index.
Every later geometry audit must retain 1.95 zoom. Review/keyframes/render require this gate,
so an old un-zoomed opening cannot be exported. This keeps the continuous take and all hold
lengths; no phase offset or speech timing change is needed for the cover.

No recorder, synthesis, browser frame capture, OCR review or film render was run for this
round. Offline check evidence, including initial failures, is in [prep/v5/r2](prep/v5/r2/).
The earlier [AI2 source review](prep/v5/ai2-source-review.md) records round 1 only; fresh actual
frame and film acceptance belongs to the host sequence below.

| Scene | Film time | Seconds | Picture |
| --- | --- | ---: | --- |
| v500 | 0:00–0:08 | 8 | Animated DappGo intro and disclosure |
| v501 | 0:08–0:20 | 12 | Eight HTML post cards, including the original; no counter |
| v502 | 0:20–0:32 | 12 | Screenshot, PDF, Audio and Video tiles |
| v503 | 0:32–0:46 | 14 | Literal saved terminal rows, reflowed above the rail |
| v504 | 0:46–0:58 | 12 | Reused architecture SVG with timed web reveals |
| v505 | 0:58–1:56 | 58 | One real check; seven receipt-bound explanations |
| v506 | 1:56–2:18 | 22 | Sentence-bound saved terminal batch replay |
| v507 | 2:18–2:34 | 16 | Reused results: 90.2%, 1/139, $0.02, 10 s |
| v508 | 2:34–2:50 | 16 | Native corrected edit and both SEC filing links |
| v509 | 2:50–2:58 | 8 | Site robot stamp, URL, Meta/Baseten credit and DappGo |

All ten cuts are fixed; total **178.000 seconds**, 1920×1080, 30 fps. Narration words are in
[NARRATION-v5.txt](NARRATION-v5.txt); cue placement is in [the storyboard](storyboard-v5.yaml).
Unchanged narration uses the existing v402/v403/v408/v409 cache paths read-only.
The tightened host v500/v504 takes already fit their 8/12 s cuts. No cue words changed in
round 2, so voice synthesis is unnecessary unless the host edits narration again. Compilation
still rejects any measured cue that exceeds its new live phase window; it retains the source
and never accelerates or cuts speech. Intro disclosure and the architecture headline are
rendered directly from each scene's `on_screen`; exact-copy tests exercise the renderer and
SVG compiler, and the real frame audit compares every `data-on-screen` node with the storyboard.

The live overlays are HTML/CSS/JS cards, at the exact recorded phase onset:

| Receipt phase | Overlay |
| --- | --- |
| `use_apple_example` | 1 · Paste the post |
| `check_against_sec` | 2 · Muse Spark calls SEC tools (live) |
| `verdict_reveal` | 3 · Verdict: CONTRADICTED |
| `draft_reveal` | 4 · Corrected draft: $416.2B → $102.5B |
| `evidence_reveal` | 5 · SEC evidence: 10-K annual $416.2B − 10-Q nine months $313.7B = $102.5B |
| `agent_trace_expand` | 6 · Agent trace: 4 tool calls · actual model ID |
| `hover_receipt` | 7 · Receipt: actual cost and elapsed time |

Each cue's audio and overlay share the same receipt timestamp. Preview phase times are
labelled planning values, replaced when the host recorder wires its new receipt. Trace
expansion, all four tool calls, program verdict and the native Apple derivation inspector
remain mandatory. Ending validation checks the native corrected edit and the two actual
10-K/10-Q correction-citation URLs together in view throughout the held segment.

[record_v5.py](record_v5.py) and [record_v5.mjs](record_v5.mjs) retain one continuous source,
with at most one `/api/check` or `/api/check-example` POST, no retry and separate ending
extraction. Capture zoom is 1.95; the 800-CSS-pixel workspace spans 1560 pixels. Every audit
requires width ≥1500, both margins ≥60 and their difference ≤4 pixels. Playback has no
transform, crop or zoom. The language switch is removed and a mutation observer removes
rendered CJK text nodes/attributes. Language and geometry audits are stored throughout
capture. Native trace steps stay above y=548. Live cards occupy y=558–784; the three-part SEC
equation also uses y=558–784, with its three filing labels above the amounts. Key amounts/counts use 96 px; headings and supporting labels use
56 px. The ending uses its separate y=610–718 card, below the held draft and both filings.
Receipts retain native element rectangles at every cue onset and each trace-step reveal.
The frame audit checks overlay, rail and caption rectangles against those named elements;
any intersection fails. Exact onset frames are included in the review/keyframe plans.

The chapter rail spans the full width at **y=844–856**, 12 pixels tall. Its ten segments are
sized by `[8,12,12,14,12,58,22,16,16,8] / 178`; each fills linearly on the film clock. Labels
are ≥32 pixels at y=796, with the current label highlighted. The opaque band covers y=790–1080; non-live scenes clip at y=766, leaving 24 px clearance.
Labels keep at least 24 px to each side (48 px between neighbours), and the ninth label is
**Fix**. The same spacing and opacity checks run on every host frame. Captions use ≤2×42 English characters, in the existing
**y=880–1016** safe lane, leaving at least 24 pixels below the rail.

The four inputs were copied byte-for-byte from the main checkout's `docs/examples/a.*`.
[Their receipt](assets/examples-v5/receipt.json) includes source hashes and preview commands.
The PDF preview is its actual first page; audio waveform bins come from `a.mp3`; the video
preview is an actual frame of `a.mp4`. Post cards use the same retained `a.txt` story.
[Terminal receipts](assets/terminal-v5/) preserve the r5 source hashes and every re-cut range.
Comparison blocks occur at local 0/3.5/9 seconds, matching separate locked-word voice cues.
Batch blocks occur at local 0/5/8/11/15.5 seconds: CoreWeave T03 verdicts; OCR; ASR;
measured median; sequential projection. The `run` block uses the retained beat7 asciicast
range **4.02–5.80 s**, whose visible rows are FY2024 SUPPORTED, FY2025 CONTRADICTED
($51.31B → $5.131B), and FY2023 CONTRADICTED ($2.29B → $229M). It preserves the real
last-line keystrokes and holds the final rows through 5 s. Failed/unchecked batch rows remain
in the original evidence and are outside this excerpt. Both terminal scenes now decode the
hash-checked saved PTY events directly as web text; old MP4s and casts remain untouched.
Source footer row 12 is omitted from playback, and the storyboard's saved label is 56 px at
y=684–749, above the band with more than 24 px clearance. No media rebuild is needed.

The outro uses the site's H robot stamp / stamp-down / approve assets and hero pose timing,
compressed to a deterministic 1.6 s web sequence. URL, built-with credit and wordmark remain;
the disclosure is confined to the intro. No Wan asset or media insert appears in v5.

Run these commands from the video worktree on the host. Keep the existing private
`LIVE_CHECK_PASSWORD_FILE` setting; no password belongs in a command or receipt.

The delivery sandbox could not create the shared worktree's Git `index.lock`. Commits
are therefore prepared on `demo/v5` in a writable temporary clone and supplied in
`demo/out/v5-r2.bundle`. The shared host branch is unchanged. Adopt the bundle first;
`--mixed` advances the branch/index while preserving every working file, including the
host's existing build-log edits and untracked run records:

```sh
git fetch demo/out/v5-r2.bundle refs/heads/demo/v5 &&
  test "$(git branch --show-current)" = demo/v5 &&
  git merge-base --is-ancestor HEAD FETCH_HEAD &&
  git reset --mixed FETCH_HEAD
```

```sh
cd /Users/yan/git/market-claim-verifier-video
export UV_CACHE_DIR=/private/tmp/mcv-v5-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
: "${LIVE_CHECK_PASSWORD_FILE:?Set this to the existing private password file}"
export LIVE_CHECK_PASSWORD_FILE
# main must include the trace-code contrast fix from the host review.
git merge-base --is-ancestor c8b09738 main
# Retain round-1 frame/OCR evidence before reusing these output directories.
v5_review_stamp=$(date -u +%Y%m%dT%H%M%SZ)
for v5_review_dir in demo/out/review-v5 demo/out/keyframes-v5; do
  if test -e "$v5_review_dir"; then
    mv "$v5_review_dir" "$v5_review_dir-before-r2-$v5_review_stamp"
  fi
done
uv run --project demo python demo/record_v5.py --preflight
uv run --project demo python demo/record_v5.py --site-ref main --port 8765
uv run --project demo python demo/record_v5.py --check
# Only if cue words changed; none changed in round 2:
# uv run --project demo python demo/build.py voice --storyboard demo/storyboard-v5.yaml --only v500,v503,v504,v505,v506,v509
uv run --project demo python demo/motion_v5.py --measured
uv run --project demo python demo/motion_v5.py --measured --check
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v5.yaml --out demo/out/keyframes-v5
CLANG_MODULE_CACHE_PATH=/private/tmp/mcv-v5-swift-cache uv run --project demo python demo/review_v5.py --frames demo/out/review-v5
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5
```

The recorder command makes **one live check**, shared by both live scenes. Do not rerun it
because a later voice/render step fails; retain and reuse the captured receipt. The final
render writes the next versioned `demo/out/demo-vNNN.mp4`, SRT and run record. Existing
mastering enforces −14±1 LUFS and ≤−1 dBTP; v5 also rejects an export over 178 seconds.
The local Vision OCR command checks 20 actual captioned review PNGs covering all beats and
all seven live overlays; its receipt is `demo/out/review-v5/ocr-20.json`. Frame review includes
every beat boundary, every phase, five chapter sample times, every sentence/phrase start and
end, and the final encoded frame.

**AI2 follows the host render**: review the actual MP4, keyframes, `review-v5/index.json`,
`ocr-20.json`, fresh live receipts, loudness report and the completed `sync-ledger.json` against
sections 10–11 before Owner review. The ledger command prepares sentence/phrase rows with
cue start/end, required visual, and start/end review frames. It never marks a row verified.
Cue-unit onsets and lengths are measured; boundaries within a unit are proportional estimates.
Listen to the actual MP4, enter actual sentence start/end and the full visible interval, supply a
verified frame and reviewer for every row, and mark pass/blocker. A referent missing for any
part of its sentence is a blocker; picture may lead by at most 0.5 seconds and may never lag.
In particular, verify the three comparison transitions, the complete trace clause, all batch
sentences and the final result hold against the actual recording clock. Inspect silent holds too.
Round-1 source review does not approve this new frame plan or an unrendered film.

Offline checks (no browser, synthesis or live request):

```sh
uv run --project demo python demo/motion_v5.py --check
uv run --project demo python -m pytest -q demo/tests
node --test demo/tests/motion.test.mjs demo/tests/motion-v3.test.mjs demo/tests/motion-v4.test.mjs demo/tests/motion-v5.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
UV_CACHE_DIR=/private/tmp/mcv-v5-verify-uv-cache sh scripts/verify.sh
```

The default `--check` uses retained measured metadata and is portable without private caches.
After a new take, run `--measured` to refresh the receipts and measured compilation, then use
`--measured --check` while the host caches are available. Neither check synthesizes audio.
The exported film still requires actual video files, hashes, v7 startup proof and named-element
rectangles; portable metadata cannot bypass the final take gate.

The `demo/` text sources contain no literal CJK. Exact earlier source records are preserved in
[the language-history archive](../docs/evidence/demo-language-history/2026-11-04/README.md).
Legacy executable strings use lossless Unicode escapes; the older v2 metadata/shot-list
descriptions use English. Financial values, narration, take bytes and voice identities remain
intact. The new v5 DOM has its own English-only frame and host OCR gates.
