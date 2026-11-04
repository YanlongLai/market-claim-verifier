# Demo v5 implementation and host handoff

Binding source: `DESIGN-final.md` sections 4, 6 and 10, whose path and SHA-256 are retained in
[director-source.json](prep/v5/director-source.json). Base: `03d29e51` (`demo/v4` r5).
The worktree was already on `demo/v5` at that commit. AI001 remains disabled.

This delivery implements the source and prepares the terminal clips and real input previews.
The committed motion data/SRT are an **unmeasured layout preview**. A new v5 live take,
retimed voice synthesis, browser frame review, final loudness measurement and rendered-film
AI2 acceptance still run on the host. No new live check, OCR/ASR product execution, voice
synthesis or full-film render was performed during implementation. Failed preflights and
intermediate test results are retained under [prep/v5](prep/v5/).

| Scene | Film time | Seconds | Picture |
| --- | --- | ---: | --- |
| v500 | 0:00–0:08 | 8 | Animated DappGo intro and disclosure |
| v501 | 0:08–0:20 | 12 | Eight HTML post cards, including the original; no counter |
| v502 | 0:20–0:32 | 12 | Screenshot, PDF, Audio and Video tiles |
| v503 | 0:32–0:46 | 14 | Re-cut saved terminal comparison |
| v504 | 0:46–0:58 | 12 | Reused architecture SVG with timed web reveals |
| v505 | 0:58–1:56 | 58 | One real check; seven receipt-bound explanations |
| v506 | 1:56–2:18 | 22 | Sentence-bound saved terminal batch replay |
| v507 | 2:18–2:34 | 16 | Reused results: 90.2%, 1/139, $0.02, 10 s |
| v508 | 2:34–2:50 | 16 | Native corrected edit and both SEC filing links |
| v509 | 2:50–2:58 | 8 | DappGo outro, URL and Meta/Baseten credit |

All ten cuts are fixed; total **178.000 seconds**, 1920×1080, 30 fps. Narration words are in
[NARRATION-v5.txt](NARRATION-v5.txt); cue placement is in [the storyboard](storyboard-v5.yaml).
Unchanged narration uses the existing v402/v403/v408/v409 cache paths read-only.
Retimed v500/v503/v504/v505/v506 and new v509 synthesize into separate v5 cue paths. Measured
voice must fit every cue window. The old disclosure (8.24 s) and architecture (13.84 s) cannot
be reused within the new 8/12 s cuts. If newly synthesized cues overrun, compilation fails,
retains their source audio and requires a timing decision. It never speeds up or cuts speech.

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
equation uses y=486–782. Key amounts/counts use 96 px; headings and supporting labels use
56 px. The ending uses its separate y=610–740 card, below the held draft and both filings.

The chapter rail spans the full width at **y=844–856**, 12 pixels tall. Its ten segments are
sized by `[8,12,12,14,12,58,22,16,16,8] / 178`; each fills linearly on the film clock. Labels
are ≥32 pixels at y=796, with the current label highlighted. Labels shift within adjacent
spare space to avoid overlap. Captions use ≤2×42 English characters, in the existing
**y=880–1016** safe lane, leaving at least 24 pixels below the rail.

The four inputs were copied byte-for-byte from the main checkout's `docs/examples/a.*`.
[Their receipt](assets/examples-v5/receipt.json) includes source hashes and preview commands.
The PDF preview is its actual first page; audio waveform bins come from `a.mp3`; the video
preview is an actual frame of `a.mp4`. Post cards use the same retained `a.txt` story.
[Terminal receipts](assets/terminal-v5/) preserve the r5 source hashes and every re-cut range.
Comparison blocks occur at local 0/3.5/9 seconds, matching separate locked-word voice cues.
Batch blocks occur at local 0/5/8/11/15.5 seconds: post→claims→calls→verdicts; OCR; ASR;
measured median; sequential projection. Native typed pixels are retained; extra reading time
holds the last frame. These are saved replays and do not retest OCR/ASR or measure a new batch.
No Wan asset or lower-right media insert appears in v5.

Run these commands from the video worktree on the host. Keep the existing private
`LIVE_CHECK_PASSWORD_FILE` setting; no password belongs in a command or receipt.

```sh
cd /Users/yan/git/market-claim-verifier-video
export UV_CACHE_DIR=/private/tmp/mcv-v5-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
: "${LIVE_CHECK_PASSWORD_FILE:?Set this to the existing private password file}"
export LIVE_CHECK_PASSWORD_FILE
uv run --project demo python demo/record_v5.py --preflight
uv run --project demo python demo/record_v5.py --site-ref main --port 8765
uv run --project demo python demo/record_v5.py --check
uv run --project demo python demo/build.py voice --storyboard demo/storyboard-v5.yaml --only v500,v503,v504,v505,v506,v509
uv run --project demo python demo/motion_v5.py --measured
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
The independent [AI2 source review](prep/v5/ai2-source-review.md) passes; it does not
approve an unrendered film.

Offline checks (no browser, synthesis or live request):

```sh
uv run --project demo python demo/motion_v5.py --check
uv run --project demo python -m pytest -q demo/tests
node --test demo/tests/motion.test.mjs demo/tests/motion-v3.test.mjs demo/tests/motion-v4.test.mjs demo/tests/motion-v5.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
UV_CACHE_DIR=/private/tmp/mcv-v5-verify-uv-cache sh scripts/verify.sh
```

After host preparation, compiler freshness uses `motion_v5.py --measured --check` instead
of the unmeasured preview check. Full offline verification uses the committed source preview.
The broader demo test run exposed stale v4 test fixtures, now aligned with the already
committed r5 narration/trace phase. No v4 production code, historical takes, unchanged voice
files or v3 motion files were edited by this implementation.
