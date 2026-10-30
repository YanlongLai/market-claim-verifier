# Test records and reuse

Retain every paid attempt, including failed extraction, provider errors, abstentions and budget stops. Never overwrite an earlier run or silently replace it with a better result. Saved outputs are replay evidence, not a fresh live run.

## Evidence index

| Record | Purpose and boundary |
|---|---|
| [Original 357-claim evaluation](evidence/eval-v2-2026-10-27/REPORT.md) | Six systems; retained requests, outputs, gold and manifests |
| [Post-hoc evaluation](evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md) | Same claims after fixes; not a new held-out benchmark |
| [Aborted early evaluation](evidence/eval-2026-10-27-aborted-partial/) | Incomplete attempts remain available |
| [L4 issuer-release evaluation](evidence/eval-l4-2026-10-29/REPORT.md) | 32 claims; retained miss and cost |
| [Initial media probes](evidence/multimodal-2026-10-29/) | Original synthetic fixtures and baseline outputs |
| [Media hardening probes](evidence/multimodal-2026-10-30/REPORT.md) | PNG, text, WAV, video and long audio; stage and coverage limits |
| [Long-audio follow-up](evidence/multimodal-2026-10-30b/REPORT.md) | Failed extraction and adaptive repeats retained; frozen ASR comparison |
| [Additional input formats](evidence/input-formats-2026-10-30/REPORT.md) | Markdown, JPEG, WebP, MP3, silent MP4 and native-text PDF |
| [Paired multimodal corpus/protocol](../eval/multimodal-v1/README.md) | Same-input comparison; frozen code, shared preprocessing, native image reading and retained failures |
| [Single-stock saved summary](evidence/stock-review-example/stock-review.html) | Reuses three reports, no new calls; repeated occurrences are not independent facts |
| [Offline judge walkthrough](evidence/judge-walkthrough/REPORT.md) | Deterministic evidence-to-verdict checks; no model calls |

[2026-10-30 SEC refresh](evidence/sec-refresh-2026-10-30/REPORT.md) retains compressed raw snapshots for offline restoration. [Real issuer media catalogue](evidence/real-media-2026-10-30/README.md) distinguishes prepared images from link-only webcast candidates; neither is a new accuracy benchmark.

## What to retain for each new paid suite

- Before execution: case selection, expected outcomes or explicit unknown ground truth, original inputs or permitted reproducible fixtures, SHA-256 hashes, provider/model, output-token limit, budget partitions and retry policy.
- During execution: per-attempt requests/responses, extraction and verification traces, source quotes/locations, frozen evidence references, errors and reservation/reconciliation ledger events. Credentials must be redacted; account balances stay private.
- After execution: every outcome, operational coverage (separate from recall/accuracy), wall time, estimated cost, source hashes and validation commands/results. Preserve failed attempts before starting a separately named adaptive repeat.
- For new executions through the format-suite wrapper: command arguments, start/end timestamps, exit codes and stdout/stderr logs. The initial format run used the single-case runner: its protocol and structured reports are the retained execution evidence, not a fabricated historical console log.

Derived WAVs or decoded frames may be omitted when the original input is retained and the protocol records their reconstruction. Original media, OCR/ASR responses and verification traces are not interchangeable: keep their roles explicit.

## Reuse without more credits

Read the saved HTML/JSON, rebuild reports and use recorded-response replay tests. The new [format index](evidence/input-formats-2026-10-30/runs.json) also links frozen raw and normalized text for each channel. Rechecking that text with a live verifier costs text tokens but skips another OCR/ASR request; it does **not** test media extraction, timestamps, speaker labels or cross-modal alignment again.

```sh
python3 scripts/multimodal/build_format_report.py
sh scripts/verify.sh
```

The verifier is isolated from provider credentials and blocks network access. New fixture hashes are checked by the format-report builder. Input files for the additional formats are retained under `tests/fixtures/multimodal/format-probes/`; silent video reuses `tests/fixtures/multimodal/slides-silent.mp4`.

## Repeat the live format suite

This command makes paid calls, shares a $3 cap across cases ($1 per provider), validates the registered input hashes and refuses an existing output directory:

```sh
.venv/bin/python scripts/multimodal/run_format_suite.py --out-root runs/formats-001
```

Keep the original evidence unchanged. Use a new directory for each run; compare model/prompt/policy/source/input hashes before interpreting changes. Do not publish a best-of score or treat small synthetic examples as a general accuracy benchmark.

## Completed paired study and separate product follow-ups

- [Nine-format final benchmark](evidence/fair-multimodal-v1/REPORT.md): 319 expected artifact records audited, identical per-case inputs across platforms, raw requests/responses and retained failures; [offline reuse](evidence/fair-multimodal-v1/REUSE.md).
- [Real Tesla context follow-ups](evidence/stock-context-posthoc-2026-10-30/REPORT.md): both attempts retained, 41 recorded requests, Baseten only, frozen OCR reused. These known-failure checks do not replace the primary results.
- [Combined task spend](evidence/fair-multimodal-v1/task-spend.json): separate primary and post-hoc estimates/reservations, each provider below its $40 authorization.

## Chart diagnosis replay

[Real Tesla chart investigation](evidence/chart-diagnosis-2026-10-30/REPORT.md) preserves original paid outputs and source hashes; new summary explains visual geometry and zero-extraction gaps. No new API calls or accuracy scores.

## Real webcast audio and video

[Microsoft real AV v1](evidence/real-av-v1/REPORT.md) retains the exact 60-second MP4 and derived WAV, official-source provenance, reference captions, six route attempts, all raw outputs and a separate ledger. Same underlying scene, fresh Meta preprocessing per route; no provider-native audio ranking or independent accuracy claim.

## Event-context post-hoc replay

[Period and summary regression](evidence/real-av-context-posthoc/REPORT.md) reuses real-AV extracted proposals without API calls. Before/after admission, exact quotes, context provenance, raw narrative and safe program explanation are retained separately from original financial verdicts. No new accuracy estimate.

## Live event-context verification

[Real-AV context live follow-up](evidence/real-av-context-live/REPORT.md) retains 18 results, 53 raw requests, source/input freeze, three ledgers and failures. Reuses prior media/extraction; same six inputs per verifier. No independent accuracy denominator and no replacement of prior failures.
