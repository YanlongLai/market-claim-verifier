# Round-7 retained records

Base: `ed71ce698f779f4fcf17fa8228de08578c04fc6e`, branch `demo/v5`.
The [supplied AI2 v022 review](AI2-REVIEW-v022.md.before) and previous inputs,
timing, cues and ledger are retained verbatim. Earlier paid attempts and media
remain untouched. AI001 remains disabled.

The [source bindings](source-bindings.json) map the online rows to real log indices
and local condensed pairs to original CLI events. [Before](source-hashes-before.json)
and [after](source-hashes-after.json) hashes confirm the same take, log, receipts
and session. The log's first call is +2.69 s, its start count is a zero placeholder,
preprocessing records 321 characters, and it contains six program checks. The
brief's +4.3 s, 322 characters and five checks are not written into the evidence.

The [measured cue plan](sync-ledger-plan.json) has 48 rows. It corrects v506-01 to
require command typing and timestamped progress; the final local receipt is a
separate 129.433–138 s hold. [Font measurements](font-metrics.json) check 30 px Menlo,
36 px pitch, five rows, header fit and unwrapped body text. These are source and
font measurements, not actual browser frames or encoded-picture approval.

Only two voice units were synthesized, as recorded in [voice proof](voice-proof.json):
the whole-request clock sentence and "Four tool calls." All other units reuse
their caches. Audio remains local and is not redistributed. Attempts 1 and 2
failed because the engine forced a Numba cache outside writable paths. Attempt 3
used the [cache redirection](voice-cache-redirect.json), synthesized both units,
then encountered an in-progress compiler edit. The subsequent measured compile
uses those completed, hash-checked units. Every failed attempt and engine log is
retained; there was no new paid claim check, SEC request, OCR, ASR or recording.

Headless Chromium could not launch: [probe failure](layout-probe-attempt-01.log).
The previous v022 export, review frames and signed/pending ledger are retained;
none is relabelled as round 7. Actual r7 frames, export, OCR, listening and
continuous-picture review remain host work. Use the new directories in
[REVIEW-v5.md](../../../REVIEW-v5.md); no re-record is needed.

The full guarded check is `UV_OFFLINE=1 sh scripts/verify.sh`; its final log is
retained here as `offline-verify-final.log`. Focused Python and Node logs retain
the initial failures and subsequent passes. New Node regressions inspect every
spoken wait-window frame and reject the original review's premature-call and
premature-decision cases. They also reject missing count/evidence rows and small
or overlapping source labels. These checks do not retest product OCR or ASR.

Final guarded result: **1,269 product tests, 332 demo Python tests and 140 Node
tests pass**, with figure/data rebuilds and links green. Exactly **46 of 48** voice
unit hashes are unchanged ([reuse check](voice-reuse-check.json)). The baseline
clean clone had one broken link to the untracked v022 export receipt; the delivery
also retains that existing receipt unchanged so a fresh clone has its evidence.
