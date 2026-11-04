# Round-8 retained records

Base: `32d979b6`, `demo/v5`, after the round-7 host export v023.
[Baseline](baseline.json) records initial source, recording and cue hashes.
The corresponding `.before` files preserve original inputs and review notes.
AI001 remains disabled.

The [source and voice proof](source-and-voice-proof.json) confirms unchanged
recordings, receipts, the first nine scenes, their timing and all evidence/replays.
Only `v509-credit` has a new WAV: **47 other units** are reused byte for byte.
Both local Breeze attempts use the existing pinned clone, seed and parameters;
the existing r7 temporary wrapper redirects only the Numba compilation cache.

The full requested line is retained locally with its [engine receipt](voice-full-receipt.json).
Its 5.44 s WAV succeeded; the first voice command then failed on the existing
comma/phrase validator. After provider-list sentence handling was corrected,
`compile-full.log` rejected that duration because the stamp would hit the fade.
The separately synthesized owner-authorized shorter line has its own
[receipt](voice-short-receipt.json) and successful `voice-short-attempt-01.log`.
Audio stays in the ignored cache. No paid verifier request, SEC request, OCR,
ASR or new recording was performed.

[Font geometry](font-geometry.json) checks text widths and source line dimensions.
[The 370-frame plan](review-plan.json) is prepared, with no PNG approval claimed.
Headless Chromium failed to launch; native Chrome computer-use approval was
rejected. [Review limits](computer-review.json) and the actual launch log retain
those failures. No new rendered film or listening approval is claimed. The
previous host v023 receipt is retained unchanged for the historical export link.

Focused Python/Node, measured-compile and full offline logs are retained here,
including failed and partial invocations. These checks do not retest OCR/ASR.
The full guarded command is `UV_CACHE_DIR=/private/tmp/claimcheck-verify-uv-cache
UV_OFFLINE=1 sh scripts/verify.sh`. The first invocation started before this
README was present; its link/anchor failures are retained separately. The working-tree
link scan also includes ignored historical review/cache files with existing external
file references. The final disposable source-copy check excludes those artifacts.

The source worktree's Git metadata is outside the writable roots; its index write
was denied (see `git-index-attempt.log`). A disposable clone creates the delivery
commit on `demo/v5`, with the requested Claude Fable 5.1 co-author footer, then
exports `demo/out/v5-r8.bundle`. The host can import that commit without changing
or deleting prior run records. See [the current review note](../../../REVIEW-v5.md)
for the remaining host rendering commands.

Final guarded result: **1,269 product tests, 333 demo Python tests and 140 Node
tests pass**, with figures, stored-data rebuilds and Markdown links green.
`offline-verify-final.log` was run from the clean delivery copy with network guards
and no media/model/provider calls. The delivery source and compiler outputs match
the checked copy; later additions only retain these results and delivery records.

The frozen original SRT keeps its standard trailing blank separator. The raw
whitespace check flags only that archived EOF; all other staged files pass.
