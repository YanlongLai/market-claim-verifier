# Site round 5 — verbatim corrected drafts

Base: `7153ac4ef767026936b2a156c7fd93ecec2694f3`; delivery branch: `site/r5`.
AI001 remains disabled.

The draft renderer now copies unchanged passages directly from
`corrections.original_text`. Its inline `<del>` and `<strong>` tokens also
retain the exact recorded original and replacement strings. Money compaction
is confined to the edit list and the existing citation/evidence presentations.
An unchanged `$143.1 billion` therefore remains `$143.1 billion`.

The runtime regression reconstructs the corrected draft by reading unchanged
spans and insertions, excluding struck text and edit arrows. It asserts exact
equality with the original code points after applying only the recorded edit
spans. It also checks the complete annotated display and reconstructs the
original from unchanged spans and deletions. Cases cover no edits, two edits,
emoji, combining characters, CRLF, tabs, nonbreaking spaces, literal markup,
repeated amounts and language switches.

Receipt costs use two decimal places, and durations and elapsed offsets use
one decimal place. The saved post receipt is **Model cost: $0.06 · 38.4 s**.
Model trace steps retain their complete event values under **Inspect data**.
The production receipt on `/evidence/` uses the same rounded presentation;
the linked recorded report is preserved. The shared historical cost/time
helpers also use cents and a space before `s`.

[Six rendered EN/zh outputs](rendered-results.json), at 390/768/1280 px,
assert that the corrected draft equals the recorded replacements. Their
accepted r4 citation lines, evidence lines, derivation, unchanged reasons and
trace state match the retained r4 outputs exactly. These are offline DOM
captures, not browser layout measurements.

`/zh/`, the affected JavaScript stamps, the demo Hover source hash and the
preview hash were regenerated. Both saved envelopes rebuild byte for byte.
[Regeneration commands and checks](regeneration.log) retain the exact commands;
no media was generated. The [preservation audit](preservation.log) and
[source hashes](sources.sha256.json) cover the implementation, generated
artifacts and unchanged saved inputs.

Retained validation:

- [Initial regression run](runtime-red-attempt1.log.gz): all ten new cases fail
  against r4, reproducing the draft and precision defects.
- [First full runtime run after the fix](runtime-attempt2.log.gz): 51 passed;
  six existing saved-post assertions still expected compact inline tokens.
  Those assertions now compare with the recorded edit strings.
- [Final runtime run](runtime-green-attempt3.log): **57 passed**.
- [Full verifier execution record](verify-attempt1.json) and
  [output](verify-attempt1.log): `UV_OFFLINE=1 bash scripts/verify.sh` passed.
  **1,269 product tests, 206 demo tests and 97 standalone Node tests passed**;
  figure rebuild/check, both saved envelopes, all three explorer/site outputs,
  wild data, Markdown links and the offline guards all pass.
- [Route audit](routes.log): 38 local paths, zero missing, two runtime routes.
- [Final Markdown link check](links-delivery.log) includes this receipt;
  [both link-check records](links-records.json) retain the preliminary output too.

All checks reuse frozen data. They make no paid model calls or SEC requests
and do not retest OCR/ASR.
